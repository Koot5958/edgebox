const toggleBtn = document.getElementById("theme-toggle");
const icon = toggleBtn.querySelector(".theme-icon");
const text = toggleBtn.querySelector(".theme-text");

toggleBtn.addEventListener("click", () => {
    const html = document.documentElement;
    const current = html.getAttribute("data-theme");
    const newTheme = current === "light" ? "dark" : "light";

    html.setAttribute("data-theme", newTheme);

    icon.textContent = newTheme === "light" ? "🌙" : "☀️";
    text.textContent = newTheme === "light" ? "Dark Mode" : "Light Mode";
});
