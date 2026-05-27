"""
pathfinder.py — Sistem Pathfinding A* untuk Lembah Karsa 3D
Diadaptasi dari VMRectRouter + VMObstacleSet (FreeSO, C#) ke Python/Ursina.

KONSEP UTAMA:
- Grid berbasis tile (sama seperti FreeSO tapi disederhanakan)
- A* dengan 8 arah (termasuk diagonal)
- Obstacle bisa berupa tile, rectangle, atau entitas
- Path dikembalikan sebagai list titik dunia (Vec3 Ursina)
- PathMover mengurus pergerakan smooth entitas sepanjang path

CONTOH PEMAKAIAN:
    from pathfinder import PathGrid, PathMover
    from ursina import Vec3

    grid = PathGrid(width=20, height=20, tile_size=1.0)
    grid.set_obstacle(5, 5)        # tandai tile (5,5) tidak bisa dilewati
    grid.set_obstacle_rect(3,3,6,4) # tandai area persegi

    path = grid.find_path((0, 0), (15, 12))

    # Integrasikan ke entitas Ursina
    mover = PathMover(my_entity, grid, speed=3.0)
    mover.move_to(Vec3(15, 0, 12))

    # Panggil di update():
    def update():
        mover.update(time.dt)
"""

from __future__ import annotations
import heapq
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Set, Dict


# ---------------------------------------------------------------------------
# Tipe alias
# ---------------------------------------------------------------------------
GridPos = Tuple[int, int]       # (col, row) dalam grid
WorldPos = Tuple[float, float]  # (x, z) dalam koordinat dunia


# ---------------------------------------------------------------------------
# Satu tile di grid
# ---------------------------------------------------------------------------
@dataclass
class Tile:
    col: int
    row: int
    walkable: bool = True
    cost: float = 1.0           # biaya melewati tile ini (1.0 = normal, >1 = lambat)


# ---------------------------------------------------------------------------
# Node A* internal
# ---------------------------------------------------------------------------
@dataclass(order=True)
class AStarNode:
    f: float
    g: float = field(compare=False)
    pos: GridPos = field(compare=False)
    parent: Optional["AStarNode"] = field(default=None, compare=False)


