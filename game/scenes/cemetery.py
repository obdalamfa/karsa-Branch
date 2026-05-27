from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_cemetery():
    W_, H_ = 18, 22
    m = [[D]*W_ for _ in range(H_)]
    for x in range(W_): m[0][x]=DT; m[H_-1][x]=DT
    for y in range(H_): m[y][0]=DT; m[y][W_-1]=DT
    for y in range(1, H_-1): m[y][8]=P; m[y][9]=P
    for row in [3,6,9,12,15,18]:
        for col in [2,4,6,11,13,15]: m[row][col]=GR
    m[2][2]=LN; m[2][15]=LN; m[19][2]=LN; m[19][15]=LN
    m[10][3]=DT; m[14][14]=DT; m[7][12]=DT; m[16][5]=DT
    m[0][8]=GT; m[0][9]=GT
    return Scene('cemetery', 'Kuburan Tua', m, portals=[
        (8, 0, 'mountain', 2, 23), (9, 0, 'mountain', 2, 23),
    ])


