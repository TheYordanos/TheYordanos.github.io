// TOGGLE ==================================
const toggle = document.getElementById("theme-toggle");

function updateButton() {
	if (!toggle) return;
	toggle.innerHTML = document.body.classList.contains("dark") ? "[light]" : "[dark]";
}

// page load
if (localStorage.getItem("theme") === "dark") document.body.classList.add("dark");
updateButton();

if (toggle) {
	toggle.onclick = () => {
		document.body.classList.toggle("dark");
		localStorage.setItem("theme", document.body.classList.contains("dark") ? "dark" : "light");
		updateButton();
	};
}

// NAV ==================================
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
