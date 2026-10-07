"""probe_arah.py — Alat ukur arah WASD yang tidak bisa berbohong.

Latar belakangnya jujur: sebelum ini tanda arah WASD disetel empiris sampai
"terasa benar", lalu terbalik lagi setiap kali ada yang menyentuh kamera —
sudah terjadi dua kali. Percobaan terakhir memakai proyeksi layar dan
menghasilkan angka yang saling bertentangan (W dan S sama-sama "atas"),
sehingga catatan commit sebelumnya menyimpulkan ALAT UKURNYA yang rusak dan
melarang mengubah tanda lagi sampai ada probe yang kokoh. Ini probe itu.

Kenapa probe yang lama bertentangan: kamera MENGIKUTI pemain. Kalau yang
diukur adalah posisi layar pemain sebelum vs sesudah bergerak, jawabannya
selalu mendekati nol dan sisanya cuma derau kejar-kejaran kamera. Arah mana
pun bisa terbaca "atas".

Yang diukur di sini:

  1. Perpindahan pemain di RUANG DUNIA, dibaca langsung dari NodePath
     Panda3D (`player.getPos(render)`), bukan dari properti Ursina — jadi
     tidak ada konvensi sumbu yang perlu ditebak.
  2. Perpindahan itu diproyeksikan lewat SATU pose kamera yang dibekukan
     sebelum tombol ditekan. Titik awal dan titik akhir memakai matriks yang
     sama persis, jadi hasilnya menjawab tepat satu pertanyaan: "perpindahan
     dunia ini kelihatan ke arah mana di layar?" Kamera boleh ikut bergerak;
     tidak berpengaruh, karena bukan kamera yang diproyeksikan.

Harapannya (konvensi layar standar): W ke ATAS layar, S ke BAWAH, A ke KIRI,
D ke KANAN.

Pemakaian:
    python tools/probe_arah.py                 scene farm, yaw kamera 0
    python tools/probe_arah.py town            scene lain
    python tools/probe_arah.py farm 0 90 215   uji beberapa yaw kamera

Keluar dengan kode 1 kalau ada arah yang salah.
"""
from __future__ import annotations

import os
import sys
import math
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData  # noqa: E402
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'aux-display pandadx9')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

import logging  # noqa: E402
logging.basicConfig(level=logging.ERROR)

W, H = 640, 360
SETTLE = 12        # frame supaya kamera duduk di tempatnya sebelum diukur
TEKAN = 18         # frame tombol ditahan
DIAM = 10          # frame melepas tombol supaya gesekan menghabiskan momentum

# Arah yang diharapkan di layar: (nama, sumbu ndc, tanda)
HARAP = {
    'w': ('atas',  'y', +1),
    's': ('bawah', 'y', -1),
    'a': ('kiri',  'x', -1),
    'd': ('kanan', 'x', +1),
}


def _bekukan_kamera(render, cam):
    """NodePath kosong yang meniru pose kamera SEKARANG, lalu berhenti ikut."""
    from panda3d.core import NodePath
    beku = NodePath('probe-cam-beku')
    beku.reparentTo(render)
    beku.setMat(render, cam.getMat(render))
    return beku


def _ke_layar(lens, beku, render, titik):
    """Titik dunia -> koordinat layar (-1..1). None kalau di belakang lensa."""
    from panda3d.core import Point2
    rel = beku.getRelativePoint(render, titik)
    out = Point2()
    if not lens.project(rel, out):
        return None
    return (out.getX(), out.getY())


def ukur_satu(g, base, key, kembali_ke):
    """Tahan satu tombol, kembalikan (dunia, layar) perpindahannya."""
    from ursina import held_keys

    p = g.player
    # Mulai dari tempat yang sama tiap arah supaya tabrakan tidak
    # membandingkan dua situasi yang berbeda.
    p.set_tile_pos(*kembali_ke)
    p.velocity_x = p.velocity_z = 0.0
    for _ in range(SETTLE):
        base.taskMgr.step()

    render = base.render
    beku = _bekukan_kamera(render, base.cam)
    lens = base.camLens

    p0 = p.getPos(render)
    held_keys[key] = 1
    try:
        for _ in range(TEKAN):
            base.taskMgr.step()
    finally:
        held_keys[key] = 0
    p1 = p.getPos(render)

    p.velocity_x = p.velocity_z = 0.0
    for _ in range(DIAM):
        base.taskMgr.step()

    s0 = _ke_layar(lens, beku, render, p0)
    s1 = _ke_layar(lens, beku, render, p1)
    beku.removeNode()

    dunia = (p1.getX() - p0.getX(), p1.getY() - p0.getY(), p1.getZ() - p0.getZ())
    layar = None if (s0 is None or s1 is None) else (s1[0] - s0[0], s1[1] - s0[1])
    return dunia, layar


