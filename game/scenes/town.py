from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_town():
    W_, H_ = 30, 25
    m = [[G]*W_ for _ in range(H_)]
    for y in range(13, 17):
        for x in range(W_): m[y][x] = P
    for y in range(H_):
        for x in range(13, 17): m[y][x] = P
    for y in range(5, 9):
        for x in range(2, 7):   m[y][x] = H
        for x in range(9, 14):  m[y][x] = H
        for x in range(20, 25): m[y][x] = H
    m[8][4] = DR; m[8][11] = DR; m[8][22] = DR
    for y in range(18, 22):
        for x in range(5, 10):  m[y][x] = H
        for x in range(19, 24): m[y][x] = H
    m[21][7] = DR; m[21][21] = DR
    m[12][12] = LN; m[12][17] = LN; m[17][12] = LN; m[17][17] = LN
    for x in range(11, 19): m[14][x] = CT
    return Scene('town', 'Desa Karsa', m, portals=[
        (0, 14, 'farm', 26, 9), (0, 15, 'farm', 26, 10),
        (14, 0, 'mountain', 14, 23), (15, 0, 'mountain', 15, 23),
        (29, 14, 'lake', 1, 7), (29, 15, 'lake', 1, 8),
        (4, 8, 'shop', 7, 9), (11, 8, 'clinic', 7, 9), (22, 8, 'studio', 7, 9),
        (7, 21, 'smith', 7, 9),
        (14, 24, 'beach', 14, 1), (15, 24, 'beach', 15, 1),
    ])


