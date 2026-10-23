"""probe_tombol_f.py — apa yang SEBENARNYA terjadi saat pemain menekan F5/F6/F7/F9.

Game ini memakai F5 = simpan, F9 = muat, F6 = Papan Permintaan Warga
(game/app.py, cabang `elif key == 'f5'` dst.). Ursina 8.3 punya pendengarnya
sendiri untuk tombol yang sama: HotReloader (ursina/prefabs/hot_reloader.py)
memetakan f5 -> reload_code, f6 -> reload_textures, f7 -> reload_models,
f8 -> reload_shaders, f9 -> toggle_hotreloading. HotReloader hanya hidup kalau
`application.development_mode` benar, dan Ursina menyalakannya otomatis
kecuali folder induk aset punya `src` DAN `python` (ursina/application.py).
Tata letak repo ini tidak punya keduanya.

Probe lama memanggil `Game3D.input()` langsung, jadi tidak pernah melihat
HotReloader: ia duduk di lapisan dispatcher Ursina (`app.input`) yang
membagikan tombol ke SEMUA entity, dan HotReloader dibuat sebelum GameHandler.
Aturan #2 CLAUDE.md: probe harus menempuh jalur asli.

Jadi probe ini menjalankan `main.py` sendiri (runpy, `__main__` asli, sehingga
HotReloader menunjuk main.py persis seperti `python main.py`), hanya mengganti
`Game3D.run` — loop tak berujung — dengan pengemudi yang menekan tombol lewat
`app.input`. Satu tombol per proses, karena F5 bisa merusak scene.

    xvfb-run -a -s "-screen 0 1024x768x24" python _bench/probes/probe_tombol_f.py f5
    (tombol: f3 f5 f6 f7 f9; keluaran: satu baris JSON 'HASIL {...}')

Save ditulis di direktori sementara (cwd), bukan di akar repo. Tekstur repo
yang ditimpa reload_code dihitung lalu dipulihkan dari salinan.
"""
from __future__ import annotations

import json
import os
import runpy
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOMBOL = sys.argv[1] if len(sys.argv) > 1 else 'f5'

# argv[0] menentukan asset_folder dan development_mode Ursina SAAT IMPOR, jadi
# disetel sebelum apa pun mengimpor ursina -- sama dengan `python main.py`.
sys.argv = [str(ROOT / 'main.py')]
sys.path.insert(0, str(ROOT))
_KERJA = tempfile.mkdtemp(prefix='probe_tombol_f_')
os.chdir(_KERJA)                      # SAVE_FILE relatif -> jatuh di sini

from panda3d.core import loadPrcFileData  # noqa: E402
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

hasil: dict = {'tombol': TOMBOL}
_n_game = [0]


def _langkah(n=1):
    from direct.showbase.ShowBaseGlobal import base
    for _ in range(n):
        base.taskMgr.step()


def _tekan(app, key):
    from ursina.main import keyboard_keys
    app.input(key, key in keyboard_keys)


def _ke_hud(g):
    """Chargen -> Enter -> sinema dilewati dengan SPACE (bukan ESC)."""
    if g.panels.mode == 'chargen':
        _tekan(g.app, 'enter')
        _langkah(5)
    t0 = time.time()
    while time.time() - t0 < 120:
        _langkah(1)
        if g.panels.mode == 'sinema' or g.sinema.aktif:
            if g.sinema._menunggu:
                _tekan(g.app, 'space')
            continue
        if g.panels.mode == 'hud' and not g.sinema.aktif:
            _langkah(3)
            if g.panels.mode == 'hud' and not g.sinema.aktif:
                return True
    return False


