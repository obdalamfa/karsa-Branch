"""scene_io.py — Bentuk TEKS berkas scene, dan baca/tulisnya.

Dipisahkan dari `scene_base.py` dengan sengaja:

  - `scene_base` adalah bentuk DATA yang dipakai game setiap kali dijalankan.
  - modul ini adalah bentuk BERKAS, yang hanya dipakai alat yang MENULIS dan
    MEMBACA scene: `tools/scene_export.py` dan editor peta.

Game tidak pernah menulis scene. Kalau bentuk teksnya ditaruh di `scene_base`,
ia jadi kode mati di jalur yang berjalan tiap frame -- dan audit proyek ini
sudah pernah menegur kebiasaan itu.

Dua pemakai modul ini adalah alasannya ada. Kalau `tools/scene_export.py` dan
editor masing-masing punya penulisnya sendiri, keduanya akan perlahan
menghasilkan bentuk berkas yang berbeda, dan tiap penyimpanan dari editor akan
memperlihatkan diff besar yang isinya hanya perbedaan format.
"""
import json
from pathlib import Path

from .scene_base import SCENE_VERSION, Scene

# Field yang isinya "daftar baris kecil", ditulis SATU BARIS PER ELEMEN.
# `tiles` = satu baris per baris peta, `portals` = satu baris per portal,
# `paint` = satu baris per zona. Selebihnya memakai indentasi JSON biasa.
_RINGKAS = ('tiles', 'portals', 'paint')


def teks_scene(data: dict) -> str:
    """JSON scene dengan bentuk yang bisa dibaca manusia.

    `json.dumps(indent=2)` menaruh tiap ANGKA di barisnya sendiri: `farm` jadi
    731 baris dan bentuk petanya tidak terlihat sama sekali -- padahal justru
    itu keunggulan berkas ini dibanding kode. Di sini `tiles`, `portals`, dan
    `paint` ditulis satu baris per elemen, sehingga ladang, kandang, kolam, dan
    jalan utama terbaca langsung dari berkasnya. `farm` turun ke 63 baris dan
    seluruh dunia dari 72 KB ke 27 KB.

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


def tulis_scene(scene: Scene, path) -> None:
    """Tulis scene ke berkas dalam bentuk teks baku."""
    Path(path).write_text(teks_scene(scene.to_dict()), encoding='utf-8')


def baca_scene(path) -> Scene:
    """Baca scene dari berkas.

    `utf-8-sig` menerima berkas dengan maupun tanpa BOM. Notepad Windows
    menuliskan BOM, dan tanpa ini berkas yang disunting dengan Notepad akan
    ditolak -- scenenya kembali ke kode dan perubahan penyuntingnya diam-diam
    tidak berpengaruh.
    """
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    return Scene.from_dict(data)
