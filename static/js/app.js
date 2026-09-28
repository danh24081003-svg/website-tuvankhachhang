const state = {
  services: [],
  sessionId: null,
  clientId: null,
  conversationId: null,
  chatOpened: false,
  isExpanded: false,
  currentServiceName: null,
  currentServiceSlug: null,
  sending: false,
  lastFailedMessage: null,
  newConversationPending: false,
  hasUserMessages: false,
  historyOpen: false,
  pendingFiles: [],
};

const selectors = {
  services: document.querySelector("[data-services]"),
  servicesPrev: document.querySelector("[data-services-prev]"),
  servicesNext: document.querySelector("[data-services-next]"),
  footerServices: document.querySelector("[data-footer-services]"),
  serviceSelect: document.querySelector("[data-service-select]"),
  leadForm: document.querySelector("[data-lead-form]"),
  leadStatus: document.querySelector("[data-lead-status]"),
  chatWidget: document.querySelector("[data-chat-widget]"),
  chatFab: document.querySelector("[data-chat-fab]"),
  chatToggleExpand: document.querySelector("[data-toggle-expand]"),
  chatMessages: document.querySelector("[data-chat-messages]"),
  chatForm: document.querySelector("[data-chat-form]"),
  quickReplies: document.querySelector("[data-quick-replies]"),
  chatStatus: document.querySelector("[data-chat-status]"),
  chatAttachmentPreview: document.querySelector("[data-chat-attachment-preview]"),
  chatFileInput: document.querySelector("[data-chat-file-input]"),
  chatAttachBtn: document.querySelector("[data-chat-attach-btn]"),
  chatLightbox: document.querySelector("[data-chat-lightbox]"),
  chatLightboxImg: document.querySelector("[data-chat-lightbox-img]"),
  chatLightboxClose: document.querySelector("[data-chat-lightbox-close]"),
  menuToggle: document.querySelector("[data-menu-toggle]"),
  mainNav: document.querySelector("[data-main-nav]"),
  header: document.querySelector("[data-site-header]"),
};

const pageContext = {
  currentPage: document.body.dataset.currentPage || (
    window.location.pathname.startsWith("/dich-vu/") ? "service_detail" :
    window.location.pathname === "/dich-vu" ? "services_index" :
    window.location.pathname === "/" ? "home" : "other"
  ),
  serviceSlug: document.body.dataset.serviceSlug || null,
  serviceName: document.body.dataset.serviceName || null,
};

const SERVICE_PHOTOS = {
  "van-chuyen-di-doi": "/static/img/services/van-chuyen-di-doi.png",
  "ve-sinh-cong-nghiep": "/static/img/services/ve-sinh-cong-nghiep.png",
  "trang-tri-sua-chua": "/static/img/services/trang-tri-sua-chua.png",
  "cung-cap-quan-ly-lao-dong": "/static/img/services/cung-cap-quan-ly-lao-dong.png",
  "giup-viec": "/static/img/services/giup-viec.png",
  "cham-soc-cay-canh": "/static/img/services/cham-soc-cay-canh.png",
  "diet-con-trung": "/static/img/services/diet-con-trung.png",
};

const SERVICE_ICONS = {
  "van-chuyen-di-doi": `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13"></rect><polygon points="16 8 20 8 23 11 23 16 16 16 16 16 8"></polygon><circle cx="5.5" cy="18.5" r="2.5"></circle><circle cx="18.5" cy="18.5" r="2.5"></circle></svg>`,
  "ve-sinh-cong-nghiep": `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>`,
  "trang-tri-sua-chua": `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
  "cung-cap-quan-ly-lao-dong": `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  "giup-viec": `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
  "cham-soc-cay-canh": `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  "diet-con-trung": `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h2v4a4 4 0 0 0 8 0v-4h2a2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z"/></svg>`
};

let siteImages = {};

function makeSessionId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function makeClientMessageId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getSessionId() {
  const existing = localStorage.getItem("customer_ai_session_id");
  if (existing) return existing;
  const created = makeSessionId();
  localStorage.setItem("customer_ai_session_id", created);
  return created;
}

function getClientId() {
  const existing = localStorage.getItem("customer_ai_client_id");
  if (existing) return existing;
  const created = makeSessionId();
  localStorage.setItem("customer_ai_client_id", created);
  return created;
}

function setText(element, text) {
  if (element) element.textContent = text || "";
}

function cleanTel(value) {
  return String(value || "").replace(/[^\d+]/g, "");
}

function openChatLightbox(src) {
  if (!selectors.chatLightbox || !selectors.chatLightboxImg) return;
  selectors.chatLightboxImg.src = src;
  selectors.chatLightbox.hidden = false;
}

function closeChatLightbox() {
  if (!selectors.chatLightbox) return;
  selectors.chatLightbox.hidden = true;
  if (selectors.chatLightboxImg) selectors.chatLightboxImg.src = "";
}

function renderAttachmentPreviews() {
  if (!selectors.chatAttachmentPreview) return;
  selectors.chatAttachmentPreview.replaceChildren();
  if (!state.pendingFiles || state.pendingFiles.length === 0) {
    selectors.chatAttachmentPreview.hidden = true;
    return;
  }
  selectors.chatAttachmentPreview.hidden = false;
  state.pendingFiles.forEach((file, index) => {
    const item = document.createElement("div");
    item.className = "chat-preview-item";

    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.alt = file.name || "Preview";

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "chat-preview-remove";
    removeBtn.textContent = "×";
    removeBtn.title = "Xóa ảnh";
    removeBtn.setAttribute("aria-label", "Xóa ảnh này");
    removeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      state.pendingFiles.splice(index, 1);
      renderAttachmentPreviews();
    });

    item.append(img, removeBtn);
    selectors.chatAttachmentPreview.appendChild(item);
  });
}

