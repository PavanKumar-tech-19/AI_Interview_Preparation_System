// ===============================
// AI Interview Professional UI
// ===============================

// Dark / Light Mode

const themeBtn = document.getElementById("theme-toggle");

if (themeBtn) {

    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
        themeBtn.innerHTML = '<i class="bi bi-sun-fill"></i>';
    }

    themeBtn.addEventListener("click", () => {

        document.body.classList.toggle("dark-mode");

        if (document.body.classList.contains("dark-mode")) {

            localStorage.setItem("theme", "dark");
            themeBtn.innerHTML = '<i class="bi bi-sun-fill"></i>';

        } else {

            localStorage.setItem("theme", "light");
            themeBtn.innerHTML = '<i class="bi bi-moon-stars-fill"></i>';

        }

    });

}

// Loading Spinner

window.addEventListener("load", () => {

    const loader = document.getElementById("loader");

    if (loader) {

        loader.classList.add("d-none");

    }

});

// Fade Animation

document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".card,.dashboard-card,.report-card").forEach((item) => {

        item.classList.add("fade-up");

    });

});