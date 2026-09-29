import os
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.config import BASE_DIR, get_settings
from app.database import get_db
from app.models import AdminSession, AdminUser, ChatMessage, Customer, Lead, ManagedService, SiteImage, SiteSetting, StoredMedia
from app.services.auth_service import clear_admin_session, create_admin_session, hash_password, hash_token, require_admin, require_admin_with_csrf, verify_password
from app.services.storage_service import get_storage_provider


router = APIRouter(tags=["admin"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
_login_attempts: dict[str, deque[float]] = defaultdict(deque)

LEAD_STATUSES = {
    "new",
    "contacted",
    "consulting",
    "survey_scheduled",
    "quoted",
    "won",
    "completed",
    "cancelled",
}


class LoginPayload(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=200)


class SettingPayload(BaseModel):
    values: dict[str, str] = Field(default_factory=dict)


class ServicePayload(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=120)
    short_description: str = Field(min_length=2, max_length=800)
    description: str = Field(default="", max_length=3000)
    image_key: str = Field(min_length=2, max_length=120)
    hero_image: str | None = None
    card_image: str | None = None
    content: str | None = None
    scope_of_work: str | None = None
    process: str | None = None
    benefits: str | None = None
    faq: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    is_active: bool = True
    display_order: int = Field(ge=0, le=999)


class LeadStatusPayload(BaseModel):
    status: str = Field(min_length=2, max_length=40)


def _admin_logged_in(request: Request, db: Session) -> bool:
    token = request.cookies.get("oshin_admin_session")
    if not token:
        return False
    session = db.scalars(select(AdminSession).where(AdminSession.token_hash == hash_token(token))).first()
    return bool(session and session.expires_at > datetime.utcnow() and session.user.is_active)


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def _rate_limit_login(request: Request) -> None:
    settings = get_settings()
    now = time.monotonic()
    bucket = _login_attempts[_client_key(request)]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= settings.admin_login_rate_limit_per_minute:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Thử đăng nhập quá nhanh. Vui lòng chờ ít phút.")
    bucket.append(now)


def _setting_dict(db: Session) -> dict[str, str]:
    return {item.key: item.value for item in db.scalars(select(SiteSetting)).all()}


def _image_dict(db: Session) -> dict[str, dict]:
    return {item.key: image_out(item) for item in db.scalars(select(SiteImage).order_by(SiteImage.id)).all()}


def image_out(item: SiteImage) -> dict:
    return {
        "id": item.id,
        "key": item.key,
        "label": item.label,
        "filename": item.filename,
        "url": item.url,
        "alt_text": item.alt_text,
        "default_url": item.default_url,
        "recommendation": item.recommendation,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def service_out(item: ManagedService, images: dict[str, dict] | None = None) -> dict:
    image = images.get(item.image_key) if images else None
    return {
        "id": item.id,
        "slug": item.slug,
        "name": item.name,
        "short_description": item.short_description,
        "description": item.description,
        "image_key": item.image_key,
        "image_url": image["url"] if image else "",
        "hero_image": item.hero_image or "",
        "card_image": item.card_image or (image["url"] if image else ""),
        "content": item.content or "",
        "scope_of_work": item.scope_of_work or "",
        "process": item.process or "",
        "benefits": item.benefits or "",
        "faq": item.faq or "",
        "seo_title": item.seo_title or "",
        "seo_description": item.seo_description or "",
        "is_active": item.is_active,
        "display_order": item.display_order,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def lead_out(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "customer_name": lead.customer.name,
        "phone": lead.customer.phone,
        "address": lead.customer.address or "",
        "service": lead.service,
        "message": lead.message,
        "status": lead.status,
        "source": lead.source or "FORM",
        "location": lead.location or lead.customer.address or "",
        "requirements": lead.requirements or "",
        "session_id": lead.session_id or "",
        "notes": lead.notes or "",
        "created_at": lead.created_at.isoformat(),
    }


@router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request, db: Session = Depends(get_db)):
    if _admin_logged_in(request, db):
        return RedirectResponse("/admin", status_code=302)
    return templates.TemplateResponse(request, "admin_login.html")


@router.get("/admin", response_class=HTMLResponse)
@router.get("/admin/{path:path}", response_class=HTMLResponse)
def admin_page(request: Request, path: str = "", db: Session = Depends(get_db)):
    if not _admin_logged_in(request, db):
        return RedirectResponse("/admin/login", status_code=302)
    return templates.TemplateResponse(request, "admin.html")


@router.post("/api/admin/auth/login")
def admin_login(payload: LoginPayload, request: Request, response: Response, db: Session = Depends(get_db)):
    _rate_limit_login(request)
    raw_email = payload.email.strip().lower()
    
    # Check if admin table is empty, auto-seed default admin
    admin_count = db.scalar(select(func.count(AdminUser.id))) or 0
    if admin_count == 0:
        default_email = os.getenv("ADMIN_EMAIL", "admin@oshin.vn").strip().lower()
        default_pwd = os.getenv("ADMIN_PASSWORD", "Admin@123456")
        db.add(AdminUser(email=default_email, password_hash=hash_password(default_pwd), is_active=True))
        db.commit()

    user = db.scalars(
        select(AdminUser).where(
            (AdminUser.email == raw_email)
            | (AdminUser.email == f"{raw_email}@oshin.vn")
        )
    ).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Thông tin đăng nhập không đúng")
    create_admin_session(db, user, response)
    return {"ok": True}


@router.post("/api/admin/auth/logout")
def admin_logout(request: Request, response: Response, db: Session = Depends(get_db), _: AdminUser = Depends(require_admin_with_csrf)):
    token = request.cookies.get("oshin_admin_session")
    if token:
        session = db.scalars(select(AdminSession).where(AdminSession.token_hash == hash_token(token))).first()
        if session:
            db.delete(session)
            db.commit()
    clear_admin_session(response)
    return {"ok": True}


@router.get("/api/admin/me")
def admin_me(user: AdminUser = Depends(require_admin)):
    return {"email": user.email}


@router.get("/api/admin/overview")
def admin_overview(db: Session = Depends(get_db), _: AdminUser = Depends(require_admin)):
    total_leads = db.scalar(select(func.count(Lead.id))) or 0
    new_leads = db.scalar(select(func.count(Lead.id)).where(Lead.status == "new")) or 0
    total_chats = db.scalar(select(func.count(func.distinct(ChatMessage.session_id)))) or 0
    service_count = db.scalar(select(func.count(ManagedService.id)).where(ManagedService.is_active.is_(True))) or 0
    recent = db.scalars(select(Lead).options(joinedload(Lead.customer)).order_by(Lead.created_at.desc()).limit(8)).all()
    return {
        "cards": {
            "total_leads": total_leads,
            "new_leads": new_leads,
            "total_chats": total_chats,
            "service_count": service_count,
        },
        "recent_leads": [lead_out(item) for item in recent],
    }


@router.get("/api/admin/images")
def admin_images(db: Session = Depends(get_db), _: AdminUser = Depends(require_admin)):
    return list(_image_dict(db).values())


@router.post("/api/admin/images/{image_key}")
async def admin_upload_image(
    image_key: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(require_admin_with_csrf),
):
    image = db.scalars(select(SiteImage).where(SiteImage.key == image_key)).first()
    if not image:
        raise HTTPException(status_code=404, detail="Không tìm thấy vị trí ảnh")
    provider = get_storage_provider(db=db)
    stored = await provider.upload(file, prefix=image_key, db=db)
    old_url = image.url
    try:
        image.filename = stored.filename
        image.url = stored.url
        image.updated_at = datetime.utcnow()
        db.commit()
    except Exception:
        provider.delete(stored.url, db=db)
        db.rollback()
        raise
    # Only delete old image if not default and not referenced by another key
    if old_url and old_url != image.default_url:
        other_use = db.scalar(select(func.count(SiteImage.id)).where(SiteImage.url == old_url, SiteImage.key != image_key)) or 0
        if other_use == 0:
            provider.delete(old_url, db=db)
    db.refresh(image)
    return image_out(image)


@router.post("/api/admin/images/{image_key}/restore")
def admin_restore_image(image_key: str, db: Session = Depends(get_db), _: AdminUser = Depends(require_admin_with_csrf)):
    image = db.scalars(select(SiteImage).where(SiteImage.key == image_key)).first()
    if not image:
        raise HTTPException(status_code=404, detail="Không tìm thấy vị trí ảnh")
    old_url = image.url
    image.url = image.default_url
    image.filename = Path(image.default_url).name
    image.updated_at = datetime.utcnow()
    db.commit()
    if old_url and old_url != image.default_url:
        other_use = db.scalar(select(func.count(SiteImage.id)).where(SiteImage.url == old_url, SiteImage.key != image_key)) or 0
        if other_use == 0:
            get_storage_provider(db=db).delete(old_url, db=db)
    db.refresh(image)
    return image_out(image)


@router.get("/api/admin/services")
def admin_services(db: Session = Depends(get_db), _: AdminUser = Depends(require_admin)):
    images = _image_dict(db)
    services = db.scalars(select(ManagedService).order_by(ManagedService.display_order.asc(), ManagedService.id.asc())).all()
    return [service_out(item, images) for item in services]


@router.post("/api/admin/services")
def admin_create_service(
    payload: ServicePayload,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(require_admin_with_csrf),
):
    clean_slug = payload.slug.strip().lower()
    existing = db.scalars(select(ManagedService).where(ManagedService.slug == clean_slug)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mã định danh (slug) dịch vụ đã tồn tại")
    if not db.scalars(select(SiteImage).where(SiteImage.key == payload.image_key)).first():
        raise HTTPException(status_code=400, detail="Ảnh dịch vụ không hợp lệ")

    service = ManagedService(
        name=payload.name.strip(),
        slug=clean_slug,
        short_description=payload.short_description.strip(),
        description=payload.description.strip(),
        image_key=payload.image_key,
        hero_image=payload.hero_image.strip() if payload.hero_image else None,
        card_image=payload.card_image.strip() if payload.card_image else None,
        content=payload.content.strip() if payload.content else None,
        scope_of_work=payload.scope_of_work,
        process=payload.process,
        benefits=payload.benefits,
        faq=payload.faq,
        seo_title=payload.seo_title.strip() if payload.seo_title else None,
        seo_description=payload.seo_description.strip() if payload.seo_description else None,
        is_active=payload.is_active,
        display_order=payload.display_order,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service_out(service, _image_dict(db))


@router.put("/api/admin/services/{service_id}")
def admin_update_service(
    service_id: int,
    payload: ServicePayload,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(require_admin_with_csrf),
):
    service = db.get(ManagedService, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ")
    clean_slug = payload.slug.strip().lower()
    duplicate_slug = db.scalars(
        select(ManagedService).where(ManagedService.slug == clean_slug, ManagedService.id != service_id)
    ).first()
    if duplicate_slug:
        raise HTTPException(status_code=400, detail="Mã định danh (slug) đã được dịch vụ khác sử dụng")
    if not db.scalars(select(SiteImage).where(SiteImage.key == payload.image_key)).first():
        raise HTTPException(status_code=400, detail="Ảnh dịch vụ không hợp lệ")
    service.name = payload.name.strip()
    service.slug = clean_slug
    service.short_description = payload.short_description.strip()
    service.description = payload.description.strip()
    service.image_key = payload.image_key
    service.is_active = payload.is_active
    service.display_order = payload.display_order
    if payload.hero_image is not None:
        service.hero_image = payload.hero_image.strip() or None
    if payload.card_image is not None:
        service.card_image = payload.card_image.strip() or None
    if payload.content is not None:
        service.content = payload.content.strip() or None
    if payload.scope_of_work is not None:
        service.scope_of_work = payload.scope_of_work
    if payload.process is not None:
        service.process = payload.process
    if payload.benefits is not None:
        service.benefits = payload.benefits
    if payload.faq is not None:
        service.faq = payload.faq
    if payload.seo_title is not None:
        service.seo_title = payload.seo_title.strip() or None
    if payload.seo_description is not None:
        service.seo_description = payload.seo_description.strip() or None
    db.commit()
    db.refresh(service)
    return service_out(service, _image_dict(db))


@router.delete("/api/admin/services/{service_id}")
def admin_delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(require_admin_with_csrf),
):
    service = db.get(ManagedService, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ")
    db.delete(service)
    db.commit()
    return {"ok": True}


@router.get("/api/admin/content")
def admin_content(db: Session = Depends(get_db), _: AdminUser = Depends(require_admin)):
    settings = _setting_dict(db)
    keys = [
        "hero_eyebrow",
        "hero_heading",
        "hero_description",
        "hero_cta_text",
        "why_heading",
        "why_description",
        "final_cta_heading",
        "final_cta_description",
        "final_cta_button_text",
    ]
    return {key: settings.get(key, "") for key in keys}


@router.put("/api/admin/content")
def admin_update_content(payload: SettingPayload, db: Session = Depends(get_db), _: AdminUser = Depends(require_admin_with_csrf)):
    allowed = set(admin_content(db, _).keys())
    _update_settings(db, payload.values, allowed)
    return admin_content(db, _)


@router.get("/api/admin/company")
def admin_company(db: Session = Depends(get_db), _: AdminUser = Depends(require_admin)):
    settings = _setting_dict(db)
    keys = ["company_name", "brand_name", "hotline", "slogan", "email", "address", "working_hours"]
    return {key: settings.get(key, "") for key in keys}


@router.put("/api/admin/company")
def admin_update_company(payload: SettingPayload, db: Session = Depends(get_db), _: AdminUser = Depends(require_admin_with_csrf)):
    allowed = {"company_name", "brand_name", "hotline", "slogan", "email", "address", "working_hours"}
    _update_settings(db, payload.values, allowed)
    return admin_company(db, _)


def _update_settings(db: Session, values: dict[str, str], allowed: set[str]) -> None:
    existing = {item.key: item for item in db.scalars(select(SiteSetting).where(SiteSetting.key.in_(allowed))).all()}
    for key, value in values.items():
        if key not in allowed:
            continue
        clean = str(value or "").strip()
        if key in existing:
            existing[key].value = clean
        else:
            db.add(SiteSetting(key=key, value=clean))
    db.commit()


@router.get("/api/admin/leads")
def admin_leads(
    q: str = "",
    service: str = "",
    status_filter: str = "",
    source_filter: str = "",
    db: Session = Depends(get_db),
    _: AdminUser = Depends(require_admin),
):
    query = select(Lead).options(joinedload(Lead.customer)).order_by(Lead.created_at.desc())
    if q:
        like = f"%{q.strip()}%"
        query = query.join(Lead.customer).where((Customer.name.ilike(like)) | (Customer.phone.ilike(like)))
    if service:
        query = query.where(Lead.service == service)
    if status_filter:
        query = query.where(Lead.status == status_filter.strip().lower())
    if source_filter:
        query = query.where(Lead.source == source_filter.strip().upper())
    return [lead_out(item) for item in db.scalars(query.limit(200)).all()]


@router.get("/api/admin/leads/{lead_id}")
def admin_lead_detail(lead_id: int, db: Session = Depends(get_db), _: AdminUser = Depends(require_admin)):
    lead = db.scalars(select(Lead).options(joinedload(Lead.customer)).where(Lead.id == lead_id)).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    data = lead_out(lead)
    if lead.session_id:
        chat_msgs = db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == lead.session_id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        ).all()
        data["chat_messages"] = [
            {
                "id": m.id,
                "role": m.role,
                "message": m.message,
                "created_at": m.created_at.isoformat(),
            }
            for m in chat_msgs
        ]
    else:
        data["chat_messages"] = []
    return data


@router.put("/api/admin/leads/{lead_id}/status")
def admin_update_lead_status(
    lead_id: int,
    payload: LeadStatusPayload,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(require_admin_with_csrf),
):
    clean_status = payload.status.strip().lower()
    if clean_status not in LEAD_STATUSES:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    lead.status = clean_status
    db.commit()
    db.refresh(lead)
    return {"id": lead.id, "status": lead.status}


@router.get("/api/admin/chats")
def admin_chats(db: Session = Depends(get_db), _: AdminUser = Depends(require_admin)):
    rows = db.execute(
        select(
            ChatMessage.session_id,
            func.count(ChatMessage.id).label("message_count"),
            func.max(ChatMessage.created_at).label("last_message_at"),
        )
        .group_by(ChatMessage.session_id)
        .order_by(func.max(ChatMessage.created_at).desc())
        .limit(200)
    ).all()
    return [
        {
            "session_id": row.session_id,
            "message_count": row.message_count,
            "last_message_at": row.last_message_at.isoformat() if row.last_message_at else None,
        }
        for row in rows
    ]


@router.get("/api/admin/chats/{session_id}")
def admin_chat_detail(session_id: str, db: Session = Depends(get_db), _: AdminUser = Depends(require_admin)):
    messages = db.scalars(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())).all()
    return [
        {
            "id": item.id,
            "session_id": item.session_id,
            "role": item.role,
            "message": item.message,
            "created_at": item.created_at.isoformat(),
        }
        for item in messages
    ]


@router.get("/api/admin/media")
def admin_media(db: Session = Depends(get_db), _: AdminUser = Depends(require_admin)):
    used_urls = {item.url for item in db.scalars(select(SiteImage)).all()}
    used_urls.update(item.default_url for item in db.scalars(select(SiteImage)).all())
    items = []
    seen_keys = set()

    # 1. Database StoredMedia (Production Persistent Storage)
    db_medias = db.scalars(select(StoredMedia).order_by(StoredMedia.created_at.desc())).all()
    for m in db_medias:
        url = f"/api/media/{m.key}"
        seen_keys.add(m.key)
        items.append({
            "filename": m.key,
            "url": url,
            "size": m.file_size,
            "in_use": url in used_urls or m.key in [Path(u.split('?')[0]).name for u in used_urls],
        })

    # 2. Local filesystem uploads (if present in local dev)
    upload_dir = Path(get_settings().upload_dir)
    if upload_dir.exists():
        for file in sorted(upload_dir.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
            if file.is_file() and file.name not in seen_keys:
                url = f"{get_settings().upload_url_prefix.rstrip('/')}/{file.name}"
                seen_keys.add(file.name)
                items.append({
                    "filename": file.name,
                    "url": url,
                    "size": file.stat().st_size,
                    "in_use": url in used_urls,
                })
    return items


@router.post("/api/admin/media")
async def admin_upload_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(require_admin_with_csrf),
):
    provider = get_storage_provider(db=db)
    stored = await provider.upload(file, prefix="media", db=db)
    return {
        "filename": stored.filename,
        "url": stored.url,
        "in_use": False,
    }


@router.delete("/api/admin/media/{filename}")
def admin_delete_media(
    filename: str,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(require_admin_with_csrf),
):
    settings = get_settings()
    clean_name = Path(filename).name
    url_media = f"/api/media/{clean_name}"
    url_static = f"{settings.upload_url_prefix.rstrip('/')}/{clean_name}"
    in_use_count = db.scalar(
        select(func.count(SiteImage.id)).where(
            (SiteImage.url == url_media)
            | (SiteImage.default_url == url_media)
            | (SiteImage.url == url_static)
            | (SiteImage.default_url == url_static)
            | (SiteImage.filename == clean_name)
        )
    ) or 0
    if in_use_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa hình ảnh đang được website sử dụng.",
        )
    provider = get_storage_provider(db=db)
    provider.delete(clean_name, db=db)
    return {"ok": True}

