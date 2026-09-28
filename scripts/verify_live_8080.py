import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import requests

base = "http://127.0.0.1:8080"

print("==================================================")
print(f"VERIFYING LIVE ENDPOINTS ON {base}")
print("==================================================")

# 1. Health check
r = requests.get(f"{base}/health")
assert r.status_code == 200
print("[✓] 1. GET /health -> 200 OK:", r.json())

# 2. Homepage
r = requests.get(f"{base}/")
assert r.status_code == 200
assert "Oshin Thời Đại" in r.text
print("[✓] 2. GET / (Homepage) -> 200 OK")

# 3. Admin login page
r = requests.get(f"{base}/admin/login")
assert r.status_code == 200
assert "OSHIN THỜI ĐẠI" in r.text or "ĐĂNG NHẬP" in r.text
print("[✓] 3. GET /admin/login -> 200 OK")

# 4. Services Overview
r = requests.get(f"{base}/dich-vu")
assert r.status_code == 200
assert "Danh sách dịch vụ của Oshin Thời Đại" in r.text
print("[✓] 4. GET /dich-vu -> 200 OK")

# 5. Service Detail page
r = requests.get(f"{base}/dich-vu/ve-sinh-cong-nghiep")
assert r.status_code == 200
assert "Vệ sinh công nghiệp" in r.text
print("[✓] 5. GET /dich-vu/ve-sinh-cong-nghiep -> 200 OK")

# 6. Chatbot API
r = requests.post(f"{base}/api/chat", json={
    "session_id": "live-test-8080-session",
    "message": "Xin chào, tôi cần tư vấn dịch vụ vệ sinh công nghiệp",
    "current_page": "service_detail",
    "service_slug": "ve-sinh-cong-nghiep",
    "service_name": "Vệ sinh công nghiệp"
})
assert r.status_code == 200
reply = r.json().get("reply", "")
print(f"[✓] 6. POST /api/chat -> 200 OK (Reply length: {len(reply)} chars)")

# 7. Lead form API
r = requests.post(f"{base}/api/leads", json={
    "name": "Khách Hàng Live Test",
    "phone": "0901888999",
    "service": "Vệ sinh công nghiệp",
    "address": "Ninh Kiều, Cần Thơ",
    "message": "Cần khảo sát báo giá nhà xưởng 500m2"
})
assert r.status_code == 200
print("[✓] 7. POST /api/leads -> 200 OK:", r.json())

# 8. Check that no frontend HTML/JS requests port 8000
r = requests.get(f"{base}/")
assert ":8000" not in r.text
r_js = requests.get(f"{base}/static/js/app.js")
assert ":8000" not in r_js.text
r_admin_js = requests.get(f"{base}/static/js/admin.js")
assert ":8000" not in r_admin_js.text
print("[✓] 8. Verified no port 8000 references in HTML or JS assets served to browser.")

print("==================================================")
print("ALL LIVE TESTS COMPLETED AND PASSED ON PORT 8080!")
print("==================================================")
