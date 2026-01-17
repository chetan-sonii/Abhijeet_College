// static/js/admin/courses.js (updated)
document.addEventListener("DOMContentLoaded", function(){
  const modal = new bootstrap.Modal(document.getElementById("courseModal"));
  const form = document.getElementById("course-form");
  const createBtn = document.getElementById("course-create-btn");
  const deptFeeSection = document.getElementById("dept-fee-section");
  const deptFeesList = document.getElementById("dept-fees-list");
  const addFeeBtn = document.getElementById("add-fee-btn");

  function openCreate(){
    document.getElementById("course-id").value = "";
    document.getElementById("course-title").value = "";
    document.getElementById("course-code").value = "";
    document.getElementById("course-dept").value = "";
    document.getElementById("course-credits").value = "";
    document.getElementById("course-desc").value = "";
    deptFeeSection.style.display = "none";
    modal.show();
  }

  function populateDeptFees(deptId){
    if(!deptId){
      deptFeeSection.style.display = "none";
      return;
    }
    deptFeeSection.style.display = "block";
    deptFeesList.innerHTML = "Loading…";
    fetch(`/admin/api/fee_structures?department_id=${encodeURIComponent(deptId)}`, {credentials:"same-origin"})
      .then(r=>r.json()).then(data=>{
        if(data.status !== "ok"){ deptFeesList.innerHTML = "Failed to load fees"; return; }
        if(!data.fee_structures.length) deptFeesList.innerHTML = "<div class='small text-muted'>No fees defined for this department</div>";
        else{
          deptFeesList.innerHTML = data.fee_structures.map(f => `<div class="d-flex justify-content-between align-items-center mb-1">
            <div><strong>${escapeHtml(f.name)}</strong> — ${escapeHtml(f.amount)} <div class="small text-muted">${escapeHtml(f.description || '')}</div></div>
            <div><button class="btn btn-sm btn-outline-danger btn-delete-fee" data-id="${f.id}">Delete</button></div>
          </div>`).join("");
          // bind delete buttons
          document.querySelectorAll(".btn-delete-fee").forEach(b => b.addEventListener("click", async (e)=>{
            const fid = e.currentTarget.dataset.id;
            if(!confirm("Delete fee?")) return;
            const res = await fetch(`/admin/api/fee_structures/${fid}/delete`, {method:"POST", credentials:"same-origin"});
            const json = await res.json().catch(()=>({status:"error"}));
            if(json.status === "ok"){ populateDeptFees(deptId); } else alert("Delete failed");
          }));
        }
      }).catch(()=>{ deptFeesList.innerHTML = "Failed to load fees"; });
  }

  createBtn.addEventListener("click", openCreate);
  document.querySelectorAll(".edit-course").forEach(b => b.addEventListener("click", e => {
    const id = e.currentTarget.dataset.id;
    const row = document.querySelector(`tr[data-cid="${id}"]`);
    if(!row) return;
    document.getElementById("course-id").value = id;
    document.getElementById("course-title").value = row.cells[1].textContent.trim();
    document.getElementById("course-code").value = row.cells[2].textContent.trim();
    // set department select if data-dept-id exists
    const deptId = row.dataset.deptId || "";
    if(deptId) document.getElementById("course-dept").value = deptId;
    document.getElementById("course-credits").value = row.cells[4].textContent.trim() || "";
    document.getElementById("course-desc").value = "";
    populateDeptFees(deptId);
    modal.show();
  }));

  // when department select changes, fetch fee structures
  document.getElementById("course-dept").addEventListener("change", function(){
    populateDeptFees(this.value);
  });

  addFeeBtn.addEventListener("click", async function(){
    const deptId = document.getElementById("course-dept").value;
    if(!deptId){ alert("Select department first"); return; }
    const name = document.getElementById("new-fee-name").value.trim();
    const amount = document.getElementById("new-fee-amount").value;
    if(!name || !amount){ alert("Provide fee name and amount"); return; }
    const payload = { name: name, amount: amount, department_id: deptId };
    const res = await fetch("/admin/api/fee_structures", {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type":"application/json","X-Requested-With":"XMLHttpRequest"},
      body: JSON.stringify(payload)
    });
    const data = await res.json().catch(()=>({status:"error"}));
    if(data.status === "ok"){ document.getElementById("new-fee-name").value = ""; document.getElementById("new-fee-amount").value = ""; populateDeptFees(deptId); }
    else alert("Add fee failed: " + (data.message || ""));
  });

  document.querySelectorAll(".delete-course").forEach(b => b.addEventListener("click", async e => {
    const id = e.currentTarget.dataset.id;
    if(!confirm("Delete course?")) return;
    const res = await fetch(`/admin/api/courses/${id}/delete`, {method:"POST", credentials:"same-origin"});
    const data = await res.json().catch(()=>({status:"error"}));
    if(data.status === "ok"){ location.reload(); } else alert("Delete failed");
  }));

  form.addEventListener("submit", async function(ev){
    ev.preventDefault();
    const id = document.getElementById("course-id").value;
    const payload = {
      title: document.getElementById("course-title").value.trim(),
      code: document.getElementById("course-code").value.trim(),
      department_id: document.getElementById("course-dept").value || null,
      credits: document.getElementById("course-credits").value || null,
      description: document.getElementById("course-desc").value || ""
    };
    const url = id ? `/admin/api/courses/${id}/update` : `/admin/api/courses/create`;
    const res = await fetch(url, {method:"POST", credentials:"same-origin", headers: {"Content-Type":"application/json","X-Requested-With":"XMLHttpRequest"}, body: JSON.stringify(payload)});
    const data = await res.json().catch(()=>({status:"error"}));
    if(data.status === "ok"){ modal.hide(); location.reload(); } else alert("Save failed: " + (data.message || ""));
  });

  function escapeHtml(s){ if(!s) return ""; return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
});