def _pengemudi(self):
    from ursina import application, scene, window
    from game.state import GameState
    if _n_game[0] > 1:
        # reload_code meng-exec main.py lagi -> Game3D kedua -> run() kedua.
        # Loop asli akan bersarang di dalam penangan tombol; di sini cukup
        # dicatat lalu dikembalikan.
        hasil['run_bersarang'] = True
        return
    g = self
    hasil['development_mode'] = bool(application.development_mode)
    hr = getattr(application, 'hot_reloader', None)
    # Di `python main.py` HotReloader menunjuk main.py (`__main__.__file__`
    # saat Ursina dibuat). Di bawah runpy, `__main__` yang dilihat ursina
    # adalah probe ini, jadi jalurnya disamakan dengan permainan asli.
    if hr is not None:
        hr.path = ROOT / 'main.py'
    hasil['hot_reloader_aktif'] = bool(hr is not None and hr.enabled)
    hasil['hot_reloader_path'] = str(getattr(hr, 'path', ''))
    # `window.fullscreen` Ursina hanya membaca `_fullscreen` (bawaan True bila
    # belum pernah disetel), jadi yang dibaca properti jendela Panda3D.
    from direct.showbase.ShowBaseGlobal import base
    _wp = base.win.getProperties()
    hasil['jendela_fullscreen'] = bool(_wp.getFullscreen())
    hasil['jendela_px'] = [_wp.getXSize(), _wp.getYSize()]
    hasil['ke_hud'] = _ke_hud(g)
    hasil['sinema_aktif'] = bool(g.sinema.aktif)
    def _overlay():
        return sorted(
            n for n in ('exit_button', 'fps_counter', 'entity_counter',
                        'collider_counter', 'cog_button')
            if getattr(window, n, None) is not None
            and getattr(window, n).enabled
            and not getattr(window, n).has_disabled_ancestor())
    hasil['overlay_debug_tampak'] = _overlay()
    # Siapa saja yang menerima tombol di dispatcher Ursina, urut seperti
    # `app.input` membagikannya.
    hasil['pendengar'] = [
        type(e).__name__ if type(e).__name__ != 'Entity' else (e.name or 'Entity')
        for e in scene.entities
        if callable(getattr(e, 'input', None)) and e.enabled
        and not e.ignore and not e.ignore_input and not e.has_disabled_ancestor()]
    save = Path(GameState.slot_path(0)).resolve()
    hasil['save_di'] = str(save)

    if TOMBOL == 'f9':
        # Siapkan save yang berbeda dari keadaan sekarang, lalu muat.
        g.state.gold = 4321
        g.state.save()
        g.state.gold = 7
    else:
        save.unlink(missing_ok=True)

    # reload_code meng-exec main.py dengan `__file__` milik hot_reloader.py,
    # sehingga main.py tidak menemukan assets/ dan menjalankan make_assets --
    # yang MENULIS ULANG assets/textures/*.png milik repo. Disalin dulu supaya
    # probe bisa menghitung kerusakannya lalu memulihkannya.
    tekstur = ROOT / 'assets' / 'textures'
    salinan = {f: f.read_bytes() for f in tekstur.glob('*.png')}

    ukuran0 = tuple(window.size)
    n0 = len(scene.entities)
    pemain0 = g.player is not None and not g.player.is_empty()
    t0 = time.time()
    try:
        _tekan(g.app, TOMBOL)
        _langkah(5)
        hasil['exception'] = None
    except BaseException as ex:          # SystemExit juga dicatat
        hasil['exception'] = f'{type(ex).__name__}: {ex}'
    hasil['detik'] = round(time.time() - t0, 2)
    hasil['game3d_dibuat'] = _n_game[0]
    hasil['entity'] = [n0, len(scene.entities)]
    hasil['pemain_utuh'] = [pemain0, bool(g.player is not None and not g.player.is_empty())]
    hasil['ukuran_jendela'] = [list(ukuran0), list(window.size)]
    _wp = base.win.getProperties()
    hasil['jendela_px_sesudah'] = [_wp.getXSize(), _wp.getYSize()]
    hasil['overlay_sesudah'] = _overlay()
    hasil['hotreload_menyala'] = bool(getattr(hr, 'hotreload', False))
    hasil['flash'] = getattr(g.panels._flash_ent, 'text', None)
    hasil['mode'] = g.panels.mode
    hasil['panel'] = g.panels._panel_name
    hasil['save_ada'] = save.exists()
    hasil['gold'] = g.state.gold
    save.unlink(missing_ok=True)
    berubah = [f for f, isi in salinan.items()
               if not f.exists() or f.read_bytes() != isi]
    hasil['tekstur_repo_ditimpa'] = len(berubah)
    for f in berubah:
        f.write_bytes(salinan[f])


def main():
    import game.app as ga
    asli_init = ga.Game3D.__init__

    def _init(self, *a, **kw):
        _n_game[0] += 1
        asli_init(self, *a, **kw)
    ga.Game3D.__init__ = _init
    ga.Game3D.run = _pengemudi
    try:
        runpy.run_path(str(ROOT / 'main.py'), run_name='__main__')
    except BaseException as ex:
        import traceback
        traceback.print_exc()
        hasil.setdefault('exception_luar', f'{type(ex).__name__}: {ex}')
    import shutil
    shutil.rmtree(_KERJA, ignore_errors=True)
    print('HASIL ' + json.dumps(hasil, ensure_ascii=False))
    sys.stdout.flush()
    os._exit(0)


if __name__ == '__main__':
    main()
