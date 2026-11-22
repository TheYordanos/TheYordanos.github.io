---
title: Overview
description: Compact reference for Karl2D, a beginner friendly 2D game library for Odin (Windows, Linux, Mac, Web).
project: Karl2D
order: 1
updated: 2026-11-22
---
Karl2D makes 2D games in [Odin](https://odin-lang.org) with few dependencies and no emscripten for web builds. Everything is called as `k2.name`. This page follows the API overview file `karl2d.doc.odin`.

## Getting started

Put the Karl2D repository in a `karl2d` subfolder of your game, then:

```odin
package hello_world

import k2 "karl2d"

main :: proc() {
	k2.init(1280, 720, "Greetings from Karl2D!")

	for k2.update() {
		k2.clear(k2.LIGHT_BLUE)
		k2.draw_text("Hellope!", {50, 50}, 100, k2.DARK_BLUE)
		k2.present()
	}

	k2.shutdown()
}
```

Run with `odin run .` from the game folder.

## Conventions

- **Units:** pixels, radians, seconds. Origin is top-left, Y grows down
- **Types:** `Vec2` is `[2]f32`, `Color` is `[4]u8`, `Rect` is `{x, y, w, h}` with `(x, y)` top-left
- **Loaders** return `(value, bool)`. Checking the `bool` is optional, failures are logged, and a failed value is safe to use but draws or plays nothing
- **Handles** (`Texture`, `Sound`, `Font`...) are cheap to copy. A finished `Sound` handle is safe: its procs do nothing
- **Per-frame slices** from `get_events`, `get_typed_runes` and `get_touches` are only valid this frame. Clone with `slice.clone`
- **`Maybe(...)` settings** (camera, shader, render texture, scissor): pass a value to enable, `nil` to reset

## Frame and window

| Procedure | Job |
|-----------|-----|
| `init(w, h, title, options, allocator)` | Open window, start renderer and audio. Call before almost everything (`get_monitors` is the exception). Returns `^State` |
| `update()` | Read input, update frame time, run audio. Returns `false` when the player tries to close |
| `clear(color)` | Clear the screen (or the current render texture) |
| `present()` | Show the frame. Call it on web too |
| `shutdown()` | Close and clean up |
| `get_frame_time()` / `get_time()` | Seconds the last frame took (`f32`) / since start (`f64`) |

`update` is shorthand for `reset_frame_allocator`, `calculate_frame_time`, `update_audio` and `process_events`. Call them yourself for more control, and test `close_window_requested()`.

**`Init_Options`:** `window_mode` (`.Windowed`, `.Windowed_Resizable`, `.Borderless_Fullscreen`), `monitor`, `anti_alias`, `disable_auto_scale_hint`, `depth_test`, `depth_range_min`/`depth_range_max`.

```odin
k2.init(1280, 720, "Game", options = { window_mode = .Windowed_Resizable, anti_alias = true })
```

| Window procedure | Job |
|------------------|-----|
| `get_screen_width/height/size`, `set_screen_size(w, h)` | Drawable area |
| `set_window_title`, `set_window_position`, `get_window_position` | Position does nothing on web. Get returns `{}` on web and Wayland |
| `set_window_mode`, `get_window_mode` | Switch modes |
| `get_window_scale()` | OS DPI scale (1.5 is 150%). **No automatic scaling:** multiply sizes yourself and use it as camera zoom |
| `get_monitors()` | Callable before `init`. Slice and names are allocated: free them |
| `get_window_monitor`, `set_window_monitor(id)` | Which monitor |
| `set_window_icon(image)` | Image is copied. Returns `bool` |

## Input

Names end in `_went_down`, `_went_up` or `_is_held`. All are filled by `process_events`.

```odin
if k2.key_is_held(.Right) { player.x += 300 * k2.get_frame_time() }
if k2.key_went_down(.Space) { jump() }
```

| Device | Procedures |
|--------|------------|
| Keyboard | `key_went_down(key, allow_repeat := false)`, `key_went_up`, `key_is_held`, `get_typed_runes` (for text fields), `get_held_modifiers` |
| Mouse | `mouse_button_went_down/up/is_held(.Left/.Right/.Middle)`, `get_mouse_position`, `get_mouse_delta`, `get_mouse_wheel_delta`, `get_mouse_wheel_delta_horizontal`, `set_mouse_locked`, `is_mouse_locked` |
| Touch | `get_touches` returns `Touch{id, position, delta, went_down, went_up, cancelled}`. Identify fingers by `id`. Max 11 |
| Gamepad | `is_gamepad_active(i)`, `gamepad_button_went_down/up/is_held(i, button)`, `get_gamepad_axis(i, axis)`, `set_gamepad_vibration(i, left, right)`. 4 pads (`MAX_GAMEPADS`) |

- **Modifiers:** `get_held_modifiers() == { .Control, .Shift }` is true only for exactly those (left or right)
- **Mouse lock** can be undone by the OS, so check `is_mouse_locked()`. Use `get_mouse_delta` while locked. It does not hide the cursor
- **Touch emulation:** `set_mouse_touch_emulation(.Touch_To_Mouse)` is the default. Use `.None` if you handle both yourself, or `.Mouse_To_Touch` to test touch on desktop
- **Gamepad:** sticks are -1 to 1, triggers 0 to 1. Face buttons are positional: `.Right_Face_Down` is A on Xbox and X on PlayStation. Others: `.Left_Face_*` (d-pad), `.Left/Right_Shoulder`, `.Left/Right_Trigger`, `.Left/Right_Stick_Press`, `.Middle_Face_Left/Middle/Right`. Axes: `.Left_Stick_X/Y`, `.Right_Stick_X/Y`, `.Left_Trigger`, `.Right_Trigger`
- **Keys:** `Keyboard_Key` has `.A`-`.Z`, `.N0`-`.N9`, arrows, `.Space`, `.Enter`, `.Escape`, `.Tab`, `.F1`-`.F12`, `.Left_Shift` and the other modifiers, numpad `.NP_*`, punctuation

**Events:** `get_events()` lists everything that happened, including things polling can't see:

```odin
for event in k2.get_events() {
	#partial switch e in event {
	case k2.Event_Screen_Resize: relayout(e.width, e.height)
	case k2.Event_Window_Unfocused: pause_game()
	}
}
```

Types: `Event_Key_Went_Down/Up/Repeat`, `Event_Typed_Rune`, `Event_Mouse_Move/Wheel/Wheel_Horizontal/Teleported`, `Event_Mouse_Button_Went_Down/Up`, `Event_Gamepad_Button_Went_Down/Up`, `Event_Touch_Went_Down/Moved/Went_Up/Cancelled`, `Event_Screen_Resize`, `Event_Window_Focused/Unfocused/Scale_Changed`, `Event_Close_Window_Requested`. Stick and trigger movement is not an event.

## Drawing

| Procedure | Notes |
|-----------|-------|
| `draw_rect(rect, color, origin, rotation)` | `origin` is the rotation pivot and shifts the rect. `{w/2, h/2}` rotates around the center |
| `draw_rect_vec(pos, size, color, ...)` | Same, from position and size |
| `draw_rect_outline(rect, thickness, color)` | |
| `draw_circle(center, radius, color, segments := 16)` | Made of slices, raise `segments` for big circles |
| `draw_circle_outline(center, radius, thickness, color, segments)` | |
| `draw_line(start, end, thickness, color)` | |
| `draw_triangle([3]Vec2, color)` | Winding does not matter |
| `draw_texture(tex, pos, origin, rotation, tint := WHITE)` | `tint` multiplies colors |
| `draw_texture_rect(tex, source, pos, ...)` | Draw the `source` region (texture pixels). Negative `w`/`h` flips |
| `draw_texture_fit(tex, source, dest, ...)` | Stretch `source` into `dest` |
| `draw_text(text, pos, size, color, font, origin, rotation)` | `pos` is top-left. Stays sharp with a camera |
| `measure_text(text, size, font)` | Returns `Vec2` |

```odin
middle := k2.rect_middle(k2.get_texture_rect(tex))
k2.draw_texture(tex, pos + middle, middle, rot)        // rotate around the center

size := k2.measure_text("Game Over", 64)
k2.draw_text("Game Over", (k2.get_screen_size() - size) / 2, 64, k2.WHITE)
```

**Colors:** `WHITE BLACK BLANK RED GREEN BLUE ORANGE PURPLE MAGENTA YELLOW BROWN` with `LIGHT_`/`DARK_` variants, `LIGHT_GRAY GRAY DARK_GRAY`, and Raylib-style `RL_*`. `color_alpha(c, a)` replaces alpha.

**Batching:** draws are collected and sent on `present`, `clear`, a full vertex buffer, or when you destroy a resource in use (or call `draw_current_batch`). These start a **new draw call**: a different texture, `set_shader`, `set_blend_mode`, `set_scissor_rect`, `set_camera`, `set_render_texture`. `set_z` does not. Use an atlas and group draws by texture.

## Textures and images

A `Texture` (`handle`, `width`, `height`) is on the GPU. An `Image` (`pixels []Color`, `width`, `height`) is in RAM, always RGBA8 with straight alpha.

| Procedure | Job |
|-----------|-----|
| `load_texture_from_file(name, options)` | PNG, BMP, TGA. Baseline PNG only, **no progressive PNG** |
| `load_texture_from_bytes(bytes, options)` | Encoded file in memory, e.g. `#load("a.png")`. Use on web |
| `load_texture_from_bytes_raw(bytes, w, h, format)` | Headerless pixels |
| `load_texture_from_image(image)` | From an `Image` |
| `create_texture(w, h, format)` | Empty texture |
| `load_image_from_file/bytes`, `destroy_image` | Images |
| `update_texture(tex, bytes, rect, pitch := 0)` | Overwrite a region |
| `get_texture_rect(tex)` | `{0, 0, w, h}` |
| `set_texture_filter(tex, .Point/.Linear)` | Pixelated or smooth. `set_texture_filter_ex` splits down/up/mip |
| `destroy_texture(tex)` | |

`options` is `{ .Premultiply_Alpha }` for use with `set_blend_mode(.Premultiplied_Alpha)`. `Pixel_Format`: `RGBA_8_Norm`, `RG_8_Norm`, `R_8_Norm`, `R_8_UInt`, `RGBA_32_Float`, `RGB_32_Float`, `RG_32_Float`, `R_32_Float`. `pixel_format_size(f)` gives bytes per pixel.

**Render textures** let you draw into a texture. `create_render_texture(w, h)`, `set_render_texture(rt)` (`nil` returns to the screen), `destroy_render_texture(rt)`. Use `rt.texture` like any texture. `clear` clears the current target.

```odin
k2.set_render_texture(minimap)
k2.clear(k2.DARK_GREEN)
draw_world_small()
k2.set_render_texture(nil)
```

## Fonts

`FONT_DEFAULT` is built-in Roboto. Pass a `Font` as the `font` argument to `draw_text`/`measure_text`.

| | Static | Dynamic |
|--|--------|---------|
| Load | `load_static_font_from_file/bytes(data, font_size, codepoints)` | `load_dynamic_font_from_file/bytes(data)` |
| How | Baked once at one size. ASCII unless you pass `codepoints` | Shared atlas grows as you draw. Any size |

The shared atlas maxes at 4096×4096. When full, the least recently used 50% of glyphs are dropped. `Font_Options`: `premultiply_alpha`, `filter`, `font_index` (for `.ttc`). A failed load draws with the default font. `destroy_font(font)`.

## Audio

Mixer runs at 44100 Hz. `update` runs `update_audio`, which must run once per frame.

| Type | Meaning |
|------|---------|
| `Audio_Clip` | Fully loaded audio (WAV, OGG). For effects |
| `Audio_Stream` | OGG decoded bit by bit. For music |
| `Sound` | Something playing now. Returned by `play_audio_*` |

```odin
sfx := k2.load_audio_clip_from_file("jump.wav")
k2.play_audio_clip(sfx, volume = 0.8, pitch = 1.2)

music := k2.load_audio_stream_from_file("music.ogg")
song := k2.play_audio_stream(music, loop = true)
// every frame:
k2.update_audio_stream(music)
```

- **Clips:** `load_audio_clip_from_file/bytes` (bytes must be the **whole file**), `load_audio_clip_from_bytes_raw(bytes, format, sample_rate, channels)`, `destroy_audio_clip`, `get_num_sounds_playing_clip`
- **Streams:** `load_audio_stream_from_file/bytes` (bytes are **not copied**, keep them alive), `update_audio_stream` every frame (safe on one thread per stream), `destroy_audio_stream`. A stream plays one sound at a time: playing again returns the existing sound and ignores new settings. `stop_sound` first to restart
- **`play_audio_*` args:** `volume` (0 to 1), `pan` (-1 to 1), `pitch` (0.01 and up), `loop`, `bus`. Looping with a discarded `Sound` can't be stopped
- **Sound control:** `stop_sound`, `set_sound_paused`, `sound_is_playing`, `sound_is_valid`, `set_sound_volume/pan/pitch/loop/time/bus`, `get_sound_time`, `get_sound_length`
- **Buses** group sounds: `create_audio_bus`, `destroy_audio_bus`, `set_audio_bus_volume/pan`, `set_audio_bus_effect(bus, proc, user_data)`. `AUDIO_BUS_MASTER` is the default, so `set_audio_bus_volume(k2.AUDIO_BUS_MASTER, v)` sets master volume
- **Effects:** `proc(samples: [][2]Audio_Sample, user_data: rawptr)` edits the bus mix in place. State must live in `user_data`

## Camera

```odin
Camera :: struct { target, offset: Vec2, rotation, zoom: f32, flip_y: bool }
```

`set_camera(cam)` applies to all later draws. `set_camera(nil)` returns to none.

- `target` is the world point at the top-left of the screen. Set `offset` to half the screen size to center it
- `zoom` bigger is closer. 0 counts as 1. For a fixed visible height use `f32(k2.get_screen_height()) / wanted_height`
- `flip_y` makes the origin bottom-left, Y up and rotation reversed. `Rect`s, textures and text then anchor at the bottom-left. This suits Box2D. The `rect_top_*`, `rect_bottom_*` and `rect_cut_*` helpers still assume top-left, so use `flip_y` only for the world camera and draw UI without it

```odin
camera.target = player.pos
camera.offset = k2.get_screen_size() / 2
k2.set_camera(camera); draw_world(); k2.set_camera(nil); draw_ui()

world_mouse := k2.screen_to_camera(k2.get_mouse_position(), camera)
```

`screen_to_camera` and `camera_to_screen` convert points. `camera_view_matrix` and `camera_inverse_view_matrix` return the `Mat4`s behind them.

## Shaders

Source files use the shading language of your render backend (D3D11, OpenGL or WebGL). There is no cross-API translation yet.

| Procedure | Job |
|-----------|-----|
| `load_shader_from_file(vert, frag, layout_formats)` | Pass the same file twice if both stages are in it |
| `load_shader_from_bytes(vert, frag, layout_formats)` | From memory |
| `set_shader(shader)` / `set_shader(nil)` | Use / back to default. `get_default_shader()` |
| `set_shader_constant(shader, loc, val)` | `loc := shader.constant_lookup["name"]` |
| `set_shader_texture(shader, bindpoint, tex)` | Extra textures. `shader.texture_lookup["name"]` |
| `override_shader_input(shader, index, val)` | Per-object vertex input data |
| `destroy_shader` | |

A failed load makes `set_shader` do nothing. Default inputs are position, texcoord and color. `layout_formats` can usually stay default.

## Math helpers

| Group | Procedures |
|-------|-----------|
| Overlap | `rect_overlapping(a, b)`, `rect_overlap(a, b) -> (Rect, bool)`, `point_in_rect(p, r)` |
| Points | `rect_middle` (also `rect_center`/`rect_centre`), `rect_top_left/middle/right`, `rect_bottom_left/middle/right`, `rect_from_pos_size` |
| Size | `rect_shrink(r, x, y)`, `rect_expand(r, x, y)`: each edge moves, so width changes by `2x` |
| Cut | `rect_cut_top/bottom/left/right(&r, size, margin)` returns the strip and shrinks `r` by `size + margin` |
| Split | `rect_split_left/right/top/bottom(r, size, margin)` returns two new rects without modifying `r` |
| Other | `rotate(v, radians)` around `(0, 0)`, `color_alpha(c, a)` |

```odin
screen := k2.Rect { 0, 0, 800, 600 }
header  := k2.rect_cut_top(&screen, 60, 8)   // {0, 0, 800, 60}, screen is now {0, 68, 800, 532}
sidebar := k2.rect_cut_left(&screen, 200, 8)
```

## Misc

- **Blend:** `set_blend_mode(.Alpha | .Premultiplied_Alpha | .Additive)`. Default `.Alpha`
- **Scissor:** `set_scissor_rect(rect)` clips to a screen rect, `nil` turns it off
- **Depth:** set `depth_test` in `Init_Options`, then `set_z(z)` (higher is in front, `get_z()` reads it). Default range -1 to 1. Without `depth_test` it has no effect
- **Cursors:** `set_cursor(.Hand)` with `Default Text Hand Crosshair Wait Progress Resize_EW Resize_NS Resize_NESW Resize_NWSE Move Not_Allowed` (missing ones fall back, e.g. macOS lacks `Wait` and diagonal resize). `create_custom_cursor(image, hotspot)`, `destroy_custom_cursor`. `set_cursor_hidden(bool)` and `is_cursor_hidden()`. The OS can unhide it, so check
- **URLs:** `open_url(url)` needs `https://`, `http://` or `file:///` and no spaces. Returns `.None`, `.Invalid_URL` or `.Failed_To_Open`
- **Icon and logo:** `make_karl2d_icon(size)` (multiple of 16), `make_karl2d_logo(width)` (multiple of 30). Free with `destroy_image`
- **Hot reload:** keep the pointer from `init` and call `set_internal_state(ptr)` after reloading the library
- **Experimental UI:** `ui_button(rect, text) -> bool`, `ui_button_width(text, height)`. Copy it into your code rather than depend on it

## Web builds

The browser calls your code once per redraw, so split `main` into `init` and `step`:

```odin
main :: proc() { init(); for step() {}; shutdown() }

init :: proc() { k2.init(1280, 720, "Game") }

step :: proc() -> bool {
	if !k2.update() { return false }
	k2.clear(k2.LIGHT_BLUE)
	k2.present()
	return true
}

shutdown :: proc() { k2.shutdown() }
```

Build with `odin run karl2d/build_web -- .` (add `-debug` after `--` for symbols, `-o:speed` or `-o:size` to optimize). Output goes to `bin/web`. If the page is blank, serve it with `python -m http.server` from that folder. On Linux and Mac you may need an `lld` package for `wasm-ld`.

There is no file system on web, so use `_from_bytes` with `#load`:

```odin
k2.load_texture_from_bytes(#load("image.png"))
```

To share code, define `load_texture :: proc($name: string)` twice: once in a file starting `#+build !js` (calls `load_texture_from_file(name)`), once in a file starting `#+build js` (calls `load_texture_from_bytes(#load(name))`). The `$` makes `name` a compile-time constant, which `#load` needs.

## Platform notes

Backends: D3D11, OpenGL and WebGL. On Windows pick with `-define:KARL2D_RENDER_BACKEND=gl` or `d3d11`. On Linux Karl2D tries Wayland, then X11 at runtime. Override with `KARL2D_LINUX_WINDOWING=x11` or `wayland`.