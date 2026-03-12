// ART ==================================
const galleryImages = document.querySelectorAll(".gallery-item img");
const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightbox-img");

const prevBtn = document.querySelector(".prev");
const nextBtn = document.querySelector(".next");

let currentIndex = 0;

galleryImages.forEach((img, index) => {
  img.addEventListener("click", () => {
    currentIndex = index;
    showImage();
    lightbox.classList.add("active");
  });
});

function showImage(){
  lightboxImg.src = galleryImages[currentIndex].src;
}

function nextImage(){
  currentIndex++;

  if(currentIndex >= galleryImages.length){
    currentIndex = 0;
  }

  showImage();
}


function prevImage(){
  currentIndex--;

  if(currentIndex < 0){
    currentIndex = galleryImages.length - 1;
  }

  showImage();
}

nextBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  nextImage();
});

prevBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  prevImage();
});


lightbox.addEventListener("click", () => {
  lightbox.classList.remove("active");
});


document.addEventListener("keydown", (e) => {
  
  if(!lightbox.classList.contains("active")) return;
  
  if(e.key === "ArrowRight"){
    nextImage();
  }
  
  if(e.key === "ArrowLeft"){
    prevImage();
  }
  
  if(e.key === "Escape"){
    lightbox.classList.remove("active");
  }

});


/* SWIPE SUPPORT */
let startX = 0;
let endX = 0;

lightbox.addEventListener("touchstart", (e) => {
  startX = e.changedTouches[0].screenX;
});

lightbox.addEventListener("touchend", (e) => {
  endX = e.changedTouches[0].screenX;
  handleSwipe();
});

function handleSwipe(){
  const swipeDistance = endX - startX;

  if(Math.abs(swipeDistance) < 50) return;

  if(swipeDistance < 0){
    nextImage(); // swipe left
  } else {
    prevImage(); // swipe right
  }
}