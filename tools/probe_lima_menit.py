"""probe_lima_menit.py — lima menit pertama pemain baru, dari boot sampai panen.

Modal PAGI PERTAMA (Majelis Batin) terbuka di cangkul pertama dan menelan
tombol sampai dijawab; probe menjawabnya dengan tombol yang tertulis di modal
itu sendiri (`jawab_modal_batin`), seperti pemain yang membacanya.

DoD M1 ROADMAP: "orang baru bisa panen pertama tanpa bertanya". Tidak ada
alat yang pernah mengukurnya. Probe ini memulai game TANPA save (layar Buat
Karakter muncul, seperti pemain baru), lalu mengikuti petunjuk tutorial di
HUD apa adanya -- tombol yang disebut petunjuk itulah yang ditekan.

Semua aksi lewat `Game3D.input()`. Yang TIDAK lewat tombol hanya perpindahan
pemain antar-petak (`set_tile_pos` + `facing`), karena jalan kaki WASD sudah
dijaga `arah_maju` di regresi, dan yang diuji di sini adalah apakah petunjuk
tutorial benar-benar membawa pemain sampai panen.

    python tools/probe_lima_menit.py
"""
from __future__ import annotations

import os
import re
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

hasil: list[tuple[str, bool, str]] = []


def cek(nama, ok, ket=''):
    hasil.append((nama, bool(ok), ket))


def langkah(n=6):
    from direct.showbase.ShowBaseGlobal import base
    for _ in range(n):
        base.taskMgr.step()


def tombol_petunjuk(s) -> str | None:
    """Huruf tombol yang disebut petunjuk tutorial saat ini, mis. 'r'."""
    from game.tutorial import tracker_lines
    _, _, hint = tracker_lines(s)
    m = re.search(r'\[([A-Z])\]', hint or '')
    return m.group(1).lower() if m else None


def jawab_modal_batin(g):
    """Cangkul pertama membuka modal PAGI PERTAMA (Majelis Batin), yang
    menelan tombol sampai dijawab. Pemain baru membaca modalnya dan menekan
    tombol yang TERTULIS di sana ('Tekan 1-3 untuk memilih.') -- jadi probe
    juga membacanya, bukan menebak. Mengembalikan tombol yang ditekan."""
    p = g.panels
    if p.mode != 'batin':
        return None
    for e in getattr(p, '_bc_ents', []) or []:
        m = re.search(r'Tekan (\d)-\d', getattr(e, 'text', '') or '')
        if m:
            g.input(m.group(1))
            langkah(4)
            return m.group(1)
    return None


def tonton_sinema(g):
    """Sinema yang terpicu di tengah jalan (mis. 'panen_pertama' pada tahap
    quest 2, tepat saat pemain berjalan ke kasur) menelan tombol berikutnya.
    Pemain melihatnya dan menekan SPACE sampai selesai; probe juga. Dulu ini
    tidak pernah terjadi di probe: ESC di sinema intro meninggalkan
    `sinema.aktif` True selamanya, jadi sinema berikutnya tidak bisa mulai."""
    for _ in range(200):
        if not g.sinema.aktif:
            return
        if g.sinema._menunggu:
            g.input('space')
        langkah(2)


def ke_hud(g):
    """Tutup apa pun yang terbuka (dialog, sinema) seperti pemain: escape."""
    for _ in range(6):
        if g.panels.mode == 'hud':
            return True
        g.input('escape')
        langkah(4)
    return g.panels.mode == 'hud'


def jalan(g, scene, x, y, hadap):
    from direct.showbase.ShowBaseGlobal import base
    s = g.state
    if s.scene_name != scene:
        s.scene_name = scene
        for _ in range(30):
            base.taskMgr.step()
    g.player.set_tile_pos(x, y)
    g.player.facing = hadap
    langkah(3)


