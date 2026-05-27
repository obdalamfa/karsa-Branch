from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_lake():
    W_, H_ = 18, 14
    m = [[G]*W_ for _ in range(H_)]
    for y in range(2, 12):
        for x in range(3, 16): m[y][x] = W
    for x in range(3, 8): m[7][x] = DCK
    m[8][7] = DCK; m[7][9] = BOT
    for x, y in [(5,4),(12,5),(14,8),(11,10),(6,10),(13,3)]:
        if 0<=x<W_ and 0<=y<H_ and m[y][x]==W: m[y][x] = LLY
    rng = random.Random(50)
    for y in range(H_):
        for x in [0, W_-2]:
            if rng.random() < 0.4: m[y][x] = TR
    m[7][0]=P; m[8][0]=P; m[7][1]=P; m[8][1]=P
    m[12][2]=DT; m[3][3]=DT
    return Scene('lake', 'Danau Karsa', m, portals=[
        (0, 7, 'town', 28, 14), (0, 8, 'town', 28, 15),
    ])


