"""state.py — GameState + save/load.
Identik dengan v17, hanya SAVE_FILE mengarah ke file 3D.
"""
import json
import logging
import os
import time
from dataclasses import dataclass, field, fields
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
    # Kesejahteraan ternak versi `husbandry.py`: {animal_id: {...}}.
    #
    # SEBELUMNYA TIDAK ADA DI SINI, dan itu bug yang menghapus data. `care_of()`
    # menulis `state.animal_care` sebagai atribut dinamis; `save()` menulisnya
    # ke JSON karena ia menyerialkan `__dict__`; tapi `load()` dulu menyaring
    # dengan `hasattr()` terhadap instance BARU -- yang belum punya atribut itu
    # -- sehingga seluruh akumulasi kelalaian ternak dibuang setiap kali save
    # dimuat, dan model biaya peternakan jadi tidak berarti.
    animal_care:     dict = field(default_factory=dict)

    # id hewan yang SEDANG ditunggangi, '' kalau pemain berjalan kaki.
    # Ditaruh di state, bukan di Player3D, karena tiga sistem lain
    # harus tahu: entities.py membekukan AI hewan itu dan menempelkannya
    # ke pemain, _update_npc_schedules berhenti menariknya pulang ke
    # jadwalnya, dan penyimpanan ikut membawanya sehingga memuat game
    # tidak menurunkan pemain di tengah jalan.
    menunggang:      str = ''
    soil:            dict = field(default_factory=dict)
    npc_hearts:      dict = field(default_factory=dict)
    npc_dialog_index:dict = field(default_factory=dict)
    npc_positions:   dict = field(default_factory=dict)
    wild_entities:   list = field(default_factory=list)

    mobs: list = field(default_factory=list)

    # ─── Ekosistem & pasar (game/ecology.py, game/market.py) ───
    # Keduanya dict biasa supaya save tetap JSON murni. Keduanya juga sengaja
    # dibiarkan KOSONG di sini: `ecology.ensure()` mengisi kolam yang hilang
    # dengan kapasitas penuh, jadi save lama membuka dunia yang utuh, bukan
    # dunia yang tiba-tiba habis. Lihat catatan di kedua modul itu.
    eco:    dict = field(default_factory=dict)
    market: dict = field(default_factory=dict)

    # Papan kerja sampingan (game/jobs.py) dan buku catatan memancing
    # (game/fishing.py). Bentuknya dijaga oleh `ensure()` masing-masing modul.
    jobs:     dict = field(default_factory=dict)
    fish_log: dict = field(default_factory=dict)

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

    # ── Sistem Sims, digabung dari feature/3d-mobs ─────────────────────────
    # Aditif terhadap mesin motif di atas, bukan pengganti: `motives` tetap
    # sumber kebenaran untuk kebutuhan, sementara blok di bawah membawa
    # sistem yang belum pernah ada di sisi ini sama sekali — skill & karier,
    # mode Bangun/Beli, rumah tangga & tagihan, keinginan & aspirasi, tahap
    # hidup, dan relasi asmara. `lapar`/`sosial`/`senang` sengaja TIDAK
    # diikutkan lagi dari sisi sana; ketiganya sudah dideklarasikan di atas
    # sebagai cermin save lama, dan mendeklarasikannya dua kali membuat
    # dataclass menolak dimuat.
    # ─── Needs / Motives (ala The Sims / FreeSO) ───
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
    # Rumah tangga & tagihan (S8)
    household:    list = field(default_factory=list)   # npc_id yang tinggal bersama
    bill_days:    int  = 0
    unpaid_bills: int  = 0
    # Keinginan & aspirasi (S9)
    wants:           list = field(default_factory=list)
    wants_done:      int  = 0
    aspiration:      str  = ''
    aspiration_done: bool = False
    title:           str  = ''
    # Tahap hidup (S10)
    age_days:   int = 14          # mulai sebagai dewasa
    life_stage: str = 'dewasa'

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
    char_perk:  int = 0          # indeks game.keahlian.KEAHLIAN
    keahlian_terpasang: str = ''  # penanda supaya bonus maks tidak dobel

    # ─── Keinginan (Tahap 4, game/wishes.py) ───
    # `janji` = daftar keinginan yang sedang dikejar, tiap entri membawa garis
    # dasarnya sendiri ('awal') supaya kemajuan dihitung dari saat DIJANJIKAN,
    # bukan dari total seumur hidup. `kebahagiaan` dibelanjakan, `_total` hanya
    # dipajang. `hadiah` = {id: berapa kali dibeli}.
    #
    # Semuanya dict/list/int murni supaya save tetap JSON, sama seperti `soil`
    # dan `motives` — dan supaya tidak mengulang bug `animal_care`, yang dulu
    # ditulis sebagai atribut dinamis sehingga `load()` membuangnya tiap kali.
    janji:             list = field(default_factory=list)
    kebahagiaan:       int  = 0
    kebahagiaan_total: int  = 0
    hadiah:            dict = field(default_factory=dict)

    quest_stage:        int  = 0
    mail_read:          bool = False
    shop_unlocked:      bool = False
    greenhouse_open:    bool = False
    met_jin:            bool = False
    captured_supernatural: int = 0

    lore_collected: list = field(default_factory=list)  # list of lore item IDs found

    # Sinema yang sudah pernah ditonton, supaya adegan pembuka tidak main lagi
    # tiap kali save dimuat. List, bukan set — save memakai json.dump.
    sinema_selesai: list = field(default_factory=list)

    # ─── WISHES ──────────────────────────────────────────
    # Tekad tidak pernah meluruh — itu yang membedakannya dari delapan motif,
    # dan itu sebabnya ia terasa seperti membangun sesuatu alih-alih seperti
    # hari yang lancar. Dibelanjakan untuk perabot dan resep, karena neraca
    # motif (#6) diseimbangkan di sekitar suplai perabot: perabot yang lebih
    # baik adalah satu-satunya hal yang menurunkan 54,5% hidup yang habis
    # mengurus motif.
    tekad:       int  = 0
    wishes:      dict = field(default_factory=dict)   # janji / ambang / selesai
    aksi_hitung: dict = field(default_factory=dict)   # nama aksi -> jumlah tuntas
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

    @staticmethod
    def slot_path(slot: int = 0) -> str:
        """Slot 0 = file lama (kompatibel mundur); slot 1-3 = file bersufiks."""
        if not slot:
            return SAVE_FILE
        base, ext = os.path.splitext(SAVE_FILE)
        return f"{base}_slot{slot}{ext}"

    # Versi format save. Naikkan saat MAKNA sebuah field berubah, lalu tangani
    # perbedaannya di `load_with_status`. Save yang tidak punya kunci ini
    # dianggap versi 1 (dibuat sebelum versi diperkenalkan).
    SAVE_VERSION = 2

    def save(self, slot: int = 0) -> bool:
        """Tulis save secara atomik ke SLOT tertentu. True kalau benar-benar tersimpan.

        Versi lama membuka berkas dengan mode 'w' -- MEMOTONG file hidup
        lebih dulu -- lalu menjalankan `sync_motives()` dan `json.dump` di
        dalam blok itu. Satu exception saja (disk penuh, proses dimatikan di
        tengah tulis, atau `sync_motives` gagal membangun mesin motif)
        meninggalkan file 0 byte, dan salinan terakhir sudah tidak ada. Itu
        jalur kehilangan save yang paling langsung di proyek ini.

        Sekarang isinya dirakit di memori dulu, ditulis ke berkas sementara,
        di-`fsync` supaya benar-benar sampai disk, baru `os.replace` menukarnya.
        `os.replace` atomik, jadi tidak ada pembaca yang pernah melihat berkas
        separuh -- dan kalau perakitan gagal, berkas lama tidak pernah
        tersentuh sama sekali. `slot` memilih berkasnya lewat `slot_path`.
        """
        try:
            self.sync_motives()
            payload = {k: v for k, v in self.__dict__.items()
                       if not k.startswith('_')}
            payload['save_version'] = self.SAVE_VERSION
            blob = json.dumps(payload, indent=2)
        except Exception as e:
            logging.error("Save gagal dirakit, berkas lama tidak disentuh: %s",
                          e, exc_info=True)
            return False

        path = GameState.slot_path(slot)
        tmp = f"{path}.tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(blob)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            return True
        except Exception as e:
            logging.error("Save gagal ditulis ke %s: %s", tmp, e, exc_info=True)
            try:
                os.remove(tmp)
            except OSError:
                pass
            return False

    @classmethod
    def load_with_status(cls, slot: int = 0):
        """Muat save slot -> (GameState|None, status), status 'ok'|'absent'|'corrupt'.

        'absent' berarti pemain belum pernah main -- itu normal dan bukan
        kesalahan. 'corrupt' berarti berkasnya ADA tapi tidak bisa dibaca.

        Dulu kedua keadaan itu tidak bisa dibedakan, dan itulah jalur kehilangan
        data yang sesungguhnya: `load()` mengembalikan None, `app.py` membuat
        state baru, `char_name` yang kosong memicu layar buat-karakter, dan
        konfirmasinya menulis save baru di atas satu-satunya salinan pemain --
        tanpa pemain pernah menekan simpan.

        Sekarang berkas rusak dipindahkan ke `<nama>.corrupt-<capwaktu>` lebih
        dulu, jadi isinya masih bisa diselamatkan, dan pemanggil bisa memberi
        tahu pemain alih-alih berpura-pura tidak terjadi apa-apa.
        """
        path = cls.slot_path(slot)
        if not os.path.exists(path):
            return None, 'absent'
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError(
                    f"save bukan objek JSON, melainkan {type(data).__name__}")
        except Exception as e:
            moved = cls._quarantine(slot)
            logging.error("Save rusak (%s). Dipindahkan ke %s supaya tidak "
                          "tertimpa oleh save baru.", e, moved)
            return None, 'corrupt'

        version = data.get('save_version', 1)
        if not isinstance(version, int) or version > cls.SAVE_VERSION:
            logging.warning("save_version tidak dikenal (%r); dimuat apa adanya",
                            version)
        elif version < cls.SAVE_VERSION:
            # Belum ada field yang berganti makna, jadi belum ada langkah
            # migrasi yang benar-benar dijalankan. Kaitannya sengaja ditaruh di
            # sini supaya perubahan berikutnya tidak lupa: tambahkan
            # `if version < N:` lalu tulis penyesuaiannya SEBELUM `_repair()`.
            logging.info("Save versi %d -> %d (belum ada langkah khusus)",
                         version, cls.SAVE_VERSION)

        gs = cls()
        known = {f.name for f in fields(cls)}
        unknown = []
        for k, v in data.items():
            if k in known:
                setattr(gs, k, v)
            elif k != 'save_version':
                unknown.append(k)
        if unknown:
            # `hasattr()` yang lama menerima nama METHOD dan PROPERTY juga.
            # Terverifikasi: `hasattr(GameState(), 'mv')` dan `'save'` sama-sama
            # True -- jadi satu kunci bernama `save` dulu bisa membayangi method
            # `save()` pada instance, dan `state.save()` berikutnya melempar
            # TypeError. Sekarang hanya field dataclass yang diterima.
            logging.warning("Save punya %d kunci tak dikenal, diabaikan: %s",
                            len(unknown), ', '.join(sorted(unknown)[:8]))
        gs._repair()
        return gs, 'ok'

    @classmethod
    def load(cls, slot: int = 0):
        """Jalur lama: GameState atau None. Lihat `load_with_status`."""
        return cls.load_with_status(slot)[0]

    @classmethod
    def slot_info(cls, slot: int = 0):
        """Ringkasan ringkas slot untuk UI simpan/muat; None bila kosong/rusak."""
        path = cls.slot_path(slot)
        if not os.path.exists(path):
            return None
        try:
            with open(path, encoding='utf-8') as f:
                d = json.load(f)
            return {
                'name': d.get('char_name') or 'Tanpa Nama',
                'day':  int(d.get('day', 1)),
                'gold': int(d.get('gold', 0)),
            }
        except Exception:
            return None

    @classmethod
    def _quarantine(cls, slot: int = 0) -> str:
        """Pindahkan save slot yang rusak ke samping. Dipindahkan, tidak dihapus."""
        path = cls.slot_path(slot)
        target = f"{path}.corrupt-{time.strftime('%Y%m%d-%H%M%S')}"
        try:
            os.replace(path, target)
            return target
        except OSError as e:
            logging.error("Gagal memindahkan save rusak: %s", e)
            return f"(gagal memindahkan: {e})"

    def _repair(self) -> None:
        """Paksa nilai yang, kalau liar, mematikan game sebelum bisa disimpan.

        `panels.py` mengindeks `SEASON_NAMES[season_index]` setiap frame tanpa
        penjaga, jadi satu save dengan `season_index` di luar rentang membuat
        HUD crash di frame pertama setelah dimuat. Field bertipe dict juga
        diindeks langsung (`soil.values()`, `inventory[...]`), jadi list di
        posisinya meledak jauh dari tempat kesalahannya berada.
        """
        if not isinstance(self.season_index, int) or not 0 <= self.season_index < len(SEASONS):
            logging.warning("season_index tidak sah (%r), dikembalikan ke 0",
                            self.season_index)
            self.season_index = 0
        for name in ('inventory', 'soil', 'npc_hearts', 'npc_dialog_index',
                     'npc_positions', 'buffs', 'upgrades', 'motives',
                     'side_quests', 'stats', 'animals', 'animal_care',
                     'hadiah'):
            if not isinstance(getattr(self, name, None), dict):
                logging.warning("%s bukan dict di save, direset ke kosong", name)
                setattr(self, name, {})
        for name in ('wild_entities', 'mobs', 'dungeon_tiles', 'lore_collected',
                     'janji'):
            if not isinstance(getattr(self, name, None), list):
                logging.warning("%s bukan list di save, direset ke kosong", name)
                setattr(self, name, [])
