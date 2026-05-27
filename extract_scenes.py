import os
import re

scenes_dir = os.path.join('game', 'scenes')
os.makedirs(scenes_dir, exist_ok=True)

with open('game/scenes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Match def build_...( ) -> up to the next def or SCENES =
funcs = re.findall(r'(def build_(\w+)\(.*?\):\n.*?(?=\n\w|\Z))', content, re.DOTALL)

init_imports = []
init_dict = []

for func_text, name in funcs:
    if name == 'dungeon_placeholder':
        name = 'dungeon'
        
    out_file = os.path.join(scenes_dir, f"{name}.py")
    
    # We also need imports. Let's just put common imports in all of them.
    file_content = f"""from game.config import *
from game.scenes.scene_base import Scene
import random
import math

{func_text}
"""
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(file_content)
        
    init_imports.append(f"from .{name} import build_{name if name != 'dungeon' else 'dungeon_placeholder'}")
    init_dict.append(f"    '{name}': build_{name if name != 'dungeon' else 'dungeon_placeholder'}(),")

# Write scene_base.py
scene_base_content = """class Scene:
    def __init__(self, name, display, tiles, portals=None, indoor=False, builder=None, has_horizon=True):
        self.builder = builder
        self.name    = name
        self.display = display
        self.tiles   = tiles
        self.w       = len(tiles[0]) if tiles else 0
        self.h       = len(tiles) if tiles else 0
        self.portals = portals or []
        self.indoor  = indoor
        self.has_horizon = has_horizon
"""
with open(os.path.join(scenes_dir, 'scene_base.py'), 'w', encoding='utf-8') as f:
    f.write(scene_base_content)

# Write __init__.py
init_content = "\n".join(init_imports) + "\n\nSCENES = {\n" + "\n".join(init_dict) + "\n}\n"
with open(os.path.join(scenes_dir, '__init__.py'), 'w', encoding='utf-8') as f:
    f.write(init_content)

print("Extraction complete.")
