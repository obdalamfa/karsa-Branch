"""
dungeon.py — Random roguelike dungeon generator.
Port dari v17 — algoritma identik, tidak bergantung pada rendering.

Return value generate_dungeon_level():
  (grid_2d, spawn_x, spawn_y, mob_specs_list)

grid_2d  : list[list[int]] tile IDs (24×18)
spawn_x/y: tile koordinat awal player
mob_specs: list dict {kind, x, y, hp, max_hp, damage, speed, drops, xp, is_boss, ...}
"""
import random
from .config import (CV_W, CV_F, MINED, ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH,
                     STAIRS_DOWN, STAIRS_UP, CRYS, D, W, DCK, LLY)
from .data import MOB_TEMPLATES, BHUTAKALA_BOSS, DUNGEON_MAX_LEVEL

ORE_SPAWN_TABLE = {
    1:  [(ORE_TBG, 8),  (CV_W, 92)],
    2:  [(ORE_TBG, 10), (CV_W, 90)],
    3:  [(ORE_TBG, 8),  (ORE_BSI, 4),  (CV_W, 88)],
    4:  [(ORE_TBG, 6),  (ORE_BSI, 6),  (ORE_KRS, 2),  (CV_W, 86)],
    5:  [(ORE_TBG, 5),  (ORE_BSI, 8),  (ORE_KRS, 3),  (CV_W, 84)],
    6:  [(ORE_BSI, 8),  (ORE_EMS, 3),  (ORE_KRS, 4),  (CV_W, 85)],
    7:  [(ORE_BSI, 7),  (ORE_EMS, 4),  (ORE_KRS, 5),  (CV_W, 84)],
    8:  [(ORE_BSI, 5),  (ORE_EMS, 6),  (ORE_KRS, 5),  (CV_W, 84)],
    9:  [(ORE_EMS, 7),  (ORE_KRS, 6),  (ORE_BSI, 3),  (CV_W, 84)],
    10: [(ORE_EMS, 6),  (ORE_MTH, 2),  (ORE_KRS, 5),  (CV_W, 87)],
    11: [(ORE_EMS, 5),  (ORE_MTH, 4),  (ORE_KRS, 5),  (CV_W, 86)],
    12: [(ORE_EMS, 4),  (ORE_MTH, 6),  (CRYS, 4),     (CV_W, 86)],
    13: [(ORE_MTH, 8),  (ORE_EMS, 3),  (CRYS, 5),     (CV_W, 84)],
    14: [(ORE_MTH, 10), (CRYS, 8),     (ORE_EMS, 2),  (CV_W, 80)],
    15: [(CRYS, 15),    (ORE_MTH, 8),  (CV_W, 77)],
}


def _weighted_choice(rng, options):
    total = sum(w for _, w in options)
    r = rng.random() * total
    cum = 0
    for item, w in options:
        cum += w
        if r <= cum:
            return item
    return options[-1][0]


def _cellular_automata_step(grid, w, h):
    new_grid = [row[:] for row in grid]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            wall_count = sum(
                1 for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                if grid[y + dy][x + dx] == CV_W
            )
            new_grid[y][x] = CV_W if wall_count >= 5 else CV_F
    return new_grid


