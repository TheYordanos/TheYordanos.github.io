---
title: Fonts
description: The default font, loading your own TTF fonts, and the difference between static and dynamic fonts.
project: Karl2D
order: 6
updated: 2026-11-22
---
A `Font` is a small handle (`distinct int`). Pass it to `draw_text` and `measure_text` with the `font` argument.

```odin
font := k2.load_dynamic_font_from_file("fonts/lato.ttf")
k2.draw_text("Score: 100", {20, 20}, 32, k2.WHITE, font)
```

## Built-in fonts

| Constant | Meaning |
|----------|---------|
| `FONT_DEFAULT` | The built-in Roboto font. Used when you don't pass a font |
| `FONT_NONE` | The zero font, meaning "no font" |

## Static and dynamic fonts

Karl2D supports two kinds of font. Pick based on how you use the text.

| | Static | Dynamic |
|--|--------|---------|
| How it works | Characters you choose are baked into a texture once, at one size | An atlas grows as you draw new characters |
| Size | Fixed at load: `font_size` | Any size per `draw_text` call |
| Characters | ASCII 32 to 127 by default, or your own `codepoints` | Whatever you draw |
| Good for | Pixel fonts, a fixed UI size, predictable memory | Most text, especially with several sizes |

All dynamic fonts share one atlas that can grow to 4096×4096. When it is full, it is compacted: the least recently used 50% of the glyphs are thrown out and will be re-created if you draw them again.

## Loading static fonts

```odin
load_static_font_from_file :: proc(
	filename: string,
	font_size: f32,
	codepoints: []rune = {},
	options: Font_Options = {},
) -> (Font, bool) #optional_ok

load_static_font_from_bytes :: proc(
	data: []byte,
	font_size: f32,
	codepoints: []rune = {},
	options: Font_Options = {},
) -> (Font, bool) #optional_ok
```

Both load a TTF font and bake its characters at `font_size` into a texture. Leave `codepoints` empty to get ASCII.

```odin
// bake only the digits and a few symbols
chars := []rune { '0','1','2','3','4','5','6','7','8','9','+','-','%' }
numbers := k2.load_static_font_from_file("fonts/pixel.ttf", 16, chars)
```

## Loading dynamic fonts

```odin
load_dynamic_font_from_file :: proc(filename: string, options: Font_Options = {}) -> (Font, bool) #optional_ok
load_dynamic_font_from_bytes :: proc(data: []u8, options: Font_Options = {}) -> (Font, bool) #optional_ok
```

No size and no codepoint list: they are not needed. Use `_from_bytes` with `#load` for the web and for single-file builds:

```odin
font := k2.load_dynamic_font_from_bytes(#load("fonts/lato.ttf"))
```

## Font_Options

| Field | Meaning |
|-------|---------|
| `premultiply_alpha` | Multiply alpha into the color when the font is loaded. Use with `set_blend_mode(.Premultiplied_Alpha)` |
| `filter` | `.Point` or `.Linear`, used when drawing text with this font |
| `font_index` | Picks one font out of a collection such as `.ttc`. Leave at 0 for normal fonts |

```odin
pixel := k2.load_static_font_from_file("pixel.ttf", 8, options = { filter = .Point })
```

## Errors

Like other loaders these return `(Font, bool)`. If loading fails, the returned font is still safe to use, and text drawn with it uses the default font.

## Destroying

`destroy_font(font)` frees a font.

## Planned

The source mentions a future *Slug* type, which uploads glyph curves to the GPU and needs no atlas. It is not implemented yet.
