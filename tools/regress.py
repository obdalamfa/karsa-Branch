"""regress.py — Jaring pengaman: buktikan game masih utuh setelah diubah.

Dipakai setiap kali ada perubahan, terutama saat banyak orang/agen menulis ke
pohon kerja yang sama. Verifikasi manual sudah gagal dua kali di proyek ini
(WASD dinyatakan beres padahal belum; metode disisipkan di tengah fungsi
sehingga fungsi induknya mati total) — keduanya ketahuan cuma karena kebetulan
diuji ulang.

Setiap pemeriksaan di sini terikat pada kegagalan NYATA yang pernah terjadi,
bukan pada kemungkinan yang dikarang:

  geom_nol       bug NodePath-bersama. Mesh Ursina adalah NodePath Panda3D dan
                 hanya boleh punya SATU parent; mesh cache yang diberikan ke
                 banyak Entity membuat semua kecuali yang TERAKHIR kehilangan
                 geometri. Terjadi DUA KALI: di meshes.py dan di entities.py.
  frame_kosong   "rumah ga muncul" — scene yang dirender jadi langit polos.
  pemain_valid   terjepit permanen di tile yang tidak bisa dijalani.
  motif_waras    mesin motif baru; nilai harus tetap di -100..+100.
  save_bolak     format save berubah; save lama tidak boleh merusak loader.
  ms_frame       4-29 FPS dan belum pernah diprofil. Dicatat sebagai angka
                 supaya regresi performa terlihat, bukan cuma terasa.

Pemakaian:
    python tools/regress.py                 semua scene
    python tools/regress.py farm house      scene tertentu

Keluar dengan kode 1 kalau ada yang GAGAL, supaya bisa dipakai di skrip.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData, Filename  # noqa: E402
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'aux-display pandadx9')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

import logging  # noqa: E402
logging.basicConfig(level=logging.ERROR)

OUT = ROOT / '_bench' / 'regress'
OUT.mkdir(parents=True, exist_ok=True)

W, H = 640, 360
WARM = 30          # frame pemanasan setelah ganti scene
MEASURE = 12       # frame yang diukur waktunya


def _fail(msg):
    return (False, msg)


def _ok(msg=''):
    return (True, msg)


# ─── PEMERIKSAAN ─────────────────────────────────────────

def cek_geom_nol(scene_mod):
    """Entity yang punya model tapi nol GeomNode = korban NodePath-bersama."""
    from ursina import scene as uscene
    korban = []
    for e in uscene.children:
        m = getattr(e, 'model', None)
        if m is None:
            continue
        try:
            n = len(m.findAllMatches('**/+GeomNode'))
        except Exception:
            continue
        if n == 0:
            nama = getattr(e, 'name', None) or type(e).__name__
            korban.append(nama)
    if korban:
        from collections import Counter
        ring = ', '.join(f'{k}x{v}' for k, v in Counter(korban).most_common(4))
        return _fail(f'{len(korban)} entity tanpa geometri ({ring})')
    return _ok()


def cek_frame_kosong(png: Path):
    """Frame yang nyaris satu warna = scene tidak benar-benar dirender."""
    try:
        from PIL import Image
        im = Image.open(png).convert('RGB').resize((80, 45))
    except Exception as e:
        return _fail(f'gagal baca png: {e}')
    px = list(im.getdata())
    unik = len(set(px))
    dominan = max(px.count(c) for c in set(px)) / len(px)
    if unik < 12 or dominan > 0.93:
        return _fail(f'frame nyaris polos (warna unik {unik}, dominan {dominan:.0%})')
    return _ok(f'{unik} warna')


def cek_bisa_keluar(g):
    """ESC harus mengembalikan mode panel apa pun ke 'hud'.

    player.tick() hanya dipanggil saat mode == 'hud', jadi mode yang macet
    membekukan pemain sepenuhnya — tidak jalan, waktu berhenti, motif berhenti.
    Pernah terjadi: ESC tidak berfungsi di mode 'dialog', dan pie menu objek
    tidak punya jalan keluar selain memilih. Pemilik melaporkannya sebagai
    "jalan saja tidak bisa".
    """
    asal = g.panels.mode
    macet = []
    for mode in ('dialog', 'panel', 'pie'):
        g.panels.mode = mode
        try:
            g.input('escape')
        except Exception as e:
            macet.append(f'{mode} (ESC error: {type(e).__name__})')
            continue
        if g.panels.mode != 'hud':
            macet.append(f'{mode} -> {g.panels.mode}')
    g.panels.mode = asal if asal in ('hud',) else 'hud'
    if macet:
        return _fail('terkunci: ' + ', '.join(macet))
    return _ok()


def cek_pemain_valid(g):
    tx, ty = g.player.get_tile_pos()
    if not g.world.is_walkable(tx, ty):
        return _fail(f'pemain di tile tak-walkable ({tx},{ty})')
    sc = g.world.scene_obj
    grid = getattr(sc, 'tiles', None)
    if grid:
        rows, cols = len(grid), len(grid[0])
        if not (0 <= tx < cols and 0 <= ty < rows):
            return _fail(f'pemain di luar peta ({tx},{ty}) peta {cols}x{rows}')
    return _ok(f'({tx},{ty})')


def cek_motif_waras(g):
    from game.motives import MOTIVES, MOTIVE_MIN, MOTIVE_MAX
    mv = g.state.mv
    for m in MOTIVES:
        v = mv.get(m)
        if not (MOTIVE_MIN - 0.01 <= v <= MOTIVE_MAX + 0.01):
            return _fail(f'motif {m}={v:.1f} di luar rentang')
    mood = mv.mood
    if mood != mood or abs(mood) > 1e6:
        return _fail(f'mood tidak terhingga: {mood}')
    sebelum = mv.get('lapar')
    mv.tick(240.0)
    if mv.get('lapar') >= sebelum:
        return _fail('lapar tidak turun setelah 4 jam-sim')
    return _ok(f'mood {mood:+.1f}')


def cek_save_bolak(g):
    from game.state import GameState
    try:
        g.state.sync_motives()
        blob = json.dumps({k: v for k, v in g.state.__dict__.items()
                           if not k.startswith('_')})
    except Exception as e:
        return _fail(f'state tidak bisa di-JSON: {e}')
    try:
        data = json.loads(blob)
        gs = GameState()
        for k, v in data.items():
            if hasattr(gs, k):
                setattr(gs, k, v)
        asli, ulang = g.state.mv.get('lapar'), gs.mv.get('lapar')
    except Exception as e:
        return _fail(f'muat balik gagal: {e}')
    if abs(asli - ulang) > 0.01:
        return _fail(f'motif berubah saat bolak-balik ({asli:.2f} -> {ulang:.2f})')
    return _ok(f'{len(blob)}B')


# ─── PENGGERAK ───────────────────────────────────────────

def main():
    from ursina import application
    application.asset_folder = ROOT
    application.fonts_folder = ROOT / 'fonts'
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = W, H

    from game.scenes import SCENES
    minta = [a for a in sys.argv[1:] if not a.startswith('-')]
    scenes = minta or [s for s in SCENES if s != 'dungeon']

    from game.app import Game3D
    t0 = time.time()
    try:
        g = Game3D()
    except Exception:
        print('GAGAL TOTAL: game tidak bisa dibangun\n')
        traceback.print_exc()
        sys.exit(1)
    from direct.showbase.ShowBaseGlobal import base
    for _ in range(20):
        base.taskMgr.step()
    boot_s = time.time() - t0

    from ursina import scene as uscene
    baris = []
    gagal_total = 0

    for nama in scenes:
        hasil = {}
        try:
            g.state.scene_name = nama
            for _ in range(WARM):
                base.taskMgr.step()

            tm = time.time()
            for _ in range(MEASURE):
                base.taskMgr.step()
            ms = (time.time() - tm) / MEASURE * 1000.0

            png = OUT / f'{nama}.png'
            img = base.win.getScreenshot()
            if img is not None:
                img.write(Filename.fromOsSpecific(str(png)))

            hasil['geom_nol'] = cek_geom_nol(nama)
            hasil['frame_kosong'] = cek_frame_kosong(png) if png.exists() \
                else _fail('tidak ada tangkapan layar')
            hasil['pemain_valid'] = cek_pemain_valid(g)
            hasil['bisa_keluar'] = cek_bisa_keluar(g)
            hasil['motif_waras'] = cek_motif_waras(g)
            hasil['save_bolak'] = cek_save_bolak(g)
            n_ent = len(uscene.children)
        except Exception as e:
            hasil['boot'] = _fail(f'{type(e).__name__}: {e}')
            ms, n_ent = float('nan'), 0
            traceback.print_exc()

        buruk = [k for k, (ok, _) in hasil.items() if not ok]
        gagal_total += len(buruk)
        baris.append((nama, hasil, ms, n_ent, buruk))

    # ── laporan ──
    print()
    print(f'{"scene":14s} {"hasil":>7s} {"ms/frame":>9s} {"entity":>7s}  catatan')
    print('-' * 78)
    for nama, hasil, ms, n_ent, buruk in baris:
        tanda = 'LULUS' if not buruk else 'GAGAL'
        catatan = '; '.join(f'{k}: {hasil[k][1]}' for k in buruk) if buruk else \
                  hasil.get('pemain_valid', (True, ''))[1]
        print(f'{nama:14s} {tanda:>7s} {ms:9.1f} {n_ent:7d}  {catatan[:44]}')
    print('-' * 78)
    n_lulus = sum(1 for _, _, _, _, b in baris if not b)
    print(f'{n_lulus}/{len(baris)} scene lulus, {gagal_total} pemeriksaan gagal, '
          f'boot {boot_s:.1f}s')

    laporan = OUT / 'report.md'
    with open(laporan, 'w', encoding='utf-8') as f:
        f.write('# Laporan regresi\n\n')
        f.write(f'{n_lulus}/{len(baris)} scene lulus, {gagal_total} pemeriksaan gagal.\n\n')
        f.write('| scene | hasil | ms/frame | entity | catatan |\n|---|---|--:|--:|---|\n')
        for nama, hasil, ms, n_ent, buruk in baris:
            tanda = 'LULUS' if not buruk else '**GAGAL**'
            catatan = '; '.join(f'`{k}` {hasil[k][1]}' for k in buruk) or '-'
            f.write(f'| {nama} | {tanda} | {ms:.1f} | {n_ent} | {catatan} |\n')
    print(f'laporan: {laporan}')

    try:
        with open(ROOT / '_bench' / 'progress.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'slice': 'REGRESI', 'round': 0, 'role': 'note',
                'note': f'{n_lulus}/{len(baris)} scene lulus, '
                        f'{gagal_total} pemeriksaan gagal',
            }, ensure_ascii=False) + '\n')
    except Exception:
        pass

    sys.stdout.flush()
    os._exit(1 if gagal_total else 0)


if __name__ == '__main__':
    main()