# ---------------------------------------------------------------------------
# Grid pathfinding utama
# ---------------------------------------------------------------------------
class PathGrid:
    """
    Grid tile walkable/obstacle dengan A*.
    Diadaptasi dari VMObstacleSet (k-d tree) + VMRectRouter (A*) FreeSO.
    Untuk Lembah Karsa, versi ini menggunakan grid 2D biasa (cocok untuk 3D isometrik).
    """

    # 8 arah: kardinal + diagonal
    DIRECTIONS_8 = [
        (0, 1), (0, -1), (1, 0), (-1, 0),   # N S E W
        (1, 1), (1, -1), (-1, 1), (-1, -1),  # NE SE NW SW
    ]
    DIRECTIONS_4 = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def __init__(self, width: int, height: int, tile_size: float = 1.0,
                 allow_diagonal: bool = True):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.allow_diagonal = allow_diagonal
        self._grid: Dict[GridPos, Tile] = {}
        self._dynamic_obstacles: Set[GridPos] = set()  # obstacle bisa bergerak (NPC lain)

    # -- Akses tile --
    def get_tile(self, col: int, row: int) -> Tile:
        if (col, row) not in self._grid:
            self._grid[(col, row)] = Tile(col, row)
        return self._grid[(col, row)]

    def is_valid(self, col: int, row: int) -> bool:
        return 0 <= col < self.width and 0 <= row < self.height

    def is_walkable(self, col: int, row: int) -> bool:
        if not self.is_valid(col, row):
            return False
        if (col, row) in self._dynamic_obstacles:
            return False
        return self.get_tile(col, row).walkable

    # -- Set obstacle --
    def set_obstacle(self, col: int, row: int, walkable: bool = False):
        self.get_tile(col, row).walkable = walkable

    def set_obstacle_rect(self, c1: int, r1: int, c2: int, r2: int, walkable: bool = False):
        """Tandai seluruh persegi (c1,r1)-(c2,r2) sebagai obstacle."""
        for c in range(min(c1, c2), max(c1, c2) + 1):
            for r in range(min(r1, r2), max(r1, r2) + 1):
                self.set_obstacle(c, r, walkable)

    def set_tile_cost(self, col: int, row: int, cost: float):
        """Atur biaya tile (misal: lumpur = 2.0, jalan = 0.5)."""
        self.get_tile(col, row).cost = max(0.1, cost)

    # -- Dynamic obstacles (NPC lain) --
    def add_dynamic_obstacle(self, col: int, row: int):
        self._dynamic_obstacles.add((col, row))

    def remove_dynamic_obstacle(self, col: int, row: int):
        self._dynamic_obstacles.discard((col, row))

    def clear_dynamic_obstacles(self):
        self._dynamic_obstacles.clear()

    # -- Konversi koordinat --
    def world_to_grid(self, x: float, z: float) -> GridPos:
        col = int(x / self.tile_size)
        row = int(z / self.tile_size)
        return (
            max(0, min(self.width - 1, col)),
            max(0, min(self.height - 1, row))
        )

    def grid_to_world(self, col: int, row: int) -> WorldPos:
        return (
            col * self.tile_size + self.tile_size * 0.5,
            row * self.tile_size + self.tile_size * 0.5
        )

    # -- Heuristik --
    def _heuristic(self, a: GridPos, b: GridPos) -> float:
        if self.allow_diagonal:
            # Octile distance — akurat untuk 8 arah
            dx = abs(a[0] - b[0])
            dy = abs(a[1] - b[1])
            return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
        else:
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _move_cost(self, dc: int, dr: int, cost: float) -> float:
        if dc != 0 and dr != 0:
            return math.sqrt(2) * cost  # diagonal lebih jauh
        return cost

    # -- A* utama --
    def find_path(self, start: GridPos, goal: GridPos) -> Optional[List[GridPos]]:
        """
        Cari path dari start ke goal.
        Return: list GridPos dari start ke goal, atau None kalau tidak ada path.
        """
        if not self.is_walkable(*goal):
            goal = self._nearest_walkable(goal, start)
            if goal is None:
                return None

        if start == goal:
            return [start]

        open_heap: List[AStarNode] = []
        open_set: Dict[GridPos, AStarNode] = {}
        closed_set: Set[GridPos] = set()

        start_node = AStarNode(f=self._heuristic(start, goal), g=0.0, pos=start)
        heapq.heappush(open_heap, start_node)
        open_set[start] = start_node

        directions = self.DIRECTIONS_8 if self.allow_diagonal else self.DIRECTIONS_4

        while open_heap:
            current = heapq.heappop(open_heap)

            if current.pos in closed_set:
                continue

            if current.pos == goal:
                return self._reconstruct_path(current)

            closed_set.add(current.pos)

            for dc, dr in directions:
                nc, nr = current.pos[0] + dc, current.pos[1] + dr
                neighbor = (nc, nr)

                if not self.is_walkable(nc, nr):
                    continue
                if neighbor in closed_set:
                    continue

                # Hindari memotong sudut obstacle saat diagonal
                if dc != 0 and dr != 0:
                    if not self.is_walkable(current.pos[0] + dc, current.pos[1]):
                        continue
                    if not self.is_walkable(current.pos[0], current.pos[1] + dr):
                        continue

                tile_cost = self.get_tile(nc, nr).cost
                move_cost = self._move_cost(dc, dr, tile_cost)
                new_g = current.g + move_cost
                h = self._heuristic(neighbor, goal)
                new_f = new_g + h

                if neighbor in open_set and open_set[neighbor].g <= new_g:
                    continue

                node = AStarNode(f=new_f, g=new_g, pos=neighbor, parent=current)
                heapq.heappush(open_heap, node)
                open_set[neighbor] = node

        return None  # tidak ada path

    def find_path_world(self, start_world: WorldPos, goal_world: WorldPos
                        ) -> Optional[List[WorldPos]]:
        """Versi langsung pakai koordinat dunia (x, z)."""
        start = self.world_to_grid(*start_world)
        goal = self.world_to_grid(*goal_world)
        grid_path = self.find_path(start, goal)
        if grid_path is None:
            return None
        return [self.grid_to_world(*p) for p in grid_path]

    def _reconstruct_path(self, node: AStarNode) -> List[GridPos]:
        path = []
        current = node
        while current is not None:
            path.append(current.pos)
            current = current.parent
        path.reverse()
        return path

    def _nearest_walkable(self, pos: GridPos, preferred_near: GridPos,
                           max_radius: int = 5) -> Optional[GridPos]:
        """Cari tile walkable terdekat dari pos."""
        best = None
        best_dist = float("inf")
        for r in range(1, max_radius + 1):
            for dc in range(-r, r + 1):
                for dr in range(-r, r + 1):
                    if abs(dc) != r and abs(dr) != r:
                        continue
                    candidate = (pos[0] + dc, pos[1] + dr)
                    if self.is_walkable(*candidate):
                        dist = self._heuristic(candidate, preferred_near)
                        if dist < best_dist:
                            best_dist = dist
                            best = candidate
            if best is not None:
                return best
        return None

    # -- Path smoothing (line-of-sight pruning) --
    def smooth_path(self, path: List[GridPos]) -> List[GridPos]:
        """
        Hapus waypoint yang tidak diperlukan menggunakan line-of-sight.
        Diadaptasi dari OptimizeLines() di VMRectRouter FreeSO.
        """
        if len(path) <= 2:
            return path

        smoothed = [path[0]]
        i = 0
        while i < len(path) - 1:
            j = len(path) - 1
            while j > i + 1:
                if self._has_line_of_sight(path[i], path[j]):
                    break
                j -= 1
            smoothed.append(path[j])
            i = j

        return smoothed

    def _has_line_of_sight(self, a: GridPos, b: GridPos) -> bool:
        """Bresenham line — cek apakah ada garis lurus tanpa obstacle."""
        x0, y0 = a
        x1, y1 = b
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if not self.is_walkable(x0, y0):
                return False
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        return True


