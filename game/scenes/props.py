from game.config import *
from game.config import SHOP_EXT, CLINIC_EXT, SMITH_EXT, GREENHOUSE_EXT
from ursina import color
import math
import random

TS = TILE_SIZE

# ─── PALET WARNA LEMBAH KARSA (Decay Tropical / Disco Elysium style) ─────────
# Seng berkarat & material lapuk — menggantikan palette cerah sebelumnya
ROOF_TEXTURES = [
    ('roof/metal_h',         color.rgb(148, 125,  98)),   # seng usang
    ('roof/asphaltshingle1', color.rgb( 95,  88,  82)),   # aspal gelap
    ('roof/asphaltshingle3', color.rgb(112, 102,  90)),   # aspal cokelat
    ('roof/composite_tan',   color.rgb(130, 105,  72)),   # coklat lapuk
    ('roof/composite_green', color.rgb( 72,  98,  72)),   # seng hijau lumut
    ('roof/slate_h',         color.rgb( 88,  95, 108)),   # batu abu
    ('roof/blacktile1',      color.rgb( 52,  48,  52)),   # seng hitam tua
    ('roof/metal_h',         color.rgb(162, 108,  68)),   # seng karat oranye
    ('roof/composite_light', color.rgb(145, 138, 120)),   # seng pudar
    ('roof/composite_sea',   color.rgb( 78, 112, 108)),   # seng kehijauan lembab
    ('roof/composite_red',   color.rgb(148,  75,  58)),   # seng merah berkarat
    ('roof/asphaltshingle1', color.rgb( 82,  78,  68)),   # bitumen gelap
]

# ─── WARNA MATERIAL DASAR ─────────────────────────────────────────────────────
# Mid-tone yang masih kusam/decay TAPI kebaca di bawah pencahayaan overcast.
# (Sebelumnya terlalu gelap → bangunan jadi slab hitam.)
C_CONCRETE      = color.rgb(178, 170, 158)   # beton blok abu pudar
C_CONCRETE_DARK = color.rgb(132, 125, 114)   # beton dalam bayangan (aksen)
C_WOOD_OLD      = color.rgb(148, 112,  72)   # kayu lapuk
C_WOOD_DARK     = color.rgb(112,  82,  50)   # kayu gelap, tua (aksen)
C_MOLD          = color.rgb( 88, 118,  82)   # jamur/lumut tropis
C_RUST          = color.rgb(178, 118,  68)   # karat logam
C_STAIN         = color.rgb(102,  96,  86)   # noda air/lumpur
C_PLYWOOD       = color.rgb(192, 162, 118)   # tripleks kecoklatan
C_PLASTIC       = color.rgb(172, 178, 162)   # plastik pudar
C_ROPE          = color.rgb(198, 172, 122)   # tali manila usang


def _hash(x, z):
    """Deterministic pseudo-random float 0-1 dari posisi tile."""
    return abs(math.sin(x * 31.7 + z * 47.3 + x * z * 0.13))


# ─── LOADER ASET KIT (CC0 Kenney/Quaternius) — cache ──────────────────────────
_KIT_MODEL_CACHE = {}
def _kit_model(name):
    """Muat model .glb/.obj dari assets/models (None bila tak ada). Untuk drop-in aset."""
    if name in _KIT_MODEL_CACHE:
        return _KIT_MODEL_CACHE[name]
    m = None
    try:
        from game.entities import load_model_file
        m = load_model_file(name)
    except Exception:
        m = None
    _KIT_MODEL_CACHE[name] = m
    return m


# ─── KONVERTER OBJ+MTL → Mesh vertex-color (untuk aset Kenney CC0) ─────────────
# Kenney pakai warna material Kd per-bagian (butuh shader/light). Kita "bake"
# warna itu jadi vertex-color → tampil unlit di pipeline shader-kustom kita.
_KENNEY_MESH_CACHE = {}
def _kenney_colored_mesh(name, dull=0.82):
    import os
    if name in _KENNEY_MESH_CACHE:
        return _KENNEY_MESH_CACHE[name]
    from pathlib import Path
    base = Path(__file__).resolve().parent.parent / 'assets' / 'models'
    obj_p = base / f'{name}.obj'
    mtl_p = base / f'{name}.mtl'
    if not obj_p.exists():
        _KENNEY_MESH_CACHE[name] = None
        return None
    # parse MTL → Kd per material
    mats = {}
    if mtl_p.exists():
        cur = None
        for line in open(mtl_p):
            t = line.split()
            if not t:
                continue
            if t[0] == 'newmtl':
                cur = t[1]
            elif t[0] == 'Kd' and cur:
                mats[cur] = (float(t[1]) * dull, float(t[2]) * dull, float(t[3]) * dull)
    # parse OBJ, bake warna material ke tiap vertex (non-indexed)
    from ursina import Vec3, Vec4, Mesh
    V = []
    out_v = []
    out_c = []
    cur_col = (0.6, 0.6, 0.6)
    for line in open(obj_p):
        t = line.split()
        if not t:
            continue
        if t[0] == 'v':
            V.append((float(t[1]), float(t[2]), float(t[3])))
        elif t[0] == 'usemtl':
            cur_col = mats.get(t[1], (0.6, 0.6, 0.6))
        elif t[0] == 'f':
            idx = [int(p.split('/')[0]) - 1 for p in t[1:]]
            for k in range(1, len(idx) - 1):       # triangulasi fan
                for j in (0, k, k + 1):
                    vx = V[idx[j]]
                    out_v.append(Vec3(vx[0], vx[1], vx[2]))
                    out_c.append(Vec4(cur_col[0], cur_col[1], cur_col[2], 1))
    m = Mesh(vertices=out_v, colors=out_c, mode='triangle')
    _KENNEY_MESH_CACHE[name] = m
    return m


# ─── VEGETASI ─────────────────────────────────────────────────────────────────

def _obj_vegetasi(name, wx, wz, h, jitter=0.20):
    """Pohon dari aset Blender baked (skala meter). Return Entity atau None."""
    try:
        from game.entities import load_model_file
        mdl = load_model_file(name)
    except Exception:
        mdl = None
    if not mdl:
        return None
    from ursina import Entity
    e = Entity()
    e.model = mdl                 # setter (pola actor), bukan constructor
    e.position = (wx, GROUND_H, wz)
    e.scale = 1.0 + (h - 0.5) * 2 * jitter
    e.rotation_y = h * 360
    return e


def build_tree(world, wx, wz):
    """Pohon — aset Blender baked (pohon_tropis) bila ada; lalu kit Kenney;
    fallback prosedural (cylinder + bola) bila tak ada aset."""
    h = _hash(wx, wz)

    e = _obj_vegetasi('pohon_tropis', wx, wz, h)
    if e is not None:
        world._obj_ents.append(e)
        return

    # ── Aset kit Kenney (CC0): mesh vertex-color hasil bake dari OBJ+MTL ──
    variants = ['kenney_tree_default', 'kenney_tree_detailed', 'kenney_tree_fat']
    mesh = _kenney_colored_mesh(variants[int(h * 3) % 3])
    if mesh is not None:
        from ursina import Entity
        sc = 2.0 + h * 0.9          # ~3.4–5.0 unit tinggi
        e = Entity(model=mesh, position=(wx, GROUND_H, wz), scale=sc,
                   rotation=(0, h * 360, 0))
        try: e.setLightOff()        # unlit → vertex-color tampil penuh
        except Exception: pass
        world._obj_ents.append(e)
        return

    # ── Fallback prosedural ──
    lean_x = (h - 0.5) * 6
    lean_z = (_hash(wx + 1, wz) - 0.5) * 6

    # Batang kurus, condong
    trunk_col = color.rgb(int(72 + h * 30), int(52 + h * 18), int(28 + h * 12))
    trunk = world._create_entity('cylinder', (wx, TREE_H * 0.40, wz),
               (TS * 0.30, TREE_H * 0.85, TS * 0.30), 'tree_trunk',
               trunk_col, rotation=(lean_x, 0, lean_z))

    # Dedaunan gelap — hijau tua, tidak rimbun
    leaf_r = int(35 + h * 25)
    leaf_g = int(95 + h * 35)
    leaf_b = int(28 + h * 18)
    leaf1 = world._create_entity('sphere', (wx, TREE_H * 0.95, wz),
               (TS * 1.5, TS * 1.2, TS * 1.5), 'cloth_green',
               color.rgb(leaf_r, leaf_g, leaf_b))
    leaf2 = world._create_entity('sphere', (wx + TS*0.25, TREE_H * 1.28, wz - TS*0.2),
               (TS * 1.1, TS * 0.9, TS * 1.0), 'cloth_green',
               color.rgb(leaf_r - 8, leaf_g + 15, leaf_b))
    leaf3 = world._create_entity('sphere', (wx - TS*0.2, TREE_H * 1.18, wz + TS*0.25),
               (TS * 0.9, TS * 0.8, TS * 0.9), 'cloth_green',
               color.rgb(leaf_r + 5, leaf_g - 10, leaf_b + 5))
    world._obj_ents.extend([trunk, leaf1, leaf2, leaf3])


def build_palm(world, wx, wz):
    """Kelapa — batang coklat tua, condong dramatis."""
    h = _hash(wx, wz)

    e = _obj_vegetasi('pohon_kelapa', wx, wz, h)
    if e is not None:
        world._obj_ents.append(e)
        return
    trunk = world._create_entity('cylinder', (wx, TREE_H * 0.5, wz),
               (TS * 0.22, TREE_H * 1.1, TS * 0.22), 'tree_trunk',
               color.rgb(128, 88, 52), rotation=(8, 0, 12))
    world._obj_ents.append(trunk)
    for i in range(5):
        rad = math.radians(i * 72 + h * 30)
        cx = wx + math.sin(rad) * 0.55
        cz = wz + math.cos(rad) * 0.55
        leaf = world._create_entity('cube', (cx, TREE_H * 1.02 - 0.1, cz),
                  (TS * 0.65, 0.05, TS * 0.28), 'cloth_green',
                  color.rgb(58, 168, 42), rotation=(18, -i * 72 + 90, 0))
        world._obj_ents.append(leaf)
    for i in range(3):
        rad = math.radians(i * 120)
        cx = wx + math.sin(rad) * 0.22
        cz = wz + math.cos(rad) * 0.22
        coconut = world._create_entity('sphere', (cx, TREE_H * 0.92, cz),
                     (0.22, 0.22, 0.22), 'wood_plank', color.rgb(148, 112, 45))
        world._obj_ents.append(coconut)


def build_dead_tree(world, wx, wz):
    """Pohon mati — tulang belulang kayu, cabang terentang."""
    h = _hash(wx, wz)

    e = _obj_vegetasi('pohon_mati', wx, wz, h)
    if e is not None:
        world._obj_ents.append(e)
        return
    col = color.rgb(58, 42, 28)
    trunk = world._create_entity('cylinder', (wx, TREE_H * 0.45, wz),
               (TS * 0.18, TREE_H * 0.90, TS * 0.18), 'tree_trunk', col)
    # Cabang kiri-kanan
    branch_l = world._create_entity('cylinder',
                  (wx - TS*0.4, TREE_H * 0.75, wz),
                  (TS * 0.08, TREE_H * 0.45, TS * 0.08), 'tree_trunk', col,
                  rotation=(0, 0, -45))
    branch_r = world._create_entity('cylinder',
                  (wx + TS*0.3, TREE_H * 0.82, wz + TS*0.15),
                  (TS * 0.06, TREE_H * 0.35, TS * 0.06), 'tree_trunk', col,
                  rotation=(8, 30, 38))
    world._obj_ents.extend([trunk, branch_l, branch_r])


# ─── SEBAR PROPS OBJ (dressing aman lintas-scene, M2) ─────────────────────────