function handleAddFiles(fileList) {
  if (!fileList || fileList.length === 0) return;
  const allowed = ["image/jpeg", "image/png", "image/webp"];
  for (let i = 0; i < fileList.length; i++) {
    if (state.pendingFiles.length >= 4) {
      alert("Mỗi tin nhắn chỉ đính kèm tối đa 4 hình ảnh.");
      break;
    }
    const f = fileList[i];
    if (f.size > 5 * 1024 * 1024) {
      alert(`Ảnh "${f.name}" vượt quá kích thước cho phép 5MB.`);
      continue;
    }
    const ext = f.name.split(".").pop().toLowerCase();
    if (!allowed.includes(f.type) && !["jpg", "jpeg", "png", "webp"].includes(ext)) {
      alert(`Tập tin "${f.name}" không đúng định dạng JPG, PNG hoặc WebP.`);
      continue;
    }
    state.pendingFiles.push(f);
  }
  renderAttachmentPreviews();
}

function addMessage(role, message, options = {}) {
  if (!selectors.chatMessages) return null;
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  if (options.welcome) {
    bubble.dataset.welcome = "true";
  }

  if (options.loading) {
    bubble.dataset.loading = "true";
    const typing = document.createElement("div");
    typing.className = "typing";
    for (let i = 0; i < 3; i += 1) {
      typing.appendChild(document.createElement("span"));
    }
    bubble.appendChild(typing);
  } else {
    if (options.attachments && Array.isArray(options.attachments) && options.attachments.length > 0) {
      const imgContainer = document.createElement("div");
      imgContainer.className = "chat-bubble-images";
      options.attachments.forEach((att) => {
        const img = document.createElement("img");
        img.className = "chat-bubble-img";
        const src = typeof att === "string" ? att : (att.url || "");
        img.src = src;
        img.alt = (typeof att === "object" && att.filename) ? att.filename : "Hình ảnh hiện trạng";
        img.loading = "lazy";
        img.addEventListener("click", () => openChatLightbox(src));
        imgContainer.appendChild(img);
      });
      bubble.appendChild(imgContainer);
    }
    if (message && message !== "[Hình ảnh đính kèm]") {
      const textSpan = document.createElement("span");
      setText(textSpan, message);
      bubble.appendChild(textSpan);
    }
  }

  selectors.chatMessages.appendChild(bubble);
  selectors.chatMessages.scrollTop = selectors.chatMessages.scrollHeight;
  if (role === "user" && !options.historyLoad) {
    state.hasUserMessages = true;
  }
  return bubble;
}

function showWelcomeIfEmpty() {
  if (!selectors.chatMessages || selectors.chatMessages.children.length > 0) return;
  const sName = state.currentServiceName || pageContext.serviceName;
  if (sName) {
    addMessage(
      "assistant",
      `Dạ em chào anh/chị 👋 Em thấy anh/chị đang xem dịch vụ ${sName}. Anh/chị muốn em tư vấn thêm phần nào ạ?`,
      { welcome: true }
    );
  } else {
    addMessage(
      "assistant",
      "Xin chào 👋 Em là Trợ lý Oshin. Anh/chị cần em hỗ trợ dịch vụ nào hôm nay?",
      { welcome: true }
    );
  }
}

function openChat() {
  if (!selectors.chatWidget) return;
  selectors.chatWidget.hidden = false;
  selectors.chatWidget.classList.add("is-open");
  document.body.classList.add("chat-is-open");
  if (selectors.chatFab) selectors.chatFab.classList.add("is-hidden");
  state.chatOpened = true;
  showWelcomeIfEmpty();
  if (selectors.chatForm && selectors.chatForm.message) {
    selectors.chatForm.message.focus();
  }
}

function openChatWithService(serviceName, serviceSlug) {
  state.currentServiceName = serviceName;
  if (serviceSlug) {
    state.currentServiceSlug = serviceSlug;
  } else if (serviceName && state.services && state.services.length) {
    const match = state.services.find(
      (s) => s.name && s.name.toLowerCase() === serviceName.toLowerCase()
    );
    if (match) state.currentServiceSlug = match.id;
  }
  openChat();
}

function closeChat() {
  if (!selectors.chatWidget) return;
  selectors.chatWidget.classList.remove("is-open");
  selectors.chatWidget.hidden = true;
  document.body.classList.remove("chat-is-open");
  if (selectors.chatFab) selectors.chatFab.classList.remove("is-hidden");
  state.chatOpened = false;
}

