import re

# 1. Update scenes.py
with open('game/scenes.py', 'r', encoding='utf-8') as f:
    scenes_content = f.read()

# Add on_load to Scene
if "def __init__(self, name, display, tiles, portals=None, indoor=False):" in scenes_content:
    scenes_content = scenes_content.replace(
        "def __init__(self, name, display, tiles, portals=None, indoor=False):",
        "def __init__(self, name, display, tiles, portals=None, indoor=False, on_load=None):\n        self.on_load = on_load"
    )

# Add beach on_load function
beach_onload = """
def _beach_on_load(world):
    from .config import GROUND_H, TS
    from ursina import color
    if not getattr(world.state, 'lighthouse_fixed', False):
        return
    base_x = 10 * TS
    base_z = 25 * TS
    y = GROUND_H + 0.2
    
    # Needs to use world._e instead of _e since it's in world
    # For simplicity, we just import what we need in world or pass world object.
    # Actually, world already has self._obj_ents.append(world._make_custom(...)) or we can just import _e from world.py
    # But wait! The logic uses _e which is a private function in world.py.
    # Let's just move the _build_black_dragon_ship into world.py's Scene class? No, we want to move map-specific logic out.
"""

# Let's change the approach. Instead of full python script rewriting, I can just do it manually with multi_replace_file_content or a simpler script.
