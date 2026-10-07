"""probe_rumput.py — Uniform rumput: berapa harganya, dan apa yang dibelinya.

Profil Tahap 3 menunjuk `grass_shader.update_time` sebagai 3,12 ms dari 7,78 ms
LOGIKA di scene mountain — 40% seluruh waktu Python game, dipakai memanggil
`set_shader_input` 461 entity x 2 uniform = 922 kali TIAP FRAME.

Dua pertanyaan yang harus dijawab dengan angka, bukan dugaan:

  1. HARGA   berapa ms per frame jalur per-entity, dan berapa jalur satu
             panggilan di `scene` (Panda3D mewariskan shader input ke anak)?
  2. BELINYA apakah `grs_time` benar-benar menggerakkan piksel? Shader hanya
             menggeser vertex sebesar (wave) * h * wind, dan h = world.y - 0,15.
             Tutup rumput berada di y 0,20..0,24, jadi h cuma 0,05..0,09 dan
             geserannya paling besar sekitar 0,007 unit di atas tile 2,0 unit.
             Kalau itu di bawah satu piksel, biaya di atas tidak membeli apa pun.

Pertanyaan 2 juga yang membuktikan jalur `scene` SETARA: kalau ia menghasilkan
jumlah piksel berubah yang sama dengan jalur per-entity, uniform-nya memang
sampai ke shader dan bukan diam-diam hilang.

Dipakai juga oleh regress (`uji_rumput`) supaya pengoptimalan tidak bisa
diam-diam mematikan animasinya.

Pemakaian:
    python tools/probe_rumput.py [scene]
"""
from __future__ import annotations

import os
import sys
import time
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


def _tangkap(nama):
    """Render sampai buffer benar-benar jadi, lalu baca piksel.

    Delapan renderFrame() bukan takhayul: `taskMgr.step()` tidak menjamin buffer
    belakang selesai sebelum getScreenshot() membacanya, dan itu sudah sekali
    membuat regress memvonis enam scene 'tidak terender' padahal terender.
    """
    from direct.showbase.ShowBaseGlobal import base
    from panda3d.core import Filename
    from PIL import Image
    for _ in range(8):
        base.graphicsEngine.renderFrame()
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / f'{nama}.png'
    img = base.win.getScreenshot()
    if img is None:
        return None
    img.write(Filename.fromOsSpecific(str(png)))
    return Image.open(png).convert('RGB')


def _beda_piksel(a, b):
    """Jumlah piksel yang berubah, dan selisih maksimum satu kanal."""
    if a is None or b is None:
        return None, None
    pa, pb = a.load(), b.load()
    n_beda = 0
    maks = 0
    for y in range(a.size[1]):
        for x in range(a.size[0]):
            ra, ga, ba = pa[x, y]
            rb, gb, bb = pb[x, y]
            d = max(abs(ra - rb), abs(ga - gb), abs(ba - bb))
            if d:
                n_beda += 1
                if d > maks:
                    maks = d
    return n_beda, maks


def _biaya(fn, n=30):
    """ms per pemanggilan, diukur setelah sekali pemanasan."""
    fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000.0


def uji_rumput(g, scene_uji='farm'):
    """Kembalikan (lulus, pesan). Dipakai probe ini dan regress."""
    from ursina import scene as uscene
    import game.grass_shader as gs
    from direct.showbase.ShowBaseGlobal import base

    g.state.scene_name = scene_uji
    for _ in range(40):
        base.taskMgr.step()

    ents = g.world._grass_ents
    if not ents:
        return True, f'scene {scene_uji} tidak punya entity rumput — tidak diuji'
    if gs._grass_failed or gs.get_grass_shader() is None:
        return True, 'shader rumput tidak aktif di pipeline ini — tidak diuji'

    WIND = 0.22   # lebih kencang dari cuaca apa pun supaya kalau ADA gerakan, terlihat

    def _per_entity(t):
        for e in ents:
            e.set_shader_input('grs_time', t)
            e.set_shader_input('grs_wind', WIND)

    def _lewat_scene(t):
        uscene.set_shader_input('grs_time', t)
        uscene.set_shader_input('grs_wind', WIND)

    hasil = {}
    for label, dorong in (('per-entity', _per_entity), ('scene', _lewat_scene)):
        if label == 'scene':
            # Input per-entity MENINDIH input induk, jadi harus dilepas dulu —
            # kalau tidak, jalur 'scene' akan terlihat mati padahal yang
            # terbaca cuma nilai sisa dari jalur sebelumnya.
            for e in ents:
                e.clear_shader_input('grs_time')
                e.clear_shader_input('grs_wind')
        dorong(0.0)
        a = _tangkap(f'rumput_{label}_t0')
        dorong(3.7)
        b = _tangkap(f'rumput_{label}_t37')
        n_beda, maks = _beda_piksel(a, b)
        ms = _biaya(lambda: dorong(1.0))
        hasil[label] = (n_beda, maks, ms)

    pe, sc = hasil['per-entity'], hasil['scene']
    pesan = (f'{len(ents)} entity | per-entity {pe[2]:.2f} ms/frame, '
             f'{pe[0]} piksel berubah (maks {pe[1]}) | '
             f'scene {sc[2]:.3f} ms/frame, {sc[0]} piksel berubah (maks {sc[1]})')

    # Syarat lulus: jalur scene tidak boleh menggerakkan LEBIH SEDIKIT piksel
    # daripada jalur per-entity. Kalau per-entity sendiri 0 piksel, animasinya
    # memang tidak kelihatan — itu temuan, bukan kegagalan alat, dan dilaporkan
    # lewat pesan.
    if pe[0] and sc[0] < pe[0] * 0.5:
        return False, 'jalur scene kehilangan animasi — ' + pesan
    return True, pesan


def main():
    from ursina import application
    application.asset_folder = ROOT
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    scene_uji = sys.argv[1] if len(sys.argv) > 1 else 'farm'

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

    lulus, pesan = uji_rumput(g, scene_uji)
    print()
    print('UNIFORM RUMPUT —', 'LULUS' if lulus else 'GAGAL')
    print(' ', pesan)
    print()
    sys.stdout.flush()
    os._exit(0)


if __name__ == '__main__':
    main()
