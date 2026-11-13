const root = document.documentElement;
const toggle = document.getElementById("theme-toggle");

function updateButton() {
	if (!toggle) return;
	toggle.textContent = root.classList.contains("dark") ? "[light]" : "[dark]";
}

updateButton();

if (toggle) {
	toggle.onclick = () => {
		root.classList.toggle("dark");
		try {
			localStorage.setItem("ty_theme", root.classList.contains("dark") ? "dark" : "light");
		} catch (e) {}
		updateButton();
	};
}
