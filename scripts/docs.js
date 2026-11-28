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

	var input = document.getElementById("docs-search");
	var results = document.getElementById("docs-results");
	var body = document.querySelector(".docs-body");
	if (input && results && body) {
		var index = null;
		var loading = false;

		var waiting = [];

		function loadIndex(then) {
			if (index) return then();
			waiting.push(then);
			if (loading) return;
			loading = true;
			fetch("search.json")
				.then(function (r) { return r.json(); })
				.then(function (data) {
					index = data;
					var queued = waiting;
					waiting = [];
					queued.forEach(function (fn) { fn(); });
				})
				.catch(function () {
					loading = false;
					waiting = [];
					show([], "Search is unavailable here.");
				});
		}

		function clear() {
			input.value = "";
			results.textContent = "";
			body.classList.remove("searching");
		}

		function rank(entry, terms) {
			var title = entry.t.toLowerCase();
			var desc = entry.d.toLowerCase();
			var total = 0;
			for (var i = 0; i < terms.length; i++) {
				var term = terms[i];
				var found = 0;
				if (title.indexOf(term) === 0) found += 20;
				else if (title.indexOf(term) > 0) found += 12;
				if (desc.indexOf(term) >= 0) found += 3;
				for (var k = 0; k < entry.s.length && found < 20; k++) {
					if (entry.s[k][0].toLowerCase().indexOf(term) >= 0) { found += 6; break; }
				}
				for (var m = 0; m < entry.s.length; m++) {
					if (entry.s[m][2].toLowerCase().indexOf(term) >= 0) { found += 1; break; }
				}
				if (!found) return null;
				total += found;
			}
			return { score: total, entry: entry, section: bestSection(entry, terms) };
		}

		function bestSection(entry, terms) {
			var best = null;
			var bestScore = 0;
			for (var i = 0; i < entry.s.length; i++) {
				var name = entry.s[i][0].toLowerCase();
				var text = entry.s[i][2].toLowerCase();
				var s = 0;
				for (var t = 0; t < terms.length; t++) {
					if (name.indexOf(terms[t]) >= 0) s += 6;
					if (text.indexOf(terms[t]) >= 0) s += 1;
				}
				if (s > bestScore) { bestScore = s; best = entry.s[i]; }
			}
			return best;
		}

		function snippet(entry, section, term) {
			var source = section ? section[2] : entry.d;
			var at = section ? source.toLowerCase().indexOf(term) : -1;
			if (at < 0) return [source.slice(0, 110), -1, 0];
			var from = Math.max(0, at - 40);
			var text = (from ? "\u2026" : "") + source.slice(from, at + term.length + 70);
			return [text, at - from + (from ? 1 : 0), term.length];
		}

		function show(list, message, term) {
			results.textContent = "";
			body.classList.add("searching");
			if (!list.length) {
				var none = document.createElement("span");
				none.className = "r-empty";
				none.textContent = message || "No results.";
				results.appendChild(none);
				return;
			}
			list.forEach(function (hit) {
				var entry = hit.entry;
				var section = hit.section;
				var a = document.createElement("a");
				a.href = entry.u + (section && section[1] ? "#" + section[1] : "");
				var title = document.createElement("span");
				title.className = "r-title";
				title.textContent = entry.t;
				a.appendChild(title);
				if (entry.p) {
					var path = document.createElement("span");
					path.className = "r-path";
					path.textContent = entry.p;
					a.appendChild(path);
				}
				if (section && section[0]) {
					var sec = document.createElement("span");
					sec.className = "r-sec";
					sec.textContent = "# " + section[0];
					a.appendChild(sec);
				}
				var s = snippet(entry, section, term);
				if (s[0]) {
					var snip = document.createElement("span");
					snip.className = "r-snip";
					if (s[1] >= 0) {
						snip.appendChild(document.createTextNode(s[0].slice(0, s[1])));
						var m = document.createElement("mark");
						m.textContent = s[0].slice(s[1], s[1] + s[2]);
						snip.appendChild(m);
						snip.appendChild(document.createTextNode(s[0].slice(s[1] + s[2])));
					} else {
						snip.textContent = s[0];
					}
					a.appendChild(snip);
				}
				results.appendChild(a);
			});
		}

		function run() {
			var query = input.value.trim().toLowerCase();
			if (!query) return clear();
			loadIndex(function () {
				var terms = query.split(/\s+/);
				var scope = (input.getAttribute("data-project") || "").toLowerCase();
				var ranked = [];
				index.forEach(function (entry) {
					if (entry.j.toLowerCase() !== scope) return;
					var hit = rank(entry, terms);
					if (hit) ranked.push(hit);
				});
				ranked.sort(function (a, b) { return b.score - a.score || a.entry.t.localeCompare(b.entry.t); });
				show(ranked.slice(0, 8), "", terms[0]);
			});
		}

		input.addEventListener("input", run);
		input.addEventListener("focus", function () { loadIndex(function () {}); });

		input.addEventListener("keydown", function (e) {
			var links = results.querySelectorAll("a");
			if (e.key === "Escape") {
				clear();
			} else if (e.key === "Enter" && links.length) {
				links[0].click();
			} else if (e.key === "ArrowDown" && links.length) {
				e.preventDefault();
				links[0].focus();
			}
		});

		results.addEventListener("keydown", function (e) {
			var links = Array.prototype.slice.call(results.querySelectorAll("a"));
			var i = links.indexOf(document.activeElement);
			if (e.key === "ArrowDown" && i < links.length - 1) {
				e.preventDefault();
				links[i + 1].focus();
			} else if (e.key === "ArrowUp") {
				e.preventDefault();
				(i > 0 ? links[i - 1] : input).focus();
			} else if (e.key === "Escape") {
				clear();
				input.focus();
			}
		});

		document.addEventListener("keydown", function (e) {
			if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
			var t = document.activeElement;
			if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
			e.preventDefault();
			var toggle = document.getElementById("docs-toggle");
			if (toggle && !input.offsetParent) toggle.checked = true;
			input.focus();
		});
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
