import re

with open('game/player.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Inject imports
import_str = "from .pathfinder import PathGrid, PathMover"
new_import = import_str + "\nfrom .time_manager import TimeManager\nfrom .quest_manager import QuestManager\nfrom .player_interaction import PlayerInteractionController"
content = content.replace(import_str, new_import)

# 2. Inject initializations
init_str = "self._portal_cd = 0.0"
new_init = init_str + "\n\n        self.time_manager = TimeManager(state)\n        self.quest_manager = QuestManager(state)\n        self.interaction_controller = PlayerInteractionController(self, world)"
content = content.replace(init_str, new_init)

# 3. Replace delegations in handle_input and others
# Because we extracted the methods to InteractionController, we just redirect the calls
replacements = {
    "self._use_tool(entities_mgr, panels)": "self.interaction_controller.use_tool(entities_mgr, panels)",
    "self._interact(entities_mgr, panels)": "self.interaction_controller.interact(entities_mgr, panels)",
    "self._attack(entities_mgr, panels)": "self.interaction_controller.attack(entities_mgr, panels)",
    "self._capture(entities_mgr, panels)": "self.interaction_controller.capture(entities_mgr, panels)",
    "self._consume_item(panels)": "self.interaction_controller.consume_item(panels)",
    "self._advance_day()": "self.time_manager.advance_day(self)",
    "self._check_dungeon_lore(s.dungeon_level)": "self.quest_manager.check_dungeon_lore(s.dungeon_level, self)",
    "self._check_quest_progress(panels)": "self.quest_manager.check_quest_progress(panels)",
    "self._check_quest_progress()": "self.quest_manager.check_quest_progress()",
}

for old, new in replacements.items():
    content = content.replace(old, new)

# 4. Remove the huge methods that were extracted
methods_to_remove = [
    "def _use_tool(",
    "def _use_tool_at(",
    "def _interact(",
    "def _try_fishing(",
    "def _try_healing(",
    "def _try_repair_lighthouse(",
    "def _attack(",
    "def _capture(",
    "def _consume_item(",
    "def _advance_day(",
    "def _check_quest_progress(",
    "def _check_dungeon_lore("
]

lines = content.split('\n')
new_lines = []
skip = False
for line in lines:
    is_method_start = any(line.strip().startswith(m) for m in methods_to_remove)
    
    if is_method_start:
        skip = True
        continue
        
    if skip:
        # Stop skipping if we hit another def that is NOT in the remove list
        if line.strip().startswith("def ") and not any(line.strip().startswith(m) for m in methods_to_remove):
            skip = False
        else:
            continue
            
    if not skip:
        new_lines.append(line)

content = '\n'.join(new_lines)

with open('game/player.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Player refactor successful.")
