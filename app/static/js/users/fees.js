// static/js/users/fees.js
document.addEventListener("DOMContentLoaded", async function(){
  const area = document.getElementById("fees-area");
  const payBtn = document.getElementById("pay-fees-btn");
  area.innerHTML = '<div class="small text-muted">Loading…</div>';
  let currentRemaining = 0;

  async function loadFees(){
    try {
      const res = await fetch("/users/api/fees", {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest"}});
      const data = await res.json();
      if(!data || data.status !== "ok"){ area.innerHTML = '<div class="text-danger">Failed to load</div>'; return; }
      const fees = data.fees;
      currentRemaining = fees.remaining || 0;
      let html = `<div><strong>Total:</strong> ₹ ${ (fees.total_fees||0).toFixed(2) } </div>`;
      html += `<div><strong>Paid:</strong> ₹ ${ (fees.total_paid||0).toFixed(2) } </div>`;
      html += `<div><strong>Remaining:</strong> ₹ ${ (fees.remaining||0).toFixed(2) } </div>`;
      html += `<hr><h6>Fee breakdown</h6>`;
      if(fees.lines && fees.lines.length){
        html += fees.lines.map(l => `<div class="fee-line"><div>${escapeHtml(l.name)}</div><div>₹ ${ (l.amount||0).toFixed(2) }</div></div>`).join("");
      } else html += '<div class="small text-muted">No fee lines</div>';
      html += '<hr><h6>Payments</h6>';
      if(fees.payments && fees.payments.length){
        html += fees.payments.map(p => `<div class="small">₹ ${ (p.amount||0).toFixed(2) } <div class="text-muted small">${new Date(p.created_at).toLocaleString()}</div></div>`).join("");
      } else html += '<div class="small text-muted">No payments</div>';
      area.innerHTML = html;
    } catch (err) {
      area.innerHTML = '<div class="text-danger">Failed to load</div>';
    }
  }

  payBtn.addEventListener("click", async function(){
    const toPay = prompt("Enter amount to pay (numeric)", currentRemaining.toFixed(2));
    if(!toPay) return;
    const amount = parseFloat(toPay);
    if(isNaN(amount) || amount <= 0){ alert("Invalid amount"); return; }
    try {
      const res = await fetch("/users/api/fees/pay", {
        method: "POST",
        credentials: "same-origin",
        headers: {"Content-Type":"application/json","X-Requested-With":"XMLHttpRequest"},
        body: JSON.stringify({amount: amount, method: "mock"})
      });
      const data = await res.json();
      if(data.status === "ok"){
        alert("Payment recorded (dummy).");
        await loadFees();
      } else {
        alert("Failed to record payment: " + (data.message || ""));
      }
    } catch (err) {
      alert("Failed to record payment");
    }
  });

  await loadFees();

  function escapeHtml(s){ if(!s && s !== 0) return ""; return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
});
