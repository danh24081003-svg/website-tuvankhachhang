const form = document.querySelector("[data-login-form]");
const message = document.querySelector("[data-login-message]");

document.querySelectorAll("[data-no-autofill]").forEach((input) => {
  input.value = "";
  setTimeout(() => {
    input.value = "";
    input.removeAttribute("readonly");
  }, 250);
});

const params = new URLSearchParams(window.location.search);
if (params.get("error") === "not_admin") {
  message.textContent = "Tài khoản này chưa được cấp quyền admin.";
  history.replaceState({}, document.title, window.location.pathname);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Có lỗi xảy ra.");
  return data;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "Đang đăng nhập...";
  const formData = new FormData(form);
  const payload = {
    email: String(formData.get("admin_email") || "").trim(),
    password: String(formData.get("admin_password") || ""),
  };
  try {
    await requestJson("/api/admin/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    window.location.href = "/admin";
  } catch (error) {
    message.textContent = error.message || "Đăng nhập thất bại.";
  }
});
