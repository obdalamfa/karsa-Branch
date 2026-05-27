from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_naga_cave():
    W_, H_ = 15, 12
    m = [[CV_F]*W_ for _ in range(H_)]
    for x in range(W_): m[0][x]=CV_W; m[H_-1][x]=CV_W
    for y in range(H_): m[y][0]=CV_W; m[y][W_-1]=CV_W
    m[H_-1][7] = DR
    for x, y in [(2,2),(12,2),(2,9),(12,9),(3,4),(11,6)]:
        m[y][x] = CV_W
    m[10][13] = STAIRS_DOWN
    m[5][7] = STAIRS_UP
    # Lentera obor di dinding cave supaya tidak gelap total
    for x, y in [(1,3),(13,3),(1,7),(13,7),(1,10),(6,1),(9,1)]:
        m[y][x] = LN
    return Scene('naga_cave', 'Gua Sang Hyang', m, portals=[
        (7, 11, 'mountain', 14, 4),
        (7, 5, 'swarga', 15, 20),
    ], indoor=True, has_horizon=False)


