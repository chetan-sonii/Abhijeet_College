// static/js/admin/exams.js
document.addEventListener("DOMContentLoaded", function(){
  // Elements
  const createModalEl = document.getElementById("examCreateModal");
  const createModal = new bootstrap.Modal(createModalEl);
  const resultsModalEl = document.getElementById("examResultsModal");
  const resultsModal = new bootstrap.Modal(resultsModalEl);
  const createBtn = document.getElementById("exam-create-btn");
  const createForm = document.getElementById("exam-create-form");
  const resultsBody = document.getElementById("exam-results-body");
  const saveResultsBtn = document.getElementById("save-results-btn");
  const filterBtn = document.getElementById("filter-exams-btn");
  const examsTableBody = document.querySelector("#exams-table tbody");

  // Keep track if the create modal is editing
  createModalEl.dataset.editId = "";

  // Utility
  function qs(sel, parent=document) { return parent.querySelector(sel); }
  function qsa(sel, parent=document) { return Array.from(parent.querySelectorAll(sel)); }
  function escapeHtml(s){ if(!s && s !== 0) return ""; return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

  // Load exams with optional filters
  async function loadExams(filters = {}) {
    const params = new URLSearchParams();
    if(filters.department_id) params.set("department_id", filters.department_id);
    if(filters.q) params.set("q", filters.q);
    if(filters.date_from) params.set("date_from", filters.date_from);
    if(filters.date_to) params.set("date_to", filters.date_to);
    const url = "/admin/api/exams" + (params.toString() ? "?" + params.toString() : "");
    try {
      const res = await fetch(url, {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json"}});
      const data = await res.json();
      if(data.status !== "ok"){ alert("Failed to load exams"); return; }      
      renderExamRows(data.exams || []);
    } catch (err) {
      console.error("loadExams error", err);
      alert("Failed to load exams");
    }
  }

  // Render rows & attach no direct handlers (we use delegation)
 // renderExamRows (use in your existing admin/exams.js)
function renderExamRows(exams) {
  const tbody = document.querySelector("#exams-table tbody");
  if (!tbody) return;
  tbody.innerHTML = exams.length
    ? exams
        .map(e => `
      <tr data-eid="${e.id}" data-section-id="${e.section_id || ''}">
        <td>${escapeHtml(e.id)}</td>
        <td>${escapeHtml(e.title || '')}</td>
        <td>
          ${escapeHtml(e.course || 'Error')}
          <div class="small text-muted">${escapeHtml(e.section_code || '')}</div>
        </td>
        <td>${e.exam_date ? new Date(e.exam_date).toLocaleDateString() : ''}</td>
        <td>${e.total_marks || '—'}</td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary btn-results" data-id="${e.id}">Results</button>
          <button class="btn btn-sm btn-outline-secondary btn-edit" data-id="${e.id}">Edit</button>
          <button class="btn btn-sm btn-outline-danger btn-delete" data-id="${e.id}">Delete</button>
        </td>
      </tr>
    `)
        .join('')
    : `<tr><td colspan="6" class="text-center small text-muted">No exams found</td></tr>`;
}


  // Event delegation for actions in the table
  if(examsTableBody){
    examsTableBody.addEventListener("click", async function(ev){
      const btn = ev.target.closest("button");
      if(!btn) return;
      const id = btn.dataset.id;
      if(btn.classList.contains("btn-results")){
        await openResults(id);
        return;
      }
      if(btn.classList.contains("btn-edit")){
        await openEditModal(id);
        return;
      }
      if(btn.classList.contains("btn-delete")){
        await deleteExam(id);
        return;
      }
    });
  }

  // Open results modal (unchanged logic)
  async function openResults(id){
    resultsBody.innerHTML = '<div class="text-center small text-muted">Loading…</div>';
    resultsModal.show();
    try {
      const res = await fetch(`/admin/api/exams/${id}/results`, {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json"}});
      const data = await res.json();
      if(data.status !== "ok"){ resultsBody.innerHTML = '<div class="text-danger">Failed to load results</div>'; return; }
      const rows = data.rows || [];
      const exam = data.exam || {};
      let html = `<div class="mb-3"><strong>Exam:</strong> ${escapeHtml(exam.title || '')} &nbsp; <small class="text-muted">Total marks: ${exam.total_marks || '—'}</small></div>`;
      html += `<div class="table-responsive"><table class="table table-sm"><thead><tr><th>#</th><th>Student</th><th>Marks</th><th>Grade</th></tr></thead><tbody>`;
      rows.forEach((r,i) => {
        html += `<tr data-enrollment-id="${r.enrollment_id}" data-result-id="${r.result_id || ''}">
          <td>${i+1}</td>
          <td>${escapeHtml(r.student_name || '')}</td>
          <td><input class="form-control form-control-sm marks-input" type="number" step="0.01" value="${r.marks_obtained!==null && r.marks_obtained!==undefined ? r.marks_obtained : ''}"></td>
          <td><input class="form-control form-control-sm grade-input" value="${r.grade || ''}"></td>
        </tr>`;
      });
      html += `</tbody></table></div>`;
      resultsBody.innerHTML = html;
      saveResultsBtn.dataset.eid = id;
    } catch (err) {
      resultsBody.innerHTML = '<div class="text-danger">Failed to load results</div>';
      console.error(err);
    }
  }

  // Delete exam
  async function deleteExam(id){
    if(!confirm("Delete exam? This cannot be undone.")) return;
    try {
      const res = await fetch(`/admin/api/exams/${id}/delete`, {method:"POST", credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest"}});
      const data = await res.json();
      if(data.status === "ok"){ await loadCurrentFilters(); } else alert("Delete failed");
    } catch(err){
      console.error("deleteExam failed", err);
      alert("Delete failed");
    }
  }

  // Open create modal (for new exam)
  createBtn.addEventListener("click", function(){
    // clear form
    createModalEl.querySelector(".modal-title").textContent = "Create Exam";
    qs("#exam-title", createForm).value = "";
    qs("#exam-section", createForm).value = "";
    qs("#exam-date", createForm).value = "";
    qs("#exam-total", createForm).value = "";
    createModalEl.dataset.editId = "";
    createModal.show();
  });

  // Open edit modal (populate fields)
  async function openEditModal(id){
    createModalEl.querySelector(".modal-title").textContent = "Edit Exam";
    // fetch exam detail (we can reuse /admin/api/exams to get exam list or call single exam)
    try {
      const res = await fetch(`/admin/api/exams?limit=200&q=${encodeURIComponent(id)}`, {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json"}});
      const data = await res.json();
      // try to find exam in returned list by id
      let found = null;
      if(data.status === "ok" && Array.isArray(data.exams)){
        found = data.exams.find(x => String(x.id) === String(id));
      }
      // if not found, attempt fetching via the results endpoint metadata (fallback)
      if(!found){
        // fallback: build a minimal set by calling /admin/api/exams (no filters)
        const res2 = await fetch(`/admin/api/exams`, {credentials:"same-origin", headers: {"X-Requested-With":"XMLHttpRequest","Accept":"application/json"}});
        const data2 = await res2.json();
        if(data2.status === "ok" && Array.isArray(data2.exams)){
          found = data2.exams.find(x => String(x.id) === String(id));
        }
      }
      if(!found){
        alert("Failed to fetch exam details for edit");
        return;
      }
      // populate form
      qs("#exam-title", createForm).value = found.title || "";
      // we have section_id in found? if not present, leave blank
      if(found.section_id) qs("#exam-section", createForm).value = found.section_id;
      else qs("#exam-section", createForm).value = "";
      qs("#exam-date", createForm).value = found.exam_date ? found.exam_date.split("T")[0] : "";
      qs("#exam-total", createForm).value = found.total_marks || "";
      createModalEl.dataset.editId = String(found.id);
      createModal.show();
    } catch (err) {
      console.error("openEditModal error", err);
      alert("Failed to open edit modal");
    }
  }

  // Create or update - same form
  createForm.addEventListener("submit", async function(ev){
    ev.preventDefault();
    const eid = createModalEl.dataset.editId;
    const payload = {
      title: qs("#exam-title", createForm).value.trim(),
      section_id: qs("#exam-section", createForm).value || null,
      exam_date: qs("#exam-date", createForm).value || null,
      total_marks: qs("#exam-total", createForm).value || null
    };
    try {
      const url = eid ? `/admin/api/exams/${eid}/update` : "/admin/api/exams/create";
      const res = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {"Content-Type":"application/json","X-Requested-With":"XMLHttpRequest"},
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if(data.status === "ok"){
        createModal.hide();
        // clear edit state
        createModalEl.dataset.editId = "";
        await loadCurrentFilters(); // refresh table via AJAX
      } else {
        alert("Save failed: " + (data.message || "server error"));
      }
    } catch(err){
      console.error("createForm submit error", err);
      alert("Save failed");
    }
  });

  // Filters
  filterBtn.addEventListener("click", loadCurrentFilters);
  function loadCurrentFilters(){
    const dept = qs("#filter-department") ? qs("#filter-department").value : "";
    const q = qs("#filter-q") ? qs("#filter-q").value.trim() : "";
    const df = qs("#filter-date-from") ? qs("#filter-date-from").value : "";
    const dt = qs("#filter-date-to") ? qs("#filter-date-to").value : "";
    return loadExams({ department_id: dept, q: q, date_from: df, date_to: dt });
  }

  // Save results handler (unchanged logic)
  saveResultsBtn.addEventListener("click", async function(){
    const eid = this.dataset.eid;
    if(!eid) return;
    const trs = resultsBody.querySelectorAll("tbody tr");
    const payload = { rows: [] };
    trs.forEach(tr => {
      const enrollment_id = tr.dataset.enrollmentId;
      const result_id = tr.dataset.resultId || null;
      const marks = tr.querySelector(".marks-input").value;
      const grade = tr.querySelector(".grade-input").value.trim();
      payload.rows.push({ enrollment_id: enrollment_id, result_id: result_id, marks_obtained: marks === "" ? null : marks, grade: grade });
    });
    try {
      const res = await fetch(`/admin/api/exams/${eid}/results/save`, {method:"POST", credentials:"same-origin", headers: {"Content-Type":"application/json","X-Requested-With":"XMLHttpRequest"}, body: JSON.stringify(payload)});
      const data = await res.json();
      if(data.status === "ok"){ resultsModal.hide(); await loadCurrentFilters(); } else alert("Save failed");
    } catch(err){
      console.error("saveResults error", err);
      alert("Save failed");
    }
  });

  // Initial load
  loadCurrentFilters();
});



// Function to Load Marks into the Modal
function openMarksModal(examId) {
    const modal = new bootstrap.Modal(document.getElementById('marksModal'));
    const tableBody = document.querySelector('#marksTable tbody');
    const saveBtn = document.getElementById('saveMarksBtn');

    // Clear previous data
    tableBody.innerHTML = '<tr><td colspan="4" class="text-center">Loading...</td></tr>';

    // Store exam ID on the save button for later use
    saveBtn.dataset.examId = examId;

    fetch(`/admin/api/exams/${examId}/results`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('marksModalLabel').textContent = `Enter Marks for ${data.exam_title}`;
            tableBody.innerHTML = ''; // Clear loading message

            if (data.results.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No students enrolled in this section.</td></tr>';
                return;
            }

            // Generate Rows
            data.results.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.admission_no}</td>
                    <td>${row.student_name}</td>
                    <td>
                        <input type="number"
                               class="form-control marks-input"
                               data-enrollment-id="${row.enrollment_id}"
                               value="${row.marks_obtained}"
                               max="${data.total_marks}"
                               min="0" step="0.5">
                    </td>
                    <td>
                        <input type="text"
                               class="form-control remarks-input"
                               value="${row.remarks || ''}"
                               placeholder="Optional">
                    </td>
                `;
                tableBody.appendChild(tr);
            });

            modal.show();
        })
        .catch(err => {
            console.error(err);
            alert("Failed to load students.");
        });
}

// Function to Save Marks
document.getElementById('saveMarksBtn').addEventListener('click', function() {
    const examId = this.dataset.examId;
    const inputs = document.querySelectorAll('.marks-input');
    const payload = [];

    inputs.forEach(input => {
        const row = input.closest('tr');
        const remarks = row.querySelector('.remarks-input').value;

        payload.push({
            enrollment_id: input.dataset.enrollmentId, // Crucial: matches backend expectation
            marks_obtained: input.value,
            remarks: remarks
        });
    });

    // Send Data
    fetch(`/admin/api/exams/${examId}/results`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ results: payload })
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            alert("Marks saved successfully!");
            bootstrap.Modal.getInstance(document.getElementById('marksModal')).hide();
        } else {
            alert("Error saving marks: " + data.message);
        }
    })
    .catch(err => console.error(err));
});