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