def nilai(key, dunia, layar):
    """LULUS/GAGAL untuk satu arah, plus alasannya dalam bahasa manusia."""
    nama, sumbu, tanda = HARAP[key]
    jarak = math.sqrt(sum(c * c for c in dunia))
    if jarak < 0.05:
        return False, f'tidak bergerak sama sekali ({jarak:.3f} unit) — terjepit?'
    if layar is None:
        return False, 'titik jatuh di belakang lensa, tidak bisa diproyeksikan'

    dx, dy = layar
    besar = abs(dy) if sumbu == 'y' else abs(dx)
    lain = abs(dx) if sumbu == 'y' else abs(dy)
    if besar < 1e-4:
        return False, f'nyaris tidak bergerak di layar (dx={dx:+.4f} dy={dy:+.4f})'
    if besar < lain:
        arah_lain = 'mendatar' if sumbu == 'y' else 'menegak'
        return False, (f'{arah_lain} lebih dominan daripada {nama} '
                       f'(dx={dx:+.4f} dy={dy:+.4f})')

    nyata = dy if sumbu == 'y' else dx
    if (nyata > 0) != (tanda > 0):
        kebalikan = {'atas': 'bawah', 'bawah': 'atas',
                     'kiri': 'kanan', 'kanan': 'kiri'}[nama]
        return False, f'TERBALIK — harusnya {nama}, nyatanya {kebalikan} ({nyata:+.4f})'
    return True, f'{nama} (dx={dx:+.4f} dy={dy:+.4f}, {jarak:.2f} unit)'



def tile_lapang(g):
    """Tile berjalan yang tetangganya juga berjalan — supaya yang diukur arah,
    bukan dinding. Jatuh kembali ke tile pemain kalau tidak ada yang lapang."""
    tx, ty = g.player.get_tile_pos()
    for r in range(0, 8):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                c = (tx + dx, ty + dy)
                if all(g.world.is_walkable(c[0] + ox, c[1] + oy)
                       for ox in (-1, 0, 1) for oy in (-1, 0, 1)):
                    return c
    return (tx, ty)


def uji_arah(g, base, yaw=0.0, mulai=None):
    """Uji WASD pada satu yaw kamera. -> [(tombol, lulus, catatan, dunia), ...]

    Dipakai oleh main() di sini DAN oleh tools/regress.py, supaya jaring
    pengaman memakai alat ukur yang sama persis dengan probe manual.
    """
    if mulai is None:
        mulai = tile_lapang(g)
    g.camera_yaw = yaw
    g._snap_camera_to_player()
    for _ in range(SETTLE):
        base.taskMgr.step()
    hasil = []
    for key in ('w', 's', 'a', 'd'):
        dunia, layar = ukur_satu(g, base, key, mulai)
        ok, catatan = nilai(key, dunia, layar)
        hasil.append((key, ok, catatan, dunia))
    return hasil


def main():
    from ursina import application
    application.asset_folder = ROOT
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = W, H

    arg = [a for a in sys.argv[1:] if not a.startswith('-')]
    scene = arg[0] if arg else 'farm'
    yaws = [float(v) for v in arg[1:]] or [0.0]

    from game.app import Game3D
    try:
        g = Game3D()
    except Exception:
        print('GAGAL TOTAL: game tidak bisa dibangun\n')
        traceback.print_exc()
        sys.exit(1)

    from direct.showbase.ShowBaseGlobal import base
    # Chargen membajak semua input dan membekukan update; probe butuh HUD.
    if g.panels.mode != 'hud':
        if getattr(g, '_chargen', None):
            g._chargen.destroy_all()
            g._chargen = None
        g.panels.mode = 'hud'

    g.state.scene_name = scene
    for _ in range(40):
        base.taskMgr.step()

    mulai = tile_lapang(g)

    gagal = 0
    for yaw in yaws:
        print()
        print(f'scene {scene}, yaw kamera {yaw:g}°, mulai dari tile {mulai}')
        print(f'{"tombol":7s} {"hasil":>6s}  {"dunia (x,y,z)":26s} catatan')
        print('-' * 92)
        for key, ok, catatan, dunia in uji_arah(g, base, yaw, mulai):
            gagal += 0 if ok else 1
            dstr = f'({dunia[0]:+.2f},{dunia[1]:+.2f},{dunia[2]:+.2f})'
            print(f'{key.upper():7s} {"LULUS" if ok else "GAGAL":>6s}  {dstr:26s} {catatan}')
        print('-' * 92)

    print()
    print('SEMUA ARAH BENAR' if not gagal else f'{gagal} arah SALAH')
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
