---
title: Gist reference
description: Every gist feature in one page, written as a template to copy from.
date: 2026-11-23
language: Goose
source: https://github.com/aardappel/goose
---
A gist is plain markdown. Prose goes anywhere, and every fenced block is either a **file** or a plain code block.

## Files

A file block puts `file="name"` in the fence. It gets line numbers, a Copy button and a Raw link. The text after `label=` is shown next to the line count, and you can write anything there. Without `label`, the block shows the `language` from the front matter.

````markdown
```{.goose file="hello.goose" label="Goose"}
fn main() { print("hello") }
```
````

The `.goose` class only picks syntax highlighting when Pandoc knows the language. Unknown ones render as plain text, which is fine.

```{.goose file="hello.goose"}
fn greet(name: string) -> string {
	"hello, " + name
}

fn main() {
	print(greet("goose"))
}
```

Files can use any extension and any label, so a theme or a config is no different from code.

```{.json file="Quiet.sublime-color-scheme" label="Sublime Text theme"}
{
	"name": "Quiet",
	"variables": {
		"bg": "#1c1e22",
		"fg": "#c9cdd4"
	},
	"globals": {
		"background": "var(bg)",
		"foreground": "var(fg)"
	},
	"rules": [
		{ "scope": "comment", "foreground": "#6b7280", "font_style": "italic" }
	]
}
```

```{file="focus.config" label="Focus config"}
[default]
tab_size: 4
highlight_line: true
```

## Plain blocks

A block without `file` is a normal code block with a hover Copy button. Use it for commands and short snippets.

```bash
build/goose file.goose
build/goose build file.goose
```

## Buttons

- **Copy all** appears when the gist has two or more files and copies them in order.
- **Download** is the file itself for one file, or a zip for several.
- **Source** appears when the front matter has `source:`.
- **Copy** and **Raw** sit on each file. Raw opens the plain text.

Gists with only plain blocks get none of these, and the Files row appears with two or more files.