def scatter_obj_props(world, scene, specs, count, seed=0, avoid=2, floor=None):
    """Sebar model .obj di tile lantai kosong yang walkable & jauh dari portal.

    specs : list (model_name, scale). Penempatan deterministik (LCG) supaya
            konsisten tiap boot & tak menimpa portal/jalur. Aman: kalau model
            tak ada atau tak ada tile kosong, fungsi diam saja.
    floor : tile (atau tuple tile) yang dianggap lantai kosong; default G (rumput).
            Scene berlantai lain (mis. kuburan = D) cukup oper floor=D.
    """
    from game.config import TILE_SIZE as _TS, GROUND_H as _GH, G as _G
    try:
        from game.entities import make_obj_entity
    except Exception:
        return
    allowed = (floor,) if (floor is not None and not isinstance(floor, (tuple, list, set))) \
        else (tuple(floor) if floor is not None else (_G,))
    portals = {(p[0], p[1]) for p in getattr(scene, 'portals', [])}
    cands = []
    for ty in range(1, scene.h - 1):
        for tx in range(1, scene.w - 1):
            if scene.tiles[ty][tx] not in allowed:
                continue
            if any(abs(tx - px) <= avoid and abs(ty - py) <= avoid for (px, py) in portals):
                continue
            cands.append((tx, ty))
    if not cands:
        return
    placed = 0
    i = seed * 7 + 3
    used = set()
    guard = 0
    while placed < count and guard < count * 40:
        guard += 1
        i = (i * 1103515245 + 12345) & 0x7fffffff
        tx, ty = cands[i % len(cands)]
        if (tx, ty) in used:
            continue
        used.add((tx, ty))
        name, sc = specs[placed % len(specs)]
        placed += 1
        e = make_obj_entity(name, (tx * _TS, _GH, ty * _TS), scale=sc, rot_y=i % 360)
        if e is not None:
            world._obj_ents.append(e)


# ─── OBJEK KECIL ─────────────────────────────────────────────────────────────

def build_lantern(world, wx, wz):
    """Tiang lampu jalan — besi berkarat, cahaya redup."""
    pole = world._create_entity('cylinder', (wx, OBJ_H * 0.45, wz),
              (TS * 0.07, OBJ_H * 0.90, TS * 0.07), 'wood_plank', C_RUST)
    lamp = world._create_entity('cube', (wx, OBJ_H * 0.95, wz),
              (TS * 0.32, 0.35, TS * 0.32), 'lamp_glow',
              color.rgb(200, 175, 105))  # kuning pucat, bukan putih bersih
    world._obj_ents.extend([pole, lamp])


def build_ore(world, wx, wz, tex_name='crystal'):
    base = world._create_entity('cube', (wx, WALL_H / 2 + GROUND_H, wz),
              (TS * 0.98, WALL_H, TS * 0.98), 'wall_cave')
    gem  = world._create_entity('cube',
              (wx, WALL_H + GROUND_H + SMALL_OBJ_H * 0.4, wz),
              (TS * 0.45, SMALL_OBJ_H * 0.7, TS * 0.45),
              tex_name, rotation=(30, 45, 15))
    world._obj_ents.extend([base, gem])


def build_fireplace(world, wx, wz):
    base = world._create_entity('cube', (wx, OBJ_H * 0.5 + GROUND_H, wz),
              (TS * 0.85, OBJ_H, TS * 0.85), 'wall_stone', color.rgb(78, 70, 65))
    flame = world._create_entity('sphere', (wx, OBJ_H + GROUND_H + 0.22, wz),
               (TS * 0.38, 0.40, TS * 0.38), 'fire_orange')
    world._obj_ents.extend([base, flame])


def build_grave(world, wx, wz):
    h = _hash(wx, wz)
    col = color.rgb(int(88 + h*25), int(80 + h*20), int(95 + h*25))
    vert  = world._create_entity('cube', (wx, OBJ_H * 0.50 + GROUND_H, wz),
               (TS * 0.15, OBJ_H * 0.88, TS * 0.13), 'grave_stone', col)
    horiz = world._create_entity('cube', (wx, OBJ_H * 0.68 + GROUND_H, wz),
               (TS * 0.50, TS * 0.13, TS * 0.11), 'grave_stone', col)
    # Noda lumpur di bawah nisan
    stain = world._create_entity('cube', (wx, GROUND_H + 0.05, wz),
               (TS * 0.60, 0.04, TS * 0.55), None, C_STAIN)
    world._obj_ents.extend([vert, horiz, stain])


def build_tv(world, wx, wz):
    base   = world._create_entity('cube', (wx, OBJ_H*0.2 + GROUND_H, wz),
                (TS*0.7, OBJ_H*0.4, TS*0.3), 'wood_plank', color.rgb(42, 40, 38))
    screen = world._create_entity('cube', (wx, OBJ_H*0.7 + GROUND_H, wz),
                (TS*0.8, OBJ_H*0.6, TS*0.1), None, color.rgb(18, 18, 25))
    glass  = world._create_entity('cube', (wx, OBJ_H*0.7 + GROUND_H, wz - TS*0.06),
                (TS*0.7, OBJ_H*0.5, 0.04), None, color.rgb(80, 100, 145))
    world._obj_ents.extend([base, screen, glass])


def build_chair(world, wx, wz):
    col = C_WOOD_DARK
    seat = world._create_entity('cube', (wx, OBJ_H*0.3 + GROUND_H, wz),
              (TS*0.4, 0.09, TS*0.4), 'wood_plank', col)
    for dx, dz in [(-0.15,-0.15),(+0.15,-0.15),(-0.15,+0.15),(+0.15,+0.15)]:
        leg = world._create_entity('cube',
                 (wx+TS*dx, OBJ_H*0.15 + GROUND_H, wz+TS*dz),
                 (0.07, OBJ_H*0.3, 0.07), 'wood_plank', col)
        world._obj_ents.append(leg)
    back = world._create_entity('cube', (wx, OBJ_H*0.62 + GROUND_H, wz+TS*0.15),
              (TS*0.4, OBJ_H*0.58, 0.07), 'wood_plank', col)
    world._obj_ents.extend([seat, back])


def build_calendar(world, wx, wz):
    paper = world._create_entity('cube', (wx, WALL_H*0.6 + GROUND_H, wz),
               (TS*0.38, 0.55, 0.04), None, color.rgb(218, 210, 195))
    bind  = world._create_entity('cube', (wx, WALL_H*0.6 + 0.28 + GROUND_H, wz),
               (TS*0.38, 0.04, 0.06), None, color.rgb(158, 42, 38))
    world._obj_ents.extend([paper, bind])


# ─── TUMPUKAN PUING / JUNK ────────────────────────────────────────────────────

def build_debris_pile(world, wx, wz):
    """Tumpukan sampah dan puing — ban, drum, beton patah."""
    h = _hash(wx, wz)
    # Drum berkarat
    drum = world._create_entity('cylinder',
              (wx + TS*0.1, SMALL_OBJ_H*0.5 + GROUND_H, wz - TS*0.1),
              (TS*0.38, SMALL_OBJ_H*0.95, TS*0.38), None,
              color.rgb(int(118 + h*30), int(72 + h*20), int(38 + h*15)))
    # Ban/tire (torus diganti dengan cylinder pipih)
    tire = world._create_entity('cylinder',
              (wx - TS*0.15, GROUND_H + 0.18, wz + TS*0.08),
              (TS*0.38, 0.22, TS*0.38), None, color.rgb(38, 35, 32))
    # Potongan beton
    rubble = world._create_entity('cube',
                (wx + TS*0.05, GROUND_H + 0.12, wz + TS*0.2),
                (TS*0.28, 0.22, TS*0.22), None, C_CONCRETE_DARK)
    world._obj_ents.extend([drum, tire, rubble])


# ─── JEMURAN ──────────────────────────────────────────────────────────────────

def build_laundry_line(world, wx, wz):
    """Tali jemuran dengan kain usang tergantung."""
    h = _hash(wx, wz)
    # Dua tiang bambu/kayu
    pole1 = world._create_entity('cylinder',
               (wx - TS*0.45, OBJ_H*0.55 + GROUND_H, wz),
               (TS*0.06, OBJ_H*1.1, TS*0.06), 'wood_plank', C_WOOD_OLD)
    pole2 = world._create_entity('cylinder',
               (wx + TS*0.45, OBJ_H*0.55 + GROUND_H, wz),
               (TS*0.06, OBJ_H*1.1, TS*0.06), 'wood_plank', C_WOOD_OLD)
    # Tali
    rope = world._create_entity('cube',
              (wx, OBJ_H*1.08 + GROUND_H, wz),
              (TS*0.90, 0.025, 0.025), None, C_ROPE)
    # Kain-kain tergantung (3 potong, warna pudar)
    cloth_colors = [
        color.rgb(145, 128, 108), color.rgb(98, 118, 138), color.rgb(155, 108, 88)
    ]
    for i, cx in enumerate([-0.28, 0.0, 0.28]):
        cloth = world._create_entity('cube',
                   (wx + TS*cx, OBJ_H*0.78 + GROUND_H, wz + 0.02),
                   (TS*0.18, OBJ_H*0.55, 0.03), None,
                   cloth_colors[i % len(cloth_colors)])
        world._obj_ents.append(cloth)
    world._obj_ents.extend([pole1, pole2, rope])


# ─── ALTAR/SHRINE ─────────────────────────────────────────────────────────────

def build_shrine_altar(world, wx, wz):
    """Altar kecil pinggir jalan — batu, dupa, sesaji."""
    # Alas batu
    base = world._create_entity('cube',
              (wx, GROUND_H + 0.15, wz),
              (TS*0.55, 0.28, TS*0.45), 'wall_stone', C_CONCRETE_DARK)
    # Meja kecil di atas
    table = world._create_entity('cube',
               (wx, GROUND_H + 0.35, wz),
               (TS*0.45, 0.08, TS*0.38), None, color.rgb(105, 85, 65))
    # Atap mini (penanda)
    roof = world._create_entity('cube',
              (wx, GROUND_H + 0.72, wz),
              (TS*0.52, 0.06, TS*0.44), None, color.rgb(88, 68, 48))
    tiang_l = world._create_entity('cylinder',
                 (wx - TS*0.2, GROUND_H + 0.55, wz),
                 (0.04, 0.46, 0.04), None, color.rgb(88, 68, 48))
    tiang_r = world._create_entity('cylinder',
                 (wx + TS*0.2, GROUND_H + 0.55, wz),
                 (0.04, 0.46, 0.04), None, color.rgb(88, 68, 48))
    # Dupa (batang tipis dengan titik merah)
    incense = world._create_entity('cylinder',
                 (wx, GROUND_H + 0.55, wz - TS*0.08),
                 (0.018, 0.35, 0.018), None, color.rgb(185, 142, 88))
    ember = world._create_entity('sphere',
               (wx, GROUND_H + 0.72, wz - TS*0.08),
               (0.04, 0.04, 0.04), None, color.rgb(220, 88, 42))
    # Sesaji (buah kecil)
    offering = world._create_entity('sphere',
                  (wx + TS*0.08, GROUND_H + 0.42, wz),
                  (0.07, 0.07, 0.07), None, color.rgb(205, 165, 42))
    world._obj_ents.extend([base, table, roof, tiang_l, tiang_r, incense, ember, offering])


# ─── KUIL SURGAWI (CANDI SWARGA) ─────────────────────────────────────────────

