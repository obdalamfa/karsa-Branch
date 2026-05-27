import re

# 1. Update world.py
with open('game/world.py', 'r', encoding='utf-8') as f:
    world_content = f.read()

# Add _create_entity helper to World3D
if "def load_scene(self, name: str):" in world_content:
    world_content = world_content.replace(
        "def load_scene(self, name: str):",
        "def _create_entity(self, model, pos, scale, tex_name, tint=None, **kw):\n        from .world import _e\n        return _e(model, pos, scale, tex_name, tint, **kw)\n\n    def load_scene(self, name: str):"
    )

# Remove hardcoded beach logic from load_scene
world_content = world_content.replace(
    "if name == 'beach' and getattr(self.state, 'lighthouse_fixed', False):\n            self._build_black_dragon_ship()",
    "if hasattr(self.scene_obj, 'builder') and self.scene_obj.builder:\n            self.scene_obj.builder(self)"
)

# Remove _build_black_dragon_ship completely from world.py
start_idx = world_content.find("    def _build_black_dragon_ship(self):")
if start_idx != -1:
    end_idx = world_content.find("        world._obj_ents.extend([mast1, sail1, mast2, sail2])") 
    # Wait, end_idx should just be to the end of the method. In world.py it was wheel2
    # I can just use regex or simple string find to chop it.
    end_idx = world_content.find("self._obj_ents.extend([wheel1, wheel2])", start_idx)
    # The actual end in world.py was some sails too, wait let's just chop until the next def or end of class
    next_def_idx = world_content.find("    def ", start_idx + 10)
    if next_def_idx == -1:
        world_content = world_content[:start_idx]
    else:
        world_content = world_content[:start_idx] + world_content[next_def_idx:]

with open('game/world.py', 'w', encoding='utf-8') as f:
    f.write(world_content)

# 2. Update scenes.py
with open('game/scenes.py', 'r', encoding='utf-8') as f:
    scenes_content = f.read()

scenes_content = scenes_content.replace(
    "def __init__(self, name, display, tiles, portals=None, indoor=False):",
    "def __init__(self, name, display, tiles, portals=None, indoor=False, builder=None):\n        self.builder = builder"
)

scenes_content = scenes_content.replace(
    "    return Scene('beach', 'Pantai Selatan', m, portals=[",
    "    from .scene_builders import beach_builder\n    return Scene('beach', 'Pantai Selatan', m, builder=beach_builder, portals=["
)

with open('game/scenes.py', 'w', encoding='utf-8') as f:
    f.write(scenes_content)

print("Scene logic extracted successfully.")
