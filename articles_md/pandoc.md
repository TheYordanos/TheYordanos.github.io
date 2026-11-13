---
title: Pandoc cheatsheet
description: Reference for the Markdown syntax Pandoc turns into styled HTML on this site.
date: 2026-11-13
---

Everything here is styled by `article.css`. Anything not listed has no styling.

## Workflow

```bat
build.bat      # build.sh on Unix
```

- Write `articles_md/name.md`. It builds to `articles/name.html`, and the filename is the URL.
- Every build deletes `articles/*.html` first, then regenerates the list in `index.html`.
- `draft: true` in the front matter skips an article completely.

## Front matter

```yaml
---
title: Chess in Odin
description: Meta description for search and link previews.
date: 2026-09-12
draft: true
---
```

| Field         | Purpose                                                        |
|:--------------|:---------------------------------------------------------------|
| `title`       | Page title, the `<h1>`, and the entry in the index list.       |
| `description` | Meta description.                                              |
| `date`        | `YYYY-MM-DD`. The index list is sorted newest first.           |
| `draft`       | Optional. `true` skips the article.                            |

## Inline

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

## Headings

```markdown
## Section
### Subsection
#### Level 4
```

- Start at `##`. The title already is the `<h1>`.
- Every heading gets an id from its text: `## Some Title` is linkable as `#some-title`.

## Paragraphs and line breaks

```markdown
A blank line starts a new paragraph.

A backslash at the end of a line\
forces a line break.
```

## Lists

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

## Quotes and rules

```markdown
> Quote text.
>
> — Attribution
```

Result:

> Quote text.
>
> — Attribution

The last paragraph of a quote with two or more paragraphs is right-aligned and smaller, so use it for the attribution only.

```markdown
| line one
| line two
```

Result (a line block keeps its line breaks, good for addresses and poems):

| line one
| line two

A horizontal rule is `---` on its own line with a blank line on each side.

## Code

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

## Tables

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

The colons in the divider row set alignment. Wide tables scroll sideways on a phone.

## Images and media

Paths are relative to the built page in `articles/`, so a file in `res/` is `../res/`.

| Write                    | Get                                               |
|:-------------------------|:--------------------------------------------------|
| `![Caption](../res/a.png)`  | Figure. The alt text becomes the caption.      |
| `![Alt](../res/a.png)\`     | Plain image. The trailing backslash stops the figure. |
| `![](../res/a.mp4)`         | Video player.                                  |
| `![](../res/a.mp3)`         | Audio player.                                  |

Images are full width and capped at 500px tall.

## Footnotes

```markdown
Text with a note.[^1]

[^1]: The note. It can sit anywhere in the file.
```

Result: Text with a note.[^demo]

[^demo]: Notes collect at the bottom of the page and link back to where they came from.

## Gotchas

- Put a blank line before lists, quotes, tables and code fences, or they render as plain text.
- Raw HTML passes through, but `article.css` has no rules for `kbd`, `mark`, `details`, `abbr` or `iframe`. Avoid them.
- Escape special characters with a backslash: `\*`, `\_`, `\#`, `\|`.
- Two `$` in one paragraph can be read as math. Write `\$` for a literal dollar sign.
- Straight quotes, `--` and `...` are converted to curly quotes, dashes and an ellipsis. Escape with a backslash to keep them literal.
