const content = document.querySelector("[data-admin-content]");
const title = document.querySelector("[data-page-title]");
const toast = document.querySelector("[data-toast]");
const sidebar = document.querySelector("[data-sidebar]");
const backdrop = document.querySelector("[data-sidebar-backdrop]");
const lightbox = document.querySelector("[data-lightbox]");
const lightboxImg = document.querySelector("[data-lightbox-img]");
const lightboxClose = document.querySelector("[data-lightbox-close]");

const STATUS_LABELS = {
  new: "Mới",
  contacted: "Đã liên hệ",
  consulting: "Đang tư vấn",
  survey_scheduled: "Đã hẹn khảo sát",
  quoted: "Đã gửi báo giá",
  won: "Thành công / Chốt deal",
  completed: "Hoàn thành",
  cancelled: "Hủy",
};

const USER_ROLE_LABELS = {
  customer: "Khách hàng",
  staff: "Nhân viên",
  manager: "Quản lý",
  admin: "Quản trị",
};

const USER_PERMISSION_LABELS = {
  "chat:view": "Xem hội thoại",
  "lead:view": "Xem yêu cầu tư vấn",
  "lead:update": "Cập nhật yêu cầu",
  "service:view": "Xem dịch vụ",
  "service:update": "Sửa dịch vụ",
  "content:update": "Sửa nội dung",
  "media:update": "Quản lý media",
};

function csrfToken() {
  const match = document.cookie
    .split("; ")
    .find((item) => item.startsWith("oshin_admin_csrf="));
  return match ? match.split("=")[1] : "";
}

async function api(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (options.method && options.method.toUpperCase() !== "GET") {
    headers["x-csrf-token"] = decodeURIComponent(csrfToken());
  }
  const response = await fetch(url, { headers, ...options });
  if (response.status === 401) {
    window.location.href = "/admin/login";
    return null;
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg = Array.isArray(data.detail)
      ? data.detail.map((e) => e.msg || "Lỗi").join("; ")
      : (data.detail || "Đã xảy ra lỗi.");
    throw new Error(errorMsg);
  }
  return data;
}

function showToast(message, isError = false) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.removeAttribute("hidden");
  toast.style.display = "flex";
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.setAttribute("hidden", "");
    toast.style.display = "none";
  }, 3500);
}

