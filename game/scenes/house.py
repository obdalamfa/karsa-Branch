from game.config import *
from game.scenes.scene_base import Scene, _build_indoor_room
import random
import math

def build_house():
    return _build_indoor_room('house', 'Rumah Kamu', [
        (1,1,BD),(2,1,BD),(1,2,CH),(4,1,BS),(5,1,BS),(1,3,MR),(1,4,PP),
        (7,1,FP),(9,1,CL),(10,1,CAL),(6,3,TB),(7,3,TB),(6,2,CHR),(7,2,CHR),
        (11,1,ST),(12,1,ST),(11,2,CT),(12,2,CT),(13,1,SH),(3,3,TV),(3,4,CHR)
    ], ('farm', 3, 5))


