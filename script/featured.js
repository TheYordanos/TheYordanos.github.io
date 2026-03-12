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
    linkText: "▶ Play",
    linkType: "button"
  },

  {
    type: "Article",
    title: "Trying to make money off Games",
    desc: "A short reflection on whether indie games can actually make money.",
    media: `<img src="res/placeholder.png" alt="Article cover">`,
    link: "blog/monetizing.html",
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