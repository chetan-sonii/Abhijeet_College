// app/static/js/admin/courses.js

const courseModalEl = document.getElementById('courseModal');
const courseModal = new bootstrap.Modal(courseModalEl);
const form = document.getElementById('courseForm');

function openCreateModal() {
    form.reset();
    document.getElementById('c_id').value = ''; // Clear ID implies CREATE mode
    document.getElementById('courseModalLabel').textContent = "Add New Course";
    courseModal.show();
}

function editCourse(id) {
    fetch(`/admin/api/courses/${id}`)
        .then(res => res.json())
        .then(res => {
            if(res.status === 'success') {
                const d = res.data;
                document.getElementById('c_id').value = d.id;
                document.getElementById('c_code').value = d.code;
                document.getElementById('c_title').value = d.title;
                document.getElementById('c_credits').value = d.credits;
                document.getElementById('c_fee').value = d.fee;
                document.getElementById('c_dept').value = d.department_id || '';
                document.getElementById('c_desc').value = d.description || '';

                document.getElementById('courseModalLabel').textContent = "Edit Course";
                courseModal.show();
            }
        });
}

function saveCourse(e) {
    e.preventDefault();
    const id = document.getElementById('c_id').value;
    const formData = new FormData(form);

    // Determine URL and Method based on ID presence
    const url = id ? `/admin/api/courses/${id}` : '/admin/api/courses';

    fetch(url, {
        method: 'POST', // Using POST for both (Flask simplifies this, or use PUT if preferred)
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            const c = data.course;
            const tbody = document.getElementById('courses-body');

            // HTML for the row cells
            const rowHTML = `
                <td class="ps-4 fw-bold text-primary">${c.code}</td>
                <td><div class="fw-bold">${c.title}</div></td>
                <td><span class="badge bg-light text-dark border">${c.dept_name}</span></td>
                <td>${c.credits}</td>
                <td>${c.fee}</td>
                <td class="text-end pe-4">
                    <button class="btn btn-sm btn-outline-secondary me-1" onclick="editCourse('${c.id}')"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteCourse('${c.id}')"><i class="bi bi-trash"></i></button>
                </td>
            `;

            if (id) {
                // UPDATE: Find existing row and replace content
                const row = document.getElementById(`course-row-${id}`);
                row.innerHTML = rowHTML;
            } else {
                // CREATE: Append new row
                const newRow = document.createElement('tr');
                newRow.id = `course-row-${c.id}`;
                newRow.innerHTML = rowHTML;
                tbody.appendChild(newRow);
            }

            courseModal.hide();
        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(err => console.error(err));
}

function deleteCourse(id) {
    if(!confirm("Delete this course? Sections and results might be affected.")) return;

    fetch(`/admin/api/courses/${id}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                document.getElementById(`course-row-${id}`).remove();
            } else {
                alert(data.message);
            }
        });
}