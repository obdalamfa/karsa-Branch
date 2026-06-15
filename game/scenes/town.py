from game.config import *
from game.scenes.scene_base import Scene
import random
import math

# Import tile types bangunan berportal (eksterior bertema)
from game.config import SHOP_EXT, CLINIC_EXT, SMITH_EXT, GREENHOUSE_EXT

def build_town():
    """
    Desa Karsa — district suram ala Martinaise Nusantara.
    Hub-based layout: jalan utama sempit, bangunan saling menghimpit,
    graffiti, jemuran, tumpukan sampah, warung malam di persimpangan.
    Portals dipertahankan di posisi persis sama.
    """
    W_, H_ = 30, 25
    m = [[G] * W_ for _ in range(H_)]

    # ── Jalan utama (dua koridor) ──────────────────────────────────────────
    # Jalur N-S (vertikal) — 2 tile lebar
    for y in range(H_):
        m[y][13] = P
        m[y][14] = P

    # Jalur E-W (horizontal) — 2 tile lebar
    for x in range(W_):
        m[13][x] = P
        m[14][x] = P

    # Gang kecil selatan
    for x in range(W_):
        m[20][x] = P

    # Gang kecil utara (menuju daerah perumahan atas)
    for y in range(0, 9):
        m[y][7] = P
        m[y][21] = P

    # ── BANGUNAN ZONA UTARA ────────────────────────────────────────────────

    # Toko (shop) — portal tetap di (4,8)
    for y in range(5, 8):
        for x in range(2, 7): m[y][x] = SHOP_EXT
    m[8][4] = DR

    # Klinik (clinic) — portal tetap di (11,8)
    for y in range(5, 8):
        for x in range(9, 13): m[y][x] = CLINIC_EXT
    m[8][11] = DR

    # Studio (studio) — portal tetap di (22,8) — sebagai RUMAH_PG
    for y in range(5, 8):
        for x in range(19, 24): m[y][x] = RUMAH_PG
    m[8][22] = DR

    # Rumah panggung di sudut kiri atas
    for y in range(1, 4):
        for x in range(1, 4): m[y][x] = RUMAH_PG

    # Rumah panggung di sudut kanan atas
    for y in range(1, 5):
        for x in range(25, 29): m[y][x] = RUMAH_PG

    # Rumah biasa di antara klinik dan gang
    for y in range(2, 5):
        for x in range(16, 20): m[y][x] = H

    # ── UNION HALL — gedung besar di pusat (tidak ada portal di sana) ──
    for y in range(9, 13):
        for x in range(17, 23): m[y][x] = UNION_HL

    # ── BANGUNAN ZONA SELATAN ──────────────────────────────────────────────

    # Bengkel/smith — portal tetap di (7,21)
    for y in range(17, 21):
        for x in range(5, 9): m[y][x] = SMITH_EXT
    m[21][7] = DR

    # Greenhouse — portal tetap di (21,21)
    for y in range(17, 21):
        for x in range(18, 23): m[y][x] = GREENHOUSE_EXT
    m[21][21] = DR

    # Rumah panggung di selatan kiri
    for y in range(21, 24):
        for x in range(10, 13): m[y][x] = RUMAH_PG

    # Rumah di selatan kanan
    for y in range(21, 24):
        for x in range(25, 29): m[y][x] = H

    # ── LAPAK PASAR (CT) — di persimpangan tengah ──────────────────────────
    # Baris lapak utara persimpangan
    for x in range(15, 22): m[11][x] = CT
    # Baris lapak di bawah union hall
    for x in range(15, 22): m[15][x] = CT

    # ── WARUNG MALAM (WARUNG) — di persimpangan strategis ──────────────────
    m[12][3]  = WARUNG   # warung barat (dekat gang)
    m[15][26] = WARUNG   # warung timur
    m[12][26] = WARUNG   # warung pojok timur

    # ── ALTAR/SHRINE di persimpangan ───────────────────────────────────────
    m[14][6]  = SHRINE   # persimpangan kiri
    m[13][24] = SHRINE   # persimpangan kanan
    m[19][3]  = SHRINE   # selatan kiri

    # ── TUMPUKAN SAMPAH (DEBRIS) ────────────────────────────────────────────
    m[3][8]   = DEBRIS
    m[4][17]  = DEBRIS
    m[10][3]  = DEBRIS
    m[10][25] = DEBRIS
    m[16][3]  = DEBRIS
    m[22][16] = DEBRIS
    m[23][24] = DEBRIS

    # ── JEMURAN (LAUNDRY) ─────────────────────────────────────────────────
    m[9][2]   = LAUNDRY
    m[4][24]  = LAUNDRY
    m[16][11] = LAUNDRY
    m[22][4]  = LAUNDRY
    m[22][26] = LAUNDRY

    # ── DINDING GRAFFITI ──────────────────────────────────────────────────
    m[9][8]   = GRAFFITI_W
    m[9][15]  = GRAFFITI_W
    m[16][24] = GRAFFITI_W
    m[22][13] = GRAFFITI_W

    # ── LAMPU JALAN (LN) di persimpangan utama ─────────────────────────────
    m[12][12] = LN;  m[12][15] = LN
    m[15][12] = LN;  m[15][15] = LN

    # ── POHON & TANAMAN ────────────────────────────────────────────────────
    # Pohon tua di tepi area
    m[1][9]  = TR;  m[1][11] = TR
    m[2][25] = TR;  m[3][27] = TR
    m[23][1] = TR;  m[24][3] = TR
    m[23][27]= TR

    # Pohon mati (saksi bisu kota yang reot)
    m[3][5]  = DT
    m[10][28]= DT
    m[17][15]= DT
    m[22][9] = DT
    m[24][19]= DT

    # Palm tua di sisi selatan (sisa kebun lama)
    m[22][25]= PALM
    m[1][27] = PALM

    return Scene('town', 'Desa Karsa', m, builder=town_builder, portals=[
        (0,  14, 'farm',       23, 14),
        (0,  15, 'farm',       23, 15),
        (14,  0, 'mountain',   14, 23),
        (15,  0, 'mountain',   15, 23),
        (29, 14, 'lake',        1,  7),
        (29, 15, 'lake',        1,  8),
        (4,   8, 'shop',        7,  9),
        (11,  8, 'clinic',      7,  9),
        (22,  8, 'studio',      7,  9),
        (7,  21, 'smith',       7,  9),
        (21, 21, 'greenhouse',  7,  9),
        (14, 24, 'beach',      14,  1),
        (15, 24, 'beach',      15,  1),
    ])


