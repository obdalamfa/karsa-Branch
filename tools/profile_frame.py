"""profile_frame.py — di mana 100 ms per frame itu sebenarnya habis.

TAHAPAN.md menulis "4-29 FPS, belum pernah diprofil" dan menaruh Tahap 3 di
belakang jaring pengaman justru karena itu: menebak sumber lambatnya lalu
mengoptimasi tebakan adalah cara paling cepat membuang waktu. Alat ini
menjawab satu pertanyaan sebelum satu baris pun dioptimasi:

    waktunya habis di PYTHON (logika game per frame),
    atau di RENDER (Panda menggambar terlalu banyak batch)?

Jawabannya menentukan seluruh sisa Tahap 3, dan dua jawabannya menuntut
pekerjaan yang sama sekali berbeda:

  Python berat   → kurangi kerja per frame: cache, jangan lintasi semua
                   entity tiap frame, jangan set shader input yang tidak
                   berubah. (Satu kasus seperti ini sudah ditemukan: setter
                   `scene.fog_color` melintasi seluruh scene.entities tiap
                   assignment — 51,9 ms dari 79,9 ms di town.)
  Render berat   → kurangi BATCH, bukan entity: gabung mesh sejenis, pakai
                   instancing, culling. Mengecilkan jumlah entity Python
                   tidak menolong kalau batch-nya tetap.

Cara memisahkannya
==================

`base.taskMgr.step()` menjalankan dua hal: task Python (termasuk update
Ursina dan update game) lalu `graphicsEngine.renderFrame()`. Alat ini
mengukur keduanya terpisah dengan mematikan salah satunya:

  penuh    step() apa adanya
  render   task update game dimatikan → yang tersisa render
  python   selisihnya

Ditambah cProfile atas step() untuk menyebut FUNGSI mana yang berat, dan
hitungan Geom/GeomNode untuk tahu berapa batch yang sebenarnya digambar.

Peringatan yang menentukan cara membaca angkanya
================================================

Alat ini MENCETAK nama perender yang benar-benar dipakai, dan itu bukan
hiasan. Di container tanpa GPU (`/dev/dri` tidak ada) Mesa jatuh ke llvmpipe —
rasterizer perangkat lunak yang berjalan di CPU. Di sana biaya frame didominasi
FILL RATE: diukur di mountain, 158 ms di 1280x720 turun jadi 77 ms di 640x360
untuk seperempat piksel, yang berarti ~50 ms biaya tetap + ~108 ms fill.

Di mesin ber-GPU sungguhan susunannya terbalik: fill hampir gratis dan yang
tersisa jumlah batch serta waktu Python. Jadi:

    ms/frame dari container tanpa GPU TIDAK BOLEH dipakai menilai
    target 30 FPS Tahap 3, dan tidak boleh dipakai memilih optimasi.

Yang tetap sah diukur di sini karena tidak bergantung GPU:

    jumlah Entity, GeomNode, dan Geom   → batas bawah jumlah batch
    waktu Python per frame              → sama di mesin mana pun
    jumlah panggilan di cProfile        → sama di mesin mana pun

Optimasi yang dipilih dari tiga angka itu menolong di mesin mana pun.
Optimasi yang dipilih dari ms/frame llvmpipe menolong llvmpipe.

Pemakaian
=========

    python tools/profile_frame.py                    semua scene berat
    python tools/profile_frame.py mountain           satu scene
    python tools/profile_frame.py mountain --top 30  lebih banyak baris profil
"""
from __future__ import annotations

import argparse
import cProfile
import io as _io
import os
import pstats
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData  # noqa: E402
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

import logging  # noqa: E402
logging.basicConfig(level=logging.ERROR)

W, H = 1280, 720
WARM = 30
UKUR = 40

# Scene terberat lebih dulu — kalau cuma sempat membaca satu baris, baca ini.
BAWAAN = ['mountain', 'town', 'beach', 'farm', 'swarga']


def _hitung_geom(uscene):
    """Berapa GeomNode dan Geom yang benar-benar ada di graf scene.

    Ini yang menentukan biaya render, BUKAN jumlah Entity Python. Seribu
    Entity yang berbagi satu mesh tergabung jauh lebih murah daripada seratus
    Entity dengan mesh sendiri-sendiri.
    """
    n_node = n_geom = 0
    for e in uscene.children:
        try:
            for gn in e.findAllMatches('**/+GeomNode'):
                n_node += 1
                n_geom += gn.node().getNumGeoms()
        except Exception:
            continue
    return n_node, n_geom


