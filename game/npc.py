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

    # ── PERCAKAPAN ──────────────────────────────────────────────────────────
    # Pendengar yang benar-benar beku sama merusaknya dengan pembicara yang
    # beku. Rig NPC di sini satu mesh tanpa pivot, jadi yang bisa digerakkan
    # cuma seluruh badannya — dan ternyata itu cukup: menghadap lawan bicara,
    # anggukan kecil, dan perpindahan berat yang periodenya tidak sinkron
    # dengan anggukan sudah membuat orang terbaca sedang mendengarkan.
    ANGGUK_DERAJAT  = 5.2      # dalamnya satu anggukan
    ANGGUK_PERIODE  = 2.35     # detik antar anggukan
    ANGGUK_LEBAR    = 0.34     # bagian periode yang dipakai anggukan itu sendiri
    SWAY_DERAJAT    = 2.4
    SWAY_PERIODE    = 4.6      # detik satu ayunan berat penuh
    NAPAS_DERAJAT   = 0.6      # selalu ada, bahkan di antara anggukan
    NAPAS_PERIODE   = 3.1

    def mulai_percakapan(self, px: float, pz: float) -> None:
        from .config import TILE_SIZE as _TS
        # Fase awal diambil dari id-nya, bukan nol: kalau dua NPC memakai fase
        # yang sama, mereka mengangguk serempak seperti pasukan.
        self._bicara_t = (hash(self.actor_id) % 1000) / 1000.0 * self.ANGGUK_PERIODE
        self._bicara_rot0 = self.rotation_y
        dx = px / _TS - self.logical_x
        dz = pz / _TS - self.logical_y
        if abs(dx) > 1e-6 or abs(dz) > 1e-6:
            self.rotation_y = math.degrees(math.atan2(dx, dz))

    def tick_percakapan(self, dt: float, px: float, pz: float) -> None:
        """Anggukan berdenyut + napas yang tidak pernah berhenti.

        Versi pertama memakai `max(0, sin(t * 1,15))`. Setengah gelombang yang
        dipotong itu berarti kepala DIAM PERSIS NOL selama 2,7 detik penuh tiap
        siklus — diukur dari jejak: delapan sampel berturut-turut n_rx = 0,00.
        Pendengar yang membeku hampir tiga detik adalah persis pembekuan yang
        mau dihilangkan potongan ini; ia cuma pindah tempat.

        Sekarang anggukan jadi DENYUT pendek (34% dari 2,35 detik) dan sisanya
        diisi napas kecil yang selalu jalan, jadi tidak pernah ada frame dengan
        kepala benar-benar diam.
        """
        if getattr(self, '_bicara_t', None) is None:
            self.mulai_percakapan(px, pz)
        self._bicara_t += dt
        t = self._bicara_t

        napas = self.NAPAS_DERAJAT * math.sin(t * math.tau / self.NAPAS_PERIODE)

        u = (t % self.ANGGUK_PERIODE) / self.ANGGUK_PERIODE
        if u < self.ANGGUK_LEBAR:
            # Kosinus terangkat: turun cepat, naik lebih pelan, tanpa sudut
            # tajam di kedua ujungnya.
            v = u / self.ANGGUK_LEBAR
            angguk = self.ANGGUK_DERAJAT * (0.5 - 0.5 * math.cos(math.tau * v))
        else:
            angguk = 0.0

        self.rotation_x = napas + angguk
        # Periodenya tidak berkelipatan periode anggukan, jadi keduanya tidak
        # pernah jatuh bersamaan — kalau sinkron, yang terlihat satu getaran,
        # bukan dua kebiasaan tubuh.
        self.rotation_z = self.SWAY_DERAJAT * math.sin(t * math.tau / self.SWAY_PERIODE)

    def akhiri_percakapan(self) -> None:
        if getattr(self, '_bicara_t', None) is None:
            return
        self._bicara_t = None
        self.rotation_x = 0.0
        self.rotation_z = 0.0