def town_builder(world):
    """Dress Desa Karsa dgn struktur kampung 3D Blender yg sebelumnya tak terpakai
    (sumur, rumah kampung/limasan/joglo, warung, lentera, pagar & pohon bambu)."""
    from .props import default_prop_builder
    default_prop_builder(world, world.scene_obj)

    from game.config import TILE_SIZE as TS, GROUND_H
    from ursina import Entity
    try:
        from game.entities import load_model_file
    except Exception:
        return

    # (model, tile_x, tile_y, scale, rot_y) — taruh di tepi/ruang kosong rumput
    VILLAGE = [
        ('sumur',           16, 18, 1.4, 0),    # sumur umum di ruang terbuka
        ('rumah_kampung',   10, 17, 1.0, 25),   # rumah dekorasi kampung
        ('rumah_limasan',   24, 17, 1.0, -25),
        ('rumah_joglo',     24, 11, 1.0, 0),    # joglo besar (pojok timur-tengah)
        ('warung',           3, 16, 1.0, 20),   # warung obj (selain WARUNG prosedural)
        ('lantern',         12, 16, 2.4, 0),    # lentera persimpangan
        ('lantern',         17, 16, 2.4, 0),
        ('lantern',         11, 22, 2.4, 0),
        ('pagar_bambu',     15, 18, 1.0, 0),    # segmen pagar bambu
        ('pagar_bambu',     17, 18, 1.0, 0),
        ('pohon_bambu',      2, 11, 1.2, 0),    # rumpun bambu tepi
        ('pohon_bambu',     28, 18, 1.2, 0),
    ]
    for name, tx, ty, sc, ry in VILLAGE:
        mdl = load_model_file(name)
        if not mdl:
            continue
        world._obj_ents.append(
            Entity(model=mdl, position=(tx * TS, GROUND_H, ty * TS),
                   scale=sc, rotation=(0, ry, 0)))
