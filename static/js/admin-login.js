const form = document.querySelector("[data-login-form]");
const message = document.querySelector("[data-login-message]");

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
  const payload = Object.fromEntries(new FormData(form).entries());
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
