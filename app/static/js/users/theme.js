// static/js/users/theme.js
// Adds .is-loaded to body after rendering for subtle fade-in animations
document.addEventListener("DOMContentLoaded", function(){
  window.requestAnimationFrame(function(){
    setTimeout(function(){ document.body.classList.add("is-loaded"); }, 120);
  });
});
