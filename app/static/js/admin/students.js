// app/static/js/admin/students.js

document.addEventListener("DOMContentLoaded", function() {
    loadStudents();

    document.getElementById('btn-filter').addEventListener('click', loadStudents);

    // Enter key on search box triggers filter
    document.getElementById('filter-search').addEventListener('keyup', function(e) {
        if (e.key === 'Enter') loadStudents();
    });
});

function loadStudents() {
    const q = document.getElementById('filter-search').value;
    const course = document.getElementById('filter-course').value;
    const fee = document.getElementById('filter-fee').value;

    const tbody = document.getElementById('students-body');
    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-5 text-muted"><div class="spinner-border spinner-border-sm"></div> Loading...</td></tr>';

    fetch(`/admin/api/students?q=${q}&course_id=${course}&fee_status=${fee}`)
        .then(r => r.json())
        .then(res => {
            if(res.status === 'success') {
                tbody.innerHTML = '';
                if(res.students.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-5 text-muted">No students found matching filters.</td></tr>';
                    return;
                }

                res.students.forEach(s => {
                    const statusBadge = s.is_active
                        ? '<span class="badge bg-success bg-opacity-10 text-success">Active</span>'
                        : '<span class="badge bg-danger bg-opacity-10 text-danger">Blocked</span>';

                    const feeBadge = s.is_paid
                        ? '<span class="badge bg-success">Paid</span>'
                        : `<span class="badge bg-warning text-dark">${s.fee_status}</span>`;

                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="ps-4 fw-bold text-secondary">${s.admission_no}</td>
                        <td>
                            <div class="fw-bold text-dark">${s.name}</div>
                            <div class="small text-muted">${s.email}</div>
                        </td>
                        <td>${s.courses_count} Course(s)</td>
                        <td>${feeBadge}</td>
                        <td>${statusBadge}</td>
                        <td class="text-end pe-4">
                            <button class="btn btn-sm btn-outline-primary" onclick="viewStudent(${s.id})">View Details</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        });
}

let currentStudentId = null;
const studentModal = new bootstrap.Modal(document.getElementById('studentModal'));

// app/static/js/admin/students.js

// ... (Keep existing loadStudents code) ...

function viewStudent(id) {
    currentStudentId = id;

    fetch(`/admin/api/students/${id}`)
        .then(r => r.json())
        .then(res => {
            if(res.status === 'success') {
                const p = res.profile;
                const f = res.finance;

                // 1. Update Header with Avatar
                // We assume there is an <img> tag with id='modal-avatar' in the HTML (see next step)
                const avatarImg = document.getElementById('modal-avatar');
                if(avatarImg) avatarImg.src = p.avatar;

                document.getElementById('modal-name').textContent = p.name;
                document.getElementById('modal-adm').textContent = p.admission_no;
                document.getElementById('modal-email').textContent = p.email;

                // Status Badge logic (Active/Blocked)
                const badge = document.getElementById('modal-status-badge');
                const blockBtn = document.getElementById('btn-block-user');
                // ... (Keep existing status logic) ...
                if(p.is_active) {
                    badge.className = 'badge bg-success'; badge.textContent = 'Active';
                    blockBtn.textContent = 'Block User'; blockBtn.classList.replace('btn-outline-success', 'btn-outline-danger');
                    blockBtn.onclick = () => performAction('block');
                } else {
                    badge.className = 'badge bg-danger'; badge.textContent = 'Blocked';
                    blockBtn.textContent = 'Unblock User'; blockBtn.classList.replace('btn-outline-danger', 'btn-outline-success');
                    blockBtn.onclick = () => performAction('unblock');
                }

                // 2. Academics Table
                const enrTbody = document.getElementById('modal-enrollments');
                enrTbody.innerHTML = '';
                res.academics.forEach(e => {
                    enrTbody.innerHTML += `
                        <tr>
                            <td>
                                <div class="fw-bold">${e.course_code}</div>
                                <div class="small text-muted">${e.course_title}</div>
                            </td>
                            <td>$${e.fee.toFixed(2)}</td>
                            <td>${e.enrolled_on}</td>
                            <td class="text-end">
                                <button class="btn btn-xs btn-outline-danger" onclick="unenrollStudent(${e.id})">Drop</button>
                            </td>
                        </tr>
                    `;
                });

                // 3. Finance Tab (Updated Logic)
                document.getElementById('modal-fee-total').textContent = '$' + f.total_fee.toFixed(2);
                document.getElementById('modal-fee-paid').textContent = '$' + f.total_paid.toFixed(2);

                const balEl = document.getElementById('modal-fee-balance');
                if (f.credit > 0) {
                    // Show Credit (Green)
                    balEl.innerHTML = `<span class="text-success">+$${f.credit.toFixed(2)} (Credit)</span>`;
                } else if (f.balance_due > 0) {
                    // Show Due (Red)
                    balEl.innerHTML = `<span class="text-danger">-$${f.balance_due.toFixed(2)} (Due)</span>`;
                } else {
                    // Settled
                    balEl.innerHTML = `<span class="text-muted">$0.00</span>`;
                }

                const payList = document.getElementById('modal-payments');
                payList.innerHTML = '';
                f.history.forEach(pay => {
                    payList.innerHTML += `
                        <li class="list-group-item d-flex justify-content-between px-0">
                            <span>Paid on ${pay.date}</span>
                            <span class="fw-bold text-success">+$${pay.amount.toFixed(2)}</span>
                        </li>
                    `;
                });
                if(f.history.length === 0) payList.innerHTML = '<li class="list-group-item px-0 text-muted">No payments recorded.</li>';

                // Info Tab
                document.getElementById('modal-phone').textContent = p.phone || '-';
                document.getElementById('modal-dob').textContent = p.dob;
                document.getElementById('modal-addr').textContent = p.address || '-';

                studentModal.show();
            }
        });
}

// ... (Keep existing actions) ...

function performAction(action, extraData = {}) {
    if(!confirm(`Are you sure you want to ${action} this student?`)) return;

    const formData = new FormData();
    formData.append('action', action);
    for (const key in extraData) {
        formData.append(key, extraData[key]);
    }

    fetch(`/admin/api/students/${currentStudentId}/action`, {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(res => {
        if(res.status === 'success') {
            alert(res.message);
            studentModal.hide();
            loadStudents(); // Reload list
        } else {
            alert(res.message);
        }
    });
}

function unenrollStudent(enrollmentId) {
    performAction('unenroll', { enrollment_id: enrollmentId });
}