from ..data import QUEST_STAGES
from ..sound import play as sound_play
from ursina import invoke

class QuestController:
    """Manages quest progression, checks, and lore."""
    
    def __init__(self, state):
        self.state = state

    def check_quest_progress(self, panels=None):
        s = self.state
        # Rantai: satu aksi bisa melompati beberapa tahap sekaligus (cegah macet).
        while s.quest_stage < 11 and self._stage_done(s.quest_stage):
            s.quest_stage += 1
            if s.quest_stage >= 11:
                s.post_game = True
            self._notify_quest_up(panels)

    def _stage_done(self, st):
        """Syarat tiap tahap — DICOCOKKAN dgn deskripsi QUEST_STAGES, pakai sinyal
        yang benar-benar terjadi di gameplay (audit M4)."""
        s = self.state
        inv = s.inventory
        stt = s.stats
        if st == 0:  return bool(s.mail_read)                                       # cek kotak pos
        if st == 1:  return stt.get('lobak_planted', 0) >= 3 and stt.get('watered', 0) >= 3
        if st == 2:  return stt.get('lobak_harvested', 0) >= 3                       # panen 3 lobak
        if st == 3:  return s.gold >= 150                                           # kumpulkan 150G
        if st == 4:  return s.pickaxe_tier >= 1 or bool(s.sword_id)                 # alat lebih baik
        if st == 5:  return s.pickaxe_tier >= 1 and stt.get('deepest_level', 0) >= 1 # crafting + masuk gua
        if st == 6:  return inv.get('tembaga', 0) >= 5 and inv.get('besi', 0) >= 3   # 5 tembaga + 3 besi
        # Pedang besi ATAU lebih tinggi (kalau pemain sudah upgrade ke emas/mithril,
        # '== sword_besi' bikin quest MACET PERMANEN — pemblokir tamat game).
        if st == 7:  return s.sword_id in ('sword_besi', 'sword_emas', 'sword_mithril') and stt.get('mobs_killed', 0) >= 5
        if st == 8:  return s.captured_supernatural >= 1                            # tangkap makhluk halus
        if st == 9:  return stt.get('deepest_level', 0) >= 10                       # gua level 10
        if st == 10: return bool(s.naga_defeated)                                   # kalahkan Naga
        return False

    def _notify_quest_up(self, panels):
        s = self.state
        sound_play('magic', 0.8)
        # QUEST_STAGES adalah list of {'s','t','d'} (bukan dict) — cari berdasarkan stage.
        stage_title = next((q['t'] for q in QUEST_STAGES if q['s'] == s.quest_stage), 'Rahasia baru terungkap')
        msg = f"Quest Update: Tahap {s.quest_stage} - {stage_title}"
        if panels:
            panels.flash_msg(msg, 3.5)
        else:
            print("[Quest]", msg)

    # Kedalaman gua yang menyimpan fragmen prasasti. Angkanya BUKAN pilihan
    # baru: `LORE_ITEMS[...]['found_at']` sudah menyebut dungeon_5, dungeon_10,
    # dan dungeon_14 sejak lama. Yang tidak pernah ada cuma kode yang
    # memberikannya — ketiga fragmen itu mustahil didapat, dan panel Catatan
    # tidak akan pernah menampilkannya sebanyak apa pun pemain menggali.
    FRAGMEN_GUA = {
        5:  'fragmen_prasasti_1',
        10: 'fragmen_prasasti_2',
        14: 'fragmen_prasasti_3',
    }

    def check_dungeon_lore(self, dungeon_level, player, panels=None):
        s = self.state

        # Fragmen prasasti — masuk KOLEKSI, bukan cuma pesan sekilas.
        lore_id = self.FRAGMEN_GUA.get(dungeon_level)
        if lore_id and lore_id not in getattr(s, 'lore_collected', []):
            self.add_lore(lore_id, player, panels)

        # Tiga pesan kedalaman di bawah tetap dipertahankan sebagai suasana,
        # tapi dulu ia satu-satunya cerita di gua DAN ia hilang begitu kotak
        # pesannya habis. Sekarang ia pendamping fragmen, bukan penggantinya.
        lore_msg = None
        # State pakai lore_collected (list), konsisten dgn add_lore() di bawah.
        lore_col = getattr(s, 'lore_collected', [])
        if dungeon_level == 3 and 'dungeon_3' not in lore_col:
            lore_col.append('dungeon_3'); s.lore_collected = lore_col
            lore_msg = "Sebuah prasasti kuno: 'Kutukan Lembah Karsa berawal dari keserakahan manusia...'"
        elif dungeon_level == 7 and 'dungeon_7' not in lore_col:
            lore_col.append('dungeon_7'); s.lore_collected = lore_col
            lore_msg = "Sisa-sisa kemah penambang. Ada buku harian: 'Kami menggali terlalu dalam. Sesuatu terbangun...'"
        elif dungeon_level == 12 and 'dungeon_12' not in lore_col:
            lore_col.append('dungeon_12'); s.lore_collected = lore_col
            lore_msg = "Dinding bercahaya: 'Hanya hati yang murni yang bisa menenangkan sang Naga Bumi...'"

        if lore_msg:
            if panels:
                invoke(panels.flash_msg, lore_msg, 5.0, delay=1.0)
            else:
                player._pending_lore_msg = lore_msg

    def add_lore(self, lore_id, player, panels=None):
        """Add a lore item to the player's collection if not already found."""
        s = self.state
        lore_list = getattr(s, 'lore_collected', [])
        if lore_id not in lore_list:
            lore_list.append(lore_id)
            s.lore_collected = lore_list
            from ..data import LORE_ITEMS
            item = LORE_ITEMS.get(lore_id, {})
            name = item.get('name', lore_id)
            if panels:
                panels.flash_msg(f"[N] Catatan baru: {name}", 3.5)
            else:
                # Delayed flash via stored pending
                player._pending_lore_msg = f"[N] Catatan baru: {name}"

    def check_npc_lore_gift(self, npc_id, player, panels):
        """Check if an NPC should gift a lore item based on hearts."""
        s = self.state
        hearts = s.npc_hearts.get(npc_id, 0)
        lore_gifts = {
            'sari': (6, 'buku_paman_arsa'),
            'maya': (7, 'peta_mimpi_maya'),
        }
        if npc_id in lore_gifts:
            req_hearts, lore_id = lore_gifts[npc_id]
            if hearts >= req_hearts:
                self.add_lore(lore_id, player, panels)
