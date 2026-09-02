from enum import Enum, auto
from .base_actor import BaseActor
from .config import NPC_SPEED, TILE_SIZE
import math
import random

class AnimalState(Enum):
    IDLE = auto()
    WANDER = auto()
    SLEEPING = auto()

class FarmAnimal(BaseActor):
    """
    Farm animals handling wandering inside bounds and interactions.
    """
    def __init__(self, state, actor_id, **kwargs):
        super().__init__(state, actor_id, **kwargs)
        self.speed = NPC_SPEED / (TILE_SIZE * 20)
        self.animal_pen = (3, 3, 22, 12)  # default bounds
        self.ai_state = AnimalState.IDLE

    def set_bounds(self, bounds):
        self.animal_pen = bounds

    def ayun_kaki(self, dt: float, laju: float = 1.0):
        """Ayunkan keempat kaki mengikuti `_walk_t`.

        Kaki depan-kiri sefase dengan belakang-kanan, dan sebaliknya — itu
        pola langkah berkaki empat, bukan empat kaki yang berayun serempak.
        Urutan `_kaki` dari `_legs()`: (-x,-z), (-x,+z), (+x,-z), (+x,+z).
        """
        kaki = getattr(self, '_kaki', None)
        if not kaki:
            return
        amp = 26.0 * laju
        for i, k in enumerate(kaki):
            fase = 0.0 if (i in (0, 3)) else math.pi
            try:
                k.rotation_x = math.sin(self._walk_t + fase) * amp
            except Exception:
                pass

    def update_ai(self, dt: float, can_walk_fn):
        if self.state.is_night():
            self.target_x = self.logical_x
            self.target_y = self.logical_y
            self.ai_state = AnimalState.SLEEPING
            return
            
        is_moving = abs(self.logical_x - self.target_x) > 0.02 or abs(self.logical_y - self.target_y) > 0.02
        
        if not is_moving and random.random() < 0.015:
            self.ai_state = AnimalState.WANDER
            bounds = self.animal_pen
            nx = max(bounds[0], min(bounds[2], int(self.logical_x) + random.choice([-1, 0, 0, 1])))
            ny = max(bounds[1], min(bounds[3], int(self.logical_y) + random.choice([-1, 0, 0, 1])))
            if can_walk_fn(nx, ny):
                self.target_x, self.target_y = float(nx), float(ny)
                
        if not is_moving and self.ai_state != AnimalState.SLEEPING:
            self.ai_state = AnimalState.IDLE
                
        # Lerp movement logic
        dx = self.target_x - self.logical_x
        dy = self.target_y - self.logical_y
        dist = math.hypot(dx, dy)
        move = self.speed * (dt * 1000)
        
        if dist <= move:
            self.logical_x, self.logical_y = float(self.target_x), float(self.target_y)
        elif dist > 0:
            self.logical_x += (dx / dist) * move
            self.logical_y += (dy / dist) * move
