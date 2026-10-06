"""probe_acuan.py — Acuan "atas layar" mana yang bisa dipercaya.

Pemeriksaan arah_maju memakai vektor kamera->fokus sebagai acuan. Di sebagian
scene dan yaw ia melaporkan 180 derajat dengan jarak sehat -- town yaw270,
beach yaw0. Probe ini membandingkan tiga acuan pada keadaan yang sama persis:

  A  kamera->fokus (yang dipakai pemeriksaan)
  B  vektor hadap kamera dari quaternion Panda3D, diproyeksikan ke tanah
  C  arah gerak pemain yang sebenarnya

Kalau A menyimpang dari B dan C sementara B dan C sepakat, acuannya yang rusak.
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

from ursina import application, camera, held_keys  # noqa: E402
application.asset_folder = ROOT
import game.config as cfg  # noqa: E402
cfg.SCREEN_W, cfg.SCREEN_H = 640, 360
from game.app import Game3D  # noqa: E402

g = Game3D()
from direct.showbase.ShowBaseGlobal import base  # noqa: E402
for _ in range(20):
    base.taskMgr.step()
if getattr(g.panels, 'mode', 'hud') == 'chargen' and g._chargen is not None:
    g._chargen._name_buf = 'Probe'
    g._chargen._confirm()
    for _ in range(10):
        base.taskMgr.step()


def sudut(ax, az, bx, bz):
    na, nb = math.hypot(ax, az) or 1e-9, math.hypot(bx, bz) or 1e-9
    return math.degrees(math.acos(max(-1.0, min(1.0, (ax * bx + az * bz) / (na * nb)))))


print(f'{"scene":10s} {"yaw":>5s} {"A kam->fokus":>16s} {"B hadap kamera":>16s} '
      f'{"C gerak":>16s} {"A-B":>6s} {"B-C":>6s} {"A-C":>6s}')
print('-' * 100)

for scene in ('town', 'beach', 'farm'):
    g.state.scene_name = scene
    for _ in range(30):
        base.taskMgr.step()
    pos0 = tuple(g.player.position)
    for yaw in (0.0, 135.0, 270.0):
        g.player.position = pos0
        g.player.velocity_x = g.player.velocity_z = 0.0
        g.camera_yaw = yaw
        g._snap_camera_to_player()
        for _ in range(6):
            base.taskMgr.step()

        cx, _, cz = camera.world_position
        ax, az = g.camera_focus[0] - cx, g.camera_focus[2] - cz      # A
        q = base.cam.getQuat(base.render)
        f = q.getForward()
        bx, bz = f.x, f.z                                            # B

        x0, _, z0 = g.player.world_position
        held_keys['w'] = 1
        for _ in range(60):
            base.taskMgr.step()
            x1, _, z1 = g.player.world_position
            if math.hypot(x1 - x0, z1 - z0) >= 0.40:
                break
        held_keys['w'] = 0
        cxg, czg = x1 - x0, z1 - z0                                  # C
        g.player.position = pos0
        g.player.velocity_x = g.player.velocity_z = 0.0

        print(f'{scene:10s} {yaw:5.0f} ({ax:+6.2f},{az:+6.2f}) ({bx:+6.2f},{bz:+6.2f}) '
              f'({cxg:+6.2f},{czg:+6.2f}) {sudut(ax,az,bx,bz):6.1f} '
              f'{sudut(bx,bz,cxg,czg):6.1f} {sudut(ax,az,cxg,czg):6.1f}')

print()
print('A-B besar = acuan kamera->fokus tidak sejalan dengan hadap kamera')
print('B-C kecil = pemain memang bergerak ke arah hadap kamera (game benar)')