function toggleChatExpand(forceState) {
  if (!selectors.chatWidget) return;
  const next = typeof forceState === "boolean" ? forceState : !state.isExpanded;
  state.isExpanded = next;

  const messagesEl = selectors.chatMessages;
  const isAtBottom = messagesEl ? (messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 60) : true;
  const currentScrollTop = messagesEl ? messagesEl.scrollTop : 0;

  selectors.chatWidget.classList.toggle("is-expanded", next);

  if (selectors.chatToggleExpand) {
    selectors.chatToggleExpand.title = next ? "Thu nhỏ" : "Phóng to";
    selectors.chatToggleExpand.setAttribute("aria-label", next ? "Thu nhỏ khung trò chuyện" : "Phóng to khung trò chuyện");
  }

  try {
    localStorage.setItem("chat_expanded", next ? "true" : "false");
  } catch (e) {}

  if (messagesEl) {
    requestAnimationFrame(() => {
      if (isAtBottom) {
        messagesEl.scrollTop = messagesEl.scrollHeight;
      } else {
        messagesEl.scrollTop = currentScrollTop;
      }
    });
  }
}

function closeMobileMenu() {
  if (!selectors.mainNav || !selectors.menuToggle) return;
  selectors.mainNav.classList.remove("open");
  selectors.menuToggle.setAttribute("aria-expanded", "false");
  document.body.classList.remove("menu-open");
}

async function requestJson(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (state.clientId) {
    headers["x-chat-client-id"] = state.clientId;
  }
  const response = await fetch(url, {
    headers,
    ...options,
  });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (data && data.error) {
      const err = new Error(data.message || "Trợ lý đang tạm thời gián đoạn. Anh/chị vui lòng thử lại sau.");
      err.code = data.error;
      err.retryable = Boolean(data.retryable);
      throw err;
    }
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg || "Dữ liệu chưa hợp lệ").join("; ")
      : data.detail;
    throw new Error(detail || "Có lỗi xảy ra. Vui lòng thử lại.");
  }

  return data;
}

function setChatStatus(available) {
  if (!selectors.chatStatus) return;
  if (available === "busy") {
    selectors.chatStatus.textContent = "Đang bận";
    selectors.chatStatus.classList.add("is-offline");
    return;
  }
  selectors.chatStatus.textContent = available ? "Đang trực tuyến" : "Tạm thời gián đoạn";
  selectors.chatStatus.classList.toggle("is-offline", !available);
}

async function refreshAIStatus() {
  try {
    const status = await requestJson("/api/ai/status");
    setChatStatus(Boolean(status.available));
  } catch (error) {
    setChatStatus(false);
  }
}

async function loadCompany() {
  try {
    const company = await requestJson("/api/company");
    const brandName = company.brand_name || company.company_name || "Oshin Thời Đại";
    const companyName = company.company_name || brandName;
    const slogan = company.slogan || "";
    const hotline = company.hotline || "0901 040 484";
    const tel = cleanTel(hotline) || "0901040484";

    document.querySelectorAll("[data-company-name]").forEach((item) => setText(item, brandName));
    document.querySelectorAll("[data-company-name-bottom]").forEach((item) => setText(item, companyName));
    document.querySelectorAll("[data-company-description]").forEach((item) => setText(item, slogan));
    document.querySelectorAll("[data-company-hotline-text]").forEach((item) => setText(item, hotline));

    document.querySelectorAll("[data-company-hotline]").forEach((item) => {
      setText(item, hotline);
      item.href = `tel:${tel}`;
    });

    updateOptionalCompanyField("[data-company-email]", company.email);
    updateOptionalCompanyField("[data-company-address]", company.address);
    updateOptionalCompanyField("[data-company-hours]", company.working_hours);
  } catch (e) {
    console.warn("Could not load company settings:", e);
  }
}

async function loadSiteContent() {
  try {
    const content = await requestJson("/api/site/content");
    const mapping = {
      hero_eyebrow: ".hero-copy .eyebrow",
      hero_heading: ".hero-copy h1",
      hero_description: ".hero-description",
      hero_cta_text: ".hero-actions .btn-gold",
      why_heading: ".statement-copy h2",
      why_description: ".statement-copy p:not(.eyebrow)",
      final_cta_heading: ".final-cta h2",
      final_cta_button_text: ".final-actions .btn-gold",
    };
    Object.entries(mapping).forEach(([key, selector]) => {
      const element = document.querySelector(selector);
      if (element && content[key]) setText(element, content[key]);
    });
  } catch (e) {
    console.warn("Could not load site content:", e);
  }
}

async function loadSiteImages() {
  try {
    siteImages = await requestJson("/api/site/images");
    updateImage(".media-main img", siteImages.hero_main);
    updateImage(".media-left img, .media-top img", siteImages.hero_secondary_1);
    updateImage(".media-right img, .media-bottom img", siteImages.hero_secondary_2);
    updateImage(".image-break img", siteImages.brand_section || siteImages.brand_team);
  } catch (e) {
    console.warn("Could not load site images:", e);
  }
}

function updateImage(selector, url) {
  const image = document.querySelector(selector);
  if (image && url) image.src = url;
}

function updateOptionalCompanyField(selector, value) {
  document.querySelectorAll(selector).forEach((item) => {
    if (value) {
      setText(item, value);
      item.hidden = false;
    } else {
      item.hidden = true;
    }
  });
}

