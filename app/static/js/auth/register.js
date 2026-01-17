// static/js/auth/register.js
document.addEventListener("DOMContentLoaded", function () {
  var pwdToggle = document.getElementById("register-password-toggle");
  var pwdInput = document.getElementById("password");
  var strengthEl = document.getElementById("pwd-strength-value");
  var form = document.getElementById("register-form");

  if (pwdToggle && pwdInput) {
    pwdToggle.addEventListener("click", function () {
      if (pwdInput.type === "password") {
        pwdInput.type = "text";
        pwdToggle.textContent = "Hide";
        pwdToggle.setAttribute("aria-pressed", "true");
      } else {
        pwdInput.type = "password";
        pwdToggle.textContent = "Show";
        pwdToggle.setAttribute("aria-pressed", "false");
      }
    });
  }

  if (pwdInput && strengthEl) {
    pwdInput.addEventListener("input", function () {
      var s = scorePassword(pwdInput.value);
      if (s >= 4) {
        strengthEl.textContent = "Strong";
        strengthEl.style.color = "#198754";
      } else if (s >= 2) {
        strengthEl.textContent = "Fair";
        strengthEl.style.color = "#0d6efd";
      } else if (s === 1) {
        strengthEl.textContent = "Weak";
        strengthEl.style.color = "#ffc107";
      } else {
        strengthEl.textContent = "Very weak";
        strengthEl.style.color = "#dc3545";
      }
    });
  }

  // Basic client-side form check
  if (form) {
    form.addEventListener("submit", function (e) {
      var username = document.getElementById("username").value.trim();
      var email = document.getElementById("email").value.trim();
      var pwd = pwdInput.value || "";

      if (!username || !email || pwd.length < 6) {
        e.preventDefault();
        showInlineError("Please fill required fields correctly. Password must be at least 6 characters.");
        return false;
      }
      // let server handle duplicate username/email
    });
  }

  function showInlineError(msg) {
    var existing = document.querySelector(".auth-inline-error");
    if (existing) existing.remove();
    var el = document.createElement("div");
    el.className = "auth-inline-error alert alert-danger small mt-2";
    el.textContent = msg;
    var cardBody = document.querySelector(".auth-card .card-body");
    if (cardBody) cardBody.insertBefore(el, cardBody.firstChild.nextSibling);
  }

  // simple password scoring
  function scorePassword(p) {
    if (!p) return 0;
    var score = 0;
    if (p.length >= 6) score++;
    if (/[A-Z]/.test(p)) score++;
    if (/[0-9]/.test(p)) score++;
    if (/[^A-Za-z0-9]/.test(p)) score++;
    return score;
  }
});
