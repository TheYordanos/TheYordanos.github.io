async function copyText(text) {
	if (navigator.clipboard && window.isSecureContext) {
		return navigator.clipboard.writeText(text);
	}

	// Fallback for contexts where the clipboard API isn't available
	const area = document.createElement("textarea");
	area.value = text;
	area.style.position = "fixed";
	area.style.opacity = "0";
	document.body.appendChild(area);
	area.select();
	const ok = document.execCommand("copy");
	area.remove();
	if (!ok) throw new Error("copy failed");
}

function bindCopy(button, getText, idleLabel) {
	let timer;
	function flash(label) {
		button.textContent = label;
		button.classList.add("done");
		clearTimeout(timer);
		timer = setTimeout(() => {
			button.textContent = idleLabel;
			button.classList.remove("done");
		}, 1500);
	}

	button.addEventListener("click", async () => {
		try {
			await copyText(getText());
			flash("Copied");
		} catch {
			flash("Failed");
		}
	});
}

function makeButton(className, label, ariaLabel) {
	const button = document.createElement("button");
	button.type = "button";
	button.className = className;
	button.textContent = label;
	button.setAttribute("aria-label", ariaLabel);
	return button;
}

document.querySelectorAll("main pre").forEach(pre => {
	if (pre.closest(".gist-file")) return;

	const wrap = document.createElement("div");
	wrap.className = "code-wrap";
	pre.parentNode.insertBefore(wrap, pre);
	wrap.appendChild(pre);

	const button = makeButton("copy-btn", "Copy", "Copy code to clipboard");
	wrap.appendChild(button);
	bindCopy(button, () => (pre.querySelector("code") || pre).textContent, "Copy");
});

function gistText(figure) {
	const code = figure.querySelector(".gist-code > :not(.gist-gutter)");
	return code.textContent.replace(/\n+$/, "") + "\n";
}

document.querySelectorAll("figure.gist-file").forEach(figure => {
	const button = makeButton("gist-btn", "Copy", "Copy file to clipboard");
	const caption = figure.querySelector("figcaption");
	caption.insertBefore(button, caption.querySelector("a.gist-btn"));
	bindCopy(button, () => gistText(figure), "Copy");
});
