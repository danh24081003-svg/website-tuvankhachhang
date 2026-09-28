from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ManagedService, SiteImage, SiteSetting
from app.services.knowledge_service import KnowledgeService, get_knowledge_service


router = APIRouter(tags=["knowledge"])


@router.get("/api/services")
def get_services(db: Session = Depends(get_db), knowledge: KnowledgeService = Depends(get_knowledge_service)):
    services = db.scalars(
        select(ManagedService)
        .where(ManagedService.is_active.is_(True))
        .order_by(ManagedService.display_order.asc(), ManagedService.id.asc())
    ).all()
    if not services:
        return knowledge.services()
    images = {item.key: item.url for item in db.scalars(select(SiteImage)).all()}
    return [
        {
            "id": service.slug,
            "name": service.name,
            "description": service.short_description,
            "detail": service.description,
            "image_key": service.image_key,
            "image_url": images.get(service.image_key, ""),
        }
        for service in services
    ]


@router.get("/api/company")
def get_company(db: Session = Depends(get_db), knowledge: KnowledgeService = Depends(get_knowledge_service)):
    settings = {item.key: item.value for item in db.scalars(select(SiteSetting)).all()}
    if not settings:
        return knowledge.company()
    return {
        "company_name": settings.get("company_name", ""),
        "brand_name": settings.get("brand_name", ""),
        "hotline": settings.get("hotline", ""),
        "email": settings.get("email", ""),
        "address": settings.get("address", ""),
        "working_hours": settings.get("working_hours", ""),
        "slogan": settings.get("slogan", ""),
    }


@router.get("/api/site/images")
def get_site_images(db: Session = Depends(get_db)):
    return {item.key: item.url for item in db.scalars(select(SiteImage)).all()}


@router.get("/api/site/content")
def get_site_content(db: Session = Depends(get_db)):
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
    settings = {item.key: item.value for item in db.scalars(select(SiteSetting).where(SiteSetting.key.in_(keys))).all()}
    return {key: settings.get(key, "") for key in keys}


@router.get("/api/pricing")
def get_pricing(knowledge: KnowledgeService = Depends(get_knowledge_service)):
    return knowledge.pricing()


@router.get("/api/services/{slug}")
def get_service_detail(slug: str, db: Session = Depends(get_db)):
    import json
    from fastapi import HTTPException
    from app.services.service_consultation_flows import normalize_slug

    clean_slug = normalize_slug(slug)
    service = db.scalars(
        select(ManagedService)
        .where(
            (ManagedService.slug == clean_slug) | (ManagedService.slug == slug),
            ManagedService.is_active.is_(True),
        )
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ")

    images = {item.key: item.url for item in db.scalars(select(SiteImage)).all()}
    card_img = service.card_image or images.get(service.image_key, "")
    hero_img = service.hero_image or card_img

    def safe_json(val):
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return []

    return {
        "id": service.slug,
        "name": service.name,
        "short_description": service.short_description,
        "description": service.description,
        "content": service.content,
        "image_key": service.image_key,
        "image_url": card_img,
        "hero_image": hero_img,
        "card_image": card_img,
        "scope_of_work": safe_json(service.scope_of_work),
        "process": safe_json(service.process),
        "benefits": safe_json(service.benefits),
        "faq": safe_json(service.faq),
        "seo_title": service.seo_title,
        "seo_description": service.seo_description,
    }

