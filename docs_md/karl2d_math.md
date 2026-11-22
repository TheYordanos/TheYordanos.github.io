---
title: Math helpers
description: Rectangle helpers, cutting and splitting rectangles for layouts, and vector rotation.
project: Karl2D
order: 10
updated: 2026-11-22
---
Karl2D has a small set of math helpers. Most of them work on `Rect`, which is `{x, y, w, h}` with `(x, y)` in the top-left corner.

## Overlap and containment

| Procedure | Result |
|-----------|--------|
| `rect_overlapping(a, b)` | `true` if the rectangles overlap |
| `rect_overlap(a, b)` | `(Rect, bool)`: the overlapping area, and `false` if there is none |
| `point_in_rect(point, rect)` | `true` if the point is inside |

```odin
button := k2.Rect { 100, 100, 200, 50 }

if k2.point_in_rect(k2.get_mouse_position(), button) {
	k2.draw_rect(button, k2.LIGHT_BLUE)
}
```

## Points on a rectangle

| Procedure | Result |
|-----------|--------|
| `rect_middle(r)` | The middle. Also named `rect_center` and `rect_centre` |
| `rect_top_left(r)`, `rect_top_middle(r)`, `rect_top_right(r)` | Top edge points |
| `rect_bottom_left(r)`, `rect_bottom_middle(r)`, `rect_bottom_right(r)` | Bottom edge points |
| `rect_from_pos_size(pos, size)` | Build a `Rect` from a `Vec2` position and a `Vec2` size |

`rect_middle` is handy as the `origin` when you want something to rotate around its center.

## Growing and shrinking

```odin
rect_shrink :: proc(r: Rect, x: f32, y: f32) -> Rect
rect_expand :: proc(r: Rect, x: f32, y: f32) -> Rect
```

Each edge moves by `x` (left and right) or `y` (top and bottom), so the width changes by `2 * x` and the height by `2 * y`. The center stays where it is. Use `rect_shrink` for padding.

```odin
panel := k2.Rect { 0, 0, 300, 200 }
inner := k2.rect_shrink(panel, 10, 10) // {10, 10, 280, 180}
```

## Cutting rectangles

The cut procedures take a **pointer** to a rectangle. They remove a strip from one side, shrink the original and return the strip. That is perfect for laying out UI step by step:

```odin
rect_cut_top    :: proc(r: ^Rect, h: f32, m: f32) -> Rect
rect_cut_bottom :: proc(r: ^Rect, h: f32, m: f32) -> Rect
rect_cut_left   :: proc(r: ^Rect, w: f32, m: f32) -> Rect
rect_cut_right  :: proc(r: ^Rect, w: f32, m: f32) -> Rect
```

`h` or `w` is the size of the strip. `m` is a margin that is skipped between the strip and what is left. So `r` shrinks by the size plus the margin.

```odin
screen := k2.Rect { 0, 0, 800, 600 }

header := k2.rect_cut_top(&screen, 60, 8)   // {0, 0, 800, 60}
                                           // screen is now {0, 68, 800, 532}
footer := k2.rect_cut_bottom(&screen, 40, 8)
sidebar := k2.rect_cut_left(&screen, 200, 8)
// `screen` is now the content area that remains

k2.draw_rect(header, k2.DARK_BLUE)
k2.draw_rect(sidebar, k2.GRAY)
```

## Splitting rectangles

The split procedures do not modify the rectangle. They return two new ones.

```odin
rect_split_left   :: proc(r: Rect, x: f32, m: f32) -> (left: Rect, right: Rect)
rect_split_right  :: proc(r: Rect, x: f32, m: f32) -> (left: Rect, right: Rect)
rect_split_top    :: proc(r: Rect, y: f32, m: f32) -> (top: Rect, bottom: Rect)
rect_split_bottom :: proc(r: Rect, y: f32, m: f32) -> (top: Rect, bottom: Rect)
```

- `rect_split_left(r, x, m)`: the left part is `x` wide and the right part starts at `x + m`
- `rect_split_right(r, x, m)`: the right part is `x` wide, measured from the right edge, and the left part gets smaller by `x + m`
- `rect_split_top` and `rect_split_bottom` work the same way vertically

```odin
list, details := k2.rect_split_left(screen, 250, 10)
```

## Colors

`color_alpha(c, a)` returns color `c` with its alpha replaced by `a`:

```odin
shadow := k2.color_alpha(k2.BLACK, 100)
```

## Rotating vectors

```odin
rotate :: proc(v: Vec2, angle_radians: f32) -> Vec2
```

Rotates `v` around `(0, 0)`. To rotate around another point, subtract that point, rotate, and add it back:

```odin
rotated := k2.rotate(p - pivot, angle) + pivot
```

## Types

| Type | Definition |
|------|------------|
| `Vec2`, `Vec3`, `Vec4` | `[2]f32`, `[3]f32`, `[4]f32` |
| `Mat4` | `matrix[4,4]f32` |
| `Rect` | `struct { x, y, w, h: f32 }` |
| `Color` | `[4]u8` |

Because vectors are Odin arrays, you can add, subtract and multiply them directly: `a + b`, `v * 2`.

## Flipped cameras

The corner and cut helpers assume `(x, y)` is the top-left. If you use a camera with `flip_y`, see the caveat in [Camera](karl2d_camera.html#flipping-y).
