"""scene_roundtrip.py — Gerbang untuk menjadikan scene sebagai DATA.

Membuktikan `Scene` bisa bolak-balik lewat dict TANPA berubah sedikit pun.

Selama tes ini belum hijau untuk KELIMA BELAS scene, tidak boleh ada berkas
scene yang ditulis dan game tidak boleh memuatnya. Alasannya ada di
`docs/CODE_MAP.md` hambatan #13: format yang belum terbukti hanya menambah
sumber kebenaran kedua, dan dua sumber kebenaran yang berbeda diam-diam adalah
cara paling tenang untuk merusak peta.

Yang diperiksa per scene:

  - grid ubin identik, sel per sel (bukan cuma ukurannya)
  - zona cat identik, termasuk urutannya
  - portal identik, termasuk urutannya
  - indoor, has_horizon, nama builder, name, display, w, h
  - `to_dict()` STABIL: dipanggil dua kali menghasilkan dict yang sama
  - bolak-balik lewat JSON sungguhan (`dumps` -> `loads`), bukan cuma dict
  - builder hasil rekonstruksi benar-benar bisa dipanggil

Pemakaian:
    python tools/scene_roundtrip.py                 semua scene
    python tools/scene_roundtrip.py farm naga_cave  scene tertentu
Keluar dengan kode 1 kalau ada yang gagal.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game.scenes import SCENE_BUILDERS             # noqa: E402
from game.scenes.scene_base import (               # noqa: E402
    BUILDER_NAMES, Scene, tile_key, TILE_IDS,
)


def bandingkan(asli: Scene, ulang: Scene) -> list[str]:
    """Daftar perbedaan antara scene asli dan hasil rekonstruksi."""
    beda = []

    for field in ('name', 'display', 'w', 'h', 'indoor', 'has_horizon',
                  'builder_name'):
        a, b = getattr(asli, field), getattr(ulang, field)
        if a != b:
            beda.append(f'{field}: {a!r} -> {b!r}')

    # Grid: laporkan sel pertama yang berbeda, bukan sekadar "tidak sama" --
    # pesan yang menyebut koordinat langsung menunjuk ke penyebabnya.
    if asli.tiles != ulang.tiles:
        ketemu = False
        for y in range(min(asli.h, ulang.h)):
            for x in range(min(asli.w, ulang.w)):
                if asli.tiles[y][x] != ulang.tiles[y][x]:
                    beda.append(
                        f'ubin ({x},{y}): {tile_key(asli.tiles[y][x])} -> '
                        f'{tile_key(ulang.tiles[y][x])}')
                    ketemu = True
                    break
            if ketemu:
                break
        if not ketemu:
            beda.append(f'bentuk grid berbeda: {asli.h}x{asli.w} vs '
                        f'{ulang.h}x{ulang.w}')

    if asli.portals != ulang.portals:
        beda.append(f'portals: {asli.portals} -> {ulang.portals}')

    zona_a = [z.to_dict() for z in asli.paint]
    zona_b = [z.to_dict() for z in ulang.paint]
    if zona_a != zona_b:
        beda.append(f'paint: {zona_a} -> {zona_b}')

    if asli.objects != ulang.objects:
        beda.append(f'objects: {len(asli.objects)} -> {len(ulang.objects)}')
        # Sebut objek pertama yang berbeda, bukan seluruh daftar: peta dengan
        # banyak objek akan membanjiri laporan dan menyembunyikan yang penting.
        for i, (a, b) in enumerate(zip(asli.objects, ulang.objects)):
            if a != b:
                beda.append(f'  objek[{i}]: {a} -> {b}')
                break

    if asli.builder_name not in BUILDER_NAMES:
        beda.append(f"nama builder '{asli.builder_name}' tidak ada di "
                    f'BUILDER_NAMES {BUILDER_NAMES}')
    if not callable(ulang.builder):
        beda.append('builder hasil rekonstruksi tidak bisa dipanggil')

    return beda


def main() -> int:
    dipilih = sys.argv[1:]
    nama_scene = dipilih or sorted(SCENE_BUILDERS)

    tak_dikenal = [n for n in nama_scene if n not in SCENE_BUILDERS]
    if tak_dikenal:
        print(f'scene tidak dikenal: {tak_dikenal}')
        return 2

    print(f'{"scene":<13}{"ubin":>7}{"zona":>6}{"portal":>7}  hasil')
    gagal = 0
    for nama in nama_scene:
        # Dibangun dari KODE, bukan diambil dari SCENES: sejak Fase 3 SCENES
        # bisa berisi hasil bacaan berkas data, sedangkan tes ini menguji
        # FORMAT-nya, bukan datanya.
        asli = SCENE_BUILDERS[nama]()
        masalah = []

        # 1. Bolak-balik lewat dict.
        try:
            d1 = asli.to_dict()
            ulang = Scene.from_dict(d1)
        except Exception as e:
            print(f'{nama:<13}{"":>7}{"":>6}{"":>7}  GAGAL: '
                  f'{type(e).__name__}: {e}')
            gagal += 1
            continue
        masalah += bandingkan(asli, ulang)

        # 2. `to_dict()` harus stabil. Legend dibangun dari urutan kemunculan
        #    ubin; kalau urutannya tidak deterministik, dua penyimpanan berturut
        #    -turut menghasilkan berkas berbeda untuk peta yang sama.
        if asli.to_dict() != d1:
            masalah.append('to_dict() tidak stabil antar-panggilan')

        # 3. Bolak-balik lewat JSON sungguhan, bukan cuma dict. Ini yang
        #    menangkap tipe yang tidak JSON-native (tuple, set, np.int64).
        try:
            lewat_json = Scene.from_dict(json.loads(json.dumps(d1)))
        except Exception as e:
            masalah.append(f'JSON: {type(e).__name__}: {e}')
            lewat_json = None
        if lewat_json is not None:
            masalah += [f'(via JSON) {m}' for m in bandingkan(asli, lewat_json)]

        # 4. Setiap nama di legend harus ada di TILE_IDS -- kalau tidak,
        #    berkasnya tidak akan bisa dimuat lagi setelah ditulis.
        for key in d1['legend']:
            if key not in TILE_IDS:
                masalah.append(f'legend memuat nama ubin tak dikenal: {key}')

        tanda = 'LULUS' if not masalah else 'GAGAL'
        print(f'{nama:<13}{asli.w * asli.h:>7}{len(asli.paint):>6}'
              f'{len(asli.portals):>7}  {tanda}')
        for m in masalah:
            print(f'    - {m}')
        gagal += bool(masalah)

    print(f'\n{len(nama_scene) - gagal}/{len(nama_scene)} scene bolak-balik utuh')
    return 1 if gagal else 0


if __name__ == '__main__':
    sys.exit(main())