function consumeLoginSuccessParam() {
  const url = new URL(window.location.href);
  if (url.searchParams.get("login") !== "success") return;
  showToast("Đăng nhập thành công.");
  url.searchParams.delete("login");
  const cleanUrl = `${url.pathname}${url.search}${url.hash}`;
  window.history.replaceState({}, document.title, cleanUrl);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

function renderChatAttachments(attachments = []) {
  if (!attachments || attachments.length === 0) return "";
  return `
    <div class="chat-admin-attachments" style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
      ${attachments.map((att) => `
        <button type="button" data-lightbox-trigger="${escapeHtml(att.url)}" style="border:0;background:transparent;padding:0;cursor:pointer">
          <img src="${escapeHtml(att.url)}" alt="${escapeHtml(att.filename || "Ảnh khách gửi")}" loading="lazy" style="width:84px;height:84px;object-fit:cover;border-radius:8px;border:1px solid var(--line)">
        </button>
      `).join("")}
    </div>
  `;
}

function setTitle(text) {
  if (title) title.textContent = text;
  document.querySelectorAll("[data-nav]").forEach((item) => {
    const navKey = item.dataset.nav;
    const path = window.location.pathname;
    const isActive =
      (navKey === "overview" && (path === "/admin" || path === "/admin/")) ||
      (navKey !== "overview" && path.startsWith(`/admin/${navKey}`));
    item.classList.toggle("active", isActive);
  });
}

// Explicitly hide overlays at startup
if (lightbox) {
  lightbox.style.display = "none";
  lightbox.setAttribute("hidden", "");
}
if (backdrop) {
  backdrop.style.display = "none";
  backdrop.setAttribute("hidden", "");
}
if (toast) {
  toast.style.display = "none";
  toast.setAttribute("hidden", "");
}

function openLightbox(src) {
  if (!lightbox || !lightboxImg) return;
  lightboxImg.src = src;
  lightbox.removeAttribute("hidden");
  lightbox.style.display = "grid";
}

function closeLightbox() {
  if (!lightbox) return;
  lightbox.setAttribute("hidden", "");
  lightbox.style.display = "none";
  if (lightboxImg) lightboxImg.src = "";
}

if (lightboxClose) lightboxClose.addEventListener("click", closeLightbox);
if (lightbox) {
  lightbox.addEventListener("click", (e) => {
    if (e.target === lightbox) closeLightbox();
  });
}

// ==================================================
// 1. OVERVIEW / DASHBOARD
// ==================================================
async function renderOverview() {
  setTitle("Tổng quan");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải dữ liệu...</div>`;
  const data = await api("/api/admin/overview");

  content.innerHTML = `
    <div class="cards">
      <article class="card">
        <span>Tổng yêu cầu tư vấn</span>
        <strong>${data.cards.total_leads}</strong>
      </article>
      <article class="card">
        <span>Yêu cầu mới</span>
        <strong>${data.cards.new_leads}</strong>
      </article>
      <article class="card">
        <span>Tổng cuộc hội thoại</span>
        <strong>${data.cards.total_chats}</strong>
      </article>
      <article class="card">
        <span>Số dịch vụ hoạt động</span>
        <strong>${data.cards.service_count}</strong>
      </article>
      <a class="card dashboard-link-card" href="/admin/users">
        <span>Người dùng Google</span>
        <strong>${data.cards.user_count || 0}</strong>
      </a>
    </div>

    <section class="panel">
      <div class="panel-header">
        <h2>Yêu cầu tư vấn gần đây</h2>
        <div class="actions">
          <a class="ghost" href="/admin/users">Phân quyền người dùng →</a>
          <a class="ghost" href="/admin/leads">Xem tất cả →</a>
        </div>
      </div>
      <div class="table-responsive">
        ${renderLeadsTable(data.recent_leads)}
      </div>
    </section>
  `;
}

function renderLeadsTable(leads) {
  if (!leads || leads.length === 0) {
    return `<div style="padding:32px;text-align:center;color:var(--muted)">Chưa có yêu cầu tư vấn nào.</div>`;
  }
  return `
    <table>
      <thead>
        <tr>
          <th>Khách hàng</th>
          <th>SĐT</th>
          <th>Dịch vụ</th>
          <th>Nguồn</th>
          <th>Ngày gửi</th>
          <th>Trạng thái</th>
          <th>Thao tác</th>
        </tr>
      </thead>
      <tbody>
        ${leads.map((lead) => {
          const src = lead.source || "FORM";
          const isAi = src === "AI_CHAT";
          return `
          <tr>
            <td><strong>${escapeHtml(lead.customer_name)}</strong></td>
            <td><a href="tel:${escapeHtml(lead.phone)}" style="color:var(--blue);font-weight:700">📞 ${escapeHtml(lead.phone)}</a></td>
            <td>${escapeHtml(lead.service)}</td>
            <td><span class="source-pill ${src.toLowerCase()}">${isAi ? "🤖 AI CHAT" : "📝 FORM"}</span></td>
            <td>${new Date(lead.created_at).toLocaleString("vi-VN")}</td>
            <td><span class="status-pill ${escapeHtml(lead.status)}">${STATUS_LABELS[lead.status] || lead.status}</span></td>
            <td><a class="ghost" href="/admin/leads/${lead.id}">Chi tiết</a></td>
          </tr>
        `;}).join("")}
      </tbody>
    </table>
  `;
}

// ==================================================
// 2. IMAGE MANAGEMENT
// ==================================================
async function renderImages() {
  setTitle("Quản lý hình ảnh website");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải danh sách ảnh...</div>`;
  const images = await api("/api/admin/images");

  const heroImages = images.filter((i) => i.key.startsWith("hero_"));
  const serviceImages = images.filter((i) => i.key.startsWith("service_"));
  const brandImages = images.filter((i) => i.key.startsWith("brand_"));

  content.innerHTML = `
    <div style="margin-bottom:28px">
      <p style="margin:0 0 8px;color:var(--muted)">
        Thay đổi ảnh website trực tiếp. Hệ thống tự động tối ưu hóa sang WebP, giữ nguyên tỷ lệ khung hình và không làm méo ảnh.
      </p>
    </div>

    <section class="panel">
      <div class="panel-header"><h2>Vị trí HERO (Đầu trang)</h2></div>
      <div class="panel-body">
        <div class="grid">${heroImages.map((img) => imageCard(img)).join("")}</div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header"><h2>Ảnh các DỊCH VỤ</h2></div>
      <div class="panel-body">
        <div class="grid">${serviceImages.map((img) => imageCard(img)).join("")}</div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header"><h2>Ảnh THƯƠNG HIỆU & ĐỘI NGŨ</h2></div>
      <div class="panel-body">
        <div class="grid">${brandImages.map((img) => imageCard(img)).join("")}</div>
      </div>
    </section>
  `;

  bindImageCards();
}

function imageCard(image) {
  const is169 = image.recommendation.includes("16:9");
  return `
    <article class="panel image-card" data-card-key="${escapeHtml(image.key)}">
      <div class="panel-body">
        <div class="image-header-row">
          <div>
            <h3>${escapeHtml(image.label)}</h3>
            <span class="recommendation-badge">📐 ${escapeHtml(image.recommendation)}</span>
          </div>
        </div>

        <div class="current-preview-wrapper ${is169 ? "ratio-16-9" : ""}">
          <img src="${escapeHtml(image.url)}" alt="${escapeHtml(image.alt_text)}" loading="lazy">
        </div>

        <div class="actions" style="margin-top:auto">
          <input type="file" data-file-input="${escapeHtml(image.key)}" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" style="display:none">
          <button type="button" class="file-select-btn" data-trigger-file="${escapeHtml(image.key)}">
            🖼 Thay ảnh
          </button>
          <button type="button" class="ghost" data-restore="${escapeHtml(image.key)}">
            Khôi phục mặc định
          </button>
        </div>

        <div class="new-preview-box" data-preview-box="${escapeHtml(image.key)}" hidden>
          <p>Xem trước ảnh mới:</p>
          <img data-preview-img="${escapeHtml(image.key)}" src="" alt="Preview">
          <div class="actions" style="justify-content:center">
            <button type="button" class="btn-primary" data-save-image="${escapeHtml(image.key)}">
              💾 Lưu thay đổi
            </button>
            <button type="button" class="ghost" data-cancel-image="${escapeHtml(image.key)}">
              ✕ Hủy
            </button>
          </div>
        </div>
      </div>
    </article>
  `;
}

function bindImageCards() {
  document.querySelectorAll("[data-card-key]").forEach((card) => {
    const key = card.dataset.cardKey;
    const fileInput = card.querySelector(`[data-file-input="${key}"]`);
    const triggerBtn = card.querySelector(`[data-trigger-file="${key}"]`);
    const previewBox = card.querySelector(`[data-preview-box="${key}"]`);
    const previewImg = card.querySelector(`[data-preview-img="${key}"]`);
    const saveBtn = card.querySelector(`[data-save-image="${key}"]`);
    const cancelBtn = card.querySelector(`[data-cancel-image="${key}"]`);
    const restoreBtn = card.querySelector(`[data-restore="${key}"]`);

    let selectedFile = null;

    triggerBtn.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files[0]) {
        selectedFile = fileInput.files[0];
        if (selectedFile.size > 5 * 1024 * 1024) {
          showToast("Lỗi: Ảnh vượt quá kích thước 5MB", true);
          fileInput.value = "";
          selectedFile = null;
          return;
        }
        previewImg.src = URL.createObjectURL(selectedFile);
        previewBox.hidden = false;
      }
    });

    cancelBtn.addEventListener("click", () => {
      fileInput.value = "";
      selectedFile = null;
      previewBox.hidden = true;
      previewImg.src = "";
    });

    saveBtn.addEventListener("click", async () => {
      if (!selectedFile) return;
      saveBtn.disabled = true;
      saveBtn.textContent = "Đang xử lý...";
      try {
        const formData = new FormData();
        formData.append("file", selectedFile);
        await api(`/api/admin/images/${key}`, { method: "POST", body: formData });
        showToast("Đã cập nhật hình ảnh thành công.");
        renderImages();
      } catch (err) {
        showToast(err.message, true);
        saveBtn.disabled = false;
        saveBtn.textContent = "💾 Lưu thay đổi";
      }
    });

    restoreBtn.addEventListener("click", async () => {
      if (!confirm("Bạn có chắc chắn muốn khôi phục ảnh mặc định cho vị trí này không?")) return;
      try {
        await api(`/api/admin/images/${key}/restore`, { method: "POST", body: "{}" });
        showToast("Đã khôi phục ảnh mặc định.");
        renderImages();
      } catch (err) {
        showToast(err.message, true);
      }
    });
  });
}

