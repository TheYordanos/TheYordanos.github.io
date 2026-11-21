---
title: Recursive Division Algorithm
description: Starting with an open room and building walls, each with a single gap
date: 2026-11-21
series: Maze Generation
part: 11
source: https://codeberg.org/yordanos/mazes
---

## Recursive Division Algorithm

Every algorithm so far carved passages out of a solid block. Recursive Division does the opposite: it starts with an open space and builds walls. Split the space in two with a wall that runs all the way across it, leaving exactly one gap. Then split each half the same way, and keep going until every space is a single room.

It makes a perfect maze for a simple reason. Each wall has exactly one gap, so the two halves are connected in exactly one place, and by the same argument each half is a perfect maze of its own. The mazes have long straight walls, which stand out as soon as you run it.

On our grid, walls go on even coordinates and gaps on odd ones. ^[A gap on an odd coordinate always lands on a cell between two rooms. On an even one it would land on a pillar and connect nothing.]

![Recursive Division Algorithm](../res/articles/maze_generation/recursive_division.gif)

### Pseudocode

```
divide(chamber):
    if the chamber is a single room: return
    choose a direction: split across the longer side (random if it's square)
    wall = a random position strictly inside the chamber, running the full length
    gap = a random position along that wall
    build the wall everywhere except the gap
    divide(first half)
    divide(second half)

start: open everything inside the border; divide(the whole grid)
```

### Solution

```odin
divide :: proc(maze: ^[COLS][ROWS]Cell, lo, hi: [2]i32) {
	if lo == hi do return

	size := (hi - lo) / 2 + {1, 1} // rooms across and down

	// split across the longer side, at random if it's square
	axis := size.x > size.y ? 0 : size.x < size.y ? 1 : rand.int31_max(2)
	other := 1 - axis

	// the wall sits on an even coordinate, the gap on an odd one
	wall := lo[axis] + 1 + 2 * rand.int31_max(size[axis] - 1)
	gap := lo[other] + 2 * rand.int31_max(size[other])

	pos: [2]i32
	pos[axis] = wall
	for i in lo[other]..=hi[other] {
		pos[other] = i
		maze[pos.x][pos.y] = .WALL
	}

	pos[other] = gap
	maze[pos.x][pos.y] = .PATH

	// divide the two halves
	first_hi := hi
	first_hi[axis] = wall - 1

	second_lo := lo
	second_lo[axis] = wall + 1

	divide(maze, lo, first_hi)
	divide(maze, second_lo, hi)
}

recursive_division :: proc(maze: ^[COLS][ROWS]Cell) {
	// open everything inside the border
	for x in 1..<COLS - 1 {
		for y in 1..<ROWS - 1 {
			maze[x][y] = .PATH
		}
	}

	divide(maze, {1, 1}, {COLS - 2, ROWS - 2})
}

generate :: proc(maze: ^[COLS][ROWS]Cell) {
	recursive_division(maze)
}
```

Run it, press space a few times.
```
odin run .
```
