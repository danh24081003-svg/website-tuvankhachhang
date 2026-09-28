import io
import json
import sys
import time
import urllib.request
import urllib.parse
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://website-tuvankhachhang.vercel.app"
print(f"Testing live production at: {BASE_URL}")

def req(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    if "User-Agent" not in headers:
        headers["User-Agent"] = "LiveProductionTester/1.0"
    body = None
    if data is not None:
        if isinstance(data, dict):
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, bytes):
            body = data
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=35) as resp:
            content = resp.read()
            return resp.status, content, resp.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers
    except Exception as e:
        return 500, str(e).encode(), {}

# 1. Health check
status, body, _ = req(f"{BASE_URL}/health")
print(f"1. /health -> Status: {status}, Response: {body.decode(errors='ignore')}")
assert status == 200, f"Health failed with {status}"

# 2. Homepage
status, body, _ = req(f"{BASE_URL}/")
html = body.decode(errors='ignore')
print(f"2. Homepage / -> Status: {status}, Length: {len(html)} bytes, Title in HTML: {'Oshin' in html}")
assert status == 200

# 3. Services Index
status, body, _ = req(f"{BASE_URL}/dich-vu")
print(f"3. /dich-vu -> Status: {status}, Title in HTML: {'Dịch vụ' in body.decode(errors='ignore')}")
assert status == 200

# 4. 7 Service detail pages
services = [
    "ve-sinh-cong-nghiep", "van-chuyen-di-doi", "cung-cap-quan-ly-lao-dong",
    "cham-soc-cay-canh", "giup-viec", "diet-con-trung", "trang-tri-sua-chua"
]
for s in services:
    status, body, _ = req(f"{BASE_URL}/dich-vu/{s}")
    print(f"  - /dich-vu/{s} -> Status: {status}")
    assert status == 200, f"Service {s} failed with {status}"

# 5. Admin Login Page
status, body, _ = req(f"{BASE_URL}/admin/login")
print(f"5. /admin/login -> Status: {status}")
assert status == 200

# 6. Static Asset
status, body, _ = req(f"{BASE_URL}/static/css/style.css")
print(f"6. Static CSS -> Status: {status}, Length: {len(body)} bytes")
assert status == 200

# 7. AI Status API
status, body, _ = req(f"{BASE_URL}/api/ai/status")
print(f"7. /api/ai/status -> Status: {status}, Response: {body.decode(errors='ignore')}")
assert status == 200

# 8. Text Chatbot
session_id = f"live-test-session-{int(time.time())}"
status, body, _ = req(
    f"{BASE_URL}/api/chat",
    method="POST",
    data={"message": "Xin chào, bên mình có vệ sinh nhà ở không?", "session_id": session_id}
)
chat_res = json.loads(body.decode(errors='ignore'))
print(f"8. Text Chat -> Status: {status}, Reply: {chat_res.get('reply', '')[:100]}...")
assert status == 200

# 9. Lead creation
status, body, _ = req(
    f"{BASE_URL}/api/leads",
    method="POST",
    data={
        "name": "Khách Test Live",
        "phone": "0987654321",
        "service": "ve-sinh-cong-nghiep",
        "address": "Ninh Kiều, Cần Thơ",
        "message": "Cần tư vấn vệ sinh nhà 100m2",
        "session_id": session_id
    }
)
print(f"9. Lead Creation -> Status: {status}, Response: {body.decode(errors='ignore')}")
assert status == 200

# 10. Chat History
status, body, _ = req(f"{BASE_URL}/api/chat/{session_id}/messages")
hist_res = json.loads(body.decode(errors='ignore'))
print(f"10. Chat History -> Status: {status}, Messages count: {len(hist_res)}")
assert status == 200
assert len(hist_res) >= 2

# 11. Image Upload + Gemini Vision test
img = Image.new("RGB", (200, 200), color="blue")
buf = io.BytesIO()
img.save(buf, format="JPEG")
img_bytes = buf.getvalue()

boundary = "----WebKitFormBoundaryLiveTest123"
body_parts = [
    f"--{boundary}".encode(),
    b'Content-Disposition: form-data; name="session_id"',
    b"",
    session_id.encode(),
    f"--{boundary}".encode(),
    b'Content-Disposition: form-data; name="files"; filename="blue_test.jpg"',
    b"Content-Type: image/jpeg",
    b"",
    img_bytes,
    f"--{boundary}--".encode(),
    b""
]
multipart_body = b"\r\n".join(body_parts)
status, body, _ = req(
    f"{BASE_URL}/api/chat/upload",
    method="POST",
    data=multipart_body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
)
upload_res = json.loads(body.decode(errors='ignore'))
print(f"11. Image Upload -> Status: {status}, Attachments: {upload_res}")
assert status == 200
att_id = upload_res[0]["id"]

# 12. Multimodal Chat (Vision)
status, body, _ = req(
    f"{BASE_URL}/api/chat",
    method="POST",
    data={
        "message": "Tôi gửi hình này, bạn xem trong hình có màu gì?",
        "session_id": session_id,
        "attachment_ids": [att_id]
    }
)
vision_res = json.loads(body.decode(errors='ignore'))
print(f"12. Multimodal Vision -> Status: {status}, AI Reply: {vision_res.get('reply', '')[:100]}...")
assert status == 200

print("\n==================================================")
print("ALL LIVE PRODUCTION TESTS PASSED 100%! ✅")
print("==================================================")
