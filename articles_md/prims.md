---
title: Prim's Algorithm
description: Growing a perfect maze outward from a single room, one random wall at a time
date: 2026-11-18
series: Maze Generation
part: 4
---

## Prim's Algorithm

Where Kruskal's builds the maze everywhere at once, Prim's grows a single maze outward from one room. We keep a **frontier**: the walls between the maze so far and a room that isn't in it yet. Pick a random wall from the frontier. If the room beyond it isn't in the maze, knock the wall down, open that room, and add its walls to the frontier. If it already is, throw the wall away, because knocking it down would make a loop. Repeat until the frontier is empty.

The texture is similar to Kruskal's ^[Plenty of short dead ends and branches instead of long winding paths like the backtracker.], but you can watch it spread outward from the starting room.

![Prim's Algorithm](../res/articles/maze_generation/prims.gif)

There is only ever one group here, so no union-find is needed. A room is in the maze if it is a `PATH`, and not yet if it is a `WALL`.

### Pseudocode

```
carve(start room); add_walls(start room)

while frontier is not empty:
    wall = remove a random wall from frontier
    a, b = the two rooms on either side of wall
    if exactly one of them is not in the maze yet:
        knock out the wall
        open that room
        add_walls(that room)

add_walls(room):
    for each direction:
        wall = room + direction
        far  = room + 2 * direction
        if far is in bounds and not in the maze:
            add wall to frontier
```

### Solution

```odin
// the offset trick from Kruskal's, pulled out so we can reuse it
rooms_beside_wall :: proc(wall: [2]i32) -> (a, b: [2]i32) {
	offset := [2]i32{wall.y & 1, wall.x & 1}
	return wall - offset, wall + offset
}

add_walls :: proc(maze: ^[COLS][ROWS]Cell, frontier: ^[dynamic][2]i32, room: [2]i32) {
	dirs := [4][2]i32{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}

	for dir in dirs {
		wall := room + dir
		far := room + 2 * dir

		if is_cell_in_bounds(far) && maze[far.x][far.y] == .WALL {
			append(frontier, wall)
		}
	}
}

prims :: proc(maze: ^[COLS][ROWS]Cell, start: [2]i32) {
	frontier: [dynamic][2]i32
	defer delete(frontier)

	maze[start.x][start.y] = .PATH
	add_walls(maze, &frontier, start)

	for len(frontier) > 0 {
		i := rand.int_max(len(frontier))
		wall := frontier[i]
		unordered_remove(&frontier, i)

		a, b := rooms_beside_wall(wall)

		// both rooms already open: carving this wall would make a loop
		if maze[a.x][a.y] == maze[b.x][b.y] do continue

		next := maze[a.x][a.y] == .WALL ? a : b

		maze[wall.x][wall.y] = .PATH
		maze[next.x][next.y] = .PATH

		add_walls(maze, &frontier, next)
	}
}

generate :: proc(maze: ^[COLS][ROWS]Cell) {
	prims(maze, random_room())
}
```

Run it, press space a few times.
```
odin run .
```
