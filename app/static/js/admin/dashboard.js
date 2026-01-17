// static/js/admin/dashboard.js
document.addEventListener("DOMContentLoaded", function () {
  const refreshBtn = document.getElementById("refresh-dashboard");

  async function fetchJson(url) {
    const res = await fetch(url, {
      credentials: "same-origin",
      headers: { "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" }
    });
    if (!res.ok) throw new Error("Network response was not ok");
    return res.json();
  }

  async function refreshStats() {
    try {
      const data = await fetchJson("/admin/api/stats");
      if (data && data.status === "ok" && data.stats) {
        const s = data.stats;
        document.getElementById("stat-total-apps").textContent = s.total_apps;
        document.getElementById("stat-new-apps").textContent = s.new_apps;
        document.getElementById("stat-total-contacts").textContent = s.total_contacts;
        document.getElementById("stat-unread-contacts").textContent = s.unread_contacts;
        document.getElementById("stat-pending-users").textContent = s.pending_users;
        document.getElementById("stat-total-users").textContent = s.total_users;
        document.getElementById("stat-courses").textContent = s.courses;
        document.getElementById("stat-students").textContent = s.students;
        document.getElementById("stat-faculty").textContent = s.faculty;
      }
    } catch (err) {
      console.error("refreshStats error", err);
    }
  }

  async function refreshRecentApps() {
    try {
      const data = await fetchJson("/admin/api/recent_applications?limit=8");
      if (data && data.status === "ok") {
        const tbody = document.getElementById("recent-apps-body");
        if (!tbody) return;
        tbody.innerHTML = data.applications.length ? data.applications.map(a => `
          <tr>
            <td>${a.id}</td>
            <td>${escapeHtml(a.name)} <div class="small text-muted">${escapeHtml(a.email)}</div></td>
            <td>${escapeHtml(a.program || '—')}</td>
            <td>${escapeHtml(a.status)}</td>
            <td>${formatDate(a.created_at)}</td>
          </tr>
        `).join("") : `<tr><td colspan="5" class="text-center small text-muted">No applications yet</td></tr>`;
      }
    } catch (err) {
      console.error("refreshRecentApps error", err);
    }
  }

  async function refreshRecentContacts() {
    try {
      const data = await fetchJson("/admin/api/recent_contacts?limit=8");
      if (data && data.status === "ok") {
        const tbody = document.getElementById("recent-contacts-body");
        if (!tbody) return;
        tbody.innerHTML = data.contacts.length ? data.contacts.map(c => `
          <tr>
            <td>${c.id}</td>
            <td>${escapeHtml(c.name)} <div class="small text-muted">${escapeHtml(c.email)}</div></td>
            <td>${escapeHtml(c.subject || '—')}</td>
            <td>${c.is_read ? 'Yes' : 'No'}</td>
            <td>${formatDate(c.created_at)}</td>
          </tr>
        `).join("") : `<tr><td colspan="5" class="text-center small text-muted">No contacts yet</td></tr>`;
      }
    } catch (err) {
      console.error("refreshRecentContacts error", err);
    }
  }

  function escapeHtml(s) {
    if (!s) return "";
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function formatDate(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      return d.toLocaleString();
    } catch {
      return iso;
    }
  }

  // initial load
  refreshStats();
  refreshRecentApps();
  refreshRecentContacts();

  if (refreshBtn) {
    refreshBtn.addEventListener("click", function () {
      refreshBtn.disabled = true;
      refreshBtn.textContent = "Refreshing…";
      Promise.all([refreshStats(), refreshRecentApps(), refreshRecentContacts()]).finally(() => {
        refreshBtn.disabled = false;
        refreshBtn.textContent = "Refresh";
      });
    });
  }
});