def build_kuil_swarga(world, scene, tx, ty, wx, wz):
    """Candi surgawi bertingkat — grand temple emas gaya Jawa-Hindu di awan.
    Dipanggil per tile KUIL; hanya menggambar dari tile pojok kiri atas."""
    # Hanya spawn dari pojok kiri-atas blok KUIL
    left_is_k = tx > 0 and scene.tiles[ty][tx - 1] == KUIL
    up_is_k   = ty > 0 and scene.tiles[ty - 1][tx] == KUIL
    if left_is_k or up_is_k:
        return

    # Ukur lebar & tinggi blok KUIL
    w_t = 1
    while tx + w_t < scene.w and scene.tiles[ty][tx + w_t] == KUIL:
        w_t += 1
    h_t = 1
    while ty + h_t < scene.h and scene.tiles[ty + h_t][tx] == KUIL:
        h_t += 1

    cx = wx + (w_t - 1) * TS / 2.0   # pusat world X
    cz = wz + (h_t - 1) * TS / 2.0   # pusat world Z
    GH = GROUND_H

    # ── Palet warna suci ────────────────────────────────────────────────────
    C_GOLD        = color.rgb(218, 185,  95)
    C_GOLD_LIGHT  = color.rgb(245, 222, 130)
    C_GOLD_DARK   = color.rgb(162, 135,  55)
    C_GOLD_BRIGHT = color.rgb(255, 242, 162)
    C_WHITE       = color.rgb(248, 246, 238)
    C_CREAM       = color.rgb(235, 222, 198)
    C_SACRED_FIRE = color.rgb(255, 215,  48)
    C_RED_ACCENT  = color.rgb(185,  52,  38)
    C_JADE        = color.rgb( 88, 165, 118)
    C_LOTUS       = color.rgb(228, 148, 185)
    C_NAGA        = color.rgb(105, 178, 125)

    e  = world._create_entity
    oe = world._obj_ents.extend

    # ─── 1. PLATFORM DASAR ─────────────────────────────────────────────────
    y0 = GH
    plat = e('cube', (cx, y0 + 0.14, cz), (10.6, 0.28, 10.6), None, C_GOLD_DARK)

    # ─── 2. TIGA ANAK TANGGA (stepped pyramid) ─────────────────────────────
    y1 = y0 + 0.28
    tier1 = e('cube', (cx, y1 + 0.27, cz), (8.8, 0.55, 8.8), None, C_GOLD_DARK)

    y2 = y1 + 0.55
    tier2 = e('cube', (cx, y2 + 0.32, cz), (6.8, 0.65, 6.8), None, C_GOLD)

    y3 = y2 + 0.65
    tier3 = e('cube', (cx, y3 + 0.35, cz), (5.2, 0.70, 5.2), None, C_GOLD_LIGHT)

    # ─── 3. BADAN UTAMA CANDI ───────────────────────────────────────────────
    y_wall = y3 + 0.70
    wall_h = 2.80
    body_outer = e('cube', (cx, y_wall + wall_h*0.5, cz), (4.4, wall_h, 4.4), None, C_GOLD)
    body_inner = e('cube', (cx, y_wall + wall_h*0.5, cz), (3.8, wall_h * 0.98, 3.8), None, C_WHITE)

    # Aksen ceruk/panel di 4 sisi (ala candi Prambanan)
    for sz_off, rx in ((1, 0), (-1, 0), (0, 90), (0, 90)):
        pass  # skip (costly), cukup warna badan berbeda

    # Pintu depan (selatan) — warna merah sakral
    door_front = e('cube', (cx, y_wall + 0.80, cz + 2.21),
                   (1.05, 1.60, 0.10), None, C_RED_ACCENT)
    door_arch  = e('cube', (cx, y_wall + 1.68, cz + 2.21),
                   (1.20, 0.32, 0.10), None, C_GOLD)

    # Jendela kecil di sisi timur/barat
    wins = []
    for ox, oz in ((2.21, 0), (-2.21, 0)):
        wins.append(e('cube', (cx + ox, y_wall + 1.40, cz + oz),
                      (0.10, 0.65, 0.55), None, C_GOLD))
    # Ornamen panel di sisi utara/selatan
    for ox, oz in ((0, 2.21), (0, -2.21)):
        wins.append(e('cube', (cx + ox, y_wall + 1.40, cz + oz),
                      (0.55, 0.65, 0.10), None, C_GOLD))

    # ─── 4. ATAP BERTINGKAT (multi-tier roof) ───────────────────────────────
    y_r = y_wall + wall_h
    roof1 = e('cube', (cx, y_r + 0.25,  cz), (5.4, 0.50, 5.4), None, C_GOLD)
    roof1_lip = e('cube', (cx, y_r + 0.04, cz), (5.8, 0.09, 5.8), None, C_GOLD_DARK)

    y_r2 = y_r + 0.50
    roof2 = e('cube', (cx, y_r2 + 0.30, cz), (4.0, 0.60, 4.0), None, C_GOLD_LIGHT)
    roof2_lip = e('cube', (cx, y_r2 + 0.04, cz), (4.4, 0.08, 4.4), None, C_GOLD)

    y_r3 = y_r2 + 0.60
    roof3 = e('cube', (cx, y_r3 + 0.30, cz), (2.8, 0.60, 2.8), None, C_GOLD)
    roof3_lip = e('cube', (cx, y_r3 + 0.04, cz), (3.1, 0.08, 3.1), None, C_GOLD_DARK)

    y_r4 = y_r3 + 0.60
    roof4 = e('cube', (cx, y_r4 + 0.22, cz), (1.8, 0.44, 1.8), None, C_GOLD_LIGHT)

    # ─── 5. PUNCAK MENARA (spire) ───────────────────────────────────────────
    y_sp = y_r4 + 0.44
    spire_body = e('cylinder', (cx, y_sp + 0.95, cz), (0.52, 1.90, 0.52), None, C_GOLD_LIGHT)
    spire_cap  = e('sphere',   (cx, y_sp + 2.00, cz), (0.72, 0.72, 0.72), None, C_GOLD_BRIGHT)
    sacred_flame = e('sphere', (cx, y_sp + 2.58, cz), (0.38, 0.38, 0.38), None, C_SACRED_FIRE)

    # Cincin halo di spire
    halo = e('cube', (cx, y_sp + 2.00, cz), (1.20, 0.06, 1.20), None, C_GOLD_BRIGHT)

    oe([plat, tier1, tier2, tier3,
        body_outer, body_inner, door_front, door_arch] +
       wins +
       [roof1, roof1_lip, roof2, roof2_lip, roof3, roof3_lip, roof4,
        spire_body, spire_cap, sacred_flame, halo])

    # ─── 6. MENARA SUDUT (4 mini-towers di sudut KUIL area) ─────────────────
    for sx, sz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        mx = cx + sx * 4.3
        mz = cz + sz * 4.3
        mt_base  = e('cube',     (mx, y0 + 0.55,   mz), (1.25, 1.10, 1.25), None, C_GOLD_DARK)
        mt_body  = e('cube',     (mx, y0 + 1.58,   mz), (0.95, 1.05, 0.95), None, C_WHITE)
        mt_roof  = e('cube',     (mx, y0 + 2.28,   mz), (1.15, 0.48, 1.15), None, C_GOLD)
        mt_spire = e('cylinder', (mx, y0 + 2.88,   mz), (0.28, 0.90, 0.28), None, C_GOLD_LIGHT)
        mt_top   = e('sphere',   (mx, y0 + 3.42,   mz), (0.35, 0.35, 0.35), None, C_GOLD_BRIGHT)
        oe([mt_base, mt_body, mt_roof, mt_spire, mt_top])

    # ─── 7. PILAR GERBANG SELATAN (naga pillars) ────────────────────────────
    for px_off in (-2.6, 2.6):
        px = cx + px_off
        pz = cz + 5.0
        p_base  = e('cube',     (px, y0 + 0.45, pz), (0.75, 0.90, 0.75), None, C_GOLD_DARK)
        p_body  = e('cylinder', (px, y0 + 1.85, pz), (0.42, 2.80, 0.42), None, C_GOLD)
        p_cap   = e('cube',     (px, y0 + 3.35, pz), (0.68, 0.28, 0.68), None, C_GOLD_LIGHT)
        p_naga  = e('sphere',   (px, y0 + 3.72, pz), (0.52, 0.42, 0.48), None, C_NAGA)
        p_horn1 = e('cube',     (px - 0.15, y0 + 4.00, pz), (0.10, 0.34, 0.10), None, C_NAGA)
        p_horn2 = e('cube',     (px + 0.15, y0 + 4.00, pz), (0.10, 0.34, 0.10), None, C_NAGA)
        oe([p_base, p_body, p_cap, p_naga, p_horn1, p_horn2])

    # ─── 8. LOTUS DEKORASI DI ANAK TANGGA ───────────────────────────────────
    for lx, lz in (( 3.8,  3.8), (-3.8,  3.8), ( 3.8, -3.8), (-3.8, -3.8),
                   ( 0.0,  4.2), ( 0.0, -4.2), ( 4.2,  0.0), (-4.2,  0.0)):
        lp = e('sphere', (cx + lx, y1 + 0.45, cz + lz), (0.30, 0.22, 0.30), None, C_LOTUS)
        lc = e('sphere', (cx + lx, y1 + 0.60, cz + lz), (0.14, 0.14, 0.14), None, C_GOLD_BRIGHT)
        oe([lp, lc])

    # ─── 9. LAMPU GANTUNG JADE DI SUDUT BADAN ───────────────────────────────
    for ox, oz in ((1.8, 1.8), (-1.8, 1.8), (1.8, -1.8), (-1.8, -1.8)):
        bell = e('sphere', (cx + ox, y_wall + wall_h - 0.30, cz + oz),
                 (0.22, 0.30, 0.22), None, C_JADE)
        oe([bell])


# ─── DINDING GRAFFITI ─────────────────────────────────────────────────────────

def build_graffiti_wall(world, wx, wz):
    """Dinding beton dengan graffiti — simbol serikat, nama, coretan politik."""
    h = _hash(wx, wz)
    # Dinding dasar
    wall = world._create_entity('cube',
              (wx, WALL_H*0.5 + GROUND_H, wz),
              (TS*0.95, WALL_H, TS*0.12), None, C_CONCRETE)
    # Strip graffiti (simulated sebagai strip warna)
    graffiti_cols = [
        color.rgb(185, 62, 48),   # merah tua
        color.rgb(48, 88, 148),   # biru union
        color.rgb(175, 155, 42),  # kuning pudar
    ]
    gi = int(h * len(graffiti_cols))
    gfx = world._create_entity('cube',
             (wx + TS*(h-0.5)*0.3, WALL_H*0.55 + GROUND_H, wz - 0.07),
             (TS*0.55, WALL_H*0.28, 0.04), None, graffiti_cols[gi % 3])
    # Noda air di bawah
    stain = world._create_entity('cube',
               (wx, GROUND_H + 0.12, wz - 0.05),
               (TS*0.90, 0.22, 0.06), None, C_STAIN)
    world._obj_ents.extend([wall, gfx, stain])


# ─── WARUNG MALAM ─────────────────────────────────────────────────────────────

