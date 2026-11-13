---
title: Pandoc
description: A cheat sheet of every Markdown element available when writing articles for this site, with the syntax and the result.
date: 2026-11-13
---

Everything in `articles_md/` is written in Markdown and turned into HTML by Pandoc when the build script runs. Pandoc's flavour of Markdown can do a lot, but this site only styles a specific set of elements. This article is the cheat sheet: each element, how to write it, and what it looks like once built.

## The basics

### Front matter

Every article starts with a block of metadata between two lines of three dashes.

```yaml
---
title: Chess in Odin
description: Shown in search results and link previews.
date: 2026-09-12
draft: true
---
```

- `title` becomes the page title, the big heading at the top, and the entry in the articles list on the home page.
- `description` goes into the page's meta description.
- `date` uses `YYYY-MM-DD`. The articles list is sorted by it, newest first.
- `draft: true` is optional. Drafts are skipped by the build, so they are never built or listed.

### Paragraphs and line breaks

A paragraph is any run of text. Start a new paragraph by leaving a blank line. To break a line without starting a new paragraph, end the line with a backslash.

```markdown
First line\
Second line, same paragraph.
```

Renders as:

First line\
Second line, same paragraph.

### Headings

The title already becomes the page's single top-level heading, so start your own headings at two hashes. Using a single `#` would add a second top-level heading.

```markdown
## Section
### Subsection
#### Level 4
##### Level 5
###### Level 6
```

Levels two and three are used throughout this article. Here are the smaller ones:

#### Level 4 heading

##### Level 5 heading

###### Level 6 heading

Each heading also gets an automatic anchor made from its text, lowercased with dashes between words. That means you can link to any section, for example `[see lists](#lists)`.

## Inline text

### Emphasis and strong

```markdown
*italic*, **bold**, and ***both***.
```

Renders as: *italic*, **bold**, and ***both***.

### Strikethrough

```markdown
~~deleted ideas~~
```

Renders as: ~~deleted ideas~~

### Superscript and subscript

Wrap text in carets for superscript and tildes for subscript. No spaces are allowed inside; escape a space with a backslash if you really need one.

```markdown
H~2~O and E = mc^2^
```

Renders as: H~2~O and E = mc^2^

### Inline code

Wrap code in backticks.

```markdown
Run `./build.sh` to rebuild.
```

Renders as: Run `./build.sh` to rebuild.

### Links

```markdown
[Pandoc's manual](https://pandoc.org/MANUAL.html)
<https://pandoc.org>
[jump to lists](#lists)
```

