"""probe_ternak.py — Loop perawatan ternak, lewat jalur tombol sungguhan.

`husbandry.py` jadi sumber kebenaran ternak (keputusan pemilik, 2026-10-07),
dan peluruhan hariannya dihidupkan kembali. Itu kombinasi yang pernah MERUSAK:
waktu `daily_tick` berjalan tanpa aksi perawatan yang terjangkau, kedelapan
ternak sakit permanen di hari 4 dan hati semua hewan menyentuh 0 di hari 6.

Jadi yang diukur di sini tepat hal itu, dua sisi sekaligus:

  TERAWAT    pemain yang mengurus ternaknya tidak boleh kehilangan satu pun
             hewan ke penyakit, dan harus benar-benar memanen hasilnya.
  TELANTAR   pemain yang MENGABAIKAN ternaknya memang harus menanggung
             akibatnya — kalau tidak, perawatannya tidak berarti apa-apa.

Keduanya perlu. Hanya menguji yang pertama membuat sistem yang tidak punya
konsekuensi apa pun tetap lulus; hanya menguji yang kedua adalah keadaan rusak
yang baru saja diperbaiki.

Aksinya dijalankan lewat `execute_pie_action` — jalur yang sama dengan tombol
pemain — bukan dengan memanggil husbandry langsung. Modul yang benar tapi tak
tersambung sudah dua kali terjadi di proyek ini.

Pemakaian:
    python tools/probe_ternak.py
"""
from __future__ import annotations

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


def _ternak():
    import game.husbandry as hb
    from game.data import ANIMAL_NPCS
    return [a for a in ANIMAL_NPCS if hb.is_livestock(a)]


def _bekali(s):
    """Beri pemain pakan berlimpah supaya yang diuji perawatannya, bukan stok."""
    for k in ('jerami', 'pakan', 'jagung', 'wortel', 'bayam', 'kacang_hijau',
              'ubi_jalar', 'ikan', 'telur', 'susu'):
        s.inventory[k] = 999


def uji_ternak(g):
    import game.husbandry as hb
    from direct.showbase.ShowBaseGlobal import base

    if g.panels.mode != 'hud':
        g.panels.close_all()
        g.panels.mode = 'hud'
        for _ in range(3):
            base.taskMgr.step()

    s = g.state
    hewan = _ternak()
    cek('ada ternak untuk diuji', bool(hewan), f'{len(hewan)} ekor')
    if not hewan:
        return

    # ── 1. Pilihan pie menu memang lima, dan labelnya menyebut keadaan ──
    _bekali(s)
    s.animal_care = {}
    aid = hewan[0]
    opts = g.player._build_pie_options(aid)
    aksi = {o[0] for o in opts}
    cek('pie kandang punya keempat pekerjaan',
        {'beri_makan', 'beri_minum', 'bersihkan'} <= aksi,
        f'aksi: {sorted(aksi)}')
    label = ' | '.join(o[1] for o in opts)
    cek('label pie menyebut keadaan hewan, bukan cuma nama aksi',
        '%' in label, label[:70])

    # ── 2. Tiap aksi benar-benar mengubah takaran DAN memakai energi ──
    rec = hb.care_of(s, aid)
    rec['kenyang'], rec['air'], rec['bersih'] = 10, 10, 10
    s.energy = 100
    for act, kunci in (('beri_makan', 'kenyang'), ('beri_minum', 'air'),
                       ('bersihkan', 'bersih')):
        sebelum = rec[kunci]
        en_sebelum = s.energy
        g.player.execute_pie_action(aid, act, g.entities, g.panels)
        cek(f'[{act}] menaikkan {kunci}', rec[kunci] > sebelum,
            f'{sebelum}% -> {rec[kunci]}%')
        cek(f'[{act}] memakai energi', s.energy < en_sebelum,
            f'{en_sebelum} -> {s.energy}')

    # ── 3. Pemain yang MERAWAT tidak kehilangan hewan ──
    s.animal_care = {}
    s.npc_hearts = {a: 5 for a in hewan}
    _bekali(s)
    panen = 0
    for hari in range(1, 15):
        s.day = hari
        s.energy = 100
        for a in hewan:
            for act in ('beri_makan', 'beri_minum', 'bersihkan'):
                g.player.execute_pie_action(a, act, g.entities, g.panels)
            sebelum = s.stats.get('produce_collected', 0)
            g.player.execute_pie_action(a, 'ambil_hasil', g.entities, g.panels)
            panen += s.stats.get('produce_collected', 0) - sebelum
        hb.daily_tick(s)
    sakit = [a for a in hewan if hb.care_of(s, a)['sakit']]
    cek('dirawat 14 hari: tidak ada yang sakit', not sakit,
        f'{len(sakit)} sakit dari {len(hewan)}')
    cek('dirawat 14 hari: benar-benar memanen hasil', panen > 0,
        f'{panen} hasil dipungut')
    hati_turun = [a for a in hewan if s.npc_hearts.get(a, 0) < 5]
    cek('dirawat 14 hari: hati tidak turun', not hati_turun,
        f'{len(hati_turun)} hewan hatinya turun')

    # ── 4. Pemain yang MENELANTARKAN memang menanggung akibatnya ──
    s2_care, s2_hearts = {}, {a: 5 for a in hewan}
    s.animal_care, s.npc_hearts = s2_care, s2_hearts
    for hari in range(1, 15):
        s.day = hari
        hb.daily_tick(s)
    sakit2 = [a for a in hewan if hb.care_of(s, a)['sakit']]
    cek('ditelantarkan 14 hari: ada akibatnya', bool(sakit2),
        f'{len(sakit2)} dari {len(hewan)} jatuh sakit')


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
        uji_ternak(g)
    except Exception as ex:
        import traceback
        traceback.print_exc()
        cek('probe meledak', False, f'{type(ex).__name__}: {ex}')

    print()
    print('LOOP PERAWATAN TERNAK')
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
