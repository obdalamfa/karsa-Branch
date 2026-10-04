"""probe_basis_kamera.py — Basis arah gerak lawan basis layar yang sebenarnya.

probe_arah_wasd.py menemukan keempat arah salah DAN sesuatu yang lebih dalam:
W/S bergerak di diagonal dunia (1,1) sementara A/D di sumbu (1,0). Dua vektor
itu hanya 45 derajat terpisah, padahal "maju" dan "kanan" wajib 90 derajat.
Basisnya bukan cuma salah tanda -- ia MIRING.

Probe ini membandingkan, pada tiap yaw:
  a. basis yang DIPAKAI player.py  (dari quaternion kamera)
  b. basis layar yang SEBENARNYA   (dari posisi kamera, tanpa tanda ditebak)
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

g = Game3D()
from direct.showbase.ShowBaseGlobal import base  # noqa: E402
for _ in range(20):
    base.taskMgr.step()
if getattr(g.panels, 'mode', 'hud') == 'chargen' and g._chargen is not None:
    g._chargen._name_buf = 'Probe'
    g._chargen._confirm()
    for _ in range(10):
        base.taskMgr.step()

print('SEKARANG = yang dipakai player.py  |  KANDIDAT = komponen (.x,.z)')
print('beda_* = sudut dari basis layar yang sebenarnya; 0 derajat berarti tepat')
print('-' * 118)
for yaw in (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0):
    g.camera_yaw = yaw
    for _ in range(45):
        base.taskMgr.step()

    q = base.cam.getQuat(base.render)
    f, r = q.getForward(), q.getRight()
    fx, fz = -f.x, -f.y
    rx, rz = r.x, r.y
    nf = math.hypot(fx, fz) or 1.0
    nr = math.hypot(rx, rz) or 1.0
    fx, fz, rx, rz = fx / nf, fz / nf, rx / nr, rz / nr
    dot = fx * rx + fz * rz

    cx, _, cz = camera.world_position
    tx, _, tz = g.camera_focus
    ux, uz = tx - cx, tz - cz
    nu = math.hypot(ux, uz) or 1.0
    ux, uz = ux / nu, uz / nu
    kx, kz = uz, -ux

    beda = math.degrees(math.acos(max(-1.0, min(1.0, fx * ux + fz * uz))))

    # KANDIDAT: ambil komponen (.x, .z), bukan (.x, .y). Ursina memakai bidang
    # mendatar (x, z) dan getQuat(render) sudah relatif terhadap akar Ursina,
    # jadi komponen mendatarnya .x dan .z -- bukan .y, yang di Ursina adalah
    # sumbu ATAS. Tidak ada tanda yang ditebak di sini: dipakai apa adanya.
    gx, gz = f.x, f.z
    hx, hz = r.x, r.z
    ng = math.hypot(gx, gz) or 1.0
    nh = math.hypot(hx, hz) or 1.0
    gx, gz, hx, hz = gx / ng, gz / ng, hx / nh, hz / nh
    dot2 = gx * hx + gz * hz
    beda2 = math.degrees(math.acos(max(-1.0, min(1.0, gx * ux + gz * uz))))
    beda2k = math.degrees(math.acos(max(-1.0, min(1.0, hx * kx + hz * kz))))

    print(f'{yaw:4.0f}  SEKARANG maju({fx:+.3f},{fz:+.3f}) dot{dot:+.3f} beda{beda:6.1f}d'
          f'   |  KANDIDAT maju({gx:+.3f},{gz:+.3f}) kanan({hx:+.3f},{hz:+.3f})'
          f' dot{dot2:+.3f} beda_maju{beda2:6.1f}d beda_kanan{beda2k:6.1f}d')

print()
print('dot        : 0,000 = maju tegak lurus kanan (benar); 0,707 = miring 45 derajat')
print('beda maju  : sudut antara "maju" player.py dan "atas layar" yang sebenarnya')
