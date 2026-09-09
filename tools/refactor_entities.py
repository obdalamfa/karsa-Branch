with open('game/entities.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_str = "    def _create_mob_entity(self, idx, mob):"
end_str = "    # ─── PRIVATE: AI UPDATE ──────────────────────────────"

if start_str in content and end_str in content:
    idx1 = content.find(start_str)
    idx2 = content.find(end_str)
    
    new_mob_entity = """    def _create_mob_entity(self, idx, mob):
        from ursina import Entity, color
        from .config import GROUND_H
        
        kind = mob['kind']
        is_boss = mob.get('is_boss', False)
        sc = 1.4 if is_boss else 1.0
        
        root = Entity()
        root.x = mob['x'] * TS; root.y = 0; root.z = mob['y'] * TS
        
        body_ref = EntityFactory.create_model(root, kind, 'cube', color.red)
        body_ref.scale = sc
        
        hp_y = GROUND_H + (3.5 if is_boss else 2.4) * sc
        bg_bar = Entity(parent=root, model='cube', position=(0, hp_y, 0), scale=(0.9*sc, 0.10, 0.10), color=color.rgb(45, 45, 45))
        hp_bar = Entity(parent=root, model='cube', position=(0, hp_y, -0.02), scale=(0.9*sc, 0.08, 0.08), color=color.rgb(225, 48, 48))
        
        if hasattr(bg_bar, 'setLightOff'): bg_bar.setLightOff()
        if hasattr(hp_bar, 'setLightOff'): hp_bar.setLightOff()
        
        self._mob_ents[idx] = (root, hp_bar, body_ref)

"""
    content = content[:idx1] + new_mob_entity + content[idx2:]
    with open('game/entities.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Mob refactor successful.")
else:
    print("Could not find markers.")
