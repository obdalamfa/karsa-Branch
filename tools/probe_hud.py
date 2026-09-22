"""probe_hud.py — Buktikan tidak ada elemen HUD yang terpotong tepi layar.

Kegagalan nyata yang melatarinya: pada tangkapan layar 1280x720 jam, tanggal,
cuaca, nama scene dan uang semuanya lari keluar tepi kanan — "Hari 1 | Musim
S…", "> Kebun Paman…". Teks-teks itu ditempatkan di x=0,70 dengan perataan
KIRI, padahal tepi kanan ruang UI Ursina cuma aspect/2 (0,889 pada 16:9).
Sisanya 0,189 satuan, dan tidak satu pun baris itu muat.

Kenapa butuh alat, bukan mata: lebar teks berubah mengikuti isinya. "Hari 1 |
Semi" muat, "Hari 28 | Musim Gugur" tidak. Pemeriksaan sekali lihat pada satu
hari kebetulan lolos, lalu rusak diam-diam di hari lain. Jadi probe ini mengisi
HUD dengan NILAI TERPANJANG yang mungkin muncul, bukan nilai awal.

Yang diukur: kotak batas sejati tiap NodePath relatif `camera.ui`
(getTightBounds), bukan lebar hasil hitungan Ursina — sama seperti probe arah,
yang ditanya mesinnya sendiri, bukan pembungkusnya.

Pemakaian:
    python tools/probe_hud.py                 resolusi default 1280x720
    python tools/probe_hud.py 800 600         resolusi lain

Keluar dengan kode 1 kalau ada yang terpotong.
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
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'aux-display pandadx9')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

import logging  # noqa: E402
logging.basicConfig(level=logging.ERROR)

# Nilai terpanjang yang bisa muncul di tiap teks HUD. Kalau ini muat, semua
# nilai lain juga muat.
TERPANJANG = {
    '_time_txt':    '23:59',
    '_date_txt':    'Hari 28 | Musim Gugur',
    '_weather_txt': '^ Berangin',
    '_scene_txt':   '> Gua Bertingkat 15',
    '_gold_txt':    '§ 999999G',
    '_tool_name':   'Cangkul',
    '_seed_txt':    'Benih: Stroberi',
    '_buff_txt':    'Kenyang +2 hari',
    '_queue_txt':   'Menyiram  [##########] 100%  (+9 antri)',
    '_mood_lbl':    'SUASANA HATI',
}


def batas_ui():
    """Setengah-lebar dan setengah-tinggi ruang camera.ui yang terlihat."""
    from ursina import camera
    fs = camera.ui_lens.getFilmSize()
    skala = camera.ui.getScale()[0]
    return (fs[0] / 2.0) / skala, (fs[1] / 2.0) / skala


def kumpulkan(ui_mgr):
    """(nama, NodePath) tiap elemen HUD yang harus tetap di dalam layar."""
    hasil = []
    for nama, nilai in vars(ui_mgr).items():
        if nama.startswith('_') and hasattr(nilai, 'getTightBounds'):
            hasil.append((nama, nilai))
        elif isinstance(nilai, list):
            for i, e in enumerate(nilai):
                if hasattr(e, 'getTightBounds'):
                    hasil.append((f'{nama}[{i}]', e))
    return hasil


def uji_hud(g):
    """Uji semua elemen HUD terhadap tepi layar. -> [(nama, lulus, catatan)].

    Dipakai oleh main() di sini DAN oleh tools/regress.py, supaya jaring
    pengaman memakai alat ukur yang sama persis dengan probe manual.
    """
    from ursina import camera
    p = g.panels
    for nama, teks in TERPANJANG.items():
        ent = getattr(p, nama, None)
        if ent is not None and hasattr(ent, 'text'):
            ent.text = teks
    from direct.showbase.ShowBaseGlobal import base
    for _ in range(6):
        base.taskMgr.step()

    hx, hy = batas_ui()
    hasil = []
    for nama, ent in sorted(kumpulkan(p)):
        if not getattr(ent, 'enabled', True):
            continue
        try:
            kotak = ent.getTightBounds(camera.ui)
        except Exception:
            continue
        if not kotak:
            continue
        lo, hi = kotak
        lewat = []
        if lo.x < -hx - 1e-4: lewat.append(f'kiri {lo.x:+.3f}')
        if hi.x > hx + 1e-4:  lewat.append(f'kanan {hi.x:+.3f}')
        if lo.y < -hy - 1e-4: lewat.append(f'bawah {lo.y:+.3f}')
        if hi.y > hy + 1e-4:  lewat.append(f'atas {hi.y:+.3f}')
        hasil.append((nama, not lewat,
                      ('keluar ' + ', '.join(lewat)) if lewat else 'di dalam'))
    return hasil


def main():
    from ursina import application
    application.asset_folder = ROOT
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    arg = [a for a in sys.argv[1:] if not a.startswith('-')]
    W = int(arg[0]) if len(arg) > 0 else 1280
    H = int(arg[1]) if len(arg) > 1 else 720

    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = W, H

    from game.app import Game3D
    try:
        g = Game3D()
    except Exception:
        print('GAGAL TOTAL: game tidak bisa dibangun\n')
        traceback.print_exc()
        sys.exit(1)

    from direct.showbase.ShowBaseGlobal import base
    from ursina import camera

    p = g.panels
    if p.mode != 'hud':
        if getattr(g, '_chargen', None):
            g._chargen.destroy_all()
            g._chargen = None
        p.mode = 'hud'

    # Isi dengan nilai terpanjang sebelum diukur.
    for nama, teks in TERPANJANG.items():
        ent = getattr(p, nama, None)
        if ent is not None and hasattr(ent, 'text'):
            ent.text = teks

    for _ in range(10):
        base.taskMgr.step()

    hx, hy = batas_ui()
    print()
    print(f'layar {W}x{H}, ruang UI terlihat: x ±{hx:.3f}, y ±{hy:.3f}')
    print(f'{"elemen":24s} {"hasil":>6s}  {"kiri":>7s} {"kanan":>7s} {"bawah":>7s} {"atas":>7s}  catatan')
    print('-' * 96)

    gagal = 0
    for nama, ent in sorted(kumpulkan(p)):
        if not getattr(ent, 'enabled', True):
            continue
        try:
            kotak = ent.getTightBounds(camera.ui)
        except Exception:
            continue
        if not kotak:
            continue
        lo, hi = kotak
        lewat = []
        if lo.x < -hx - 1e-4: lewat.append(f'kiri {lo.x:+.3f}')
        if hi.x > hx + 1e-4:  lewat.append(f'kanan {hi.x:+.3f}')
        if lo.y < -hy - 1e-4: lewat.append(f'bawah {lo.y:+.3f}')
        if hi.y > hy + 1e-4:  lewat.append(f'atas {hi.y:+.3f}')
        if lewat:
            gagal += 1
        tanda = 'GAGAL' if lewat else 'LULUS'
        catatan = 'keluar ' + ', '.join(lewat) if lewat else ''
        if lewat:
            print(f'{nama:24s} {tanda:>6s}  {lo.x:+7.3f} {hi.x:+7.3f} {lo.y:+7.3f} {hi.y:+7.3f}  {catatan}')

    print('-' * 96)
    print('SEMUA ELEMEN HUD DI DALAM LAYAR' if not gagal
          else f'{gagal} elemen HUD terpotong tepi layar')
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
