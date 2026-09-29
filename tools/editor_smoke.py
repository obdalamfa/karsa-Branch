"""editor_smoke.py — Buktikan editor bisa dibangun dan panel peta Karsa hidup.

Editor memanggil `Ursina()` sendiri, dan itu singleton: ia tidak bisa
di-instansiasi di dalam `gauntlet/check.py` yang sudah punya satu. Karena itu
pemeriksaannya berdiri sebagai proses terpisah.

Dijalankan offscreen, jadi tidak butuh layar dan tidak akan muncul di muka.

Yang diperiksa adalah hal-hal yang bisa dibuktikan tanpa mata: editor terbangun,
panelnya ada dan tersembunyi saat lahir, kelima belas scene terdaftar, sebuah
scene bisa dibuka dengan jumlah entity yang benar, dan klik pada ubin benar-benar
mengubah grid. Apakah panelnya enak dipakai tidak bisa dijawab dari sini.

Pemeriksaan ini SENGAJA tidak menyimpan apa pun: menyimpan berarti menulis
`game/scenes/<nama>.json`, dan harness tidak boleh menyentuh scene asli.

    python tools/editor_smoke.py
Keluar dengan kode 1 kalau ada yang gagal.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from panda3d.core import loadPrcFileData            # noqa: E402
loadPrcFileData('', 'window-type offscreen\naudio-library-name null')

from ursina_editor.main import UrsinaEditorApp      # noqa: E402


def main() -> int:
    gagal = []

    def cek(nama, syarat, info=''):
        if syarat:
            print(f'  LULUS  {nama}')
        else:
            print(f'  GAGAL  {nama}  {info}')
            gagal.append(nama)

    app = UrsinaEditorApp(headless=True)

    panel = getattr(app, 'karsa_panel', None)
    cek('editor terbangun', True)
    cek('panel Karsa ada', panel is not None)
    if panel is None:
        return 1

    cek('panel tersembunyi saat lahir', not panel.root.enabled)
    cek('panel bisa dinyalakan', panel.toggle() is True)

    daftar = panel.sesi.daftar()
    cek('15 scene game terdaftar', len(daftar) == 15, f'dapat {len(daftar)}')

    ringkas = panel.sesi.buka('farm')
    lapis = panel.sesi.layer
    cek('farm terbuka', ringkas['ukuran'] == (28, 20), str(ringkas['ukuran']))
    cek('satu entity per ubin',
        lapis.jumlah_entity() == 28 * 20, f"dapat {lapis.jumlah_entity()}")
    cek('zona terbaca', ringkas['zona'] == 4, str(ringkas['zona']))
    cek('portal terbaca', ringkas['portal'] == 4, str(ringkas['portal']))
    cek('sumber dari berkas data', panel.sesi.sumber == 'data',
        str(panel.sesi.sumber))

    from ursina_editor.karsa_tiles import palet
    cek('palet mencakup 51 ubin', len(palet()) == 51, str(len(palet())))

    # Klik pada sesuatu yang bukan ubin harus ditolak, bukan crash.
    cek('klik bukan-ubin ditolak', panel.sesi.klik(object()) is False)

    # Klik pada ubin harus mengubah grid lewat jalur yang sama dengan UI.
    import time
    from game.config import G
    x, y = 10, 10
    lama = panel.sesi.scene.tiles[y][x]
    panel.sesi.pilih_ubin(G if lama != G else 0)
    ent = lapis.ubin[(x, y)]
    sebelum = lapis.ubin[(x, y)]
    cek('klik ubin diterima', panel.sesi.klik(ent) is True)
    cek('grid berubah', panel.sesi.scene.tiles[y][x] == panel.sesi.tid_aktif != lama)
    cek('viewport dibangun ulang', lapis.ubin[(x, y)] is not sebelum)
    cek('sesi ditandai kotor', panel.sesi.kotor is True)

    # ─── Objek terpasang ────────────────────────────────────────────────────
    # Inilah yang membuat gizmo editor berguna untuk game: benda yang berdiri
    # di posisi bebas, bukan menempati sel.
    lapis_obj = panel.sesi.layer_objek
    n0 = lapis_obj.jumlah()
    ent = panel.sesi.tambah_objek('peti')
    cek('objek bisa ditambah', ent is not None and lapis_obj.jumlah() == n0 + 1,
        f'{n0} -> {lapis_obj.jumlah()}')
    cek('objek baru langsung terpilih', panel.sesi.klik_objek(ent) is True)
    ent.x += 2.0
    ent.rotation_y = 90.0
    cek('geser objek tersinkron', panel.sesi.sinkron_objek(ent) is True)
    idx = lapis_obj.index_dari(ent)
    cek('rotasi ikut tertulis',
        panel.sesi.scene.objects[idx]['rot_y'] == 90.0,
        str(panel.sesi.scene.objects[idx]))
    cek('hapus objek', panel.sesi.hapus_objek(ent) is True
        and lapis_obj.jumlah() == n0, f'{lapis_obj.jumlah()} vs {n0}')

    # Scene asli tidak boleh tersentuh sama sekali.
    import game.scenes as _gs
    cek('scene asli tidak ditulis', not (_gs._DIR / 'farm.json').stat().st_mtime
        > time.time() - 1, 'farm.json baru saja berubah')

    print(f'\n{len(gagal)} gagal' if gagal else '\nsemua lulus')
    return 1 if gagal else 0


if __name__ == '__main__':
    sys.exit(main())
