from game.config import *
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

def build_tree(world, wx, wz):
    """Pohon — pakai model kit CC0 (kenney_tree*) bila ada, di-tint kumuh;
    fallback prosedural (cylinder + bola) bila tak ada aset."""
    h = _hash(wx, wz)

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

def build_house_block(world, scene, tx, ty, wx, wz):
    """Rumah kampung lapuk — bukan vila eropa, tapi bangunan tropis yang sudah aus."""
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

    # Fondasi — beton kusam
    foundation = world._create_entity('cube',
                    (cx, GROUND_H + 0.10, cz),
                    (sx, 0.20, sz), None, C_CONCRETE_DARK)

    # Tinggi dinding — JELAS menjulang di atas player (player ~3.0 unit).
    # Rumah kampung 2-lantai kumuh: ~4.6 unit.
    wallh = HOUSE_H * 1.45
    base_y = GROUND_H + 0.20   # di atas fondasi

    # Dinding utama — cat usang, warna pudar tidak seragam
    wall_r = int(170 + h*30)
    wall_g = int(156 + h*26)
    wall_b = int(132 + h*22)
    body = world._create_entity('cube',
              (cx, base_y + wallh*0.5, cz),
              (sx, wallh, sz), None,
              color.rgb(wall_r, wall_g, wall_b))

    # Garis pemisah lantai (papan horizontal) — perkuat kesan 2 lantai
    floor_line = world._create_entity('cube',
              (cx, base_y + wallh*0.5, cz),
              (sx + 0.06, 0.12, sz + 0.06), None, C_WOOD_DARK)

    # Strip seng berkarat di bagian bawah dinding (material campuran)
    seng = world._create_entity('cube',
              (cx, base_y + wallh*0.14, cz),
              (sx + 0.06, wallh*0.26, sz + 0.06), None,
              color.rgb(int(150 + h*28), int(108 + h*20), int(64 + h*15)))

    # Pintu kayu tua (proporsi ~tinggi manusia)
    door_col = color.rgb(int(95 + h*25), int(65 + h*18), int(38 + h*12))
    door = world._create_entity('cube',
              (cx, base_y + 0.95, cz + sz*0.5 + 0.02),
              (TS*0.7, 1.9, 0.10), 'wood_plank', door_col)
    if h > 0.55:  # beberapa rumah dipalang
        door_bar = world._create_entity('cube',
                      (cx, base_y + 1.0, cz + sz*0.5 + 0.13),
                      (TS*0.68, 0.10, 0.06), None, C_WOOD_DARK)
        world._obj_ents.append(door_bar)

    # Jendela lantai atas — depan, beberapa dipalang tripleks
    for side_x in [-sx*0.26, sx*0.26]:
        wy = base_y + wallh*0.74
        frame = world._create_entity('cube',
                   (cx + side_x, wy, cz + sz*0.5 + 0.03),
                   (TS*0.42, 0.95, 0.10), None, C_WOOD_DARK)
        world._obj_ents.append(frame)
        if _hash(cx + side_x, wy) > 0.45:  # boarded
            board = world._create_entity('cube',
                       (cx + side_x, wy, cz + sz*0.5 + 0.09),
                       (TS*0.36, 0.78, 0.05), None, C_PLYWOOD)
            world._obj_ents.append(board)
        else:  # kaca gelap
            glass = world._create_entity('cube',
                       (cx + side_x, wy, cz + sz*0.5 + 0.08),
                       (TS*0.34, 0.72, 0.04), None, color.rgb(38, 44, 52))
            world._obj_ents.append(glass)

    # Teras + tiang penyangga di depan pintu
    porch = world._create_entity('cube',
               (cx, base_y + 2.0, cz + sz*0.5 + TS*0.32),
               (TS*1.3, 0.14, TS*0.7), r_tex, r_col)
    pillar1 = world._create_entity('cylinder',
                 (cx - TS*0.5, base_y + 1.0, cz + sz*0.5 + TS*0.6),
                 (0.10, 2.0, 0.10), 'wood_plank', C_WOOD_OLD)
    pillar2 = world._create_entity('cylinder',
                 (cx + TS*0.5, base_y + 1.0, cz + sz*0.5 + TS*0.6),
                 (0.10, 2.0, 0.10), 'wood_plank', C_WOOD_OLD)

    # Atap seng pelana — jelas kontras di atas dinding
    from ursina.models.procedural.cone import Cone
    roof_y = base_y + wallh
    roof = world._create_entity(Cone(resolution=4),
              (cx, roof_y + HOUSE_H*0.40, cz),
              (sx*1.4, HOUSE_H*0.85, sz*1.4), r_tex, r_col, rotation=(0, 45, 0))
    eave = world._create_entity('cube',
              (cx, roof_y + 0.05, cz),
              (sx*1.42, 0.10, sz*1.42), None, r_col)

    # Pipa berkarat di sisi dinding
    pipe = world._create_entity('cylinder',
              (cx + sx*0.52, base_y + wallh*0.5, cz - sz*0.22),
              (0.07, wallh, 0.07), None, C_RUST)

    # Noda jamur pojok bawah + noda air vertikal
    mold = world._create_entity('cube',
              (cx - sx*0.5, base_y + wallh*0.18, cz - sz*0.40),
              (TS*0.22, wallh*0.34, 0.05), None, C_MOLD)
    water_stain = world._create_entity('cube',
                     (cx + sx*0.30, base_y + wallh*0.45, cz - sz*0.52),
                     (TS*0.10, wallh*0.7, 0.04), None, C_STAIN)

    world._obj_ents.extend([foundation, body, floor_line, seng, door,
                             porch, pillar1, pillar2, roof, eave, pipe,
                             mold, water_stain])


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
            elif tid == WARUNG:   build_warung(world, wx, wz)
            elif tid == SHRINE:   build_shrine_altar(world, wx, wz)
            elif tid == DEBRIS:   build_debris_pile(world, wx, wz)
            elif tid == LAUNDRY:  build_laundry_line(world, wx, wz)
            elif tid == GRAFFITI_W: build_graffiti_wall(world, wx, wz)
            elif tid == DCK:      build_dock_rotten(world, wx, wz)
            elif tid in _FURNITURE_BUILDERS:
                _FURNITURE_BUILDERS[tid](world, wx, wz)
            elif tid in (ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH, CRYS):
                ore_tex = OBJ_TEX.get(tid, 'crystal')
                build_ore(world, wx, wz, ore_tex)
