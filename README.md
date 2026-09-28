# Oshin Thời Đại — Nền Tảng Dịch Vụ & Trợ Lý Tư Vấn AI

Hệ thống website dịch vụ và trợ lý ảo AI thông minh cho **CÔNG TY TNHH DỊCH VỤ OSHIN THỜI ĐẠI - ĐẤT PHƯƠNG NAM**.

---

## 🌟 Tổng Quan Dự Án

* **Backend:** FastAPI (Python 3.10+), SQLAlchemy ORM, Pydantic v2.
* **AI Engine:** Google Cloud Vertex AI / Google GenAI SDK (`gemini-2.5-flash`), hỗ trợ Multimodal Vision (nhận diện hình ảnh thực tế của khách hàng) và quy chuẩn tư vấn tự nhiên *Conversation First*.
* **Frontend:** HTML5 Semantic, Modern CSS (Responsive Design cho Mobile/Tablet/Desktop), Vanilla JavaScript tối ưu tốc độ tải trang.
* **Admin Dashboard:** Quản lý khách hàng tiềm năng (Leads), lịch sử hội thoại, đính kèm hình ảnh và cập nhật hình ảnh/nội dung website trực tiếp.
* **Database:** SQLite (mặc định cho Local Development) / PostgreSQL (Production).

---

## 🚀 Tính Năng Nổi Bật

1. **Trợ lý AI Tư Vấn Thông Minh (Conversation First):**
   * Lắng nghe, thấu hiểu nhu cầu của khách hàng trước khi tư vấn giải pháp.
   * Không gượng ép, không biến cuộc trò chuyện thành form khảo sát cứng nhắc.
   * Gợi ý câu hỏi tự nhiên theo từng bước, chỉ đề nghị liên hệ khi đã nắm rõ nhu cầu.
2. **Gemini Vision (Gửi Ảnh Cho AI):**
   * Khách hàng có thể gửi ảnh hiện trạng nhà ở, công trình, mặt bằng.
   * Hỗ trợ định dạng JPG, PNG, WebP (nén và tối ưu hóa tự động).
   * AI phân tích hình ảnh và đưa ra lời tư vấn cụ thể ngay lập tức.
3. **Widget Chat Hiện Đại:**
   * Nút mở chatbot nổi bật với hiệu ứng viền sáng thu hút.
   * Chế độ **Phóng to / Thu nhỏ** (Maximize / Minimize) toàn màn hình mượt mà, hỗ trợ phím tắt `ESC`.
   * Lưu lịch sử trò chuyện cục bộ và đồng bộ với server.
4. **Hệ Thống 7 Nhóm Dịch Vụ Chuyên Nghiệp:**
   * Vệ sinh công nghiệp & sau xây dựng.
   * Vận chuyển & di dời trọn gói.
   * Cung ứng & quản lý nguồn lao động.
   * Chăm sóc cây cảnh & cảnh quan sân vườn.
   * Giúp việc nhà theo giờ & định kỳ.
   * Kiểm soát & diệt côn trùng gây hại.
   * Trang trí nội thất & sửa chữa, cải tạo nhà ở.
5. **Trang Quản Trị (Admin Dashboard):**
   * Đăng nhập bảo mật với `bcrypt` password hashing, HttpOnly Session Cookie và CSRF Protection.
   * Quản lý danh sách Lead, chi tiết thông tin và ảnh đính kèm của khách hàng.
   * Xem toàn bộ lịch sử trao đổi của từng phiên chat.
   * Tùy chỉnh thông tin công ty và thay đổi hình ảnh website không cần can thiệp code.

---

## 🛠️ Cài Đặt & Chạy Local Development

### 1. Yêu cầu môi trường
* Python 3.10 trở lên.
* Git.

### 2. Thiết lập môi trường ảo
```bash
# Clone repository
git clone <repository_url>
cd website-tuvankhachhang

# Tạo virtual environment
python -m venv .venv

# Kích hoạt trên Windows PowerShell:
.venv\Scripts\Activate.ps1

# Hoặc kích hoạt trên macOS/Linux:
source .venv/bin/activate
```

### 3. Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### 4. Cấu hình file môi trường `.env`
Sao chép từ file mẫu:
```bash
cp .env.example .env   # Linux/macOS
copy .env.example .env # Windows CMD/PowerShell
```

Chỉnh sửa file `.env` theo thông tin dự án của bạn (ví dụ Google Cloud Project ID hoặc Gemini API Key).

### 5. Tạo tài khoản quản trị (Admin)
```bash
python scripts/create_admin.py --email admin@oshinthoidai.vn --password MatKhauBaoMat123
```

### 6. Khởi chạy Server
```bash
# Khởi chạy bằng script runner:
python run.py

# Hoặc chạy trực tiếp với uvicorn:
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Truy cập website tại:
* **Trang chủ:** `http://127.0.0.1:8080`
* **Dịch vụ:** `http://127.0.0.1:8080/dich-vu`
* **Quản trị Admin:** `http://127.0.0.1:8080/admin`
* **Kiểm tra trạng thái (Health Check):** `http://127.0.0.1:8080/health`

---

## ☁️ Triển Khai Production (Deployment)

### Cấu hình biến môi trường Production
Trên các nền tảng Cloud (GCP Cloud Run, Render, Railway, VPS Ubuntu...):
1. **Bắt buộc cấu hình:**
   * `APP_ENV=production`
   * `PORT=8080` (hoặc cổng do hệ thống Cloud cấp tự động qua `$PORT`)
   * `SECRET_KEY=<chuỗi_ngẫu_nhiên_bảo_mật>` (tạo bằng lệnh `openssl rand -hex 32`)
   * `ALLOWED_ORIGINS=https://yourdomain.vn,https://www.yourdomain.vn`
   * `GOOGLE_CLOUD_PROJECT=<project-id>`
   * `GOOGLE_CLOUD_LOCATION=global`
   * `VERTEX_MODEL=gemini-2.5-flash`
2. **Khởi chạy máy chủ Production:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
   ```

---

## 🔒 Bảo Mật & Lưu Ý
* Không bao giờ commit file `.env` hoặc các file khóa `service-account*.json` lên Git.
* Thư mục `storage/chat_uploads` và `static/uploads` lưu ảnh tải lên runtime được tự động bỏ qua trong `.gitignore` để đảm bảo quyền riêng tư của khách hàng.