// ==================================================
// 3. SERVICE MANAGEMENT
// ==================================================
async function renderServices() {
  setTitle("Quản lý dịch vụ");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải danh sách dịch vụ...</div>`;

  const [services, images] = await Promise.all([
    api("/api/admin/services"),
    api("/api/admin/images"),
  ]);

  const imageOptions = images.map(
    (img) => `<option value="${escapeHtml(img.key)}">${escapeHtml(img.label)} (${escapeHtml(img.key)})</option>`
  ).join("");

  content.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px">
      <p style="margin:0;color:var(--muted)">Quản lý 7 dịch vụ hiện tại. Thay đổi tên, mô tả, ảnh liên kết, trạng thái ẩn/hiện và thứ tự hiển thị.</p>
    </div>

    <div class="grid">
      ${services.map((svc) => serviceCard(svc, imageOptions)).join("")}
    </div>
  `;

  bindServiceForms();
}

function formatScopeToLines(scopeVal) {
  if (!scopeVal) return "";
  if (Array.isArray(scopeVal)) return scopeVal.join("\n");
  try {
    const parsed = JSON.parse(scopeVal);
    if (Array.isArray(parsed)) return parsed.join("\n");
  } catch (e) {}
  return String(scopeVal);
}

function formatJsonPretty(val) {
  if (!val) return "[]";
  if (typeof val === "object") return JSON.stringify(val, null, 2);
  try {
    const parsed = JSON.parse(val);
    return JSON.stringify(parsed, null, 2);
  } catch (e) {
    return String(val);
  }
}

function serviceCard(service, imageOptions) {
  const scopeLines = formatScopeToLines(service.scope_of_work);
  const processJson = formatJsonPretty(service.process);
  const benefitsJson = formatJsonPretty(service.benefits);
  const faqJson = formatJsonPretty(service.faq);

  return `
    <article class="panel" style="grid-column: 1 / -1;">
      <div class="panel-body">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:12px">
          <div>
            <h3 style="margin:0;font-size:1.25rem;color:var(--navy)">${escapeHtml(service.name)}</h3>
            <span style="font-size:0.82rem;color:var(--muted);font-family:monospace">/${escapeHtml(service.slug)}</span>
          </div>
          <div style="display:flex;gap:10px;align-items:center">
            <a href="/dich-vu/${service.slug}" target="_blank" rel="noopener" class="ghost" style="font-size:0.85rem">
              Xem trang dịch vụ ↗
            </a>
            <span class="status-pill ${service.is_active ? "completed" : "cancelled"}">
              ${service.is_active ? "Đang hiển thị" : "Đang ẩn"}
            </span>
          </div>
        </div>

        <form data-service-form="${service.id}" data-selected-image="${escapeHtml(service.image_key)}">
          <div class="service-editor-tabs">
            <button type="button" class="service-editor-tab active" data-tab-target="basic">📌 Cơ bản</button>
            <button type="button" class="service-editor-tab" data-tab-target="content">📝 Nội dung & Ảnh</button>
            <button type="button" class="service-editor-tab" data-tab-target="scope">📋 Hạng mục & Quy trình</button>
            <button type="button" class="service-editor-tab" data-tab-target="benefits-faq">⭐ Lợi ích & FAQ</button>
            <button type="button" class="service-editor-tab" data-tab-target="seo">🔍 Cấu hình SEO</button>
          </div>

          <!-- TAB 1: BASIC -->
          <div class="service-tab-pane" data-tab-pane="basic">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
              <label>Tên dịch vụ *
                <input name="name" value="${escapeHtml(service.name)}" required>
              </label>

              <label>Mã định danh (Slug) *
                <input name="slug" value="${escapeHtml(service.slug)}" required>
              </label>
            </div>

            <label style="margin-top:12px">Mô tả ngắn (Hiển thị ngoài trang chủ & card) *
              <textarea name="short_description" required rows="2">${escapeHtml(service.short_description)}</textarea>
            </label>

            <label style="margin-top:12px">Mô tả tổng quan
              <textarea name="description" rows="3">${escapeHtml(service.description)}</textarea>
            </label>

            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-top:12px;align-items:center">
              <label>Ảnh đại diện mặc định
                <select name="image_key">${imageOptions}</select>
              </label>

              <label>Thứ tự hiển thị
                <input name="display_order" type="number" min="0" max="999" value="${service.display_order}">
              </label>

              <label class="checkbox-label" style="margin-top:20px">
                <input name="is_active" type="checkbox" ${service.is_active ? "checked" : ""}>
                <span>Hiển thị trên website</span>
              </label>
            </div>
          </div>

          <!-- TAB 2: CONTENT & IMAGES -->
          <div class="service-tab-pane" data-tab-pane="content" hidden>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
              <label>URL Ảnh Hero chi tiết (tùy chọn)
                <input name="hero_image" value="${escapeHtml(service.hero_image || "")}" placeholder="/static/img/services/...">
                <span class="field-hint">Để trống sẽ dùng ảnh mặc định của dịch vụ</span>
              </label>

              <label>URL Ảnh Thẻ Card (tùy chọn)
                <input name="card_image" value="${escapeHtml(service.card_image || "")}" placeholder="/static/img/services/...">
                <span class="field-hint">Để trống sẽ dùng ảnh mặc định</span>
              </label>
            </div>

            <label style="margin-top:14px">Bài viết giới thiệu chi tiết (Phần Giới thiệu dịch vụ)
              <textarea name="content" rows="6" placeholder="Nội dung giới thiệu chi tiết về dịch vụ...">${escapeHtml(service.content || "")}</textarea>
            </label>
          </div>

          <!-- TAB 3: SCOPE & PROCESS -->
          <div class="service-tab-pane" data-tab-pane="scope" hidden>
            <label>Các hạng mục triển khai (Mỗi dòng là 1 hạng mục)
              <textarea name="scope_of_work" rows="5" placeholder="Hạng mục 1&#10;Hạng mục 2&#10;Hạng mục 3">${escapeHtml(scopeLines)}</textarea>
              <span class="field-hint">Mỗi dòng sẽ được tự động hiển thị thành một ô hạng mục trên trang chi tiết</span>
            </label>

            <label style="margin-top:14px">Quy trình thực hiện (JSON 5 bước)
              <textarea name="process" rows="8" style="font-family:monospace;font-size:0.85rem">${escapeHtml(processJson)}</textarea>
              <span class="field-hint">Định dạng JSON mảng các bước [{ "step": "01", "title": "...", "desc": "..." }]</span>
            </label>
          </div>

          <!-- TAB 4: BENEFITS & FAQ -->
          <div class="service-tab-pane" data-tab-pane="benefits-faq" hidden>
            <label>Lợi ích khi chọn Oshin Thời Đại (JSON)
              <textarea name="benefits" rows="6" style="font-family:monospace;font-size:0.85rem">${escapeHtml(benefitsJson)}</textarea>
              <span class="field-hint">Định dạng JSON mảng [{ "title": "...", "desc": "..." }]</span>
            </label>

            <label style="margin-top:14px">Câu hỏi thường gặp FAQ (JSON)
              <textarea name="faq" rows="8" style="font-family:monospace;font-size:0.85rem">${escapeHtml(faqJson)}</textarea>
              <span class="field-hint">Định dạng JSON mảng [{ "q": "...", "a": "..." }]</span>
            </label>
          </div>

          <!-- TAB 5: SEO -->
          <div class="service-tab-pane" data-tab-pane="seo" hidden>
            <label>Tiêu đề trang SEO (SEO Title)
              <input name="seo_title" value="${escapeHtml(service.seo_title || "")}" placeholder="Tên dịch vụ - Oshin Thời Đại">
            </label>

            <label style="margin-top:12px">Mô tả tóm tắt SEO (SEO Description)
              <textarea name="seo_description" rows="3" placeholder="Mô tả chuẩn SEO dài khoảng 120-160 ký tự...">${escapeHtml(service.seo_description || "")}</textarea>
            </label>
          </div>

          <div class="actions" style="margin-top:20px;padding-top:14px;border-top:1px solid var(--line)">
            <button type="submit" class="btn-primary">💾 Lưu tất cả thông tin dịch vụ</button>
            <button type="button" class="danger" data-delete-service="${service.id}">🗑 Xóa</button>
          </div>
        </form>
      </div>
    </article>
  `;
}

