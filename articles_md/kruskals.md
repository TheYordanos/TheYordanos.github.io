---
title: Kruskal's Algorithm
description: Building a perfect maze by knocking down walls in random order, using union-find to avoid loops
date: 2026-11-17
series: Maze Generation
part: 3
source: https://codeberg.org/yordanos/mazes
---

## Kruskal's Algorithm

Every room starts as its own sealed-off island. Shuffle all the walls, then go through them one by one. If the rooms on either side are already connected, leave the wall alone, because knocking it down would make a loop. Otherwise knock it down and two islands become one. When the walls run out, everything is one connected maze.

The result is a busy, even texture with lots of short dead ends, quite unlike the backtracker's long corridors.

![Kruskal's Algorithm](../res/articles/maze_generation/kruskals.gif)

### The new idea: union-find

We need to ask "are these two rooms already connected?" for every wall, so it has to be fast. **Union-find** does that. Every room stores a **parent**, and at the start each room is its own parent, which makes it a **root**. `find(room)` follows parents up to the root, and two rooms are connected exactly when their roots match. `join(a, b)` points one root at the other.

To keep `find` fast we use **path compression**: once it has reached the root, every room along the way is pointed directly at it. ^[Always attaching the smaller group under the larger one, called union by size, speeds lookups up even more.]

### Pseudocode

```
for each room: parent[room] = room
walls = every wall between two rooms
shuffle(walls)

for each wall in walls:
    a, b = the two rooms on either side of wall
    if find(a) != find(b):
        knock out the wall
        join(a, b)
```

### Solution

```odin
find :: proc(room: [2]i32, parents: ^[COLS][ROWS][2]i32) -> [2]i32 {
	parent := parents[room.x][room.y]
	if room == parent do return room

	root := find(parent, parents)
	parents[room.x][room.y] = root // path compression
	return root
}

join :: proc(root_a, root_b: [2]i32, parents: ^[COLS][ROWS][2]i32) {
	parents[root_a.x][root_a.y] = root_b
}

kruskals :: proc(maze: ^[COLS][ROWS]Cell) {
	parents: [COLS][ROWS][2]i32

	walls: [dynamic][2]i32
	defer delete(walls)

	for x in 1..<i32(COLS - 1) {
		for y in 1..<i32(ROWS - 1) {
			if x & 1 == 1 && y & 1 == 1 {
				// a room: open it, and make it its own group
				maze[x][y] = .PATH
				parents[x][y] = {x, y}
			} else if (x + y) & 1 == 1 {
				// exactly one odd coordinate: a wall
				append(&walls, [2]i32{x, y})
			}
			// both even: a pillar, never touched
		}
	}

	rand.shuffle(walls[:])

	for wall in walls {
		// an even x puts the two rooms left and right of the wall,
		// an even y puts them above and below
		offset := [2]i32{wall.y & 1, wall.x & 1}
		a, b := wall - offset, wall + offset

		root_a, root_b := find(a, &parents), find(b, &parents)
		if root_a == root_b do continue

		maze[wall.x][wall.y] = .PATH
		join(root_a, root_b, &parents)
	}
}

generate :: proc(maze: ^[COLS][ROWS]Cell) {
	kruskals(maze)
}
```

Run it, press space a few times.
```
odin run .
```