function createServiceCard(service) {
  const card = document.createElement("article");
  card.className = "service-card reveal";
  card.dataset.slug = service.id;

  const cardLink = document.createElement("a");
  cardLink.href = `/dich-vu/${service.id}`;
  cardLink.className = "service-card-link";
  cardLink.setAttribute("aria-label", `Xem chi tiết dịch vụ ${service.name}`);

  const image = document.createElement("div");
  image.className = "service-image";
  const img = document.createElement("img");
  img.src = service.image_url || siteImages[service.image_key] || SERVICE_PHOTOS[service.id] || "/static/img/placeholder-oshin-service.svg";
  img.alt = service.name;
  img.loading = "lazy";
  image.appendChild(img);

  const content = document.createElement("div");
  content.className = "service-content";

  const iconCircle = document.createElement("div");
  iconCircle.className = "service-icon-circle";
  iconCircle.innerHTML = SERVICE_ICONS[service.id] || `<span class="icon-fallback">★</span>`;

  const title = document.createElement("h3");
  title.className = "service-title";
  setText(title, service.name);

  const desc = document.createElement("p");
  desc.className = "service-desc";
  setText(desc, service.description);

  const footer = document.createElement("div");
  footer.className = "service-card-footer";

  const arrow = document.createElement("span");
  arrow.className = "service-arrow";
  arrow.innerHTML = `Chi tiết <span aria-hidden="true">→</span>`;

  const consultBtn = document.createElement("button");
  consultBtn.type = "button";
  consultBtn.className = "btn-card-consult";
  consultBtn.textContent = "TƯ VẤN →";
  consultBtn.setAttribute("aria-label", `Tư vấn nhanh dịch vụ ${service.name}`);
  consultBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    openChatWithService(service.name, service.id);
  });

  footer.append(arrow, consultBtn);
  content.append(iconCircle, title, desc, footer);
  cardLink.append(image, content);
  card.appendChild(cardLink);
  return card;
}

function setupServicesScroll() {
  if (!selectors.services) return;
  if (selectors.servicesPrev) {
    selectors.servicesPrev.onclick = () => {
      selectors.services.scrollBy({ left: -340, behavior: "smooth" });
    };
  }
  if (selectors.servicesNext) {
    selectors.servicesNext.onclick = () => {
      selectors.services.scrollBy({ left: 340, behavior: "smooth" });
    };
  }
}

async function loadServices() {
  try {
    state.services = await requestJson("/api/services");
    if (selectors.services) {
      selectors.services.replaceChildren();
      state.services.forEach((service) => {
        selectors.services.appendChild(createServiceCard(service));
      });
    }
    if (selectors.serviceSelect) {
      selectors.serviceSelect.replaceChildren(new Option("Chọn dịch vụ...", ""));
      state.services.forEach((service) => {
        selectors.serviceSelect.appendChild(new Option(service.name, service.name));
      });
    }
    if (selectors.footerServices) {
      selectors.footerServices.replaceChildren();
      state.services.forEach((service) => {
        const footerItem = document.createElement("li");
        const footerLink = document.createElement("a");
        footerLink.href = `/dich-vu/${service.id}`;
        footerLink.textContent = service.name;
        footerItem.appendChild(footerLink);
        selectors.footerServices.appendChild(footerItem);
      });
    }
    setupReveal();
    setupServicesScroll();
  } catch (e) {
    console.warn("Could not load services:", e);
  }
}

async function loadChatHistory() {
  if (!selectors.chatMessages) return;
  try {
    const messages = await requestJson(`/api/chat/${encodeURIComponent(state.sessionId)}/messages`);
    selectors.chatMessages.replaceChildren();
    state.hasUserMessages = messages.some((item) => item.role === "user");
    messages.forEach((item) => addMessage(item.role, item.message, { historyLoad: true, attachments: item.attachments }));
    if (messages.length === 0 && state.chatOpened) {
      showWelcomeIfEmpty();
    }
  } catch (e) {
    console.warn("Could not load chat history:", e);
  }
}

function setSending(isSending) {
  state.sending = isSending;
  if (!selectors.chatForm) return;
  const input = selectors.chatForm.message;
  const button = selectors.chatForm.querySelector("button[type='submit']");
  if (input) input.disabled = isSending;
  if (button) button.disabled = isSending;
  if (selectors.chatAttachBtn) selectors.chatAttachBtn.disabled = isSending;
  if (selectors.quickReplies) {
    selectors.quickReplies.querySelectorAll("button").forEach((item) => {
      item.disabled = isSending;
    });
  }
}

function addRetryMessage(message) {
  const bubble = addMessage("assistant", "Trợ lý đang tạm thời gián đoạn. Anh/chị vui lòng thử lại sau hoặc liên hệ 0901 040 484.");
  if (!bubble) return;
  const retry = document.createElement("button");
  retry.type = "button";
  retry.className = "chat-retry-btn";
  retry.textContent = "Thử lại";
  retry.addEventListener("click", () => {
    bubble.remove();
    sendChatMessage(message.text, { showUser: false, clientMessageId: message.clientMessageId, files: message.files, attachment_ids: message.attachment_ids });
  });
  bubble.appendChild(retry);
}