function bindServiceForms() {
  document.querySelectorAll("[data-service-form]").forEach((form) => {
    const serviceId = form.dataset.serviceForm;
    const selectedImageKey = form.dataset.selectedImage;
    if (form.image_key) form.image_key.value = selectedImageKey;

    // Tab switcher
    const tabButtons = form.querySelectorAll(".service-editor-tab");
    const tabPanes = form.querySelectorAll(".service-tab-pane");
    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.dataset.tabTarget;
        tabButtons.forEach((b) => b.classList.toggle("active", b === btn));
        tabPanes.forEach((p) => {
          p.hidden = p.dataset.tabPane !== target;
        });
      });
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = form.querySelector("button[type=submit]");

      // Validate JSON fields
      let processVal = form.process.value.trim();
      if (processVal) {
        try {
          JSON.parse(processVal);
        } catch (err) {
          showToast("Lỗi định dạng JSON ở trường Quy trình thực hiện!", true);
          return;
        }
      }

      let benefitsVal = form.benefits.value.trim();
      if (benefitsVal) {
        try {
          JSON.parse(benefitsVal);
        } catch (err) {
          showToast("Lỗi định dạng JSON ở trường Lợi ích!", true);
          return;
        }
      }

      let faqVal = form.faq.value.trim();
      if (faqVal) {
        try {
          JSON.parse(faqVal);
        } catch (err) {
          showToast("Lỗi định dạng JSON ở trường Câu hỏi thường gặp FAQ!", true);
          return;
        }
      }

      // Convert Scope of Work lines to JSON string
      const scopeArr = form.scope_of_work.value
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
      const scopeVal = JSON.stringify(scopeArr);

      submitBtn.disabled = true;
      submitBtn.textContent = "Đang lưu...";
      try {
        const payload = {
          name: form.name.value.trim(),
          slug: form.slug.value.trim(),
          short_description: form.short_description.value.trim(),
          description: form.description.value.trim(),
          content: form.content.value.trim(),
          hero_image: form.hero_image.value.trim(),
          card_image: form.card_image.value.trim(),
          scope_of_work: scopeVal,
          process: processVal,
          benefits: benefitsVal,
          faq: faqVal,
          seo_title: form.seo_title.value.trim(),
          seo_description: form.seo_description.value.trim(),
          image_key: form.image_key.value,
          display_order: parseInt(form.display_order.value, 10) || 0,
          is_active: form.is_active.checked,
        };
        await api(`/api/admin/services/${serviceId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        showToast("Đã lưu toàn bộ thông tin dịch vụ thành công.");
        renderServices();
      } catch (err) {
        showToast(err.message, true);
        submitBtn.disabled = false;
        submitBtn.textContent = "💾 Lưu tất cả thông tin dịch vụ";
      }
    });

    const deleteBtn = form.querySelector(`[data-delete-service="${serviceId}"]`);
    if (deleteBtn) {
      deleteBtn.addEventListener("click", async () => {
        if (!confirm(`Bạn có chắc chắn muốn xóa dịch vụ "${form.name.value}"?`)) return;
        try {
          await api(`/api/admin/services/${serviceId}`, { method: "DELETE" });
          showToast("Đã xóa dịch vụ.");
          renderServices();
        } catch (err) {
          showToast(err.message, true);
        }
      });
    }
  });
}

// ==================================================
// 4. HOMEPAGE CONTENT MANAGEMENT
// ==================================================
async function renderContent() {
  setTitle("Nội dung trang chủ");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải nội dung...</div>`;
  const data = await api("/api/admin/content");

  content.innerHTML = `
    <section class="panel">
      <div class="panel-body">
        <form data-content-form class="form-grid">
          <div class="section-divider">
            <h3>PHẦN HERO (ĐẦU TRANG)</h3>
          </div>

          <label>Eyebrow (Dòng chữ nhỏ trên tiêu đề)
            <input name="hero_eyebrow" value="${escapeHtml(data.hero_eyebrow || "")}">
          </label>

          <label>Nút kêu gọi hành động (CTA Text)
            <input name="hero_cta_text" value="${escapeHtml(data.hero_cta_text || "")}">
          </label>

          <label class="full">Tiêu đề chính (Heading) *
            <input name="hero_heading" value="${escapeHtml(data.hero_heading || "")}" required>
          </label>

          <label class="full">Mô tả ngắn
            <textarea name="hero_description">${escapeHtml(data.hero_description || "")}</textarea>
          </label>

          <div class="section-divider">
            <h3>PHẦN VÌ SAO CHỌN CHÚNG TÔI (WHY US)</h3>
          </div>

          <label class="full">Tiêu đề (Heading)
            <input name="why_heading" value="${escapeHtml(data.why_heading || "")}">
          </label>

          <label class="full">Mô tả
            <textarea name="why_description">${escapeHtml(data.why_description || "")}</textarea>
          </label>

          <div class="section-divider">
            <h3>PHẦN KÊU GỌI CUỐI TRANG (FINAL CTA)</h3>
          </div>

          <label>Tiêu đề (Heading)
            <input name="final_cta_heading" value="${escapeHtml(data.final_cta_heading || "")}">
          </label>

          <label>Chữ nút bấm (Button Text)
            <input name="final_cta_button_text" value="${escapeHtml(data.final_cta_button_text || "")}">
          </label>

          <label class="full">Mô tả thêm (Tùy chọn)
            <textarea name="final_cta_description">${escapeHtml(data.final_cta_description || "")}</textarea>
          </label>

          <div class="full" style="margin-top:14px">
            <button type="submit" class="btn-primary" style="min-width:180px">💾 Lưu nội dung</button>
          </div>
        </form>
      </div>
    </section>
  `;

  document.querySelector("[data-content-form]").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button[type=submit]");
    btn.disabled = true;
    btn.textContent = "Đang lưu...";
    try {
      const values = Object.fromEntries(new FormData(e.target).entries());
      await api("/api/admin/content", {
        method: "PUT",
        body: JSON.stringify({ values }),
      });
      showToast("Đã lưu nội dung website thành công.");
      btn.disabled = false;
      btn.textContent = "💾 Lưu nội dung";
    } catch (err) {
      showToast(err.message, true);
      btn.disabled = false;
      btn.textContent = "💾 Lưu nội dung";
    }
  });
}

