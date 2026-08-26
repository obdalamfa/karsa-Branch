from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_farm():
    W_, H_ = 25, 18
    m = [[G]*W_ for _ in range(H_)]
    
    # Menaruh ubin bangunan rumah eksterior (H) setebal 3x2 tile di sisi kiri kebun
    for y in range(2, 4):
        for x in range(2, 5):
            m[y][x] = H
            
    # Jalan setapak dari teras depan pintu rumah (3,4) ke jalan raya utama kebun
    m[4][3] = P
    m[4][4] = P

    # Peti Kirim: satu-satunya cara menjual tanpa berjalan ke Warung (85%
    # harga). Ditaruh menempel jalan setapak keluar rumah supaya pemain
    # melewatinya setiap pagi dan tidak mungkin tidak menemukannya.
    m[4][6] = CH
    for y in range(5, 14):
        m[y][4] = P

    for y in range(2, 8):
        for x in range(15, 22):
            m[y][x] = STR_T
            if y in (2, 7) or x in (15, 21): m[y][x] = PEN
    m[7][18] = GT
    for x in range(W_): m[0][x] = FN; m[H_-1][x] = FN
    for y in range(H_):
        m[y][0] = FN
        m[y][W_-1] = P if 12 < y < 16 else FN
    for x in range(4, W_): m[14][x] = P; m[15][x] = P
    return Scene('farm', 'Kebun Paman Arsa', m, portals=[
        (3, 4, 'house', 7, 9),
        (24, 14, 'town', 1, 14),
        (24, 15, 'town', 1, 15),
    ])


