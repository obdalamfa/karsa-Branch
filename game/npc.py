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
        # Berpaling balik berlanjut sesudah kotak dialog ditutup; tanpa ini
        # gerakannya terpotong di frame terakhir percakapan dan yang terlihat
        # tetap sebuah patahan, cuma dipindah ke ujung yang lain.
        if self._tick_paling(dt):
            return
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

    # Berpaling butuh WAKTU. Versi pertama menulis rotation_y sekali di frame
    # pembuka, jadi lawan bicara mematah menghadap pemain dalam satu frame —
    # gerakan yang tidak dilakukan makhluk hidup mana pun. Diukur dari jejak:
    # rentang rotation_y selama seluruh percakapan 0,0 derajat, karena seluruh
    # perubahannya sudah selesai sebelum frame pertama tercatat.
    PALING_MS       = 320.0    # menoleh ke pemain saat percakapan dimulai
    PALING_BALIK_MS = 420.0    # kembali ke arah semula sesudah selesai

    def mulai_percakapan(self, px: float, pz: float) -> None:
        from .config import TILE_SIZE as _TS
        # Fase awal diambil dari id-nya, bukan nol: kalau dua NPC memakai fase
        # yang sama, mereka mengangguk serempak seperti pasukan.
        #
        # sum(ord) — BUKAN hash(), yang diacak ulang tiap proses Python. Dengan
        # hash(), dua rekaman dari kode yang sama persis punya fase anggukan
        # berbeda dan tidak bisa dibandingkan. Jebakan yang sama sudah tercatat
        # di entities.py:262.
        self._bicara_t = ((sum(map(ord, self.actor_id)) % 1000) / 1000.0
                          * self.ANGGUK_PERIODE)
        self._bicara_rot0 = self.rotation_y
        dx = px / _TS - self.logical_x
        dz = pz / _TS - self.logical_y
        if abs(dx) > 1e-6 or abs(dz) > 1e-6:
            self._paling(math.degrees(math.atan2(dx, dz)), self.PALING_MS)

    # ── berpaling ───────────────────────────────────────────────────────────
    def _paling(self, ke_derajat: float, panjang_ms: float) -> None:
        """Mulai berpaling ke `ke_derajat` selama `panjang_ms`."""
        self._paling_dari = float(self.rotation_y)
        # Lewat jalur terpendek: memutar 350 derajat untuk sampai ke -10 adalah
        # cara paling cepat membuat orang terlihat seperti mesin.
        selisih = (float(ke_derajat) - self._paling_dari + 180.0) % 360.0 - 180.0
        self._paling_delta = selisih
        self._paling_t = 0.0
        self._paling_ms = float(panjang_ms)

    def _tick_paling(self, dt: float) -> bool:
        """Satu langkah berpaling. True kalau masih berjalan."""
        if getattr(self, '_paling_t', None) is None:
            return False
        self._paling_t += dt
        u = min(1.0, self._paling_t * 1000.0 / self._paling_ms)
        # Ease-out kubik: kepala berangkat cepat lalu mendarat pelan, seperti
        # leher yang berhenti sendiri, bukan seperti motor yang dimatikan.
        e = 1.0 - (1.0 - u) ** 3
        self.rotation_y = self._paling_dari + self._paling_delta * e
        if u >= 1.0:
            self._paling_t = None
            return False
        return True

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
        self._tick_paling(dt)
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
        # `_bicara_rot0` disimpan sejak awal tapi tidak pernah dipakai: lawan
        # bicara tetap menghadap ke tempat pemain berdiri, selamanya, bahkan
        # sesudah pemain pergi. Sekarang ia berpaling kembali — lebih lambat
        # daripada saat menoleh, karena tidak ada yang menariknya.
        rot0 = getattr(self, '_bicara_rot0', None)
        if rot0 is not None:
            self._paling(rot0, self.PALING_BALIK_MS)