def _rata(fn, n):
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scenes', nargs='*', default=None)
    ap.add_argument('--top', type=int, default=18)
    args = ap.parse_args()

    from ursina import application
    application.asset_folder = ROOT
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = W, H

    from game.app import Game3D
    g = Game3D()
    from direct.showbase.ShowBaseGlobal import base
    from ursina import scene as uscene
    for _ in range(20):
        base.taskMgr.step()

    gsg = base.win.getGsg()
    perender = gsg.getDriverRenderer()
    vendor = gsg.getDriverVendor()
    lunak = any(k in perender.lower() for k in ('llvmpipe', 'softpipe', 'swrast'))
    print()
    print(f'perender : {vendor} — {perender}')
    if lunak:
        print()
        print('  *** RASTERIZER PERANGKAT LUNAK — TANPA GPU ***')
        print('  Kolom ms/frame di bawah didominasi fill rate CPU dan TIDAK')
        print('  mewakili mesin ber-GPU. Jangan pakai untuk menilai target 30')
        print('  FPS, dan jangan pakai untuk memilih optimasi. Yang sah dibaca')
        print('  dari sini: jumlah entity/GeomNode/Geom, waktu Python, dan')
        print('  jumlah panggilan cProfile — ketiganya tidak bergantung GPU.')

    scenes = args.scenes or BAWAAN
    baris = []
    profil_teks = {}

    for nama in scenes:
        g.state.scene_name = nama
        for _ in range(WARM):
            base.taskMgr.step()

        n_ent = len(uscene.children)
        n_node, n_geom = _hitung_geom(uscene)

        ms_penuh = _rata(base.taskMgr.step, UKUR)

        # Render saja: task update game dimatikan, sisanya tetap jalan.
        # Ursina menaruh update-nya di task bernama 'update'; kalau namanya
        # berubah, angka python-nya akan jadi ~0 dan itu terlihat jelas di
        # tabel — lebih baik daripada diam-diam salah.
        tugas = base.taskMgr.getTasksNamed('update')
        for t in tugas:
            t.remove()
        for _ in range(8):
            base.taskMgr.step()
        ms_render = _rata(base.taskMgr.step, UKUR)
        for t in tugas:
            base.taskMgr.add(t)
        for _ in range(8):
            base.taskMgr.step()

        ms_python = max(0.0, ms_penuh - ms_render)
        baris.append((nama, n_ent, n_node, n_geom, ms_penuh, ms_render, ms_python))

        pr = cProfile.Profile()
        pr.enable()
        for _ in range(UKUR):
            base.taskMgr.step()
        pr.disable()
        buf = _io.StringIO()
        pstats.Stats(pr, stream=buf).sort_stats('tottime').print_stats(args.top)
        profil_teks[nama] = buf.getvalue()

    print()
    print(f'{"scene":11s} {"entity":>7s} {"geomnode":>9s} {"geom":>7s} '
          f'{"penuh":>7s} {"render":>7s} {"python":>7s}  {"tersangka":>9s}')
    print('-' * 84)
    for nama, ne, nn, ng, mp, mr, mpy in baris:
        siapa = 'RENDER' if mr > mpy else 'PYTHON'
        print(f'{nama:11s} {ne:7d} {nn:9d} {ng:7d} '
              f'{mp:7.1f} {mr:7.1f} {mpy:7.1f}  {siapa:>9s}')
    print('-' * 84)
    print('ms per frame. `render` = step() dengan task update dimatikan.')
    print('`python` = selisihnya. Kolom terakhir menyebut yang lebih besar.')

    out = ROOT / '_bench' / 'profil.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write('# Profil frame\n\n')
        f.write(f'{W}x{H}, {UKUR} frame diukur setelah {WARM} frame pemanasan.\n\n')
        f.write(f'Perender: **{vendor} — {perender}**\n\n')
        if lunak:
            f.write('> **Rasterizer perangkat lunak, tanpa GPU.** Kolom ms/frame\n'
                    '> didominasi fill rate CPU dan tidak mewakili mesin ber-GPU.\n'
                    '> Yang sah dibaca dari tabel ini: jumlah entity/GeomNode/Geom\n'
                    '> dan waktu Python. Keduanya tidak bergantung GPU.\n\n')
        f.write('| scene | entity | GeomNode | Geom | penuh ms | render ms | python ms | tersangka |\n')
        f.write('|---|--:|--:|--:|--:|--:|--:|---|\n')
        for nama, ne, nn, ng, mp, mr, mpy in baris:
            siapa = 'RENDER' if mr > mpy else 'PYTHON'
            f.write(f'| {nama} | {ne} | {nn} | {ng} | {mp:.1f} | {mr:.1f} | '
                    f'{mpy:.1f} | {siapa} |\n')
        for nama, teks in profil_teks.items():
            f.write(f'\n## cProfile — {nama}\n\n```\n{teks}```\n')
    print(f'laporan: {out}')

    sys.stdout.flush()
    os._exit(0)


if __name__ == '__main__':
    main()
