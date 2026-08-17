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

    # ─── Needs / Motives (ala The Sims / FreeSO) ───
    lapar:   float = 100.0  # Hunger  — turun waktu → isi dengan makan
    sosial:  float = 100.0  # Social  — turun waktu → isi dengan ngobrol
    senang:  float = 100.0  # Fun     — turun waktu → isi dengan panen/jelajah
    kandung: float = 100.0  # Bladder — terisi waktu → kosongkan di toilet (S1 Sims)
    bersih:  float = 100.0  # Hygiene — turun waktu → isi dengan mandi (S1 Sims)
    free_will: bool = True  # Autonomi ala Sims (S3): Sim urus kebutuhan sendiri
    # Relasi dua-meter ala Sims (S5). Persahabatan pakai npc_hearts yang sudah
    # ada; asmara & catatan hari interaksi terakhir (utk peluruhan) di sini.
    npc_romance:     dict = field(default_factory=dict)
    npc_last_social: dict = field(default_factory=dict)
    # Skill & karier ala Sims (S6)
    skills:       dict = field(default_factory=dict)   # id -> {'lv':int,'xp':float}
    career:       str  = ''
    career_level: int  = 0
    work_days:    int  = 0
    worked_today: bool = False
    # Mode Bangun/Beli (S7): objek yang dibeli pemain per scene
    placed_objects: dict = field(default_factory=dict)  # scene -> {'x,y': tile_id}

    # ─── Majelis Batin (4 suara + skill-check ala Disco Elysium) ───
    batin: dict = field(default_factory=lambda: {'bara': 1, 'akar': 1, 'sukma': 1, 'lapar': 1})
    batin_red: list = field(default_factory=list)   # id red-check yang sudah gagal (terkunci)

    # ─── Peti Kirim (shipping bin ala Stardew) — jual hasil panen saat tidur ───
    ship_bin: dict = field(default_factory=dict)     # item → jumlah menunggu dijual
    animals_collected: list = field(default_factory=list)  # id hewan yg hasilnya diambil hari ini

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

    def get_mood(self) -> float:
        # Rata-rata 5 motif Sims (kandung/bersih ikut menekan mood saat rendah)
        return (self.lapar + self.sosial + self.senang
                + self.kandung + self.bersih) / 5.0

    def mood_energy_multiplier(self) -> float:
        mood = self.get_mood()
        if mood >= NEED_HIGH:
            return 0.8
        elif mood >= NEED_CRITICAL:
            return 1.0
        else:
            return 1.4

    @staticmethod
    def slot_path(slot: int = 0) -> str:
        """Slot 0 = file lama (kompatibel mundur); slot 1-3 = file bersufiks."""
        if not slot:
            return SAVE_FILE
        base, ext = os.path.splitext(SAVE_FILE)
        return f"{base}_slot{slot}{ext}"

    def save(self, slot: int = 0):
        # Tulis atomik: temp dulu lalu os.replace → save lama TAK pernah rusak
        # walau penulisan gagal/crash di tengah (cegah kehilangan progres).
        path = GameState.slot_path(slot)
        tmp = path + '.tmp'
        try:
            with open(tmp, 'w') as f:
                json.dump({k: v for k, v in self.__dict__.items()}, f, indent=2)
            os.replace(tmp, path)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            return False

    @classmethod
    def load(cls, slot: int = 0):
        path = cls.slot_path(slot)
        if not os.path.exists(path):
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            gs = cls()
            for k, v in data.items():
                if hasattr(gs, k):
                    setattr(gs, k, v)
            return gs
        except Exception as e:
            print(f"Load error: {e}")
            return None

    @classmethod
    def slot_info(cls, slot: int = 0):
        """Ringkasan ringkas slot untuk UI simpan/muat; None bila kosong/rusak."""
        path = cls.slot_path(slot)
        if not os.path.exists(path):
            return None
        try:
            with open(path) as f:
                d = json.load(f)
            return {
                'name': d.get('char_name') or 'Tanpa Nama',
                'day':  int(d.get('day', 1)),
                'gold': int(d.get('gold', 0)),
            }
        except Exception:
            return None