async function sendChatMessage(message, options = {}) {
  const trimmed = (message || "").trim();
  const filesToSend = options.files || [...state.pendingFiles];
  if ((!trimmed && filesToSend.length === 0) || state.sending) return;
  const clientMessageId = options.clientMessageId || makeClientMessageId();

  if (options.showUser !== false) {
    const localPreviews = filesToSend.map((f) => {
      if (typeof f === "string") return { url: f, filename: "image.webp" };
      if (f.url) return f;
      return { url: URL.createObjectURL(f), filename: f.name || "image.webp" };
    });
    addMessage("user", trimmed, { attachments: localPreviews });
  }

  state.pendingFiles = [];
  renderAttachmentPreviews();
  if (selectors.chatFileInput) selectors.chatFileInput.value = "";

  const loading = addMessage("assistant", "", { loading: true });
  setSending(true);

  const activeSlug = state.currentServiceSlug || pageContext.serviceSlug || null;
  const activeName = state.currentServiceName || pageContext.serviceName || null;

  try {
    let attachmentIds = options.attachment_ids || [];
    if (filesToSend.length > 0 && (!attachmentIds || attachmentIds.length === 0)) {
      const formData = new FormData();
      filesToSend.forEach((f) => {
        if (f instanceof File || f instanceof Blob) {
          formData.append("files", f);
        }
      });
      formData.append("session_id", state.sessionId);
      if (state.clientId) formData.append("client_id", state.clientId);

      const uploaded = await requestJson("/api/chat/upload", {
        method: "POST",
        body: formData,
      });
      if (Array.isArray(uploaded)) {
        attachmentIds = uploaded.map((item) => item.id);
      }
    }

    const data = await requestJson("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        session_id: state.sessionId,
        client_id: state.clientId,
        client_message_id: clientMessageId,
        message: trimmed,
        attachment_ids: attachmentIds,
        current_page: pageContext.currentPage,
        service_slug: activeSlug,
        service_name: activeName,
      }),
    });
    loading.remove();
    if (data.conversation_id) {
      state.conversationId = data.conversation_id;
    }
    state.lastFailedMessage = null;
    setChatStatus(true);
    addMessage("assistant", data.reply);

    if (data.quick_actions && Array.isArray(data.quick_actions) && selectors.quickReplies) {
      selectors.quickReplies.replaceChildren();
      data.quick_actions.forEach((act) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = act;
        selectors.quickReplies.appendChild(btn);
      });
    }
  } catch (error) {
    loading.remove();
    state.lastFailedMessage = { text: trimmed, clientMessageId, files: filesToSend, attachment_ids: attachmentIds };
    if (error.code === "AI_TEMPORARILY_UNAVAILABLE" || error.retryable) {
      setChatStatus("busy");
    } else {
      setChatStatus(false);
    }
    addRetryMessage(state.lastFailedMessage);
  } finally {
    setSending(false);
  }
}

function resetChatUI() {
  if (selectors.chatMessages) {
    selectors.chatMessages.replaceChildren();
  }
  if (selectors.quickReplies) {
    selectors.quickReplies.replaceChildren();
  }
  state.currentServiceName = pageContext.serviceName || null;
  state.currentServiceSlug = pageContext.serviceSlug || null;
  state.lastFailedMessage = null;
  state.hasUserMessages = false;
  state.pendingFiles = [];
  renderAttachmentPreviews();
  if (selectors.chatFileInput) selectors.chatFileInput.value = "";
  setSending(false);
  showWelcomeIfEmpty();
}

function setNewConversationControls(disabled) {
  document.querySelectorAll("[data-new-conversation], [data-confirm-new-conversation]").forEach((item) => {
    item.disabled = disabled;
  });
}

function closeNewConversationDialog() {
  const dialog = document.querySelector("[data-new-conversation-dialog]");
  if (dialog) dialog.remove();
}

function showNewConversationError() {
  addMessage("assistant", "Chưa thể bắt đầu cuộc trò chuyện mới. Vui lòng thử lại.");
}

function showNewConversationDialog() {
  if (document.querySelector("[data-new-conversation-dialog]") || !selectors.chatWidget) return;

  const backdrop = document.createElement("div");
  backdrop.className = "chat-confirm-backdrop";
  backdrop.dataset.newConversationDialog = "true";
  backdrop.setAttribute("role", "presentation");

  const dialog = document.createElement("div");
  dialog.className = "chat-confirm";
  dialog.setAttribute("role", "dialog");
  dialog.setAttribute("aria-modal", "true");
  dialog.setAttribute("aria-labelledby", "new-conversation-title");
  dialog.setAttribute("aria-describedby", "new-conversation-description");

  const title = document.createElement("h3");
  title.id = "new-conversation-title";
  title.textContent = "CUỘC TRÒ CHUYỆN MỚI";

  const description = document.createElement("p");
  description.id = "new-conversation-description";
  description.textContent = "Bắt đầu cuộc trò chuyện mới? Cuộc trò chuyện hiện tại vẫn được lưu lại.";

  const actions = document.createElement("div");
  actions.className = "chat-confirm-actions";

  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.className = "chat-confirm-cancel";
  cancelButton.textContent = "Hủy";
  cancelButton.addEventListener("click", closeNewConversationDialog);

  const confirmButton = document.createElement("button");
  confirmButton.type = "button";
  confirmButton.className = "chat-confirm-primary";
  confirmButton.dataset.confirmNewConversation = "true";
  confirmButton.textContent = "Bắt đầu mới";
  confirmButton.addEventListener("click", async () => {
    confirmButton.textContent = "Đang tạo...";
    await startNewConversation();
  });

  actions.append(cancelButton, confirmButton);
  dialog.append(title, description, actions);
  backdrop.appendChild(dialog);
  selectors.chatWidget.appendChild(backdrop);
  cancelButton.focus();
}

