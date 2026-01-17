// static/js/admin/notices.js
document.addEventListener("DOMContentLoaded", function(){
  const modal = new bootstrap.Modal(document.getElementById("noticeModal"));
  document.getElementById("notice-create-btn").addEventListener("click", ()=> modal.show());
  document.querySelectorAll(".delete-notice").forEach(btn => btn.addEventListener("click", async (e) => {
    const id = e.currentTarget.dataset.id;
    if(!confirm("Delete notice?")) return;
    const res = await fetch(`/admin/api/notices/${id}/delete`, {method:"POST", credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json"}});
    const data = await res.json().catch(()=>({status:"error"}));
    if(data.status === "ok") location.reload();
    else alert("Delete failed");
  }));

  document.getElementById("notice-form").addEventListener("submit", async function(ev){
    ev.preventDefault();
    const payload = {title: document.getElementById("notice-title").value, category: document.getElementById("notice-category").value, body: document.getElementById("notice-body").value};
    const res = await fetch("/admin/api/notices/create", {method:"POST", credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json","Content-Type":"application/json"}, body: JSON.stringify(payload)});
    const data = await res.json().catch(()=>({status:"error"}));
    if(data.status === "ok"){ modal.hide(); location.reload(); } else alert("Create failed");
  });
});
