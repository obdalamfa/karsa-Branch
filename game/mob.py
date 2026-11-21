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
        # Telegraph serangan: jeda wind-up sebelum pukulan mendarat
        self.windup_ms = 0
        self.windup_total = 1
        self.telegraph_ms = 0
        # Animasi kematian: tumbang + menyusut sebelum dihapus
        self.dying = False
        self.death_ms = 0
        # Fase individual deterministik agar hantu-hantu di satu ruangan tidak bergerak serempak seperti robot
        self._ghost_phase = (sum(map(ord, str(actor_id))) % 100) * 0.0628
        self._ghost_t = self._ghost_phase
        self._base_scale = 1.4 if self.is_boss else 1.0

    def sync_visuals(self, dt: float, tile_size: float, ground_h: float):
        """Gerakan organik & khas tiap makhluk/hantu Nusantara di dungeon."""
        tx, ty = self.logical_x * tile_size, self.logical_y * tile_size
        dx = tx - self.x
        dz = ty - self.z

        lf = min(1.0, dt * 8.5)
        self.x += dx * lf
        self.z += dz * lf

        self.is_moving = abs(dx) > 0.012 or abs(dz) > 0.012
        self._ghost_t += dt * (2.4 if self.is_moving else 1.35)
        t = self._ghost_t
        sc = getattr(self, '_base_scale', 1.4 if self.is_boss else 1.0)

        # Putar mulus menghadap arah gerak (bukan patah 90 derajat)
        if self.is_moving and self.kind != 'banaspati':
            tujuan = math.degrees(math.atan2(dx, dz))
            beda = (tujuan - self.rotation_y + 180.0) % 360.0 - 180.0
            self.rotation_y += beda * min(1.0, dt * 10.0)

        # Telegraph wind-up: saat bersiap menyerang (windup_ms > 0), tarik badan ke belakang / bergetar
        w_ratio = 0.0
        if self.windup_ms > 0 and self.windup_total > 0:
            w_ratio = 1.0 - (self.windup_ms / float(self.windup_total))

        k = self.kind
        if k == 'pocong':
            # Pocong TIDAK berjalan meluncur: ia melompat parabolik dengan squash & stretch!
            siklus = (t * (1.8 if self.is_moving else 0.75)) % 1.0
            if siklus < 0.65:
                # Fase melayang di udara (parabola)
                u = siklus / 0.65
                lompat = math.sin(u * math.pi)
                self.y = lompat * (0.68 if self.is_moving else 0.22)
                stretch = 1.0 + 0.14 * lompat
                squash = 1.0 - 0.07 * lompat
                self.scale = (sc * squash, sc * stretch, sc * squash)
                self.rotation_x = (14.0 if self.is_moving else 5.0) * math.sin(u * math.pi)
            else:
                # Fase mendarat & ancang-ancang (squash sebelum lompatan berikutnya)
                u = (siklus - 0.65) / 0.35
                tekan = math.sin(u * math.pi)
                self.y = 0.0
                self.scale = (sc * (1.0 + 0.10 * tekan), sc * (1.0 - 0.14 * tekan), sc * (1.0 + 0.10 * tekan))
                self.rotation_x = -8.0 * tekan
            self.rotation_z = math.sin(t * 1.7) * 4.5
        elif k == 'kuntilanak':
            # Kuntilanak melayang di udara tanpa menyentuh tanah, kepala/badan miring menyeramkan
            self.y = 0.32 + math.sin(t * 1.5) * 0.18 + math.cos(t * 0.7) * 0.06
            self.rotation_z = math.sin(t * 1.1) * 9.5
            self.rotation_x = (12.0 if self.is_moving else 4.0) + math.cos(t * 1.4) * 5.0
            napas = 1.0 + math.sin(t * 2.2) * 0.035
            self.scale = (sc, sc * napas, sc)
        elif k == 'leak':
            # Leak (kepala & organ melayang) bergerak liar meliuk-liuk seperti gelombang
            self.y = 0.42 + math.sin(t * 2.3) * 0.22 + math.sin(t * 4.1) * 0.07
            self.rotation_z = math.sin(t * 2.8) * 14.0
            self.rotation_x = math.cos(t * 2.1) * 11.0
            denyut = 1.0 + math.sin(t * 5.0) * 0.06
            self.scale = (sc * denyut, sc / denyut, sc * denyut)
        elif k == 'banaspati':
            # Banaspati (bola api berwajah tengkorak) melayang, berputar & berkobar membesar-mengecil
            self.y = 0.25 + abs(math.sin(t * 2.0)) * 0.24
            self.rotation_y = (self.rotation_y + dt * (165.0 if self.is_moving else 75.0)) % 360.0
            self.rotation_z = math.sin(t * 3.2) * 10.0
            kobar = 1.0 + math.sin(t * 6.5) * 0.085
            self.scale = (sc * kobar, sc * (1.0 + math.cos(t * 5.2) * 0.10), sc * kobar)
        elif k == 'kelelawar':
            # Kelelawar terbang mengepak cepat naik-turun
            self.y = math.sin(t * 5.5) * 0.20
            kepak = 1.0 + math.sin(t * 11.0) * 0.12
            self.scale = (sc * kepak, sc * (2.0 - kepak), sc)
            self.rotation_z = math.cos(t * 5.5) * 8.0
        elif k in ('genderuwo', 'golem_batu') or self.is_boss:
            # Raksasa berat: langkah menghentak dengan goyangan bahu kiri-kanan
            hentak = abs(math.sin(t * 2.6)) if self.is_moving else (math.sin(t * 1.2) * 0.2)
            self.y = hentak * (0.14 if self.is_moving else 0.03)
            self.rotation_z = math.cos(t * 2.6) * (7.5 if self.is_moving else 1.8)
            self.rotation_x = (8.0 if self.is_moving else 2.0) + hentak * 4.0
            napas = 1.0 + math.sin(t * 1.8) * 0.04
            self.scale = (sc * napas, sc, sc * napas)
        else:
            # Tikus gua & mob darat cepat: lari merendah berdenyut
            loncat = abs(math.sin(t * 4.2)) if self.is_moving else 0.0
            self.y = loncat * 0.12
            self.rotation_x = (10.0 if self.is_moving else 0.0) * math.cos(t * 4.2)
            self.scale = (sc, sc * (1.0 - 0.06 * loncat), sc * (1.0 + 0.08 * loncat))

        # Efek wind-up serangan (tarik ke belakang lalu terkam ke depan!)
        if w_ratio > 0.0:
            if w_ratio < 0.72:
                tarik = w_ratio / 0.72
                self.rotation_x -= 24.0 * tarik
                self.scale = (self.scale_x * (1.0 + 0.12 * tarik),
                              self.scale_y * (1.0 - 0.10 * tarik),
                              self.scale_z * (1.0 + 0.12 * tarik))
            else:
                terkam = (w_ratio - 0.72) / 0.28
                self.rotation_x += 36.0 * terkam
                self.scale = (self.scale_x * 0.92, self.scale_y * 1.15, self.scale_z * 1.15)

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
                # pukulan mendarat — hanya kena bila pemain masih di jangkauan
                if dist <= self.atk_r * 1.35 and self.state.invuln_timer_ms <= 0:
                    self.state.hp = max(0, self.state.hp - self.damage)
                    self.state.invuln_timer_ms = INVULN_AFTER_HIT_MS
                    try:
                        from .sound import play as _play
                        _play('hurt')
                    except Exception: pass
                self.attack_cooldown_ms = 1000
        elif dist <= self.atk_r and self.attack_cooldown_ms <= 0:
            # mulai wind-up (telegraph) — boss menahan lebih lama agar terbaca
            self.windup_total = 600 if self.is_boss else 380
            self.windup_ms = self.windup_total
            self.telegraph_ms = self.windup_total
            self.ai_state = MobState.ATTACK
            try:
                from .sound import play as _play
                _play('mob_windup')
            except Exception: pass
