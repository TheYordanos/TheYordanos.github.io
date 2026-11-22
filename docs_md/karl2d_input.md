---
title: Input
description: Keyboard, mouse, touch and gamepad input, plus the raw event list.
project: Karl2D
order: 3
updated: 2026-11-22
---
Input is read from state that `process_events` fills in. `update` calls it, so in a normal game you can query input anywhere after `update`.

Most input procedures answer one of three questions:

| Name pattern | Meaning |
|--------------|---------|
| `..._went_down` | Became pressed between the previous and the current frame |
| `..._went_up` | Was released between the previous and the current frame |
| `..._is_held` | Is down right now |

## Keyboard

```odin
if k2.key_is_held(.Right) {
	player.x += 300 * k2.get_frame_time()
}

if k2.key_went_down(.Space) {
	jump()
}
```

| Procedure | Result |
|-----------|--------|
| `key_went_down(key, allow_repeat := false)` | `true` on the frame a key goes down |
| `key_went_up(key)` | `true` on the frame a key is released |
| `key_is_held(key)` | `true` while the key is down |
| `get_typed_runes()` | Unicode code points typed since the last frame |

With `allow_repeat = true`, `key_went_down` is also `true` for OS key-repeat events. That is what a text field wants for Backspace. Rate and delay come from the OS keyboard settings.

### Keys

The `Keyboard_Key` enum follows Raylib and GLFW. Names you will use most:

- Letters `.A` to `.Z` and digits `.N0` to `.N9`
- Arrows `.Left`, `.Right`, `.Up`, `.Down`
- `.Space`, `.Enter`, `.Escape`, `.Tab`, `.Backspace`, `.Delete`, `.Insert`
- `.Home`, `.End`, `.Page_Up`, `.Page_Down`
- `.F1` to `.F12`
- `.Left_Shift`, `.Right_Shift`, `.Left_Control`, `.Right_Control`, `.Left_Alt`, `.Right_Alt`, `.Left_Super`, `.Right_Super`, `.Menu`
- Punctuation: `.Apostrophe`, `.Comma`, `.Minus`, `.Period`, `.Slash`, `.Semicolon`, `.Equal`, `.Left_Bracket`, `.Backslash`, `.Right_Bracket`, `.Backtick`
- Numpad: `.NP_0` to `.NP_9`, `.NP_Decimal`, `.NP_Divide`, `.NP_Multiply`, `.NP_Subtract`, `.NP_Add`, `.NP_Enter`, `.NP_Equal`
- Lock and system keys: `.Caps_Lock`, `.Scroll_Lock`, `.Num_Lock`, `.Print_Screen`, `.Pause`

### Typed text

For text fields use `get_typed_runes` rather than key presses. It respects the keyboard layout.

```odin
for r in k2.get_typed_runes() {
	strings.write_rune(&builder, r)
}
```

The returned slice is only valid for the current frame.

### Modifiers

`get_held_modifiers` returns a `bit_set[Modifier]` with `Control`, `Alt`, `Shift` and `Super`. Left and right keys count as the same modifier. Compare against an exact set to match a hotkey:

```odin
if k2.get_held_modifiers() == { .Control, .Shift } && k2.key_went_down(.S) {
	save_as()
}
```

That is only true when Control and Shift are held and Alt and Super are not. For an in-game action tied to one specific key, use `key_is_held(.Left_Control)` instead.

## Mouse

| Procedure | Result |
|-----------|--------|
| `mouse_button_went_down(button)` | Button pressed this frame |
| `mouse_button_went_up(button)` | Button released this frame |
| `mouse_button_is_held(button)` | Button is down |
| `get_mouse_position()` | `Vec2`, from the top-left of the window |
| `get_mouse_delta()` | `Vec2`, pixels moved since the previous frame |
| `get_mouse_wheel_delta()` | Wheel clicks, positive is up |
| `get_mouse_wheel_delta_horizontal()` | Positive is right. Driven by tilt wheels and sideways trackpad swipes |

`Mouse_Button` is `.Left`, `.Right` or `.Middle`.

```odin
if k2.mouse_button_went_down(.Left) {
	shoot_at(k2.get_mouse_position())
}
```

