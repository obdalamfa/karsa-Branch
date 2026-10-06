"""probe_kontaminasi.py — Kenapa `arah_maju` menuduh scene yang sehat.

Pemeriksaan `arah_maju` di tools/regress.py menuduh enam scene di larian 14
scene, padahal scene yang sama LULUS kalau dijalankan sendirian. Probe ini
menguji satu hipotesis yang belum pernah diuji:

    Pengukuran memakai `player.world_position`, tapi `_snap_camera_to_player`
    menghitung `camera_focus` dari `player.position` -- koordinat LOKAL. Kalau
    parent pemain bukan identitas, dua angka itu berbeda, dan vektor
    "kamera -> fokus" yang dipakai sebagai acuan "atas layar" jadi salah.

Dicetak per scene: posisi lokal, posisi dunia, selisihnya, dan sudut antara
acuan versi `camera_focus` dengan acuan versi posisi DUNIA pemain.
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from panda3d.core import loadPrcFileData
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

import logging
logging.basicConfig(level=logging.ERROR)

from ursina import application, camera  # noqa: E402
application.asset_folder = ROOT
import game.config as cfg  # noqa: E402
cfg.SCREEN_W, cfg.SCREEN_H = 640, 360
from game.app import Game3D  # noqa: E402
from game.scenes import SCENES  # noqa: E402

g = Game3D()
from direct.showbase.ShowBaseGlobal import base  # noqa: E402
for _ in range(20):
    base.taskMgr.step()
if getattr(g.panels, 'mode', 'hud') == 'chargen' and g._chargen is not None:
    g._chargen._name_buf = 'Probe'
    g._chargen._confirm()
    for _ in range(10):
        base.taskMgr.step()

print(f'{"scene":12s} {"lokal(x,z)":>18s} {"dunia(x,z)":>18s} {"selisih":>8s} '
      f'{"beda acuan":>11s}  parent')
print('-' * 92)

for nama in [s for s in SCENES if s != 'dungeon']:
    g.state.scene_name = nama
    for _ in range(30):
        base.taskMgr.step()

    lx, _, lz = g.player.position
    wx, _, wz = g.player.world_position
    selisih = math.hypot(wx - lx, wz - lz)

    cx, _, cz = camera.world_position
    # acuan A: seperti yang dipakai pemeriksaan sekarang (camera_focus)
    ax, az = g.camera_focus[0] - cx, g.camera_focus[2] - cz
    na = math.hypot(ax, az) or 1.0
    # acuan B: dari posisi DUNIA pemain
    bx, bz = wx - cx, wz - cz
    nb = math.hypot(bx, bz) or 1.0
    cos = max(-1.0, min(1.0, (ax * bx + az * bz) / (na * nb)))
    beda = math.degrees(math.acos(cos))

    induk = getattr(g.player, 'parent', None)
    nama_induk = getattr(induk, 'name', type(induk).__name__ if induk else '-')

    print(f'{nama:12s} ({lx:7.2f},{lz:7.2f}) ({wx:7.2f},{wz:7.2f}) '
          f'{selisih:8.3f} {beda:10.1f}d  {nama_induk}')

print()
print('selisih > 0      -> posisi lokal != dunia; camera_focus dihitung dari LOKAL')
print('beda acuan > 0   -> acuan "atas layar" yang dipakai pemeriksaan MELESET')
