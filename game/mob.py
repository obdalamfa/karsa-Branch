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

# Gaya serang per jenis: (windup ms, jangkauan petak, jeda sesudah pukul ms,
# terjang petak). Dulu semua mob sama persis (380 ms, 1 petak, 1000 ms):
# kelelawar yang gesit dan genderuwo yang berat terasa satu makhluk.
#   windup   cepat = sulit dielak, pendek jangkauannya
#   terjang  di ujung windup mob MELOMPAT maju sejauh ini sebelum pukulan
#            diperiksa -- mundur satu langkah tidak cukup melawan kelelawar
GAYA_SERANG = {
    'kelelawar':  (260, 0.9, 750,  0.8),
    'tikus_gua':  (240, 0.8, 700,  0.6),
    'genderuwo':  (560, 1.5, 1400, 0.0),
    'banaspati':  (440, 1.6, 1300, 0.0),
    'kuntilanak': (380, 1.1, 1050, 0.5),
    'leak':       (340, 1.2, 950,  0.7),
    'pocong':     (500, 1.3, 1300, 0.9),
}
GAYA_BOS = (620, 1.9, 1500, 0.0)


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
        g = GAYA_BOS if self.is_boss else GAYA_SERANG.get(self.kind, (380, 1.0, 1000, 0.0))
        self.windup_gaya, self.atk_r, self.cd_total, self.terjang = g
        
        self.patrol_t = 0.0
        self.patrol_interval = random.uniform(1.5, 3.5)
        self.patrol_dx = 0
        self.patrol_dy = 0
        
        self.attack_cooldown_ms = 0
        self.dmg_flash_ms = 0
        # Telegraph serangan: jeda wind-up sebelum pukulan mendarat
        self.windup_ms = 0
        self.windup_total = 1
        self.telegraph_ms = 0
        # Animasi kematian: tumbang + menyusut sebelum dihapus
        self.dying = False
        self.death_ms = 0

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
            # Diam saat sedang wind-up (telegraph) supaya peringatan terbaca
            if dist > 0.3 and self.windup_ms <= 0:
                spd_mult = 1.6 if self.ai_state == MobState.ALERT else 1.0
                spd = self.speed * spd_mult / TILE_SIZE * dt
                dx = (player_x - self.logical_x) / dist
                dy = (player_y - self.logical_y) / dist
                nx = self.logical_x + dx * spd
                ny = self.logical_y + dy * spd
                if can_walk_fn(nx, self.logical_y): self.logical_x = nx
                if can_walk_fn(self.logical_x, ny): self.logical_y = ny
                
        # Telegraph + serangan: ada jeda wind-up sebelum pukulan mendarat,
        # memberi pemain jendela untuk mengelak (rasa combat lebih adil).
        if self.windup_ms > 0:
            self.ai_state = MobState.ATTACK
            self.windup_ms = max(0, self.windup_ms - dt * 1000)
            self.telegraph_ms = self.windup_ms
            if self.windup_ms <= 0:
                # Terjang: mob yang gesit melompat maju di ujung ancang-ancang.
                if self.terjang > 0 and dist > 0.3:
                    lompat = min(self.terjang, max(0.0, dist - 0.4))
                    dx = (player_x - self.logical_x) / dist
                    dy = (player_y - self.logical_y) / dist
                    for _ in range(4):
                        nx = self.logical_x + dx * lompat / 4
                        ny = self.logical_y + dy * lompat / 4
                        if not can_walk_fn(nx, ny):
                            break
                        self.logical_x, self.logical_y = nx, ny
                    dist = math.hypot(self.logical_x - player_x, self.logical_y - player_y)
                # pukulan mendarat — hanya kena bila pemain masih di jangkauan
                if dist <= self.atk_r * 1.35 and self.state.invuln_timer_ms <= 0:
                    self.state.hp = max(0, self.state.hp - self.damage)
                    self.state.invuln_timer_ms = INVULN_AFTER_HIT_MS
                    try:
                        from .sound import play as _play
                        _play('hurt')
                    except Exception: pass
                self.attack_cooldown_ms = self.cd_total
        elif dist <= self.atk_r and self.attack_cooldown_ms <= 0:
            # mulai wind-up (telegraph) — lamanya menurut watak jenisnya
            self.windup_total = self.windup_gaya
            self.windup_ms = self.windup_total
            self.telegraph_ms = self.windup_total
            self.ai_state = MobState.ATTACK
            try:
                from .sound import play as _play
                _play('mob_windup')
            except Exception: pass