def generate_dungeon_level(level, seed=None):
    """Generate satu level dungeon.
    Return (grid, spawn_x, spawn_y, mob_specs).
    """
    if seed is None:
        seed = random.randint(0, 999999)
    rng = random.Random(seed)
    w, h = 24, 18

    # Boss Arena (Level 13)
    if level == DUNGEON_MAX_LEVEL:
        grid = [[CV_F]*w for _ in range(h)]
        for x in range(w): grid[0][x] = CV_W; grid[h-1][x] = CV_W
        for y in range(h): grid[y][0] = CV_W; grid[y][w-1] = CV_W
        
        # Danau Legendaris (Legendary Lake) di ujung utara arena
        for y in range(1, 6):
            for x in range(4, w-4):
                grid[y][x] = W
        
        # Jembatan kayu kecil menuju air
        grid[5][11] = DCK
        grid[5][12] = DCK
        grid[4][11] = DCK
        grid[4][12] = DCK
        grid[3][10] = LLY
        grid[2][15] = LLY
        
        # Player spawn at bottom center
        spawn_x, spawn_y = w//2, h - 3
        grid[spawn_y][spawn_x] = STAIRS_UP
        
        bx, by = w//2, 8
        mob_specs = [{
            'kind': 'bhutakala',
            'x': float(bx), 'y': float(by),
            'hp': BHUTAKALA_BOSS['hp'], 'max_hp': BHUTAKALA_BOSS['hp'],
            'damage': BHUTAKALA_BOSS['damage'], 'speed': BHUTAKALA_BOSS['speed'],
            'drops': dict(BHUTAKALA_BOSS['drops']), 'xp': 500,
            'is_boss': True,
            'target_x': float(bx), 'target_y': float(by),
            'dmg_flash_ms': 0, 'attack_cooldown_ms': 0,
        }]
        return grid, spawn_x, spawn_y, mob_specs

    # Phase 1: Random fill (45% wall)
    grid = [[CV_W if rng.random() < 0.45 else CV_F for _ in range(w)] for _ in range(h)]
    for x in range(w):
        grid[0][x] = CV_W; grid[h - 1][x] = CV_W
    for y in range(h):
        grid[y][0] = CV_W; grid[y][w - 1] = CV_W

    # Phase 2: 4x cellular automata smoothing
    for _ in range(4):
        grid = _cellular_automata_step(grid, w, h)

    # Phase 3: Replace wall tiles dengan ore (weighted)
    spawn_table = ORE_SPAWN_TABLE.get(level, ORE_SPAWN_TABLE[1])
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if grid[y][x] == CV_W:
                grid[y][x] = _weighted_choice(rng, spawn_table)

    # Phase 4: Kumpulkan semua floor cells
    floor_cells = [(x, y) for y in range(1, h - 1) for x in range(1, w - 1)
                   if grid[y][x] == CV_F]
    if not floor_cells:
        cx, cy = w // 2, h // 2
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                grid[cy + dy][cx + dx] = CV_F
        floor_cells = [(cx + dx, cy + dy) for dy in range(-2, 3) for dx in range(-2, 3)]

    # Phase 5: Tempatkan STAIRS_UP di sebelah player + clear 3x3
    spawn_x, spawn_y = rng.choice(floor_cells)
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            nx, ny = spawn_x + dx, spawn_y + dy
            if 0 < nx < w - 1 and 0 < ny < h - 1:
                if grid[ny][nx] != CV_F:
                    grid[ny][nx] = CV_F
    
    up_x, up_y = spawn_x, spawn_y - 1
    if up_y < 1: up_y = spawn_y + 1
    grid[up_y][up_x] = STAIRS_UP

    # Phase 6: STAIRS_DOWN (kecuali boss level)
    if level < DUNGEON_MAX_LEVEL:
        far_cells = [c for c in floor_cells
                     if abs(c[0] - spawn_x) + abs(c[1] - spawn_y) >= 8]
        dest = rng.choice(far_cells if far_cells else floor_cells)
        grid[dest[1]][dest[0]] = STAIRS_DOWN

    # Phase 7: Spawn mobs
    mob_specs = []
    eligible = [k for k, m in MOB_TEMPLATES.items()
                if m['min_lvl'] <= level <= m['max_lvl']]
    n_mobs = min(3 + level // 2, 8)
    avail = [c for c in floor_cells
             if (c[0], c[1]) != (spawn_x, spawn_y)
             and abs(c[0] - spawn_x) + abs(c[1] - spawn_y) >= 4]
    rng.shuffle(avail)
    for i in range(min(n_mobs, len(avail))):
        mx, my = avail[i]
        kind = rng.choice(eligible)
        tmpl = MOB_TEMPLATES[kind]
        mob_specs.append({
            'kind': kind,
            'x': float(mx), 'y': float(my),
            'hp': tmpl['hp'], 'max_hp': tmpl['hp'],
            'damage': tmpl['damage'], 'speed': tmpl['speed'],
            'drops': dict(tmpl['drops']), 'xp': tmpl['xp'],
            'is_boss': False,
            'target_x': float(mx), 'target_y': float(my),
            'dmg_flash_ms': 0, 'attack_cooldown_ms': 0,
        })

    return grid, spawn_x, spawn_y, mob_specs


def random_stairs_chance(level, rng=None):
    if rng is None:
        rng = random
    if level >= DUNGEON_MAX_LEVEL:
        return False
    chance = 0.30 + min(0.20, level * 0.02)
    return rng.random() < chance
