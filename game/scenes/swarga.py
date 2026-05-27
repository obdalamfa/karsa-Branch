from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_swarga():
    W_, H_ = 31, 31
    # Base is empty cave floor (which will just be empty space or we can use W for sky/clouds)
    # Actually, we will make a cross/diamond shape of CLOUD tiles
    m = [[CV_F]*W_ for _ in range(H_)]
    
    # Symmetrical cloud island
    cx, cy = 15, 15
    for y in range(H_):
        for x in range(W_):
            dist = abs(x - cx) + abs(y - cy)
            if dist <= 12:
                m[y][x] = CLOUD
                
    # Golden pillars and structures
    for x, y in [(5,15), (25,15), (15,5), (15,25), (10,10), (20,10), (10,20), (20,20)]:
        m[y][x] = GOLD_W
        
    # Fountain in center
    m[15][15] = W
    m[14][15] = GOLD_W; m[16][15] = GOLD_W
    m[15][14] = GOLD_W; m[15][16] = GOLD_W

    m[21][15] = STAIRS_DOWN
    
    return Scene('swarga', 'Swarga (Dunia Langit)', m, portals=[
        (15, 21, 'naga_cave', 7, 6)
    ], indoor=False)

