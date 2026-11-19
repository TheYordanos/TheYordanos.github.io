---
title: Growing Tree Algorithm
description: One algorithm with a dial, where the way you pick the next room decides what kind of maze you get
date: 2026-11-19
series: Maze Generation
part: 8
source: https://codeberg.org/yordanos/mazes
---

## Growing Tree Algorithm

Growing Tree keeps a list of *active* rooms, the ones that might still have unvisited neighbours. Pick a room from the list. If it has an unvisited neighbour, knock down the wall to it, open that room, and add it to the list. If it doesn't, remove it, because it's finished. Repeat until the list is empty.

Everything interesting is in *how* you pick. Always take the newest room, and you get the Recursive Backtracker: the list is the stack, and removing a finished room is the backtrack. Take a random room, and the maze grows outward in a blob, much like Prim's. Mix the two, and you get mazes somewhere in between. ^[`ordered_remove` keeps the list in order, which "newest" depends on. Prim's could use `unordered_remove` because it never cared about order.]

![Growing Tree Algorithm](../res/articles/maze_generation/growing_tree.gif)

### Pseudocode

```
active = [a random room]; mark it visited

while active is not empty:
    room = pick one from active
    if room has an unvisited neighbour:
        next = a random unvisited neighbour
        knock out the wall between room and next
        mark next visited
        add next to active
    else:
        remove room from active
```

### Solution

This uses the `random_dir` helper from the Hunt and Kill article.

```odin
Strategy :: enum { NEWEST, RANDOM, MIXED }

pick :: proc(strategy: Strategy, count: int) -> int {
	switch strategy {
	case .NEWEST:
		return count - 1
	case .RANDOM:
		return rand.int_max(count)
	case .MIXED:
		// half the time the newest, half the time a random one
		if rand.float32() < 0.5 do return count - 1
		return rand.int_max(count)
	}

	return 0
}

growing_tree :: proc(maze: ^[COLS][ROWS]Cell, first: [2]i32, strategy: Strategy) {
	active: [dynamic][2]i32
	defer delete(active)

	maze[first.x][first.y] = .PATH
	append(&active, first)

	for len(active) > 0 {
		i := pick(strategy, len(active))
		room := active[i]

		dir, ok := random_dir(maze, room, .WALL)
		if !ok {
			// no unvisited neighbours: this room is finished
			ordered_remove(&active, i)
			continue
		}

		wall, next := room + dir, room + 2 * dir
		maze[wall.x][wall.y] = .PATH
		maze[next.x][next.y] = .PATH

		append(&active, next)
	}
}

generate :: proc(maze: ^[COLS][ROWS]Cell) {
	growing_tree(maze, random_room(), .MIXED) // try .NEWEST and .RANDOM too
}
```

Run it, press space a few times, and you'll get a new maze each time.
```
odin run .
```
