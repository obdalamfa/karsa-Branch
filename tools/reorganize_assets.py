import os
import shutil
from pathlib import Path

base_dir = Path(r"c:\Users\User\lembah-karsa\3d")
assets_dir = base_dir / "assets"

models_dir = assets_dir / "models"
textures_dir = assets_dir / "textures"
sounds_dir = assets_dir / "sounds"
ui_dir = assets_dir / "ui"

for d in [models_dir, textures_dir, sounds_dir, ui_dir]:
    d.mkdir(parents=True, exist_ok=True)

# 1. Move UI assets
ui_files = ["up_thermo_slice.png", "up_thermo_highlight.png", "up_thermo_slice_active.png"]
for uf in ui_files:
    src = assets_dir / uf
    if src.exists():
        shutil.move(str(src), str(ui_dir / uf))
font = assets_dir / "Montserrat-Bold.ttf"
if font.exists():
    shutil.move(str(font), str(ui_dir / font.name))

# 2. Move Models
vitaboy_dir = assets_dir / "vitaboy"
if vitaboy_dir.exists():
    for f in vitaboy_dir.glob("*.glb"):
        shutil.move(str(f), str(models_dir / f.name))
for f in assets_dir.glob("*.obj"):
    shutil.move(str(f), str(models_dir / f.name))
for f in assets_dir.glob("*.mtl"):
    shutil.move(str(f), str(models_dir / f.name))

# 3. Move Textures
for f in assets_dir.glob("*.png"):
    shutil.move(str(f), str(textures_dir / f.name))

# Move subdirectories to textures if they exist and are relevant
terrain = assets_dir / "terrain"
if terrain.exists():
    if not (textures_dir / "terrain").exists():
        shutil.move(str(terrain), str(textures_dir / "terrain"))
roof = assets_dir / "roof"
if roof.exists():
    if not (textures_dir / "roof").exists():
        shutil.move(str(roof), str(textures_dir / "roof"))

print("Asset reorganization completed successfully.")
