---
title: Window and frame
description: Starting Karl2D, the main loop, window modes, monitors and frame timing.
project: Karl2D
order: 2
updated: 2026-11-22
---
## init

```odin
init :: proc(
	screen_width: int,
	screen_height: int,
	window_title: string,
	options := Init_Options {},
	allocator := context.allocator,
	loc := #caller_location,
	audio_thread_logger := context.logger,
) -> ^State
```

Opens a window, sets up the renderer and starts the audio systems.

`screen_width` and `screen_height` are the size of the drawable area. The window itself may be a bit larger because of borders and the title bar. The real size is also multiplied by the OS scaling setting, see [Window scale](#window-scale).

`allocator` is used for everything that lives longer than one frame. Single-frame allocations use an internal frame allocator that is emptied by `update`.

`audio_thread_logger` is kept for the audio thread, so use a thread safe logger. The file and console loggers in Odin are.

The return value is a pointer to Karl2D's internal state. You can ignore it unless you do hot reload, see [Misc](karl2d_misc.html#hot-reload).

### Init_Options

| Field | Meaning |
|-------|---------|
| `window_mode` | `.Windowed`, `.Windowed_Resizable` or `.Borderless_Fullscreen` |
| `monitor` | Which monitor to start on. Zero means the default one |
| `anti_alias` | Request anti-aliasing. On most systems this is 4x MSAA |
| `disable_auto_scale_hint` | A hint to skip OS scaling. Works on some platforms (Windows), not on others (Linux with Wayland) |
| `depth_test` | Sort draws by the value from `set_z` |
| `depth_range_min`, `depth_range_max` | The z range. Both zero gives the default of -1 to 1 |

```odin
k2.init(1280, 720, "My game", options = {
	window_mode = .Windowed_Resizable,
	anti_alias = true,
})
```

With `.Borderless_Fullscreen` the width and height arguments are ignored and the full desktop resolution is used.

When the monitor is set and the mode is not fullscreen, the window is centered on that monitor.

## The main loop

```odin
for k2.update() {
	k2.clear(k2.BLACK)
	// draw things
	k2.present()
}
k2.shutdown()
```

### update

`update` should run early in the frame so that input and frame times are fresh. It returns `false` when the player has asked to close the window. You decide what to do with that. A game can show a "Really quit?" screen instead of leaving.

### clear

`clear(color)` fills the screen with a color. If you have set a render texture, that texture is cleared instead.

### present

`present` shows what you drew. Drawing goes to an invisible backbuffer, and `present` flips it to the screen so no half-drawn frame is ever seen. On the web the flip happens automatically, but call `present` anyway because it also sends the remaining draw work to the GPU.

### shutdown

Closes the window and cleans up the internal state.

## Doing the frame by hand

`update` is a shortcut for a handful of smaller procedures. If you need more control, call them yourself in this order:

```odin
for {
	k2.reset_frame_allocator()
	k2.calculate_frame_time()
	k2.update_audio()
	k2.process_events()

	k2.clear(k2.BLUE)
	k2.present()

	if k2.close_window_requested() {
		break
	}
}
```

| Procedure | Job |
|-----------|-----|
| `reset_frame_allocator` | Empties the frame allocator |
| `calculate_frame_time` | Updates the values behind `get_frame_time` and `get_time` |
| `update_audio` | Runs the mixer where there is no audio thread, and removes finished sounds. Must run once per frame |
| `process_events` | Reads keyboard, mouse, gamepad and window events from the OS |
| `close_window_requested` | `true` if the player pressed the close button or used a shortcut like ALT+F4 |

## Time

```odin
dt := k2.get_frame_time() // f32, seconds the previous frame took
t  := k2.get_time()       // f64, seconds since the game started

player.x += speed * dt
```

Both are updated when `calculate_frame_time` runs, which `update` does for you. `get_time` is an `f64` so it stays precise in a game that runs for a long time.

## Window size

| Procedure | Result |
|-----------|--------|
| `get_screen_width()` | Width of the drawable area, `int` |
| `get_screen_height()` | Height of the drawable area, `int` |
| `get_screen_size()` | Both as a `Vec2` |
| `set_screen_size(w, h)` | Resize the drawable area |

A user cannot resize a `.Windowed` window, but `set_screen_size` can. Use `.Windowed_Resizable` if you want the player to drag the edges. When the size changes an `Event_Screen_Resize` is sent, see [Input](karl2d_input.html#events).

## Window scale

```odin
get_window_scale :: proc() -> f32
```

Returns the OS scaling, where 1 means 100% and 1.5 means 150%. Karl2D does **not** scale anything automatically. If you want a bigger window on a scaled display, multiply your size by the scale and pass it to `set_screen_size`. Then set a camera zoom equal to the scale so that things keep the same apparent size:

```odin
scale := k2.get_window_scale()
k2.set_screen_size(int(1280 * scale), int(720 * scale))

camera := k2.Camera { zoom = scale }
```

An `Event_Window_Scale_Changed` event tells you when the scale changes.

## Title and position

```odin
k2.set_window_title("Level 2")
k2.set_window_position(100, 100)
pos := k2.get_window_position()
```

`set_window_position` does nothing on web. `get_window_position` returns `{}` on web and on Wayland.

## Window modes

`set_window_mode` switches between `.Windowed`, `.Windowed_Resizable` and `.Borderless_Fullscreen`. `get_window_mode` returns the latest mode, whether it was set by `init` or by `set_window_mode`.

```odin
if k2.key_went_down(.F11) {
	if k2.get_window_mode() == .Borderless_Fullscreen {
		k2.set_window_mode(.Windowed_Resizable)
	} else {
		k2.set_window_mode(.Borderless_Fullscreen)
	}
}
```

## Monitors

`get_monitors` lists the connected monitors. It is the one procedure that is safe to call before `init`, which is handy for building a "start on this monitor" option.

```odin
monitors := k2.get_monitors()
defer {
	for m in monitors {
		delete(m.name)
	}
	delete(monitors)
}
```

Both the slice and each `name` are allocated with the `allocator` argument (the default is `context.allocator`), so free them when you are done.

`Monitor_Info` has these fields:

| Field | Meaning |
|-------|---------|
| `id` | A `Monitor_Id` for `set_window_monitor` and `Init_Options` |
| `name` | The monitor's name (allocated) |
| `position` | Window-space position. Top-left is `{0, 0}` and Y grows down on most platforms. On Mac the position is measured from the bottom-left and Y grows up |
| `size` | Resolution in pixels |
| `physical_size` | Size in millimeters |
| `scale` | OS scale of the monitor |
| `primary` | `true` for the primary monitor |

`get_window_monitor` returns the monitor the window is on. If it spans several, the one it overlaps most wins. `set_window_monitor(id)` moves the window there. A fullscreen window is moved and resized properly. `MONITOR_NONE` is the zero value.

## Window icon

```odin
set_window_icon :: proc(image: Image) -> bool
```

Sets the icon in the title bar and program switcher (on web, the tab icon). The image data is copied, so you can destroy the image straight afterwards. Returns `true` if the icon was set. By default Karl2D shows its own icon, see [Misc](karl2d_misc.html#built-in-images).

```odin
icon := k2.load_image_from_file("icon.png")
k2.set_window_icon(icon)
k2.destroy_image(icon)
```
