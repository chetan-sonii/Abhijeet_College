// static/js/public/contact.js
document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("contact-form");
  if (!form) return;

  var submitBtn = document.getElementById("contact-submit");

  form.addEventListener("submit", function (e) {
    if (!window.fetch) return true; // fallback to normal POST

    e.preventDefault();
    submitBtn.disabled = true;
    submitBtn.innerText = "Sending…";

    var fd = new FormData(form);

    fetch(form.action, {
      method: "POST",
      body: fd,
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
      }
    }).then(function (resp) {
      return resp.json().catch(function () { return { status: "error", message: "Invalid response" }; });
    }).then(function (data) {
      if (data && data.status === "ok") {
        showToast("Message sent — we'll reply soon.", "success");
        form.reset();
      } else {
        showToast(data && data.message ? data.message : "Send failed. Try again.", "danger");
      }
    }).catch(function (err) {
      console.error("Contact submit failed:", err);
      showToast("Network error. Try again later.", "danger");
    }).finally(function () {
      submitBtn.disabled = false;
      submitBtn.innerText = "Send message";
    });
  });

  function showToast(message, category) {
    var container = document.querySelector(".toast-container");
    if (!container) {
      alert(message);
      return;
    }
    var t = document.createElement("div");
    t.className = "toast align-items-center text-bg-" + (category || "info") + " border-0";
    t.setAttribute("role", "alert");
    t.setAttribute("aria-live", "assertive");
    t.setAttribute("aria-atomic", "true");
    t.setAttribute("data-bs-delay", "4000");
    t.innerHTML = '<div class="d-flex"><div class="toast-body">' + escapeHtml(message) + '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>';
    container.appendChild(t);
    var b = new bootstrap.Toast(t);
    b.show();
    t.addEventListener('hidden.bs.toast', function () { t.remove(); });
  }

  function escapeHtml(s) {
    return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
});
