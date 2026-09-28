import json
import sys
import urllib.request
import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE = "http://127.0.0.1:8080"


def send_chat(session_id: str, message: str, service_slug: str | None = None, current_page: str = "home"):
    url = f"{API_BASE}/api/chat"
    payload = {
        "session_id": session_id,
        "message": message,
        "service_slug": service_slug,
        "current_page": current_page,
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


def run_behavior_tests():
    print("=" * 60)
    print("BẮT ĐẦU KIỂM THỬ 8 TÌNH HUỐNG BEHAVIOR THEO YÊU CẦU")
    print("=" * 60)

    # ----------------------------------------------------
    # TEST 1: Khách hỏi "bên mình có vệ sinh nhà không"
    # ----------------------------------------------------
    print("\n--- TEST 1: 'bên mình có vệ sinh nhà không' ---")
    sess1 = f"behav-sess-{uuid.uuid4().hex[:8]}"
    r1 = send_chat(sess1, "bên mình có vệ sinh nhà không")
    reply1 = r1["reply"]
    print("BOT:", reply1)
    # Phải trả lời có/nhận làm trước
    assert any(w in reply1.lower() for w in ["dạ có", "bên em có", "có ạ", "có nhận"])
    # Không được dồn dập hỏi họ tên, sđt, địa chỉ
    assert not any(w in reply1.lower() for w in ["họ và tên", "xin số điện thoại", "cho em xin sđt", "1.", "2."])
    print("✓ Test 1 Passed: Trả lời có trước, gợi mở nhẹ nhàng, không hỏi form.")

    # ----------------------------------------------------
    # TEST 2: Khách nối tiếp "nhà 100m2"
    # ----------------------------------------------------
    print("\n--- TEST 2: 'nhà 100m2' ---")
    r2 = send_chat(sess1, "nhà 100m2")
    reply2 = r2["reply"]
    print("BOT:", reply2)
    # Nhận diện 100m2 và tư vấn phương án, KHÔNG lập tức đòi SĐT
    assert any(w in reply2.lower() for w in ["100m", "100 m"])
    assert not any(w in reply2.lower() for w in ["xin số điện thoại", "cho em xin sđt", "số điện thoại của"])
    print("✓ Test 2 Passed: Ghi nhận 100m2, tiếp tục tư vấn tự nhiên, không ép xin SĐT.")

    # ----------------------------------------------------
    # TEST 3: Khách nói "tôi chỉ hỏi tham khảo"
    # ----------------------------------------------------
    print("\n--- TEST 3: 'tôi chỉ hỏi tham khảo' ---")
    sess3 = f"behav-sess-{uuid.uuid4().hex[:8]}"
    r3 = send_chat(sess3, "tôi chỉ hỏi tham khảo")
    reply3 = r3["reply"]
    print("BOT:", reply3)
    # Thoải mái cho khách tham khảo, KHÔNG xin SĐT
    assert any(w in reply3.lower() for w in ["thoải mái", "tham khảo", "dạ được", "hỗ trợ thông tin"])
    assert not any(w in reply3.lower() for w in ["xin số điện thoại", "cho em xin sđt", "để lại sđt"])
    print("✓ Test 3 Passed: Tôn trọng việc tham khảo, tuyệt đối không xin SĐT.")

    # ----------------------------------------------------
    # TEST 4: Khách hỏi "giá bao nhiêu"
    # ----------------------------------------------------
    print("\n--- TEST 4: 'giá bao nhiêu' ---")
    sess4 = f"behav-sess-{uuid.uuid4().hex[:8]}"
    r4 = send_chat(sess4, "giá bao nhiêu", service_slug="ve-sinh-cong-nghiep")
    reply4 = r4["reply"]
    print("BOT:", reply4)
    # Không bịa giá (không đưa 500k, 1 triệu, 20.000đ/m2)
    assert not any(c in reply4 for c in ["500.000", "20.000", "1.000.000", "300.000"])
    # Giải thích chi phí phụ thuộc hiện trạng/hạng mục
    assert any(w in reply4.lower() for w in ["phụ thuộc", "hiện trạng", "hạng mục", "khảo sát"])
    print("✓ Test 4 Passed: Không tự ý bịa giá, giải thích chi phí rõ ràng.")

    # ----------------------------------------------------
    # TEST 5: Khách hỏi "có làm chủ nhật không"
    # ----------------------------------------------------
    print("\n--- TEST 5: 'có làm chủ nhật không' ---")
    sess5 = f"behav-sess-{uuid.uuid4().hex[:8]}"
    r5 = send_chat(sess5, "có làm chủ nhật không")
    reply5 = r5["reply"]
    print("BOT:", reply5)
    # Trả lời thẳng vào câu hỏi Chủ nhật
    assert any(w in reply5.lower() for w in ["chủ nhật", "thứ 7", "cuối tuần", "lịch"])
    assert not any(w in reply5.lower() for w in ["cho em xin địa chỉ", "xin số điện thoại"])
    print("✓ Test 5 Passed: Trả lời trực tiếp câu hỏi về Chủ nhật, không đòi thông tin.")

    # ----------------------------------------------------
    # TEST 6: Khách nói "cảm ơn"
    # ----------------------------------------------------
    print("\n--- TEST 6: 'cảm ơn' ---")
    sess6 = f"behav-sess-{uuid.uuid4().hex[:8]}"
    r6 = send_chat(sess6, "cảm ơn em")
    reply6 = r6["reply"]
    print("BOT:", reply6)
    # Lịch sự, vui vẻ, KHÔNG xin SĐT
    assert any(w in reply6.lower() for w in ["không có gì", "dạ không", "sẵn sàng", "chúc anh/chị"])
    assert not any(w in reply6.lower() for w in ["xin số điện thoại", "cho em xin sđt", "để lại sđt"])
    print("✓ Test 6 Passed: Kết thúc tự nhiên, lịch sự, không xin SĐT.")

    # ----------------------------------------------------
    # TEST 7: Khách: "Tôi muốn đặt vệ sinh nhà."
    # ----------------------------------------------------
    print("\n--- TEST 7: 'Tôi muốn đặt vệ sinh nhà.' ---")
    sess7 = f"behav-sess-{uuid.uuid4().hex[:8]}"
    r7 = send_chat(sess7, "Tôi muốn đặt vệ sinh nhà.")
    reply7 = r7["reply"]
    print("BOT:", reply7)
    # Bắt đầu tiếp nhận nhu cầu tự nhiên từng bước
    assert any(w in reply7.lower() for w in ["sẵn lòng", "tiếp nhận", "hỗ trợ", "vệ sinh"])
    print("✓ Test 7 Passed: Tiếp nhận nhu cầu đặt dịch vụ tự nhiên từng bước.")

    # ----------------------------------------------------
    # TEST 8: Khách: "Tôi cần vệ sinh nhà 100m2 ở Ninh Kiều vào thứ 7, SĐT 0918123456."
    # ----------------------------------------------------
    print("\n--- TEST 8: Khách cung cấp đầy đủ thông tin ---")
    sess8 = f"behav-sess-{uuid.uuid4().hex[:8]}"
    r8 = send_chat(sess8, "Tôi cần vệ sinh nhà 100m2 ở Ninh Kiều vào thứ 7, SĐT 0918123456.")
    reply8 = r8["reply"]
    print("BOT:", reply8)
    # Bot KHÔNG được hỏi lại: diện tích, khu vực, thời gian, sđt
    lower_r8 = reply8.lower()
    assert "diện tích bao nhiêu" not in lower_r8
    assert "ở đâu" not in lower_r8 and "khu vực nào" not in lower_r8
    assert "ngày nào" not in lower_r8 and "khi nào" not in lower_r8
    assert "xin số điện thoại" not in lower_r8 and "cho em xin sđt" not in lower_r8
    assert r8.get("lead_created") is True or r8.get("lead_id") is not None
    print("✓ Test 8 Passed: Nhận diện toàn bộ thông tin đã có, không hỏi lại, tạo Lead thành công.")

    print("\n" + "=" * 60)
    print(">>> TẤT CẢ 8 TEST BEHAVIOR ĐỀU ĐẠT CHUẨN XUẤT SẮC! <<<")
    print("=" * 60)


if __name__ == "__main__":
    run_behavior_tests()
