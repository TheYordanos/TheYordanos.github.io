---
title: Misc
description: Blend modes, scissor, depth sorting, cursors, hot reload, opening URLs and the experimental UI button.
project: Karl2D
order: 11
updated: 2026-11-22
---
## Blend modes

```odin
set_blend_mode :: proc(mode: Blend_Mode)
```

Chooses how new colors mix with what is already on the screen. The default is `.Alpha`. Changing it starts a new draw call.

| Mode | Meaning |
|------|---------|
| `.Alpha` | Normal transparency |
| `.Premultiplied_Alpha` | Needs alpha already multiplied into the color channels. Load textures with the `Premultiply_Alpha` option (and fonts with `premultiply_alpha`) |
| `.Additive` | Adds the source color, multiplied by its alpha, to what is there. Good for glows, fire and light |

```odin
k2.set_blend_mode(.Additive)
k2.draw_circle(light_pos, 80, k2.color_alpha(k2.YELLOW, 120))
k2.set_blend_mode(.Alpha)
```

## Scissor rectangle

```odin
set_scissor_rect :: proc(scissor_rect: Maybe(Rect))
```

Everything outside the rectangle (in screen space) is not drawn. Pass `nil` to turn it off. It is useful for scroll areas and clipped panels. Changing it starts a new draw call.

```odin
k2.set_scissor_rect(list_area)
draw_list_items()
k2.set_scissor_rect(nil)
```

## Depth and z

Turn on `depth_test` in `Init_Options` and draws are sorted by z instead of by drawing order:

```odin
k2.init(1280, 720, "Layers", options = { depth_test = true })

k2.set_z(1)
draw_player()
k2.set_z(0)
draw_background() // still ends up behind the player
```

- Higher z is in front. Things at the same z follow drawing order.
- The default range is -1 to 1 (`DEPTH_RANGE_DEFAULT_MIN` and `DEPTH_RANGE_DEFAULT_MAX`). Set `depth_range_min` and `depth_range_max` to use other numbers, such as 0 to 1000 if you want to feed world coordinates to `set_z`.
- `get_z()` returns the current value, which starts at 0.
- `set_z` has no effect without `depth_test`. It never starts a new draw call, so you can call it before every draw.

## Cursors

```odin
k2.set_cursor(.Hand)
```

`Cursor` is either a `Standard_Cursor` from the OS or a `Custom_Cursor` you made. `set_cursor(.Default)` goes back to the normal arrow.

Standard cursors: `Default`, `Text`, `Hand`, `Crosshair`, `Wait`, `Progress`, `Resize_EW`, `Resize_NS`, `Resize_NESW`, `Resize_NWSE`, `Move` and `Not_Allowed`.

Not every platform has all of them, and the nearest one is used instead. macOS has no public busy cursor (so `Wait` and `Progress` show the arrow) or diagonal resize cursors (so `Resize_NESW` and `Resize_NWSE` show the arrow too). On Linux they come from the user's cursor theme, and a missing one falls back to whatever the window inherits, usually the arrow.

### Custom cursors

```odin
icon := k2.load_image_from_file("cursor.png")
cursor := k2.create_custom_cursor(icon, hotspot = {4, 4})
k2.destroy_image(icon) // the cursor does not need it anymore

k2.set_cursor(cursor)
```

`hotspot` is the pixel inside the image that does the pointing, in physical pixels. Returns `(Custom_Cursor, bool)`. If it fails, setting it leaves the cursor as it is. `destroy_custom_cursor` frees it, and restores the default cursor if it was showing.

### Hiding the cursor

`set_cursor_hidden(true)` hides it and `is_cursor_hidden()` tells you the real state. The OS may show the cursor again, for example when the window loses focus, so check `is_cursor_hidden()` and hide again when needed. Hiding does not lock the mouse. See [Input](karl2d_input.html#locking-the-mouse).

## Built-in images

Karl2D can make its own icon and logo as `Image` values:

```odin
icon := k2.make_karl2d_icon(64)
logo := k2.make_karl2d_logo(300)
```

The icon is `size × size` pixels, scaled up from 16×16 pixel art, so use a multiple of 16. The logo is `width × width/3` pixels from 30×10 pixel art, so use a multiple of 30. Free them with `destroy_image`. `init` uses the icon as the default window icon.

## Hot reload

`init` returns a pointer to Karl2D's internal state. When you reload the library, that state is lost. Save the pointer and give it back afterwards with `set_internal_state`:

```odin
state := k2.init(1280, 720, "Hot")
// ... library reloaded ...
k2.set_internal_state(state)
```

Built-in hot reload is only planned. There is an experimental template in the separate `karl2d-hot-reload-template` repository.

## Opening URLs

```odin
if err := k2.open_url("https://odin-lang.org"); err != .None {
	// handle it
}
```

The URL must start with `https://`, `http://` or `file:///`, and may not contain spaces. The result is an `Open_URL_Error`: `.None` on success, `.Invalid_URL` for a bad URL and `.Failed_To_Open` when the OS utility fails.

## Experimental UI

> **Experimental:** these may be removed.

```odin
ui_button_width :: proc(text: string, button_height: f32) -> f32
ui_button :: proc(r: Rect, text: string) -> bool
```

`ui_button` draws a button and returns `true` when pressed, by a left click or by a tap. The rectangle is in the space of the current camera. It exists mainly for the "Source" button in the examples. You are better off copying it into your own code than relying on it.

```odin
w := k2.ui_button_width("Play", 40)
if k2.ui_button({20, 20, w, 40}, "Play") {
	start_game()
}
```

## Platform notes

On Linux Karl2D tries Wayland first, then X11, and loads them at runtime, so neither has to be installed. Set the environment variable `KARL2D_LINUX_WINDOWING=x11` or `wayland` to override it, usually for troubleshooting.

The render backends are D3D11, OpenGL and WebGL. Choose between D3D11 and OpenGL on Windows with `-define:KARL2D_RENDER_BACKEND=gl` or `d3d11`.