// ==================================================
// 5. COMPANY INFORMATION
// ==================================================
async function renderCompany() {
  setTitle("Thông tin công ty");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải thông tin...</div>`;
  const data = await api("/api/admin/company");

  content.innerHTML = `
    <div style="margin-bottom:20px;padding:16px 20px;background:#FEF0C7;border-radius:12px;color:#93370D;font-weight:600">
      💡 <strong>Lưu ý:</strong> Khi bạn thay đổi <strong>Hotline</strong> hoặc thông tin tại đây, toàn bộ website (Header, Hero, Thanh tin cậy, Form liên hệ, Footer) sẽ tự động cập nhật theo.
    </div>

    <section class="panel">
      <div class="panel-body">
        <form data-company-form class="form-grid">
          <label class="full">Tên công ty đầy đủ *
            <input name="company_name" value="${escapeHtml(data.company_name || "")}" required>
          </label>

          <label>Tên thương hiệu *
            <input name="brand_name" value="${escapeHtml(data.brand_name || "")}" required>
          </label>

          <label>Hotline (Source of truth) *
            <input name="hotline" value="${escapeHtml(data.hotline || "")}" required>
            <span class="field-hint">Số hotline liên hệ chính của công ty</span>
          </label>

          <label class="full">Slogan / Khẩu hiệu
            <input name="slogan" value="${escapeHtml(data.slogan || "")}">
          </label>

          <label>Email liên hệ
            <input name="email" type="email" value="${escapeHtml(data.email || "")}">
            <span class="field-hint">Để trống nếu không muốn hiển thị trên trang chủ</span>
          </label>

          <label>Giờ làm việc
            <input name="working_hours" value="${escapeHtml(data.working_hours || "")}">
            <span class="field-hint">Ví dụ: 07:30 - 18:00 (Hàng ngày)</span>
          </label>

          <label class="full">Địa chỉ trụ sở / văn phòng
            <input name="address" value="${escapeHtml(data.address || "")}">
            <span class="field-hint">Để trống nếu không muốn hiển thị trên trang chủ</span>
          </label>

          <div class="full" style="margin-top:14px">
            <button type="submit" class="btn-primary" style="min-width:200px">💾 Lưu thông tin công ty</button>
          </div>
        </form>
      </div>
    </section>
  `;

  document.querySelector("[data-company-form]").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button[type=submit]");
    btn.disabled = true;
    btn.textContent = "Đang lưu...";
    try {
      const values = Object.fromEntries(new FormData(e.target).entries());
      await api("/api/admin/company", {
        method: "PUT",
        body: JSON.stringify({ values }),
      });
      showToast("Đã cập nhật thông tin công ty thành công.");
      btn.disabled = false;
      btn.textContent = "💾 Lưu thông tin công ty";
    } catch (err) {
      showToast(err.message, true);
      btn.disabled = false;
      btn.textContent = "💾 Lưu thông tin công ty";
    }
  });
}

// ==================================================
// 6. LEAD MANAGEMENT
// ==================================================
async function renderLeads() {
  setTitle("Yêu cầu tư vấn khách hàng");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải danh sách...</div>`;

  const [leads, services] = await Promise.all([
    api("/api/admin/leads"),
    api("/api/admin/services"),
  ]);

  content.innerHTML = `
    <div class="filter-bar">
      <input type="search" placeholder="🔍 Tìm theo Tên hoặc Số điện thoại..." data-lead-search>
      <select data-lead-service-filter>
        <option value="">Tất cả dịch vụ</option>
        ${services.map((s) => `<option value="${escapeHtml(s.name)}">${escapeHtml(s.name)}</option>`).join("")}
      </select>
      <select data-lead-source-filter>
        <option value="">Tất cả nguồn</option>
        <option value="FORM">Form Website</option>
        <option value="AI_CHAT">Trợ lý AI</option>
      </select>
      <select data-lead-status-filter>
        <option value="">Tất cả trạng thái</option>
        <option value="new">Mới</option>
        <option value="contacted">Đã liên hệ</option>
        <option value="consulting">Đang tư vấn</option>
        <option value="survey_scheduled">Đã hẹn khảo sát</option>
        <option value="quoted">Đã gửi báo giá</option>
        <option value="won">Thành công / Chốt deal</option>
        <option value="completed">Hoàn thành</option>
        <option value="cancelled">Hủy</option>
      </select>
    </div>

    <section class="panel">
      <div class="table-responsive" data-leads-container>
        ${renderLeadsTable(leads)}
      </div>
    </section>
  `;

  const searchInput = document.querySelector("[data-lead-search]");
  const serviceFilter = document.querySelector("[data-lead-service-filter]");
  const sourceFilter = document.querySelector("[data-lead-source-filter]");
  const statusFilter = document.querySelector("[data-lead-status-filter]");
  const container = document.querySelector("[data-leads-container]");

  async function applyFilter() {
    const q = encodeURIComponent(searchInput.value.trim());
    const svc = encodeURIComponent(serviceFilter.value);
    const src = encodeURIComponent(sourceFilter.value);
    const st = encodeURIComponent(statusFilter.value);
    const filtered = await api(`/api/admin/leads?q=${q}&service=${svc}&status_filter=${st}&source_filter=${src}`);
    container.innerHTML = renderLeadsTable(filtered);
  }

  let searchTimeout;
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(applyFilter, 300);
  });
  serviceFilter.addEventListener("change", applyFilter);
  sourceFilter.addEventListener("change", applyFilter);
  statusFilter.addEventListener("change", applyFilter);
}

