"""profil.py — Ke mana milidetiknya pergi. Tahap 3 dimulai dengan mengukur.

docs/TAHAPAN.md Tahap 3 menulis "4-29 FPS, BELUM PERNAH DIPROFIL" lalu
"mulai dari optimasi bertahap SAMBIL MENGUKUR". Alat ini bagian "mengukur"-nya,
dan sengaja dibuat sebelum satu baris pun dioptimalkan.

Yang dipisahkan, karena dua angka ini punya nilai yang sangat berbeda:

  LOGIKA   waktu di dalam Game3D.update — kode Python milik game sendiri.
  URSINA   Python di luar update: loop per-entity Ursina, properti, culling
           bawaan. Bukan milik proyek ini, tapi harganya ditentukan oleh
           proyek ini — jumlah entity dan collider.
  GAMBAR   waktu di dalam GraphicsEngine.renderFrame(). HANYA kolom inilah
           yang dikerjakan llvmpipe secara perangkat lunak di kontainer tanpa
           GPU, jadi hanya kolom ini yang tidak boleh dipakai menyimpulkan
           apa pun tentang mesin pemilik.

Dua kolom pertama SAHIH di mana pun dijalankan: Python tidak jadi lebih cepat
karena ada GPU.

Versi pertama alat ini cuma punya LOGIKA dan SISANYA, dan itu menyesatkan:
SISANYA ikut menampung ~14 ms Python milik Ursina (has_disabled_ancestor 777
panggilan/frame, enabled_getter 5.669/frame, collider_getter 2.490/frame di
scene mountain) di bawah label "abaikan, itu llvmpipe". Padahal itu CPU murni
dan berlaku di mesin mana pun. Yang boleh diabaikan cuma renderFrame.

Daftar fungsi dibatasi ke paket `game/` karena yang bisa diubah cuma itu;
tumpukan Panda3D di bawahnya bukan milik proyek ini.

Pemakaian:
    python tools/profil.py                 scene farm, 60 frame
    python tools/profil.py town 120        scene lain, jumlah frame lain

Tidak pernah keluar dengan kode gagal: ini alat ukur, bukan penguji.
"""
from __future__ import annotations

import cProfile
import io
import os
import pstats
import sys
import time
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

W, H = 640, 360
WARM = 40


