from game.config import *
from game.scenes.scene_base import Scene, _build_indoor_room
import random
import math

def build_smith():
    return _build_indoor_room('smith', 'Bengkel Budi', [
        (6,1,TB),(1,2,SH),(12,1,FP),(8,1,SH),(9,1,SH),
    ], ('town', 7, 22))


