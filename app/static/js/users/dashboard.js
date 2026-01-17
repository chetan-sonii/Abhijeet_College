// static/js/users/dashboard.js
document.addEventListener("DOMContentLoaded", function(){
  async function loadOverview(){
    const res = await fetch("/users/api/overview", {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest"}});
    const data = await res.json().catch(()=>({status:"error"}));
    if(!data || data.status !== "ok"){
      document.getElementById("upcoming-exams").innerHTML = '<div class="text-danger">Failed to load</div>';
      return;
    }
    const d = data.data || {};
    document.getElementById("stat-enroll-count").textContent = d.enroll_count || 0;
    document.getElementById("stat-upcoming-count").textContent = (d.upcoming_exams || []).length;
    document.getElementById("stat-total-fees").textContent = (d.total_fees || 0).toFixed(2);
    document.getElementById("stat-remaining").textContent = (d.remaining || 0).toFixed(2);

    // upcoming
    const ue = d.upcoming_exams || [];
    const ueEl = document.getElementById("upcoming-exams");
    if(!ue.length){ ueEl.innerHTML = '<div class="small text-muted">No upcoming exams</div>'; }
    else {
      ueEl.innerHTML = ue.map(x => `<div class="exam-row"><strong>${escapeHtml(x.title)}</strong> <div class="small text-muted">${new Date(x.exam_date).toLocaleString()}</div></div>`).join("");
    }

    // payments - we reuse fees API to show last 3 payments
    const feesRes = await fetch("/users/api/fees", {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest"}});
    const fdata = await feesRes.json().catch(()=>({status:"error"}));
    const rp = document.getElementById("recent-payments");
    if(!fdata || fdata.status !== "ok"){ rp.innerHTML = '<div class="small text-muted">No payments</div>'; }
    else {
      const pays = fdata.fees.payments || [];
      if(!pays.length) rp.innerHTML = '<div class="small text-muted">No payments made yet</div>';
      else rp.innerHTML = pays.slice(0,5).map(p => `<div class="small">₹ ${p.amount} <div class="text-muted small">${new Date(p.created_at).toLocaleString()}</div></div>`).join("");
    }
  }

  // quick pay button (dummy: opens fees page)
  document.getElementById("quick-pay-btn").addEventListener("click", function(){
    window.location.href = "/users/fees";
  });

  loadOverview();

  function escapeHtml(s){ if(!s) return ""; return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
});
