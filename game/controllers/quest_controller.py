from ..data import QUEST_STAGES
from ..sound import play as sound_play

class QuestController:
    """Manages quest progression, checks, and lore."""

    def __init__(self, state):
        self.state = state

    def check_quest_progress(self, panels=None):
        s = self.state
        if s.quest_stage == 0 and s.mail_read:
            s.quest_stage = 1

        # NOTE: ambang `earned >= 500` tidak sama dengan teks tahapan
        # "Kumpulkan 150G" di data.QUEST_STAGES — threshold quest masih perlu
        # satu pass desain terpisah. Di sini hanya jalur crash yang diperbaiki.
        if s.quest_stage == 1:
            if s.stats.get('lobak_harvested', 0) >= 3 and s.stats.get('earned', 0) >= 500:
                s.quest_stage = 2
                self._notify_quest_up(panels)

        if s.quest_stage == 2:
            # npc_hearts berskala 0..10 (di-cap min(10, ...) di semua penambah),
            # jadi ambang lama 15 tidak pernah tercapai. 3 hati = kira-kira 3x
            # hadiah atau belasan dialog.
            if s.npc_hearts.get('arya', 0) >= 3:
                s.quest_stage = 3
                self._notify_quest_up(panels)

        if s.quest_stage == 3:
            if getattr(s, 'lighthouse_fixed', False):
                s.quest_stage = 4
                self._notify_quest_up(panels)

    def _notify_quest_up(self, panels):
        s = self.state
        sound_play('magic', 0.8)
        stage = next((q for q in QUEST_STAGES if q.get('s') == s.quest_stage), None)
        title = stage['t'] if stage else 'Rahasia baru terungkap'
        msg = f"Quest Update: Tahap {s.quest_stage} - {title}"
        if panels:
            panels.flash_msg(msg, 3.5)
        else:
            print("[Quest]", msg)

    def check_dungeon_lore(self, dungeon_level, player, panels=None):
        s = self.state
        level_to_lore = {
            3: 'fragmen_prasasti_1',
            7: 'fragmen_prasasti_2',
            12: 'fragmen_prasasti_3',
        }
        lore_id = level_to_lore.get(dungeon_level)
        if lore_id and lore_id not in s.lore_collected:
            self.add_lore(lore_id, player, panels)

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
