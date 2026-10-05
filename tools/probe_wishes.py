"""probe_wishes.py — Panel Keinginan di permainan yang SUNGGUHAN.

`tools/uji_wishes.py` membuktikan mesinnya; alat ini membuktikan pemain bisa
MENCAPAINYA. Dua hal yang berbeda, dan yang kedua sudah pernah gagal di proyek
ini dengan cara yang tidak kelihatan:

  * `husbandry.py` lengkap dan benar, tapi `feed`/`water`/`clean` tidak punya
    pemanggil — jadi 434 baris tidak pernah tersentuh pemain.
  * HUD pernah tertata rapi di ruang UI yang salah, lalu seluruh isinya
    menumpuk di tengah layar.

Jadi yang diukur di sini keterjangkauan dan keterlihatan, lewat jalur tombol
yang sama dengan pemain:

  1. tekan `l` di HUD  -> mode jadi 'panel', namanya 'wishes'
  2. tekan `1`         -> satu janji masuk ke slot
  3. tekan `6`         -> janji itu dilupakan lagi
  4. tekan `a`         -> hadiah dibeli kalau Kebahagiaan cukup, ditolak dengan
                          alasan kalau tidak (bukan diam)
  5. tekan `escape`    -> panel tertutup, pemain tidak terkunci
  6. getTightBounds    -> seluruh teks panel ada DI DALAM layar
  7. tangkapan layar   -> piksel panelnya memang berubah, bukan panel kosong

Pemakaian:
    python tools/probe_wishes.py
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData  # noqa: E402
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

import logging  # noqa: E402
logging.basicConfig(level=logging.ERROR)

OUT = ROOT / '_bench' / 'probe'
W, H = 640, 360

hasil: list[tuple[str, bool, str]] = []


def cek(nama, ok, ket=''):
    hasil.append((nama, bool(ok), ket))


def _batas_ui():
    from ursina import camera
    try:
        fs = camera.ui_lens.getFilmSize()
        sk = camera.ui.getScale()[0]
        return abs(fs[0]) / 2.0 / sk, abs(fs[1]) / 2.0 / sk
    except Exception:
        return 0.889, 0.5


def _render(n=6):
    from direct.showbase.ShowBaseGlobal import base
    for _ in range(n):
        base.graphicsEngine.renderFrame()


def _tangkap(nama):
    from direct.showbase.ShowBaseGlobal import base
    from panda3d.core import Filename
    _render(8)
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / f'{nama}.png'
    img = base.win.getScreenshot()
    if img is None:
        return None
    img.write(Filename.fromOsSpecific(str(png)))
    from PIL import Image
    return Image.open(png).convert('RGB')


def uji_panel_hidup(g):
    import game.wishes as w
    from direct.showbase.ShowBaseGlobal import base

    s = g.state
    # Beri bekal supaya tawaran kaya: benih, pickaxe, pedang.
    s.inventory.setdefault('tomat_seed', 5)
    s.pickaxe_tier = 1
    s.sword_id = 'pedang_kayu'
    s.janji = []
    s.kebahagiaan = 0

    for _ in range(30):
        base.taskMgr.step()

    sebelum = _tangkap('wishes_hud')

    # 1. tombol pembuka
    g.input('l')
    for _ in range(3):
        base.taskMgr.step()
    cek('tekan [l] membuka panel Keinginan',
        g.panels.mode == 'panel' and g.panels._panel_name == 'wishes',
        f"mode={g.panels.mode} nama={getattr(g.panels, '_panel_name', None)}")

    isi = g.panels._panel_body.text or ''
    cek('panel punya isi', len(isi) > 60, f'{len(isi)} karakter')
    cek('panel menyebut Kebahagiaan', 'Kebahagiaan' in isi)
    cek('panel memajang tawaran', 'TAWARAN' in isi)

    # 2. janjikan
    n_awal = len(s.janji)
    g.input('1')
    for _ in range(2):
        base.taskMgr.step()
    cek('tekan [1] menambah satu janji', len(s.janji) == n_awal + 1,
        f'{n_awal} -> {len(s.janji)}'
        + (f" ({s.janji[-1]['teks']})" if s.janji else ''))

    # Garis dasarnya ikut tercatat lewat jalur tombol, bukan hanya di uji unit.
    if s.janji:
        j = s.janji[-1]
        cek('janji dari tombol membawa garis dasar', 'awal' in j,
            f"awal={j.get('awal')}")

    # 3. lupakan
    n = len(s.janji)
    g.input('6')
    for _ in range(2):
        base.taskMgr.step()
    cek('tekan [6] melupakan janji pertama', len(s.janji) == n - 1,
        f'{n} -> {len(s.janji)}')

    # 4. hadiah: tanpa Kebahagiaan harus DITOLAK DENGAN ALASAN, bukan diam
    s.kebahagiaan = 0
    maks_lama = s.max_energy
    pesan = g.panels.beli_hadiah_keinginan('a')
    cek('hadiah tanpa Kebahagiaan ditolak dengan alasan',
        bool(pesan) and s.max_energy == maks_lama, f'pesan={pesan!r}')

    s.kebahagiaan = 100_000
    pesan2 = g.panels.beli_hadiah_keinginan('a')
    cek('hadiah dengan Kebahagiaan cukup benar-benar menaikkan batas',
        s.max_energy > maks_lama, f'{maks_lama} -> {s.max_energy} ({pesan2})')

    # 5. ESC menutup dan tidak mengunci pemain
    g.input('escape')
    for _ in range(3):
        base.taskMgr.step()
    cek('ESC menutup panel dan kembali ke HUD', g.panels.mode == 'hud',
        f'mode={g.panels.mode}')

    # 6. seluruh teks panel di dalam layar
    g.input('l')
    for _ in range(3):
        base.taskMgr.step()
    _render(4)
    HX, HY = _batas_ui()
    luar = []
    for nama_e, e in (('judul', g.panels._panel_title),
                      ('isi', g.panels._panel_body),
                      ('hint', g.panels._panel_hint)):
        from ursina import camera
        kotak = e.getTightBounds(camera.ui)
        if not kotak:
            luar.append(f'{nama_e}: tanpa geometri')
            continue
        lo, hi = kotak
        if lo[0] < -HX - 1e-3 or hi[0] > HX + 1e-3:
            luar.append(f'{nama_e}: x {lo[0]:.3f}..{hi[0]:.3f} vs +-{HX:.3f}')
        if lo[2] < -HY - 1e-3 or hi[2] > HY + 1e-3:
            luar.append(f'{nama_e}: y {lo[2]:.3f}..{hi[2]:.3f} vs +-{HY:.3f}')
    cek('seluruh teks panel di dalam layar', not luar, '; '.join(luar) or
        f'batas UI +-{HX:.3f} x +-{HY:.3f}')

    # 7. panelnya benar-benar terlihat
    sesudah = _tangkap('wishes_panel')
    if sebelum is None or sesudah is None:
        cek('panel terlihat di layar', False, 'tangkapan layar gagal')
    else:
        pa, pb = sebelum.load(), sesudah.load()
        beda = sum(1 for y in range(0, H, 2) for x in range(0, W, 2)
                   if pa[x, y] != pb[x, y])
        total = (W // 2) * (H // 2)
        cek('panel benar-benar mengubah piksel layar', beda > total * 0.05,
            f'{beda}/{total} piksel berubah ({beda/total:.1%})')


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
        print('GAGAL TOTAL: game tidak bisa dibangun')
        traceback.print_exc()
        sys.exit(1)

    if g.panels.mode != 'hud':
        if getattr(g, '_chargen', None):
            g._chargen.destroy_all()
            g._chargen = None
        g.panels.mode = 'hud'

    try:
        uji_panel_hidup(g)
    except Exception as ex:
        traceback.print_exc()
        cek('probe meledak', False, f'{type(ex).__name__}: {ex}')

    print()
    print('PANEL KEINGINAN DI PERMAINAN SUNGGUHAN')
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