async function startNewConversation() {
  if (state.newConversationPending) return;

  if (!state.hasUserMessages) {
    closeNewConversationDialog();
    resetChatUI();
    return;
  }

  const oldSessionId = state.sessionId;
  state.newConversationPending = true;
  setNewConversationControls(true);

  try {
    const data = await requestJson("/api/chat/conversations", {
      method: "POST",
      body: JSON.stringify({
        session_id: state.sessionId,
        client_id: state.clientId,
        service_slug: pageContext.serviceSlug || null,
      }),
    });
    if (!data.session_id || data.session_id === oldSessionId) {
      throw new Error("New conversation was not created.");
    }
    state.sessionId = data.session_id;
    state.conversationId = data.conversation_id || null;
    localStorage.setItem("customer_ai_session_id", state.sessionId);
    closeNewConversationDialog();
    resetChatUI();
  } catch (error) {
    console.warn("Could not create new conversation:", error);
    showNewConversationError();
  } finally {
    state.newConversationPending = false;
    setNewConversationControls(false);
  }
}

function formatConversationTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function closeHistoryPanel() {
  const panel = document.querySelector("[data-conversation-history-panel]");
  if (panel) panel.remove();
  state.historyOpen = false;
}

function createConfirmShell(titleText, descriptionText = "") {
  closeNewConversationDialog();
  const backdrop = document.createElement("div");
  backdrop.className = "chat-confirm-backdrop";
  backdrop.dataset.newConversationDialog = "true";
  const dialog = document.createElement("div");
  dialog.className = "chat-confirm";
  dialog.setAttribute("role", "dialog");
  dialog.setAttribute("aria-modal", "true");
  const title = document.createElement("h3");
  title.textContent = titleText;
  dialog.appendChild(title);
  if (descriptionText) {
    const description = document.createElement("p");
    description.textContent = descriptionText;
    dialog.appendChild(description);
  }
  const actions = document.createElement("div");
  actions.className = "chat-confirm-actions";
  const cancel = document.createElement("button");
  cancel.type = "button";
  cancel.className = "chat-confirm-cancel";
  cancel.textContent = "Hủy";
  cancel.addEventListener("click", closeNewConversationDialog);
  const primary = document.createElement("button");
  primary.type = "button";
  primary.className = "chat-confirm-primary";
  actions.append(cancel, primary);
  dialog.appendChild(actions);
  backdrop.appendChild(dialog);
  selectors.chatWidget.appendChild(backdrop);
  return backdrop;
}

async function loadConversationMessages(conversation) {
  try {
    const messages = await requestJson(
      `/api/chat/conversations/${encodeURIComponent(conversation.conversation_id)}/messages?client_id=${encodeURIComponent(state.clientId)}`
    );
    state.sessionId = conversation.session_id;
    state.conversationId = conversation.conversation_id;
    localStorage.setItem("customer_ai_session_id", state.sessionId);
    if (selectors.chatMessages) selectors.chatMessages.replaceChildren();
    if (selectors.quickReplies) selectors.quickReplies.replaceChildren();
    state.hasUserMessages = messages.some((item) => item.role === "user");
    state.lastFailedMessage = null;
    messages.forEach((item) => addMessage(item.role, item.message, { historyLoad: true, attachments: item.attachments }));
    if (messages.length === 0) showWelcomeIfEmpty();
    closeHistoryPanel();
  } catch (error) {
    console.warn("Could not load conversation:", error);
  }
}

async function refreshConversationHistory() {
  const list = document.querySelector("[data-conversation-history-list]");
  if (!list) return;
  list.replaceChildren();
  try {
    const conversations = await requestJson(`/api/chat/conversations?client_id=${encodeURIComponent(state.clientId)}`);
    if (!state.conversationId && state.sessionId) {
      const active = conversations.find((item) => item.session_id === state.sessionId);
      if (active) state.conversationId = active.conversation_id;
    }
    conversations.forEach((conversation) => {
      const row = document.createElement("div");
      row.className = "chat-history-item";
      if (conversation.session_id === state.sessionId) row.classList.add("is-active");

      const openButton = document.createElement("button");
      openButton.type = "button";
      openButton.className = "chat-history-open";
      openButton.addEventListener("click", () => loadConversationMessages(conversation));

      const title = document.createElement("strong");
      title.textContent = conversation.title || "Cuộc trò chuyện mới";
      const time = document.createElement("span");
      time.textContent = formatConversationTime(conversation.last_message_at || conversation.updated_at || conversation.created_at);
      openButton.append(title, time);

      const menuButton = document.createElement("button");
      menuButton.type = "button";
      menuButton.className = "chat-history-menu-btn";
      menuButton.title = "Tùy chọn";
      menuButton.setAttribute("aria-label", "Tùy chọn cuộc trò chuyện");
      menuButton.textContent = "⋯";
      menuButton.addEventListener("click", (event) => {
        event.stopPropagation();
        showConversationMenu(row, conversation);
      });

      row.append(openButton, menuButton);
      list.appendChild(row);
    });
    if (conversations.length === 0) {
      const empty = document.createElement("p");
      empty.className = "chat-history-empty";
      empty.textContent = "Chưa có cuộc trò chuyện nào.";
      list.appendChild(empty);
    }
  } catch (error) {
    const err = document.createElement("p");
    err.className = "chat-history-empty";
    err.textContent = "Chưa tải được lịch sử trò chuyện.";
    list.appendChild(err);
  }
}

