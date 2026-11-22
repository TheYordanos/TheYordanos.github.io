---
title: Overview
description: Make 2D games in Odin with Karl2D. What it is, how to start, and how the pieces fit together.
project: Karl2D
order: 1
updated: 2026-11-22
---

- Author: [Karl Zylinkski](https://zylinski.se/)
- Site: [karl2d.com](https://karl2d.com/)

Karl2D is a beginner friendly 2D game library for the [Odin programming language](https://odin-lang.org). It keeps its dependencies low: the code goes all the way down to the OS and rendering APIs. You can ship desktop games and web games, and the web builds do not need emscripten.

It handles the things most 2D games need:

- Windows, Linux, Mac and Web
- Textures, shapes and text
- Cameras that move, rotate and zoom the view
- Audio clips, music streaming, buses and effects
- Keyboard, mouse, touch and gamepad input
- Render textures and custom shaders

These docs follow the API overview file, `karl2d.doc.odin`. Every procedure mentioned is called as `k2.name`.

## Getting started

1. Install the Odin compiler from [odin-lang.org](https://odin-lang.org).
2. Create a folder for your game.
3. Put the contents of the Karl2D repository in a subfolder called `karl2d`.
4. Create `game.odin` in your game folder and paste this in:

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

5. Run it from the game folder with `odin run .` (the period matters).

A window opens that says "Hellope!".

## The shape of a game

Every Karl2D game has the same skeleton:

| Step | Procedure | What it does |
|------|-----------|--------------|
| Start | `init` | Opens the window, starts the renderer and the audio |
| Each frame | `update` | Reads input, updates frame time, runs audio. Returns `false` when the player tries to close the window |
| Each frame | `clear`, `draw_*` | Your drawing |
| Each frame | `present` | Shows the finished frame |
| End | `shutdown` | Closes the window and cleans up |

`init` must run before almost everything else. The one exception is `get_monitors`, which can be called before `init`.

## Conventions

A few rules apply across the whole API, so they are worth knowing up front.

**Units.** Positions and sizes are in pixels. Rotation is in radians. Time is in seconds.

**Types.** `Vec2` is `[2]f32`. `Color` is `[4]u8` (red, green, blue, alpha, 0 to 255). `Rect` is a struct with `x`, `y`, `w` and `h`.

**Coordinates.** The origin is the top-left corner of the window and Y grows downwards. A camera can flip this, see [Camera](karl2d_camera.html).

**Loading returns two values.** Procedures that load or create something return the thing and a `bool` for success. Handling the `bool` is optional, because failures are logged too. A failed load still gives you a value you can pass around safely, it just draws or plays nothing.

```odin
tex, ok := k2.load_texture_from_file("player.png")
if !ok {
	// handle it, or ignore it: the log already has the error
}

// or just ignore the second value
tex2 := k2.load_texture_from_file("enemy.png")
```

**Handles.** Textures, sounds, fonts and similar resources are small handle values. Copy them freely. A `Sound` handle stays safe to use after the sound has finished: the procedures just do nothing.

**Per-frame slices.** `get_events`, `get_typed_runes` and `get_touches` return slices that are only valid for the current frame. Clone them with `slice.clone` if you need to keep them.

**`Maybe` and `nil`.** Settings such as the camera, shader, render texture and scissor rectangle take a `Maybe(...)`. Pass a value to turn it on and `nil` to go back to the default.

```odin
k2.set_camera(my_camera)
// ... draw the world ...
k2.set_camera(nil)
// ... draw the UI ...
```

## Making a web build

A browser cannot run a blocking loop like `for k2.update() {}`. Instead it calls your code once each time it wants to redraw. So split the game into `init`, `step` and `shutdown`:

```odin
package hello_world

import k2 "karl2d"

main :: proc() {
	init()
	for step() {}
	shutdown()
}

init :: proc() {
	k2.init(1280, 720, "Greetings from Karl2D!")
}

step :: proc() -> bool {
	if !k2.update() {
		return false
	}

	k2.clear(k2.LIGHT_BLUE)
	k2.draw_text("Hellope!", {50, 50}, 100, k2.DARK_BLUE)
	k2.present()

	return true
}

shutdown :: proc() {
	k2.shutdown()
}
```

`main` is still used on desktop. The web build calls `init` and `step` directly.

Build it with the `build_web` tool that comes with Karl2D. Run this in your game folder (note the double dash and the period):

```
odin run karl2d/build_web -- .
```

The result ends up in `bin/web`. Open `index.html` from there.

> **Note:** If the page is blank, the browser console may mention a "cross site policy" error. Serve the folder with `python -m http.server` from `bin/web` instead of opening the file directly. On Linux and Mac you may also need a package that provides the `wasm-ld` linker (often called `lld`). Add `-debug` after the `--` for better debug symbols in the browser.

There is no file system on the web, so `load_texture_from_file` does not work there. Embed the file into the program with `#load` and use the `_from_bytes` loaders:

```odin
k2.load_texture_from_bytes(#load("image.png"))
```

To use files on desktop and embedded bytes on web, hide the difference behind one procedure. Put the desktop version in a file that starts with `#+build !js`:

```odin
load_texture :: proc($name: string) -> k2.Texture {
	return k2.load_texture_from_file(name)
}
```

and the web version in a file that starts with `#+build js`:

```odin
load_texture :: proc($name: string) -> k2.Texture {
	return k2.load_texture_from_bytes(#load(name))
}
```

The `$` on `name` makes it a compile-time constant, which `#load` requires.

## Where to go next

- [Window and frame](karl2d_window.html): `init` options, the main loop, window modes and monitors
- [Input](karl2d_input.html): keyboard, mouse, touch and gamepads
- [Drawing](karl2d_drawing.html): shapes, textures and text
- [Textures and images](karl2d_textures.html): loading, filtering and render textures
- [Fonts](karl2d_fonts.html): static and dynamic fonts
- [Audio](karl2d_audio.html): clips, music, buses and effects
- [Camera](karl2d_camera.html): moving the view and converting coordinates
- [Shaders](karl2d_shaders.html): custom shaders and constants
- [Math helpers](karl2d_math.html): rectangles, colors and rotation
- [Misc](karl2d_misc.html): blend modes, scissor, depth, hot reload, cursors and more