async function renderLeadDetail(id) {
  setTitle("Chi tiết yêu cầu tư vấn");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải thông tin...</div>`;

  const lead = await api(`/api/admin/leads/${id}`);
  const src = lead.source || "FORM";
  const isAi = src === "AI_CHAT";

  let reqsHtml = "";
  if (lead.requirements) {
    try {
      const parsedReq = typeof lead.requirements === "object" ? lead.requirements : JSON.parse(lead.requirements);
      const reqEntries = Object.entries(parsedReq);
      if (reqEntries.length > 0) {
        reqsHtml = `
          <div class="lead-detail-row" style="background:#F0FDF4;padding:14px 18px;border-radius:12px;border:1px solid #BBF7D0">
            <strong style="color:#166534">Nhu cầu đã thu thập (AI):</strong>
            <ul style="margin:8px 0 0;padding-left:20px;color:#166534">
              ${reqEntries.map(([k, v]) => `<li><strong>${escapeHtml(k)}:</strong> ${escapeHtml(String(v))}</li>`).join("")}
            </ul>
          </div>
        `;
      }
    } catch (e) {
      reqsHtml = `<div class="lead-detail-row"><strong>Nhu cầu chi tiết:</strong><span>${escapeHtml(String(lead.requirements))}</span></div>`;
    }
  }

  let chatHistoryHtml = "";
  if (lead.chat_messages && lead.chat_messages.length > 0) {
    chatHistoryHtml = `
      <div style="margin-top:28px;padding-top:20px;border-top:1px solid var(--line)">
        <h3 style="margin-bottom:12px;font-size:1.05rem;color:var(--navy)">💬 Lịch sử trò chuyện với AI (${lead.chat_messages.length} tin nhắn)</h3>
        <div class="chat-log" style="max-height:360px;overflow-y:auto;background:#F8FAFC;padding:16px;border-radius:14px;border:1px solid var(--line)">
          ${lead.chat_messages.map((m) => `
            <div class="bubble ${m.role === "user" ? "user" : "assistant"}" style="margin-bottom:10px">
              <strong>${m.role === "user" ? "👤 KHÁCH HÀNG" : "🤖 TRỢ LÝ OSHIN"}</strong>
              <div style="margin-top:4px">${escapeHtml(m.message)}</div>
              ${renderChatAttachments(m.attachments)}
              <small style="color:var(--muted);font-size:0.75rem">${new Date(m.created_at).toLocaleTimeString("vi-VN")} ${new Date(m.created_at).toLocaleDateString("vi-VN")}</small>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  content.innerHTML = `
    <div style="margin-bottom:20px">
      <a class="ghost" href="/admin/leads">← Quay lại danh sách yêu cầu</a>
    </div>

    <section class="panel lead-detail-card">
      <div class="panel-header">
        <h2>Yêu cầu #${lead.id}</h2>
        <div style="display:flex;gap:8px;align-items:center">
          <span class="source-pill ${src.toLowerCase()}">${isAi ? "🤖 AI CHAT" : "📝 FORM WEBSITE"}</span>
          <span class="status-pill ${escapeHtml(lead.status)}">${STATUS_LABELS[lead.status] || lead.status}</span>
        </div>
      </div>
      <div class="panel-body">
        <div class="lead-detail-row">
          <strong>Họ và tên:</strong>
          <span>${escapeHtml(lead.customer_name)}</span>
        </div>
        <div class="lead-detail-row">
          <strong>Số điện thoại:</strong>
          <span>
            <a href="tel:${escapeHtml(lead.phone)}" style="color:var(--blue);font-weight:800">📞 ${escapeHtml(lead.phone)}</a>
          </span>
        </div>
        <div class="lead-detail-row">
          <strong>Dịch vụ quan tâm:</strong>
          <span>${escapeHtml(lead.service)}</span>
        </div>
        <div class="lead-detail-row">
          <strong>Nguồn yêu cầu:</strong>
          <span class="source-pill ${src.toLowerCase()}">${isAi ? "🤖 Trợ lý ảo AI Chatbot" : "📝 Form đăng ký trực tuyến"}</span>
        </div>
        <div class="lead-detail-row">
          <strong>Địa chỉ / Khu vực:</strong>
          <span>${escapeHtml(lead.location || lead.address || "Không cung cấp")}</span>
        </div>
        <div class="lead-detail-row">
          <strong>Nội dung yêu cầu:</strong>
          <div style="white-space:pre-wrap">${escapeHtml(lead.message || "Không có")}</div>
        </div>
        ${reqsHtml}
        ${lead.session_id ? `
          <div class="lead-detail-row">
            <strong>Mã phiên chat:</strong>
            <code>${escapeHtml(lead.session_id)}</code>
          </div>
        ` : ""}
        <div class="lead-detail-row">
          <strong>Ngày tiếp nhận:</strong>
          <span>${new Date(lead.created_at).toLocaleString("vi-VN")}</span>
        </div>

        <div style="margin:24px 0">
          <a class="call-btn" href="tel:${escapeHtml(lead.phone)}">
            ☎ Gọi khách ngay: ${escapeHtml(lead.phone)}
          </a>
        </div>

        ${chatHistoryHtml}

        <div style="margin-top:28px;padding-top:20px;border-top:1px solid var(--line)">
          <form data-lead-status-form style="max-width:340px">
            <label>Cập nhật trạng thái
              <select name="status">
                ${Object.entries(STATUS_LABELS).map(([k, label]) => `
                  <option value="${k}" ${lead.status === k ? "selected" : ""}>${label}</option>
                `).join("")}
              </select>
            </label>
            <button type="submit" class="btn-primary" style="margin-top:10px">Cập nhật trạng thái</button>
          </form>
        </div>
      </div>
    </section>
  `;

  document.querySelector("[data-lead-status-form]").addEventListener("submit", async (e) => {
    e.preventDefault();
    const newStatus = e.target.status.value;
    try {
      await api(`/api/admin/leads/${id}/status`, {
        method: "PUT",
        body: JSON.stringify({ status: newStatus }),
      });
      showToast("Đã cập nhật trạng thái yêu cầu.");
      renderLeadDetail(id);
    } catch (err) {
      showToast(err.message, true);
    }
  });
}

// ==================================================
// 7. CHAT HISTORY
// ==================================================
async function renderChats() {
  setTitle("Chat / Lịch sử hội thoại");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải hội thoại...</div>`;
  const chats = await api("/api/admin/chats");

  content.innerHTML = `
    <section class="panel">
      <div class="panel-header">
        <h2>Danh sách cuộc hội thoại với Trợ lý AI</h2>
      </div>
      <div class="table-responsive">
        ${!chats || chats.length === 0 ? `
          <div style="padding:32px;text-align:center;color:var(--muted)">Chưa có phiên chat nào.</div>
        ` : `
          <table>
            <thead>
              <tr>
                <th>Mã phiên (Session)</th>
                <th>Số tin nhắn</th>
                <th>Tin nhắn cuối</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              ${chats.map((c) => `
                <tr>
                  <td><code>${escapeHtml(c.session_id)}</code></td>
                  <td><strong>${c.message_count}</strong></td>
                  <td>${c.last_message_at ? new Date(c.last_message_at).toLocaleString("vi-VN") : ""}</td>
                  <td><a class="ghost" href="/admin/chats/${encodeURIComponent(c.session_id)}">Xem hội thoại →</a></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        `}
      </div>
    </section>
  `;
}

async function renderChatDetail(sessionId) {
  setTitle("Chi tiết hội thoại");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải tin nhắn...</div>`;

  const messages = await api(`/api/admin/chats/${encodeURIComponent(sessionId)}`);

  content.innerHTML = `
    <div style="margin-bottom:20px">
      <a class="ghost" href="/admin/chats">← Quay lại danh sách hội thoại</a>
    </div>

    <section class="panel">
      <div class="panel-header">
        <h2>Phiên: <code>${escapeHtml(sessionId)}</code></h2>
        <span>${messages.length} tin nhắn</span>
      </div>
      <div class="panel-body">
        <div class="chat-log">
          ${messages.map((m) => `
            <div class="bubble ${m.role === "user" ? "user" : "assistant"}">
              <strong>${m.role === "user" ? "👤 KHÁCH HÀNG" : "🤖 TRỢ LÝ OSHIN"}</strong>
              <div style="margin-top:4px">${escapeHtml(m.message)}</div>
              ${renderChatAttachments(m.attachments)}
              <small>${new Date(m.created_at).toLocaleTimeString("vi-VN")} • ${new Date(m.created_at).toLocaleDateString("vi-VN")}</small>
            </div>
          `).join("")}
        </div>
      </div>
    </section>
  `;

  document.querySelectorAll("[data-lightbox-trigger]").forEach((el) => {
    el.addEventListener("click", () => openLightbox(el.dataset.lightboxTrigger));
  });
}

// ==================================================
// 8. USER PERMISSIONS
// ==================================================
async function renderUsers() {
  setTitle("Người dùng & phân quyền");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải danh sách người dùng...</div>`;
  const users = await api("/api/admin/users");

  content.innerHTML = `
    <section class="panel">
      <div class="panel-header">
        <h2>Tài khoản đăng nhập Google</h2>
        <span>${users.length} người dùng</span>
      </div>
      <div class="panel-body">
        ${users.length === 0 ? `
          <div style="padding:24px;text-align:center;color:var(--muted)">Chưa có người dùng đăng nhập Google.</div>
        ` : `
          <div class="user-grid">
            ${users.map((user) => userPermissionCard(user)).join("")}
          </div>
        `}
      </div>
    </section>
  `;

  document.querySelectorAll("[data-user-permission-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const userId = form.dataset.userPermissionForm;
      const permissions = Array.from(form.querySelectorAll("input[name='permissions']:checked")).map((item) => item.value);
      const payload = {
        role: form.role.value,
        is_active: form.is_active.checked,
        permissions,
      };
      const button = form.querySelector("button[type='submit']");
      button.disabled = true;
      try {
        await api(`/api/admin/users/${encodeURIComponent(userId)}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        showToast("Đã cập nhật quyền người dùng.");
        renderUsers();
      } catch (error) {
        showToast(error.message, true);
        button.disabled = false;
      }
    });
  });
}