function showConversationMenu(row, conversation) {
  document.querySelectorAll("[data-conversation-item-menu]").forEach((item) => item.remove());
  const menu = document.createElement("div");
  menu.className = "chat-history-menu";
  menu.dataset.conversationItemMenu = "true";

  const rename = document.createElement("button");
  rename.type = "button";
  rename.textContent = "Đổi tên";
  rename.addEventListener("click", () => showRenameDialog(conversation));

  const remove = document.createElement("button");
  remove.type = "button";
  remove.textContent = "Xóa cuộc trò chuyện";
  remove.addEventListener("click", () => showDeleteDialog(conversation));

  menu.append(rename, remove);
  row.appendChild(menu);
}

function showRenameDialog(conversation) {
  const backdrop = createConfirmShell("Đổi tên cuộc trò chuyện");
  const input = document.createElement("input");
  input.className = "chat-confirm-input";
  input.maxLength = 80;
  input.value = conversation.title || "Cuộc trò chuyện mới";
  input.setAttribute("aria-label", "Tên cuộc trò chuyện");
  const actions = backdrop.querySelector(".chat-confirm-actions");
  backdrop.querySelector(".chat-confirm").insertBefore(input, actions);
  const primary = actions.querySelector(".chat-confirm-primary");
  primary.textContent = "Lưu";
  primary.addEventListener("click", async () => {
    const title = input.value.trim();
    if (!title) return;
    primary.disabled = true;
    try {
      await requestJson(`/api/chat/conversations/${encodeURIComponent(conversation.conversation_id)}`, {
        method: "PATCH",
        body: JSON.stringify({ client_id: state.clientId, title }),
      });
      closeNewConversationDialog();
      refreshConversationHistory();
    } catch (error) {
      primary.disabled = false;
      console.warn("Could not rename conversation:", error);
    }
  });
  input.focus();
  input.select();
}

function showDeleteDialog(conversation) {
  const backdrop = createConfirmShell("Xóa cuộc trò chuyện?", "Bạn có chắc muốn xóa cuộc trò chuyện này?");
  const primary = backdrop.querySelector(".chat-confirm-primary");
  primary.textContent = "Xóa";
  primary.classList.add("is-danger");
  primary.addEventListener("click", async () => {
    primary.disabled = true;
    try {
      const data = await requestJson(`/api/chat/conversations/${encodeURIComponent(conversation.conversation_id)}`, {
        method: "DELETE",
        body: JSON.stringify({
          client_id: state.clientId,
          active_session_id: state.sessionId,
          service_slug: pageContext.serviceSlug || null,
        }),
      });
      closeNewConversationDialog();
      if (data.session_id) {
        state.sessionId = data.session_id;
        state.conversationId = data.conversation_id || null;
        localStorage.setItem("customer_ai_session_id", state.sessionId);
        resetChatUI();
      }
      refreshConversationHistory();
    } catch (error) {
      primary.disabled = false;
      console.warn("Could not delete conversation:", error);
    }
  });
}

function showConversationHistory() {
  if (!selectors.chatWidget) return;
  if (state.historyOpen) {
    closeHistoryPanel();
    return;
  }
  closeNewConversationDialog();
  const panel = document.createElement("div");
  panel.className = "chat-history-panel";
  panel.dataset.conversationHistoryPanel = "true";
  const header = document.createElement("div");
  header.className = "chat-history-header";
  const title = document.createElement("h3");
  title.textContent = "LỊCH SỬ TRÒ CHUYỆN";
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "×";
  close.setAttribute("aria-label", "Đóng lịch sử trò chuyện");
  close.addEventListener("click", closeHistoryPanel);
  header.append(title, close);
  const list = document.createElement("div");
  list.className = "chat-history-list";
  list.dataset.conversationHistoryList = "true";
  const create = document.createElement("button");
  create.type = "button";
  create.className = "chat-history-new";
  create.textContent = "+ Cuộc trò chuyện mới";
  create.addEventListener("click", () => {
    closeHistoryPanel();
    showNewConversationDialog();
  });
  panel.append(header, list, create);
  selectors.chatWidget.appendChild(panel);
  state.historyOpen = true;
  refreshConversationHistory();
}

function validateLead(payload) {
  if (!payload.name || payload.name.trim().length < 2) {
    return "Anh/chị vui lòng nhập họ và tên.";
  }
  if (!payload.phone || payload.phone.trim().length < 8) {
    return "Anh/chị vui lòng nhập số điện thoại.";
  }
  if (!payload.service) {
    return "Anh/chị vui lòng chọn dịch vụ quan tâm.";
  }
  return "";
}

function setupHeader() {
  if (!selectors.header) return;
  const update = () => {
    selectors.header.classList.toggle("is-scrolled", window.scrollY > 24);
  };
  update();
  window.addEventListener("scroll", update, { passive: true });
}

