"""probe_arah_wasd.py — Arah WASD di layar, diukur lewat jalur asli.

MASALAH YANG DIPECAHKAN
═══════════════════════
`obsidian/40-Bug/Arah WASD belum terverifikasi.md` mencatat satu-satunya 🔴
yang bisa dikerjakan tanpa GPU: tanda arah WASD tidak boleh disentuh sebelum
ada probe yang kokoh, karena probe sebelumnya memberi angka yang saling
bertentangan -- "W dan S sama-sama atas".

Hipotesis kenapa probe lama gagal, dan itu yang diuji di sini: **kamera
MENGIKUTI pemain**. Jadi kalau yang diukur adalah pergeseran PEMAIN DI LAYAR,
jawabannya selalu "hampir nol, arah acak" apa pun tombolnya -- bukan karena
kodenya salah, tapi karena pengukurannya mustahil. Probe ini mengukurnya dengan
cara yang tidak bisa dirusak kamera:

  1. Tombol ditekan lewat `held_keys`, lalu frame dijalankan dengan
     `base.taskMgr.step()` -- yaitu JALUR ASLI `Game3D.update` -> `player.tick`,
     termasuk gerbang `panels.mode`. (Tiga probe dulu gagal menangkap bug
     pembeku pemain karena memanggil `player.tick()` langsung.)
  2. Yang diukur perpindahan DUNIA (x, z), bukan posisi di layar.
  3. Arah dunia itu baru diubah ke arah layar lewat PETA yang dikalibrasi
     dari dua titik bantu nyata: entity di (pemain + 1 satuan X) dan
     (pemain + 1 satuan Z), diproyeksikan lensa Panda3D pada frame yang sama
     dengan kamera diam. Engine yang mengerjakan konversi Y-up/Z-up, jadi tidak
     ada konvensi yang perlu ditebak.
  4. Kalibrasi diperiksa: determinannya harus jauh dari nol. Kalau kamera
     memandang tegak lurus ke bawah, peta itu memang singular -- dan probe
     HARUS bilang "tidak bisa diukur", bukan mengarang arah.
  5. Diulang pada beberapa yaw kamera, karena justru perubahan kamera yang dua
     kali membalik tanda arah di proyek ini.

Keluaran: untuk tiap yaw, arah layar tiap tombol dalam derajat (0 = kanan,
90 = ATAS layar), plus pemeriksaan silang W<->S dan A<->D berlawanan.
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from panda3d.core import loadPrcFileData, Point2, Point3
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

import logging
logging.basicConfig(level=logging.ERROR)

from ursina import application, held_keys, Entity  # noqa: E402
application.asset_folder = ROOT

import game.config as cfg  # noqa: E402
cfg.SCREEN_W, cfg.SCREEN_H = 640, 360

from game.app import Game3D  # noqa: E402

FRAMES_SETTLE = 40      # frame untuk kamera menyusul sesudah ganti yaw
FRAMES_PRESS = 45       # frame tombol ditahan
MIN_GERAK = 0.35        # satuan dunia; di bawah ini dianggap tidak bergerak
MIN_DET = 1e-3          # di bawah ini peta dunia->layar singular

g = Game3D()
# `base` baru ada SESUDAH ShowBase dibangun, yaitu sesudah Game3D() --
# mengimpornya di level modul gagal. tools/regress.py melakukan hal yang sama.
from direct.showbase.ShowBaseGlobal import base  # noqa: E402

for _ in range(20):
    base.taskMgr.step()

# Gerbang mode: pemain BEKU kalau panel apa pun terbuka (bug 7ed8d59).
# Chargen terbuka otomatis kalau karakter belum punya nama.
if getattr(g.panels, 'mode', 'hud') == 'chargen' and g._chargen is not None:
    # Ditutup lewat JALUR ASLI: _confirm() adalah yang dipanggil saat pemain
    # menekan tombol selesai -- ia mengisi char_name, membongkar UI-nya, dan
    # mengembalikan panels.mode ke 'hud'. Menyetel mode dengan tangan akan
    # meninggalkan UI chargen hidup di layar dan menguji keadaan yang tidak
    # pernah dialami pemain.
    g._chargen._name_buf = 'Probe'
    g._chargen._confirm()
    for _ in range(10):
        base.taskMgr.step()
print(f'panels.mode = {getattr(g.panels, "mode", "?")}  (harus hud, kalau tidak pemain beku)')


def lepas_semua():
    for k in ('w', 'a', 's', 'd', 'shift', 'up arrow', 'down arrow',
              'left arrow', 'right arrow'):
        held_keys[k] = 0


def layar(np_):
    """Koordinat film (x kanan, y ATAS) sebuah NodePath, atau None."""
    p = Point2()
    titik = base.cam.getRelativePoint(np_, Point3(0, 0, 0))
    return (p.x, p.y) if base.camLens.project(titik, p) else None


def kalibrasi():
    """Peta dunia(x,z) -> layar(x,y), dari dua titik bantu nyata. (a,b,c,d,det)."""
    px, py, pz = g.player.world_position
    o = Entity(position=(px, py, pz), visible=False)
    ex = Entity(position=(px + 1.0, py, pz), visible=False)
    ez = Entity(position=(px, py, pz + 1.0), visible=False)
    base.taskMgr.step()                      # satu frame supaya transform terpasang
    so, sx, sz = layar(o), layar(ex), layar(ez)
    for e in (o, ex, ez):
        e.disable()
    if None in (so, sx, sz):
        return None
    a, c = sx[0] - so[0], sx[1] - so[1]      # kolom untuk +1 X dunia
    b, d = sz[0] - so[0], sz[1] - so[1]      # kolom untuk +1 Z dunia
    return a, b, c, d, a * d - b * c


def ukur(tombol):
    """Perpindahan dunia (dx, dz) sesudah menahan `tombol`."""
    lepas_semua()
    g.player.velocity_x = g.player.velocity_z = 0.0
    for _ in range(6):
        base.taskMgr.step()
    x0, _, z0 = g.player.world_position
    held_keys[tombol] = 1
    for _ in range(FRAMES_PRESS):
        base.taskMgr.step()
    held_keys[tombol] = 0
    x1, _, z1 = g.player.world_position
    lepas_semua()
    return x1 - x0, z1 - z0


def sudut(vx, vy):
    return math.degrees(math.atan2(vy, vx)) % 360.0


def nama_arah(deg):
    for lo, hi, nm in ((45, 135, 'ATAS'), (135, 225, 'KIRI'),
                       (225, 315, 'BAWAH')):
        if lo <= deg < hi:
            return nm
    return 'KANAN'


HARAP = {'w': 'ATAS', 's': 'BAWAH', 'a': 'KIRI', 'd': 'KANAN'}
gagal = []

for yaw in (45.0, 135.0, 225.0, 315.0):
    g.camera_yaw = yaw
    if hasattr(g, 'snap_camera'):
        g.snap_camera()
    for _ in range(FRAMES_SETTLE):
        base.taskMgr.step()

    kal = kalibrasi()
    print()
    if kal is None:
        print(f'yaw {yaw:5.1f}  TIDAK BISA DIUKUR: titik bantu di luar lensa')
        gagal.append(f'yaw{yaw:.0f}:proyeksi')
        continue
    a, b, c, d, det = kal
    print(f'yaw {yaw:5.1f}  peta dunia->layar  det={det:+.5f}'
          f'   [+1X -> ({a:+.4f},{c:+.4f})  +1Z -> ({b:+.4f},{d:+.4f})]')
    if abs(det) < MIN_DET:
        print('          TIDAK BISA DIUKUR: peta singular (kamera nyaris tegak lurus)')
        gagal.append(f'yaw{yaw:.0f}:singular')
        continue

    hasil = {}
    for tombol in ('w', 's', 'a', 'd'):
        dx, dz = ukur(tombol)
        jarak = math.hypot(dx, dz)
        if jarak < MIN_GERAK:
            print(f'          {tombol.upper()}  TIDAK BERGERAK  ({jarak:.3f} satuan)')
            gagal.append(f'yaw{yaw:.0f}:{tombol}-diam')
            continue
        sx_, sy_ = a * dx + b * dz, c * dx + d * dz
        deg = sudut(sx_, sy_)
        arah = nama_arah(deg)
        hasil[tombol] = (deg, sx_, sy_)
        tanda = 'OK  ' if arah == HARAP[tombol] else 'SALAH'
        if arah != HARAP[tombol]:
            gagal.append(f'yaw{yaw:.0f}:{tombol}={arah}')
        print(f'          {tombol.upper()}  dunia({dx:+.2f},{dz:+.2f}) {jarak:5.2f}'
              f'  layar {deg:6.1f} deg  {arah:5s}  harap {HARAP[tombol]:5s}  {tanda}')

    # Pemeriksaan silang: pasangan harus berlawanan ~180 derajat.
    for p, q in (('w', 's'), ('a', 'd')):
        if p in hasil and q in hasil:
            beda = abs((hasil[p][0] - hasil[q][0] + 180) % 360 - 180)
            ok = beda > 150
            print(f'          {p.upper()}<->{q.upper()} selisih {beda:5.1f} deg'
                  f'  {"berlawanan OK" if ok else "TIDAK berlawanan"}')
            if not ok:
                gagal.append(f'yaw{yaw:.0f}:{p}{q}-tidak-berlawanan')

print()
if gagal:
    print('HASIL: ADA MASALAH ->', ', '.join(gagal))
else:
    print('HASIL: keempat arah benar di semua yaw yang diuji.')
sys.exit(1 if gagal else 0)
