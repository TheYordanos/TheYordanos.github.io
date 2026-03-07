// TOGGLE ==================================
const toggle = document.getElementById("theme-toggle");

function updateButton() {
  if (!toggle) return;
  toggle.textContent = document.body.classList.contains("dark")
    ? "[light]"
    : "[dark]";
}

// apply saved theme on page load
if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark");
}

updateButton();

// toggle behavior
if (toggle) {
  toggle.onclick = () => {
    document.body.classList.toggle("dark");

    localStorage.setItem(
      "theme",
      document.body.classList.contains("dark") ? "dark" : "light"
    );

    updateButton();
  };
}

// ART ==================================
function openLightbox(img){
  const lightbox = document.getElementById("lightbox");
  const lightboxImg = document.getElementById("lightbox-img");

  lightboxImg.src = img.src;

  lightbox.classList.add("active");
}

function closeLightbox(){
  document.getElementById("lightbox").classList.remove("active");
}

document.addEventListener("keydown", function(event){
  if(event.key === "Escape"){
    closeLightbox();
  }
});