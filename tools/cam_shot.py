"""cam_shot.py — boot game offscreen, masuk gameplay, screenshot kamera live.
Untuk mendiagnosa & memverifikasi perbaikan kamera. python tools/cam_shot.py
"""
import sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from panda3d.core import loadPrcFileData, Filename
loadPrcFileData('', 'window-type offscreen')
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'audio-library-name null')
logging.basicConfig(level=logging.ERROR)

from pathlib import Path
from ursina import application, held_keys
_ROOT = Path(__file__).resolve().parent.parent
application.asset_folder = _ROOT
os.chdir(_ROOT)

from game.app import Game3D

g = Game3D(); app = g.app
def step(n=1):
    for _ in range(n):
        app.taskMgr.step()

step(5)
g.input('1'); step(3)        # Mulai Baru -> chargen
g.input('enter'); step(3)    # konfirmasi chargen -> intro
g.input('space'); step(4)    # tutup intro -> gameplay
step(25)                     # biar kamera settle

# gerak sedikit supaya terlihat follow
held_keys['w'] = 1
step(20)
held_keys['w'] = 0
step(15)

for _ in range(3):
    base.graphicsEngine.renderFrame()
out = str(_ROOT / 'tools' / 'cam_shot.png')
base.win.saveScreenshot(Filename.fromOsSpecific(out))
print('SHOT', out)
os._exit(0)