def build_warung(world, wx, wz):
    """Warung makan kecil — rangka kayu, atap plastik, meja panjang."""
    h = _hash(wx, wz)
    # Empat tiang
    for dx, dz in [(-0.38,-0.38),(+0.38,-0.38),(-0.38,+0.38),(+0.38,+0.38)]:
        pole = world._create_entity('cylinder',
                  (wx + TS*dx, OBJ_H*0.55 + GROUND_H, wz + TS*dz),
                  (0.08, OBJ_H*1.1, 0.08), 'wood_plank', C_WOOD_OLD)
        world._obj_ents.append(pole)
    # Atap plastik/kanvas (sangat tipis, sedikit transparan-ish via warna)
    roof_col = color.rgb(int(125 + h*30), int(118 + h*25), int(108 + h*20))
    roof = world._create_entity('cube',
              (wx, OBJ_H*1.08 + GROUND_H, wz),
              (TS*0.95, 0.06, TS*0.95), None, roof_col)
    # Dinding plastik sisi belakang (bukan sisi depan — open air)
    back_wall = world._create_entity('cube',
                   (wx, OBJ_H*0.5 + GROUND_H, wz - TS*0.38),
                   (TS*0.80, OBJ_H, 0.05), None, C_PLASTIC)
    # Meja counter
    counter = world._create_entity('cube',
                 (wx, OBJ_H*0.42 + GROUND_H, wz + TS*0.2),
                 (TS*0.75, 0.08, TS*0.28), 'wood_plank', C_WOOD_DARK)
    # Bangku panjang
    bench = world._create_entity('cube',
               (wx, OBJ_H*0.22 + GROUND_H, wz + TS*0.42),
               (TS*0.65, 0.07, TS*0.14), 'wood_plank', C_WOOD_DARK)
    # Lampu gantung (redup)
    lamp_wire = world._create_entity('cylinder',
                   (wx, OBJ_H*0.98 + GROUND_H, wz),
                   (0.015, 0.18, 0.015), None, color.rgb(38, 35, 32))
    lamp_bulb = world._create_entity('sphere',
                   (wx, OBJ_H*0.88 + GROUND_H, wz),
                   (0.09, 0.09, 0.09), 'lamp_glow', color.rgb(215, 195, 138))
    world._obj_ents.extend([roof, back_wall, counter, bench, lamp_wire, lamp_bulb])


# ─── RUMAH PANGGUNG ───────────────────────────────────────────────────────────

def build_rumah_panggung(world, scene, tx, ty, wx, wz):
    """Rumah panggung (stilted house) tropis yang sudah lapuk."""
    left_is_rp = tx > 0 and scene.tiles[ty][tx-1] == RUMAH_PG
    up_is_rp   = ty > 0 and scene.tiles[ty-1][tx] == RUMAH_PG
    if left_is_rp or up_is_rp:
        return

    w_tiles = 1
    while tx + w_tiles < scene.w and scene.tiles[ty][tx + w_tiles] == RUMAH_PG:
        w_tiles += 1
    h_tiles = 1
    while ty + h_tiles < scene.h and scene.tiles[ty + h_tiles][tx] == RUMAH_PG:
        h_tiles += 1

    cx = wx + (w_tiles - 1) * TS / 2.0
    cz = wz + (h_tiles - 1) * TS / 2.0
    sx = TS * w_tiles * 0.90
    sz = TS * h_tiles * 0.90
    h  = _hash(wx, wz)

    STILT_H = 1.2   # ketinggian kolong panggung

    # Tiang-tiang (stilts) — 4 di sudut + tengah untuk lebar > 1 tile
    stilt_positions = [
        (cx - sx*0.42, cz - sz*0.42),
        (cx + sx*0.42, cz - sz*0.42),
        (cx - sx*0.42, cz + sz*0.42),
        (cx + sx*0.42, cz + sz*0.42),
    ]
    if w_tiles > 1:
        stilt_positions.append((cx, cz - sz*0.42))
        stilt_positions.append((cx, cz + sz*0.42))
    for sx_p, sz_p in stilt_positions:
        stilt_col = color.rgb(int(78 + h*22), int(55 + h*15), int(32 + h*10))
        stilt = world._create_entity('cylinder',
                   (sx_p, STILT_H*0.5 + GROUND_H, sz_p),
                   (0.14, STILT_H, 0.14), 'wood_plank', stilt_col)
        world._obj_ents.append(stilt)

    # Platform kolong (lantai panggung)
    platform = world._create_entity('cube',
                  (cx, STILT_H + GROUND_H + 0.06, cz),
                  (sx + 0.12, 0.12, sz + 0.12), 'wood_plank',
                  color.rgb(int(105 + h*20), int(78 + h*15), int(48 + h*10)))

    # Dinding utama — kayu/seng campuran, warna pudar
    wall_col = color.rgb(int(162 + h*20), int(148 + h*18), int(128 + h*15))
    body = world._create_entity('cube',
              (cx, STILT_H + GROUND_H + HOUSE_H*0.42, cz),
              (sx, HOUSE_H*0.82, sz), None, wall_col)

    # Strip seng berkarat di bagian bawah dinding
    seng_col = color.rgb(int(128 + h*30), int(88 + h*20), int(52 + h*15))
    seng_base = world._create_entity('cube',
                   (cx, STILT_H + GROUND_H + HOUSE_H*0.12, cz),
                   (sx + 0.04, HOUSE_H*0.22, sz + 0.04), None, seng_col)

    # Pintu (depan)
    door = world._create_entity('cube',
              (cx, STILT_H + GROUND_H + HOUSE_H*0.32, cz + sz*0.5 + 0.02),
              (TS*0.7, HOUSE_H*0.58, 0.09), 'wood_plank', C_WOOD_DARK)

    # Tangga depan (3 anak tangga)
    for step_i in range(3):
        step = world._create_entity('cube',
                  (cx, GROUND_H + 0.12 + step_i * (STILT_H/3.2),
                   cz + sz*0.5 + TS*(0.22 + step_i*0.18)),
                  (TS*0.55, 0.10, TS*0.16), 'wood_plank', C_WOOD_OLD)
        world._obj_ents.append(step)

    # Atap seng — hampir datar, sedikit pitch
    ri = int(abs(h) * len(ROOF_TEXTURES)) % len(ROOF_TEXTURES)
    r_tex, r_col = ROOF_TEXTURES[ri]
    roof = world._create_entity('cube',
              (cx, STILT_H + GROUND_H + HOUSE_H*0.88, cz),
              (sx + TS*0.35, 0.15, sz + TS*0.35), r_tex, r_col)

    # Pipa air berkarat di sisi dinding
    pipe = world._create_entity('cylinder',
              (cx + sx*0.52, STILT_H + GROUND_H + HOUSE_H*0.45, cz - sz*0.2),
              (0.06, HOUSE_H*0.85, 0.06), None, C_RUST)

    # Noda jamur di pojok bawah dinding
    mold = world._create_entity('cube',
              (cx - sx*0.42, STILT_H + GROUND_H + HOUSE_H*0.15, cz - sz*0.38),
              (TS*0.25, HOUSE_H*0.28, 0.06), None, C_MOLD)

    world._obj_ents.extend([platform, body, seng_base, door, roof, pipe, mold])


# ─── UNION HALL / GEDUNG KOPERASI ─────────────────────────────────────────────

def build_union_hall(world, scene, tx, ty, wx, wz):
    """Gedung besar beton — bekas serikat buruh/koperasi, cat mengelupas."""
    left_is_u = tx > 0 and scene.tiles[ty][tx-1] == UNION_HL
    up_is_u   = ty > 0 and scene.tiles[ty-1][tx] == UNION_HL
    if left_is_u or up_is_u:
        return

    w_tiles = 1
    while tx + w_tiles < scene.w and scene.tiles[ty][tx + w_tiles] == UNION_HL:
        w_tiles += 1
    h_tiles = 1
    while ty + h_tiles < scene.h and scene.tiles[ty + h_tiles][tx] == UNION_HL:
        h_tiles += 1

    cx = wx + (w_tiles - 1) * TS / 2.0
    cz = wz + (h_tiles - 1) * TS / 2.0
    sx = TS * w_tiles * 0.96
    sz = TS * h_tiles * 0.96
    bh = HOUSE_H * 1.35   # gedung lebih tinggi
    h  = _hash(wx, wz)

    # Fondasi beton
    foundation = world._create_entity('cube',
                    (cx, GROUND_H + 0.14, cz),
                    (sx + 0.10, 0.26, sz + 0.10), None, C_CONCRETE_DARK)

    # Badan utama — beton blok abu
    body = world._create_entity('cube',
              (cx, bh*0.5 + GROUND_H, cz),
              (sx, bh, sz), None, C_CONCRETE)

    # Strip horizontal beton gelap (detail arsitektur)
    for strip_y in [0.30, 0.65]:
        strip = world._create_entity('cube',
                   (cx, bh*strip_y + GROUND_H, cz),
                   (sx + 0.08, 0.10, sz + 0.08), None, C_CONCRETE_DARK)
        world._obj_ents.append(strip)

    # Jendela-jendela dipalang tripleks (3 jendela di sisi depan)
    for j, jx in enumerate([-0.32, 0.0, 0.32]):
        win_frame = world._create_entity('cube',
                       (cx + sx*jx, bh*0.60 + GROUND_H, cz + sz*0.5 + 0.03),
                       (TS*0.32, bh*0.22, 0.10), None, color.rgb(62, 58, 52))
        plywood = world._create_entity('cube',
                     (cx + sx*jx, bh*0.60 + GROUND_H, cz + sz*0.5 + 0.09),
                     (TS*0.28, bh*0.19, 0.04), None, C_PLYWOOD)
        world._obj_ents.extend([win_frame, plywood])

    # Pintu besar (loading dock style)
    door = world._create_entity('cube',
              (cx, bh*0.28 + GROUND_H, cz + sz*0.5 + 0.02),
              (TS*1.1, bh*0.50, 0.08), None, C_WOOD_DARK)

    # Logo/tulisan serikat (strip warna di dinding samping)
    logo_col = color.rgb(48, 82, 138)  # biru union, pudar
    logo = world._create_entity('cube',
              (cx + sx*0.52, bh*0.62 + GROUND_H, cz),
              (0.07, bh*0.30, sz*0.55), None, logo_col)

    # Atap datar — beton + detail seng berkarat
    roof = world._create_entity('cube',
              (cx, bh + GROUND_H + 0.07, cz),
              (sx + 0.15, 0.14, sz + 0.15), None, C_CONCRETE_DARK)
    roof_seng = world._create_entity('cube',
                   (cx, bh + GROUND_H + 0.15, cz - sz*0.2),
                   (sx*0.6, 0.06, sz*0.4), None, C_RUST)

    # Graffiti di bawah jendela (strip)
    graffiti = world._create_entity('cube',
                  (cx - sx*0.2, bh*0.32 + GROUND_H, cz + sz*0.5 + 0.08),
                  (TS*0.45, bh*0.12, 0.03), None, color.rgb(145, 48, 42))

    world._obj_ents.extend([foundation, body, door, logo, roof, roof_seng, graffiti])


# ─── RUMAH KAMPUNG (revamp build_house_block) ─────────────────────────────────

def _add_window(world, ents, cx, cy, cz, face, w_size, h_size, is_boarded, wall_thick=0.12):
    """Tambah jendela (frame + kaca/tripleks) di salah satu face bangunan.
    face: 'front'|'back'|'left'|'right'
    w_size, h_size: lebar & tinggi jendela.
    """
    off = wall_thick
    if face == 'front':   px, pz, fw, fz = cx,   cz + off,  w_size, 0.08
    elif face == 'back':  px, pz, fw, fz = cx,   cz - off,  w_size, 0.08
    elif face == 'right': px, pz, fw, fz = cx + off, cz,    0.08,   w_size
    else:                 px, pz, fw, fz = cx - off, cz,    0.08,   w_size

    # Frame kayu — sedikit lebih besar dari kaca
    frame = world._create_entity('cube', (px, cy, pz),
                (fw + 0.10, h_size + 0.10, fz + 0.10), None, C_WOOD_DARK)
    ents.append(frame)
    if is_boarded:
        board = world._create_entity('cube', (px, cy, pz),
                    (fw + 0.04, h_size + 0.04, fz + 0.16), None, C_PLYWOOD)
        ents.append(board)
    else:
        # Kaca — warna biru-abu gelap dengan sedikit tint hangat (lampu dalam)
        glass = world._create_entity('cube', (px, cy, pz),
                    (fw, h_size, fz + 0.14), None, color.rgb(52, 62, 72))
        ents.append(glass)
        # Pantulan/cahaya interior — strip tipis kuning di dalam kaca
        glow = world._create_entity('cube', (px, cy, pz),
                   (fw * 0.55, h_size * 0.55, fz + 0.16),
                   None, color.rgb(190, 158, 88))
        ents.append(glow)


