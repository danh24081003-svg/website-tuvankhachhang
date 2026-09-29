import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.main import app
from app.models import AdminUser
from app.services.auth_service import hash_password

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

client = TestClient(app)

def run_tests():
    print("=== STARTING ADMIN NAVIGATION & ACCESS TEST SUITE ===")
    init_db()
    db = SessionLocal()

    # 1. Test Homepage Navbar Admin Elements
    print("\n1. Testing Homepage header admin elements...")
    home_res = client.get("/")
    assert home_res.status_code == 200
    html = home_res.text
    assert 'class="nav-admin-btn"' in html, "nav-admin-btn missing in homepage!"
    assert 'href="/admin"' in html, 'href="/admin" missing in nav-admin-btn!'
    assert 'aria-label="Đăng nhập quản trị"' in html, "aria-label missing in nav-admin-btn!"
    assert 'title="Đăng nhập quản trị"' in html, "title tooltip missing in nav-admin-btn!"
    assert 'class="nav-admin-link"' in html, "nav-admin-link missing for mobile menu!"
    assert 'target="_blank"' not in html.split('nav-admin-btn')[1].split('>')[0], "nav-admin-btn must NOT have target=_blank!"
    print("  Homepage nav-admin-btn & nav-admin-link: PASS ✅")

    # 2. Test Other Pages Header
    print("\n2. Testing /dich-vu, /dich-vu/{slug}, and 404 headers...")
    for path in ["/dich-vu", "/dich-vu/ve-sinh-cong-nghiep", "/non-existent-page-404"]:
        res = client.get(path)
        assert res.status_code in (200, 404)
        assert 'class="nav-admin-btn"' in res.text, f"nav-admin-btn missing in {path}!"
        assert 'class="nav-admin-link"' in res.text, f"nav-admin-link missing in {path}!"
    print("  All site pages header admin access: PASS ✅")

    # 3. Test /admin/login Page Back Link
    print("\n3. Testing /admin/login page back to home link...")
    login_page_res = client.get("/admin/login")
    assert login_page_res.status_code == 200
    login_html = login_page_res.text
    assert 'href="/"' in login_html, "Back to home link href=/ missing in /admin/login!"
    assert "Quay lại trang chủ" in login_html, "Text 'Quay lại trang chủ' missing in /admin/login!"
    assert 'target="_blank"' not in login_html.split('back-home-link')[1].split('>')[0], "Back link must open in same tab!"
    print("  /admin/login back to home in same tab: PASS ✅")

    # 4. Test /admin Protection (Unauthenticated -> Redirect /admin/login)
    print("\n4. Testing /admin protection without session...")
    unauth_admin_res = client.get("/admin", follow_redirects=False)
    assert unauth_admin_res.status_code == 302, f"Expected 302 redirect, got {unauth_admin_res.status_code}"
    assert unauth_admin_res.headers.get("location") == "/admin/login"
    print("  /admin unauthenticated redirects to /admin/login: PASS ✅")

    # 5. Test Admin Login -> /admin Dashboard & 'Xem website' link in same tab
    print("\n5. Testing Admin Login & Dashboard 'Xem website' link...")
    admin = db.scalars(select(AdminUser).where(AdminUser.email == "admin@oshin.vn")).first()
    if not admin:
        admin = AdminUser(email="admin@oshin.vn", password_hash=hash_password("Admin@123456"), is_active=True)
        db.add(admin)
        db.commit()
        db.refresh(admin)

    login_res = client.post("/api/admin/auth/login", json={"email": "admin@oshin.vn", "password": "Admin@123456"})
    assert login_res.status_code == 200
    cookies = login_res.cookies

    auth_admin_res = client.get("/admin", cookies=cookies, follow_redirects=False)
    assert auth_admin_res.status_code == 200, f"Authenticated /admin returned {auth_admin_res.status_code}"
    admin_html = auth_admin_res.text
    assert "preview-site-link" in admin_html
    assert 'href="/"' in admin_html
    assert 'target="_blank"' not in admin_html.split('preview-site-link')[0].split('<a')[-1], "'Xem website' link must NOT have target=_blank!"
    print("  Authenticated /admin loads and has 'Xem website' in same tab: PASS ✅")

    # 6. Test Admin Logout
    print("\n6. Testing Admin Logout...")
    csrf_token = cookies.get("oshin_admin_csrf", "")
    logout_res = client.post("/api/admin/auth/logout", cookies=cookies, headers={"x-csrf-token": csrf_token})
    assert logout_res.status_code == 200

    after_logout_res = client.get("/admin", cookies=cookies, follow_redirects=False)
    assert after_logout_res.status_code == 302, "Expected 302 redirect after logout!"
    assert after_logout_res.headers.get("location") == "/admin/login"
    print("  Logout terminates session and /admin redirects to /admin/login: PASS ✅")

    db.close()
    print("\n==================================================")
    print("ALL ADMIN ACCESS & NAVIGATION TESTS PASSED 100%! ✅")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
