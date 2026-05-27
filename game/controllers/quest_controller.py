from ..data import QUEST_STAGES
from ..sound import play as sound_play
from ursina import invoke

class QuestController:
    """Manages quest progression, checks, and lore."""
    
    def __init__(self, state):
        self.state = state

    def check_quest_progress(self, panels=None):
        s = self.state
        if s.quest_stage == 0 and s.mail_read:
            s.quest_stage = 1

        if s.quest_stage == 1:
            if s.stats.get('lobak_harvested', 0) >= 3 and s.stats.get('earned', 0) >= 500:
                s.quest_stage = 2
                self._notify_quest_up(panels)

        if s.quest_stage == 2:
            if s.npc_relations.get('arya', 0) >= 15:
                s.quest_stage = 3
                self._notify_quest_up(panels)

        if s.quest_stage == 3:
            if getattr(s, 'lighthouse_fixed', False):
                s.quest_stage = 4
                self._notify_quest_up(panels)

    def _notify_quest_up(self, panels):
        s = self.state
        sound_play('magic', 0.8)
        msg = f"Quest Update: Tahap {s.quest_stage} - {QUEST_STAGES.get(s.quest_stage, 'Rahasia baru terungkap')}"
        if panels:
            panels.flash_msg(msg, 3.5)
        else:
            print("[Quest]", msg)

    def check_dungeon_lore(self, dungeon_level, player, panels=None):
        s = self.state
        lore_msg = None
        if dungeon_level == 3 and not s.lore_found.get('dungeon_3'):
            s.lore_found['dungeon_3'] = True
            lore_msg = "Sebuah prasasti kuno: 'Kutukan Lembah Karsa berawal dari keserakahan manusia...'"
        elif dungeon_level == 7 and not s.lore_found.get('dungeon_7'):
            s.lore_found['dungeon_7'] = True
            lore_msg = "Sisa-sisa kemah penambang. Ada buku harian: 'Kami menggali terlalu dalam. Sesuatu terbangun...'"
        elif dungeon_level == 12 and not s.lore_found.get('dungeon_12'):
            s.lore_found['dungeon_12'] = True
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