The mouse position is in screen space. To get a position in the world when you use a camera, convert it with `screen_to_camera`, see [Camera](karl2d_camera.html#converting-points).

### Locking the mouse

```odin
k2.set_mouse_locked(true)
k2.set_cursor_hidden(true)
```

While the mouse is locked, `get_mouse_position` can give odd or static values. Use `get_mouse_delta` for look controls. Depending on the platform the mouse is either pinned in place or teleported back to the middle of the window each frame.

The OS can unlock the mouse for you, for example when the window loses focus. So check `is_mouse_locked()` and lock it again as needed, instead of assuming your earlier call is still in effect.

Locking does not hide the cursor. Do that with `set_cursor_hidden`, see [Misc](karl2d_misc.html#cursors).

## Touch

```odin
for t in k2.get_touches() {
	if t.went_down {
		spawn_marker(t.position)
	}
}
```

`get_touches` returns every touch active this frame, including ones that ended this frame (their `went_up` is `true`). The order can change from frame to frame, so identify a finger with its `id`.

A `Touch` has:

| Field | Meaning |
|-------|---------|
| `id` | Stable from touch down until touch up. May be reused afterwards |
| `position` | From the top-left of the window |
| `delta` | Pixels moved since the previous frame |
| `went_down` | Started this frame |
| `went_up` | Ended this frame |
| `cancelled` | The OS discarded the touch (palm rejection, focus loss). `went_up` is also set |

Karl2D tracks up to `MAX_TOUCHES` (11) touches: ten fingers plus the one made by mouse emulation.

### Mouse and touch emulation

`set_mouse_touch_emulation` takes a `Mouse_Touch_Emulation`:

| Value | Behaviour |
|-------|-----------|
| `.Touch_To_Mouse` | Touches become left mouse button events. This is the default, so mouse-only games work on touch screens |
| `.Mouse_To_Touch` | Mouse events become touches. Handy for testing touch controls on desktop |
| `.None` | No conversion |

If your game handles both mouse and touch itself, set `.None`, or a tap will count twice.

## Gamepad

Up to `MAX_GAMEPADS` (4) gamepads are supported. A `Gamepad_Index` is an `int` from 0 to 3.

```odin
pad := 0
if k2.is_gamepad_active(pad) {
	move := k2.Vec2 {
		k2.get_gamepad_axis(pad, .Left_Stick_X),
		k2.get_gamepad_axis(pad, .Left_Stick_Y),
	}

	if k2.gamepad_button_went_down(pad, .Right_Face_Down) {
		jump()
	}
}
```

| Procedure | Result |
|-----------|--------|
| `is_gamepad_active(i)` | A gamepad is connected at that index |
| `gamepad_button_went_down(i, b)` | Button pressed this frame |
| `gamepad_button_went_up(i, b)` | Button released this frame |
| `gamepad_button_is_held(i, b)` | Button is down |
| `get_gamepad_axis(i, axis)` | Analogue value. -1 to 1 for sticks, 0 to 1 for triggers |
| `set_gamepad_vibration(i, left, right)` | Motor speeds from 0 to 1 |

On most gamepads the left motor is low frequency and the right is high frequency, so they do not feel the same at the same value.

### Buttons

The face buttons are named by position, so they work for every controller:

| Enum value | Xbox | PlayStation |
|------------|------|-------------|
| `.Right_Face_Up` | Y | Triangle |
| `.Right_Face_Down` | A | X |
| `.Right_Face_Left` | X | Square |
| `.Right_Face_Right` | B | Circle |

Other buttons: the d-pad as `.Left_Face_Up`, `.Left_Face_Down`, `.Left_Face_Left`, `.Left_Face_Right`, then `.Left_Shoulder`, `.Right_Shoulder`, `.Left_Trigger`, `.Right_Trigger`, `.Left_Stick_Press`, `.Right_Stick_Press`, `.Middle_Face_Left` (select/back), `.Middle_Face_Middle` (PS button, not on Xbox) and `.Middle_Face_Right` (start).

Triggers also exist as axes. The button tells you "pressed", the axis `.Left_Trigger` or `.Right_Trigger` tells you how far.

### Axes

`.Left_Stick_X`, `.Left_Stick_Y`, `.Right_Stick_X`, `.Right_Stick_Y`, `.Left_Trigger`, `.Right_Trigger`.

## Events

If you prefer a list of what happened this frame over polling, use `get_events`. It also reports things polling cannot, like focus and resize.

```odin
for event in k2.get_events() {
	#partial switch e in event {
	case k2.Event_Screen_Resize:
		relayout(e.width, e.height)
	case k2.Event_Window_Unfocused:
		pause_game()
	case k2.Event_Key_Went_Down:
		if e.key == .Escape {
			open_menu()
		}
	}
}
```

The slice is only valid during the current frame. Analogue stick and trigger movement is **not** an event: use `get_gamepad_axis`.

| Event | Fields |
|-------|--------|
| `Event_Close_Window_Requested` | none |
| `Event_Key_Went_Down`, `Event_Key_Went_Up` | `key` |
| `Event_Key_Repeat` | `key`. Sent in addition to the first `Event_Key_Went_Down` |
| `Event_Typed_Rune` | `typed` |
| `Event_Mouse_Move` | `position` |
| `Event_Mouse_Teleported` | `position`. Like a move, but ignored when computing the mouse delta |
| `Event_Mouse_Wheel`, `Event_Mouse_Wheel_Horizontal` | `delta` |
| `Event_Mouse_Button_Went_Down`, `Event_Mouse_Button_Went_Up` | `button` |
| `Event_Gamepad_Button_Went_Down`, `Event_Gamepad_Button_Went_Up` | `gamepad`, `button` |
| `Event_Screen_Resize` | `width`, `height` |
| `Event_Window_Focused`, `Event_Window_Unfocused` | none |
| `Event_Window_Scale_Changed` | `scale`, `screen_width`, `screen_height` |
| `Event_Touch_Went_Down`, `Event_Touch_Moved`, `Event_Touch_Went_Up` | `id`, `position` |
| `Event_Touch_Cancelled` | `id` only, since not every platform knows where it was |
