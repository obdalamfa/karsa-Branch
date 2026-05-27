from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_dungeon_placeholder():
    W_, H_ = 24, 18
    m = [[CV_F]*W_ for _ in range(H_)]
    for x in range(W_): m[0][x]=CV_W; m[H_-1][x]=CV_W
    for y in range(H_): m[y][0]=CV_W; m[y][W_-1]=CV_W
    return Scene('dungeon', 'Gua Bertingkat', m, portals=[], indoor=True, has_horizon=False)


