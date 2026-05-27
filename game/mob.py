from ursina import color, Entity
from enum import Enum, auto
from .base_actor import BaseActor
from .config import INVULN_AFTER_HIT_MS, TILE_SIZE
import math
import random

class MobState(Enum):
    PATROL = auto()
    ALERT = auto()
    CHASE = auto()
    ATTACK = auto()
    DEAD = auto()

class Monster(BaseActor):
    """
    Hostile mobs with patrol, alert, and chase states.
    """
    def __init__(self, state, actor_id, mob_spec, **kwargs):
        super().__init__(state, actor_id, **kwargs)
        self.mob_spec = mob_spec
        self.kind = mob_spec['kind']
        self.hp = mob_spec.get('hp', 20)
        self.damage = mob_spec.get('damage', 5)
        self.speed = mob_spec.get('speed', 2.0)
        self.is_boss = mob_spec.get('is_boss', False)
        
        self.logical_x = mob_spec.get('x', 0)
        self.logical_y = mob_spec.get('y', 0)
        
        self.ai_state = MobState.PATROL
        self.alert_r = 10.0 if self.is_boss else 5.0
        self.chase_r = 14.0 if self.is_boss else 8.0
        self.atk_r = 1.5 if self.is_boss else 1.0
        
        self.patrol_t = 0.0
        self.patrol_interval = random.uniform(1.5, 3.5)
        self.patrol_dx = 0
        self.patrol_dy = 0
        
        self.attack_cooldown_ms = 0
        self.dmg_flash_ms = 0

    def update_ai(self, dt: float, player_x: float, player_y: float, can_walk_fn):
        if self.hp <= 0:
            self.ai_state = MobState.DEAD
            return
            
        if self.dmg_flash_ms > 0:
            self.dmg_flash_ms = max(0, self.dmg_flash_ms - dt * 1000)
        if self.attack_cooldown_ms > 0:
            self.attack_cooldown_ms = max(0, self.attack_cooldown_ms - dt * 1000)
            
        dist = math.hypot(self.logical_x - player_x, self.logical_y - player_y)
        
        # State transitions
        if dist <= self.alert_r:
            self.ai_state = MobState.CHASE
        elif dist <= self.chase_r:
            if self.ai_state == MobState.PATROL:
                self.ai_state = MobState.ALERT
        else:
            self.ai_state = MobState.PATROL
            
        # Behavior based on state
        if self.ai_state == MobState.PATROL:
            self.patrol_t += dt
            if self.patrol_t >= self.patrol_interval:
                self.patrol_t = 0.0
                self.patrol_interval = random.uniform(1.5, 3.5)
                self.patrol_dx = random.choice([-1, 0, 0, 1])
                self.patrol_dy = random.choice([-1, 0, 0, 1])
            
            if self.patrol_dx != 0 or self.patrol_dy != 0:
                spd = self.speed * 0.4 / TILE_SIZE * dt
                nx = self.logical_x + self.patrol_dx * spd
                ny = self.logical_y + self.patrol_dy * spd
                if can_walk_fn(nx, self.logical_y): self.logical_x = nx
                if can_walk_fn(self.logical_x, ny): self.logical_y = ny
                
        elif self.ai_state in (MobState.ALERT, MobState.CHASE):
            if dist > 0.3:
                spd_mult = 1.6 if self.ai_state == MobState.ALERT else 1.0
                spd = self.speed * spd_mult / TILE_SIZE * dt
                dx = (player_x - self.logical_x) / dist
                dy = (player_y - self.logical_y) / dist
                nx = self.logical_x + dx * spd
                ny = self.logical_y + dy * spd
                if can_walk_fn(nx, self.logical_y): self.logical_x = nx
                if can_walk_fn(self.logical_x, ny): self.logical_y = ny
                
        # Attack logic
        if dist <= self.atk_r and self.attack_cooldown_ms <= 0:
            if self.state.invuln_timer_ms <= 0:
                self.state.hp = max(0, self.state.hp - self.damage)
                self.state.invuln_timer_ms = INVULN_AFTER_HIT_MS
                self.ai_state = MobState.ATTACK
            self.attack_cooldown_ms = 1000
