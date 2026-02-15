"""presentation.py

Small tool to build and visualize a 6x6x6 cube and place 4-cube bricks (polycubes of 4 units).

Run as:
    python presentation.py

Interactive commands (simple):
    add <brick_id> x y z rx ry rz   # add a brick by id at position (x,y,z) with rotations (multiples of 90deg)
    show                            # display the current grid
    list                            # list available bricks
    reset                           # clear the grid
    exit

Bricks are defined as sets of 4 integer cube coordinates relative to (0,0,0).
"""
from __future__ import annotations
import sys
from typing import List, Tuple, Dict
import json
import numpy as np

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
except Exception as e:  # pragma: no cover - helpful error if deps missing
    print("matplotlib is required to run this script. Install with: pip install -r requirements.txt")
    raise

Coord = Tuple[int, int, int]


def rotate_point(p: Coord, rx: int, ry: int, rz: int) -> Coord:
    """Rotate point p by rx, ry, rz steps (each step = 90 degrees) around X, Y, Z axes about the origin.

    rx, ry, rz are integers (can be negative); rotation is applied X, then Y, then Z.
    """
    x, y, z = p

    def rot_x(a):
        # (x, y, z) -> (x, -z, y)
        return (a[0], -a[2], a[1])

    def rot_y(a):
        # (x, y, z) -> (z, y, -x)
        return (a[2], a[1], -a[0])

    def rot_z(a):
        # (x, y, z) -> (-y, x, z)
        return (-a[1], a[0], a[2])

    a = (x, y, z)
    for _ in range(rx % 4):
        a = rot_x(a)
    for _ in range(ry % 4):
        a = rot_y(a)
    for _ in range(rz % 4):
        a = rot_z(a)
    return a


class Brick:
    """A brick is a set of 4 cube coordinates relative to an origin.

    Example shapes are provided in `sample_bricks()`.
    """

    def __init__(self, cubes: List[Coord], name: str = ""):
        if len(cubes) != 4:
            raise ValueError("Each brick must consist of exactly 4 cubes")
        self.cubes = list(cubes)
        self.name = name or "brick"        

    def rotated(self, rx: int, ry: int, rz: int) -> "Brick":
        return Brick([rotate_point(c, rx, ry, rz) for c in self.cubes], name=self.name)

    def normalized(self) -> "Brick":
        # shift so min coord is at origin
        xs, ys, zs = zip(*self.cubes)
        minx, miny, minz = min(xs), min(ys), min(zs)
        return Brick([(x - minx, y - miny, z - minz) for x, y, z in self.cubes], name=self.name)


