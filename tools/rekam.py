"""rekam.py — Rekam gameplay jadi klip pendek, untuk disandingkan dengan patokan.

Kenapa alat ini ada. Seluruh bench Lembah Karsa berupa delapan GAMBAR DIAM, dan
gambar diam tidak bisa menilai gerak. Apakah `gosok` terbaca sebagai menggosok
dan bukan sebagai mengayun kapak, apakah menaiki kuda terlihat seperti menaiki
kuda — dua-duanya pertanyaan tentang gerak, dan `bar_gate` sampai sekarang buta
terhadap keduanya. Tanpa rekaman dari sisi kita, potongan gerak di gauntlet
tidak punya apa pun untuk disandingkan, dan kritikus akan mengarang.

TIDAK ADA ffmpeg di lingkungan ini — diperiksa, bukan diasumsikan. Jadi
keluarannya WebP animasi, ditulis Pillow sendiri, dan bisa dibuka siapa pun
tanpa memasang apa-apa. GIF hanya ditulis kalau diminta `--gif`, setengah
lebar: diukur pada klip nyata, GIF lebar penuh 6.479 KiB lawan WebP 983 KiB
untuk isi yang persis sama.

Ia menjalankan game yang sebenarnya lewat jalur yang sama dengan `capture.py`
dan `main.py`, jadi rekamannya bukti, bukan mockup.

    python tools/rekam.py --out _bench/klip/gosok.webp --scene farm \\
        --anim gosok:900 --detik 1.6
    python tools/rekam.py --out _bench/klip/panen.webp --scene farm \\
        --anim bend --detik 1.2 --dist 7 --pitch 16

Catatan kecepatan: tidak ada GPU di container ini (Mesa llvmpipe), jadi
merekam 2 detik pada 20 fps berarti 40 frame yang tiap satunya butuh
puluhan milidetik. Itu wajar dan bukan tanda ada yang salah. Yang direkam
adalah ISI frame-nya, bukan seberapa cepat ia dihasilkan — `--fps` menentukan
kecepatan PEMUTARAN klipnya, bukan kecepatan perekamannya.
"""
from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData  # noqa: E402
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'window-type onscreen')
loadPrcFileData('', 'sync-video false')
loadPrcFileData('', 'audio-library-name null')

import logging  # noqa: E402
logging.basicConfig(level=logging.WARNING)


