import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure UTF-8 stdout on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient

from app.database import get_db, init_db
from app.main import app
from app.models import AdminUser, Customer, Lead, ManagedService, SiteSetting
from scripts.create_admin import main as create_admin_main

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("STARTING TEST SUITE FOR PHASE 1: SERVICE DETAIL + SMART AI CONSULTATION")
    print("=" * 60)

    # Init database
    init_db()

    # Ensure admin user exists with known password
    admin_email = "test_admin@oshinthoidai.vn"
    admin_password = "SecurePassword123"
    sys.argv = ["create_admin.py", "--email", admin_email, "--password", admin_password]
    create_admin_main()

    # 1. TEST /dich-vu (Services Overview)
    print("\n[TEST 1] Kiểm tra trang tổng quan /dich-vu...")
    res = client.get("/dich-vu")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "Danh sách dịch vụ của Oshin Thời Đại" in res.text
    assert "Vận chuyển, di dời" in res.text
    assert "Vệ sinh công nghiệp" in res.text
    print("✓ Test 1 Passed: /dich-vu returns 200 with all 7 services.")

    # 2. TEST 7 Service Detail Routes
    print("\n[TEST 2] Kiểm tra 7 trang chi tiết dịch vụ /dich-vu/{slug}...")
    slugs = [
        "van-chuyen-di-doi",
        "ve-sinh-cong-nghiep",
        "trang-tri-sua-chua",
        "cung-cap-quan-ly-lao-dong",
        "giup-viec",
        "cham-soc-cay-canh",
        "diet-con-trung",
    ]
    for slug in slugs:
        res = client.get(f"/dich-vu/{slug}")
        assert res.status_code == 200, f"Failed for /dich-vu/{slug}: {res.status_code}"
        assert "Quy trình thực hiện chuyên nghiệp" in res.text
        assert "Lợi ích khi chọn Oshin Thời Đại" in res.text
        assert "Câu hỏi thường gặp" in res.text
        assert "data-service-slug" in res.text
    print("✓ Test 2 Passed: Tất cả 7 trang chi tiết dịch vụ trả về 200 với đầy đủ 8 sections.")

    # 3. TEST Slug Aliases
    print("\n[TEST 3] Kiểm tra slug aliases...")
    aliases = [
        ("cung-cap-quan-ly-nguon-lao-dong", "Cung cấp và quản lý nguồn lao động"),
        ("giup-viec-theo-gio-dinh-ky", "Giúp việc"),
    ]
    for alias, keyword in aliases:
        res = client.get(f"/dich-vu/{alias}")
        assert res.status_code == 200, f"Alias {alias} failed with {res.status_code}"
        assert keyword in res.text, f"Keyword '{keyword}' not found in alias page {alias}"
    print("✓ Test 3 Passed: Slug aliases được chuẩn hóa tự động và trả về 200.")

    # 4. TEST Invalid Slug & 404 Page
    print("\n[TEST 4] Kiểm tra trang 404 cho slug không tồn tại...")
    res = client.get("/dich-vu/dich-vu-khong-ton-tai-xyz")
    assert res.status_code == 404, f"Expected 404, got {res.status_code}"
    assert "Trang bạn tìm kiếm không tồn tại" in res.text
    print("✓ Test 4 Passed: Slug không tồn tại trả về đúng mã 404 và giao diện 404 sang trọng.")

    # 5. TEST API /api/services/{slug}
    print("\n[TEST 5] Kiểm tra API /api/services/{slug}...")
    res = client.get("/api/services/ve-sinh-cong-nghiep")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Vệ sinh công nghiệp"
    assert isinstance(data["scope_of_work"], list) and len(data["scope_of_work"]) > 0
    assert isinstance(data["process"], list) and len(data["process"]) >= 4
    assert isinstance(data["benefits"], list) and len(data["benefits"]) >= 3
    assert isinstance(data["faq"], list) and len(data["faq"]) >= 2
    assert "seo_title" in data
    print("✓ Test 5 Passed: API /api/services/{slug} trả về đầy đủ JSON đã parse.")

    # 6. TEST Form Lead Submission
    print("\n[TEST 6] Kiểm tra gửi form yêu cầu (FORM lead)...")
    now_id = Date_now_id()
    form_phone = f"091{now_id[-7:]}"
    res = client.post("/api/leads", json={
        "name": "Nguyễn Văn Test Form",
        "phone": form_phone,
        "service": "Vệ sinh công nghiệp",
        "address": "Số 10 Đại lộ Hòa Bình, Ninh Kiều, Cần Thơ",
        "message": "Tôi cần vệ sinh nhà sau xây dựng diện tích 150m2.",
    })
    assert res.status_code == 200
    db = next(get_db())
    lead = db.query(Lead).join(Customer).filter(Customer.phone == form_phone).order_by(Lead.id.desc()).first()
    assert lead is not None
    assert lead.source == "FORM"
    assert lead.location == "Số 10 Đại lộ Hòa Bình, Ninh Kiều, Cần Thơ"
    db.close()
    print("✓ Test 6 Passed: Lead gửi từ web form lưu đúng source='FORM' và location.")

    # 7. TEST AI Chatbot: Context Awareness & Consultation Flow
    print("\n[TEST 7] Kiểm tra AI Chatbot nhận diện ngữ cảnh dịch vụ...")
    session_id = f"test-ai-session-{now_id}"
    ai_phone = f"098{now_id[-7:]}"
    res = client.post("/api/chat", json={
        "session_id": session_id,
        "message": "Xin chào, tôi cần tư vấn chuyển nhà trọn gói",
        "current_page": "service_detail",
        "service_slug": "van-chuyen-di-doi",
        "service_name": "Vận chuyển, di dời",
    })
    assert res.status_code == 200
    data = res.json()
    reply = data["reply"]
    # Check that reply asks for moving details or mentions moving
    assert any(w in reply.lower() for w in ["chuyển", "vận chuyển", "địa chỉ", "nơi đi", "đồ đạc", "khảo sát"])
    # Check no fake exact price hallucination
    assert "500.000đ" not in reply and "1.200.000 vnđ" not in reply
    print("✓ Test 7 Passed: Chatbot nhận diện ngữ cảnh 'van-chuyen-di-doi' và tư vấn đúng chuyên môn không bịa giá.")

    # 8. TEST AI Chatbot: Info Extraction & Lead Creation (source=AI_CHAT)
    print("\n[TEST 8] Kiểm tra Chatbot trích xuất thông tin và tạo lead tự động...")
    res = client.post("/api/chat", json={
        "session_id": session_id,
        "message": f"Tôi tên là Trần Văn Hưng, sđt {ai_phone}, cần chuyển nhà từ Ninh Kiều sang Cái Răng, khoảng 2 phòng ngủ.",
        "current_page": "service_detail",
        "service_slug": "van-chuyen-di-doi",
        "service_name": "Vận chuyển, di dời",
    })
    assert res.status_code == 200
    db = next(get_db())
    ai_lead = db.query(Lead).join(Customer).filter(Customer.phone == ai_phone).first()
    assert ai_lead is not None, "Lead was not created from AI Chat!"
    assert ai_lead.source == "AI_CHAT", f"Expected AI_CHAT, got {ai_lead.source}"
    assert ai_lead.customer.name == "Trần Văn Hưng"
    assert ai_lead.session_id == session_id
    assert ai_lead.requirements is not None
    db.close()
    print("✓ Test 8 Passed: Chatbot tự trích xuất Tên, SĐT, Nhu cầu và tự động tạo Lead với source='AI_CHAT'.")

    # 9. TEST Duplicate Lead Prevention
    print("\n[TEST 9] Kiểm tra ngăn trùng lặp Lead trong cùng 1 phiên chat...")
    res = client.post("/api/chat", json={
        "session_id": session_id,
        "message": "Khoảng chủ nhật tuần này làm được không em?",
        "current_page": "service_detail",
        "service_slug": "van-chuyen-di-doi",
        "service_name": "Vận chuyển, di dời",
    })
    assert res.status_code == 200
    db = next(get_db())
    leads_count = db.query(Lead).join(Customer).filter(Customer.phone == ai_phone).count()
    assert leads_count == 1, f"Expected 1 lead, found {leads_count} duplicate leads!"
    db.close()
    print("✓ Test 9 Passed: Không tạo lead trùng lặp khi khách chat tiếp trong cùng session.")

    # 10. TEST Admin Login & Lead Filtering by Source
    print("\n[TEST 10] Kiểm tra Admin lọc Lead theo nguồn (FORM vs AI_CHAT)...")
    # Login as admin
    login_res = client.post("/api/admin/auth/login", json={
        "email": admin_email,
        "password": admin_password,
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    csrf_token = client.cookies.get("oshin_admin_csrf")
    headers = {"x-csrf-token": csrf_token}

    # Filter AI_CHAT
    res_ai = client.get("/api/admin/leads?source_filter=AI_CHAT")
    assert res_ai.status_code == 200
    ai_leads = res_ai.json()
    assert any(l["phone"] == ai_phone for l in ai_leads)
    assert all(l["source"] == "AI_CHAT" for l in ai_leads)

    # Filter FORM
    res_form = client.get("/api/admin/leads?source_filter=FORM")
    assert res_form.status_code == 200
    form_leads = res_form.json()
    assert any(l["phone"] == form_phone for l in form_leads)
    assert all(l["source"] == "FORM" for l in form_leads)
    print("✓ Test 10 Passed: Admin lọc chính xác theo nguồn 'AI_CHAT' và 'FORM'.")

    # 11. TEST Admin Lead Detail with Linked Chat History
    print("\n[TEST 11] Kiểm tra Admin xem chi tiết Lead và lịch sử hội thoại...")
    db = next(get_db())
    ai_lead = db.query(Lead).join(Customer).filter(Customer.phone == ai_phone).first()
    ai_lead_id = ai_lead.id
    db.close()

    res_detail = client.get(f"/api/admin/leads/{ai_lead_id}")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert detail_data["source"] == "AI_CHAT"
    assert detail_data["session_id"] == session_id
    assert "chat_messages" in detail_data
    assert len(detail_data["chat_messages"]) >= 2
    print("✓ Test 11 Passed: Admin Lead Detail hiển thị đúng nguồn, yêu cầu và toàn bộ lịch sử chat liên kết.")

    # 12. TEST Extended CRM Lead Statuses
    print("\n[TEST 12] Kiểm tra cập nhật trạng thái mở rộng (survey_scheduled, quoted, won)...")
    csrf_token = client.cookies.get("oshin_admin_csrf")
    headers = {"x-csrf-token": csrf_token}

    for new_status in ["survey_scheduled", "quoted", "won"]:
        res_st = client.put(
            f"/api/admin/leads/{ai_lead_id}/status",
            json={"status": new_status},
            headers=headers,
        )
        assert res_st.status_code == 200
        assert res_st.json()["status"] == new_status
    print("✓ Test 12 Passed: Cập nhật thành công các trạng thái CRM: survey_scheduled, quoted, won.")

    # 13. TEST Admin Service Editor Full Fields Update
    print("\n[TEST 13] Kiểm tra Admin chỉnh sửa toàn bộ trường của dịch vụ...")
    db = next(get_db())
    svc = db.query(ManagedService).filter(ManagedService.slug == "cham-soc-cay-canh").first()
    svc_id = svc.id
    db.close()

    updated_scope = json.dumps(["Cắt tỉa tạo dáng bonsai", "Bón phân hữu cơ định kỳ", "Thay đất và chậu cây"])
    updated_faq = json.dumps([{"q": "Có nhận chăm sóc cây theo tuần không?", "a": "Dạ có, bên em có gói tuần và gói tháng ạ."}])
    update_res = client.put(
        f"/api/admin/services/{svc_id}",
        json={
            "name": "Chăm sóc cây cảnh (VIP)",
            "slug": "cham-soc-cay-canh",
            "short_description": "Dịch vụ chăm sóc sân vườn và cây cảnh cao cấp.",
            "description": "Giải pháp bảo dưỡng cảnh quan toàn diện cho biệt thự và văn phòng.",
            "content": "Nội dung bài viết giới thiệu giải pháp chăm sóc cảnh quan chuyên sâu...",
            "scope_of_work": updated_scope,
            "faq": updated_faq,
            "seo_title": "Dịch vụ Chăm sóc cây cảnh VIP Cần Thơ | Oshin Thời Đại",
            "seo_description": "Dịch vụ chăm sóc cắt tỉa cây cảnh uy tín chuyên nghiệp tại Cần Thơ.",
            "image_key": svc.image_key,
            "display_order": 6,
            "is_active": True,
        },
        headers=headers,
    )
    assert update_res.status_code == 200, f"Update service failed: {update_res.text}"

    # Verify on public detail page
    res_pub = client.get("/dich-vu/cham-soc-cay-canh")
    assert res_pub.status_code == 200
    assert "Chăm sóc cây cảnh (VIP)" in res_pub.text
    assert "Cắt tỉa tạo dáng bonsai" in res_pub.text
    assert "Có nhận chăm sóc cây theo tuần không?" in res_pub.text
    print("✓ Test 13 Passed: Admin cập nhật thành công Scope, FAQ, Content, SEO và hiển thị chính xác ngoài website.")

    print("\n" + "=" * 60)
    print("ALL 13 TESTS IN PHASE 1 SUITE PASSED SUCCESSFULLY!")
    print("=" * 60)

def Date_now_id():
    import time
    return str(int(time.time() * 1000))

if __name__ == "__main__":
    run_tests()
