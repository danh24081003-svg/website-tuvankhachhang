import json
from pathlib import Path

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import BASE_DIR, get_settings
from app.services.default_service_data import DEFAULT_SERVICE_DETAILS


settings = get_settings()

db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def _run_safe_migrations() -> None:
    """Safe additive migrations without dropping or losing data."""
    with engine.connect() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()

        if "leads" in tables:
            lead_cols = {col["name"] for col in inspector.get_columns("leads")}
            if "source" not in lead_cols:
                conn.exec_driver_sql("ALTER TABLE leads ADD COLUMN source VARCHAR(40) DEFAULT 'FORM' NOT NULL")
            if "session_id" not in lead_cols:
                conn.exec_driver_sql("ALTER TABLE leads ADD COLUMN session_id VARCHAR(80)")
            if "location" not in lead_cols:
                conn.exec_driver_sql("ALTER TABLE leads ADD COLUMN location VARCHAR(255)")
            if "requirements" not in lead_cols:
                conn.exec_driver_sql("ALTER TABLE leads ADD COLUMN requirements TEXT")
            if "notes" not in lead_cols:
                conn.exec_driver_sql("ALTER TABLE leads ADD COLUMN notes TEXT")

        if "chat_messages" in tables:
            chat_cols = {col["name"] for col in inspector.get_columns("chat_messages")}
            if "conversation_id" not in chat_cols:
                conn.exec_driver_sql("ALTER TABLE chat_messages ADD COLUMN conversation_id INTEGER")
            if "attachments" not in chat_cols:
                conn.exec_driver_sql("ALTER TABLE chat_messages ADD COLUMN attachments TEXT")
            if "client_message_id" not in chat_cols:
                conn.exec_driver_sql("ALTER TABLE chat_messages ADD COLUMN client_message_id VARCHAR(120)")
            if "status" not in chat_cols:
                conn.exec_driver_sql("ALTER TABLE chat_messages ADD COLUMN status VARCHAR(40) DEFAULT 'SUCCESS' NOT NULL")

        if "conversations" in tables:
            conversation_cols = {col["name"] for col in inspector.get_columns("conversations")}
            if "client_id" not in conversation_cols:
                conn.exec_driver_sql("ALTER TABLE conversations ADD COLUMN client_id VARCHAR(80)")
            if "title" not in conversation_cols:
                conn.exec_driver_sql("ALTER TABLE conversations ADD COLUMN title VARCHAR(80) DEFAULT 'Cuộc trò chuyện mới' NOT NULL")
            if "deleted_at" not in conversation_cols:
                conn.exec_driver_sql("ALTER TABLE conversations ADD COLUMN deleted_at DATETIME")

        if "managed_services" in tables:
            service_cols = {col["name"] for col in inspector.get_columns("managed_services")}
            if "hero_image" not in service_cols:
                conn.exec_driver_sql("ALTER TABLE managed_services ADD COLUMN hero_image VARCHAR(500)")
            if "card_image" not in service_cols:
                conn.exec_driver_sql("ALTER TABLE managed_services ADD COLUMN card_image VARCHAR(500)")
            if "content" not in service_cols:
                conn.exec_driver_sql("ALTER TABLE managed_services ADD COLUMN content TEXT")
            if "scope_of_work" not in service_cols:
                conn.exec_driver_sql("ALTER TABLE managed_services ADD COLUMN scope_of_work TEXT")
            if "process" not in service_cols:
                conn.exec_driver_sql("ALTER TABLE managed_services ADD COLUMN process TEXT")
            if "benefits" not in service_cols:
                conn.exec_driver_sql("ALTER TABLE managed_services ADD COLUMN benefits TEXT")
            if "faq" not in service_cols:
                conn.exec_driver_sql("ALTER TABLE managed_services ADD COLUMN faq TEXT")
            if "seo_title" not in service_cols:
                conn.exec_driver_sql("ALTER TABLE managed_services ADD COLUMN seo_title VARCHAR(255)")
            if "seo_description" not in service_cols:
                conn.exec_driver_sql("ALTER TABLE managed_services ADD COLUMN seo_description VARCHAR(500)")

        if "chat_attachments" in tables:
            attachment_cols = {col["name"] for col in inspector.get_columns("chat_attachments")}
            if "data" not in attachment_cols:
                conn.exec_driver_sql("ALTER TABLE chat_attachments ADD COLUMN data BYTEA" if not db_url.startswith("sqlite") else "ALTER TABLE chat_attachments ADD COLUMN data BLOB")

        if "site_users" in tables:
            user_cols = {col["name"] for col in inspector.get_columns("site_users")}
            if "avatar_url" not in user_cols:
                conn.exec_driver_sql("ALTER TABLE site_users ADD COLUMN avatar_url VARCHAR(500)")
            if "google_sub" not in user_cols:
                conn.exec_driver_sql("ALTER TABLE site_users ADD COLUMN google_sub VARCHAR(255)")
            if "role" not in user_cols:
                conn.exec_driver_sql("ALTER TABLE site_users ADD COLUMN role VARCHAR(40) DEFAULT 'customer' NOT NULL")
            if "permissions" not in user_cols:
                conn.exec_driver_sql("ALTER TABLE site_users ADD COLUMN permissions TEXT DEFAULT '[]' NOT NULL")
            if "is_active" not in user_cols:
                conn.exec_driver_sql("ALTER TABLE site_users ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL")
            if "updated_at" not in user_cols:
                conn.exec_driver_sql("ALTER TABLE site_users ADD COLUMN updated_at DATETIME")
            if "last_login" not in user_cols:
                conn.exec_driver_sql("ALTER TABLE site_users ADD COLUMN last_login DATETIME")

        if "chat_messages" in tables and "conversations" in tables:
            conn.execute(
                text(
                    """
                    UPDATE chat_messages
                    SET conversation_id = (
                        SELECT conversations.id
                        FROM conversations
                        WHERE conversations.session_id = chat_messages.session_id
                        LIMIT 1
                    )
                    WHERE conversation_id IS NULL
                    """
                )
            )

        conn.commit()


