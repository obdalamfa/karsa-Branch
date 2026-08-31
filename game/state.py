"""state.py — GameState + save/load.
Identik dengan v17, hanya SAVE_FILE mengarah ke file 3D.
"""
import json
import os
from dataclasses import dataclass, field
from .config import (SAVE_FILE, START_GOLD, START_ENERGY, SEASONS, SEASON_NAMES,
                     PLAYER_BASE_HP, NEED_HIGH, NEED_CRITICAL)


@dataclass
class GameState:
    scene_name: str  = 'farm'
    player_x:   float = 8.0
    player_y:   float = 8.0
    facing:     str   = 'down'

    day:          int   = 1
    year:         int   = 1
    day_in_season:int   = 1
    season_index: int   = 0
    time_minutes: float = 360.0
    weather:      str   = 'Cerah'

    energy:     int = START_ENERGY
    max_energy: int = START_ENERGY
    gold:       int = START_GOLD
    tool_index: int = 0
    seed_key:   str = 'lobak'

    hp:              int   = PLAYER_BASE_HP
    max_hp:          int   = PLAYER_BASE_HP
    invuln_timer_ms: float = 0.0

    # python-2d-game health_and_mana.py pattern: passive regen + buff tracking
    hp_regen_rate: float = 0.8   # HP per detik saat idle
    buffs: dict = field(default_factory=dict)  # {buff_name: sisa_ms}

    pickaxe_tier: int = 0
    sword_id:     str = ''

    inventory:       dict = field(default_factory=lambda: {'lobak_seed': 3})
    # Catatan ternak: {animal_id: {'kenyang': sisa_hari, 'siap': hari_terkumpul}}.
    # Dict biasa supaya save tetap JSON murni, sama seperti `soil` dan `motives`.
    animals:         dict = field(default_factory=dict)

    # Ternak yang SUDAH DIBELI. Daftar id, bukan set — save memakai json.dump
    # atas __dict__, dan set tidak bisa di-JSON-kan.
    #
    # Kosong di awal, dan itu keputusan: sebelumnya kesembilan hewan muncul
    # gratis pada hari pertama, jadi kandang sudah penuh sebelum pemain
    # melakukan apa pun dan "membeli ternak" tidak punya arti. Sekarang ayam
    # pertama harus dibeli 392G sementara emas awal 100G — jadi bertani dulu,
    # baru beternak. Itu urutan yang sama dengan patokan kita.
    #
    # Hanya mengatur ternak PENGHASIL (LIVESTOCK_FOR_SALE). Kuda, kucing,
    # rubah, dan kelinci tetap muncul apa adanya: mereka bukan ternak, mereka
    # penghuni, dan tidak ada yang dijual atau dihasilkan dari mereka.
    owned_animals:   list = field(default_factory=list)
    soil:            dict = field(default_factory=dict)
    npc_hearts:      dict = field(default_factory=dict)
    npc_dialog_index:dict = field(default_factory=dict)
    npc_positions:   dict = field(default_factory=dict)
    wild_entities:   list = field(default_factory=list)

    mobs: list = field(default_factory=list)

    dungeon_level: int  = 0
    dungeon_tiles: list = field(default_factory=list)
    dungeon_seed:  int  = 0

    naga_defeated:          bool = False
    naga_fountain_used_today:bool = False

    upgrades: dict = field(default_factory=lambda: {
        'hoe': False, 'water': False, 'bag': False, 'axe': False
    })

    # ─── Needs / Motives (ala The Sims 1) ───
    # Delapan motif berskala -100..+100 dengan laju peluruhan asli TS1 hidup di
    # `game/motives.py`. Yang disimpan di sini hanya dict biasa supaya save
    # tetap JSON — objek mesinnya dibangun ulang saat load lewat `mv`.
    motives: dict = field(default_factory=dict)

    # Tiga need lama (skala 0..100) dipertahankan HANYA supaya save lama tetap
    # bisa dibuka dan kode lama yang membacanya tidak meledak. Sumber kebenaran
    # sekarang adalah `motives`; ketiganya dicerminkan tiap tick.
    lapar:  float = 100.0
    sosial: float = 100.0
    senang: float = 100.0

    # ─── Penampilan karakter (chargen) ───
    char_name:  str = ''         # kosong = belum buat karakter (trigger chargen)
    char_skin:  int = 0
    char_hair:  int = 0
    char_shirt: int = 0
    char_pants: int = 0
    char_hat:   int = 0

    quest_stage:        int  = 0
    mail_read:          bool = False
    shop_unlocked:      bool = False
    greenhouse_open:    bool = False
    met_jin:            bool = False
    captured_supernatural: int = 0

    lore_collected: list = field(default_factory=list)  # list of lore item IDs found
    post_game:      bool = False                        # True after quest_stage reaches 11
    side_quests: dict = field(default_factory=dict)
    lighthouse_fixed: bool = False                      # True after repairing lighthouse on the beach

    stats: dict = field(default_factory=lambda: {
        'lobak_planted':0, 'watered':0, 'lobak_harvested':0, 'corn_harvested':0,
        'earned':0, 'gifts':0, 'mobs_killed':0, 'minerals_mined':0, 'deepest_level':0,
        'seasons_harvested':[],
    })

    def get_season(self):      return SEASONS[self.season_index]
    def get_season_name(self): return SEASON_NAMES[self.season_index]
    def get_time_str(self):    return f"{int(self.time_minutes//60)%24:02d}:{int(self.time_minutes%60):02d}"
    def get_hour(self):        return int(self.time_minutes // 60) % 24
    def is_night(self):        return self.get_hour() < 5 or self.get_hour() >= 19
    def get_player_tile(self): return (int(round(self.player_x)), int(round(self.player_y)))

    @property
    def mv(self):
        """Mesin motif, dibangun sekali lalu dipakai ulang.

        Disimpan di luar dataclass field supaya tidak ikut ke json.dump.
        """
        eng = self.__dict__.get('_mv')
        if eng is None:
            from .motives import Motives
            eng = Motives()
            eng.load_save(self.motives)
            self.__dict__['_mv'] = eng
        return eng

    def sync_motives(self) -> None:
        """Tulis balik mesin ke dict yang dipersistenkan, dan cerminkan ke tiga
        need lama (dipetakan dari -100..100 ke 0..100) agar UI dan kode lama
        yang belum dipindahkan tetap menampilkan angka yang benar."""
        eng = self.mv
        self.motives = eng.to_save()
        self.lapar  = (eng.lapar + 100.0) / 2.0
        self.sosial = (eng.sosial + 100.0) / 2.0
        self.senang = (eng.senang + 100.0) / 2.0

    def get_mood(self) -> float:
        """Mood dalam skala 0..100 untuk konsumen lama.

        Mesin memakai skala -100..+100 (rata-rata delapan motif); di sini
        dipetakan ulang supaya ambang NEED_* yang ada tetap berlaku.
        """
        return (self.mv.mood + 100.0) / 2.0

    def mood_energy_multiplier(self) -> float:
        mood = self.get_mood()
        if mood >= NEED_HIGH:
            return 0.8
        elif mood >= NEED_CRITICAL:
            return 1.0
        else:
            return 1.4

    def save(self):
        try:
            with open(SAVE_FILE, 'w') as f:
                self.sync_motives()
                json.dump({k: v for k, v in self.__dict__.items()
                           if not k.startswith('_')}, f, indent=2)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    @classmethod
    def load(cls):
        if not os.path.exists(SAVE_FILE):
            return None
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
            gs = cls()
            for k, v in data.items():
                if hasattr(gs, k):
                    setattr(gs, k, v)
            return gs
        except Exception as e:
            print(f"Load error: {e}")
            return None
