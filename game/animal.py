from enum import Enum, auto
from .base_actor import BaseActor
from .config import NPC_SPEED, TILE_SIZE
import math
import random

class AnimalState(Enum):
    IDLE = auto()
    WANDER = auto()
    SLEEPING = auto()
    MINUM = auto()

class FarmAnimal(BaseActor):
    """
    Farm animals handling wandering inside bounds and interactions.
    """
    def __init__(self, state, actor_id, **kwargs):
        super().__init__(state, actor_id, **kwargs)
        self.speed = NPC_SPEED / (TILE_SIZE * 20)
        self.animal_pen = (3, 3, 22, 12)  # default bounds
        self.ai_state = AnimalState.IDLE
        # Keadaan minum: (tunda_detik, tujuan_tile, jam_sejak_sampai)
        self._minum_tunda = 0.0
        self._minum_tile = None
        self._minum_t = None

    def set_bounds(self, bounds):
        self.animal_pen = bounds

    # ── MINUM ───────────────────────────────────────────────────────────────
    # Kenapa hewan harus benar-benar berjalan ke palung: kalau air masuk ke
    # angka tanpa ada yang meminumnya, mengisi palung cuma jadi klik. Yang
    # membuat merawat terasa seperti merawat adalah melihat akibatnya berjalan
    # menghampiri.
    TUNDUK_DERAJAT = 26.0        # sudut moncong turun saat minum
    TUNDUK_MASUK   = 0.45        # detik untuk menunduk
    MINUM_DETIK    = 2.6         # lama kepala menunduk di palung
    TUNDUK_KELUAR  = 0.55        # detik untuk mengangkat kepala lagi

    def panggil_minum(self, tx: int, ty: int, tunda: float = 0.0) -> None:
        """Suruh hewan ini mendatangi palung di (tx,ty) sesudah `tunda` detik."""
        self._minum_tunda = max(0.0, float(tunda))
        self._minum_tile = (int(tx), int(ty))
        self._minum_t = None
        self.ai_state = AnimalState.MINUM

    def _petak_minum(self):
        """Ubin tepat di sisi palung, dipilih dari sisi terdekat hewan ini.

        Semua hewan menuju ubin yang SAMA akan menumpuk jadi satu tumpukan
        kotak; memilih sisi terdekat membuat kawanan berbaris di keliling
        palung seperti kawanan sungguhan.
        """
        tx, ty = self._minum_tile
        kandidat = [(tx - 1, ty), (tx + 1, ty), (tx, ty - 1), (tx, ty + 1),
                    (tx - 1, ty + 1), (tx + 1, ty + 1)]
        return min(kandidat, key=lambda c: (c[0] - self.logical_x) ** 2
                   + (c[1] - self.logical_y) ** 2)

    def _tick_minum(self, dt: float, can_walk_fn) -> bool:
        """Return True kalau keadaan minum sedang memegang kendali."""
        if self.ai_state != AnimalState.MINUM or self._minum_tile is None:
            return False

        if self._minum_tunda > 0.0:
            self._minum_tunda = max(0.0, self._minum_tunda - dt)
            return True

        if self._minum_t is None:
            gx, gy = self._petak_minum()
            if can_walk_fn(gx, gy):
                self.target_x, self.target_y = float(gx), float(gy)
            sampai = (abs(self.logical_x - self.target_x) < 0.06
                      and abs(self.logical_y - self.target_y) < 0.06)
            if sampai:
                self._minum_t = 0.0
                # Menghadap palung, bukan menunduk ke arah mana saja.
                tx, ty = self._minum_tile
                self.rotation_y = math.degrees(
                    math.atan2(tx - self.logical_x, ty - self.logical_y))
            return True

        self._minum_t += dt
        t = self._minum_t
        total = self.TUNDUK_MASUK + self.MINUM_DETIK + self.TUNDUK_KELUAR
        if t >= total:
            self.rotation_x = 0.0
            self.ai_state = AnimalState.IDLE
            self._minum_tile = None
            self._minum_t = None
            return False

        if t < self.TUNDUK_MASUK:
            u = t / self.TUNDUK_MASUK
            sudut = self.TUNDUK_DERAJAT * (1.0 - (1.0 - u) ** 3)   # ease-out
        elif t < self.TUNDUK_MASUK + self.MINUM_DETIK:
            # Ditahan menunduk, dengan getaran kecil: kepala yang benar-benar
            # diam selama 2,6 detik terbaca sebagai patung, bukan sebagai hewan.
            lokal = t - self.TUNDUK_MASUK
            sudut = self.TUNDUK_DERAJAT + math.sin(lokal * 7.5) * 1.8
        else:
            u = (t - self.TUNDUK_MASUK - self.MINUM_DETIK) / self.TUNDUK_KELUAR
            sudut = self.TUNDUK_DERAJAT * (1.0 - u) ** 2
        self.rotation_x = sudut
        return True

    def update_ai(self, dt: float, can_walk_fn):
        # Minum menang atas jadwal tidur dan atas jalan-jalan: hewan yang
        # dipanggil ke palung harus sampai ke palung.
        if self._tick_minum(dt, can_walk_fn):
            self._gerak_lerp(dt)
            return

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
                
        self._gerak_lerp(dt)

    def _gerak_lerp(self, dt: float):
        """Satu langkah menuju target. Dipisah supaya keadaan minum memakai
        jalur gerak yang persis sama, bukan salinannya."""
        dx = self.target_x - self.logical_x
        dy = self.target_y - self.logical_y
        dist = math.hypot(dx, dy)
        move = self.speed * (dt * 1000)
        
        if dist <= move:
            self.logical_x, self.logical_y = float(self.target_x), float(self.target_y)
        elif dist > 0:
            self.logical_x += (dx / dist) * move
            self.logical_y += (dy / dist) * move