Renders as: [Pandoc's manual](https://pandoc.org/MANUAL.html), <https://pandoc.org>, and [jump to lists](#lists).

### Smart typography

Pandoc quietly improves punctuation: straight quotes become curly quotes, two dashes become an en dash, three become an em dash, and three dots become an ellipsis.

```markdown
"Quotes" -- dashes --- and ellipses...
```

Renders as: "Quotes" -- dashes --- and ellipses...

## Lists

### Unordered lists

Start each item with `-`. Indent nested items by four spaces. Leave a blank line before the list.

```markdown
- Never trust a suspicious-looking sandwich.
- The deeper you go, the stranger things become.
    - First, you find a spoon.
    - Then, you find another spoon.
```

Renders as:

- Never trust a suspicious-looking sandwich.
- The deeper you go, the stranger things become.
    - First, you find a spoon.
    - Then, you find another spoon.

### Ordered lists

Use numbers followed by a dot. The first number sets where the list starts, and the rest are renumbered automatically.

```markdown
3. Stare at the ceiling.
4. Question the existence of ceilings.
5. Repeat until further notice.
```

Renders as:

3. Stare at the ceiling.
4. Question the existence of ceilings.
5. Repeat until further notice.

### Task lists

Put `[ ]` or `[x]` after the dash for checkboxes.

```markdown
- [x] Write the article
- [ ] Proofread it
```

Renders as:

- [x] Write the article
- [ ] Proofread it

### Definition lists

Put the term on its own line, then start the definition on the next line with a colon and spaces.

```markdown
Debugging
:   Removing bugs from software while introducing new problems.
```

Renders as:

Debugging
:   Removing bugs from software while introducing new problems.

## Quotes and breaks

### Blockquotes

Start each line with `>`. For an attribution, add a final paragraph that begins with an em dash. The stylesheet right-aligns and shrinks the last paragraph of any quote that has two or more paragraphs, so keep the attribution as the last one.

```markdown
> The moon is just the sun's night shift.
>
> — Anonymous Moon Economist
```

Renders as:

> The moon is just the sun's night shift.
>
> — Anonymous Moon Economist

### Line blocks

Line blocks keep each line break exactly as written. Start every line with a vertical bar and a space. They suit addresses and poems.

```markdown
| Written somewhere on Earth,
| Probably near a coffee shop,
| Planet Earth, Solar System.
```

Renders as:

| Written somewhere on Earth,
| Probably near a coffee shop,
| Planet Earth, Solar System.

### Horizontal rules

Put three dashes on a line by themselves, with a blank line on each side.

```markdown
---
```

Renders as:

---

## Media

Image and media paths are relative to the built page, which lives in `articles/`. A file in `res/` is therefore written as `../res/file.png`. These are shown as code only, so no broken images appear on this page.

### Images with captions

An image on its own in a paragraph becomes a figure, and its alt text is used as the caption.

```markdown
![Figure 1. The finished board.](../res/board.png)
```

### Images without captions

To keep an image as a plain image, add a backslash straight after it. The backslash becomes a line break, which stops Pandoc from treating the image as a figure.

```markdown
![The finished board](../res/board.png)\
```

Images fill the width of the article and are capped at 500 pixels tall.

### Video and audio

Use the image syntax with a video or audio file. Pandoc recognises the file extension and builds a video or audio player instead of an image.

```markdown
![](../res/demo.mp4)

![](../res/theme.mp3)
```

## Code and tables

### Code blocks

Fence the code with three backticks and name the language after the opening fence. Pandoc highlights the code when it builds the page, and the colors switch along with the light and dark toggle. Names that work include `javascript`, `typescript`, `python`, `c`, `cpp`, `rust`, `go`, `java`, `lua`, `bash`, `html`, `css`, `json`, `yaml` and `markdown`. Run `pandoc --list-highlight-languages` to see the full list. A block with no language, or one Pandoc doesn't know, is shown in plain text.

````markdown
```javascript
function makeSandwich() {
	return { bread: "bread", cheese: "cheese" };
}
```
````

Renders as:

```javascript
function makeSandwich() {
	return { bread: "bread", cheese: "cheese" };
}
```

To show a code block inside a code block, as above, use four backticks for the outer fence.

### Tables

Separate columns with vertical bars. The dashes under the header row can have colons to set alignment.

```markdown
| Object       | Quantity | Importance     |
|:-------------|---------:|:--------------:|
| Potatoes     |       17 | Very high      |
| Rubber ducks |       42 | Extremely high |
```

Renders as:

| Object       | Quantity | Importance     |
|:-------------|---------:|:--------------:|
| Potatoes     |       17 | Very high      |
| Rubber ducks |       42 | Extremely high |

## Footnotes

Mark the spot with `[^label]` and write the note anywhere in the file as `[^label]: The note`. All footnotes are collected at the bottom of the page, each with a link back to where it came from.

```markdown
Footnotes are tidy.[^tidy]

[^tidy]: They are collected at the bottom of the article.
```

Renders as: Footnotes are tidy.[^tidy]

[^tidy]: They are collected at the bottom of the article.

## What is not covered

Pandoc passes raw HTML through untouched, but the stylesheet has no rules for tags such as `<kbd>`, `<mark>`, `<details>`, `<abbr>` or `<iframe>`, so they will look unstyled. Stick to the elements above and every article will match the rest of the site.