def uji(g):
    from game.config import MB
    from game.scenes import SCENES
    s = g.state

    # 1. pemain baru: Buat Karakter -> Enter -> sinema -> escape
    cek('game baru membuka Buat Karakter', g.panels.mode == 'chargen',
        f'mode={g.panels.mode}')
    g.input('enter')
    langkah(30)
    cek('sampai di HUD setelah Enter dan melewati sinema', ke_hud(g),
        f'mode={g.panels.mode}')

    # 2. surat: berdiri menghadap kotak pos, tekan tombol yang DISEBUT petunjuk
    mb = next((x, y) for y, r in enumerate(SCENES['farm'].tiles)
              for x, v in enumerate(r) if v == MB)
    jalan(g, 'farm', mb[0], mb[1] - 1, 'up')
    t = tombol_petunjuk(s)
    g.input(t or 'e')
    langkah(6)
    cek(f'langkah 1 "{t}" sesuai petunjuk membaca surat', s.mail_read,
        f'tombol petunjuk={t!r} mail_read={s.mail_read}')
    ke_hud(g)
    if not s.mail_read:
        return

    # 3-5. cangkul, tanam, siram tiga petak di ladang (x 10..12, y 12)
    petak = [(10, 12), (11, 12), (12, 12)]
    for alat, stat, nama in (('1', 'tilled', 'cangkul'),
                             ('3', 'lobak_planted', 'tanam'),
                             ('2', 'watered', 'siram')):
        g.input(alat)
        awal = s.stats.get(stat, 0)
        for x, y in petak:
            jalan(g, 'farm', x, y - 1, 'up')
            g.input('space')
            langkah(8)
            jawab_modal_batin(g)
        cek(f'{nama} 3 petak dengan [{alat}] + [SPACE]',
            s.stats.get(stat, 0) - awal >= 3, f'{stat}: {awal} -> {s.stats.get(stat, 0)}')

    # 6. tidur: ikuti petunjuk ("masuk rumah ... tekan [X]") sampai hari 3,
    # siram lagi tiap pagi; lobak butuh dua hari.
    for hari in range(2):
        # Petunjuk: "berdiri di kasur" -- jadi berdiri DI ubin kasur.
        from game.config import BD
        bd = next((x, y) for y, r in enumerate(SCENES['house'].tiles)
                  for x, v in enumerate(r) if v == BD)
        jalan(g, 'house', bd[0], bd[1], 'down')
        tonton_sinema(g)
        t = tombol_petunjuk(s) or 't'
        d0 = s.day
        g.input(t)
        langkah(30)
        ke_hud(g)
        if s.day == d0:
            cek(f'tidur hari {d0} dengan [{t.upper()}] sesuai petunjuk', False,
                f'hari tetap {s.day}')
            g.input('t')                 # tombol tidur yang sebenarnya
            langkah(30)
            ke_hud(g)
        if hari == 0:
            cek('hari berganti setelah tidur', s.day == d0 + 1, f'{d0} -> {s.day}')
        g.input('2')
        for x, y in petak:
            jalan(g, 'farm', x, y - 1, 'up')
            g.input('space')
            langkah(6)

    # 7. panen
    g.input('4')
    awal = s.stats.get('lobak_harvested', 0)
    for x, y in petak:
        jalan(g, 'farm', x, y - 1, 'up')
        g.input('space')
        langkah(8)
    cek('panen lobak pertama', s.stats.get('lobak_harvested', 0) > awal,
        f'lobak_harvested {awal} -> {s.stats.get("lobak_harvested", 0)} (hari {s.day})')


def main():
    from ursina import application
    application.asset_folder = ROOT
    application.fonts_folder = ROOT / 'assets' / 'fonts'
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))
    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = 640, 360
    save = ROOT / cfg.SAVE_FILE
    if save.exists():
        print(f'{save.name} ada; probe ini butuh game BARU. Pindahkan dulu.')
        sys.exit(2)
    from game.app import Game3D
    try:
        g = Game3D()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    try:
        uji(g)
    except Exception as ex:
        traceback.print_exc()
        cek('probe meledak', False, f'{type(ex).__name__}: {ex}')
    finally:
        save.unlink(missing_ok=True)     # game menyimpan sendiri; jangan tinggalkan

    print('\nLIMA MENIT PERTAMA — mengikuti petunjuk tutorial')
    print('=' * 78)
    lebar = max(len(n) for n, _, _ in hasil)
    for nama, ok, ket in hasil:
        print(f"{'LULUS' if ok else 'GAGAL':>5s}  {nama:<{lebar}s}  {ket}")
    gagal = [n for n, ok, _ in hasil if not ok]
    print('-' * 78)
    print(f'{len(hasil) - len(gagal)}/{len(hasil)} lulus')
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
