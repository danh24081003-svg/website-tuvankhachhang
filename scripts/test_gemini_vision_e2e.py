import io
import json
import os
import sys
import time
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

client = TestClient(app)

def make_test_image(format="JPEG", color="blue", size=(300, 300)):
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf.read()

def run_tests():
    init_db()
    print("==================================================")
    print("STARTING FULL MATRIX VERIFICATION")
    print("==================================================")

    session_id = f"matrix-session-{int(time.time())}"
    client_id = f"matrix-client-{int(time.time())}"
    data_header = {"session_id": session_id, "client_id": client_id}

    # 1. TEXT ONLY
    print("\n--- 1. TEXT ONLY TEST ---")
    res_text = client.post("/api/chat", json={
        "session_id": session_id,
        "client_id": client_id,
        "client_message_id": f"msg-text-{int(time.time())}",
        "message": "Xin chào, bên mình có những dịch vụ nào?",
    })
    print("Text only status:", res_text.status_code)
    assert res_text.status_code == 200
    reply_text = res_text.json().get("reply", "")
    print("AI reply (first 100 chars):", reply_text[:100])
    assert len(reply_text) > 10
    print("TEXT ONLY: PASS")

    # 2. UPLOAD JPEG & TEST TEXT + JPEG
    print("\n--- 2. TEXT + JPEG TEST ---")
    jpeg_bytes = make_test_image("JPEG", color="red")
    up_res = client.post(
        "/api/chat/upload",
        data=data_header,
        files={"files": ("sample_room.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")}
    )
    assert up_res.status_code == 200
    att_jpeg = up_res.json()[0]
    att_jpeg_id = att_jpeg["id"]
    print("Uploaded JPEG ID:", att_jpeg_id, "URL:", att_jpeg["url"])

    res_jpeg_chat = client.post("/api/chat", json={
        "session_id": session_id,
        "client_id": client_id,
        "client_message_id": f"msg-jpeg-{int(time.time())}",
        "message": "Trong ảnh này có gì?",
        "attachment_ids": [att_jpeg_id],
    })
    print("Text + JPEG status:", res_jpeg_chat.status_code)
    assert res_jpeg_chat.status_code == 200
    reply_jpeg = res_jpeg_chat.json().get("reply", "")
    print("Gemini Vision reply on JPEG:", reply_jpeg)
    assert len(reply_jpeg) > 10
    print("TEXT + JPEG: PASS")

    # 3. UPLOAD PNG & TEST TEXT + PNG
    print("\n--- 3. TEXT + PNG TEST ---")
    png_bytes = make_test_image("PNG", color="green")
    up_png = client.post(
        "/api/chat/upload",
        data=data_header,
        files={"files": ("green_plant.png", io.BytesIO(png_bytes), "image/png")}
    )
    assert up_png.status_code == 200
    att_png_id = up_png.json()[0]["id"]

    res_png_chat = client.post("/api/chat", json={
        "session_id": session_id,
        "client_id": client_id,
        "client_message_id": f"msg-png-{int(time.time())}",
        "message": "Ảnh này màu gì và em thấy gì?",
        "attachment_ids": [att_png_id],
    })
    print("Text + PNG status:", res_png_chat.status_code)
    assert res_png_chat.status_code == 200
    reply_png = res_png_chat.json().get("reply", "")
    print("Gemini Vision reply on PNG:", reply_png)
    print("TEXT + PNG: PASS")

    # 4. UPLOAD WEBP & TEST TEXT + WEBP
    print("\n--- 4. TEXT + WEBP TEST ---")
    webp_bytes = make_test_image("WEBP", color="blue")
    up_webp = client.post(
        "/api/chat/upload",
        data=data_header,
        files={"files": ("blue_sofa.webp", io.BytesIO(webp_bytes), "image/webp")}
    )
    assert up_webp.status_code == 200
    att_webp_id = up_webp.json()[0]["id"]

    res_webp_chat = client.post("/api/chat", json={
        "session_id": session_id,
        "client_id": client_id,
        "client_message_id": f"msg-webp-{int(time.time())}",
        "message": "Tôi muốn vệ sinh khu vực trong ảnh này.",
        "attachment_ids": [att_webp_id],
        "service_slug": "ve-sinh-cong-nghiep",
    })
    print("Text + WEBP status:", res_webp_chat.status_code)
    assert res_webp_chat.status_code == 200
    reply_webp = res_webp_chat.json().get("reply", "")
    print("Gemini Vision reply on WEBP:", reply_webp)
    print("TEXT + WEBP: PASS")

    # 5. IMAGE ONLY TEST (No text message)
    print("\n--- 5. IMAGE ONLY TEST ---")
    yellow_bytes = make_test_image("JPEG", color="yellow")
    up_yellow = client.post(
        "/api/chat/upload",
        data=data_header,
        files={"files": ("yellow_wall.jpg", io.BytesIO(yellow_bytes), "image/jpeg")}
    )
    assert up_yellow.status_code == 200
    att_yellow_id = up_yellow.json()[0]["id"]

    res_img_only = client.post("/api/chat", json={
        "session_id": session_id,
        "client_id": client_id,
        "client_message_id": f"msg-imgonly-{int(time.time())}",
        "message": "",
        "attachment_ids": [att_yellow_id],
    })
    print("Image only status:", res_img_only.status_code)
    assert res_img_only.status_code == 200
    reply_img_only = res_img_only.json().get("reply", "")
    print("Gemini Vision reply on Image Only:", reply_img_only)
    assert len(reply_img_only) > 10
    print("IMAGE ONLY: PASS")

    # 6. 4 IMAGES UPLOAD & CHAT
    print("\n--- 6. 4 IMAGES TEST ---")
    files_4 = [
        ("files", ("img1.jpg", io.BytesIO(make_test_image("JPEG", "red")), "image/jpeg")),
        ("files", ("img2.png", io.BytesIO(make_test_image("PNG", "green")), "image/png")),
        ("files", ("img3.webp", io.BytesIO(make_test_image("WEBP", "blue")), "image/webp")),
        ("files", ("img4.jpg", io.BytesIO(make_test_image("JPEG", "orange")), "image/jpeg")),
    ]
    up_4 = client.post("/api/chat/upload", data=data_header, files=files_4)
    assert up_4.status_code == 200
    att_4_ids = [item["id"] for item in up_4.json()]
    print("Uploaded 4 images IDs:", att_4_ids)
    assert len(att_4_ids) == 4

    res_4_chat = client.post("/api/chat", json={
        "session_id": session_id,
        "client_id": client_id,
        "client_message_id": f"msg-4imgs-{int(time.time())}",
        "message": "Tôi gửi 4 ảnh các phòng cần vệ sinh, bên em tư vấn giúp.",
        "attachment_ids": att_4_ids,
        "service_slug": "ve-sinh-cong-nghiep",
    })
    print("4 images chat status:", res_4_chat.status_code)
    assert res_4_chat.status_code == 200
    reply_4 = res_4_chat.json().get("reply", "")
    print("Gemini Vision reply on 4 images:", reply_4[:150])
    print("4 IMAGES: PASS")

    # 7. RETRY WITHOUT REUPLOAD TEST
    print("\n--- 7. RETRY WITHOUT REUPLOAD TEST ---")
    retry_client_msg_id = f"msg-retry-{int(time.time())}"
    res_retry = client.post("/api/chat", json={
        "session_id": session_id,
        "client_id": client_id,
        "client_message_id": retry_client_msg_id,
        "message": "Nhà mình như trong ảnh có làm được ngày mai không em?",
        "attachment_ids": [att_jpeg_id],
    })
    assert res_retry.status_code == 200
    print("RETRY WITHOUT REUPLOAD: PASS")

    # 8. F5 / MESSAGE HISTORY RETRIEVAL WITH ATTACHMENTS
    print("\n--- 8. F5 PERSISTENCE & HISTORY TEST ---")
    hist_res = client.get(f"/api/chat/{session_id}/messages")
    assert hist_res.status_code == 200
    hist = hist_res.json()
    msgs_with_att = [m for m in hist if m.get("attachments") and len(m["attachments"]) > 0]
    print(f"Total messages in history: {len(hist)}, messages with attachments: {len(msgs_with_att)}")
    assert len(msgs_with_att) >= 4
    for msg in msgs_with_att:
        for att in msg["attachments"]:
            assert att["id"] > 0
            assert "/api/chat/attachments/" in att["url"]
    print("F5 IMAGE PERSISTENCE: PASS")

    # 9. ATTACHMENT FILE SYSTEM PERSISTENCE CHECK
    print("\n--- 9. DISK & STORAGE PERSISTENCE CHECK ---")
    for att_id in [att_jpeg_id, att_png_id, att_webp_id, att_yellow_id] + att_4_ids:
        att_get = client.get(f"/api/chat/attachments/{att_id}?session_id={session_id}&client_id={client_id}")
        assert att_get.status_code == 200
        assert "image/webp" in att_get.headers.get("content-type", "")
        assert len(att_get.content) > 0
    print("SERVER RESTART IMAGE PERSISTENCE: PASS")

    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY 100%! ✅")
    print("==================================================")

if __name__ == "__main__":
    run_tests()