def _frame_pil(base):
    """Ambil isi framebuffer sebagai PIL.Image.

    Lewat RAM image, bukan menulis PNG lalu membacanya lagi: satu klip 2 detik
    berarti puluhan frame, dan bolak-balik ke disk tiap frame membuat perekaman
    berkali lipat lebih lambat tanpa menambah apa pun pada hasilnya.
    """
    from PIL import Image
    tex = base.win.getScreenshot()
    if tex is None:
        return None
    ram = tex.getRamImageAs('RGB')
    if not ram:
        return None
    im = Image.frombytes('RGB', (tex.getXSize(), tex.getYSize()),
                         bytes(ram.getData()))
    # Panda3D menaruh titik asal di KIRI-BAWAH, Pillow di kiri-atas.
    return im.transpose(Image.FLIP_TOP_BOTTOM)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', required=True,
                    help='berkas keluaran .webp animasi')
    ap.add_argument('--scene', default=None)
    ap.add_argument('--hour', type=float, default=None)
    ap.add_argument('--detik', type=float, default=1.6, help='panjang klip')
    ap.add_argument('--fps', type=int, default=20, help='fps PEMUTARAN klip')
    ap.add_argument('--warmup', type=int, default=60,
                    help='frame pemanasan sebelum perekaman dimulai')
    ap.add_argument('--anim', default=None,
                    help='mode animasi pemain, mis. gosok atau gosok:900')
    ap.add_argument('--keys', default='', help='daftar tombol, dipisah koma')
    ap.add_argument('--at', default=None, help='taruh pemain di x,y')
    ap.add_argument('--pitch', type=float, default=None)
    ap.add_argument('--yaw', type=float, default=None)
    ap.add_argument('--dist', type=float, default=None)
    ap.add_argument('--width', type=int, default=960)
    ap.add_argument('--height', type=int, default=540)
    ap.add_argument('--frames-dir', default=None,
                    help='kalau diisi, tiap frame ikut ditulis sebagai PNG')
    ap.add_argument('--gif', action='store_true',
                    help='tulis juga GIF setengah lebar (untuk penampil yang '
                         'menolak WebP animasi). Diukur: GIF lebar penuh 6.479 '
                         'KiB lawan WebP 983 KiB untuk klip yang sama, jadi ia '
                         'tidak ditulis kecuali diminta.')
    args = ap.parse_args()

    from ursina import application
    application.asset_folder = ROOT
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = args.width, args.height

    from game.app import Game3D
    g = Game3D()

    # Sinema dimatikan, alasan sama seperti di regress.py dan capture.py:
    # adegan pembuka menyetel panels.mode='sinema' yang membekukan pemain dan
    # dunia, jadi klipnya akan merekam layar yang tidak bergerak.
    try:
        from game.cutscene import NASKAH as _NASKAH
        g.state.sinema_selesai = list(_NASKAH)
    except Exception:
        pass

    from direct.showbase.ShowBaseGlobal import base

    for _ in range(10):
        base.taskMgr.step()

    if args.scene:
        g.state.scene_name = args.scene
        for _ in range(30):
            base.taskMgr.step()
        if g.world.scene_name != args.scene:
            print(f'REKAM_WARN: scene masih {g.world.scene_name}, '
                  f'minta {args.scene}', file=sys.stderr)
    if args.hour is not None:
        g.state.time_minutes = float(args.hour) * 60.0
    if args.at:
        try:
            px, py = (float(v) for v in args.at.split(','))
            g.state.player_x, g.state.player_y = px, py
            g.player.set_tile_pos(px, py)
            g.player._set_initial_rotation()
        except Exception:
            traceback.print_exc()
    if args.pitch is not None:
        g.camera_pitch = args.pitch
    if args.yaw is not None:
        g.camera_yaw = args.yaw
    if args.dist is not None:
        g.camera_dist = args.dist
    if any(v is not None for v in (args.pitch, args.yaw, args.dist, args.at)):
        g._snap_camera_to_player()

    for _ in range(args.warmup):
        base.taskMgr.step()

    for k in [x for x in args.keys.split(',') if x]:
        try:
            g.input(k)
        except Exception:
            traceback.print_exc()

    # Animasi dipicu TEPAT sebelum frame pertama direkam, bukan sebelum
    # pemanasan: `_attack_anim` hitung mundur tiap frame, jadi memicunya lebih
    # awal berarti separuh gerakannya sudah lewat saat perekaman mulai.
    if args.anim:
        mode, _, ms = args.anim.partition(':')
        try:
            g.player._play_tool_anim(mode, float(ms) if ms else 350.0)
        except Exception:
            traceback.print_exc()

    n = max(2, int(round(args.detik * args.fps)))
    frames = []
    for _ in range(n):
        base.taskMgr.step()
        im = _frame_pil(base)
        if im is not None:
            frames.append(im)

    if len(frames) < 2:
        print('REKAM_GAGAL: framebuffer tidak menghasilkan gambar.',
              file=sys.stderr)
        os._exit(1)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    durasi_ms = int(round(1000.0 / max(1, args.fps)))

    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=durasi_ms, loop=0, quality=82, method=4)

    gif = None
    if args.gif:
        # Setengah lebar dan palet 128 warna: GIF hanya punya 256 warna
        # ter-indeks, jadi lebar penuh membayar mahal tanpa membeli ketajaman.
        kecil = [f.resize((f.width // 2, f.height // 2)).convert(
                     'P', palette=1, colors=128)
                 for f in frames]
        gif = out.with_suffix('.gif')
        kecil[0].save(gif, save_all=True, append_images=kecil[1:],
                      duration=durasi_ms, loop=0, optimize=True)

    if args.frames_dir:
        d = Path(args.frames_dir)
        d.mkdir(parents=True, exist_ok=True)
        for i, im in enumerate(frames):
            im.save(d / f'{out.stem}_{i:03d}.png')

    w, h = frames[0].size
    print(f'{out}  {w}x{h}  {len(frames)} frame  {args.fps} fps  '
          f'{out.stat().st_size // 1024} KiB')
    if gif is not None:
        print(f'{gif}  {gif.stat().st_size // 1024} KiB')
    os._exit(0)


if __name__ == '__main__':
    main()
