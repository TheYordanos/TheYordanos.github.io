// Light & Dark Mode
let themeToggle = document.querySelector(".theme-toggle")
let sunIcon = document.querySelector(".sun")
let moonIcon = document.querySelector(".moon")

let theme = localStorage.getItem("theme")
if (theme == null) {
	localStorage.setItem("theme", "dark")
	sunIcon.style.display = "block"
	moonIcon.style.display = "none"
}
else {
	if (theme == "dark") {
		document.body.classList.add("dark")
		sunIcon.style.display = "block"
		moonIcon.style.display = "none"
	} else {
		document.body.classList.remove("dark")
		sunIcon.style.display = "none"
		moonIcon.style.display = "block"
	}
}

themeToggle.addEventListener("click", () => {
	if (document.body.classList.contains("dark")) {
		localStorage.setItem("theme", "light")
		document.body.classList.remove("dark")
		sunIcon.style.display = "none"
		moonIcon.style.display = "block"
	} else {
		localStorage.setItem("theme", "dark")
		document.body.classList.add("dark")
		sunIcon.style.display = "block"
		moonIcon.style.display = "none"
	}
})