from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_mountain():
    W_, H_ = 30, 25
    m = [[G]*W_ for _ in range(H_)]
    rng = random.Random(42)
    for y in range(0, 4):
        for x in range(W_): m[y][x] = CV_W
    m[3][14] = DR; m[3][15] = DR
    for y in range(4, H_):
        for x in range(W_):
            if x < 12 or x > 18:
                if rng.random() < 0.2: m[y][x] = TR
            elif y > 10 and rng.random() < 0.1: m[y][x] = DT
    for y in range(4, H_): m[y][14] = D; m[y][15] = D
    for y in range(20, 23):
        for x in range(3, 7):
            if (x+y) % 2 == 0: m[y][x] = GR
    for y in range(20, 25): m[y][2] = P
    return Scene('mountain', 'Lereng Gunung', m, portals=[
        (14, 24, 'town', 14, 1), (15, 24, 'town', 15, 1),
        (14, 3, 'naga_cave', 7, 9), (15, 3, 'naga_cave', 7, 9),
        (2, 24, 'cemetery', 8, 1),
    ])


