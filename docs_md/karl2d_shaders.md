---
title: Shaders
description: Loading custom shaders, setting constants, textures and per-object inputs.
project: Karl2D
order: 9
updated: 2026-11-22
---
Karl2D draws everything with a shader. You can use your own to make effects such as outlines, color grading or wobbling water. This is an advanced topic: skip it until you need it.

The shader source files are written in the shading language of the render backend you build with (D3D11, OpenGL or WebGL). Karl2D does not translate between them. Cross-API shader compilation is only planned.

> **Tip:** on Windows you can use the OpenGL backend with `-define:KARL2D_RENDER_BACKEND=gl` if you want to share shader code with the web build, since both use almost the same `glsl` version.

## Using a shader

```odin
shader := k2.load_shader_from_file("wobble.vert", "wobble.frag")

k2.set_shader(shader)
// everything drawn here uses the shader
k2.set_shader(nil)
// back to the default shader
```

`set_shader` takes a `Maybe(Shader)`. Pass `nil` to return to the default shader. `get_default_shader()` returns the default one if you need it.

## Loading

| Procedure | Source |
|-----------|--------|
| `load_shader_from_file(vertex_filename, fragment_filename, layout_formats)` | Two files. If the vertex and fragment code are in one file, pass the name twice |
| `load_shader_from_bytes(vertex_bytes, fragment_bytes, layout_formats)` | From memory, for example with `#load` |

Both return `(Shader, bool)`. If it fails, the returned shader is safe to use but setting it does nothing, so drawing continues with the shader that was already set.

`layout_formats` is a `[]Pixel_Format` that describes the vertex inputs, as you pass them from the CPU. Most of the time you can leave it as the default.

`destroy_shader(shader)` frees a shader.

## Constants

A *constant* is what OpenGL calls a uniform. Look its location up by name through `constant_lookup`, then set the value:

```odin
loc := shader.constant_lookup["time"]
k2.set_shader_constant(shader, loc, f32(k2.get_time()))
```

```odin
set_shader_constant :: proc(shd: Shader, loc: Shader_Constant_Location, val: any)
```

Karl2D keeps the CPU-side value of all constants in one buffer. A `Shader_Constant_Location` is an `offset` and a `size` into it. Look the location up once and keep it instead of doing the map lookup every frame.

## Extra textures

Normal drawing passes the texture you give `draw_texture` into the shader for you. When a shader needs more than one texture, bind the extra ones with `set_shader_texture`. Find the bindpoint through `texture_lookup`:

```odin
bp := shader.texture_lookup["mask"]
k2.set_shader_texture(shader, bp, mask_texture)
```

## Vertex inputs

The default shader has three inputs: position, texcoord (UV) and color. If your shader has more, you can feed per-object data with `override_shader_input`:

```odin
override_shader_input :: proc(shader: Shader, input: int, val: any)
```

`input` is the index of the input, and `val` must have the right size for it. Change the expected type by giving a custom `layout_formats` when you load the shader.

An input has a name, a register, a `Shader_Input_Type` (`F32`, `Vec2`, `Vec3` or `Vec4`) and a `Pixel_Format`. The values you override are stored per input, up to `SHADER_INPUT_VALUE_MAX_SIZE` (256) bytes each.

## The Shader struct

Most fields are internal. Those you may touch:

| Field | Use |
|-------|-----|
| `constant_lookup` | Name to `Shader_Constant_Location` |
| `texture_lookup` | Name to texture bindpoint |
| `inputs` | The vertex inputs |
| `vertex_size` | Bytes per vertex. Decides how many vertices fit in a batch |

The built-in constant `View_Projection_Matrix` is filled in for you.

## Batching

Switching shaders starts a new draw call, so group objects that share a shader. See [Drawing](karl2d_drawing.html#batching-and-draw-calls).