def build_house_block(world, scene, tx, ty, wx, wz):
    """Rumah kampung lapuk — dinding, jendela & detail terlihat jelas dari luar."""
    left_is_H = tx > 0 and scene.tiles[ty][tx-1] == H
    up_is_H   = ty > 0 and scene.tiles[ty-1][tx] == H
    if left_is_H or up_is_H:
        return

    w_tiles = 1
    while tx + w_tiles < scene.w and scene.tiles[ty][tx + w_tiles] == H:
        w_tiles += 1
    h_tiles = 1
    while ty + h_tiles < scene.h and scene.tiles[ty + h_tiles][tx] == H:
        h_tiles += 1

    cx = wx + (w_tiles - 1) * TS / 2.0
    cz = wz + (h_tiles - 1) * TS / 2.0
    sx = TS * w_tiles * 0.93
    sz = TS * h_tiles * 0.93
    h  = _hash(wx, wz)

    ri = int(h * len(ROOF_TEXTURES)) % len(ROOF_TEXTURES)
    r_tex, r_col = ROOF_TEXTURES[ri]

    wallh  = HOUSE_H * 1.45        # ~4.64 — menjulang jelas di atas player
    base_y = GROUND_H + 0.20       # di atas fondasi
    ents   = []                    # kumpulkan semua entity

    # ── Fondasi beton — plinth yang menonjol ──────────────────────────────────
    ents.append(world._create_entity('cube',
        (cx, GROUND_H + 0.14, cz), (sx + 0.12, 0.28, sz + 0.12), None, C_CONCRETE))

    # ── Dinding utama — plesteran pudar dengan tekstur house_wall ─────────────
    wall_r = int(168 + h * 32);  wall_g = int(154 + h * 28);  wall_b = int(128 + h * 24)
    wall_col = color.rgb(wall_r, wall_g, wall_b)
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.5, cz), (sx, wallh, sz), 'house_wall', wall_col))

    # ── Strip plint bawah — beton gelap (beda material dari dinding) ──────────
    plint_h = wallh * 0.22
    plint_col = color.rgb(int(105 + h * 22), int(92 + h * 18), int(72 + h * 14))
    ents.append(world._create_entity('cube',
        (cx, base_y + plint_h * 0.5, cz),
        (sx + 0.06, plint_h, sz + 0.06), None, plint_col))

    # ── Garis pemisah antar-lantai — papan kayu horizontal ────────────────────
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.50, cz),
        (sx + 0.10, 0.14, sz + 0.10), None, C_WOOD_DARK))

    # ── Lisplang/trim atas dinding — batas dinding-atap ──────────────────────
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh + 0.06, cz),
        (sx + 0.14, 0.13, sz + 0.14), None, C_CONCRETE_DARK))

    # ── JENDELA di 4 sisi ────────────────────────────────────────────────────
    win_y_lo = base_y + wallh * 0.30   # lantai bawah
    win_y_hi = base_y + wallh * 0.74   # lantai atas
    win_w    = TS * 0.38
    win_h    = 0.82
    wt       = sx * 0.5 + 0.06        # tebal sisi dari center ke face

    # Tentukan posisi X jendela berdasarkan lebar bangunan
    win_x_offsets = []
    if w_tiles == 1:
        win_x_offsets = [-sx * 0.22, sx * 0.22]
    else:
        step = sx / (w_tiles + 1)
        win_x_offsets = [(-sx * 0.5 + step * (i + 1)) for i in range(w_tiles)]

    win_z_offsets = []
    if h_tiles == 1:
        win_z_offsets = [-sz * 0.22, sz * 0.22]
    else:
        step = sz / (h_tiles + 1)
        win_z_offsets = [(-sz * 0.5 + step * (i + 1)) for i in range(h_tiles)]

    # Front & back — jendela per-kolom
    for xo in win_x_offsets:
        for wy_level in [win_y_lo, win_y_hi]:
            boarded = _hash(cx + xo, wy_level) > 0.52
            _add_window(world, ents, cx + xo, wy_level, cz + sz * 0.5,
                        'front', win_w, win_h, boarded, wall_thick=0.07)
            _add_window(world, ents, cx + xo, wy_level, cz - sz * 0.5,
                        'back', win_w, win_h, boarded, wall_thick=0.07)

    # Left & right — jendela per-baris kedalaman
    for zo in win_z_offsets:
        for wy_level in [win_y_lo, win_y_hi]:
            boarded = _hash(cz + zo, wy_level) > 0.52
            _add_window(world, ents, cx + sx * 0.5, wy_level, cz + zo,
                        'right', win_w * sz / sx, win_h, boarded, wall_thick=0.07)
            _add_window(world, ents, cx - sx * 0.5, wy_level, cz + zo,
                        'left', win_w * sz / sx, win_h, boarded, wall_thick=0.07)

    # ── Pintu kayu di depan — frame + daun pintu ──────────────────────────────
    door_col = color.rgb(int(88 + h * 28), int(60 + h * 20), int(35 + h * 14))
    # Frame pintu (lebih terang dari dinding)
    ents.append(world._create_entity('cube',
        (cx, base_y + 1.05, cz + sz * 0.5 + 0.04),
        (TS * 0.76, 2.10, 0.12), None, C_CONCRETE_DARK))
    # Daun pintu
    ents.append(world._create_entity('cube',
        (cx, base_y + 0.98, cz + sz * 0.5 + 0.07),
        (TS * 0.62, 1.96, 0.09), 'wood_plank', door_col))
    # Panel jendela kecil di atas pintu (fanlight)
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.26, cz + sz * 0.5 + 0.09),
        (TS * 0.38, 0.38, 0.07), None, color.rgb(52, 62, 72)))
    if h > 0.55:  # palang horizontal
        ents.append(world._create_entity('cube',
            (cx, base_y + 1.05, cz + sz * 0.5 + 0.17),
            (TS * 0.60, 0.10, 0.06), None, C_WOOD_DARK))

    # ── Teras + tiang + railing ───────────────────────────────────────────────
    ents.append(world._create_entity('cube',
        (cx, base_y + 2.05, cz + sz * 0.5 + TS * 0.34),
        (sx * 0.80, 0.14, TS * 0.72), r_tex, r_col))
    for px_off in [-sx * 0.34, sx * 0.34]:
        ents.append(world._create_entity('cylinder',
            (cx + px_off, base_y + 1.0, cz + sz * 0.5 + TS * 0.58),
            (0.12, 2.0, 0.12), None, C_CONCRETE_DARK))
    # Railing teras — palang horizontal
    ents.append(world._create_entity('cube',
        (cx, base_y + 1.85, cz + sz * 0.5 + TS * 0.60),
        (sx * 0.70, 0.08, 0.08), None, C_WOOD_DARK))

    # ── Atap seng pelana — jelas menonjol ─────────────────────────────────────
    from ursina.models.procedural.cone import Cone
    roof_y = base_y + wallh
    ents.append(world._create_entity(Cone(resolution=4),
        (cx, roof_y + HOUSE_H * 0.42, cz),
        (sx * 1.42, HOUSE_H * 0.90, sz * 1.42), r_tex, r_col, rotation=(0, 45, 0)))
    # Lisplang atap
    ents.append(world._create_entity('cube',
        (cx, roof_y + 0.07, cz), (sx * 1.44, 0.12, sz * 1.44), None, r_col))

    # ── Detail sisi — pipa + noda air ─────────────────────────────────────────
    ents.append(world._create_entity('cylinder',
        (cx + sx * 0.48, base_y + wallh * 0.5, cz - sz * 0.22),
        (0.08, wallh, 0.08), None, C_RUST))
    ents.append(world._create_entity('cube',
        (cx - sx * 0.46, base_y + wallh * 0.20, cz - sz * 0.38),
        (TS * 0.18, wallh * 0.32, 0.05), None, C_MOLD))

    world._obj_ents.extend(ents)


# ─── EKSTERIOR BANGUNAN BERTEMA ───────────────────────────────────────────────

def _collect_block(scene, tx, ty, tile_type):
    """Bantu: hitung ukuran blok tile yang bersebelahan untuk tile_type tertentu."""
    w_tiles = 1
    while tx + w_tiles < scene.w and scene.tiles[ty][tx + w_tiles] == tile_type:
        w_tiles += 1
    h_tiles = 1
    while ty + h_tiles < scene.h and scene.tiles[ty + h_tiles][tx] == tile_type:
        h_tiles += 1
    return w_tiles, h_tiles


def build_shop_exterior(world, scene, tx, ty, wx, wz):
    """Toko kelontong — eksterior krem-kuning, awning merah, etalase kaca."""
    left_same = tx > 0 and scene.tiles[ty][tx-1] == SHOP_EXT
    up_same   = ty > 0 and scene.tiles[ty-1][tx] == SHOP_EXT
    if left_same or up_same:
        return

    w_tiles, h_tiles = _collect_block(scene, tx, ty, SHOP_EXT)

    cx = wx + (w_tiles - 1) * TS / 2.0
    cz = wz + (h_tiles - 1) * TS / 2.0
    sx = TS * w_tiles * 0.93
    sz = TS * h_tiles * 0.93
    h  = _hash(wx, wz)
    ents = []

    wallh  = HOUSE_H * 1.20
    base_y = GROUND_H + 0.20

    ri = int(h * len(ROOF_TEXTURES)) % len(ROOF_TEXTURES)
    r_tex, r_col = ROOF_TEXTURES[ri]

    # Fondasi
    ents.append(world._create_entity('cube',
        (cx, GROUND_H + 0.14, cz), (sx + 0.12, 0.28, sz + 0.12), None, C_CONCRETE))

    # Dinding utama — krem-kuning pudar
    wall_col = color.rgb(195, 178, 130)
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.5, cz), (sx, wallh, sz), 'house_wall', wall_col))

    # Plint bawah
    plint_h = wallh * 0.18
    ents.append(world._create_entity('cube',
        (cx, base_y + plint_h * 0.5, cz),
        (sx + 0.06, plint_h, sz + 0.06), None, color.rgb(168, 152, 110)))

    # Papan nama di atas awning
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.78, cz + sz * 0.5 + 0.06),
        (sx * 0.82, wallh * 0.12, 0.08), None, color.rgb(212, 195, 145)))

    # Awning/tenda di atas etalase depan
    awning_col = color.rgb(175, 88, 55)
    awning_y = base_y + wallh * 0.60
    ents.append(world._create_entity('cube',
        (cx, awning_y, cz + sz * 0.5 + TS * 0.25),
        (sx * 0.88, 0.06, TS * 0.55), None, awning_col))

    # Tiang awning — 2 silinder kecil
    for pole_x in [cx - sx * 0.30, cx + sx * 0.30]:
        ents.append(world._create_entity('cylinder',
            (pole_x, base_y + wallh * 0.30, cz + sz * 0.5 + TS * 0.50),
            (0.07, wallh * 0.60, 0.07), None, color.rgb(148, 108, 68)))

    # Etalase kaca besar di depan
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.38, cz + sz * 0.5 + 0.07),
        (TS * 0.62, 1.20, 0.10), None, C_WOOD_DARK))   # frame
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.38, cz + sz * 0.5 + 0.12),
        (TS * 0.50, 1.10, 0.05), None, color.rgb(48, 58, 68)))  # kaca
    # Kilap kaca
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.38, cz + sz * 0.5 + 0.14),
        (TS * 0.22, 0.45, 0.04), None, color.rgb(88, 110, 138)))

    # Jendela samping kiri & kanan
    win_y = base_y + wallh * 0.55
    win_w = TS * 0.32
    win_h_val = 0.68
    _add_window(world, ents, cx - sx * 0.32, win_y, cz + sz * 0.5,
                'front', win_w, win_h_val, False, wall_thick=0.07)
    _add_window(world, ents, cx + sx * 0.32, win_y, cz + sz * 0.5,
                'front', win_w, win_h_val, False, wall_thick=0.07)
    _add_window(world, ents, cx + sx * 0.5, win_y, cz,
                'right', win_w, win_h_val, False, wall_thick=0.07)
    _add_window(world, ents, cx - sx * 0.5, win_y, cz,
                'left', win_w, win_h_val, False, wall_thick=0.07)

    # Pintu kayu depan
    door_col = color.rgb(128, 78, 42)
    ents.append(world._create_entity('cube',
        (cx - sx * 0.30, base_y + 0.95, cz + sz * 0.5 + 0.04),
        (TS * 0.58, 1.90, 0.10), 'wood_plank', door_col))
    # Step/anak tangga kecil di depan
    ents.append(world._create_entity('cube',
        (cx - sx * 0.30, GROUND_H + 0.10, cz + sz * 0.5 + TS * 0.22),
        (TS * 0.62, 0.12, TS * 0.20), None, C_CONCRETE_DARK))

    # Atap pelana rendah
    from ursina.models.procedural.cone import Cone
    roof_y = base_y + wallh
    ents.append(world._create_entity(Cone(resolution=4),
        (cx, roof_y + HOUSE_H * 0.28, cz),
        (sx * 1.38, HOUSE_H * 0.62, sz * 1.38), r_tex, r_col, rotation=(0, 45, 0)))
    ents.append(world._create_entity('cube',
        (cx, roof_y + 0.06, cz), (sx * 1.40, 0.11, sz * 1.40), None, r_col))

    world._obj_ents.extend(ents)


