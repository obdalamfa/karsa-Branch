from game.config import *
from ursina import color
import math

TS = TILE_SIZE

# Roof texture variants
ROOF_TEXTURES = [
    ('roof/terracotta',      color.rgb(215,  88,  68)),
    ('roof/adobetile',       color.rgb(198, 145,  95)),
    ('roof/adobetile_red',   color.rgb(195,  72,  55)),
    ('roof/adobetile_green', color.rgb( 72, 155,  88)),
    ('roof/adobetile_blue',  color.rgb( 72, 105, 188)),
    ('roof/adobetile_gold',  color.rgb(215, 178,  65)),
    ('roof/slate_h',         color.rgb(118, 128, 148)),
    ('roof/composite_green', color.rgb( 78, 128,  88)),
    ('roof/composite_red',   color.rgb(188,  75,  65)),
    ('roof/composite_light', color.rgb(195, 185, 165)),
    ('roof/composite_tan',   color.rgb(188, 155, 108)),
    ('roof/composite_sea',   color.rgb( 85, 155, 155)),
    ('roof/asphaltshingle1', color.rgb(105, 100,  95)),
    ('roof/asphaltshingle3', color.rgb(135, 125, 115)),
    ('roof/conetile_red',    color.rgb(205,  85,  68)),
    ('roof/conetile_green',  color.rgb( 68, 148,  88)),
    ('roof/conetile_blue',   color.rgb( 68,  98, 195)),
    ('roof/metal_h',         color.rgb(148, 158, 165)),
    ('roof/blacktile1',      color.rgb( 55,  52,  58)),
    ('roof/scalloped_h',     color.rgb(218, 108,  75)),
]

def build_tree(world, wx, wz):
    trunk = world._create_entity('cylinder', (wx, TREE_H * 0.40, wz),
               (TS * 0.35, TREE_H * 0.80, TS * 0.35), 'tree_trunk', color.rgb(100, 70, 40))
    leaf1 = world._create_entity('sphere', (wx, TREE_H * 1.0, wz),
               (TS * 1.8, TS * 1.5, TS * 1.8), 'cloth_green', color.rgb(60, 140, 40))
    leaf2 = world._create_entity('sphere', (wx + TS*0.2, TREE_H * 1.4, wz - TS*0.2),
               (TS * 1.4, TS * 1.2, TS * 1.4), 'cloth_green', color.rgb(70, 160, 50))
    leaf3 = world._create_entity('sphere', (wx - TS*0.2, TREE_H * 1.3, wz + TS*0.2),
               (TS * 1.2, TS * 1.1, TS * 1.2), 'cloth_green', color.rgb(80, 180, 60))
    world._obj_ents.extend([trunk, leaf1, leaf2, leaf3])

def build_palm(world, wx, wz):
    trunk = world._create_entity('cylinder', (wx, TREE_H * 0.5, wz),
               (TS * 0.25, TREE_H * 1.1, TS * 0.25), 'tree_trunk',
               color.rgb(160, 120, 80), rotation=(5, 0, 8))
    world._obj_ents.append(trunk)
    for i in range(5):
        rad = math.radians(i * 72)
        cx = wx + math.sin(rad) * 0.6
        cz = wz + math.cos(rad) * 0.6
        leaf = world._create_entity('cube', (cx, TREE_H * 1.05 - 0.1, cz),
                  (TS * 0.7, 0.05, TS * 0.3), 'cloth_green',
                  color.rgb(80, 220, 50), rotation=(15, -i * 72 + 90, 0))
        world._obj_ents.append(leaf)
    for i in range(3):
        rad = math.radians(i * 120)
        cx = wx + math.sin(rad) * 0.25
        cz = wz + math.cos(rad) * 0.25
        coconut = world._create_entity('sphere', (cx, TREE_H * 0.95, cz),
                     (0.25, 0.25, 0.25), 'wood_plank', color.rgb(190, 210, 60))
        world._obj_ents.append(coconut)

def build_dead_tree(world, wx, wz):
    trunk = world._create_entity('cylinder', (wx, TREE_H * 0.40, wz),
               (TS * 0.22, TREE_H * 0.80, TS * 0.22), 'tree_trunk', color.rgb(68, 50, 30))
    world._obj_ents.append(trunk)

def build_lantern(world, wx, wz):
    pole = world._create_entity('cylinder', (wx, OBJ_H * 0.45, wz),
              (TS * 0.08, OBJ_H * 0.90, TS * 0.08), 'wood_plank')
    lamp = world._create_entity('cube', (wx, OBJ_H * 0.95, wz),
              (TS * 0.38, 0.40, TS * 0.38), 'lamp_glow')
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
              (TS * 0.85, OBJ_H, TS * 0.85), 'wall_stone', color.rgb(90, 80, 75))
    flame = world._create_entity('sphere', (wx, OBJ_H + GROUND_H + 0.22, wz),
               (TS * 0.40, 0.42, TS * 0.40), 'fire_orange')
    world._obj_ents.extend([base, flame])

