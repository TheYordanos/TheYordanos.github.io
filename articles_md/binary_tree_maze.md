---
title: Binary Tree Algorithm
description: Carving a perfect maze by giving every room one connection to the south or east
date: 2026-11-21
series: Maze Generation
part: 12
source: https://codeberg.org/yordanos/mazes
---

## Binary Tree Algorithm

Binary Tree is the simplest algorithm in the series. Go through every room and, for each one, knock down the wall to the south or to the east, whichever you pick at random. If only one of them is possible because the room is on an edge, take that one. The bottom-right room has neither, so it does nothing.

Every room except the bottom-right one is connected to exactly one neighbour, its parent, and following parents always leads to that corner. That makes it a tree, so the maze is perfect.

The price is a strong bias. The bottom row and the right column are always one long open corridor, and the whole maze has a diagonal grain. ^[Each room decides on its own, without looking at what any other room did, so the rooms can be visited in any order.]

![Binary Tree Algorithm](../res/articles/maze_generation/binary_tree.gif)

### Pseudocode

```
for each room:
    options = the directions south and east where the room beyond is in bounds
    if options is not empty:
        knock out the wall in a random one of them
```

### Solution

```odin
binary_tree :: proc(maze: ^[COLS][ROWS]Cell) {
	dirs := [2][2]i32{{0, 1}, {1, 0}} // south and east

	for x: i32 = 1; x < COLS - 1; x += 2 {
		for y: i32 = 1; y < ROWS - 1; y += 2 {
			room := [2]i32{x, y}
			maze[x][y] = .PATH

			options: [2][2]i32
			count := 0
			for dir in dirs {
				if is_cell_in_bounds(room + 2 * dir) {
					options[count] = dir
					count += 1
				}
			}

			if count == 0 do continue

			wall := room + options[rand.int_max(count)]
			maze[wall.x][wall.y] = .PATH
		}
	}
}

generate :: proc(maze: ^[COLS][ROWS]Cell) {
	binary_tree(maze)
}
```

Run it, press space a few times.
```
odin run .
```
