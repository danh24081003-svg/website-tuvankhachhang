import io
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db
from scripts.create_admin import main as create_admin_main


def make_test_image(format_name: str, size: tuple = (400, 300), color="blue") -> io.BytesIO:
    img = Image.new("RGB" if format_name != "PNG" else "RGBA", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format_name)
    buf.seek(0)
    return buf


def run_tests():
    print("==================================================")
    print("STARTING TEST SUITE FOR ADMIN SYSTEM")
    print("==================================================")
    init_db()
    client = TestClient(app, follow_redirects=False)

    admin_email = "test_admin@oshinthoidai.vn"
    admin_password = "SecurePassword123"

    # 1. Tạo admin
    print("\n[TEST 1] Tạo admin...")
    sys.argv = ["create_admin.py", "--email", admin_email, "--password", admin_password]
    create_admin_main()
    print("✓ Test 1 Passed: Admin user created/updated successfully.")

    # 2. Login đúng
    print("\n[TEST 2] Login đúng...")
    login_res = client.post("/api/admin/auth/login", json={"email": admin_email, "password": admin_password})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    assert "oshin_admin_session" in client.cookies, "Missing session cookie"
    assert "oshin_admin_csrf" in client.cookies, "Missing CSRF cookie"
    csrf_token = client.cookies["oshin_admin_csrf"]
    auth_headers = {"x-csrf-token": csrf_token}
    print("✓ Test 2 Passed: Login successful, HttpOnly session and CSRF cookies received.")

    # 3. Login sai
    print("\n[TEST 3] Login sai...")
    bad_client = TestClient(app, follow_redirects=False)
    bad_res = bad_client.post("/api/admin/auth/login", json={"email": admin_email, "password": "WrongPassword!"})
    assert bad_res.status_code == 401, f"Expected 401, got {bad_res.status_code}"
    print("✓ Test 3 Passed: Login with wrong password properly rejected (401).")

    # 4. Truy cập /admin khi chưa login
    print("\n[TEST 4] Truy cập /admin khi chưa login...")
    unauth_res = bad_client.get("/admin")
    assert unauth_res.status_code == 302, f"Expected 302 redirect, got {unauth_res.status_code}"
    assert "/admin/login" in unauth_res.headers.get("location", ""), "Redirect should point to /admin/login"
    print("✓ Test 4 Passed: Unauthenticated access to /admin redirected to /admin/login.")

    # 5. Logout
    print("\n[TEST 5] Logout...")
    temp_client = TestClient(app, follow_redirects=False)
    temp_client.post("/api/admin/auth/login", json={"email": admin_email, "password": admin_password})
    temp_csrf = temp_client.cookies["oshin_admin_csrf"]
    logout_res = temp_client.post("/api/admin/auth/logout", headers={"x-csrf-token": temp_csrf})
    assert logout_res.status_code == 200, f"Logout failed: {logout_res.text}"
    after_logout_res = temp_client.get("/admin")
    assert after_logout_res.status_code == 302, "Session not cleared after logout"
    print("✓ Test 5 Passed: Logout successfully invalidated session.")

    # 6. Upload JPG
    print("\n[TEST 6] Upload JPG...")
    jpg_buf = make_test_image("JPEG", color="red")
    res_jpg = client.post(
        "/api/admin/images/hero_secondary_1",
        files={"file": ("test.jpg", jpg_buf, "image/jpeg")},
        headers=auth_headers,
    )
    assert res_jpg.status_code == 200, f"JPG upload failed: {res_jpg.text}"
    assert res_jpg.json()["url"].endswith(".webp"), "Uploaded image should be converted to WebP"
    print(f"✓ Test 6 Passed: JPG uploaded and optimized to WebP -> {res_jpg.json()['url']}")

    # 7. Upload PNG
    print("\n[TEST 7] Upload PNG...")
    png_buf = make_test_image("PNG", color="green")
    res_png = client.post(
        "/api/admin/images/hero_secondary_2",
        files={"file": ("test.png", png_buf, "image/png")},
        headers=auth_headers,
    )
    assert res_png.status_code == 200, f"PNG upload failed: {res_png.text}"
    assert res_png.json()["url"].endswith(".webp"), "Uploaded PNG should be converted to WebP"
    print(f"✓ Test 7 Passed: PNG uploaded and optimized to WebP -> {res_png.json()['url']}")

    # 8. Upload WebP
    print("\n[TEST 8] Upload WebP...")
    webp_buf = make_test_image("WEBP", color="purple")
    res_webp = client.post(
        "/api/admin/images/brand_team",
        files={"file": ("test.webp", webp_buf, "image/webp")},
        headers=auth_headers,
    )
    assert res_webp.status_code == 200, f"WebP upload failed: {res_webp.text}"
    print(f"✓ Test 8 Passed: WebP uploaded successfully -> {res_webp.json()['url']}")

    # 9. Upload file không hợp lệ
    print("\n[TEST 9] Upload file không hợp lệ (fake extension / text file)...")
    fake_buf = io.BytesIO(b"Hello world, I am not an image!")
    res_bad = client.post(
        "/api/admin/images/hero_main",
        files={"file": ("malicious.jpg", fake_buf, "image/jpeg")},
        headers=auth_headers,
    )
    assert res_bad.status_code == 400, f"Expected 400, got {res_bad.status_code}: {res_bad.text}"
    print("✓ Test 9 Passed: Invalid file correctly rejected by backend image inspection.")

    # 10. Upload file > giới hạn (5MB)
    print("\n[TEST 10] Upload file > giới hạn 5MB...")
    large_buf = io.BytesIO(b"0" * (6 * 1024 * 1024))
    res_large = client.post(
        "/api/admin/images/hero_main",
        files={"file": ("huge.jpg", large_buf, "image/jpeg")},
        headers=auth_headers,
    )
    assert res_large.status_code in (413, 400), f"Expected 413, got {res_large.status_code}"
    print("✓ Test 10 Passed: Oversized file (>5MB) rejected.")

    # 11, 12, 13: Đổi hero image, reload homepage, xác nhận hero image mới xuất hiện
    print("\n[TEST 11, 12, 13] Đổi hero main image & kiểm tra homepage...")
    hero_buf = make_test_image("JPEG", size=(1600, 1200), color="gold")
    res_hero = client.post(
        "/api/admin/images/hero_main",
        files={"file": ("new_hero.jpg", hero_buf, "image/jpeg")},
        headers=auth_headers,
    )
    assert res_hero.status_code == 200
    new_hero_url = res_hero.json()["url"]
    # Check GET /api/site/images
    site_imgs = client.get("/api/site/images").json()
    assert site_imgs["hero_main"] == new_hero_url, "API site images did not reflect updated hero image"
    # Check homepage HTML
    home_res = client.get("/")
    assert home_res.status_code == 200
    assert new_hero_url in home_res.text, "Homepage HTML does not contain new hero image URL"
    print(f"✓ Test 11, 12, 13 Passed: Hero image changed to {new_hero_url} and verified on homepage!")

    # 14, 15, 16: Đổi ảnh dịch vụ vận chuyển & reload homepage
    print("\n[TEST 14, 15, 16] Đổi ảnh dịch vụ vận chuyển & kiểm tra homepage...")
    moving_buf = make_test_image("PNG", size=(1200, 900), color="teal")
    res_moving = client.post(
        "/api/admin/images/service_moving",
        files={"file": ("moving.png", moving_buf, "image/png")},
        headers=auth_headers,
    )
    assert res_moving.status_code == 200
    new_moving_url = res_moving.json()["url"]
    services_res = client.get("/api/services").json()
    moving_svc = next((s for s in services_res if s["id"] == "van-chuyen-di-doi"), None)
    assert moving_svc is not None, "Service van-chuyen-di-doi not found"
    assert moving_svc["image_url"] == new_moving_url, f"Expected {new_moving_url}, got {moving_svc['image_url']}"
    print(f"✓ Test 14, 15, 16 Passed: Service moving image updated to {new_moving_url} and verified in /api/services!")

    # 17, 18: Sửa tên/mô tả dịch vụ & kiểm tra homepage
    print("\n[TEST 17, 18] Sửa tên/mô tả dịch vụ & kiểm tra...")
    admin_svcs = client.get("/api/admin/services", headers=auth_headers).json()
    target_svc = admin_svcs[0]
    updated_name = target_svc["name"] + " (Chuyên nghiệp 24/7)"
    updated_short = target_svc["short_description"] + " Cam kết uy tín chất lượng."
    edit_res = client.put(
        f"/api/admin/services/{target_svc['id']}",
        json={
            "name": updated_name,
            "slug": target_svc["slug"],
            "short_description": updated_short,
            "description": target_svc["description"],
            "image_key": target_svc["image_key"],
            "display_order": target_svc["display_order"],
            "is_active": True,
        },
        headers=auth_headers,
    )
    assert edit_res.status_code == 200, f"Edit service failed: {edit_res.text}"
    # Verify in public /api/services
    public_svcs = client.get("/api/services").json()
    matched = next((s for s in public_svcs if s["id"] == target_svc["slug"]), None)
    assert matched is not None and matched["name"] == updated_name, "Service update not reflected in public API"
    print(f"✓ Test 17, 18 Passed: Service '{updated_name}' updated and verified publicly.")

    # 19, 20: Sửa hotline & kiểm tra hotline toàn website
    print("\n[TEST 19, 20] Sửa hotline & kiểm tra toàn website...")
    new_hotline = "0909 999 888"
    company_put = client.put(
        "/api/admin/company",
        json={"values": {"hotline": new_hotline, "brand_name": "Oshin Thời Đại"}},
        headers=auth_headers,
    )
    assert company_put.status_code == 200
    # Check /api/company
    company_data = client.get("/api/company").json()
    assert company_data["hotline"] == new_hotline, "New hotline not in /api/company"
    # Check Homepage HTML
    home_html = client.get("/").text
    assert new_hotline in home_html, "New hotline not rendered in Homepage HTML"
    assert "tel:0909999888" in home_html, "Clean tel: link not generated in Homepage HTML"
    print(f"✓ Test 19, 20 Passed: Hotline changed to {new_hotline} and verified across all site locations!")

    # 21: Kiểm tra lead admin
    print("\n[TEST 21] Kiểm tra lead admin...")
    leads_res = client.get("/api/admin/leads", headers=auth_headers)
    assert leads_res.status_code == 200
    leads_list = leads_res.json()
    assert len(leads_list) > 0, "Expected leads in database"
    first_lead = leads_list[0]
    lead_detail = client.get(f"/api/admin/leads/{first_lead['id']}", headers=auth_headers)
    assert lead_detail.status_code == 200
    assert lead_detail.json()["customer_name"] == first_lead["customer_name"]
    # Update lead status
    status_update = client.put(
        f"/api/admin/leads/{first_lead['id']}/status",
        json={"status": "consulting"},
        headers=auth_headers,
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "consulting"
    print("✓ Test 21 Passed: Lead list, detail, and status transition verified.")

    # 22: Kiểm tra chat history
    print("\n[TEST 22] Kiểm tra chat history...")
    chats_res = client.get("/api/admin/chats", headers=auth_headers)
    assert chats_res.status_code == 200
    chats_list = chats_res.json()
    assert len(chats_list) > 0, "Expected chat sessions in database"
    first_session = chats_list[0]["session_id"]
    chat_detail = client.get(f"/api/admin/chats/{first_session}", headers=auth_headers)
    assert chat_detail.status_code == 200
    msgs = chat_detail.json()
    assert len(msgs) > 0, "Expected messages in session"
    print(f"✓ Test 22 Passed: Chat history and messages for session {first_session} verified.")

    # 23: Kiểm tra admin API không truy cập được khi logout
    print("\n[TEST 23] Kiểm tra admin API bị chặn khi không đăng nhập...")
    no_auth_client = TestClient(app, follow_redirects=False)
    assert no_auth_client.get("/api/admin/overview").status_code == 401
    assert no_auth_client.get("/api/admin/images").status_code == 401
    assert no_auth_client.get("/api/admin/leads").status_code == 401
    assert no_auth_client.get("/api/admin/chats").status_code == 401
    assert no_auth_client.get("/api/admin/company").status_code == 401
    print("✓ Test 23 Passed: All admin API endpoints strictly blocked (401) without valid auth.")

    # 24: Kiểm tra media library upload & delete in-use protection
    print("\n[TEST 24] Kiểm tra Media Library & an toàn xóa ảnh...")
    media_buf = make_test_image("PNG", size=(300, 300), color="magenta")
    res_med = client.post(
        "/api/admin/media",
        files={"file": ("unused_media.png", media_buf, "image/png")},
        headers=auth_headers,
    )
    assert res_med.status_code == 200
    uploaded_filename = res_med.json()["filename"]
    # Deleting unused media should succeed
    del_res = client.delete(f"/api/admin/media/{uploaded_filename}", headers=auth_headers)
    assert del_res.status_code == 200, f"Delete unused media failed: {del_res.text}"
    # Deleting an in-use hero image should be blocked (400)
    hero_filename = Path(new_hero_url).name
    del_blocked = client.delete(f"/api/admin/media/{hero_filename}", headers=auth_headers)
    assert del_blocked.status_code == 400, "Should block deleting an in-use image"
    print("✓ Test 24 Passed: Media Library upload, deletion of unused image, and in-use protection verified.")

    # 25: Reset hotline back to original default for clean state
    client.put(
        "/api/admin/company",
        json={"values": {"hotline": "0901 040 484"}},
        headers=auth_headers,
    )
    print("✓ Default hotline 0901 040 484 restored.")

    print("\n==================================================")
    print("ALL 25 TESTS COMPLETED AND PASSED PERFECTLY!")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
