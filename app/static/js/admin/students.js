// static/js/admin/students.js
document.addEventListener("DOMContentLoaded", function(){
  const modalEl = document.getElementById("studentViewModal");
  if(!modalEl) return;
  const modal = new bootstrap.Modal(modalEl);
  const body = document.getElementById("student-modal-body");

  document.querySelectorAll(".view-student").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const sid = e.currentTarget.dataset.id;
      if(!sid) return;
      body.innerHTML = '<div class="text-center small text-muted">Loading…</div>';
      modal.show();
      try {
        const res = await fetch(`/admin/api/students/${sid}`, {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json"}});
        const data = await res.json();
        if(data.status !== "ok"){ body.innerHTML = '<div class="text-danger">Failed to load</div>'; return; }
        const p = data.profile || {};
        const enrolls = data.enrollments || [];
        const payments = data.payments || [];
        const fee_structures = data.fee_structures || [];
        let html = `<div class="row">
          <div class="col-md-6">
            <h5>${escapeHtml(p.full_name || '')}</h5>
            <div class="small text-muted">${escapeHtml(p.email || '')} ${p.phone? '<br>'+escapeHtml(p.phone):''}</div>
            <dl class="row mt-3">
              <dt class="col-sm-4">Department</dt><dd class="col-sm-8">${escapeHtml(p.department || '')}</dd>
              <dt class="col-sm-4">Class / Year</dt><dd class="col-sm-8">${escapeHtml(p.year || '')}</dd>
              <dt class="col-sm-4">Reg. No.</dt><dd class="col-sm-8">${escapeHtml(p.registration_no || '')}</dd>
            </dl>
          </div>
          <div class="col-md-6">
            <h6>Payments</h6>
            <div>${payments.length ? payments.map(px => `<div class="small">₹ ${px.amount} — ${px.method || ''} <div class="text-muted small">${px.created_at? new Date(px.created_at).toLocaleString():''}</div></div>`).join('') : '<div class="small text-muted">No payments</div>'}</div>
            <div class="mt-3">
              <strong>Total paid:</strong> ₹ ${data.total_paid || 0}
            </div>
          </div>
        </div>`;

        html += `<hr><h6>Enrollments</h6>`;
        if(enrolls.length){
          html += `<ul>`;
          enrolls.forEach(en => {
            html += `<li><strong>${escapeHtml(en.course_title || '')}</strong> — ${escapeHtml(en.section_code || '')} <div class="small text-muted">Semester: ${escapeHtml(en.semester || '')} · Status: ${escapeHtml(en.status || '')}</div></li>`;
          });
          html += `</ul>`;
        } else {
          html += `<div class="small text-muted">No enrollments</div>`;
        }

        if(fee_structures.length){
          html += `<hr><h6>Applicable fees (department)</h6><ul>`;
          fee_structures.forEach(f => {
            html += `<li><strong>${escapeHtml(f.name)}</strong> — ₹ ${escapeHtml(f.amount)} <div class="small text-muted">${escapeHtml(f.description || '')}</div></li>`;
          });
          html += `</ul>`;
        }

        body.innerHTML = html;
      } catch (err) {
        body.innerHTML = '<div class="text-danger">Failed to load</div>';
        console.error(err);
      }
    });
  });

  function escapeHtml(s){ if(!s) return ""; return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
});