# ---------------------------------------------------------------------------
# PathMover — menggerakkan entitas Ursina sepanjang path
# ---------------------------------------------------------------------------
class PathMover:
    """
    Komponen untuk menggerakkan entitas Ursina mengikuti path.
    Terinspirasi dari VMRoutingFrame di FreeSO.

    Integrasi Ursina:
        mover = PathMover(my_entity, grid, speed=3.0)
        mover.move_to(Vec3(10, 0, 8))
        # Di update():
        mover.update(time.dt)
    """

    def __init__(self, entity, grid: PathGrid, speed: float = 3.0,
                 y_position: float = 0.0):
        self.entity = entity         # Ursina Entity
        self.grid = grid
        self.speed = speed
        self.y_position = y_position  # tinggi Y tetap di 3D
        self._path: List[WorldPos] = []
        self._path_index: int = 0
        self._moving: bool = False
        self._on_arrive: Optional[callable] = None
        self._on_step: Optional[callable] = None
        self._turn_speed: float = 8.0

    @property
    def is_moving(self) -> bool:
        return self._moving

    def move_to(self, target, smooth: bool = True):
        """
        Minta entitas bergerak ke titik tujuan.
        target: bisa WorldPos tuple (x,z) atau Ursina Vec3
        """
        # Support Vec3 Ursina
        if hasattr(target, 'x'):
            tx, tz = target.x, target.z
        else:
            tx, tz = target

        # Posisi entitas saat ini
        if hasattr(self.entity, 'x'):
            ex, ez = self.entity.x, self.entity.z
        else:
            ex, ez = 0, 0

        path = self.grid.find_path_world((ex, ez), (tx, tz))
        if path is None:
            print(f"[PathMover] Tidak ada path ke ({tx}, {tz})")
            return False

        if smooth:
            grid_path = self.grid.find_path(
                self.grid.world_to_grid(ex, ez),
                self.grid.world_to_grid(tx, tz)
            )
            if grid_path:
                grid_path = self.grid.smooth_path(grid_path)
                path = [self.grid.grid_to_world(*p) for p in grid_path]

        self._path = path
        self._path_index = 0
        self._moving = True
        return True

    def on_arrive(self, callback):
        """Callback saat sampai tujuan."""
        self._on_arrive = callback

    def on_step(self, callback):
        """Callback tiap pindah ke waypoint baru."""
        self._on_step = callback

    def stop(self):
        self._moving = False
        self._path = []

    def update(self, dt: float):
        """Panggil ini tiap frame di Ursina update()."""
        if not self._moving or not self._path:
            return

        if self._path_index >= len(self._path):
            self._moving = False
            if self._on_arrive:
                self._on_arrive()
            return

        # Target waypoint saat ini
        wx, wz = self._path[self._path_index]

        # Posisi entitas (Ursina Vec3)
        if hasattr(self.entity, 'x'):
            ex, ey, ez = self.entity.x, self.entity.y, self.entity.z
        else:
            ex, ey, ez = 0, 0, 0

        dx = wx - ex
        dz = wz - ez
        dist = math.sqrt(dx * dx + dz * dz)

        if dist < 0.05:
            # Sampai di waypoint ini, lanjut ke berikutnya
            self._path_index += 1
            if self._on_step:
                self._on_step(self._path_index)
            return

        # Gerak menuju waypoint
        move = self.speed * dt
        ratio = min(move / dist, 1.0)

        if hasattr(self.entity, 'x'):
            self.entity.x += dx * ratio
            self.entity.y = self.y_position
            self.entity.z += dz * ratio

        # Rotasi menghadap arah gerak
        if dist > 0.01:
            target_angle = math.degrees(math.atan2(dx, dz))
            if hasattr(self.entity, 'rotation_y'):
                current_angle = self.entity.rotation_y
                diff = ((target_angle - current_angle + 180) % 360) - 180
                self.entity.rotation_y += diff * min(self._turn_speed * dt, 1.0)

    @property
    def progress(self) -> float:
        """0.0 = awal, 1.0 = sudah sampai."""
        if not self._path:
            return 1.0
        return self._path_index / len(self._path)


