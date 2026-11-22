---
title: Audio
description: Playing sound effects and music, controlling sounds, buses and custom effects.
project: Karl2D
order: 7
updated: 2026-11-22
---
Karl2D has a software mixer that runs at `AUDIO_MIX_SAMPLE_RATE` (44100 Hz). It starts with `init`. `update` calls `update_audio` for you, which must run once per frame (see [Window and frame](karl2d_window.html#doing-the-frame-by-hand) if you run the frame by hand).

There are three ideas to keep apart:

| Type | What it is |
|------|------------|
| `Audio_Clip` | A piece of audio fully loaded in memory. Good for sound effects |
| `Audio_Stream` | An ogg file decoded a little at a time. Good for music |
| `Sound` | Something **playing right now**. You get one when you play a clip or stream |

One clip can have many sounds playing from it at once.

## Playing a clip

```odin
jump_sfx := k2.load_audio_clip_from_file("jump.wav")

if k2.key_went_down(.Space) {
	k2.play_audio_clip(jump_sfx)
}
```

```odin
play_audio_clip :: proc(
	clip: Audio_Clip,
	volume: f32 = 1,
	pan: f32 = 0,
	pitch: f32 = 1,
	loop := false,
	bus: Audio_Bus = AUDIO_BUS_MASTER,
) -> Sound
```

You can ignore the returned `Sound` if you never need to touch the sound again.

> **Warning:** if you pass `loop = true` and throw away the returned `Sound`, you have started something you can never stop.

### Loading clips

| Procedure | Source |
|-----------|--------|
| `load_audio_clip_from_file(filename)` | WAV or OGG file on disk |
| `load_audio_clip_from_bytes(bytes)` | The **whole** WAV or OGG file in memory, headers included, for example `#load("x.wav")` |
| `load_audio_clip_from_bytes_raw(bytes, format, sample_rate, channels)` | Raw samples without a header |

All return `(Audio_Clip, bool)`. A failed clip is safe to use but plays nothing.

For raw data, describe it with a `Raw_Audio_Format` (`Integer8`, `Integer16`, `Integer24`, `Integer32`, `Float32` or `Float64`) and `Audio_Channels` (`.Mono` or `.Stereo`). 8-bit data is unsigned, like in 8-bit WAV files. The other integer formats are signed, and 24-bit is three bytes per sample, little endian.

If a clip's sample rate differs from the mixer's, the mixer interpolates.

`destroy_audio_clip(clip)` frees it and also stops any sounds playing it. `get_num_sounds_playing_clip(clip)` counts how many sounds are playing it, which is useful to avoid starting too many copies of the same effect:

```odin
if k2.get_num_sounds_playing_clip(hit_sfx) < 4 {
	k2.play_audio_clip(hit_sfx)
}
```

## Streaming music

Streams only keep a small piece of the file in memory, so long music does not take much RAM. Only **ogg** is supported.

```odin
music := k2.load_audio_stream_from_file("music.ogg")
song := k2.play_audio_stream(music, loop = true)

for k2.update() {
	k2.update_audio_stream(music) // every frame!
	// ...
}
```

A stream does not read its data by itself. Call `update_audio_stream(stream)` every frame, or it runs out of data.

| Procedure | Job |
|-----------|-----|
| `load_audio_stream_from_file(filename)` | Stream from a file |
| `load_audio_stream_from_bytes(bytes)` | Stream from an ogg file already in memory. The bytes are **not copied**: keep them alive while the stream plays |
| `update_audio_stream(stream)` | Feed new data |
| `play_audio_stream(stream, ...)` | Start playing. Same optional arguments as `play_audio_clip` |
| `destroy_audio_stream(stream)` | Clean up. It does not free the bytes you gave to `_from_bytes` |

`load_audio_stream_from_bytes` is how to stream music on the web, where there is no file system, and how to make a single-file desktop game:

```odin
music := k2.load_audio_stream_from_bytes(#load("music.ogg"))
```

There is no raw variant for streams. The point is to decode an encoded file bit by bit.

A stream can only play **one sound at a time**. If it is already playing, `play_audio_stream` returns the existing `Sound` and ignores the new settings, so use the `set_sound_*` procedures to change them. To start over from the beginning, call `stop_sound` first. If the sound was paused, `play_audio_stream` resumes it. A stream starts from wherever it last was, which is the beginning if it was just loaded, was stopped or finished.

`update_audio_stream` is thread safe for **one thread per stream**. That lets you run a music thread that is not affected by stalls in the game or by the window being dragged.

## Controlling a sound

`Sound` is a handle. When a sound finishes it is destroyed automatically, but it is safe to keep the handle: these procedures then do nothing.

| Procedure | Job |
|-----------|-----|
| `stop_sound(s)` | Stop and destroy the sound. For a stream sound it also rewinds the stream |
| `set_sound_paused(s, paused)` | Pause or resume, keeping position and settings |
| `sound_is_playing(s)` | The sound exists and is not paused |
| `sound_is_valid(s)` | The sound still exists. Paused counts, finished or stopped does not |
| `set_sound_volume(s, v)` | 0 to 1 |
| `set_sound_pan(s, p)` | -1 (left) to 1 (right), 0 is center |
| `set_sound_pitch(s, p)` | 0.01 and up, 1 is normal. Pitch 2 plays twice as fast and sounds higher |
| `set_sound_loop(s, loop)` | Loop at the end |
| `set_sound_time(s, seconds)` | Jump to a position |
| `get_sound_time(s)` | Position in seconds. A looping sound returns to 0 when it restarts. 0 if the sound does not exist |
| `get_sound_length(s)` | Length in seconds. 0 if the sound does not exist or the length is unknown |
| `set_sound_bus(s, bus)` | Route into a bus |

Seeking a clip is fast. Seeking a stream is slower because the stream may need to read from disk. Seeking fades out, moves and fades in, so you do not hear a click.

```odin
// a progress bar for a song
progress := k2.get_sound_time(song) / k2.get_sound_length(song)
```

Sound settings change a little at a time rather than instantly, to avoid clicks.

`set_sound_loop` also works for stream sounds. It tells the decoder to loop the whole file.

## Buses

A bus is a group of sounds that is mixed together before reaching the master bus. Use buses for "music volume", "effects volume" and the like.

```odin
sfx_bus   := k2.create_audio_bus()
music_bus := k2.create_audio_bus()

k2.play_audio_clip(jump_sfx, bus = sfx_bus)
k2.play_audio_stream(music, loop = true, bus = music_bus)

// options menu
k2.set_audio_bus_volume(music_bus, 0.4)
k2.set_audio_bus_volume(k2.AUDIO_BUS_MASTER, 0.8)
```

| Procedure | Job |
|-----------|-----|
| `create_audio_bus()` | A new bus. Volume 1, pan 0, no effect, so it sounds the same as the master bus until you change something |
| `destroy_audio_bus(bus)` | Destroy. Everything routed to it goes back to the master bus, including sounds playing now |
| `set_audio_bus_volume(bus, v)` | 0 to 1 |
| `set_audio_bus_pan(bus, p)` | -1 to 1 |
| `set_audio_bus_effect(bus, effect, user_data)` | Run an effect on the whole bus. `nil` removes it |

`AUDIO_BUS_MASTER` is the default for everything. All other buses are mixed into it. Use it with the bus procedures to control your game's overall volume.

A bus's pan is a **balance** control: it turns the opposite side down, and at 0 the mix is left unchanged. A sound's pan moves the sound between the speakers at constant loudness. They differ on purpose.

## Custom effects

```odin
Audio_Effect_Proc :: proc(samples: [][2]Audio_Sample, user_data: rawptr)
```

The effect gets the finished mix of the bus as stereo samples (`Audio_Sample` is an `f32` from -1 to 1). Change the samples to apply your effect. It is called once per mixed chunk, so anything it needs to remember between chunks must live in `user_data`.

```odin
Lowpass :: struct {
	last: [2]f32,
	amount: f32,
}

lowpass_effect :: proc(samples: [][2]k2.Audio_Sample, user_data: rawptr) {
	state := (^Lowpass)(user_data)
	for &s in samples {
		state.last += (s - state.last) * state.amount
		s = state.last
	}
}

lowpass := Lowpass { amount = 0.1 }
k2.set_audio_bus_effect(music_bus, lowpass_effect, &lowpass)
```

The mixer may run on an audio thread, so keep the effect fast and avoid allocating memory in it.

## Positional audio

Karl2D has no built-in "3D" sound. The usual approach is to compute volume and pan yourself from the sound's distance and horizontal position, then call `set_sound_volume` and `set_sound_pan`. The repository has a `positional_audio` example that plays sounds panned by their position in the world.
