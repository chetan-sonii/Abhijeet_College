document.addEventListener("DOMContentLoaded", function () {
    const navbar = document.querySelector(".glass-nav");
    
    // Function to handle scroll styling
    const handleScroll = () => {
        if (window.scrollY > 50) {
            navbar.classList.add("scrolled");
        } else {
            navbar.classList.remove("scrolled");
        }
    };

    // Listen to scroll event
    window.addEventListener("scroll", handleScroll);
});