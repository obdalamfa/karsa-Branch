"""foto_scene.py — Foto satu scene dari game asli, setelah layar Buat Karakter.

`tools/capture.py` memotret apa pun yang ada di layar; di checkout tanpa save
itu berarti layar Buat Karakter menutupi separuh gambar dan kamera masih
close-up. Probe ini menutupnya lewat jalur yang sama dengan pemain
(`g.input('enter')`), menandai semua sinema sudah ditonton, lalu memindah
pemain dan kamera.

Pemakaian:
    python _bench/probes/foto_scene.py OUT.png SCENE X,Y [JAM] [PITCH] [JARAK] [YAW]
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData, Filename, getModelPath
loadPrcFileData('', 'window-type onscreen')
loadPrcFileData('', 'sync-video false')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'depth-bits 24')

from ursina import application
application.asset_folder = ROOT
application.fonts_folder = ROOT / 'assets' / 'fonts'
getModelPath().append_path(str(ROOT))

import game.config as cfg
cfg.SCREEN_W, cfg.SCREEN_H = 1280, 720

from game.app import Game3D
from game.cutscene import NASKAH

g = Game3D()
from direct.showbase.ShowBaseGlobal import base


def step(n):
    for _ in range(n):
        base.taskMgr.step()


g.state.sinema_selesai = list(NASKAH)
if g.panels.mode == 'chargen':
    step(5)
    g.input('enter')
    step(30)
step(10)

out, scene, at = sys.argv[1], sys.argv[2], sys.argv[3]
arg = sys.argv[4:] + [None] * 4
if scene.startswith('dungeon'):
    # Lantai dungeon dibangkitkan saat turun tangga, bukan dari berkas scene.
    # `dungeon:5` = lantai 5. Titik X,Y diabaikan: pemain di titik spawn.
    g.state.dungeon_level = int(scene.split(':')[1]) if ':' in scene else 1
    g.state.scene_name = 'dungeon'
    g.player._generate_and_enter_dungeon()
    step(30)
    at = f'{g.state.player_x},{g.state.player_y}'
else:
    g.state.scene_name = scene
    step(30)
x, y = (float(v) for v in at.split(','))
g.state.player_x, g.state.player_y = x, y
g.player.set_tile_pos(x, y)
g.player._set_initial_rotation()
if arg[0]: g.state.time_minutes = float(arg[0]) * 60
if arg[1]: g.camera_pitch = float(arg[1])
if arg[2]: g.camera_dist = float(arg[2])
if arg[3]: g.camera_yaw = float(arg[3])
g._snap_camera_to_player()
step(120)
base.graphicsEngine.renderFrame()
base.graphicsEngine.renderFrame()
base.win.getScreenshot().write(Filename.fromOsSpecific(str(Path(out).resolve())))
print('ok', g.world.scene_name, g.panels.mode)
