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
        self._walk_anim_t = 0.0

    def set_bounds(self, bounds):
        self.animal_pen = bounds

    def update_anim(self, dt: float):
        """Animasikan bagian visual hewan berdasarkan state gerakan."""
        body = getattr(self, '_anim_body', None)
        if body is None:
            return

        head    = getattr(self, '_anim_head', None)
        legs    = getattr(self, '_anim_legs', [])
        tail    = getattr(self, '_anim_tail', None)
        body_y0 = getattr(self, '_anim_body_y', 0.5)
        head_y0 = getattr(self, '_anim_head_y', 0.9)

        is_sleeping = (self.ai_state == AnimalState.SLEEPING)
        is_moving   = (abs(self.logical_x - self.target_x) > 0.02 or
                       abs(self.logical_y - self.target_y) > 0.02)

        if is_sleeping:
            self._walk_anim_t += dt * 0.8
            t = self._walk_anim_t
            body.y = body_y0 + math.sin(t) * 0.008 - 0.04
            for leg in legs:
                leg.rotation_x = leg.rotation_x * max(0.0, 1.0 - dt * 6)
        elif is_moving:
            self._walk_anim_t += dt * 8.0
            t = self._walk_anim_t
            swing = math.sin(t)
            body.y = body_y0 + abs(swing) * 0.03
            if head:
                head.y = head_y0 + abs(swing) * 0.035
            for i, leg in enumerate(legs):
                # FL/BR in-phase, FR/BL in-phase (diagonal gait)
                phase = math.pi if (i == 1 or i == 2) else 0.0
                leg.rotation_x = math.sin(t + phase) * 30
            if tail:
                tail.rotation_z = math.sin(t * 1.5) * 12
        else:
            self._walk_anim_t += dt * 1.8
            t = self._walk_anim_t
            # Reset legs toward neutral
            for leg in legs:
                leg.rotation_x *= max(0.0, 1.0 - dt * 8)
            # Idle tail wag
            if tail:
                tail.rotation_z = math.sin(t * 2.2) * 18
                tail.rotation_x = math.sin(t * 1.3) * 6
            # Gentle head sway
            if head:
                head.y = head_y0 + math.sin(t * 0.9) * 0.012
            # Breathing body
            body.y = body_y0 + math.sin(t * 0.7) * 0.012

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