def build_clinic_exterior(world, scene, tx, ty, wx, wz):
    """Klinik — dinding putih-abu bersih, palang merah, jendela kaca semua."""
    left_same = tx > 0 and scene.tiles[ty][tx-1] == CLINIC_EXT
    up_same   = ty > 0 and scene.tiles[ty-1][tx] == CLINIC_EXT
    if left_same or up_same:
        return

    w_tiles, h_tiles = _collect_block(scene, tx, ty, CLINIC_EXT)

    cx = wx + (w_tiles - 1) * TS / 2.0
    cz = wz + (h_tiles - 1) * TS / 2.0
    sx = TS * w_tiles * 0.93
    sz = TS * h_tiles * 0.93
    h  = _hash(wx, wz)
    ents = []

    wallh  = HOUSE_H * 1.35
    base_y = GROUND_H + 0.20

    ri = int(h * len(ROOF_TEXTURES)) % len(ROOF_TEXTURES)
    r_tex, r_col = ROOF_TEXTURES[ri]

    # Fondasi beton bersih
    ents.append(world._create_entity('cube',
        (cx, GROUND_H + 0.14, cz), (sx + 0.12, 0.28, sz + 0.12), None, color.rgb(195, 192, 185)))

    # Dinding utama — putih-abu bersih
    wall_col = color.rgb(218, 215, 210)
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.5, cz), (sx, wallh, sz), 'house_wall', wall_col))

    # Plint bawah (lebih terang dari rumah biasa)
    plint_h = wallh * 0.18
    ents.append(world._create_entity('cube',
        (cx, base_y + plint_h * 0.5, cz),
        (sx + 0.06, plint_h, sz + 0.06), None, color.rgb(188, 185, 178)))

    # Lisplang atas
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh + 0.06, cz),
        (sx + 0.14, 0.13, sz + 0.14), None, color.rgb(175, 172, 165)))

    # Kanopi/overhang di atas pintu masuk
    kanopi_col = color.rgb(188, 55, 55)
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.62, cz + sz * 0.5 + TS * 0.18),
        (sx * 0.58, 0.07, TS * 0.40), None, kanopi_col))

    # Simbol palang merah di atas pintu — 2 cube saling silang
    cross_col = color.rgb(188, 55, 55)
    cross_y = base_y + wallh * 0.78
    ents.append(world._create_entity('cube',
        (cx, cross_y, cz + sz * 0.5 + 0.08),
        (0.10, 0.52, 0.06), None, cross_col))  # vertikal
    ents.append(world._create_entity('cube',
        (cx, cross_y, cz + sz * 0.5 + 0.08),
        (0.52, 0.10, 0.06), None, cross_col))  # horizontal

    # Pintu depan — bersih, terang
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.28, cz + sz * 0.5 + 0.04),
        (TS * 0.70, 0.56, 0.12), None, color.rgb(188, 185, 178)))  # frame
    ents.append(world._create_entity('cube',
        (cx, base_y + 0.95, cz + sz * 0.5 + 0.07),
        (TS * 0.60, 1.90, 0.09), 'wood_plank', color.rgb(155, 148, 138)))

    # Jendela kaca — semua tidak dipalang (klinik terawat)
    win_y_lo = base_y + wallh * 0.32
    win_y_hi = base_y + wallh * 0.70
    win_w = TS * 0.36
    win_h_val = 0.78
    for xo in [-sx * 0.28, sx * 0.28]:
        for wy_lvl in [win_y_lo, win_y_hi]:
            _add_window(world, ents, cx + xo, wy_lvl, cz + sz * 0.5,
                        'front', win_w, win_h_val, False, wall_thick=0.07)
            _add_window(world, ents, cx + xo, wy_lvl, cz - sz * 0.5,
                        'back', win_w, win_h_val, False, wall_thick=0.07)
    for zo in [-sz * 0.22, sz * 0.22]:
        for wy_lvl in [win_y_lo, win_y_hi]:
            _add_window(world, ents, cx + sx * 0.5, wy_lvl, cz + zo,
                        'right', win_w, win_h_val, False, wall_thick=0.07)
            _add_window(world, ents, cx - sx * 0.5, wy_lvl, cz + zo,
                        'left', win_w, win_h_val, False, wall_thick=0.07)

    # Atap pelana normal
    from ursina.models.procedural.cone import Cone
    roof_y = base_y + wallh
    ents.append(world._create_entity(Cone(resolution=4),
        (cx, roof_y + HOUSE_H * 0.38, cz),
        (sx * 1.42, HOUSE_H * 0.82, sz * 1.42), r_tex, r_col, rotation=(0, 45, 0)))
    ents.append(world._create_entity('cube',
        (cx, roof_y + 0.06, cz), (sx * 1.44, 0.12, sz * 1.44), None, r_col))

    world._obj_ents.extend(ents)


def build_smith_exterior(world, scene, tx, ty, wx, wz):
    """Bengkel pandai besi — dinding batu gelap, cerobong, cahaya api dari jendela."""
    left_same = tx > 0 and scene.tiles[ty][tx-1] == SMITH_EXT
    up_same   = ty > 0 and scene.tiles[ty-1][tx] == SMITH_EXT
    if left_same or up_same:
        return

    w_tiles, h_tiles = _collect_block(scene, tx, ty, SMITH_EXT)

    cx = wx + (w_tiles - 1) * TS / 2.0
    cz = wz + (h_tiles - 1) * TS / 2.0
    sx = TS * w_tiles * 0.93
    sz = TS * h_tiles * 0.93
    h  = _hash(wx, wz)
    ents = []

    wallh  = HOUSE_H * 1.60
    base_y = GROUND_H + 0.20

    ri = int(h * len(ROOF_TEXTURES)) % len(ROOF_TEXTURES)
    r_tex, _ = ROOF_TEXTURES[ri]
    # Warna atap bengkel selalu gelap — besi berkarat tua
    r_col = color.rgb(62, 55, 48)

    # Fondasi masif
    ents.append(world._create_entity('cube',
        (cx, GROUND_H + 0.16, cz), (sx + 0.16, 0.32, sz + 0.16), None, color.rgb(58, 52, 45)))

    # Dinding utama — batu bata gelap
    wall_col = color.rgb(85, 78, 68)
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.5, cz), (sx, wallh, sz), 'house_wall', wall_col))

    # Strip batu kasar di plint bawah
    plint_h = wallh * 0.22
    ents.append(world._create_entity('cube',
        (cx, base_y + plint_h * 0.5, cz),
        (sx + 0.08, plint_h, sz + 0.08), None, color.rgb(62, 55, 46)))

    # Lisplang atas gelap
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh + 0.06, cz),
        (sx + 0.16, 0.16, sz + 0.16), None, color.rgb(48, 42, 36)))

    # Pintu forge besar
    ents.append(world._create_entity('cube',
        (cx, base_y + 1.15, cz + sz * 0.5 + 0.05),
        (TS * 0.95, 2.30, 0.14), None, color.rgb(52, 46, 40)))  # frame besi
    ents.append(world._create_entity('cube',
        (cx, base_y + 1.05, cz + sz * 0.5 + 0.10),
        (TS * 0.82, 2.10, 0.09), 'wood_plank', color.rgb(68, 55, 42)))  # daun pintu

    # Jendela dengan cahaya api oranye — bukan kaca biru
    forge_win_y = base_y + wallh * 0.45
    win_w = TS * 0.30
    for xo in [-sx * 0.30, sx * 0.30]:
        # Frame
        ents.append(world._create_entity('cube',
            (cx + xo, forge_win_y, cz + sz * 0.5 + 0.06),
            (win_w + 0.10, 0.72, 0.12), None, color.rgb(48, 42, 36)))
        # Cahaya api
        ents.append(world._create_entity('cube',
            (cx + xo, forge_win_y, cz + sz * 0.5 + 0.12),
            (win_w, 0.62, 0.06), None, color.rgb(255, 140, 40)))
        # Kilap merah di dalam
        ents.append(world._create_entity('cube',
            (cx + xo, forge_win_y, cz + sz * 0.5 + 0.15),
            (win_w * 0.55, 0.28, 0.04), None, color.rgb(220, 80, 25)))

    # Jendela sisi
    side_win_y = base_y + wallh * 0.48
    _add_window(world, ents, cx + sx * 0.5, side_win_y, cz,
                'right', TS * 0.28, 0.65, False, wall_thick=0.07)
    _add_window(world, ents, cx - sx * 0.5, side_win_y, cz,
                'left', TS * 0.28, 0.65, False, wall_thick=0.07)
    # Override warna kaca jendela sisi ke oranye
    # (kaca sudah ditambahkan via _add_window, tidak perlu override — efek cukup)

    # Cerobong asap — besar di atas atap
    chimney_x = cx + sx * 0.25
    chimney_z = cz - sz * 0.22
    chimney_base_y = base_y + wallh
    ents.append(world._create_entity('cylinder',
        (chimney_x, chimney_base_y + HOUSE_H * 0.40, chimney_z),
        (0.28, HOUSE_H * 0.80, 0.28), None, color.rgb(55, 48, 40)))
    # Tutup cerobong
    ents.append(world._create_entity('cube',
        (chimney_x, chimney_base_y + HOUSE_H * 0.82, chimney_z),
        (0.44, 0.08, 0.44), None, color.rgb(42, 36, 30)))
    # Asap/soot ring
    ents.append(world._create_entity('cylinder',
        (chimney_x, chimney_base_y + HOUSE_H * 0.79, chimney_z),
        (0.32, 0.06, 0.32), None, color.rgb(28, 25, 22)))

    # Pipa-pipa di sisi dinding
    for px_off, pz_off in [(sx*0.50, sz*0.25), (sx*0.50, -sz*0.15)]:
        ents.append(world._create_entity('cylinder',
            (cx + px_off, base_y + wallh * 0.55, cz + pz_off),
            (0.07, wallh * 0.65, 0.07), None, C_RUST))

    # Atap pelana berat
    from ursina.models.procedural.cone import Cone
    roof_y = base_y + wallh
    ents.append(world._create_entity(Cone(resolution=4),
        (cx, roof_y + HOUSE_H * 0.40, cz),
        (sx * 1.42, HOUSE_H * 0.85, sz * 1.42), r_tex, r_col, rotation=(0, 45, 0)))
    ents.append(world._create_entity('cube',
        (cx, roof_y + 0.07, cz), (sx * 1.44, 0.14, sz * 1.44), None, color.rgb(48, 42, 36)))

    # Noda jelaga di dinding sekitar jendela
    ents.append(world._create_entity('cube',
        (cx, base_y + wallh * 0.72, cz + sz * 0.5 + 0.06),
        (sx * 0.65, wallh * 0.22, 0.04), None, color.rgb(28, 24, 20)))

    world._obj_ents.extend(ents)


