---
title: Drawing
description: Shapes, lines, textures and text, plus how Karl2D batches draw calls.
project: Karl2D
order: 4
updated: 2026-11-22
---
All drawing happens between `clear` and `present`. Positions are in pixels, rotation in radians, and colors are `Color` values (`[4]u8`).

## Colors

Karl2D has named colors such as `WHITE`, `BLACK`, `BLANK` (fully transparent), `RED`, `GREEN`, `BLUE`, `ORANGE`, `PURPLE`, `MAGENTA`, `YELLOW` and `BROWN`. Most come in `LIGHT_` and `DARK_` variants, and there are grays: `LIGHT_GRAY`, `GRAY` and `DARK_GRAY`. The `examples/palette` folder in the repository has a demo that shows them all.

For porting from Raylib there are `RL_` colors, such as `RL_RAYWHITE`, `RL_SKYBLUE` and `RL_GOLD`.

You can also write colors out directly. `color_alpha` returns the same color with a different alpha:

```odin
glass := k2.color_alpha(k2.BLUE, 128)
custom := k2.Color { 30, 30, 40, 255 }
```

## Rectangles

```odin
draw_rect :: proc(rect: Rect, color: Color, origin: Vec2 = {}, rotation: f32 = 0)
draw_rect_vec :: proc(position: Vec2, size: Vec2, color: Color, origin: Vec2 = {}, rotation: f32 = 0)
draw_rect_outline :: proc(r: Rect, thickness: f32, color: Color)
```

The `x` and `y` of a `Rect` is its top-left corner. `draw_rect_vec` is the same thing with a position and a size instead of a `Rect`.

`origin` is the point the rectangle rotates around. It also shifts the rectangle. With `{0, 0}` it rotates around its top-left corner. With `{w/2, h/2}` it rotates around its center.

```odin
r := k2.Rect { 400, 300, 100, 60 }
k2.draw_rect(r, k2.ORANGE, origin = {50, 30}, rotation = f32(k2.get_time()))
```

`draw_rect_outline` draws the border with four rectangles.

## Circles, lines and triangles

```odin
draw_circle :: proc(center: Vec2, radius: f32, color: Color, segments := 16)
draw_circle_outline :: proc(center: Vec2, radius: f32, thickness: f32, color: Color, segments := 16)
draw_line :: proc(start: Vec2, end: Vec2, thickness: f32, color: Color)
draw_triangle :: proc(vertices: [3]Vec2, c: Color)
```

Circles are not perfect: they are made from `segments` triangle slices. Raise the number for large circles. Triangles can be wound either way and look the same.

```odin
k2.draw_circle({200, 200}, 40, k2.RED, segments = 48)
k2.draw_line({0, 0}, {300, 200}, 4, k2.WHITE)
k2.draw_triangle({{100, 400}, {160, 300}, {220, 400}}, k2.GREEN)
```

## Textures

There are three ways to draw a texture. Load it first, see [Textures and images](karl2d_textures.html).

### draw_texture

```odin
draw_texture :: proc(
	texture: Texture,
	position: Vec2,
	origin: Vec2 = {},
	rotation: f32 = 0,
	tint := WHITE,
)
```

Draws the whole texture with its top-left corner at `position`.

- `origin` is an offset for the position and the point to rotate around
- `rotation` is in radians
- `tint` is multiplied with the texture colors, and `WHITE` means no change

To rotate around the middle of a texture, use the texture's middle as the origin and add it to the position so the sprite stays where it was:

```odin
middle := k2.rect_middle(k2.get_texture_rect(tex))
k2.draw_texture(tex, pos + middle, middle, rot)
```

### draw_texture_rect

```odin
draw_texture_rect :: proc(texture: Texture, source: Rect, position: Vec2, origin: Vec2 = {}, rotation: f32 = 0, tint := WHITE)
```

Draws only the part of the texture inside `source`, which is measured in texture pixels. Use it for sprite sheets. A negative width or height in `source` flips the image.

```odin
// the third frame in a row of 32x32 frames
frame := k2.Rect { 64, 0, 32, 32 }
k2.draw_texture_rect(sheet, frame, player.pos)
```

### draw_texture_fit

```odin
draw_texture_fit :: proc(texture: Texture, source: Rect, dest: Rect, origin: Vec2 = {}, rotation: f32 = 0, tint := WHITE)
```

Takes a `source` rectangle (texture pixels) and stretches it into a `dest` rectangle (world pixels). Use it to scale an image to a size.

```odin
k2.draw_texture_fit(tex, k2.get_texture_rect(tex), {0, 0, 640, 360})
```

## Text

```odin
draw_text :: proc(
	text: string,
	position: Vec2,
	font_size: f32,
	color: Color,
	font := FONT_DEFAULT,
	origin: Vec2 = {},
	rotation: f32 = 0,
)

measure_text :: proc(text: string, font_size: f32, font: Font = FONT_DEFAULT) -> Vec2
```

`position` is the top-left of the text. If you use a camera, Karl2D scales the font size internally so text stays sharp. Without a `font` argument the built-in Roboto font is used. See [Fonts](karl2d_fonts.html) for loading your own.

`measure_text` returns how much room text takes. Use it to center or right-align:

```odin
msg := "Game Over"
size := k2.measure_text(msg, 64)
pos := (k2.get_screen_size() - size) / 2
k2.draw_text(msg, pos, 64, k2.WHITE)
```

## Batching and draw calls

Karl2D collects what you draw into a **batch**: a list of vertices plus a list of draw calls. The batch is sent to the GPU when it is flushed. This happens when you call `present` or `clear`, when the vertex buffer is full, or when you destroy a resource that the current batch uses. You can also flush by hand:

```odin
draw_current_batch :: proc()
```

You rarely need to. What matters is that some changes start a **new draw call**, and fewer draw calls is faster:

| Change | Starts a new draw call? |
|--------|------------------------|
| Drawing with a different texture | Yes |
| `set_shader` | Yes |
| `set_blend_mode` | Yes |
| `set_scissor_rect` | Yes |
| `set_camera` | Yes |
| `set_render_texture` | Yes |
| `set_z` | No |

The practical advice: put many images in one big texture (an atlas) and draw things that share a texture together.

Within a batch, the vertex buffer holds `VERTEX_BUFFER_MAX` bytes. The maximum vertex count is `VERTEX_BUFFER_MAX / shader.vertex_size`. If you run out of room, the batch is flushed for you.
