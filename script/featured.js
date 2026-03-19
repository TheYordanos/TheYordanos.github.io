const features = [

  {
    type: "Artwork",
    title: "Afro",
    desc: "Yet another afro guy illustration :D",
    media: `<img src="res/gallery/art007.png" alt="Afro artwork">`,
    link: "#gallery",
    linkText: "View More",
  },

  {
    type: "Game",
    title: "Flappy Clone",
    desc: "A small HTML canvas recreation of the classic Flappy Bird game.",
    media: `<img src="res/placeholder.png" alt="Flappy Clone">`,
    link: "play/test.html",
    linkText: "&#x25B6; Play",
    linkType: "button"
  },

  {
    type: "Article",
    title: "Boids",
    desc: "Birds flocking around on a screen",
    media: `<img src="res/featured/boids.png" alt="Article cover">`,
    link: "article/boids.html",
    linkText: "Read Article",
  },

  {
    type: "Music",
    title: "Soft Piano Loop",
    desc: "A minimal piano loop idea recorded for a new composition.",
    media: `
      <audio controls>
        <source src="audio/piano-loop.mp3" type="audio/mpeg">
      </audio>
    `,
    link: "#audio",
    linkText: "Listen More",
  }

];

const mediaContainer = document.querySelector(".featured-media");
const contentContainer = document.querySelector(".featured-content");

const item = features[Math.floor(Math.random() * features.length)];

mediaContainer.innerHTML = item.media;

contentContainer.innerHTML = `
  <p class="featured-type">${item.type}</p>
  <h3>${item.title}</h3>
  <p class="featured-desc">${item.desc}</p>
  <a class="${item.linkType == "button" ? 'play-btn' : 'featured-link'}" href="${item.link}">${item.linkText}</a>
`;