import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from game.vitaboy.registry import asset_registry

reg = asset_registry()
stats = reg.stats()
print("Registry Stats:", stats)

# Force re-scan just in case
print("Re-scanning...")
reg.scan()
reg._save_cache()
stats2 = reg.stats()
print("Stats after force scan:", stats2)

anims = reg.list_keys('.anim')
print(f"Found {len(anims)} animations.")
print("Sample animations:", anims[:20])

sample_anim = reg.load_anim(anims[0]) if anims else None
if sample_anim:
    print("Sample animation loaded:", sample_anim.name, " duration:", sample_anim.duration)
else:
    print("Failed to load sample animation.")
