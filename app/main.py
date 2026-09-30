import json
import logging
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import BASE_DIR, get_settings
from app.database import get_db, init_db
from app.models import ManagedService, SiteImage, SiteSetting, StoredMedia
from app.routers import admin, ai, auth, chat, leads, services
from app.services.service_consultation_flows import normalize_slug


settings = get_settings()
app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
logger = logging.getLogger("uvicorn.error")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(leads.router)
app.include_router(services.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=404, content={"detail": exc.detail or "Không tìm thấy tài nguyên"})
        try:
            db = next(get_db())
            settings_map = {item.key: item.value for item in db.scalars(select(SiteSetting)).all()}
            images_map = {item.key: item.url for item in db.scalars(select(SiteImage)).all()}
            db.close()
        except Exception:
            settings_map = {}
            images_map = {}
        return templates.TemplateResponse(
            request,
            "404.html",
            {"company": settings_map, "site_images": images_map, "detail": exc.detail},
            status_code=404,
        )
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        return await http_exception_handler(request, exc)
    logger.exception("Unhandled application error")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "INTERNAL_ERROR", "message": "Hệ thống đang tạm thời gián đoạn. Anh/chị vui lòng thử lại sau."},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/media/{filename}")
@app.get("/static/uploads/{filename}")
def serve_media_file(filename: str, request: Request, db: Session = Depends(get_db)):
    clean_filename = Path(filename).name
    media = db.scalars(select(StoredMedia).where(StoredMedia.key == clean_filename)).first()
    if media and media.data:
        etag = f'W/"{media.id}-{media.file_size}-{int(media.updated_at.timestamp()) if media.updated_at else 0}"'
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag, "Cache-Control": "public, max-age=31536000, immutable"})
        return Response(
            content=media.data,
            media_type=media.mime_type or "image/webp",
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
                "ETag": etag,
            },
        )
    # Check local filesystem fallback
    local_path = BASE_DIR / "static" / "uploads" / clean_filename
    if local_path.exists() and local_path.is_file():
        return FileResponse(path=local_path)
    raise HTTPException(status_code=404, detail="Không tìm thấy tập tin hình ảnh")


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    settings_map = {item.key: item.value for item in db.scalars(select(SiteSetting)).all()}
    images_map = {item.key: item.url for item in db.scalars(select(SiteImage)).all()}
    services_list = db.scalars(
        select(ManagedService)
        .where(ManagedService.is_active.is_(True))
        .order_by(ManagedService.display_order.asc(), ManagedService.id.asc())
    ).all()
    context = {
        "company": settings_map,
        "site_images": images_map,
        "services": services_list,
        "site_content": settings_map,
    }
    return templates.TemplateResponse(request, "index.html", context)


@app.get("/dich-vu", response_class=HTMLResponse)
def services_index(request: Request, db: Session = Depends(get_db)):
    settings_map = {item.key: item.value for item in db.scalars(select(SiteSetting)).all()}
    images_map = {item.key: item.url for item in db.scalars(select(SiteImage)).all()}
    services_list = db.scalars(
        select(ManagedService)
        .where(ManagedService.is_active.is_(True))
        .order_by(ManagedService.display_order.asc(), ManagedService.id.asc())
    ).all()
    context = {
        "company": settings_map,
        "site_images": images_map,
        "services": services_list,
        "site_content": settings_map,
    }
    return templates.TemplateResponse(request, "services_index.html", context)


@app.get("/dich-vu/{slug}", response_class=HTMLResponse)
def service_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    clean_slug = normalize_slug(slug)
    service = db.scalars(
        select(ManagedService)
        .where(
            (ManagedService.slug == clean_slug) | (ManagedService.slug == slug),
            ManagedService.is_active.is_(True),
        )
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail=f"Dịch vụ '{slug}' không tồn tại hoặc đã ngừng cung cấp.")

    settings_map = {item.key: item.value for item in db.scalars(select(SiteSetting)).all()}
    images_map = {item.key: item.url for item in db.scalars(select(SiteImage)).all()}

    def parse_json(val):
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return []

    scope_of_work = parse_json(service.scope_of_work)
    process = parse_json(service.process)
    benefits = parse_json(service.benefits)
    faq = parse_json(service.faq)

    card_img = service.card_image or images_map.get(service.image_key) or f"/static/img/services/{service.slug}.png"
    hero_image_url = service.hero_image or card_img

    related_services = db.scalars(
        select(ManagedService)
        .where(ManagedService.id != service.id, ManagedService.is_active.is_(True))
        .order_by(ManagedService.display_order.asc())
        .limit(3)
    ).all()

    context = {
        "service": service,
        "company": settings_map,
        "site_images": images_map,
        "hero_image_url": hero_image_url,
        "card_image_url": card_img,
        "scope_of_work": scope_of_work,
        "process": process,
        "benefits": benefits,
        "faq": faq,
        "related_services": related_services,
        "site_content": settings_map,
    }
    return templates.TemplateResponse(request, "service_detail.html", context)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