# ---------------------------------------------------------------------------
# TEST / DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Demo PathGrid Lembah Karsa ===\n")

    grid = PathGrid(width=15, height=15, tile_size=1.0)

    # Buat tembok di tengah
    grid.set_obstacle_rect(5, 2, 5, 10)
    grid.set_obstacle_rect(3, 7, 8, 7)
    grid.set_tile_cost(4, 5, 2.5)  # lumpur — lambat

    start = (0, 0)
    goal  = (13, 13)

    path = grid.find_path(start, goal)
    if path:
        smooth = grid.smooth_path(path)
        print(f"Path ditemukan: {len(path)} langkah")
        print(f"Setelah smoothing: {len(smooth)} waypoint")
        print(f"Waypoint: {smooth[:6]}{'...' if len(smooth)>6 else ''}")
    else:
        print("Tidak ada path!")

    world_path = grid.find_path_world((0.5, 0.5), (13.5, 13.5))
    if world_path:
        print(f"\nKoordinat dunia: {world_path[:3]}...")

    print("\n=== Grid visual (. = bisa, # = obstacle) ===")
    for r in range(15):
        row_str = ""
        for c in range(15):
            if not grid.is_walkable(c, r):
                row_str += "# "
            elif (c, r) == start:
                row_str += "S "
            elif (c, r) == goal:
                row_str += "G "
            elif path and (c, r) in path:
                row_str += "* "
            else:
                row_str += ". "
        print(row_str)