def main():
    from ursina import application
    application.asset_folder = ROOT
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    arg = [a for a in sys.argv[1:] if not a.startswith('-')]
    scene = arg[0] if arg else 'farm'
    n_frame = int(arg[1]) if len(arg) > 1 else 60

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
    from ursina import scene as uscene

    if g.panels.mode != 'hud':
        if getattr(g, '_chargen', None):
            g._chargen.destroy_all()
            g._chargen = None
        g.panels.mode = 'hud'

    g.state.scene_name = scene
    for _ in range(WARM):
        base.taskMgr.step()

    # Bungkus update supaya waktu logika terukur terpisah dari waktu gambar.
    asli = g.update
    catatan = {'detik': 0.0, 'panggil': 0}

    def terukur(dt):
        t0 = time.perf_counter()
        try:
            return asli(dt)
        finally:
            catatan['detik'] += time.perf_counter() - t0
            catatan['panggil'] += 1

    g.update = terukur

    prof = cProfile.Profile()
    t_mulai = time.perf_counter()
    prof.enable()
    for _ in range(n_frame):
        base.taskMgr.step()
    prof.disable()
    total = time.perf_counter() - t_mulai

    n_ent = len(uscene.children)
    ms_frame = total / n_frame * 1000.0
    ms_logika = catatan['detik'] / max(1, catatan['panggil']) * 1000.0

    # Waktu gambar diambil dari tottime renderFrame itu sendiri, bukan dari
    # "frame dikurangi logika". Selisih itu masih berisi Python milik Ursina.
    det_gambar = 0.0
    for (_f, _l, fungsi), (_cc, _nc, tt, _ct, _cal) in pstats.Stats(prof).stats.items():
        if 'renderFrame' in fungsi:
            det_gambar += tt
    ms_gambar = det_gambar / n_frame * 1000.0
    ms_ursina = max(0.0, ms_frame - ms_logika - ms_gambar)

    print()
    print(f'scene {scene} — {n_frame} frame, {n_ent} entity, layar {W}x{H}')
    print('-' * 72)
    print(f'  per frame         {ms_frame:8.2f} ms   ({1000.0/ms_frame:.1f} FPS)')
    print(f'  LOGIKA (game/)    {ms_logika:8.2f} ms   {ms_logika/ms_frame:5.1%}  <- CPU, sahih di mana pun')
    print(f'  URSINA (per-ent)  {ms_ursina:8.2f} ms   {ms_ursina/ms_frame:5.1%}  <- CPU, sahih di mana pun')
    print(f'  GAMBAR (llvmpipe) {ms_gambar:8.2f} ms   {ms_gambar/ms_frame:5.1%}  <- bukan patokan')
    print('-' * 72)
    print(f'  CPU total         {ms_logika + ms_ursina:8.2f} ms   '
          f'<- ini yang tersisa kalau GPU-nya seketika')
    print('-' * 72)

    def _tabel(kunci, judul, saring, batas=18, ambang=0.0005):
        """Cetak satu tabel pstats yang sudah disaring.

        `kunci` 'tottime' menjawab "fungsi ini sendiri mahal", `cumtime`
        menjawab "cabang di bawah fungsi ini mahal". Keduanya perlu: tabel
        tottime game/ pada scene mountain hanya menjumlah 0,8 ms dari 7,4 ms
        LOGIKA, karena sisanya dihabiskan di setter Ursina/Panda3D yang
        DIPANGGIL kode game, bukan di kode game itu sendiri. Tanpa tabel
        cumtime, angka itu tidak kelihatan dan salah dibaca sebagai
        "logika sudah murah".
        """
        buf = io.StringIO()
        st = pstats.Stats(prof, stream=buf)
        st.sort_stats(kunci)
        st.print_stats(400)
        print()
        print(judul)
        print(f'{kunci:>9s} {"per frame":>10s} {"panggilan":>10s}  fungsi')
        print('-' * 86)
        n = 0
        for b in buf.getvalue().splitlines():
            kolom = b.split(None, 5)
            if len(kolom) < 6:
                continue
            try:
                ncalls = kolom[0].split('/')[0]
                nilai = float(kolom[1] if kunci == 'tottime' else kolom[3])
            except (ValueError, IndexError):
                continue
            nama = kolom[5]
            if not saring(nama):
                continue
            if nilai <= ambang:
                continue
            pendek = nama
            for tanda in ('/game/', '\\game\\'):
                if tanda in pendek:
                    pendek = pendek[pendek.index(tanda) + 1:]
                    break
            else:
                pendek = pendek.rsplit('/', 1)[-1]
            print(f'{nilai:9.3f} {nilai/n_frame*1000:9.2f}ms {ncalls:>10s}  {pendek[:52]}')
            n += 1
            if n >= batas:
                break
        if n == 0:
            print('  (tidak ada yang di atas ambang)')
        print('-' * 86)

    def _milik_game(nama):
        return '/game/' in nama or '\\game\\' in nama

    def _bukan_game(nama):
        return not _milik_game(nama) and '~' not in nama.split(':')[0]

    _tabel('tottime', 'A. game/ — waktu DI FUNGSI ITU SENDIRI (apa yang mahal untuk ditulis ulang):',
           _milik_game)
    _tabel('cumtime', 'B. game/ — waktu DI FUNGSI ITU BESERTA SEMUA YANG DIPANGGILNYA:',
           _milik_game)
    _tabel('tottime', 'C. di luar game/ — ke mana panggilan game/ bermuara (setter Ursina, Panda3D):',
           _bukan_game)
    print('Kolom "per frame" itu milidetik per frame.')
    print('A mahal  -> tulis ulang fungsinya.')
    print('B mahal tapi A murah -> yang mahal ada di tabel C: kurangi PANGGILANNYA.')
    print('C berisi gambar/culling llvmpipe juga, jadi baca lewat kolom panggilan.')

    sys.stdout.flush()
    os._exit(0)


if __name__ == '__main__':
    main()
