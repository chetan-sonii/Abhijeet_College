// static/js/public/counters.js
(function () {
  function animateValue(el, start, end, duration) {
    let startTime = null;
    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const eased = easeOutCubic(progress);
      const current = Math.floor(start + (end - start) * eased);
      el.textContent = formatNumber(current, end);
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        // ensure final value
        el.textContent = formatNumber(end, end);
      }
    };
    window.requestAnimationFrame(step);
  }

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function formatNumber(n, target) {
    // if target is big, add plus sign
    if (target >= 1000) {
      return n.toLocaleString();
    }
    return String(n);
  }

  function initCounters() {
    const counters = document.querySelectorAll(".counter-number");
    if (!("IntersectionObserver" in window)) {
      // no observer -> animate immediately
      counters.forEach(c => animateValue(c, 0, parseInt(c.dataset.target || 0, 10) || 0, 1200));
      return;
    }

    const io = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseInt(el.dataset.target || 0, 10) || 0;
        animateValue(el, 0, target, 1200);
        observer.unobserve(el);
      });
    }, { threshold: 0.4 });

    counters.forEach(c => io.observe(c));
  }

  document.addEventListener("DOMContentLoaded", initCounters);
})();