function userPermissionCard(user) {
  const permissions = Array.isArray(user.permissions) ? user.permissions : [];
  return `
    <article class="user-card">
      <div class="user-card-head">
        <div class="user-avatar">
          ${user.avatar_url ? `<img src="${escapeHtml(user.avatar_url)}" alt="">` : `<span>${escapeHtml((user.name || user.email || "U").slice(0, 1).toUpperCase())}</span>`}
        </div>
        <div>
          <h3>${escapeHtml(user.name || user.email)}</h3>
          <p>${escapeHtml(user.email)}</p>
          <span class="status-pill ${user.is_active ? "completed" : "cancelled"}">${user.is_active ? "Đang hoạt động" : "Đã khóa"}</span>
        </div>
      </div>

      <form data-user-permission-form="${user.id}">
        <label>Vai trò
          <select name="role">
            ${Object.entries(USER_ROLE_LABELS).map(([value, label]) => `
              <option value="${value}" ${user.role === value ? "selected" : ""}>${label}</option>
            `).join("")}
          </select>
        </label>

        <fieldset class="permission-list">
          <legend>Quyền truy cập</legend>
          ${Object.entries(USER_PERMISSION_LABELS).map(([value, label]) => `
            <label class="checkbox-label">
              <input type="checkbox" name="permissions" value="${value}" ${permissions.includes(value) ? "checked" : ""}>
              <span>${label}</span>
            </label>
          `).join("")}
        </fieldset>

        <label class="checkbox-label">
          <input name="is_active" type="checkbox" ${user.is_active ? "checked" : ""}>
          <span>Cho phép đăng nhập</span>
        </label>

        <div class="actions">
          <button type="submit" class="btn-primary">Lưu quyền</button>
        </div>
      </form>
    </article>
  `;
}

