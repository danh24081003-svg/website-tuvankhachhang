import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.main import app
from app.models import AdminUser, ChatAttachment, SiteImage, StoredMedia
from app.services.auth_service import hash_password
from app.services.storage_service import DatabaseStorageProvider, get_storage_provider

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

client = TestClient(app)

def create_dummy_image(color="blue", size=(400, 300)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def run_tests():
    print("=== STARTING PERSISTENT STORAGE TEST SUITE ===")
    init_db()

    # 1. Test DatabaseStorageProvider upload
    print("\n1. Testing DatabaseStorageProvider...")
    db = SessionLocal()
    provider = get_storage_provider(db=db)
    assert isinstance(provider, DatabaseStorageProvider), f"Expected DatabaseStorageProvider, got {type(provider)}"
    
    dummy_jpeg = create_dummy_image("red", (300, 300))
    stored = provider.upload_bytes(dummy_jpeg, original_filename="test_red.jpg", prefix="test_hero", db=db)
    print(f"  Uploaded to URL: {stored.url}, filename: {stored.filename}")
    assert stored.url.startswith("/api/media/"), f"Unexpected URL: {stored.url}"

    # Verify StoredMedia record in DB
    media = db.scalars(select(StoredMedia).where(StoredMedia.key == stored.filename)).first()
    assert media is not None, "StoredMedia record not found in DB!"
    assert media.data is not None and len(media.data) > 0, "StoredMedia data is empty!"
    assert media.mime_type == "image/webp"
    print(f"  StoredMedia found in DB: ID={media.id}, size={media.file_size} bytes, dimensions={media.width}x{media.height}")

    # 2. Test Media Serving Endpoint /api/media/{filename}
    print("\n2. Testing /api/media/{filename} endpoint...")
    resp = client.get(stored.url)
    assert resp.status_code == 200, f"Failed to fetch media: {resp.status_code}"
    assert resp.headers.get("content-type") == "image/webp"
    assert "ETag" in resp.headers
    etag = resp.headers["ETag"]
    print(f"  Fetch 200 OK. ETag: {etag}, Content-Length: {len(resp.content)}")

    # Test ETag caching (304 Not Modified)
    resp304 = client.get(stored.url, headers={"If-None-Match": etag})
    assert resp304.status_code == 304, f"Expected 304 Not Modified, got {resp304.status_code}"
    print("  ETag caching 304 Not Modified: PASS ✅")

    # 3. Test Admin Image Upload & Idempotence
    print("\n3. Testing Admin SiteImage Upload & Startup Idempotence...")
    # Setup admin user in DB
    admin = db.scalars(select(AdminUser).where(AdminUser.email == "admin@oshin.vn")).first()
    if not admin:
        admin = AdminUser(email="admin@oshin.vn", password_hash=hash_password("Admin@123456"), is_active=True)
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # Login admin
    login_res = client.post("/api/admin/auth/login", json={"email": "admin@oshin.vn", "password": "Admin@123456"})
    assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
    cookies = login_res.cookies
    csrf_token = cookies.get("oshin_admin_csrf", "")

    # Upload custom hero_main image
    hero_jpeg = create_dummy_image("green", (800, 600))
    upload_res = client.post(
        "/api/admin/images/hero_main",
        files={"file": ("custom_hero.jpg", hero_jpeg, "image/jpeg")},
        cookies=cookies,
        headers={"x-csrf-token": csrf_token},
    )
    assert upload_res.status_code == 200, f"Admin image upload failed: {upload_res.text}"
    hero_data = upload_res.json()
    new_hero_url = hero_data["url"]
    print(f"  Admin uploaded hero_main -> URL: {new_hero_url}")
    assert new_hero_url.startswith("/api/media/"), f"Unexpected hero URL: {new_hero_url}"

    # Verify homepage renders new hero image from DB
    home_res = client.get("/")
    assert home_res.status_code == 200
    assert new_hero_url in home_res.text, "Homepage did not render admin-uploaded hero image URL!"
    print("  Homepage rendered new persistent hero image URL: PASS ✅")

    # TEST STARTUP IDEMPOTENCE: Re-run init_db() simulating a server restart / redeploy
    print("\n4. Testing Startup Idempotence (simulating redeploy / restart)...")
    init_db()
    hero_after_restart = db.scalars(select(SiteImage).where(SiteImage.key == "hero_main")).first()
    db.refresh(hero_after_restart)
    assert hero_after_restart.url == new_hero_url, f"Startup reset hero_main! Expected {new_hero_url}, got {hero_after_restart.url}"
    print("  Startup / redeploy DOES NOT overwrite admin images: PASS ✅")

    # 4. Test Chat Attachment Upload & Gemini Vision Data Loading
    print("\n5. Testing Chat Attachment Upload & Persistence...")
    chat_img_bytes = create_dummy_image("purple", (400, 400))
    session_id = "test-session-storage-123"
    client_id = "test-client-id-456"

    upload_chat_res = client.post(
        "/api/chat/upload",
        data={"session_id": session_id, "client_id": client_id},
        files=[("files", ("photo.jpg", chat_img_bytes, "image/jpeg"))],
    )
    assert upload_chat_res.status_code == 200, f"Chat upload failed: {upload_chat_res.text}"
    chat_atts = upload_chat_res.json()
    assert len(chat_atts) == 1
    att_id = chat_atts[0]["id"]
    att_url = chat_atts[0]["url"]
    print(f"  Chat attachment uploaded: ID={att_id}, URL={att_url}")

    # Verify ChatAttachment has data in DB
    att_db = db.get(ChatAttachment, att_id)
    assert att_db is not None
    assert att_db.data is not None and len(att_db.data) > 0, "ChatAttachment.data is None/empty!"
    print(f"  ChatAttachment stored in DB: size={len(att_db.data)} bytes, mime={att_db.mime_type}")

    # Fetch attachment via /api/chat/attachments/{id}
    att_res = client.get(att_url, headers={"x-chat-client-id": client_id})
    assert att_res.status_code == 200, f"Failed to get chat attachment: {att_res.status_code}"
    assert att_res.headers.get("content-type") == "image/webp"
    print("  Chat attachment retrieval with ownership check: PASS ✅")

    # 5. Clean up test admin image (restore default)
    print("\n6. Restoring default hero image...")
    restore_res = client.post(
        "/api/admin/images/hero_main/restore",
        cookies=cookies,
        headers={"x-csrf-token": csrf_token},
    )
    assert restore_res.status_code == 200
    restored_hero = restore_res.json()
    assert restored_hero["url"] == restored_hero["default_url"]
    print(f"  hero_main restored to default: {restored_hero['url']}")

    # Clean up test media
    provider.delete(stored.url, db=db)
    db.close()

    print("\n==================================================")
    print("ALL PERSISTENT STORAGE TESTS PASSED 100%! ✅")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
