from ursina import Entity, Text, color, Vec3
from enum import Enum, auto
import math

class ActorState(Enum):
    IDLE = auto()
    MOVING = auto()
    SLEEPING = auto()

class BaseActor(Entity):
    """
    Base class for all dynamic characters (NPCs, Mobs, Animals) in the game.
    Handles common properties like logical position, scene tracking, and basic movement.
    """
    def __init__(self, state, actor_id, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.actor_id = actor_id
        
        # Logical position (tile coordinates)
        self.logical_x = 0.0
        self.logical_y = 0.0
        
        # Target position for movement
        self.target_x = 0.0
        self.target_y = 0.0
        
        self.scene_name = None
        self.speed = 2.0  # units per second
        self._walk_t = 0.0
        self.is_moving = False
        self.actor_state = ActorState.IDLE

    def load_model(self, model_path):
        """Loads a 3D model for this actor."""
        # Will be implemented using EntityFactory
        pass

    def update_ai(self, dt: float):
        """Base AI update loop. Override in subclasses."""
        pass

    def sync_visuals(self, dt: float, tile_size: float, ground_h: float):
        """Smoothly interpolates visual position towards logical position."""
        tx, ty = self.logical_x * tile_size, self.logical_y * tile_size
        
        dx = tx - self.x
        dz = ty - self.z
        
        # Lerp
        lf = min(1.0, dt * 8)
        self.x += dx * lf
        self.z += dz * lf
        
        self.is_moving = abs(dx) > 0.015 or abs(dz) > 0.015
        if self.is_moving:
            self.actor_state = ActorState.MOVING
        elif self.actor_state == ActorState.MOVING:
            self.actor_state = ActorState.IDLE
            
        if self.is_moving:
            if abs(dx) > abs(dz):
                self.rotation_y = 90 if dx > 0 else -90
            else:
                self.rotation_y = 0 if dz > 0 else 180
            self._walk_t += dt * 16.0
        else:
            self._walk_t += dt * 1.8

    def on_destroy(self):
        """Cleanup logic when the actor is destroyed or removed from the scene."""
        pass
