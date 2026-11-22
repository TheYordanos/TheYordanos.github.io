---
title: Textures and images
description: Loading textures and images, texture filtering, updating pixels and render textures.
project: Karl2D
order: 5
updated: 2026-11-22
---
A **texture** lives on the GPU and is what you draw. An **image** lives in RAM as an array of pixels. You load an image when you want the pixels themselves, for example for a window icon or a custom cursor.

## Texture

```odin
Texture :: struct {
	handle: Texture_Handle,
	width:  int,  // pixels
	height: int,  // pixels
}
```

## Loading textures

| Procedure | Source |
|-----------|--------|
| `load_texture_from_file(filename, options)` | A file on disk |
| `load_texture_from_bytes(bytes, options)` | An encoded file in memory, for example `#load("x.png")` |
| `load_texture_from_bytes_raw(bytes, width, height, format)` | Raw pixels with no header |
| `load_texture_from_image(image)` | An `Image` in RAM |
| `create_texture(width, height, format)` | A new empty texture |

All of them return `(Texture, bool)`. The `bool` is `true` if it worked. A failed texture is safe to use but draws nothing.

```odin
tex, ok := k2.load_texture_from_file("hero.png")
```

Supported formats are PNG, BMP and TGA. Progressive PNG files are **not** supported, only the baseline kind.

Use `_from_bytes` instead of `_from_file` on the web and whenever you want to embed assets in the executable. Use `_from_bytes_raw` only for data without a file header, such as pixels you generated. If you read a whole file from disk, use the plain `_from_bytes`.

### Load options

`options` is a `bit_set[Load_Texture_Option]`. The only option so far is `Premultiply_Alpha`, which multiplies alpha into the color channels when loading. Use it together with `set_blend_mode(.Premultiplied_Alpha)`, see [Misc](karl2d_misc.html#blend-modes).

```odin
tex := k2.load_texture_from_file("glow.png", { .Premultiply_Alpha })
```

## Pixel formats

`Pixel_Format` describes how pixels are stored. It is used by `create_texture`, `load_texture_from_bytes_raw` and shader layouts.

| Group | Values |
|-------|--------|
| 8-bit normalized | `RGBA_8_Norm`, `RG_8_Norm`, `R_8_Norm` |
| 8-bit integer | `R_8_UInt` |
| 32-bit float | `RGBA_32_Float`, `RGB_32_Float`, `RG_32_Float`, `R_32_Float` |
| Unset | `Unknown` |

`pixel_format_size(format)` returns how many bytes one pixel uses.

## Sizes and sub-rectangles

`get_texture_rect(tex)` returns a `Rect` covering the whole texture, `{0, 0, width, height}`. It is a good source rectangle for `draw_texture_fit`.

## Updating a texture

```odin
update_texture :: proc(tex: Texture, bytes: []u8, rect: Rect, pitch := 0) -> bool
```

Writes new pixels into part of an existing texture. `rect` is the area to overwrite, `bytes` holds the new pixels, and `pitch` is the number of bytes from the start of one row to the start of the next. The default of `0` means the rows are tightly packed.

## Filtering

Choose how a texture is filtered with `set_texture_filter`:

```odin
k2.set_texture_filter(sprite, .Point)   // sharp pixels, good for pixel art
k2.set_texture_filter(photo,  .Linear)  // smooth
```

`Texture_Filter` is `.Point` (like nearest neighbor) or `.Linear` (smooth). The setting is used for scaling up, scaling down and mipmap sampling.

For separate control use `set_texture_filter_ex(tex, scale_down_filter, scale_up_filter, mip_filter)`.

## Destroying

`destroy_texture(tex)` frees the GPU memory. If the current batch uses the texture, the batch is flushed first.

## Images

```odin
Image :: struct {
	pixels: []Color,
	width:  int,
	height: int,
}
```

`load_image_from_file` and `load_image_from_bytes` give you an `Image`. It is always RGBA8 with straight (not premultiplied) alpha. Call `destroy_image` when you are done. A failed load gives an empty image: no pixels and size zero.

There are no procedures for editing images yet, but you can build an `Image` yourself by filling in `pixels`, `width` and `height`, then pass it to `load_texture_from_image`.

```odin
img := k2.load_image_from_file("map.png")
defer k2.destroy_image(img)

tex := k2.load_texture_from_image(img)
```

## Render textures

A render texture is a texture you can draw **into** instead of drawing on the screen. Use it for minimap views, post-effects, caching expensive drawings, or a low-resolution game that is scaled up.

```odin
Render_Texture :: struct {
	texture:       Texture,
	render_target: Render_Target_Handle,
}
```

| Procedure | Job |
|-----------|-----|
| `create_render_texture(w, h)` | Create one. Returns `(Render_Texture, bool)` |
| `set_render_texture(rt)` | Make drawing go into it. Pass `nil` to go back to the screen |
| `destroy_render_texture(rt)` | Free it |

The `texture` field is a normal `Texture`, so you can draw it like any other. If creating the render texture fails, setting it does nothing and drawing stays on the screen.

```odin
minimap, _ := k2.create_render_texture(200, 200)

for k2.update() {
	// draw the world into the minimap
	k2.set_render_texture(minimap)
	k2.clear(k2.DARK_GREEN)
	draw_world_small()
	k2.set_render_texture(nil)

	// draw the real frame
	k2.clear(k2.BLACK)
	draw_world()
	k2.draw_texture(minimap.texture, {f32(k2.get_screen_width()) - 220, 20})
	k2.present()
}
```

While a render texture is set, `clear` clears the render texture, not the screen.