def build_greenhouse_exterior(world, scene, tx, ty, wx, wz):
    """Rumah kaca — frame logam hijau-abu, panel kaca transparan, tanaman terlihat."""
    left_same = tx > 0 and scene.tiles[ty][tx-1] == GREENHOUSE_EXT
    up_same   = ty > 0 and scene.tiles[ty-1][tx] == GREENHOUSE_EXT
    if left_same or up_same:
        return

    w_tiles, h_tiles = _collect_block(scene, tx, ty, GREENHOUSE_EXT)

    cx = wx + (w_tiles - 1) * TS / 2.0
    cz = wz + (h_tiles - 1) * TS / 2.0
    sx = TS * w_tiles * 0.93
    sz = TS * h_tiles * 0.93
    h  = _hash(wx, wz)
    ents = []

    wallh  = HOUSE_H * 1.30
    base_y = GROUND_H + 0.08

    frame_col = color.rgb(95, 115, 95)   # logam hijau-abu
    glass_col = color.rgb(140, 195, 155) # panel kaca hijau-biru muda

    # Fondasi tipis
    ents.append(world._create_entity('cube',
        (cx, GROUND_H + 0.08, cz), (sx + 0.10, 0.16, sz + 0.10), None, color.rgb(105, 118, 98)))

    # ── Frame vertikal di sudut dan tengah ─────────────────────────────────────
    frame_posts = [
        (cx - sx*0.48, cz - sz*0.48), (cx + sx*0.48, cz - sz*0.48),
        (cx - sx*0.48, cz + sz*0.48), (cx + sx*0.48, cz + sz*0.48),
        (cx,          cz - sz*0.48), (cx,          cz + sz*0.48),
        (cx - sx*0.48, cz),          (cx + sx*0.48, cz),
    ]
    for fpx, fpz in frame_posts:
        ents.append(world._create_entity('cylinder',
            (fpx, base_y + wallh * 0.5, fpz),
            (0.08, wallh, 0.08), None, frame_col))

    # ── Frame horizontal — sisi depan/belakang ────────────────────────────────
    for frame_y in [base_y + wallh * 0.25, base_y + wallh * 0.60, base_y + wallh]:
        ents.append(world._create_entity('cube',
            (cx, frame_y, cz - sz * 0.48), (sx * 0.97, 0.07, 0.08), None, frame_col))
        ents.append(world._create_entity('cube',
            (cx, frame_y, cz + sz * 0.48), (sx * 0.97, 0.07, 0.08), None, frame_col))
        ents.append(world._create_entity('cube',
            (cx - sx * 0.48, frame_y, cz), (0.08, 0.07, sz * 0.97), None, frame_col))
        ents.append(world._create_entity('cube',
            (cx + sx * 0.48, frame_y, cz), (0.08, 0.07, sz * 0.97), None, frame_col))

    # ── Panel kaca dinding — beberapa section ────────────────────────────────
    panel_h = wallh * 0.32
    panel_y_lo = base_y + wallh * 0.13
    panel_y_hi = base_y + wallh * 0.46

    # Depan — 2 panel terpisah (ada pintu di tengah)
    for pxo in [-sx * 0.25, sx * 0.25]:
        for pyl in [panel_y_lo, panel_y_hi]:
            ents.append(world._create_entity('cube',
                (cx + pxo, pyl, cz + sz * 0.48),
                (sx * 0.40, panel_h, 0.05), None, glass_col))
    # Belakang & sisi — panel penuh
    for pyl in [panel_y_lo, panel_y_hi]:
        ents.append(world._create_entity('cube',
            (cx, pyl, cz - sz * 0.48), (sx * 0.90, panel_h, 0.05), None, glass_col))
        ents.append(world._create_entity('cube',
            (cx + sx * 0.48, pyl, cz), (0.05, panel_h, sz * 0.90), None, glass_col))
        ents.append(world._create_entity('cube',
            (cx - sx * 0.48, pyl, cz), (0.05, panel_h, sz * 0.90), None, glass_col))

    # Pintu greenhouse di depan-tengah
    ents.append(world._create_entity('cube',
        (cx, base_y + 1.00, cz + sz * 0.48 + 0.05),
        (TS * 0.65, 2.00, 0.08), None, frame_col))

    # Tanaman terlihat dari luar — beberapa cube hijau di dalam
    plant_cols = [color.rgb(55, 140, 58), color.rgb(38, 115, 45), color.rgb(72, 165, 65)]
    plant_positions = [
        (cx - sx*0.30, cz - sz*0.25), (cx + sx*0.30, cz - sz*0.25),
        (cx - sx*0.20, cz + sz*0.18), (cx + sx*0.22, cz + sz*0.20),
        (cx,           cz - sz*0.10),
    ]
    for i, (ppx, ppz) in enumerate(plant_positions):
        pc = plant_cols[i % len(plant_cols)]
        ents.append(world._create_entity('sphere',
            (ppx, base_y + wallh * 0.28, ppz),
            (TS * 0.42, TS * 0.40, TS * 0.42), 'cloth_green', pc))

    # Atap segitiga greenhouse — frame + panel kaca
    roof_y = base_y + wallh
    # Ridge (puncak atap)
    ents.append(world._create_entity('cube',
        (cx, roof_y + HOUSE_H * 0.38, cz),
        (sx * 0.06, HOUSE_H * 0.78, sx * 0.06), None, frame_col))
    # Panel atap kiri-kanan
    from ursina.models.procedural.cone import Cone
    ents.append(world._create_entity(Cone(resolution=4),
        (cx, roof_y + HOUSE_H * 0.30, cz),
        (sx * 1.32, HOUSE_H * 0.65, sz * 1.32), None,
        color.rgb(125, 178, 140), rotation=(0, 45, 0)))
    # Frame atap
    ents.append(world._create_entity('cube',
        (cx, roof_y + 0.05, cz), (sx * 1.35, 0.08, sz * 1.35), None, frame_col))

    world._obj_ents.extend(ents)


# ─── DERMAGA LAPUK ────────────────────────────────────────────────────────────

def build_dock_rotten(world, wx, wz):
    """Dermaga kayu lapuk — papan berlubang, tiang membusuk."""
    h = _hash(wx, wz)
    # Platform dermaga
    deck = world._create_entity('cube',
              (wx, GROUND_H + 0.08, wz),
              (TS*0.95, 0.12, TS*0.95), 'wood_plank',
              color.rgb(int(88 + h*22), int(65 + h*15), int(42 + h*10)))
    # Tiang pilar (membusuk, tidak sempurna)
    for dx, dz in [(-0.38,-0.38),(+0.38,-0.38),(-0.38,+0.38),(+0.38,+0.38)]:
        piling_h = 0.55 + h * 0.25   # tinggi tidak rata
        piling = world._create_entity('cylinder',
                    (wx + TS*dx, GROUND_H - piling_h*0.3, wz + TS*dz),
                    (0.12, piling_h, 0.12), 'wood_plank',
                    color.rgb(int(62 + h*18), int(45 + h*12), int(28 + h*8)))
        world._obj_ents.append(piling)
    # Papan berlubang (gap visual — kegelapan di bawah)
    gap = world._create_entity('cube',
             (wx + TS*0.12, GROUND_H + 0.085, wz - TS*0.08),
             (TS*0.18, 0.13, TS*0.22), None, color.rgb(22, 18, 15))
    world._obj_ents.extend([deck, gap])


# ─── PROP BUILDER UTAMA ───────────────────────────────────────────────────────

# ─── FURNITURE INTERIOR — bentuk dikenali + warna kontras (bukan kubus coklat) ──

def build_bed(world, wx, wz):
    """Ranjang: rangka kayu + kasur + bantal + selimut (warna kontras biru)."""
    frame = world._create_entity('cube', (wx, GROUND_H+0.18, wz),
               (TS*0.78, 0.30, TS*0.92), 'wood_plank', color.rgb(95, 68, 45))
    matt  = world._create_entity('cube', (wx, GROUND_H+0.40, wz),
               (TS*0.70, 0.18, TS*0.84), None, color.rgb(205, 200, 188))   # kasur pucat
    blank = world._create_entity('cube', (wx, GROUND_H+0.44, wz+TS*0.18),
               (TS*0.70, 0.14, TS*0.48), None, color.rgb(90, 120, 150))    # selimut biru
    pillow= world._create_entity('cube', (wx, GROUND_H+0.46, wz-TS*0.32),
               (TS*0.50, 0.14, TS*0.20), None, color.rgb(225, 220, 208))
    world._obj_ents.extend([frame, matt, blank, pillow])


def build_table(world, wx, wz):
    """Meja: papan atas + 4 kaki (kayu lebih terang dari lantai)."""
    top = world._create_entity('cube', (wx, GROUND_H+0.62, wz),
             (TS*0.82, 0.10, TS*0.82), 'wood_plank', color.rgb(150, 112, 68))
    world._obj_ents.append(top)
    for dx, dz in [(-0.32,-0.32),(0.32,-0.32),(-0.32,0.32),(0.32,0.32)]:
        leg = world._create_entity('cube', (wx+TS*dx, GROUND_H+0.31, wz+TS*dz),
                 (0.09, 0.62, 0.09), 'wood_plank', color.rgb(110, 80, 50))
        world._obj_ents.append(leg)


def build_stove(world, wx, wz):
    """Kompor: badan logam abu + 2 tungku + cerobong."""
    body = world._create_entity('cube', (wx, GROUND_H+0.42, wz),
              (TS*0.78, 0.84, TS*0.72), 'metal_grey', color.rgb(108, 110, 116))
    top  = world._create_entity('cube', (wx, GROUND_H+0.86, wz),
              (TS*0.82, 0.06, TS*0.76), None, color.rgb(72, 74, 80))
    world._obj_ents.extend([body, top])
    for dx in (-0.18, 0.18):
        burner = world._create_entity('cylinder', (wx+TS*dx, GROUND_H+0.90, wz),
                    (0.18, 0.04, 0.18), None, color.rgb(40, 40, 44))
        world._obj_ents.append(burner)
    pipe = world._create_entity('cylinder', (wx+TS*0.3, GROUND_H+1.3, wz-TS*0.25),
              (0.10, 0.9, 0.10), None, C_RUST)
    glow = world._create_entity('cube', (wx, GROUND_H+0.5, wz+TS*0.37),
              (TS*0.3, 0.2, 0.04), 'fire_orange', color.rgb(220, 120, 50))
    world._obj_ents.extend([pipe, glow])


