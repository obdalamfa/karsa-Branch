"""proto_wish.py — PROTOTIPE SEKALI PAKAI. Bukan bagian dari game.

Menjawab satu pertanyaan dari tiket "Dari mana sebuah Wish muncul?":
apakah kandidat berskor tinggi dari mesin otonomi terbaca sebagai KEINGINAN,
atau cuma sebagai kebutuhan mendesak yang berganti baju?

Hipotesis yang diuji, dan ia ada di tiketnya sendiri: "Arya ingin ke kamar
mandi" bukan wish, itu cuma motif rendah. Kalau benar, wish harus datang dari
sesuatu yang justru TIDAK mendesak.

Jadi tiap warga dicetak dua kolom:

  LAKUKAN   kandidat skor tertinggi — yang benar-benar akan dikerjakan mesin
            otonomi sekarang. Ini kebutuhan.
  INGIN     kandidat tertinggi SETELAH membuang semua interaksi yang
            mengiklankan motif paling mendesak warga itu. Ini yang tersisa
            kalau kebutuhan yang berteriak paling keras diabaikan.

Kalau kolom INGIN terbaca sebagai orang yang menginginkan sesuatu sementara
kolom LAKUKAN terbaca sebagai daftar tugas, hipotesisnya benar dan wish harus
lahir dari kolom kedua.

Dibuang setelah tiketnya ditutup. Tidak dipanggil siapa pun, tidak diuji
regresi, dan tidak boleh ada kode game yang mengimpornya.

    xvfb-run -a python tools/proto_wish.py farm 8
    xvfb-run -a python tools/proto_wish.py town 13
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData  # noqa: E402
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

import logging  # noqa: E402
logging.basicConfig(level=logging.CRITICAL)


def kandidat_berskor(mv, peta, ubin):
    """[(skor, objek, interaksi), ...] terurut, hanya yang berskor positif."""
    from game.motives import score_interaction
    from game.objects import autonomy_candidates
    out = []
    for obj, inter, jarak in autonomy_candidates(peta, ubin[0], ubin[1]):
        if not inter.autonomous:
            continue
        s = score_interaction(mv, inter, jarak)
        if s > 1e-6:
            out.append((s, obj, inter))
    out.sort(key=lambda t: -t[0])
    return out


def motif_paling_mendesak(mv):
    """Motif terendah, TIDAK termasuk `ruang`.

    `ruang` tidak pernah meluruh — diukur: 0,0 poin per hari-sim, satu-satunya
    dari delapan. Ia bertahan di 0,0 sementara yang lain mulai positif, jadi
    `min()` polos selalu menobatkannya sebagai "paling mendesak" padahal ia
    tidak mendesak apa pun. Temuan sampingan yang layak dicatat: `ruang` adalah
    motif mati di mesin ini.
    """
    from game.motives import MOTIVES
    hidup = [m for m in MOTIVES if m != 'ruang']
    return min(hidup, key=lambda m: mv.get(m))


def main():
    scene = sys.argv[1] if len(sys.argv) > 1 else 'farm'
    jam = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0

    from ursina import application
    application.asset_folder = ROOT
    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = 320, 180

    from game.app import Game3D
    g = Game3D()
    from direct.showbase.ShowBaseGlobal import base
    for _ in range(20):
        base.taskMgr.step()

    g.state.time_minutes = jam * 60.0
    g.state.scene_name = scene
    for _ in range(40):
        base.taskMgr.step()

    br = g.entities.brains
    br.rebuild_grid(scene)
    from game.motives import LABELS
    from game.objects import object_name

    print()
    print(f'scene {scene}  jam {int(jam):02d}:00')
    print('=' * 78)

    # Beberapa jam berturut-turut supaya terlihat apakah pilihannya berganti
    # seperti kepribadian atau seperti kebisingan.
    for langkah in range(4):
        hadir = [n for n in br._brains if br._di_scene_aktif(n)]
        if not hadir:
            print('  (tidak ada warga di scene ini pada jam segini)')
            break
        jam_kini = int((g.state.time_minutes // 60) % 24)
        print()
        print(f'--- jam {jam_kini:02d}:00 ---')
        for npc_id in sorted(hadir):
            mv = br._motif.get(npc_id)
            ubin = br._posisi_ubin(npc_id)
            if mv is None or ubin is None or br.peta is None:
                continue
            semua = kandidat_berskor(mv, br.peta, ubin)
            if not semua:
                print(f'  {npc_id:11s} (tidak ada perabot dalam jangkauan)')
                continue

            mendesak = motif_paling_mendesak(mv)
            lakukan = semua[0]

            # Buang semua yang mengiklankan motif paling mendesak.
            sisa = [t for t in semua
                    if not any(a.motive == mendesak for a in t[2].adverts)]
            ingin = sisa[0] if sisa else None

            def sebut(t):
                if t is None:
                    return '—'
                _, obj, inter = t
                return f'{inter.name} pada {object_name(obj[2])}'

            n_obj = len({(o[0], o[1]) for _, o, _ in semua})
            print(f'  {npc_id:11s} mendesak={LABELS[mendesak]:<12s} '
                  f'({mv.get(mendesak):+6.1f})  kandidat={len(semua)} '
                  f'dari {n_obj} objek')
            print(f'  {"":11s}   LAKUKAN  {sebut(lakukan)}')
            print(f'  {"":11s}   INGIN    {sebut(ingin)}')

        # Majukan satu jam-sim penuh lewat otak, bukan lewat frame.
        for _ in range(60):
            br.tick(1.0)
        g.state.time_minutes += 60.0

    print()
    os._exit(0)


if __name__ == '__main__':
    main()
