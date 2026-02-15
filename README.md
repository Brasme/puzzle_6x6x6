# 6x6x6 Brick Presenter

This small Python tool helps you build and visualize arrangements of 4-cube bricks inside a 6x6x6 grid.

## Files
- `presentation.py` — core logic: `Brick`, `CubeGrid`, placement/rotation helpers, CLI REPL, and JSON save/load.
- `gui_presentation.py` — Tkinter GUI with an embedded matplotlib 3D view and controls for placing/moving bricks.
- `requirements.txt` — Python dependencies (numpy, matplotlib).

## Quick start
Install dependencies (PowerShell):

```powershell
python -m pip install -r .\requirements.txt
```

Run the GUI (from the repository root):

```powershell
python .\gui_presentation.py
```

Run the simple CLI/REPL (from the repository root):

```powershell
python .\presentation.py
# or demo mode
python .\presentation.py --demo
```

## GUI features
- Brick selection and rotation/position controls.
- Place / Remove / Move (±X/±Y/±Z) placed bricks.
- `Find T spaces` — scans the grid and lists valid placements for the `T` brick (double-click or "Place Selected" to add).
- `Only adjacent` checkbox — when enabled, `Find T spaces` shows only placements that touch an existing cube.
- `Add Random Adj T` — randomly picks an adjacent valid `T` placement and places it.
- `Check T between` — popup + visual indicator show whether a `T` brick can be placed touching at least two distinct existing bricks.
- Save... / Load... — persist current layout to JSON and restore it later.

The GUI also shows a small status label `T between: YES/NO` that updates automatically as you modify the grid.

## CLI commands (presentation.py)
- `add <brick_id> x y z rx ry rz` — place a brick where rotations are 90° steps.
- `show` — open the matplotlib 3D view.
- `list` — print available brick ids.
- `reset` — clear the grid.
- `exit` — quit.

## Developer API (in `presentation.py`)

If you want to script or inspect placements programmatically, `CubeGrid` exposes a couple of helpers:

- `validate_placements(brick: Brick) -> List[Tuple[Brick, Coord]]`
	- Returns a list of tuples `(rotated_brick, pos)` for every rotation and anchor position where the `brick` can currently be placed (i.e. the anchor cell is empty and that rotated brick fits without overlap).
	- Useful for building UIs that preview available placements or for enumerating all valid moves.

- `can_not_place_somewhere(brick: Brick) -> bool`
	- Scans the grid anchors (precomputed valid anchors) and returns `True` if there exists at least one empty anchor position where *no* rotation of `brick` would fit at that anchor. In other words, it detects dead/blocked empty anchors where the brick cannot be placed in any orientation.
	- The function prints a short diagnostic (anchor coordinate) when it finds such a spot.

Example usage from Python:

```python
from presentation import CubeGrid, Brick
g = CubeGrid(size=6)
T = g.bricks['T']
# list all valid rotated placements
placements = g.validate_placements(T)
print(f"{len(placements)} valid placements for T")

# check for blocked empty anchors
blocked = g.can_not_place_somewhere(T)
if blocked:
		print("There exists at least one empty anchor where T cannot be placed in any rotation")
else:
		print("Every empty anchor is compatible with at least one T rotation")
```

## JSON save format
Saved files are JSON with a simple structure:

```json
{
	"size": 6,
	"next_id": 5,
	"placed": [
		{ "pid": 1, "name": "O", "cubes": [[0,0,0],[1,0,0],[0,1,0],[1,1,0]], "pos": [0,0,0] },
		{ "pid": 2, "name": "I", "cubes": [[0,0,0],[1,0,0],[2,0,0],[3,0,0]], "pos": [0,2,0] }
	]
}
```

Each placed item stores the brick's relative `cubes`, a `pos` offset, and a `pid` used internally.

## Extending bricks
Add or change brick definitions in `sample_bricks()` inside `presentation.py`. Each brick must contain exactly 4 cube coordinates (tuples of integers).

## Notes and limitations
- The placement/rotation search is exhaustive but fast for 6x6x6 and 4-cube bricks. For larger grids or more complex pieces, consider more efficient pruning.
- The loader assumes saved files are consistent; loading an invalid file (overlaps or out-of-bounds) may raise an error. 
