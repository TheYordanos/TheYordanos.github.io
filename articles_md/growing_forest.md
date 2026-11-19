---
title: Growing Forest Algorithm
description: Growing several trees at once and merging them with Kruskal's sets
date: 2026-11-19
series: Maze Generation
part: 9
source: https://codeberg.org/yordanos/mazes
---

## Growing Forest Algorithm

Growing Forest is Growing Tree with several trees growing at once, and Kruskal's sets to stop them forming loops. Start a few trees in random rooms. Each active room either grows into an uncarved neighbour, which joins its tree, or runs into a carved room. If that room belongs to a *different* tree, knock the wall down and the two trees become one. If it belongs to the same tree, leave the wall alone. New trees can start at random along the way. When the growing is done, any trees that never met are connected by a final pass of Kruskal's.

How many trees you start with and how often new ones appear changes the texture of the maze. ^[Think Labyrinth notes that, with the right parameters, Growing Forest can reproduce the Recursive Backtracker, Kruskal's, Prim's and Growing Tree.]

![Growing Forest Algorithm](../res/articles/maze_generation/growing_forest.gif)

### Pseudocode

```
every room is its own set; all rooms uncarved
start N trees: carve a random room, add to active

while active is not empty:
    maybe start a new tree (with some chance)
    room = pick one from active
    if room has no uncarved neighbour:
        remove room from active
        continue
    next = room + 2 * (a random direction in bounds)
    if next is uncarved:
        knock out the wall, carve next, join sets, add next to active
    else if find(room) != find(next):
        knock out the wall, join sets

merge what's left: Kruskal's pass over every wall
```

### Solution

This uses `find` and `join` from Kruskal's, `rooms_beside_wall` from Prim's, and `random_dir` from Hunt and Kill.

```odin
// a random direction whose neighbouring room is in bounds
random_dir_any :: proc(room: [2]i32) -> [2]i32 {
	dirs := [4][2]i32{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}
	rand.shuffle(dirs[:])

	for d in dirs {
		if is_cell_in_bounds(room + 2 * d) do return d
	}

	return {}
}

growing_forest :: proc(maze: ^[COLS][ROWS]Cell, trees: int, spawn_chance: f32) {
	parents: [COLS][ROWS][2]i32
	walls: [dynamic][2]i32
	defer delete(walls)

	// every room is its own set, and we collect the walls for the final pass
	for x in 1..<i32(COLS - 1) {
		for y in 1..<i32(ROWS - 1) {
			if x & 1 == 1 && y & 1 == 1 {
				parents[x][y] = {x, y}
			} else if (x + y) & 1 == 1 {
				append(&walls, [2]i32{x, y})
			}
		}
	}
	rand.shuffle(walls[:])

	active: [dynamic][2]i32
	defer delete(active)

	// start the first trees
	for _ in 0..<trees {
		room := random_room()
		for maze[room.x][room.y] != .WALL do room = random_room()

		maze[room.x][room.y] = .PATH
		append(&active, room)
	}

	for len(active) > 0 {
		// sometimes start a new tree
		if rand.float32() < spawn_chance {
			room := random_room()

			if maze[room.x][room.y] == .WALL {
				maze[room.x][room.y] = .PATH
				append(&active, room)
			}
		}

		i := rand.int_max(len(active))
		room := active[i]

		// no uncarved neighbour: this room is finished
		if _, ok := random_dir(maze, room, .WALL); !ok {
			unordered_remove(&active, i)
			continue
		}

		dir := random_dir_any(room)
		wall, next := room + dir, room + 2 * dir
		root_room, root_next := find(room, &parents), find(next, &parents)

		if maze[next.x][next.y] == .WALL {
			// grow into a new room
			maze[wall.x][wall.y] = .PATH
			maze[next.x][next.y] = .PATH

			join(root_next, root_room, &parents)
			append(&active, next)
		} else if root_room != root_next {
			// two different trees meet: connect them
			maze[wall.x][wall.y] = .PATH

			join(root_next, root_room, &parents)
		}
	}

	// merge what's left: Kruskal's pass
	for wall in walls {
		a, b := rooms_beside_wall(wall)

		root_a, root_b := find(a, &parents), find(b, &parents)
		if root_a == root_b do continue

		maze[wall.x][wall.y] = .PATH
		join(root_a, root_b, &parents)
	}
}

generate :: proc(maze: ^[COLS][ROWS]Cell) {
	growing_forest(maze, 5, 0.01)
}
```

Run it, press space a few times, and you'll get a new maze each time.
```
odin run .
```
