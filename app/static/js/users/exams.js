// static/js/users/exams.js
document.addEventListener("DOMContentLoaded", async function(){
  const area = document.getElementById("my-exams-area");
  area.innerHTML = '<div class="small text-muted">Loading…</div>';
  try {
    const res = await fetch("/users/api/exams", {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest"}});
    const data = await res.json();
    if(!data || data.status !== "ok"){ area.innerHTML = '<div class="text-danger">Failed to load</div>'; return; }
    const rows = data.exams || [];
    if(!rows.length){ area.innerHTML = '<div class="small text-muted">No exams scheduled</div>'; return; }
    area.innerHTML = rows.map(r => {
      const resultHtml = (r.result && (r.result.marks_obtained !== null)) ? `<div class="small text-success">Marks: ${r.result.marks_obtained} · Grade: ${escapeHtml(r.result.grade || '')}</div>` : '<div class="small text-muted">Result pending</div>';
      return `<div class="exam-card"><strong>${escapeHtml(r.title)}</strong><div class="small text-muted">${new Date(r.exam_date).toLocaleString()}</div>${resultHtml}</div>`;
    }).join("");
  } catch (err) {
    area.innerHTML = '<div class="text-danger">Failed to load</div>';
  }

  function escapeHtml(s){ if(!s && s !== 0) return ""; return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
});
