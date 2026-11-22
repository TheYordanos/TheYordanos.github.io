---
title: Camera
description: Moving, zooming and rotating the view, flipping Y, and converting between screen and world.
project: Karl2D
order: 8
updated: 2026-11-22
---
A camera changes how everything you draw is placed on the screen. Set one with `set_camera` and every draw after that uses it, until you change it again.

```odin
set_camera :: proc(camera: Maybe(Camera))
```

Pass `nil` to go back to the default camera (no transform).

## Camera

```odin
Camera :: struct {
	target:   Vec2,
	offset:   Vec2,
	rotation: f32,
	zoom:     f32,
	flip_y:   bool,
}
```

| Field | Meaning |
|-------|---------|
| `target` | The world position the camera looks at. By default it ends up in the **top-left** corner of the screen |
| `offset` | Moves where `target` appears on screen. Half the screen size puts the target in the middle |
| `rotation` | Radians |
| `zoom` | Bigger means more zoomed in. A zoom of 0 is treated as 1, so an empty camera draws at normal size |
| `flip_y` | Flips the Y axis, see below |

### A camera that follows the player

```odin
camera := k2.Camera {
	zoom = 2,
}

for k2.update() {
	camera.target = player.pos
	camera.offset = k2.get_screen_size() / 2

	k2.clear(k2.DARK_GRAY)

	k2.set_camera(camera)
	draw_world()
	k2.set_camera(nil)

	draw_ui() // not affected by the camera
	k2.present()
}
```

Drawing the UI with `set_camera(nil)` keeps it fixed on screen.

### Fitting a fixed height

To always show the same number of world pixels vertically, set the zoom like this:

```odin
camera.zoom = f32(k2.get_screen_height()) / wanted_pixel_height
```

## Converting points

```odin
screen_to_camera :: proc(pos: Vec2, camera: Camera) -> Vec2
camera_to_screen :: proc(pos: Vec2, camera: Camera) -> Vec2
```

`screen_to_camera` turns a point on the screen into the camera's world coordinates. The classic use is the mouse:

```odin
world_mouse := k2.screen_to_camera(k2.get_mouse_position(), camera)
```

`camera_to_screen` goes the other way. Use it to place a UI marker over something in the world.

## View matrices

`camera_view_matrix(camera)` returns the matrix used by the two procedures above, as a `Mat4`. `camera_inverse_view_matrix(camera)` returns its inverse, which undoes the camera. Only the upper-left 3×3 part is used. You only need these for your own math or shaders.

A view matrix is the camera's world transform, inverted: instead of bringing the camera to the world, it brings the world in front of the camera. Karl2D builds it directly in backwards order (inverse offset, inverse scale, inverse rotation, inverse target) instead of inverting a matrix, which is faster.

## Flipping Y

By default the origin is the top-left corner and Y grows **down**. With `flip_y = true`:

- The origin is the bottom-left of the screen and Y grows **up**
- Rotation goes the other way
- A `Rect` has its `(x, y)` at its **bottom-left** corner
- Textures are drawn from their bottom-left corner
- Text blocks have their origin at the bottom-left

This makes Karl2D match libraries like Box2D, where Y is up, so you do not need to convert between gameplay and drawing code.

```odin
world_camera := k2.Camera {
	zoom = 20, // 20 pixels per meter
	flip_y = true,
}
```

> **Caveat:** the `rect_top_*` and `rect_bottom_*` helpers and the rectangle cut procedures still assume `(x, y)` is the top-left corner. Those are mostly used for screen-space UI. Use `flip_y` only for the world camera, and draw UI with no camera or a non-flipped one.