def build_grave(world, wx, wz):
    vert  = world._create_entity('cube', (wx, OBJ_H * 0.50 + GROUND_H, wz),
               (TS * 0.16, OBJ_H * 0.90, TS * 0.14), 'grave_stone', color.rgb(112, 100, 122))
    horiz = world._create_entity('cube', (wx, OBJ_H * 0.68 + GROUND_H, wz),
               (TS * 0.52, TS * 0.14, TS * 0.12), 'grave_stone', color.rgb(112, 100, 122))
    world._obj_ents.extend([vert, horiz])

def build_tv(world, wx, wz):
    base = world._create_entity('cube', (wx, OBJ_H*0.2 + GROUND_H, wz), (TS*0.7, OBJ_H*0.4, TS*0.3), 'wood_plank', color.rgb(60,60,60))
    screen = world._create_entity('cube', (wx, OBJ_H*0.7 + GROUND_H, wz), (TS*0.8, OBJ_H*0.6, TS*0.1), None, color.rgb(20,20,30))
    glass = world._create_entity('cube', (wx, OBJ_H*0.7 + GROUND_H, wz - TS*0.06), (TS*0.7, OBJ_H*0.5, 0.05), None, color.rgb(150, 200, 255))
    world._obj_ents.extend([base, screen, glass])

def build_chair(world, wx, wz):
    seat = world._create_entity('cube', (wx, OBJ_H*0.3 + GROUND_H, wz), (TS*0.4, 0.1, TS*0.4), 'wood_plank', color.rgb(130, 90, 50))
    leg1 = world._create_entity('cube', (wx-TS*0.15, OBJ_H*0.15 + GROUND_H, wz-TS*0.15), (0.08, OBJ_H*0.3, 0.08), 'wood_plank', color.rgb(130, 90, 50))
    leg2 = world._create_entity('cube', (wx+TS*0.15, OBJ_H*0.15 + GROUND_H, wz-TS*0.15), (0.08, OBJ_H*0.3, 0.08), 'wood_plank', color.rgb(130, 90, 50))
    leg3 = world._create_entity('cube', (wx-TS*0.15, OBJ_H*0.15 + GROUND_H, wz+TS*0.15), (0.08, OBJ_H*0.3, 0.08), 'wood_plank', color.rgb(130, 90, 50))
    leg4 = world._create_entity('cube', (wx+TS*0.15, OBJ_H*0.15 + GROUND_H, wz+TS*0.15), (0.08, OBJ_H*0.3, 0.08), 'wood_plank', color.rgb(130, 90, 50))
    back = world._create_entity('cube', (wx, OBJ_H*0.65 + GROUND_H, wz+TS*0.15), (TS*0.4, OBJ_H*0.6, 0.08), 'wood_plank', color.rgb(130, 90, 50))
    world._obj_ents.extend([seat, leg1, leg2, leg3, leg4, back])

def build_calendar(world, wx, wz):
    paper = world._create_entity('cube', (wx, WALL_H*0.6 + GROUND_H, wz), (TS*0.4, 0.6, 0.05), None, color.rgb(240, 240, 230))
    bind = world._create_entity('cube', (wx, WALL_H*0.6 + 0.3 + GROUND_H, wz), (TS*0.4, 0.05, 0.07), None, color.rgb(200, 50, 50))
    world._obj_ents.extend([paper, bind])

