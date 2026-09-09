from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_greenhouse():
    """
    Rumah Kaca — kebun bertahan hidup darurat di dalam gedung tua.
    Bukan greenhouse mewah: kaca retak, tanaman tumbuh seadanya,
    alat berkarat digantung di dinding. Tapi tanaman TUMBUH di sini —
    itu yang penting. Farming mechanics penuh: D bisa dicangkul.
    """
    W_, H_ = 15, 12
    m = [[FL] * W_ for _ in range(H_)]

    # ── Dinding ──
    for x in range(W_):
        m[0][x]      = WL
        m[H_-1][x]   = WL
    for y in range(H_):
        m[y][0]      = WL
        m[y][W_-1]   = WL

    # ── Pintu keluar ──
    m[H_-1][7] = DR

    # ── 4 petak lahan (D) — bisa dicangkul, ditanam, disiram, dipanen ──
    for x in range(2, 6):
        for y in range(1, 4): m[y][x] = D   # NW bed
    for x in range(9, 13):
        for y in range(1, 4): m[y][x] = D   # NE bed
    for x in range(2, 6):
        for y in range(6, 10): m[y][x] = D  # SW bed
    for x in range(9, 13):
        for y in range(6, 10): m[y][x] = D  # SE bed

    # ── Lampu tumbuh (FP) di sudut — sumber panas ──
    m[1][1]  = FP
    m[1][13] = FP
    m[10][1] = FP
    m[10][13]= FP

    # ── Meja kerja dan rak alat ──
    m[4][1]  = TB;  m[5][1]  = TB
    m[4][13] = TB;  m[5][13] = TB
    m[4][7]  = TB   # meja tengah untuk kerja

    m[6][1]  = SH   # rak alat kiri
    m[6][13] = SH   # rak alat kanan

    # ── Peti penyimpanan benih ──
    m[7][7]  = CH

    # ── Tanaman pot (contoh tanaman di dalam) ──
    m[5][7]  = PP

    from game.scenes.scene_base import _add_indoor_atmosphere

    def _greenhouse_builder(world):
        from game.scenes.props import default_prop_builder
        default_prop_builder(world, scene_gh)
        _add_indoor_atmosphere(world, scene_gh, 'greenhouse')

    scene_gh = Scene('greenhouse', 'Rumah Kaca', m,
                     portals=[(7, 11, 'town', 21, 22)], indoor=True,
                     builder=_greenhouse_builder)
    return scene_gh
