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

document.querySelectorAll("main pre").forEach(pre => {
	const wrap = document.createElement("div");
	wrap.className = "code-wrap";
	pre.parentNode.insertBefore(wrap, pre);
	wrap.appendChild(pre);

	const button = document.createElement("button");
	button.type = "button";
	button.className = "copy-btn";
	button.textContent = "Copy";
	button.setAttribute("aria-label", "Copy code to clipboard");
	wrap.appendChild(button);

	let timer;
	function flash(label) {
		button.textContent = label;
		button.classList.add("done");
		clearTimeout(timer);
		timer = setTimeout(() => {
			button.textContent = "Copy";
			button.classList.remove("done");
		}, 1500);
	}

	button.addEventListener("click", async () => {
		const code = pre.querySelector("code") || pre;
		try {
			await copyText(code.textContent);
			flash("Copied");
		} catch {
			flash("Failed");
		}
	});
});