class CubeGrid:
    def __init__(self, size: int = 6):
        self.size = size
        self.grid = np.zeros((size, size, size), dtype=int)  # 0 = empty, >0 = brick id
        self.next_id = 1
        self.placed: Dict[int, Tuple[int, Brick, Coord]] = {}  # id -> (placement_id, brick, position)
        self.bricks = {
            # T-shape
            'T': Brick([(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)], name='T'),
            # straight line of 4
            'I': Brick([(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)], name='I'),
            # L-shape: 3 in a line + one attached at end
            'L': Brick([(0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0)], name='L'),
            # square 2x2 (flat)
            'O': Brick([(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)], name='O'),
            # a small 3D hook
            'S3D': Brick([(0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1)], name='S3D')
        } 
        self.valid_placements = {
            'T': set(),
            'I': set(),
            'L': set(),
            'O': set(),
            'S3D': set()
        }
        self.valid_rotations = {
            'T': set(),
            'I': set(),
            'L': set(),
            'O': set(),
            'S3D': set()
        }
        
        for brick in self.bricks.values():
            all_rotations = set()
            for rx in range(4):
                for ry in range(4):
                    for rz in range(4):
                        b = brick.rotated(rx, ry, rz).normalized()
                        all_rotations.add(b)
            self.valid_rotations[brick.name] = all_rotations

            for x in range(self.size):
                for y in range(self.size):
                    for z in range(self.size):
                        ok_place = False
                        for b in all_rotations:
                            if self.can_place(b, (x, y, z)):
                                ok_place = True
                                break
                        if ok_place:
                            self.valid_placements[brick.name].add((x, y, z))
    
    def bricks(self) -> Dict[str, Brick]:
        return self.bricks
    
    def clear(self):
        self.grid.fill(0)
        self.next_id = 1
        self.placed.clear()

    def can_place(self, brick: Brick, pos: Coord) -> bool:
        for cx, cy, cz in brick.cubes:
            x, y, z = pos[0] + cx, pos[1] + cy, pos[2] + cz
            if not (0 <= x < self.size and 0 <= y < self.size and 0 <= z < self.size):
                return False
            if self.grid[x, y, z] != 0:
                return False
        return True

    def place(self, brick: Brick, pos: Coord) -> int:
        """Place brick at pos if fits. Returns placement id or raises ValueError."""
        if not self.can_place(brick, pos):
            raise ValueError("Brick does not fit at position or overlaps")
        pid = self.next_id
        for cx, cy, cz in brick.cubes:
            x, y, z = pos[0] + cx, pos[1] + cy, pos[2] + cz
            self.grid[x, y, z] = pid
        self.placed[pid] = (pid, brick, pos)
        self.next_id += 1
        return pid

    def remove(self, placement_id: int) -> None:
        if placement_id not in self.placed:
            raise KeyError("placement id not found")
        pid, brick, pos = self.placed.pop(placement_id)
        for cx, cy, cz in brick.cubes:
            x, y, z = pos[0] + cx, pos[1] + cy, pos[2] + cz
            self.grid[x, y, z] = 0

    def to_dict(self) -> Dict:
        """Serialize the CubeGrid to a JSON-serializable dict."""
        placed = []
        for pid, (pid2, brick, pos) in self.placed.items():
            placed.append({
                'pid': pid,
                'name': brick.name,
                'cubes': [[int(c) for c in coord] for coord in brick.cubes],
                'pos': [int(p) for p in pos],
            })
        return {
            'size': int(self.size),
            'next_id': int(self.next_id),
            'placed': placed,
        }

    def save_to_file(self, path: str) -> None:
        """Save the grid state to a JSON file at `path`."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    def load_from_file(self, path: str) -> None:
        """Load the grid state from a JSON file at `path`, replacing current state."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        size = int(data.get('size', 6))
        # reinitialize grid
        self.size = size
        self.grid = np.zeros((size, size, size), dtype=int)
        self.placed = {}
        max_pid = 0
        for item in data.get('placed', []):
            pid = int(item['pid'])
            name = item.get('name', '')
            cubes = [tuple(int(c) for c in coord) for coord in item['cubes']]
            pos = tuple(int(p) for p in item['pos'])
            brick = Brick(cubes, name=name)
            # set grid cells
            for cx, cy, cz in brick.cubes:
                x, y, z = pos[0] + cx, pos[1] + cy, pos[2] + cz
                self.grid[x, y, z] = pid
            self.placed[pid] = (pid, brick, pos)
            if pid > max_pid:
                max_pid = pid
        self.next_id = int(data.get('next_id', max_pid + 1))

    def can_move(self, placement_id: int, new_pos: Coord) -> bool:
        """Return True if the placed brick can be moved to new_pos without collisions or going out of bounds.

        This treats the bricks currently occupied by `placement_id` as free (so the brick can move into an overlapping
        area that it currently occupies while shifting).
        """
        if placement_id not in self.placed:
            return False
        _, brick, _ = self.placed[placement_id]
        for cx, cy, cz in brick.cubes:
            x, y, z = new_pos[0] + cx, new_pos[1] + cy, new_pos[2] + cz
            if not (0 <= x < self.size and 0 <= y < self.size and 0 <= z < self.size):
                return False
            occ = self.grid[x, y, z]
            if occ != 0 and occ != placement_id:
                return False
        return True

    def move(self, placement_id: int, new_pos: Coord) -> None:
        """Move the placed brick to new_pos if possible; raises ValueError on failure."""
        if placement_id not in self.placed:
            raise KeyError("placement id not found")
        if not self.can_move(placement_id, new_pos):
            raise ValueError("cannot move to the requested position (out of bounds or overlap)")
        pid, brick, old_pos = self.placed[placement_id]
        # clear old positions
        for cx, cy, cz in brick.cubes:
            x, y, z = old_pos[0] + cx, old_pos[1] + cy, old_pos[2] + cz
            self.grid[x, y, z] = 0
        # set new positions
        for cx, cy, cz in brick.cubes:
            x, y, z = new_pos[0] + cx, new_pos[1] + cy, new_pos[2] + cz
            self.grid[x, y, z] = pid
        # update record
        self.placed[placement_id] = (pid, brick, new_pos)

    def num_left(self) -> int:
        # Check if all positions are filled
        num = 0
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    if self.grid[x, y, z] == 0:
                        num += 1
        return num

    def validate_placements(self, brick: Brick) -> List[Brick, Coord]:
        placements = []   
        empties = set()
        for place in self.valid_placements.get(brick.name, set()):
            x, y, z = place
            if self.grid[x, y, z] == 0:
                empties.add((x, y, z))

        # quick reject
        if not empties:
            return placements

        rotations = self.valid_rotations.get(brick.name, set())
        for e in empties:
            for b in rotations:
                if self.can_place(b, e):
                    placements.append((b, e))
        return placements

    def can_not_place_somewhere(self, brick: Brick):
        # Default behavior: check empty connected volumes and return True
        # if the brick can be placed entirely inside any empty connected
        # component (this examines all empty spaces).
                        
        empties = set()
        for place in self.valid_placements.get(brick.name, set()):
            x, y, z = place
            if self.grid[x, y, z] == 0:
                empties.add((x, y, z))

        # quick reject
        if not empties:
            return False

        rotations = self.valid_rotations.get(brick.name, set())
        for e in empties:
            is_ok=False
            for b in rotations:
                is_ok = self.can_place(b, e)
                if is_ok:
                    break
            if not is_ok:
                print(f"can not place {brick.name} at {e} with some rotation")
                return True
        return False


    def show(self) -> None:
        # We'll use matplotlib voxels. Convert grid->bool and facecolors
        filled = self.grid != 0
        # simple color map by placement id
        unique_ids = np.unique(self.grid[self.grid != 0])
        colors = {}
        cmap = plt.get_cmap("tab20")
        for i, pid in enumerate(unique_ids):
            colors[pid] = cmap(i % 20)

        facecolors = np.empty(filled.shape + (4,), dtype=float)
        facecolors[:] = (0, 0, 0, 0)
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    pid = self.grid[x, y, z]
                    if pid != 0:
                        facecolors[x, y, z] = colors.get(pid, (0.5, 0.5, 0.5, 1.0))

        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection="3d")
        # matplotlib expects the array indexed as (x,y,z) with x as first axis
        ax.voxels(filled, facecolors=facecolors, edgecolor='k')
        ax.set_xlim(0, self.size)
        ax.set_ylim(0, self.size)
        ax.set_zlim(0, self.size)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.title(f"6x6x6 Grid — {len(unique_ids)} bricks placed")
        plt.tight_layout()
        plt.show()


