from game.config import *
from game.scenes.scene_base import Scene, _build_indoor_room
import random
import math

def build_studio():
    return _build_indoor_room('studio', 'Studio Maya', [
        (6,1,TB),(7,1,TB),(8,1,TB),(1,3,BS),(2,3,BS),
    ], ('town', 23, 10))


