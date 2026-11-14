---
title: A minimal static blog
description: The smallest useful blog setup. Markdown files turned into pages by Pandoc and one Python script, with no theme and no framework.
date: 2026-11-14
---

A blog is a folder of HTML files and one page that links to them. Everything else is optional.^[Plenty of good personal sites stay this close to the metal. [gingerbill.org](https://gingerbill.org) is one: a plain single-column list of articles and little else.] This is the smallest version of the workflow this site uses. You write Markdown, run one command and upload the folder.^[Any static host works. [GitHub Pages](https://pages.github.com) serves a repository's files as they are, and it is where this site lives.]

## The files

```text
index.html     front page, with a list the script fills in
style.css      all the styling
build.py       the build system
articles_md/   your Markdown, one file per article
articles/      generated HTML, never edited by hand
```

You need [Pandoc](https://pandoc.org/installing.html) and Python 3. Pandoc turns Markdown into HTML,^[The [Pandoc manual](https://pandoc.org/MANUAL.html) is long. You only need a handful of flags from it.] and Python does the rest.

## An article

A Markdown file with a small header on top:

```markdown
---
title: Hello
date: 2026-11-14
---

Some text, a [link](https://example.com) and `code`.
```

- The filename is the URL: `articles_md/hello.md` becomes `articles/hello.html`.
- `date` is `YYYY-MM-DD`. The list is sorted by it, newest first.
- `draft: true` keeps an article out of the build.

## The index page

An ordinary page with two comment lines where the list goes:

```html
<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>My blog</title>
	<link rel="stylesheet" href="style.css">
</head>
<body>
	<h1>My blog</h1>
	<ul>
		<!-- ARTICLES:START -->
		<!-- ARTICLES:END -->
	</ul>
</body>
</html>
```

## The build script

```python
import html, re, subprocess
from pathlib import Path

def front_matter(text):
	m = re.match(r"---\n(.*?)\n---", text, re.S)
	lines = m.group(1).splitlines() if m else []
	return {k.strip(): v.strip().strip("\"'")
		for k, v in (line.split(":", 1) for line in lines if ":" in line)}

Path("articles").mkdir(exist_ok=True)
posts = []
for md in sorted(Path("articles_md").glob("*.md")):
	meta = front_matter(md.read_text(encoding="utf-8"))
	if meta.get("draft") == "true":
		continue
	subprocess.run(["pandoc", str(md), "--standalone", "--css", "../style.css",
		"-o", f"articles/{md.stem}.html"], check=True)
	posts.append((meta.get("date", ""), md.stem, meta.get("title", md.stem)))

posts.sort(reverse=True)
items = "\n".join(
	f'\t\t<li>{d} <a href="articles/{slug}.html">{html.escape(t)}</a></li>'
	for d, slug, t in posts)

index = Path("index.html")
page = index.read_text(encoding="utf-8")
page = re.sub(r"(<!-- ARTICLES:START -->).*(<!-- ARTICLES:END -->)",
	lambda m: f"{m[1]}\n{items}\n\t\t{m[2]}", page, flags=re.S)
index.write_text(page, encoding="utf-8")
```

Run `python build.py` from the folder that holds `index.html`. It calls Pandoc once per article, then rewrites everything between the two comments. `--standalone` makes a complete page and `--css` links your stylesheet. The path is `../style.css` because articles live one folder down.

## The stylesheet

```css
body {
	max-width: 40rem;
	margin: 2rem auto;
	padding: 0 1rem;
	font: 1.1rem/1.6 system-ui, sans-serif;
}
pre { overflow-x: auto; padding: 1rem; background: #f4f4f4; }
img { max-width: 100%; }
```

That is all a page needs. Pandoc colors fenced code by itself, and because `--css` is given it leaves out its own page styles, so this file is in charge.

## Sidenotes

Footnotes at the bottom of a page pull you away from the text. Sidenotes put the note next to it instead.^[This is the idea behind [Tufte CSS](https://edwardtufte.github.io/tufte-css/), a stylesheet that imitates Edward Tufte's books and handouts. [tufte-pandoc-css](https://github.com/jez/tufte-pandoc-css) is a ready-made way to use it with Pandoc.] Pandoc has no option for them, but a short Lua filter does the job.^[Pandoc runs [Lua filters](https://pandoc.org/lua-filters.html) on the parsed document. Lua is built in, so there is nothing extra to install.] Save this as `sidenotes.lua`:

```lua
local n = 0

function Note(note)
	n = n + 1
	local id = "sn-" .. n
	local out = {
		pandoc.RawInline("html",
			'<label for="' .. id .. '" class="sidenote-number"></label>' ..
			'<input type="checkbox" id="' .. id .. '" class="margin-toggle">' ..
			'<span class="sidenote">')
	}
	for _, inline in ipairs(pandoc.utils.blocks_to_inlines(note.content)) do
		table.insert(out, inline)
	end
	table.insert(out, pandoc.RawInline("html", "</span>"))
	return out
end
```

Add `"--lua-filter", "sidenotes.lua"` to the Pandoc arguments in `build.py`, and this to `style.css`:

```css
body { counter-reset: sn; }
.sidenote-number { counter-increment: sn; }
.sidenote-number::after, .sidenote::before { font-size: .75em; vertical-align: super; }
.sidenote-number::after { content: counter(sn); }
.sidenote::before { content: counter(sn) " "; }
.sidenote { font-size: .85em; }
.margin-toggle { display: none; }

@media (min-width: 72rem) {   /* wide enough for a margin */
	.sidenote { float: right; clear: right; width: 14rem; margin-right: -16rem; }
}
@media (max-width: 71.99rem) {   /* too narrow: tap the number instead */
	.sidenote { display: none; }
	.margin-toggle:checked + .sidenote { display: block; margin: .5rem 0 1rem 1rem; }
}
```

Now write footnotes in Markdown as usual. The inline form is the easiest:

```markdown
A sentence with a note.^[The note sits right here in the source.]
```

## Growing it

Later, in rough order of usefulness: skip articles whose Markdown has not changed, give Pandoc your own HTML with `--template`, add an archive page, write an RSS feed. Each is a few lines. The cheatsheet below lists the Markdown that Pandoc understands.

## Cheatsheet

```text
python build.py     build every article and update the list
```

### Front matter

```yaml
---
title: Chess in Odin
date: 2026-09-12
draft: true
---
```

| Field   | Purpose                                              |
|:--------|:-----------------------------------------------------|
| `title` | Page title, the `<h1>`, and the entry in the list.   |
| `date`  | `YYYY-MM-DD`. The list is sorted newest first.       |
| `draft` | Optional. `true` skips the article.                  |

### Inline

| Write                         | Get                         |
|:------------------------------|:----------------------------|
| `*italic*`                    | *italic*                    |
| `**bold**`                    | **bold**                    |
| `***bold italic***`           | ***bold italic***           |
| `~~strike~~`                  | ~~strike~~                  |
| `H~2~O`                       | H~2~O                       |
| `E = mc^2^`                   | E = mc^2^                   |
| `` `code` ``                  | `code`                      |
| `[text](https://example.com)` | [text](https://example.com) |
| `<https://example.com>`       | <https://example.com>       |
| `[jump](#headings)`           | [jump](#headings)           |
| `\*not italic\*`              | \*not italic\*              |
| `"quotes" -- en --- em ...`   | "quotes" -- en --- em ...   |

Sub and superscript can't contain spaces. Escape them as `H~2\ O~` if you must.

### Headings

```markdown
## Section
### Subsection
#### Level 4
```

- Start at `##`. The title already is the `<h1>`.
- Every heading gets an id from its text: `## Some Title` is linkable as `#some-title`.

### Paragraphs and line breaks

```markdown
A blank line starts a new paragraph.

A backslash at the end of a line\
forces a line break.
```

### Lists

A blank line is required before a list. Nest with four spaces.

```markdown
- item
- item
    - nested
```

Result:

- item
- item
    - nested

```markdown
3. starts at 3
4. renumbers itself
```

Result:

3. starts at 3
4. renumbers itself

```markdown
- [x] done
- [ ] todo
```

Result:

- [x] done
- [ ] todo

```markdown
Term
:   Definition
```

Result:

Term
:   Definition

### Quotes and rules

```markdown
> Quote text.
>
> — Attribution
```

Result:

> Quote text.
>
> — Attribution

```markdown
| line one
| line two
```

Result (a line block keeps its line breaks, good for addresses and poems):

| line one
| line two

A horizontal rule is `---` on its own line with a blank line on each side.

### Code

Fence with three backticks and add the language after the opening fence. Use four backticks to show a fence inside a block.

````markdown
```odin
main :: proc() {
	fmt.println("Hellope!")
}
```
````

Result:

```odin
package main

import "core:fmt"

main :: proc() {
	fmt.println("Hellope!")
}
```

- Names that work include `odin`, `javascript`, `typescript`, `python`, `c`, `cpp`, `rust`, `go`, `java`, `lua`, `bash`, `html`, `css`, `json`, `yaml` and `markdown`.
- Full list: `pandoc --list-highlight-languages`.
- No language, or an unknown one, gives plain text.
- Inline code is single backticks. To put a backtick inside it, wrap it in double backticks with a space on each side.

### Tables

```markdown
| Left | Right | Center |
|:-----|------:|:------:|
| a    |     1 |   x    |
| b    |    22 |   y    |
```

Result:

| Left | Right | Center |
|:-----|------:|:------:|
| a    |     1 |   x    |
| b    |    22 |   y    |

The colons in the divider row set alignment.

### Images and media

Paths are relative to the built page in `articles/`, so a file in `res/` is `../res/`.

| Write                    | Get                                               |
|:-------------------------|:--------------------------------------------------|
| `![Caption](../res/a.png)`  | Figure. The alt text becomes the caption.      |
| `![Alt](../res/a.png)\`     | Plain image. The trailing backslash stops the figure. |
| `![](../res/a.mp4)`         | Video player.                                  |
| `![](../res/a.mp3)`         | Audio player.                                  |

Images are shrunk to the page width by the `img` rule in `style.css`.

### Notes

With the filter above, footnotes become sidenotes, so write them as ordinary footnotes. Either form works:

```markdown
Text with a note.[^1]

[^1]: The note. It can sit anywhere in the file.

Or write the note right in the sentence.^[Like this.]
```

Result: Text with a note.[^demo] Or write the note right in the sentence.^[Like this.]

[^demo]: On a wide screen this sits in the right margin. On a narrow one, tap the number to show it.

- Notes are numbered in the order they appear.
- A note with several paragraphs is joined into one block, so keep them short.

### Gotchas

- A title containing a colon must be quoted: `title: "Chess: a story"`.
- Put a blank line before lists, quotes, tables and code fences, or they render as plain text.
- Escape special characters with a backslash: `\*`, `\_`, `\#`, `\|`.
- Two `$` in one paragraph can be read as math. Write `\$` for a literal dollar sign.
- Straight quotes, `--` and `...` are converted to curly quotes, dashes and an ellipsis. Escape with a backslash to keep them literal.
