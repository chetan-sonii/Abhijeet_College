// static/js/public/enroll.js
document.addEventListener("DOMContentLoaded", function () {
  // open modal when floating CTA or admissions button clicked
  var enrollBtn = document.getElementById("enroll-cta");
  var modalToggleBtn = document.getElementById("admit-enroll");
  var enrollModal = new bootstrap.Modal(document.getElementById("enrollModal"), {});

  if (enrollBtn) {
    enrollBtn.addEventListener("click", function (e) {
      e.preventDefault();
      enrollModal.show();
    });
  }
  if (modalToggleBtn) {
    modalToggleBtn.addEventListener("click", function (e) {
      e.preventDefault();
      enrollModal.show();
    });
  }

  // AJAX submit
  var form = document.getElementById("enroll-form");
  if (!form) return;

  form.addEventListener("submit", function (ev) {
    // progressive enhancement: allow normal submit if fetch is not available
    if (!window.fetch) return true;

    ev.preventDefault();
    var submitBtn = document.getElementById("enroll-submit");
    var formData = new FormData(form);
    submitBtn.disabled = true;
    submitBtn.innerText = "Sending…";

    fetch(form.action, {
  method: "POST",
  body: formData,
  credentials: "same-origin",
  headers: {
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json"
  }
})
.then(function (resp) {
      return resp.json().catch(function () { return {status: "error"}; });
    }).then(function (data) {
      if (data && data.status === "ok") {
        // close modal and show toast (base.js must initialize toasts)
        enrollModal.hide();
        showToast("Application submitted — we will contact you soon.", "success");
        form.reset();
      } else {
        showToast((data && data.message) ? data.message : "Submission failed.", "danger");
      }
    }).catch(function (err) {
      console.error("Enroll submit error", err);
      showToast("Network error. Try again later.", "danger");
    }).finally(function () {
      submitBtn.disabled = false;
      submitBtn.innerText = "Send Application";
    });
  });

  // small helper to show a toast (relies on base.js to have .toast-container presence)
  function showToast(message, category) {
    // create toast DOM
    var container = document.querySelector(".toast-container") || document.querySelector(".toast-container");
    if (!container) return alert(message); // last resort
    var toast = document.createElement("div");
    toast.className = "toast align-items-center text-bg-" + (category || "info") + " border-0";
    toast.setAttribute("role","alert");
    toast.setAttribute("aria-live","assertive");
    toast.setAttribute("aria-atomic","true");
    toast.setAttribute("data-bs-delay","4000");
    toast.innerHTML = '<div class="d-flex"><div class="toast-body">' + escapeHtml(message) + '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>';
    container.appendChild(toast);
    var bToast = new bootstrap.Toast(toast);
    bToast.show();
    // remove from DOM after hidden
    toast.addEventListener('hidden.bs.toast', function() { toast.remove(); });
  }

  function escapeHtml(s) {
    return (s || "").toString().replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }
});
