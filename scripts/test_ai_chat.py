import json
import sys
import urllib.request
import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE = "http://127.0.0.1:8080"


def send_chat(session_id: str, message: str, service_slug: str | None = None):
    url = f"{API_BASE}/api/chat"
    payload = {
        "session_id": session_id,
        "message": message,
        "service_slug": service_slug,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_suite():
    print("=== KIỂM TRA STATUS AI ===")
    req = urllib.request.Request(f"{API_BASE}/api/ai/status")
    with urllib.request.urlopen(req) as resp:
        status_data = json.loads(resp.read().decode("utf-8"))
        print("AI Status:", json.dumps(status_data, ensure_ascii=False, indent=2))
        assert "provider" in status_data
        assert "model" in status_data
        assert "status" in status_data

    # Test 1: "Xin chào"
    print("\n--- Test 1: 'Xin chào' ---")
    sess1 = f"test-sess-{uuid.uuid4().hex[:8]}"
    resp1 = send_chat(sess1, "Xin chào")
    print("Reply:", resp1["reply"])
    print("Quick actions:", resp1.get("quick_actions"))
    assert "em" in resp1["reply"] or "anh/chị" in resp1["reply"]

    # Test 2: "Tôi muốn vệ sinh nhà."
    print("\n--- Test 2: 'Tôi muốn vệ sinh nhà.' ---")
    sess2 = f"test-sess-{uuid.uuid4().hex[:8]}"
    resp2 = send_chat(sess2, "Tôi muốn vệ sinh nhà.")
    print("Reply:", resp2["reply"])
    print("Service context:", resp2.get("service_context"))
    assert "vệ sinh" in resp2["reply"].lower()

    # Test 3: "Tôi cần chuyển đồ từ Ninh Kiều sang Cái Răng."
    print("\n--- Test 3: 'Tôi cần chuyển đồ từ Ninh Kiều sang Cái Răng.' ---")
    sess3 = f"test-sess-{uuid.uuid4().hex[:8]}"
    resp3 = send_chat(sess3, "Tôi cần chuyển đồ từ Ninh Kiều sang Cái Răng.")
    print("Reply:", resp3["reply"])
    print("Service context:", resp3.get("service_context"))
    assert "chuyển" in resp3["reply"].lower()

    # Test 4: "Giá vệ sinh bao nhiêu?"
    print("\n--- Test 4: 'Giá vệ sinh bao nhiêu?' ---")
    sess4 = f"test-sess-{uuid.uuid4().hex[:8]}"
    resp4 = send_chat(sess4, "Giá vệ sinh bao nhiêu?", service_slug="ve-sinh-cong-nghiep")
    print("Reply:", resp4["reply"])
    # Verify no fake price hallucination (e.g. 500k, 20.000đ)
    assert not any(c in resp4["reply"] for c in ["500.000", "20.000đ", "100.000"])

    # Test 5: Lead creation when providing phone number
    print("\n--- Test 5: Customer phone and lead creation ---")
    resp5 = send_chat(sess2, "Số điện thoại của tôi là 0918123456, nhà khoảng 120m2 ở Cái Khế")
    print("Reply:", resp5["reply"])
    print("Lead created:", resp5.get("lead_created"))
    print("Lead ID:", resp5.get("lead_id"))
    assert resp5.get("lead_created") is True or resp5.get("lead_id") is not None

    print("\n>>> TẤT CẢ 5 KIỂM TRA CHATBOT VÀ STATUS ĐỀU THÀNH CÔNG! <<<")


if __name__ == "__main__":
    test_suite()
