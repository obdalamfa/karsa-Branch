"""scene_export.py — Fase 2: tulis scene ke JSON, lalu buktikan identik.

Menulis `game/scenes/<nama>.json` dari kode, lalu MEMUAT ULANG dari disk dan
membandingkannya dengan hasil kode. Keduanya harus identik.

Pada akhir fase ini berkasnya ADA tapi belum berpengaruh apa pun: game masih
membangun seluruh scene dari kode (`game/scenes/__init__.py` memanggil
`build_*()`). Itu disengaja. Fase 3 baru membuat game memuat JSON, dan sampai
saat itu seluruh fase ini bisa dibatalkan tanpa risiko apa pun.

Pemakaian:
    python tools/scene_export.py             tulis lalu verifikasi
    python tools/scene_export.py --check     verifikasi saja, tanpa menulis
    python tools/scene_export.py farm town   scene tertentu
Keluar dengan kode 1 kalau ada yang tidak cocok.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# `bandingkan` tinggal di scene_roundtrip.py. Dipakai bersama supaya kedua alat
# tidak pernah punya gagasan berbeda tentang apa artinya "identik".
sys.path.insert(0, str(Path(__file__).resolve().parent))

from game.scenes import SCENE_BUILDERS               # noqa: E402
from game.scenes.scene_base import Scene             # noqa: E402
from scene_roundtrip import bandingkan               # noqa: E402

SCENE_DIR = ROOT / 'game' / 'scenes'


def jalur(nama: str) -> Path:
    return SCENE_DIR / f'{nama}.json'


# Field yang isinya "daftar baris kecil", ditulis SATU BARIS PER ELEMEN.
# `tiles` = satu baris per baris peta, `portals` = satu baris per portal,
# `paint` = satu baris per zona. Selebihnya memakai indentasi JSON biasa.
_RINGKAS = ('tiles', 'portals', 'paint')


def teks_scene(data: dict) -> str:
    """JSON scene dengan bentuk yang bisa dibaca manusia.

    `json.dumps(indent=2)` menaruh tiap ANGKA di barisnya sendiri: `farm` jadi
    731 baris dan bentuk petanya tidak terlihat sama sekali -- padahal justru
    itu keunggulan berkas ini dibanding kode. Di sini `tiles`, `portals`, dan
    `paint` ditulis satu baris per elemen, sehingga ladang, kandang, dan kolam
    terbaca langsung dari berkasnya. `farm` turun ke 151 baris dan seluruh dunia
    dari 72 KB ke 30 KB.

    `docs/TATA_LETAK.md` P3 menuntut bentuk zona terlihat di sumbernya, bukan
    cuma di layar saat game dijalankan; `layout.py` ada karena masalah yang sama
    di kode. Berkas ini melanjutkan maksud itu.

    Field lain tetap di-indentasi supaya diff satu nilai tetap satu baris.
    """
    bagian = []
    for kunci, nilai in data.items():
        nama = json.dumps(kunci)
        if kunci in _RINGKAS and isinstance(nilai, list):
            baris = ',\n'.join(
                '    ' + json.dumps(e, ensure_ascii=False) for e in nilai)
            bagian.append(f'  {nama}: [\n{baris}\n  ]')
        else:
            teks = json.dumps(nilai, indent=2, ensure_ascii=False)
            bagian.append(f'  {nama}: {teks.replace(chr(10), chr(10) + "  ")}')
    return '{\n' + ',\n'.join(bagian) + '\n}\n'


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
        # Sisi "kode" dibangun ULANG dari fungsi builder, bukan diambil dari
        # SCENES. Sejak Fase 3 SCENES berisi hasil bacaan berkas data, jadi
        # membandingkannya dengan berkasnya sendiri akan selalu setuju --
        # drift detector-nya mati dan tidak membuktikan apa pun.
        asli = SCENE_BUILDERS[nama]()
        p = jalur(nama)

        if not hanya_cek:
            try:
                p.write_text(teks_scene(asli.to_dict()), encoding='utf-8')
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
            # `utf-8-sig` menerima berkas dengan maupun tanpa BOM, sama seperti
            # pemuat di game/scenes/__init__.py.
            dari_disk = Scene.from_dict(
                json.loads(p.read_text(encoding='utf-8-sig')))
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