def init_db() -> None:
    from app import models

    _run_safe_migrations()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_initial_site_data(db, models)


def _load_json(filename: str):
    try:
        path = BASE_DIR / "data" / filename
        if path.exists() and path.is_file():
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
    except Exception:
        pass
    return {} if filename.endswith("company.json") else []


def seed_initial_site_data(db: Session, models_module) -> None:
    company = _load_json("company.json")
    services = _load_json("services.json")
    settings_map = {
        "company_name": company.get("company_name", "CÔNG TY TNHH DỊCH VỤ OSHIN THỜI ĐẠI - ĐẤT PHƯƠNG NAM"),
        "brand_name": company.get("brand_name", "Oshin Thời Đại"),
        "hotline": company.get("hotline", "0901 040 484"),
        "slogan": company.get("slogan", "Khẳng định sự thành đạt"),
        "email": company.get("email", ""),
        "address": company.get("address", ""),
        "working_hours": company.get("working_hours", ""),
        "hero_eyebrow": "Oshin Thời Đại • Đất Phương Nam",
        "hero_heading": "Giải pháp toàn diện cho cuộc sống tiện nghi hơn.",
        "hero_description": "Oshin Thời Đại cung cấp các giải pháp dịch vụ chuyên nghiệp cho gia đình, doanh nghiệp và công trình.",
        "hero_cta_text": "Nhận tư vấn",
        "why_heading": "Không chỉ là dịch vụ. Đó là sự an tâm.",
        "why_description": "Chúng tôi tiếp nhận từng nhu cầu với quy trình rõ ràng, giải pháp linh hoạt và sự chú trọng vào trải nghiệm của từng khách hàng.",
        "final_cta_heading": "Sẵn sàng để chúng tôi hỗ trợ bạn?",
        "final_cta_description": "",
        "final_cta_button_text": "Tư vấn ngay",
    }
    existing_setting_keys = set(db.scalars(select(models_module.SiteSetting.key)).all())
    for key, value in settings_map.items():
        if key not in existing_setting_keys:
            db.add(models_module.SiteSetting(key=key, value=value))

    images = [
        ("hero_main", "Hero main image", "doingu.png", "/static/img/doingu.png", "Đội ngũ Oshin Thời Đại", "1600 × 1200, 4:3"),
        ("hero_secondary_1", "Hero secondary image 1", "vanchuyen.png", "/static/img/vanchuyen.png", "Vận chuyển và di dời", "1200 × 900, 4:3"),
        ("hero_secondary_2", "Hero secondary image 2", "vesinh.png", "/static/img/vesinh.png", "Vệ sinh chuyên nghiệp", "1200 × 900, 4:3"),
        ("service_moving", "Vận chuyển, di dời", "van-chuyen-di-doi.png", "/static/img/services/van-chuyen-di-doi.png", "Vận chuyển di dời", "1200 × 900, 4:3"),
        ("service_industrial_cleaning", "Vệ sinh công nghiệp", "ve-sinh-cong-nghiep.png", "/static/img/services/ve-sinh-cong-nghiep.png", "Vệ sinh công nghiệp", "1200 × 900, 4:3"),
        ("service_repair", "Trang trí, sửa chữa", "trang-tri-sua-chua.png", "/static/img/services/trang-tri-sua-chua.png", "Trang trí sửa chữa", "1200 × 900, 4:3"),
        ("service_labor", "Cung cấp & quản lý nguồn lao động", "cung-cap-quan-ly-lao-dong.png", "/static/img/services/cung-cap-quan-ly-lao-dong.png", "Cung cấp lao động", "1200 × 900, 4:3"),
        ("service_housekeeping", "Giúp việc theo giờ, định kỳ", "giup-viec.png", "/static/img/services/giup-viec.png", "Giúp việc gia đình", "1200 × 900, 4:3"),
        ("service_gardening", "Chăm sóc cây cảnh", "cham-soc-cay-canh.png", "/static/img/services/cham-soc-cay-canh.png", "Chăm sóc cây cảnh", "1200 × 900, 4:3"),
        ("service_pest_control", "Diệt côn trùng", "diet-con-trung.png", "/static/img/services/diet-con-trung.png", "Diệt côn trùng", "1200 × 900, 4:3"),
        ("brand_team", "Ảnh đội ngũ", "doingu.png", "/static/img/doingu.png", "Đội ngũ Oshin Thời Đại", "1920 × 1080, 16:9"),
        ("brand_section", "Ảnh section thương hiệu", "doingu.png", "/static/img/doingu.png", "Thương hiệu Oshin", "1920 × 1080, 16:9"),
    ]
    existing_image_keys = set(db.scalars(select(models_module.SiteImage.key)).all())
    for key, label, filename, url, alt, recommendation in images:
        if key not in existing_image_keys:
            db.add(
                models_module.SiteImage(
                    key=key,
                    label=label,
                    filename=filename,
                    url=url,
                    alt_text=alt,
                    default_url=url,
                    recommendation=recommendation,
                )
            )

    image_keys = {
        "van-chuyen-di-doi": "service_moving",
        "ve-sinh-cong-nghiep": "service_industrial_cleaning",
        "trang-tri-sua-chua": "service_repair",
        "cung-cap-quan-ly-lao-dong": "service_labor",
        "giup-viec": "service_housekeeping",
        "cham-soc-cay-canh": "service_gardening",
        "diet-con-trung": "service_pest_control",
    }
    existing_services = {s.slug: s for s in db.scalars(select(models_module.ManagedService)).all()}
    for index, item in enumerate(services, start=1):
        slug = item["id"]
        details = DEFAULT_SERVICE_DETAILS.get(slug, {})
        if slug not in existing_services:
            svc = models_module.ManagedService(
                slug=slug,
                name=item["name"],
                short_description=item["description"],
                description=item["description"],
                image_key=image_keys.get(slug, "service_industrial_cleaning"),
                hero_image=details.get("hero_heading"),
                content=details.get("content"),
                scope_of_work=details.get("scope_of_work"),
                process=details.get("process"),
                benefits=details.get("benefits"),
                faq=details.get("faq"),
                seo_title=details.get("seo_title"),
                seo_description=details.get("seo_description"),
                display_order=index,
            )
            db.add(svc)
        else:
            svc = existing_services[slug]
            # Safely enrich existing services if scope_of_work is not yet populated
            if not svc.scope_of_work:
                svc.content = svc.content or details.get("content")
                svc.scope_of_work = details.get("scope_of_work")
                svc.process = details.get("process")
                svc.benefits = details.get("benefits")
                svc.faq = details.get("faq")
                svc.seo_title = svc.seo_title or details.get("seo_title")
                svc.seo_description = svc.seo_description or details.get("seo_description")

    # Ensure default admin account exists
    import os
    from app.services.auth_service import hash_password

    default_admin_email = os.getenv("ADMIN_EMAIL", "admin@oshin.vn").strip().lower()
    default_admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123456")

    admin_user = db.scalars(select(models_module.AdminUser).where(models_module.AdminUser.email == default_admin_email)).first()
    if not admin_user:
        db.add(
            models_module.AdminUser(
                email=default_admin_email,
                password_hash=hash_password(default_admin_password),
                is_active=True,
            )
        )

    try:
        Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    db.commit()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
