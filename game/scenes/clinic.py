from game.config import *
from game.scenes.scene_base import Scene, _build_indoor_room
import random
import math

def build_clinic():
    return _build_indoor_room('clinic', 'Klinik Pak Raka', [
        (1,1,BD),(2,1,BD),(12,1,BD),(13,1,BD),(1,3,TB),(13,3,BS),
    ], ('town', 13, 9))


