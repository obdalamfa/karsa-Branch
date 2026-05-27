import os
import shutil
from pathlib import Path

base_dir = Path(r"c:\Users\User\lembah-karsa\3d")
assets_dir = base_dir / "assets"
tex_dir = assets_dir / "textures"
aud_dir = assets_dir / "audio"
mod_dir = assets_dir / "models"
fnt_dir = assets_dir / "fonts"

for d in [tex_dir, aud_dir, mod_dir, fnt_dir]:
    d.mkdir(exist_ok=True)

# Move pngs
for f in assets_dir.glob("*.png"):
    shutil.move(str(f), str(tex_dir / f.name))

# Move ttf
for f in assets_dir.glob("*.ttf"):
    shutil.move(str(f), str(fnt_dir / f.name))

# Move dirs
for d_name in ["roof", "terrain"]:
    src = assets_dir / d_name
    if src.exists() and src.is_dir():
        dst = tex_dir / d_name
        if not dst.exists():
            shutil.move(str(src), str(dst))

# Update python files
def replace_in_file(filepath, old, new):
    if not filepath.exists():
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

game_dir = base_dir / "game"

# app.py
replace_in_file(game_dir / "app.py", 
                "parent.parent / 'assets' / 'snowflake.png'", 
                "parent.parent / 'assets' / 'textures' / 'snowflake.png'")

# entities.py
replace_in_file(game_dir / "entities.py", 
                "_ASSET_DIR = Path(__file__).resolve().parent.parent / 'assets'", 
                "_ASSET_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'textures'")

# panels.py
replace_in_file(game_dir / "panels.py", 
                "font=str(_a / 'Montserrat-Bold.ttf')", 
                "font=str(_a / 'fonts' / 'Montserrat-Bold.ttf')")
replace_in_file(game_dir / "panels.py", 
                "texture=str(_a / 'up_thermo_slice.png')", 
                "texture=str(_a / 'textures' / 'up_thermo_slice.png')")
replace_in_file(game_dir / "panels.py", 
                "texture=str(_a / 'up_thermo_slice_active.png')", 
                "texture=str(_a / 'textures' / 'up_thermo_slice_active.png')")
replace_in_file(game_dir / "panels.py", 
                "texture=str(_a / 'up_thermo_highlight.png')", 
                "texture=str(_a / 'textures' / 'up_thermo_highlight.png')")
replace_in_file(game_dir / "panels.py", 
                "str(_a / f'crop_{crop_name}.png')", 
                "str(_a / 'textures' / f'crop_{crop_name}.png')")

# player.py
replace_in_file(game_dir / "player.py", 
                "_ASSET_DIR = Path(__file__).resolve().parent.parent / 'assets'", 
                "_ASSET_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'textures'")

# world.py
replace_in_file(game_dir / "world.py", 
                "_ASSET_DIR = Path(__file__).resolve().parent.parent / 'assets'", 
                "_ASSET_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'textures'")

print("Assets standardized successfully.")
