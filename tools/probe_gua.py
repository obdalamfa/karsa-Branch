"""probe_gua.py — Bentuk gua, dan harga yang dibayar untuk melihat pemain.

Gua bertingkat dan Gua Sang Hyang sama-sama kehilangan bentuknya, dan sebabnya
bukan di pembangun peta melainkan di `World3D.update_wall_cutaway`.

Cutaway itu pelajaran The Sims 1 dan benar untuk rumah: dinding yang berdiri
antara kamera dan isi ruangan dipangkas setinggi lutut supaya ruangannya
terbaca. Tapi aturan lamanya memangkas SELURUH setengah-ruang di depan pemain,
tanpa memandang jarak menyamping — dan di gua itu menghancurkan ruangannya,
karena di gua dinding bukan pembatas ruangan, dinding ADALAH ruangannya:
46-57% peta gua bertingkat adalah batu padat.

Dua angka yang diukur di sini, dan keduanya harus benar sekaligus:

  BENTUK     berapa persen dinding dipangkas. Kalau hampir separuh peta rata
             setinggi lutut, yang tersisa di layar bukan gua.
  PENGHALANG berapa dinding yang MASIH berdiri penuh padahal memotong garis
             pandang kamera-ke-pemain. Harus NOL — kalau tidak, perbaikan
             bentuk dibayar dengan pemain yang hilang di balik batu, dan itu
             menukar satu cacat dengan cacat lain.

Yang kedua itu syarat yang membuat angka pertama boleh diperbaiki. Tanpa
mengukurnya, "gua jadi lebih berbentuk" cuma berarti "dindingnya tidak dipangkas
lagi" — yang memang membuat pemain tertutup.

Aturan lama ikut dihitung ulang di sini supaya perbandingannya berdampingan,
bukan dari ingatan.

Pemakaian:
    python tools/probe_gua.py
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData  # noqa: E402
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

import logging  # noqa: E402
logging.basicConfig(level=logging.ERROR)

W, H = 640, 360
hasil: list[tuple[str, bool, str]] = []


def cek(nama, ok, ket=''):
    hasil.append((nama, bool(ok), ket))


def _segmen_vs_kotak(p0, p1, cx, cz, half, atap):
    """Apakah ruas pandang p0->p1 tertutup kotak tegak di (cx,cz)?

    Kotaknya sejajar sumbu, setengah-lebar `half`, berdiri dari tanah sampai
    `atap`. Dipakai sebagai pengganti sinar tabrakan karena dinding gua tidak
    semuanya punya collider — dan karena hitungan ini deterministik, jadi
    hasilnya tidak bergantung pada frame mana yang kebetulan diukur.
    """
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dx, dz = x1 - x0, z1 - z0
    # Irisan ruas dengan kotak 2D (slab method) di bidang mendatar.
    t0, t1 = 0.0, 1.0
    for awal, arah, lo, hi in ((x0, dx, cx - half, cx + half),
                               (z0, dz, cz - half, cz + half)):
        if abs(arah) < 1e-9:
            if awal < lo or awal > hi:
                return False
            continue
        ta, tb = (lo - awal) / arah, (hi - awal) / arah
        if ta > tb:
            ta, tb = tb, ta
        t0, t1 = max(t0, ta), min(t1, tb)
        if t0 > t1:
            return False
    # Di rentang irisan itu, apakah garis pandang masih DI BAWAH puncak kotak?
    for t in (t0, t1, (t0 + t1) / 2):
        y = y0 + (y1 - y0) * t
        if y < atap:
            return True
    return False


def _ukur(g, label):
    """Kembalikan (n_dinding, n_dipangkas_sekarang, n_penghalang_tersisa)."""
    from ursina import camera
    from game.config import GROUND_H, TILE_SIZE as TS

    cam = camera.world_position
    fokus = g.camera_focus
    recs = [r for r in g.world._wall_ents if r[0]]
    n = len(recs)
    dipangkas = sum(1 for r in recs if r[0].scale_y <= 1.0)

    # Garis pandang: dari kamera ke KEPALA pemain, bukan ke kakinya — yang
    # harus terlihat badannya, bukan titik di lantai.
    p0 = (cam[0], cam[1], cam[2])
    p1 = (g.player.x, g.player.y + 1.2, g.player.z)

    penghalang = 0
    for r in recs:
        e, full_h = r[0], r[1]
        if e.scale_y <= 1.0:
            continue                      # sudah dipangkas, tidak menghalangi
        atap = GROUND_H + full_h
        half = max(abs(e.scale_x), abs(e.scale_z)) / 2.0
        if _segmen_vs_kotak(p0, p1, e.x, e.z, half, atap):
            penghalang += 1

    # Aturan LAMA dihitung ulang pada pose kamera yang sama, supaya
    # perbandingannya berdampingan dan bukan dari ingatan.
    vx, vz = fokus[0] - cam[0], fokus[2] - cam[2]
    mag = math.hypot(vx, vz) or 1.0
    vx, vz = vx / mag, vz / mag
    f_proj = fokus[0] * vx + fokus[2] * vz
    lama = sum(1 for r in recs
               if (r[0].x * vx + r[0].z * vz) < f_proj - TS * 0.5)
    return n, dipangkas, penghalang, lama


def _masuk(g, nama, tx, ty):
    """Pindah scene DAN pastikan ia benar-benar termuat.

    Dua hal harus diurus, dan keduanya sudah pernah membuat probe ini mengukur
    scene yang salah tanpa sadar:

      posisi  pemain mewarisi koordinatnya dari scene sebelumnya. Kalau itu di
              luar peta tujuan (peta rumah cuma 15x6, spawn gua bisa di tile
              20,15), permainan memulangkannya ke kebun -- dan yang terukur
              ternyata `farm`.
      portal  kalau tile tujuan kebetulan portal, ia langsung menyala dan
              pemain terlempar lagi sebelum satu frame pun diukur.

    Jadi posisinya diletakkan lebih dulu, portal diberi jeda, lalu hasilnya
    DIPERIKSA. Probe yang mengukur scene yang salah memberi vonis yang salah.
    """
    from direct.showbase.ShowBaseGlobal import base
    from game.config import TILE_SIZE as TS
    g.state.scene_name = nama
    g.state.player_x, g.state.player_y = float(tx), float(ty)
    g.player.x, g.player.z = float(tx) * TS, float(ty) * TS
    g.player._portal_cd = 3.0
    for _ in range(70):
        base.taskMgr.step()
        g.player._portal_cd = 3.0
    if g.world.scene_name != nama:
        cek(f'{nama}: scene benar-benar termuat', False,
            f'yang termuat {g.world.scene_name}')
        return False
    return True


def uji_gua(g):
    from direct.showbase.ShowBaseGlobal import base
    from game.config import TILE_SIZE as TS

    # Prasyarat, bukan kerapian: mode selain 'hud' MEMBEKUKAN pemain dan
    # perpindahan scene tidak pernah dijalankan. Dipanggil dari regress, probe
    # ini berjalan setelah probe panel Keinginan yang meninggalkan panelnya
    # terbuka -- dan akibatnya seluruh pemeriksaan gua mengukur `farm`, lalu
    # melaporkan "gua tidak punya dinding". Berdiri sendiri probe ini lulus,
    # jadi kegagalannya cuma muncul di regress dan mudah disalahartikan
    # sebagai gua yang rusak.
    if g.panels.mode != 'hud':
        g.panels.close_all()
        g.panels.mode = 'hud'
        for _ in range(3):
            base.taskMgr.step()

    adegan = []
    for lv in (1, 8):
        g.state.scene_name = 'dungeon'
        g.state.dungeon_level = lv
        g.player._generate_and_enter_dungeon()
        if _masuk(g, 'dungeon', g.state.player_x, g.state.player_y):
            adegan.append((f'gua bertingkat lv{lv}', _ukur(g, f'lv{lv}')))

    if _masuk(g, 'naga_cave', 7, 8):
        adegan.append(('gua Sang Hyang', _ukur(g, 'naga')))

    # Rumah: cutaway memang HARUS bekerja di sini. Kalau perbaikan gua
    # mematikannya untuk ruangan, satu cacat cuma ditukar dengan cacat lain.
    #
    # Pemain dipindahkan ke tengah rumah LEBIH DULU. Tanpa itu ia masih berdiri
    # di koordinat spawn gua bertingkat -- jauh di luar peta rumah yang cuma
    # 15x6 -- dan permainan memulangkannya ke kebun, sehingga yang terukur
    # ternyata scene `farm`. Probe yang mengukur scene yang salah memberi
    # vonis yang salah, dan itu sudah dua kali terjadi di proyek ini.
    if _masuk(g, 'house', 7, 4):
        adegan.append(('rumah (pembanding)', _ukur(g, 'house')))

    for nama, (n, dipangkas, penghalang, lama) in adegan:
        if n == 0:
            cek(f'{nama}: ada dinding', False, 'tidak ada dinding sama sekali')
            continue
        cek(f'{nama}: pemain tidak tertutup batu', penghalang == 0,
            f'{penghalang} dinding penuh memotong garis pandang')
        cek(f'{nama}: bentuk ruangan bertahan', dipangkas <= n * 0.25,
            f'{dipangkas}/{n} dipangkas ({dipangkas/n:.0%}); '
            f'aturan lama memangkas {lama}/{n} ({lama/n:.0%})')


def main():
    from ursina import application
    application.asset_folder = ROOT
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = W, H
    from game.app import Game3D
    try:
        g = Game3D()
    except Exception:
        import traceback
        print('GAGAL TOTAL: game tidak bisa dibangun')
        traceback.print_exc()
        sys.exit(1)
    if g.panels.mode != 'hud':
        if getattr(g, '_chargen', None):
            g._chargen.destroy_all()
            g._chargen = None
        g.panels.mode = 'hud'

    try:
        uji_gua(g)
    except Exception as ex:
        import traceback
        traceback.print_exc()
        cek('probe meledak', False, f'{type(ex).__name__}: {ex}')

    print()
    print('BENTUK GUA vs KETERLIHATAN PEMAIN')
    print('=' * 78)
    lebar = max(len(n) for n, _, _ in hasil)
    for nama, ok, ket in hasil:
        print(f"{'LULUS' if ok else 'GAGAL':>5s}  {nama:<{lebar}s}"
              f"{'  ' + ket if ket else ''}")
    gagal = [n for n, ok, _ in hasil if not ok]
    print('-' * 78)
    print(f'{len(hasil) - len(gagal)}/{len(hasil)} lulus')
    if gagal:
        print('GAGAL: ' + '; '.join(gagal))
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