def sample_bricks() -> Dict[str, Brick]:
    """Return a few sample 4-cube bricks (polycubes of 4). Coordinates chosen small and easy to rotate."""
    bricks = {
        # T-shape
        'T': Brick([(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)], name='T'),
        # straight line of 4
        'I': Brick([(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)], name='I'),
        # L-shape: 3 in a line + one attached at end
        'L': Brick([(0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0)], name='L'),
        # square 2x2 (flat)
        'O': Brick([(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)], name='O'),
        # a small 3D hook
        'S3D': Brick([(0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1)], name='S3D')
    }
    return bricks


def parse_ints(parts: List[str]) -> List[int]:
    try:
        return [int(p) for p in parts]
    except Exception:
        raise ValueError("expected integers")


def repl():
    grid = CubeGrid(size=6)
    bricks = sample_bricks()

    banner = "6x6x6 Brick Presenter — enter commands (type 'help' for usage)"
    print(banner)
    print("Available bricks: ", ", ".join(sorted(bricks.keys())))

    while True:
        try:
            line = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nexiting')
            return
        if not line:
            continue
        parts = line.split()
        cmd = parts[0].lower()
        try:
            if cmd == 'help':
                print("Commands:\n  add <brick_id> x y z rx ry rz\n  show\n  list\n  reset\n  exit")
            elif cmd == 'list':
                print("Available bricks:")
                for k, b in bricks.items():
                    print(f"  {k}: {b.cubes}")
            elif cmd == 'reset':
                grid.clear()
                print("grid cleared")
            elif cmd == 'show':
                grid.show()
            elif cmd == 'add':
                if len(parts) != 8:
                    print("Usage: add <brick_id> x y z rx ry rz")
                    continue
                bid = parts[1]
                if bid not in bricks:
                    print(f"unknown brick id '{bid}', use 'list' to see ids")
                    continue
                ints = parse_ints(parts[2:])
                x, y, z, rx, ry, rz = ints
                # rotate brick then normalize then attempt to place at (x,y,z)
                b = bricks[bid].rotated(rx, ry, rz).normalized()
                if grid.can_place(b, (x, y, z)):
                    pid = grid.place(b, (x, y, z))
                    print(f"placed {bid} as id {pid}")
                else:
                    print("cannot place brick at that position (out of bounds or overlap)")
            elif cmd == 'exit' or cmd == 'quit':
                print('bye')
                return
            else:
                print('unknown command; type help')
        except Exception as e:
            print('error:', e)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('--demo', 'demo'):
        # quick demo: place a few bricks automatically and show
        g = CubeGrid(size=6)
        b = sample_bricks()
        try:
            g.place(b['O'], (0, 0, 0))
            g.place(b['I'].rotated(0, 0, 1).normalized(), (0, 2, 0))
            g.place(b['L'].rotated(0, 1, 0).normalized(), (3, 0, 0))
        except Exception as e:
            print('demo placement problem:', e)
        g.show()
    else:
        repl()
