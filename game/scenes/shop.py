from game.config import *
from game.scenes.scene_base import Scene, _build_indoor_room
import random
import math

def build_shop():
    return _build_indoor_room('shop', 'Warung Bu Sari',
        [(x, 4, CT) for x in range(1,14)] + [(x, 1, SH) for x in range(1,14)],
        ('town', 23, 1))


