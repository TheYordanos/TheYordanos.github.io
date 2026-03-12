const nav_toggle = document.querySelector(".nav-toggle");
const links = document.querySelector(".nav-links");

nav_toggle.addEventListener("click", () => {
  links.classList.toggle("active");
});

links.querySelectorAll("a").forEach(link => {
  link.addEventListener("click", () => {
    links.classList.remove("active");
  });
});