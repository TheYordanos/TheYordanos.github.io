const btn = document.getElementById("fullscreen-btn");
const container = document.querySelector(".game-container");

btn.onclick = () => {

  if (!document.fullscreenElement) {
    container.requestFullscreen();
  } else {
    document.exitFullscreen();
  }

};