"""scene_export.py — Turunkan berkas scene dari kode, lalu buktikan identik.

Menulis `game/scenes/<nama>.json` dari KODE, lalu memuat ulang dari disk dan
membandingkannya dengan hasil kode. Keduanya harus identik.

Sejak Fase 3 game MEMAKAI berkas itu, jadi alat ini punya dua peran:

  - tanpa argumen: menurunkan ulang seluruh berkas dari kode. Ini yang dipakai
    setelah kode scene diubah, untuk menyelaraskan data kembali.
  - dengan `--check`: hanya memeriksa, dan keluar dengan kode 1 kalau ada yang
    berbeda. Itu drift detector antara kode dan data -- dan begitu editor peta
    bisa menulis berkas yang sama, ia juga yang memberi tahu kalau hasil editan
    menyimpang dari kode.

Bentuk teksnya tinggal di `game/scenes/scene_io.py` dan dipakai bersama editor,
supaya keduanya tidak pernah menghasilkan bentuk berkas yang berbeda.

Sisi "kode" sengaja dibangun ULANG dari `SCENE_BUILDERS`, bukan diambil dari
`SCENES`. Sejak Fase 3 `SCENES` berisi hasil bacaan berkas data, jadi
membandingkannya dengan berkasnya sendiri akan selalu setuju -- drift
detector-nya mati dan tidak membuktikan apa pun.

Pemakaian:
    python tools/scene_export.py             tulis lalu verifikasi
    python tools/scene_export.py --check     verifikasi saja, tanpa menulis
    python tools/scene_export.py farm town   scene tertentu
Keluar dengan kode 1 kalau ada yang tidak cocok.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# `bandingkan` tinggal di scene_roundtrip.py. Dipakai bersama supaya kedua alat
# tidak pernah punya gagasan berbeda tentang apa artinya "identik".
sys.path.insert(0, str(Path(__file__).resolve().parent))

from game.scenes import SCENE_BUILDERS               # noqa: E402
from game.scenes.scene_io import baca_scene, tulis_scene   # noqa: E402
from scene_roundtrip import bandingkan               # noqa: E402

SCENE_DIR = ROOT / 'game' / 'scenes'


def jalur(nama: str) -> Path:
    return SCENE_DIR / f'{nama}.json'


def main() -> int:
    hanya_cek = '--check' in sys.argv
    dipilih = [a for a in sys.argv[1:] if not a.startswith('--')]
    nama_scene = dipilih or sorted(SCENE_BUILDERS)

    tak_dikenal = [n for n in nama_scene if n not in SCENE_BUILDERS]
    if tak_dikenal:
        print(f'scene tidak dikenal: {tak_dikenal}')
        return 2

    mode = 'verifikasi saja' if hanya_cek else 'tulis + verifikasi'
    print(f'{mode} -- {len(nama_scene)} scene\n')
    print(f'{"scene":<13}{"berkas":>9}  hasil')

    gagal = 0
    total = 0
    for nama in nama_scene:
        asli = SCENE_BUILDERS[nama]()
        p = jalur(nama)

        if not hanya_cek:
            try:
                tulis_scene(asli, p)
            except Exception as e:
                print(f'{nama:<13}{"":>9}  GAGAL menulis: '
                      f'{type(e).__name__}: {e}')
                gagal += 1
                continue

        if not p.exists():
            print(f'{nama:<13}{"":>9}  GAGAL: berkas belum ada '
                  f'(jalankan tanpa --check)')
            gagal += 1
            continue

        ukuran = p.stat().st_size
        total += ukuran

        # Yang dibandingkan adalah scene hasil BACA DARI DISK, bukan dict di
        # memori. Itu yang membuktikan berkasnya sendiri bisa dimuat ulang.
        try:
            dari_disk = baca_scene(p)
        except Exception as e:
            print(f'{nama:<13}{ukuran/1024:>8.1f}K  GAGAL memuat: '
                  f'{type(e).__name__}: {e}')
            gagal += 1
            continue

        masalah = bandingkan(asli, dari_disk)
        tanda = 'LULUS' if not masalah else 'GAGAL'
        print(f'{nama:<13}{ukuran/1024:>8.1f}K  {tanda}')
        for m in masalah:
            print(f'    - {m}')
        gagal += bool(masalah)

    print(f'\n{len(nama_scene) - gagal}/{len(nama_scene)} scene identik '
          f'dengan kode  ({total/1024:.1f} KB di disk)')
    return 1 if gagal else 0


if __name__ == '__main__':
    sys.exit(main())
