// index.js - page-specific JS
document.addEventListener("DOMContentLoaded", function() {
    // Example: load latest notices via AJAX endpoint (if you provide /api/notices)
    // $.getJSON("/api/notices", function(data){ ... });

    // simple animation trigger using animate.css classes
    var el = document.querySelector(".jumbotron");
    if (el) {
        el.classList.add("animated", "fadeInDown");
    }
});