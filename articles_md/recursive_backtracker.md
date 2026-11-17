---
title: Recursive Backtracker
description: Carving a perfect maze with a depth-first walk
date: 2026-11-16
series: Maze Generation
part: 2
---

## Recursive Backtracker

The Recursive Backtracker is the most common maze algorithm to start with. It works like someone exploring a cave with a ball of string: walk forward into any unvisited room, knocking down the wall behind you, and keep going until you're stuck. When there's nowhere new to go, retrace your steps until you find a room that still has an unexplored neighbour, then head off in that direction. When you've backed all the way out to the start, every room has been visited and the maze is done.

In graph terms this is a randomized **depth-first search**. Because we only ever step into a room we haven't visited, we never connect two rooms that are already connected, so no loops form. And because the search doesn't stop until every room is reached, no area is left inaccessible. ^[That is exactly the "perfect maze" guarantee from the [introduction](maze_generation.html).]

![Recursive Backtracker](../res/articles/maze_generation/recursive_backtracker.gif)

### Pseudocode

Try implementing this yourself before reading the solution. ^[Question for you: Why is the neighbour `2 * direction` away and not `1`?]

```
carve(room):
    mark room as PATH
    for each direction, in random order:
        neighbour = room + 2 * direction
        if neighbour is in bounds and still a WALL:
            knock out the wall between room and neighbour
            carve(neighbour)

start: carve(a random room)
```

### Solution

```odin
recursive_backtracker :: proc(maze: ^[COLS][ROWS]Cell, room: [2]i32) {
	maze[room.x][room.y] = .PATH

	dirs := [4][2]i32{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}
	rand.shuffle(dirs[:])

	for dir in dirs {
		next := room + 2 * dir

		if !is_cell_in_bounds(next) || maze[next.x][next.y] != .WALL do continue

		wall := room + dir
		maze[wall.x][wall.y] = .PATH

		recursive_backtracker(maze, next)
	}
}

generate :: proc(maze: ^[COLS][ROWS]Cell) {
	recursive_backtracker(maze, random_room())
}
```

Run it, press space a few times, and you'll get a new maze each time.
```
odin run .
```
