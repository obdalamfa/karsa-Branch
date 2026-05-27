from enum import Enum, auto
from .base_actor import BaseActor
from .config import NPC_SPEED, TILE_SIZE
import math
import random

class NPCState(Enum):
    IDLE = auto()
    WANDER = auto()
    PATHFINDING = auto()
    SLEEPING = auto()

class NPC(BaseActor):
    """
    Friendly characters that follow schedules, pathfinding, and have dialogue.
    """
    def __init__(self, state, actor_id, **kwargs):
        super().__init__(state, actor_id, **kwargs)
        self.speed = NPC_SPEED / (TILE_SIZE * 20)
        self.path = []
        self.activity = ''
        self.sched_x = 0
        self.sched_y = 0
        self.ai_state = NPCState.IDLE

    def update_ai(self, dt: float, brains, can_walk_fn):
        if self.activity == 'sleeping':
            self.ai_state = NPCState.SLEEPING
            return

        is_moving = abs(self.logical_x - self.target_x) > 0.02 or abs(self.logical_y - self.target_y) > 0.02
        
        if not is_moving and self.path:
            nxt = self.path.pop(0)
            self.target_x, self.target_y = float(nxt[0]), float(nxt[1])
            is_moving = True
            self.ai_state = NPCState.PATHFINDING
            
        if self.ai_state != NPCState.SLEEPING and not is_moving and random.random() < 0.012:
            self.ai_state = NPCState.WANDER
            dx = random.choice([-2, -1, 0, 1, 2])
            dy = random.choice([-2, -1, 0, 1, 2])
            nx = int(self.sched_x) + dx
            ny = int(self.sched_y) + dy
            if can_walk_fn(nx, ny):
                if brains is not None:
                    new_path = brains.plan_path(self.logical_x, self.logical_y, nx, ny)
                    if new_path:
                        self.path = new_path
                        self.ai_state = NPCState.PATHFINDING
                    else:
                        self.target_x, self.target_y = float(nx), float(ny)
                else:
                    self.target_x, self.target_y = float(nx), float(ny)
                    
        if not is_moving and self.ai_state != NPCState.SLEEPING and not self.path:
            self.ai_state = NPCState.IDLE
                    
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
