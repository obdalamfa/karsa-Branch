"""probe_font.py — Buktikan kenapa HUD gagal memuat Montserrat-Bold.ttf.

Hipotesis: Panda3D mencari font di model-path secara TIDAK rekursif. Ursina
memasukkan asset_folder (akar repo) ke model-path, tapi fontnya ada di
assets/fonts/, satu tingkat lebih dalam — jadi tidak pernah ketemu.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from panda3d.core import loadPrcFileData, getModelPath
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'window-type offscreen')

from ursina import Ursina, application  # noqa: E402
application.asset_folder = ROOT
app = Ursina(size=(320, 180))

import builtins  # noqa: E402

def coba(label):
    try:
        builtins.loader.loadFont('Montserrat-Bold.ttf')
        print(f'{label:46s} KETEMU')
    except OSError:
        print(f'{label:46s} GAGAL')


# Tiru persis keadaan `python main.py` dari akar repo: Ursina memasukkan
# asset_folder (akar repo) ke model-path.
getModelPath().append_path(str(ROOT.resolve()))
coba('akar repo di model-path (seperti main.py)')

getModelPath().append_path(str((ROOT / 'assets' / 'fonts').resolve()))
coba('assets/fonts ikut di model-path')

print(f'\nfile ada di disk: {(ROOT / "assets/fonts/Montserrat-Bold.ttf").exists()}')
