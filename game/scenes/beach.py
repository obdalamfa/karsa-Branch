from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_beach():
    W_, H_ = 35, 30
    m = [[W]*W_ for _ in range(H_)]
    # Beach sand from y=0 to y=12
    for y in range(0, 13):
        for x in range(W_): m[y][x] = SD
    # Pathway from town
    for y in range(0, 5):
        m[y][14] = P; m[y][15] = P
    # Docks and broken lighthouse
    for y in range(12, 18):
        for x in range(18, 22): m[y][x] = DCK
    m[17][20] = LGH_B
    # Random debris and trees
    rng = random.Random(77)
    for y in range(0, 12):
        for x in range(W_):
            if x < 12 or x > 20:
                if rng.random() < 0.1: m[y][x] = PALM
                elif rng.random() < 0.05: m[y][x] = DT
    return Scene('beach', 'Pantai Selatan', m, builder=beach_builder, portals=[
        (14, 0, 'town', 6, 23), (15, 0, 'town', 7, 23),
    ])

def beach_builder(world):
    from .props import default_prop_builder
    default_prop_builder(world, world.scene_obj)
    
    if not getattr(world.state, 'lighthouse_fixed', False):
        return
        
    from game.config import TS, GROUND_H
    from ursina import color
    
    base_x = 10 * TS
    base_z = 25 * TS
    y = GROUND_H + 0.2

    hull = world._create_entity('cube', (base_x + 8, y, base_z), (20, 2.5, 6), 'wood_plank', color.rgb(30, 30, 35))
    world._obj_ents.append(hull)

    head = world._create_entity('cube', (base_x - 3, y + 1.5, base_z), (4, 3, 3.5), 'wood_plank', color.rgb(20, 20, 20))
    snout = world._create_entity('cube', (base_x - 5, y + 1.0, base_z), (3, 1.5, 2.5), 'wood_plank', color.rgb(20, 20, 20))
    eye1 = world._create_entity('cube', (base_x - 3, y + 2.0, base_z - 1.8), (0.5, 0.5, 0.2), 'wood_plank', color.rgb(255, 50, 50))
    eye2 = world._create_entity('cube', (base_x - 3, y + 2.0, base_z + 1.8), (0.5, 0.5, 0.2), 'wood_plank', color.rgb(255, 50, 50))
    world._obj_ents.extend([head, snout, eye1, eye2])

    wheel1 = world._create_entity('cylinder', (base_x + 8, y, base_z - 3.5), (4, 1, 4), 'wood_plank', color.rgb(50, 40, 30), rotation=(90,0,0))
    wheel2 = world._create_entity('cylinder', (base_x + 8, y, base_z + 3.5), (4, 1, 4), 'wood_plank', color.rgb(50, 40, 30), rotation=(90,0,0))
    world._obj_ents.extend([wheel1, wheel2])

    mast1 = world._create_entity('cylinder', (base_x + 3, y + 4, base_z), (0.3, 8, 0.3), 'wood_plank', color.rgb(40, 30, 20))
    sail1 = world._create_entity('cube', (base_x + 3, y + 5, base_z), (0.1, 5, 6), None, color.rgb(20, 20, 25))
    mast2 = world._create_entity('cylinder', (base_x + 10, y + 5, base_z), (0.4, 10, 0.4), 'wood_plank', color.rgb(40, 30, 20))
    sail2 = world._create_entity('cube', (base_x + 10, y + 6, base_z), (0.1, 7, 7), None, color.rgb(20, 20, 25))
    world._obj_ents.extend([mast1, sail1, mast2, sail2])


# ─── INDOOR ──────────────────────────────────────────────
