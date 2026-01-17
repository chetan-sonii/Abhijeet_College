// static/js/public/staff.js
(function () {
  function escapeHtml(s) {
    if (!s) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function renderStaff(items) {
    const grid = document.getElementById("staff-grid");
    if (!grid) return;
    if (!Array.isArray(items) || items.length === 0) {
      grid.innerHTML = '<div class="col-12"><div class="alert alert-info">No faculty found.</div></div>';
      return;
    }
    // fade-out then replace for smoothness
    grid.style.opacity = "0";
    setTimeout(() => {
      grid.innerHTML = items.map(f => `
        <div class="col-6 col-md-4 col-lg-3 staff-item">
          <div class="card staff-card h-100 text-center p-3">
            <img src="${escapeHtml(f.image || '')}" class="rounded-circle mx-auto d-block" alt="${escapeHtml(f.name)}" style="width:96px;height:96px;object-fit:cover;">
            <div class="card-body p-2">
              <h6 class="mb-0">${escapeHtml(f.name)}</h6>
              <small class="text-muted d-block">${escapeHtml(f.designation)}</small>
              <small class="text-muted d-block">${escapeHtml(f.department)}</small>
              <p class="small text-muted mt-2 mb-0">${escapeHtml(f.bio || '').slice(0,120)}${(f.bio && f.bio.length>120)?'…':''}</p>
            </div>
          </div>
        </div>
      `).join("");
      grid.style.opacity = "1";
    }, 180);
  }

  async function loadStaff(deptId) {
    const url = deptId ? `/api/staff?department=${encodeURIComponent(deptId)}` : `/api/staff`;
    try {
      const res = await fetch(url, { credentials: "same-origin" });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        if (err && err.staff) {
          renderStaff(err.staff);
          return;
        }
        throw new Error("Network response not ok");
      }
      const data = await res.json();
      renderStaff(data.staff || []);
    } catch (e) {
      console.error("Failed to load staff", e);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    const filter = document.getElementById("staff-dept-filter");
    if (!filter) return;

    filter.addEventListener("change", function () {
      const val = filter.value || "";
      loadStaff(val);
    });

    // initial: if user selected department via UI (server fallback), keep it; otherwise load default
    loadStaff(filter.value || "");
  });
})();
