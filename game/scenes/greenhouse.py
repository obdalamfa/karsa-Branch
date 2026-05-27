from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_greenhouse():
    W_, H_ = 15, 12
    m = [[FL]*W_ for _ in range(H_)]
    for x in range(W_): m[0][x]=WL; m[H_-1][x]=WL
    for y in range(H_): m[y][0]=WL; m[y][W_-1]=WL
    m[H_-1][7] = DR
    # 4 farmable dirt beds (bisa dicangkul, ditanam, disiram, dipanen)
    for x in range(2, 6):
        for y in range(1, 4): m[y][x] = D   # NW bed
    for x in range(9, 13):
        for y in range(1, 4): m[y][x] = D   # NE bed
    for x in range(2, 6):
        for y in range(6, 10): m[y][x] = D  # SW bed
    for x in range(9, 13):
        for y in range(6, 10): m[y][x] = D  # SE bed
    # Grow-lamp (FP) di pojok agar terlihat warm & greenhouse
    m[1][1] = FP; m[1][13] = FP
    # Meja kerja (TB) dan rak penyimpanan (SH) di sisi tengah
    m[4][1] = TB; m[5][1] = SH
    m[4][13] = TB; m[5][13] = SH
    return Scene('greenhouse', 'Rumah Kaca', m,
                 portals=[(7, 11, 'town', 21, 22)], indoor=True)