function setupReveal() {
  const items = document.querySelectorAll(".reveal:not(.is-observed)");
  if (!items.length) return;

  if (!("IntersectionObserver" in window)) {
    items.forEach((item) => item.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );

  items.forEach((item) => {
    item.classList.add("is-observed");
    observer.observe(item);
  });
}

function setupEvents() {
  document.querySelectorAll("[data-open-chat]").forEach((item) => item.addEventListener("click", openChat));
  
  document.querySelectorAll("[data-open-chat-service]").forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const serviceName = item.getAttribute("data-open-chat-service");
      openChatWithService(serviceName);
    });
  });

  if (selectors.chatFab) {
    selectors.chatFab.addEventListener("click", openChat);
  }

  document.querySelectorAll("[data-close-chat]").forEach((item) => {
    item.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      closeChat();
    });
  });

  document.querySelectorAll("[data-new-conversation]").forEach((item) => {
    if (item.parentElement && !item.parentElement.querySelector("[data-conversation-history]")) {
      const historyButton = document.createElement("button");
      historyButton.className = "chat-icon-btn chat-history-toggle";
      historyButton.type = "button";
      historyButton.title = "Lịch sử trò chuyện";
      historyButton.setAttribute("aria-label", "Lịch sử trò chuyện");
      historyButton.dataset.conversationHistory = "true";
      historyButton.textContent = "↺";
      historyButton.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        showConversationHistory();
      });
      item.parentElement.insertBefore(historyButton, item);
    }
    item.setAttribute("title", "Cuộc trò chuyện mới");
    item.setAttribute("aria-label", "Cuộc trò chuyện mới");
    item.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (state.newConversationPending) return;
      if (state.hasUserMessages) {
        showNewConversationDialog();
      } else {
        startNewConversation();
      }
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && selectors.chatWidget && !selectors.chatWidget.hidden) {
      if (state.isExpanded) {
        toggleChatExpand(false);
      } else {
        closeChat();
      }
    }
  });

  if (selectors.chatToggleExpand) {
    selectors.chatToggleExpand.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleChatExpand();
    });
  }

  try {
    if (localStorage.getItem("chat_expanded") === "true") {
      toggleChatExpand(true);
    }
  } catch (e) {}

  if (selectors.menuToggle && selectors.mainNav) {
    selectors.menuToggle.addEventListener("click", () => {
      const isOpen = selectors.mainNav.classList.toggle("open");
      selectors.menuToggle.setAttribute("aria-expanded", String(isOpen));
      document.body.classList.toggle("menu-open", isOpen);
    });

    selectors.mainNav.addEventListener("click", (event) => {
      if (event.target.tagName === "A") closeMobileMenu();
    });
  }

  if (selectors.quickReplies) {
    selectors.quickReplies.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (button) {
        event.preventDefault();
        event.stopPropagation();
        if (state.sending || button.disabled) return;
        openChat();
        sendChatMessage(button.textContent);
      }
    });
  }

  if (selectors.chatAttachBtn && selectors.chatFileInput) {
    selectors.chatAttachBtn.addEventListener("click", () => {
      selectors.chatFileInput.click();
    });
    selectors.chatFileInput.addEventListener("change", () => {
      if (selectors.chatFileInput.files) {
        handleAddFiles(selectors.chatFileInput.files);
      }
    });
  }

  if (selectors.chatLightboxClose) {
    selectors.chatLightboxClose.addEventListener("click", closeChatLightbox);
  }
  if (selectors.chatLightbox) {
    selectors.chatLightbox.addEventListener("click", (e) => {
      if (e.target === selectors.chatLightbox) closeChatLightbox();
    });
  }

  if (selectors.chatForm) {
    selectors.chatForm.addEventListener("submit", (event) => {
      event.preventDefault();
      if (state.sending) return;
      const input = selectors.chatForm.message;
      const message = input ? input.value : "";
      if (input) input.value = "";
      sendChatMessage(message);
    });
  }

  if (selectors.leadForm) {
    selectors.leadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (selectors.leadStatus) {
        selectors.leadStatus.classList.remove("error");
        selectors.leadStatus.textContent = "Đang gửi yêu cầu...";
      }

      const formData = new FormData(selectors.leadForm);
      const payload = Object.fromEntries(formData.entries());
      payload.name = String(payload.name || "").trim();
      payload.phone = String(payload.phone || "").trim();
      payload.service = String(payload.service || "").trim();
      payload.address = String(payload.address || "").trim() || "Chưa cung cấp";
      payload.message = String(payload.message || "").trim() || "Khách chưa cung cấp nội dung yêu cầu.";

      const validationMessage = validateLead(payload);
      if (validationMessage) {
        if (selectors.leadStatus) {
          selectors.leadStatus.classList.add("error");
          selectors.leadStatus.textContent = validationMessage;
        }
        return;
      }

      try {
        await requestJson("/api/leads", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        if (selectors.leadStatus) {
          selectors.leadStatus.textContent = "Dạ bên em đã tiếp nhận thông tin. Nhân viên Oshin Thời Đại sẽ liên hệ với anh/chị sớm nhất ạ.";
        }
        selectors.leadForm.reset();
      } catch (error) {
        if (selectors.leadStatus) {
          selectors.leadStatus.classList.add("error");
          selectors.leadStatus.textContent = error.message || "Chưa gửi được yêu cầu. Anh/chị vui lòng thử lại ạ.";
        }
      }
    });
  }
}

async function init() {
  state.sessionId = getSessionId();
  state.clientId = getClientId();
  setupHeader();
  setupReveal();
  setupEvents();
  try {
    await Promise.all([loadCompany(), loadSiteContent(), loadSiteImages(), refreshAIStatus()]);
    await Promise.all([loadServices(), loadChatHistory()]);
  } catch (error) {
    console.error(error);
  }
}

document.addEventListener("DOMContentLoaded", init);
