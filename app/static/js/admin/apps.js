// static/js/admin/apps.js
document.addEventListener("DOMContentLoaded", function(){
  const listBody = document.getElementById("apps-list-body");
  const modal = new bootstrap.Modal(document.getElementById("adminItemModal"));
  const modalBody = document.getElementById("adminItemModalBody");
  const modalMarkBtn = document.getElementById("modal-mark-btn");
  const modalDeleteBtn = document.getElementById("modal-delete-btn");
  let currentItemId = null;
  let currentItemType = null;

  async function fetchItems(q){
    const url = "/admin/api/apps" + (q ? "?q="+encodeURIComponent(q): "");
    const res = await fetch(url, {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json"}});
    if(!res.ok) return;
    const data = await res.json();
    if(data.status !== "ok") return;
    renderList(data.items);
  }

  function renderList(items){
    if(!listBody) return;
    listBody.innerHTML = items.map(it => `
      <tr data-item-id="${it.id}">
        <td class="text-capitalize">${it.type}</td>
        <td>${escapeHtml(it.name)} <div class="small text-muted">${escapeHtml(it.email)}</div></td>
        <td class="small text-muted">${escapeHtml(it.summary)}</td>
        <td>${escapeHtml(it.status)}</td>
        <td>${it.created_at? new Date(it.created_at).toLocaleString() : ''}</td>
        <td class="text-end">
          <button class="btn btn-sm btn-primary view-item" data-id="${it.id}" data-type="${it.type}">View</button>
          <button class="btn btn-sm btn-danger delete-item" data-id="${it.id}">Delete</button>
        </td>
      </tr>
    `).join("");
    bindButtons();
  }

  function bindButtons(){
    document.querySelectorAll(".view-item").forEach(b => b.addEventListener("click", onView));
    document.querySelectorAll(".delete-item").forEach(b => b.addEventListener("click", onDelete));
  }

  async function onView(e){
    const id = e.currentTarget.dataset.id;
    const type = e.currentTarget.dataset.type;
    currentItemId = id;
    currentItemType = type;
    modalBody.innerHTML = '<div class="text-center small text-muted">Loading…</div>';
    modal.show();
    const res = await fetch(`/admin/api/apps/${encodeURIComponent(id)}`, {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json"}});
    const data = await res.json().catch(()=>({status:"error"}));
    if(data.status !== "ok"){ modalBody.innerHTML = '<div class="text-danger">Failed to load</div>'; return; }
    const t = data.type;
    const d = data.data;
    if(t === "application"){
      modalBody.innerHTML = `<dl class="row">
        <dt class="col-sm-3">Name</dt><dd class="col-sm-9">${escapeHtml(d.name)}</dd>
        <dt class="col-sm-3">Email</dt><dd class="col-sm-9">${escapeHtml(d.email)}</dd>
        <dt class="col-sm-3">Phone</dt><dd class="col-sm-9">${escapeHtml(d.phone || '')}</dd>
        <dt class="col-sm-3">Program</dt><dd class="col-sm-9">${escapeHtml(d.program || '')}</dd>
        <dt class="col-sm-3">Message</dt><dd class="col-sm-9"><pre class="small">${escapeHtml(d.message || '')}</pre></dd>
        <dt class="col-sm-3">Status</dt><dd class="col-sm-9">${escapeHtml(d.status)}</dd>
        <dt class="col-sm-3">Received</dt><dd class="col-sm-9">${d.created_at? new Date(d.created_at).toLocaleString():''}</dd>
      </dl>`;
      modalMarkBtn.textContent = "Mark as reviewed";
      modalDeleteBtn.textContent = "Delete Application";
    } else {
      modalBody.innerHTML = `<dl class="row">
        <dt class="col-sm-3">From</dt><dd class="col-sm-9">${escapeHtml(d.name)} &lt;${escapeHtml(d.email)}&gt;</dd>
        <dt class="col-sm-3">Subject</dt><dd class="col-sm-9">${escapeHtml(d.subject || '')}</dd>
        <dt class="col-sm-3">Message</dt><dd class="col-sm-9"><pre class="small">${escapeHtml(d.message || '')}</pre></dd>
        <dt class="col-sm-3">Read</dt><dd class="col-sm-9">${d.is_read? 'Yes':'No'}</dd>
        <dt class="col-sm-3">Received</dt><dd class="col-sm-9">${d.created_at? new Date(d.created_at).toLocaleString():''}</dd>
      </dl>`;
      modalMarkBtn.textContent = d.is_read? "Mark unread" : "Mark read";
      modalDeleteBtn.textContent = "Delete Message";
    }
  }

  async function onDelete(e){
    const id = e.currentTarget.dataset.id || currentItemId;
    if(!id) return;
    if(!confirm("Delete this item? This cannot be undone.")) return;
    const res = await fetch(`/admin/api/apps/${encodeURIComponent(id)}/delete`, {
      method:"POST", credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json"}
    });
    const data = await res.json().catch(()=>({status:"error"}));
    if(data.status === "ok"){
      modal.hide();
      const row = document.querySelector(`tr[data-item-id="${id}"]`);
      if(row) row.remove();
    } else {
      alert("Delete failed");
    }
  }

  async function onModalMark(){
    if(!currentItemId) return;
    // For applications -> set status = "reviewed"
    // For contacts -> toggle is_read
    let payload = {};
    if(currentItemType === "application"){
      payload.status = "reviewed";
    } else {
      payload = {}; // toggle on server
    }

    const res = await fetch(`/admin/api/apps/${encodeURIComponent(currentItemId)}/mark`, {
      method:"POST",
      credentials:"same-origin",
      headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json","Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
    const data = await res.json().catch(()=>({status:"error"}));
    if(data.status === "ok"){
      // refresh list (simple)
      fetchItems(document.getElementById("apps-search").value.trim());
      modal.hide();
    } else {
      alert("Mark failed");
    }
  }

  document.getElementById("apps-refresh").addEventListener("click", ()=> fetchItems(document.getElementById("apps-search").value.trim()));
  document.getElementById("apps-search").addEventListener("keydown", (e)=> { if(e.key==="Enter") fetchItems(e.target.value.trim()); });

  modalMarkBtn.addEventListener("click", onModalMark);
  modalDeleteBtn.addEventListener("click", onDelete);

  fetchItems();

  function escapeHtml(s){ if(!s) return ""; return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
});
