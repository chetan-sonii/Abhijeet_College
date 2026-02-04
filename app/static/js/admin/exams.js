// app/static/js/admin/exams.js

const createModal = new bootstrap.Modal(document.getElementById('createExamModal'));
const marksModal = new bootstrap.Modal(document.getElementById('marksModal'));
let currentExamId = null;

document.addEventListener("DOMContentLoaded", () => {
    loadExams();
    // Search listener
    document.getElementById('filter-search').addEventListener('keyup', (e) => {
        if(e.key === 'Enter') loadExams();
    });
});

function loadExams() {
    const q = document.getElementById('filter-search').value;
    const dept = document.getElementById('filter-dept').value;

    fetch(`/admin/api/exams?q=${q}&department_id=${dept}`)
        .then(r => r.json())
        .then(res => {
            const tbody = document.getElementById('exams-body');
            tbody.innerHTML = '';

            if(res.exams.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">No exams found.</td></tr>';
                return;
            }

            res.exams.forEach(e => {
                tbody.innerHTML += `
                    <tr>
                        <td class="ps-4 fw-bold">${e.title}</td>
                        <td>
                            <div>${e.course_title}</div>
                            <small class="text-muted">${e.course_code}</small>
                        </td>
                        <td>${e.date}</td>
                        <td>${e.total_marks}</td>
                        <td class="text-end pe-4">
                            <button class="btn btn-sm btn-outline-primary me-1" onclick="openMarksModal(${e.id})">
                                <i class="bi bi-pencil-square"></i> Marks
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteExam(${e.id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            });
        });
}

function openCreateModal() {
    document.getElementById('createExamForm').reset();
    createModal.show();
}

function createExam(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    fetch('/admin/api/exams/create', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(res => {
        if(res.status === 'success') {
            createModal.hide();
            loadExams();
        } else {
            alert("Error: " + res.message);
        }
    });
}

function openMarksModal(examId) {
    currentExamId = examId;
    const tbody = document.getElementById('marks-body');
    tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3">Loading students...</td></tr>';

    marksModal.show();

    fetch(`/admin/api/exams/${examId}/results`)
        .then(r => r.json())
        .then(res => {
            if(res.status === 'success') {
                document.getElementById('marksModalLabel').textContent = `Enter Marks: ${res.exam.title}`;
                document.getElementById('marksModalSubtitle').textContent = `Max Marks: ${res.exam.total_marks}`;

                tbody.innerHTML = '';
                if(res.students.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-muted">No students enrolled in this course.</td></tr>';
                    return;
                }

                res.students.forEach(s => {
                    tbody.innerHTML += `
                        <tr data-id="${s.enrollment_id}">
                            <td class="ps-4 fw-bold text-secondary">${s.admission_no}</td>
                            <td>${s.student_name}</td>
                            <td>
                                <input type="number" class="form-control form-control-sm marks-input"
                                       value="${s.marks_obtained}" min="0" max="${res.exam.total_marks}" step="0.5">
                            </td>
                            <td>
                                <input type="text" class="form-control form-control-sm remarks-input"
                                       value="${s.remarks}" placeholder="Optional">
                            </td>
                        </tr>
                    `;
                });
            }
        });
}

function saveMarks() {
    const rows = [];
    document.querySelectorAll('#marks-body tr').forEach(tr => {
        if (tr.dataset.id) {
            rows.push({
                enrollment_id: tr.dataset.id,
                marks: tr.querySelector('.marks-input').value,
                remarks: tr.querySelector('.remarks-input').value
            });
        }
    });

    fetch(`/admin/api/exams/${currentExamId}/results`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ rows: rows })
    })
    .then(r => r.json())
    .then(res => {
        if(res.status === 'success') {
            alert("Results saved successfully!");
            marksModal.hide();
        } else {
            alert("Error saving results.");
        }
    });
}

function deleteExam(id) {
    if(confirm("Delete this exam and all associated results?")) {
        fetch(`/admin/api/exams/${id}/delete`, { method: 'POST' })
            .then(r => r.json())
            .then(() => loadExams());
    }
}