def build_house_block(world, scene, tx, ty, wx, wz):
    # Check if this is the top-left of an H block
    left_is_H = tx > 0 and scene.tiles[ty][tx-1] == H
    up_is_H = ty > 0 and scene.tiles[ty-1][tx] == H
    if left_is_H or up_is_H:
        return
    
    w_tiles = 1
    while tx + w_tiles < scene.w and scene.tiles[ty][tx + w_tiles] == H:
        w_tiles += 1
    h_tiles = 1
    while ty + h_tiles < scene.h and scene.tiles[ty + h_tiles][tx] == H:
        h_tiles += 1

    center_x = wx + (w_tiles - 1) * TS / 2.0
    center_z = wz + (h_tiles - 1) * TS / 2.0
    scale_x = TS * w_tiles * 0.94
    scale_z = TS * h_tiles * 0.94

    ri = int(abs(math.sin(wx * 31.7 + wz * 47.3)) * len(ROOF_TEXTURES)) % len(ROOF_TEXTURES)
    r_tex, r_col = ROOF_TEXTURES[ri]

    foundation = world._create_entity('cube', (center_x, GROUND_H + 0.10, center_z),
                    (scale_x, 0.20, scale_z), 'wall_stone', color.rgb(188, 172, 145))
    body = world._create_entity('cube', (center_x, HOUSE_H * 0.40 + GROUND_H, center_z),
              (scale_x, HOUSE_H * 0.80, scale_z), 'house_wall', color.rgb(248, 235, 200))
              
    door = world._create_entity('cube', (center_x, HOUSE_H * 0.35 + GROUND_H, center_z + scale_z * 0.5 + 0.02),
              (TS * 0.8, HOUSE_H * 0.6, 0.1), 'wood_plank', color.rgb(100, 60, 30))

    porch = world._create_entity('cube', (center_x, HOUSE_H * 0.65 + GROUND_H, center_z + scale_z * 0.5 + TS * 0.4),
               (TS * 1.2, 0.15, TS * 0.8), r_tex, r_col)
    
    pillar1 = world._create_entity('cylinder', (center_x - TS*0.5, HOUSE_H * 0.32 + GROUND_H, center_z + scale_z * 0.5 + TS * 0.7),
                 (0.1, HOUSE_H * 0.64, 0.1), 'wood_plank', color.rgb(150, 110, 70))
    pillar2 = world._create_entity('cylinder', (center_x + TS*0.5, HOUSE_H * 0.32 + GROUND_H, center_z + scale_z * 0.5 + TS * 0.7),
                 (0.1, HOUSE_H * 0.64, 0.1), 'wood_plank', color.rgb(150, 110, 70))

    roof_y = HOUSE_H * 0.80 + GROUND_H
    from ursina.models.procedural.cone import Cone
    roof1 = world._create_entity(Cone(resolution=4), (center_x, roof_y + HOUSE_H * 0.45, center_z),
               (scale_x * 1.45, HOUSE_H * 0.90, scale_z * 1.45), r_tex, r_col, rotation=(0, 45, 0))
    
    chimney = world._create_entity('cube', (center_x + scale_x * 0.3, HOUSE_H * 1.14 + GROUND_H, center_z - scale_z * 0.2),
                 (TS * 0.2, HOUSE_H * 0.34, TS * 0.2), 'wall_stone', color.rgb(158, 142, 122))
    chimney_cap = world._create_entity('cube', (center_x + scale_x * 0.3, HOUSE_H * 1.30 + GROUND_H, center_z - scale_z * 0.2),
                     (TS * 0.26, 0.08, TS * 0.26), None, color.rgb(90, 80, 72))
    world._obj_ents.extend([foundation, body, door, porch, pillar1, pillar2, roof1, chimney, chimney_cap])

# Ubin penghalang yang ubinnya TIDAK diurus benar oleh world.py di luar ruang.
# Cabang `_make_tile()` untuk penghalang memakai `default_tex` = 'grass', dan
# grass.png di repo ini hampir hitam (rata-rata 44,14,46) — jadi tiap pohon,
# tunggul, lentera, dan peti berdiri di atas kotak hitam. Pagar TIDAK ikut
# terdaftar di sini: world.py sudah punya cabang khusus yang memakai
# 'grass_tso' untuk FN/GT/PEN. Dinding dan bangunan juga tidak: massanya
# menutupi ubinnya sendiri.
# Lihat zone_paint.patch_tile() — ini tambalan sementara, bukan perbaikan.
_TILE_TAMBALAN = (TR, PALM, DT, LN, CH, MB, PP, CL, MR, BS, SH, CT, TB, BD,
                  ST, FP, GR, TV, CHR, CAL, BOT, DR)


def default_prop_builder(world, scene):
    from game.world import OBJ_TEX
    from game.scenes.zone_paint import paint_zone, patch_tile

    outdoor = not getattr(scene, 'indoor', False)

    # ── Lapisan zona ────────────────────────────────────────────────────────
    # Dijalankan LEBIH DULU dari prop supaya urutan gambar tanah → prop, dan
    # supaya daftar zona sudah siap dipakai sebagai penyaring tambalan di bawah.
    zones = getattr(scene, 'paint', None) or ()
    for z in zones:
        paint_zone(world, z.x0, z.y0, z.x1, z.y1, z.base, z.light, z.dark)

    # Scan tiles and place complex props
    for ty in range(scene.h):
        for tx in range(scene.w):
            tid = scene.tiles[ty][tx]
            wx, wz = tx * TS, ty * TS

            # Ubin di dalam zona TIDAK ditambal: lapisan zona sudah menutupi
            # kotak hitamnya, dan menambal di sana justru akan menempelkan
            # petak RUMPUT di tengah ladang tanah.
            if outdoor and tid in _TILE_TAMBALAN and \
                    not any(z.covers(tx, ty) for z in zones):
                patch_tile(world, tx, ty)

            if tid == TR: build_tree(world, wx, wz)
            elif tid == PALM: build_palm(world, wx, wz)
            elif tid == DT: build_dead_tree(world, wx, wz)
            elif tid == LN: build_lantern(world, wx, wz)
            elif tid == FP: build_fireplace(world, wx, wz)
            elif tid == GR: build_grave(world, wx, wz)
            elif tid == TV: build_tv(world, wx, wz)
            elif tid == CHR: build_chair(world, wx, wz)
            elif tid == CAL: build_calendar(world, wx, wz)
            elif tid == H: build_house_block(world, scene, tx, ty, wx, wz)
            elif tid in (ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH, CRYS):
                ore_tex = OBJ_TEX.get(tid, 'crystal')
                build_ore(world, wx, wz, ore_tex)
