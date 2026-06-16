from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_farm():
    """
    Kebun Paman Arsa — lahan bertani urban di pinggiran kota suram.
    Bukan ladang idilis: pagar kawat berkarat, tumpukan kompos, drum berkarat
    untuk berkebun, tanah setengah subur setengah kering.
    Farming mechanics tetap utuh: D tiles bisa dicangkul/ditanam.
    """
    W_, H_ = 25, 18
    m = [[G] * W_ for _ in range(H_)]

    # ── Rumah pemain (eksterior) ── portal ke house interior
    for y in range(2, 4):
        for x in range(2, 5): m[y][x] = H

    # ── Jalan setapak dari teras ke jalan kebun ──
    m[4][3] = P
    m[4][4] = P
    for y in range(5, 14): m[y][4] = P

    # ── Lahan pertanian utama (bisa dicangkul) ──
    # Petak kiri-tengah
    for y in range(6, 12):
        for x in range(6, 11): m[y][x] = D

    # Petak kanan-tengah
    for y in range(6, 12):
        for x in range(12, 18): m[y][x] = D

    # ── Kandang ternak (sisi kanan-atas) ──
    for y in range(2, 8):
        for x in range(15, 22):
            m[y][x] = STR_T
            if y in (2, 7) or x in (15, 21): m[y][x] = PEN
    m[7][18] = GT   # pintu kandang

    # ── Pagar keliling (kawat berkarat) ──
    for x in range(W_):
        m[0][x] = FN
        m[H_-1][x] = FN
    for y in range(H_):
        m[y][0] = FN
        m[y][W_-1] = P if 12 < y < 16 else FN

    # ── Jalan utama kebun (E-W) ──
    for x in range(4, W_):
        m[14][x] = P
        m[15][x] = P

    # ── Altar kecil di pojok — persembahan sebelum bertani ──
    m[13][2] = SHRINE

    # ── Tumpukan kompos/sampah organik di sudut ──
    m[12][6]  = DEBRIS
    m[5][20]  = DEBRIS
    m[16][20] = DEBRIS

    # ── Pohon tua di sudut (pembatas visual) ──
    m[1][6]  = TR
    m[1][11] = TR
    m[1][20] = DT   # pohon mati di sudut kanan atas
    m[16][6] = DT   # pohon mati di selatan lahan

    # ── Palm tua — sisa kebun lama sebelum jadi lahan ──
    m[1][23] = PALM

    # ── Jemuran di dekat rumah ──
    m[5][2] = LAUNDRY

    return Scene('farm', 'Kebun Paman Arsa', m, builder=farm_builder, portals=[
        (3,  4, 'house', 7, 9),
        (24, 14, 'town',  1, 14),
        (24, 15, 'town',  1, 15),
    ])


def farm_builder(world):
    """Dress kebun dgn props 3D Blender (M2). Tiles tetap diurus default builder."""
    from .props import default_prop_builder
    default_prop_builder(world, world.scene_obj)

    from game.config import TILE_SIZE as TS, GROUND_H
    from ursina import Entity
    try:
        from game.entities import load_model_file, make_obj_entity
    except Exception:
        return

    # (model, tile_x, tile_y, scale, rot_y)
    DRESSING = [
        ('prop_scarecrow',   11, 8,  1.0, 0),    # di antara dua petak
        ('prop_gerobak',      5, 13, 1.0, 90),   # tepi jalan
        ('prop_kandang_ayam',18, 4,  1.0, 0),    # dalam kandang
        ('prop_jerami',      20, 6,  1.0, 0),    # dekat kandang
        ('prop_peti_sayur',   2, 5,  1.0, 0),    # dekat rumah
        ('prop_karung',       2, 6,  1.0, 30),
        ('prop_pagar_kayu',  10, 16, 1.0, 0),    # hiasan tepi jalan selatan
        ('prop_pagar_kayu',  12, 16, 1.0, 0),
        ('prop_ember',        4, 12, 1.0, 0),    # ember di tepi petak
        ('prop_cangkul',      5, 11, 1.0, 40),   # cangkul tersandar di tepi petak
        ('mob_jago',         16, 8,  1.0, -20),  # ayam jantan berkokok dekat kandang
    ]
    for name, tx, ty, sc, ry in DRESSING:
        e = make_obj_entity(name, (tx * TS, GROUND_H, ty * TS), scale=sc, rot_y=ry)
        if e is not None:
            world._obj_ents.append(e)

    # ── Peti Kirim (shipping bin) — dekat rumah, ditandai krat + papan kuning ──
    from game.config import SHIP_BIN_TILE
    bx, bz = SHIP_BIN_TILE[0] * TS, SHIP_BIN_TILE[1] * TS
    bin_mdl = load_model_file('prop_peti_sayur')
    if bin_mdl:
        world._obj_ents.append(Entity(model=bin_mdl, position=(bx, GROUND_H, bz), scale=1.3))
    from ursina import color as _c
    sign = Entity(model='cube', position=(bx, GROUND_H + 1.2, bz),
                  scale=(0.5, 0.28, 0.06), color=_c.rgb(231, 178, 61))
    world._obj_ents.append(sign)
