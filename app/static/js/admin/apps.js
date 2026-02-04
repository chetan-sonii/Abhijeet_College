// app/static/js/admin/apps.js

document.addEventListener("DOMContentLoaded", function() {
    const modalEl = document.getElementById('adminItemModal');
    const modal = new bootstrap.Modal(modalEl);
    const modalBody = document.getElementById('adminItemModalBody');
    const markBtn = document.getElementById('modal-mark-btn');
    const deleteBtn = document.getElementById('modal-delete-btn');

    let currentItemId = null;

    // View Item
    document.querySelectorAll('.view-item').forEach(btn => {
        btn.addEventListener('click', function() {
            currentItemId = this.dataset.id;
            modalBody.innerHTML = '<div class="text-center py-3">Loading...</div>';
            modal.show();

            fetch(`/admin/api/apps/${currentItemId}`)
                .then(r => r.json())
                .then(res => {
                    if(res.status === 'ok') {
                        const d = res.data;
                        let content = `
                            <div class="mb-3">
                                <strong>From:</strong> ${d.name}<br>
                                <strong>Phone:</strong> ${d.phone}<br>
                                <strong>Email:</strong> ${d.email}<br>
                                <strong>Date:</strong> ${d.created_at.replace('T', ' ')}
                            </div>
                            <hr>
                            <div class="p-3 bg-light rounded border mb-3">
                            <strong>Message:</strong><br>
                                ${d.message || d.summary || '(No content)'}
                            </div>
                        `;

                        if(res.type === 'application') {
                            content = `
                                <div class="alert alert-info">Program of Interest: <strong>${d.program}</strong></div>
                                ${content}
                                <div class="mt-2"><strong>Phone:</strong> ${d.phone || 'N/A'}</div>
                            `;
                            markBtn.textContent = (d.status === 'new') ? "Mark Accepted" : "Mark New";
                        } else {
                            content = `
                                <h5>${d.subject || 'No Subject'}</h5>
                                ${content}
                            `;
                            markBtn.textContent = (d.is_read) ? "Mark Unread" : "Mark Read";
                        }
                        modalBody.innerHTML = content;
                    }
                });
        });
    });

    // Mark as Read/Accepted
    markBtn.addEventListener('click', function() {
        if(!currentItemId) return;
        fetch(`/admin/api/apps/${currentItemId}/mark`, { method: 'POST' })
            .then(r => r.json())
            .then(res => {
                if(res.status === 'ok') {
                    alert("Status updated");
                    location.reload();
                }
            });
    });

    // Delete
    deleteBtn.addEventListener('click', function() {
        if(!currentItemId || !confirm("Are you sure you want to delete this?")) return;
        fetch(`/admin/api/apps/${currentItemId}/delete`, { method: 'POST' })
            .then(r => r.json())
            .then(res => {
                if(res.status === 'ok') {
                    alert("Item deleted");
                    location.reload();
                }
            });
    });

    // Search / Refresh logic (simple reload for now)
    document.getElementById('apps-refresh').addEventListener('click', () => location.reload());
    document.getElementById('apps-search').addEventListener('change', function() {
        const q = this.value;
        fetch(`/admin/api/apps?q=${encodeURIComponent(q)}`)
            .then(r => r.json())
            .then(res => {
                const tbody = document.getElementById('apps-list-body');
                tbody.innerHTML = '';
                res.items.forEach(it => {
                    // Rebuild rows (simplified for brevity)
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${it.type}</td><td>${it.name}</td><td>${it.summary}</td><td>${it.status}</td><td>${it.created_at}</td><td class="text-end"><button class="btn btn-sm btn-primary view-item" data-id="${it.id}">View</button></td>`;
                    tbody.appendChild(tr);
                });
                // Re-bind click events for new buttons...
            });
    });
});