// ==================================================
// 9. MEDIA LIBRARY
// ==================================================
async function renderMedia() {
  setTitle("Media Library - Thư viện hình ảnh");
  content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)">Đang tải thư viện media...</div>`;
  const items = await api("/api/admin/media");

  content.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-wrap:wrap;gap:12px">
      <p style="margin:0;color:var(--muted)">Tất cả hình ảnh đã tải lên hệ thống. Bạn có thể sao chép đường dẫn hoặc xóa ảnh không còn sử dụng.</p>
      <div>
        <input type="file" id="media-direct-upload" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" style="display:none">
        <button type="button" class="btn-primary" id="btn-media-upload">⬆ Tải ảnh lên</button>
      </div>
    </div>

    <div class="grid" style="grid-template-columns:repeat(auto-fill, minmax(240px, 1fr))">
      ${items.map((item) => `
        <article class="panel media-card">
          <div class="panel-body">
            <div class="media-thumbnail-wrapper" data-lightbox-trigger="${escapeHtml(item.url)}">
              <img src="${escapeHtml(item.url)}" alt="${escapeHtml(item.filename)}" loading="lazy">
            </div>
            <h4>${escapeHtml(item.filename)}</h4>
            <div class="media-meta">
              <span>${Math.round(item.size / 1024)} KB</span>
              <span class="in-use-badge ${item.in_use ? "yes" : "no"}">
                ${item.in_use ? "Đang sử dụng" : "Chưa sử dụng"}
              </span>
            </div>
            <div class="actions" style="margin-top:auto">
              <button type="button" class="ghost" style="flex:1" data-copy-url="${escapeHtml(item.url)}">📋 Copy Link</button>
              <button type="button" class="danger" data-delete-media="${escapeHtml(item.filename)}" ${item.in_use ? 'title="Ảnh đang được website sử dụng" disabled' : ""}>🗑</button>
            </div>
          </div>
        </article>
      `).join("")}
    </div>
  `;

  // Direct upload
  const fileInput = document.getElementById("media-direct-upload");
  const uploadBtn = document.getElementById("btn-media-upload");
  if (uploadBtn && fileInput) {
    uploadBtn.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", async () => {
      if (fileInput.files && fileInput.files[0]) {
        uploadBtn.disabled = true;
        uploadBtn.textContent = "Đang tải...";
        try {
          const fd = new FormData();
          fd.append("file", fileInput.files[0]);
          await api("/api/admin/media", { method: "POST", body: fd });
          showToast("Đã tải ảnh lên thư viện.");
          renderMedia();
        } catch (err) {
          showToast(err.message, true);
          uploadBtn.disabled = false;
          uploadBtn.textContent = "⬆ Tải ảnh lên";
        }
      }
    });
  }

  // Lightbox trigger
  document.querySelectorAll("[data-lightbox-trigger]").forEach((el) => {
    el.addEventListener("click", () => openLightbox(el.dataset.lightboxTrigger));
  });

  // Copy URL
  document.querySelectorAll("[data-copy-url]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const url = window.location.origin + btn.dataset.copyUrl;
      await navigator.clipboard.writeText(url).catch(() => {});
      const originalText = btn.textContent;
      btn.textContent = "✓ Đã chép!";
      setTimeout(() => { btn.textContent = originalText; }, 2000);
      showToast("Đã sao chép đường dẫn hình ảnh.");
    });
  });

  // Delete media
  document.querySelectorAll("[data-delete-media]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const filename = btn.dataset.deleteMedia;
      if (!confirm(`Bạn có chắc chắn muốn xóa tập tin "${filename}" khỏi hệ thống?`)) return;
      try {
        await api(`/api/admin/media/${encodeURIComponent(filename)}`, { method: "DELETE" });
        showToast("Đã xóa ảnh thành công.");
        renderMedia();
      } catch (err) {
        showToast(err.message, true);
      }
    });
  });
}

// ==================================================
// 10. SETTINGS & SECRETS INFO
// ==================================================
function renderSettingsInfo() {
  setTitle("Cài đặt hệ thống");
  content.innerHTML = `
    <section class="panel">
      <div class="panel-header"><h2>Bảo mật & Cấu hình</h2></div>
      <div class="panel-body">
        <p><strong>Nguyên tắc bảo mật:</strong></p>
        <ul>
          <li>Các thông tin bí mật như Google Cloud Service Account, Vertex AI Gemini Key, Secret Key, Database Password <strong>KHÔNG</strong> hiển thị trong Admin Dashboard.</li>
          <li>Cấu hình bảo mật được quản lý độc quyền qua biến môi trường (Environment Variables / <code>.env</code>).</li>
          <li>Admin Dashboard được thiết kế chuyên biệt để quản trị <strong>NỘI DUNG VÀ HÌNH ẢNH</strong> của website.</li>
        </ul>
      </div>
    </section>
  `;
}

// ==================================================
// ROUTER & APP INITIALIZATION
// ==================================================
async function route() {
  const path = window.location.pathname;
  try {
    if (path === "/admin" || path === "/admin/") return renderOverview();
    if (path === "/admin/images") return renderImages();
    if (path === "/admin/services") return renderServices();
    if (path === "/admin/content") return renderContent();
    if (path === "/admin/company") return renderCompany();
    if (path === "/admin/leads") return renderLeads();
    if (path.startsWith("/admin/leads/")) return renderLeadDetail(path.split("/").pop());
    if (path === "/admin/chats") return renderChats();
    if (path.startsWith("/admin/chats/")) return renderChatDetail(path.split("/").pop());
    if (path === "/admin/users") return renderUsers();
    if (path === "/admin/media") return renderMedia();
    if (path === "/admin/settings") return renderSettingsInfo();
    return renderOverview();
  } catch (error) {
    content.innerHTML = `
      <section class="panel">
        <div class="panel-body">
          <p style="color:var(--danger)">Lỗi: ${escapeHtml(error.message)}</p>
        </div>
      </section>
    `;
  }
}

// SPA link interception
document.addEventListener("click", (event) => {
  const link = event.target.closest("a[href^='/admin']");
  if (link && !event.ctrlKey && !event.metaKey && link.target !== "_blank") {
    event.preventDefault();
    history.pushState(null, "", link.href);
    if (sidebar) sidebar.classList.remove("open");
    if (backdrop) {
      backdrop.setAttribute("hidden", "");
      backdrop.style.display = "none";
    }
    route();
  }
});

window.addEventListener("popstate", route);

// Hamburger menu toggle
const menuToggle = document.querySelector("[data-menu-toggle]");
if (menuToggle && sidebar) {
  menuToggle.addEventListener("click", () => {
    const isOpen = sidebar.classList.toggle("open");
    if (backdrop) {
      if (isOpen) {
        backdrop.removeAttribute("hidden");
        backdrop.style.display = "block";
      } else {
        backdrop.setAttribute("hidden", "");
        backdrop.style.display = "none";
      }
    }
  });
}

if (backdrop && sidebar) {
  backdrop.addEventListener("click", () => {
    sidebar.classList.remove("open");
    backdrop.setAttribute("hidden", "");
    backdrop.style.display = "none";
  });
}

// Logout
const logoutBtn = document.querySelector("[data-logout]");
if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    try {
      await api("/api/admin/auth/logout", { method: "POST", body: "{}" });
    } catch (_) {}
    window.location.href = "/admin/login";
  });
}

// Check logged in user
api("/api/admin/me").then((me) => {
  if (me && me.email) {
    const el = document.querySelector("[data-admin-email]");
    if (el) el.textContent = `👤 ${me.email}`;
  }
});

consumeLoginSuccessParam();
route();