def build_bookshelf(world, wx, wz):
    """Rak buku: rangka + 3 baris buku warna-warni (kontras)."""
    frame = world._create_entity('cube', (wx, GROUND_H+0.85, wz),
               (TS*0.78, 1.70, TS*0.30), 'wood_plank', color.rgb(92, 64, 42))
    world._obj_ents.append(frame)
    book_cols = [color.rgb(150,70,55), color.rgb(70,95,130), color.rgb(150,140,70),
                 color.rgb(80,120,80), color.rgb(120,80,120)]
    for i, sy in enumerate([0.5, 1.0, 1.5]):
        for j in range(4):
            bk = world._create_entity('cube',
                    (wx - TS*0.28 + j*TS*0.19, GROUND_H+sy, wz+0.02),
                    (TS*0.14, 0.34, TS*0.22), None, book_cols[(i*4+j) % len(book_cols)])
            world._obj_ents.append(bk)


def build_shelf_store(world, wx, wz):
    """Rak toko: tiang + papan + barang dagangan kecil warna-warni."""
    for dx in (-0.34, 0.34):
        post = world._create_entity('cube', (wx+TS*dx, GROUND_H+0.75, wz),
                  (0.08, 1.5, TS*0.5), 'wood_plank', color.rgb(100, 72, 46))
        world._obj_ents.append(post)
    goods = [color.rgb(170,90,60), color.rgb(90,140,90), color.rgb(160,150,80)]
    for i, sy in enumerate([0.45, 0.95, 1.4]):
        plank = world._create_entity('cube', (wx, GROUND_H+sy, wz),
                   (TS*0.72, 0.07, TS*0.5), 'wood_plank', color.rgb(120, 88, 56))
        world._obj_ents.append(plank)
        for j in range(3):
            it = world._create_entity('cube',
                    (wx - TS*0.22 + j*TS*0.22, GROUND_H+sy+0.18, wz),
                    (TS*0.16, 0.26, TS*0.2), None, goods[(i+j) % 3])
            world._obj_ents.append(it)


def build_counter(world, wx, wz):
    """Counter: badan kayu + permukaan atas terang."""
    base = world._create_entity('cube', (wx, GROUND_H+0.42, wz),
              (TS*0.9, 0.84, TS*0.82), 'wood_plank', color.rgb(118, 86, 54))
    top  = world._create_entity('cube', (wx, GROUND_H+0.88, wz),
              (TS*0.96, 0.10, TS*0.9), None, color.rgb(155, 120, 78))
    world._obj_ents.extend([base, top])


def build_chest(world, wx, wz):
    """Peti: kotak + tutup melengkung + kunci kuningan."""
    box = world._create_entity('cube', (wx, GROUND_H+0.28, wz),
             (TS*0.66, 0.50, TS*0.5), 'chest_wood', color.rgb(150, 110, 60))
    lid = world._create_entity('cube', (wx, GROUND_H+0.58, wz),
             (TS*0.68, 0.16, TS*0.52), 'chest_wood', color.rgb(125, 88, 48))
    lock= world._create_entity('cube', (wx, GROUND_H+0.42, wz+TS*0.26),
             (0.12, 0.16, 0.06), None, color.rgb(205, 175, 75))
    world._obj_ents.extend([box, lid, lock])


def build_plant_pot(world, wx, wz):
    """Pot tanaman: pot terakota + dedaunan hijau (kontras)."""
    pot = world._create_entity('cube', (wx, GROUND_H+0.20, wz),
             (TS*0.34, 0.40, TS*0.34), None, color.rgb(150, 92, 62))
    foliage = world._create_entity('sphere', (wx, GROUND_H+0.62, wz),
                 (TS*0.46, 0.55, TS*0.46), 'cloth_green', color.rgb(70, 130, 60))
    world._obj_ents.extend([pot, foliage])


def build_mirror(world, wx, wz):
    """Cermin: bingkai kayu + kaca biru pucat berdebu."""
    frame = world._create_entity('cube', (wx, GROUND_H+0.85, wz),
               (TS*0.5, 1.5, 0.12), 'wood_plank', color.rgb(95, 70, 48))
    glass = world._create_entity('cube', (wx, GROUND_H+0.9, wz-0.05),
               (TS*0.38, 1.25, 0.04), 'mirror_blue', color.rgb(150, 172, 188))
    world._obj_ents.extend([frame, glass])


def build_clock(world, wx, wz):
    """Jam dinding tua."""
    body = world._create_entity('cube', (wx, GROUND_H+1.4, wz),
              (TS*0.4, 0.7, 0.14), 'wood_plank', color.rgb(110, 80, 52))
    face = world._create_entity('cube', (wx, GROUND_H+1.5, wz-0.06),
              (TS*0.28, 0.28, 0.04), None, color.rgb(215, 205, 180))
    world._obj_ents.extend([body, face])


# Peta tile furniture → builder
_FURNITURE_BUILDERS = {
    BD: build_bed, TB: build_table, ST: build_stove, BS: build_bookshelf,
    SH: build_shelf_store, CT: build_counter, CH: build_chest,
    PP: build_plant_pot, MR: build_mirror, CL: build_clock,
}


def default_prop_builder(world, scene):
    from game.world import OBJ_TEX
    for ty in range(scene.h):
        for tx in range(scene.w):
            tid = scene.tiles[ty][tx]
            wx, wz = tx * TS, ty * TS

            if   tid == TR:       build_tree(world, wx, wz)
            elif tid == PALM:     build_palm(world, wx, wz)
            elif tid == DT:       build_dead_tree(world, wx, wz)
            elif tid == LN:       build_lantern(world, wx, wz)
            elif tid == FP:       build_fireplace(world, wx, wz)
            elif tid == GR:       build_grave(world, wx, wz)
            elif tid == TV:       build_tv(world, wx, wz)
            elif tid == CHR:      build_chair(world, wx, wz)
            elif tid == CAL:      build_calendar(world, wx, wz)
            elif tid == H:        build_house_block(world, scene, tx, ty, wx, wz)
            elif tid == RUMAH_PG: build_rumah_panggung(world, scene, tx, ty, wx, wz)
            elif tid == UNION_HL: build_union_hall(world, scene, tx, ty, wx, wz)
            elif tid == SHOP_EXT:       build_shop_exterior(world, scene, tx, ty, wx, wz)
            elif tid == CLINIC_EXT:     build_clinic_exterior(world, scene, tx, ty, wx, wz)
            elif tid == SMITH_EXT:      build_smith_exterior(world, scene, tx, ty, wx, wz)
            elif tid == GREENHOUSE_EXT: build_greenhouse_exterior(world, scene, tx, ty, wx, wz)
            elif tid == WARUNG:   build_warung(world, wx, wz)
            elif tid == SHRINE:   build_shrine_altar(world, wx, wz)
            elif tid == KUIL:     build_kuil_swarga(world, scene, tx, ty, wx, wz)
            elif tid == DEBRIS:   build_debris_pile(world, wx, wz)
            elif tid == LAUNDRY:  build_laundry_line(world, wx, wz)
            elif tid == GRAFFITI_W: build_graffiti_wall(world, wx, wz)
            elif tid == DCK:      build_dock_rotten(world, wx, wz)
            elif tid in _FURNITURE_BUILDERS:
                _FURNITURE_BUILDERS[tid](world, wx, wz)
            elif tid in (ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH, CRYS):
                ore_tex = OBJ_TEX.get(tid, 'crystal')
                build_ore(world, wx, wz, ore_tex)

    _build_portal_signs(world, scene)


# ─── PAPAN PETUNJUK PORTAL (ROADMAP M1) ──────────────────────────────────────

def build_signpost(world, wx, wz, text):
    """Papan petunjuk kayu dengan label arah — dibaca dari kejauhan.
    PENTING: Text wajib di-parent ke entity dunia (anchor) — tanpa parent,
    Ursina menaruh Text di camera.ui (membanjiri layar)."""
    from ursina import Entity as _E, Text
    pole = world._create_entity('cylinder',
              (wx, OBJ_H * 0.5 + GROUND_H, wz),
              (0.09, OBJ_H, 0.09), 'wood_plank', C_WOOD_OLD)
    board = world._create_entity('cube',
              (wx, OBJ_H * 0.95 + GROUND_H, wz),
              (TS * 0.72, TS * 0.26, 0.07), 'wood_plank', color.rgb(98, 78, 52))
    anchor = _E(position=(wx, OBJ_H * 1.40 + GROUND_H, wz))
    lbl = Text(text, parent=anchor, billboard=True, scale=6, origin=(0, 0),
               color=color.rgb(235, 220, 180), background=True)
    world._obj_ents.extend([pole, board, anchor, lbl])


_SIGN_OUTDOOR = {'farm', 'town', 'beach', 'lake', 'mountain'}

def _build_portal_signs(world, scene):
    """Auto-pasang papan '→ Tujuan' di samping tiap portal scene outdoor."""
    if getattr(scene, 'name', '') not in _SIGN_OUTDOOR:
        return
    try:
        from . import SCENES
    except Exception:
        SCENES = {}
    seen = set()
    for portal in (getattr(scene, 'portals', None) or []):
        try:
            px, py, dest = portal[0], portal[1], portal[2]
        except Exception:
            continue
        if dest in seen:
            continue
        seen.add(dest)
        disp = dest.title()
        sc_dest = SCENES.get(dest) if isinstance(SCENES, dict) else None
        if sc_dest is not None and getattr(sc_dest, 'display', None):
            disp = sc_dest.display
        # geser 1 tile ke dalam peta dari tepi + 1 tile menyamping dari jalur
        ox = 1 if px <= 1 else (-1 if px >= scene.w - 2 else 1)
        oy = 1 if py <= 1 else (-1 if py >= scene.h - 2 else 0)
        build_signpost(world, (px + ox) * TS, (py + oy) * TS, f"> {disp}")


# ─── BLENDER-EXPORTED .OBJ PROPS ─────────────────────────────────────────────
# Assets diekspor dari Blender ke game/assets/models/, siap pakai di Ursina.

from ursina import Entity

def _obj_entity(model_name, pos, scale=1.0, rot=(0,0,0), col=None):
    kw = dict(model=model_name, position=pos, scale=scale, rotation=rot)
    if col: kw['color'] = col
    return Entity(**kw)

def build_sumur_obj(wx, wz, scale=1.0):
    return _obj_entity('sumur', (wx, 0, wz), scale)

def build_warung_obj(wx, wz, scale=1.0, rot_y=0):
    return _obj_entity('warung', (wx, 0, wz), scale, (0, rot_y, 0))

def build_pohon_tropis_obj(wx, wz, scale=1.0):
    return _obj_entity('pohon_tropis', (wx, 0, wz), scale)

def build_pohon_kelapa_obj(wx, wz, scale=1.0):
    return _obj_entity('pohon_kelapa', (wx, 0, wz), scale)

def build_pohon_bambu_obj(wx, wz, scale=1.0):
    return _obj_entity('pohon_bambu', (wx, 0, wz), scale)

def build_pohon_mati_obj(wx, wz, scale=1.0):
    return _obj_entity('pohon_mati', (wx, 0, wz), scale)

def build_rumah_kampung_obj(wx, wz, scale=1.0, rot_y=0):
    return _obj_entity('rumah_kampung', (wx, 0, wz), scale, (0, rot_y, 0))

def build_rumah_limasan_obj(wx, wz, scale=1.0, rot_y=0):
    return _obj_entity('rumah_limasan', (wx, 0, wz), scale, (0, rot_y, 0))

def build_rumah_joglo_obj(wx, wz, scale=1.0, rot_y=0):
    return _obj_entity('rumah_joglo', (wx, 0, wz), scale, (0, rot_y, 0))

def build_lantern_obj(wx, wz, scale=1.0):
    return _obj_entity('lantern', (wx, 0, wz), scale)

def build_pagar_bambu_obj(wx, wz, scale=1.0, rot_y=0):
    return _obj_entity('pagar_bambu', (wx, 0, wz), scale, (0, rot_y, 0))
