// static/js/auth/login.js
document.addEventListener("DOMContentLoaded", function () {
  var pwdToggle = document.getElementById("login-password-toggle");
  var pwdInput = document.getElementById("password");
  var form = document.getElementById("login-form");

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

  // simple client validation to improve UX (does NOT replace server validation)
  if (form) {
    form.addEventListener("submit", function (e) {
      var email = document.getElementById("email").value.trim();
      var pwd = pwdInput.value || "";
      if (!email || pwd.length < 1) {
        e.preventDefault();
        // show inline message as fallback if no server error
        showInlineError("Please enter your email and password.");
      }
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
});
