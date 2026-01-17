// static/js/users/courses.js (top)
document.addEventListener("DOMContentLoaded", async function(){
  const area = document.getElementById("my-courses-area");
  area.innerHTML = '<div class="small text-muted">Loading…</div>';
  try {
    const res = await fetch("/users/api/courses", {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest"}});
    if (res.status === 401) {
      area.innerHTML = '<div class="text-warning">Please log in to view your courses.</div>';
      return;
    }
    if (res.status === 403) {
      const body = await res.json().catch(()=>({message:"access denied"}));
      area.innerHTML = `<div class="text-warning">Access denied: ${body.message || "You are not allowed to view student pages."}</div>`;
      return;
    }
    const data = await res.json();
    if(!data || data.status !== "ok"){ area.innerHTML = '<div class="text-danger">Failed to load</div>'; return; }
    const rows = data.courses || [];
    if(!rows.length){ area.innerHTML = '<div class="small text-muted">No enrollments</div>'; return; }
    area.innerHTML = rows.map(r => `<div class="course-item"><strong>${escapeHtml(r.course_title || '—')}</strong><div class="small text-muted">${escapeHtml(r.section_code || '')} · ${escapeHtml(r.status || '')}</div></div>`).join("");
  } catch (err) {
    area.innerHTML = '<div class="text-danger">Failed to load</div>';
    console.error("api_my_courses error", err);
  }

  function escapeHtml(s){ if(!s) return ""; return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
});
