// static/js/public/app.js
// Minimal site interactions: safe-hash links, create bootstrap toasts from a global TOASTS var (optional).

(function() {
    "use strict";

    // Prevent href="#" from jumping to top
    document.addEventListener("click", function(e) {
        const a = e.target.closest && e.target.closest("a[href='#']");
        if (a) {
            e.preventDefault();
        }
    });

    // Initialize any server-provided toasts
    // Server can pass a JS variable "FLASH_TOASTS" in a <script> block with objects {title, body, autohide, delay, type}
    function showToast(opts) {
        const container = document.getElementById("toast-container");
        if (!container) return;
        const id = "toast-" + Date.now() + Math.floor(Math.random() * 999);
        const autohide = (opts.autohide === false) ? false : true;
        const delay = opts.delay || 4000;
        const cls = opts.type === "error" ? "bg-danger text-white" : (opts.type === "success" ? "bg-success text-white" : "");
        const html = `
        <div id="${id}" class="toast ${cls}" role="status" aria-live="polite" aria-atomic="true" data-bs-autohide="${autohide}" data-bs-delay="${delay}">
          <div class="toast-header ${cls ? 'text-white' : ''}">
            <strong class="me-auto">${opts.title || ''}</strong>
            <small class="text-muted ms-2 text-white-50">${opts.when || ''}</small>
            <button type="button" class="btn-close btn-close-white ms-2 mb-1" data-bs-dismiss="toast" aria-label="Close"></button>
          </div>
          <div class="toast-body">${opts.body || ''}</div>
        </div>`;
        container.insertAdjacentHTML('beforeend', html);
        const toastEl = document.getElementById(id);
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    }

    // if the server injected FLASH_TOASTS array, show them now
    try {
        if (window.FLASH_TOASTS && Array.isArray(window.FLASH_TOASTS)) {
            window.FLASH_TOASTS.forEach(t => showToast(t));
        }
    } catch (err) {
        console.error("Toast init error", err);
    }

})();