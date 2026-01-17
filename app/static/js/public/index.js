// static/js/public/index.js
document.addEventListener("DOMContentLoaded", function () {
  const noticesContainer = document.getElementById("notices");
//  const refreshBtn = document.getElementById("refresh-notices");
// Add this inside document.addEventListener("DOMContentLoaded", function () { ...
const heroImg = document.querySelector('.hero-img-main');
if (heroImg) {
    document.addEventListener('mousemove', (e) => {
        const xAxis = (window.innerWidth / 2 - e.pageX) / 50;
        const yAxis = (window.innerHeight / 2 - e.pageY) / 50;
        heroImg.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
    });
}
  function formatDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
  }

  function placeholderThumb(seed) {
    // use picsum.photos for lively placeholders (no hard-coded local images)
    // seed to keep images consistent across loads
    const id = seed ? (Math.abs(hashCode(String(seed))) % 1000) : Math.floor(Math.random() * 1000);
    return `https://picsum.photos/seed/${id}/400/300`;
  }

  function hashCode(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) {
      h = (h << 5) - h + str.charCodeAt(i);
      h |= 0;
    }
    return h;
  }

  function escapeHtml(s) {
    if (!s) return "";
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

    loadNotices();

//    document.getElementById('refresh-notices').addEventListener('click', function() {
//        // Spin icon effect
//        const icon = this.querySelector('.refresh-icon');
//        icon.style.transition = 'transform 0.5s';
//        icon.style.transform = 'rotate(360deg)';
//        setTimeout(() => icon.style.transform = 'none', 500);
//
//        loadNotices();
//    });

function loadNotices() {
    const container = document.getElementById('notices-container');
    container.innerHTML = '<div class="col-12 text-center"><div class="spinner-border text-primary" role="status"></div></div>';

    fetch('/api/notices?limit=6')
        .then(response => response.json())
        .then(data => {
            container.innerHTML = ''; // Clear spinner

            if (data.notices.length === 0) {
                container.innerHTML = '<div class="col-12 text-center"><p>No notices found.</p></div>';
                return;
            }

            data.notices.forEach(notice => {
                // Determine badge class based on category
                const badgeClass = `badge-${notice.category}`;

                // If pinned, add a small icon
                const pinIcon = notice.is_pinned ? '📌 ' : '';

                const html = `
                <div class="col-md-6 col-lg-4">
                    <article class="notice-card-modern h-100 p-4 d-flex flex-column">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <span class="badge ${badgeClass} rounded-pill">${notice.category}</span>
                            <small class="text-muted">${notice.posted_on}</small>
                        </div>

                        <h5 class="notice-title fw-bold mb-2">${pinIcon}${notice.title}</h5>
                        <p class="text-secondary mb-4 flex-grow-1" style="overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;">
                            ${notice.body}
                        </p>

                        <button class="btn btn-outline-primary btn-sm rounded-pill w-100 mt-auto read-more-btn"
                            data-title="${notice.title}"
                            data-body="${notice.body}"
                            data-date="${notice.posted_on}"
                            data-category="${notice.category}">
                            Read Full Detail →
                        </button>
                    </article>
                </div>
                `;
                container.insertAdjacentHTML('beforeend', html);
            });

            // Attach event listeners to new buttons
           // ... inside loadNotices() ...

// Attach event listeners to new buttons
document.querySelectorAll('.read-more-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const cat = this.dataset.category; // e.g., "Exam", "Academic"

        // 1. Populate Text
        document.getElementById('modal-title').textContent = this.dataset.title;
        document.getElementById('modal-body').textContent = this.dataset.body;
        document.getElementById('modal-date').textContent = this.dataset.date;

        // 2. Setup Category Badge (White badge with colored text)
        const catBadge = document.getElementById('modal-category');
        catBadge.textContent = cat;
        catBadge.className = `badge bg-white mb-2 align-self-start text-${mapCategoryToColor(cat)}`;

        // 3. Dynamic Header Color
        const header = document.getElementById('modal-header-bg');
        // Remove old specific classes
        header.className = 'modal-header text-white';
        // Add new specific class
        header.classList.add(`modal-header-${cat}`);

        // Show Modal
        const myModal = new bootstrap.Modal(document.getElementById('noticeDetailModal'));
        myModal.show();
    });
});

// Helper to map category names to Bootstrap text colors for the badge text
function mapCategoryToColor(cat) {
    switch(cat) {
        case 'Academic': return 'primary';
        case 'Exam': return 'danger';
        case 'Event': return 'info';
        case 'Placement': return 'success';
        default: return 'secondary';
    }
}

        })
        .catch(err => {
            console.error(err);
            container.innerHTML = '<div class="col-12 text-center text-danger">Failed to load notices.</div>';
        });
}

//  if (refreshBtn) {
//    refreshBtn.addEventListener("click", function (e) {
//      e.preventDefault();
//      refreshBtn.disabled = true;
//      refreshBtn.innerText = "Refreshing…";
//      loadNotices().finally(() => {
//        refreshBtn.disabled = false;
//        refreshBtn.innerText = "Refresh";
//      });
//    });
//  }





  const grid = document.getElementById("programs-grid");
  if (!grid) return;

  fetch("/api/programs")
    .then(res => res.json())
    .then(data => {
      if (!data.programs || data.programs.length === 0) return;

      grid.innerHTML = data.programs.map(p => `
        <div class="col-md-6 col-lg-4">
          <div class="program-card card h-100 animate__animated animate__fadeInUp">
            <img src="${p.image}" class="card-img-top" alt="">
            <div class="card-body">
              <span class="program-dept">${p.department}</span>
              <h5 class="card-title">${escapeHtml(p.title)}</h5>
              <p class="program-code">${escapeHtml(p.code)}</p>
            </div>
          </div>
        </div>
      `).join("");
    })
    .catch(err => console.error("Programs load failed", err));

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g,"&amp;")
      .replace(/</g,"&lt;")
      .replace(/>/g,"&gt;");
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const grid = document.getElementById("programs-grid");
  const buttons = document.querySelectorAll(".filter-btn");

  if (!grid || buttons.length === 0) return;

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const dept = btn.dataset.dept || "";

      fetch(`/api/programs/filter?department=${dept}`)
        .then(res => res.json())
        .then(data => updateGrid(data.courses))
        .catch(err => console.error(err));
    });
  });

  function updateGrid(courses) {
    grid.style.opacity = "0";

    setTimeout(() => {
      grid.innerHTML = courses.map(c => `
        <div class="col-md-6 col-lg-4 program-item">
          <div class="program-card card h-100">
            <img src="${c.image}" class="card-img-top" alt="">
            <div class="card-body">
              <span class="program-dept">${c.department}</span>
              <h5 class="card-title">${escape(c.title)}</h5>
              <p class="program-code">${escape(c.code)}</p>
            </div>
          </div>
        </div>
      `).join("");

      grid.style.opacity = "1";
    }, 200);
  }

  function escape(str) {
    return String(str)
      .replace(/&/g,"&amp;")
      .replace(/</g,"&lt;")
      .replace(/>/g,"&gt;");
  }
});
