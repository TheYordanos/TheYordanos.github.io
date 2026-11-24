(function () {
	var toggle = document.getElementById("docs-toggle");
	var nav = document.querySelector(".docs-nav");
	if (nav && toggle) {
		nav.addEventListener("click", function (e) {
			if (e.target.closest("a")) toggle.checked = false;
		});
	}

	var here = document.querySelector(".docs-pages [aria-current]");
	if (nav && here && here.offsetParent && nav.scrollHeight > nav.clientHeight) {
		nav.scrollTop += here.getBoundingClientRect().top
			- nav.getBoundingClientRect().top - nav.clientHeight / 2;
	}

	var toc = document.getElementById("TOC");
	if (!toc) return;

	var entries = [];
	toc.querySelectorAll('a[href^="#"]').forEach(function (a) {
		var id = decodeURIComponent(a.getAttribute("href").slice(1));
		var el = document.getElementById(id);
		if (el) entries.push({ link: a, el: el });
	});
	if (!entries.length) return;

	var current = null;
	var queued = false;

	function update() {
		queued = false;
		var active = entries[0];
		for (var i = 0; i < entries.length; i++) {
			if (entries[i].el.getBoundingClientRect().top <= 90) active = entries[i];
			else break;
		}
		// at the very bottom, the last heading may never reach the top
		if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) {
			active = entries[entries.length - 1];
		}
		if (active === current) return;
		current = active;
		entries.forEach(function (x) { x.link.classList.toggle("active", x === active); });
	}

	function onScroll() {
		if (!queued) {
			queued = true;
			requestAnimationFrame(update);
		}
	}

	window.addEventListener("scroll", onScroll, { passive: true });
	window.addEventListener("resize", onScroll);
	update();
})();
