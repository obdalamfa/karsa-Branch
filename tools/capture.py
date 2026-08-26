"""capture.py — Boot the game, step N frames, save a PNG screenshot.

Usage:
    python tools/capture.py --out shot.png --scene farm --frames 90 [--hour 10]

Runs the real game (same code path as main.py), so screenshots are evidence,
not mockups.
"""
import argparse, os, sys, logging, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'aux-display pandadx9')
loadPrcFileData('', 'window-type onscreen')
loadPrcFileData('', 'sync-video false')
loadPrcFileData('', 'audio-library-name null')

logging.basicConfig(level=logging.WARNING)


def _build_toolrack(g, base):
    """Pajang tiap model alat sebagai entity terpisah, hidup bersamaan.

    Kalau salah satu alat kosong di foto, itu tanda bug NodePath-ganda balik
    lagi: Mesh Ursina adalah NodePath dan hanya boleh punya SATU parent, jadi
    mesh yang di-cache lalu dibagikan bikin semua entity kecuali yang TERAKHIR
    kehilangan geometri.
    """
    from ursina import Entity, Vec3, color, scene
    from game.tool_models import _BUILDERS, build_tool

    kinds = list(_BUILDERS.keys())
    px, pz = g.player.x, g.player.z

    # Kosongkan panggung: ini foto produk untuk alatnya, bukan untuk dunianya.
    for child in list(scene.children):
        try:
            child.enabled = False
        except Exception:
            pass

    span = len(kinds) * 0.66
    Entity(parent=scene, model='cube', color=color.rgb(34, 38, 42),
           position=Vec3(px, 1.0, pz + 2.2),
           scale=Vec3(span + 1.2, 4.2, 0.10))

    for i, kind in enumerate(kinds):
        ox = (i - (len(kinds) - 1) / 2.0) * 0.66
        holder = Entity(parent=scene, position=Vec3(px + ox, 1.95, pz + 2.0),
                        rotation=Vec3(0, 202, 0))
        build_tool(kind, parent=holder)

    g.camera_dist = 4.6
    g.camera_pitch = 2
    g.camera_yaw = 0
    g._snap_camera_to_player()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='shot.png')
    ap.add_argument('--scene', default=None)
    ap.add_argument('--frames', type=int, default=90)
    ap.add_argument('--hour', type=float, default=None)
    ap.add_argument('--keys', default='', help='comma list of keys to send after warmup')
    ap.add_argument('--at', default=None, help='letakkan pemain di x,y sebelum render')
    ap.add_argument('--pitch', type=float, default=None, help='kemiringan kamera (derajat)')
    ap.add_argument('--yaw', type=float, default=None, help='rotasi kamera (derajat)')
    ap.add_argument('--dist', type=float, default=None, help='jarak kamera dari fokus')
    ap.add_argument('--dump', action='store_true',
                    help='cetak sensus entity scene graph ke stdout')
    ap.add_argument('--toolrack', action='store_true',
                    help='pajang SEMUA model alat berjajar di depan kamera. '
                         'Sekaligus bukti bug NodePath-ganda: kalau mesh '
                         'di-cache tanpa salinan, hanya alat TERAKHIR yang '
                         'punya geometri.')
    ap.add_argument('--width', type=int, default=1280)
    ap.add_argument('--height', type=int, default=720)
    args = ap.parse_args()

    # Ursina derives asset_folder from sys.argv[0]; force it to the repo root
    # so fonts/textures/models resolve exactly as they do for main.py.
    from ursina import application
    application.asset_folder = ROOT
    application.fonts_folder = ROOT / 'fonts'
    application.scenes_folder = ROOT / 'scenes'
    application.scripts_folder = ROOT / 'scripts'
    application.textures_compressed_folder = ROOT / 'textures_compressed'
    application.models_compressed_folder = ROOT / 'models_compressed'
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = args.width, args.height

    from game.app import Game3D
    g = Game3D()

    from direct.showbase.ShowBaseGlobal import base
    from ursina import application

    # warm up
    for _ in range(10):
        base.taskMgr.step()

    if args.scene:
        # Perpindahan scene dikendalikan state.scene_name; loop update di app.py
        # yang mendeteksi perubahan lalu memuat ulang world + entities.
        g.state.scene_name = args.scene
        for _ in range(30):
            base.taskMgr.step()
        if g.world.scene_name != args.scene:
            print(f'CAPTURE_WARN: scene masih {g.world.scene_name}, minta {args.scene}',
                  file=sys.stderr)
    if args.at:
        # Player3D adalah Entity-nya sendiri; set_tile_pos ikut menghitung
        # ketinggian permukaan dan collider, jadi jangan set .position mentah.
        try:
            px, py = (float(v) for v in args.at.split(','))
            g.state.player_x, g.state.player_y = px, py
            g.player.set_tile_pos(px, py)
            g.player._set_initial_rotation()
            g._snap_camera_to_player()
        except Exception:
            traceback.print_exc()
    if args.pitch is not None:
        g.camera_pitch = args.pitch
    if args.yaw is not None:
        g.camera_yaw = args.yaw
    if args.dist is not None:
        g.camera_dist = args.dist
    if any(v is not None for v in (args.pitch, args.yaw, args.dist)):
        g._snap_camera_to_player()
    if args.hour is not None:
        try:
            g.state.hour = args.hour
        except Exception:
            pass

    if args.toolrack:
        _build_toolrack(g, base)

    for _ in range(args.frames):
        base.taskMgr.step()

    for k in [x for x in args.keys.split(',') if x]:
        try:
            g.input(k)
        except Exception:
            traceback.print_exc()
        for _ in range(6):
            base.taskMgr.step()

    for _ in range(4):
        base.taskMgr.step()

    if args.dump:
        from ursina import scene as _uscene
        import collections
        cen = collections.Counter()
        for e in _uscene.children:
            for d in [e] + list(getattr(e, 'children', [])):
                nm = getattr(d, 'name', None) or type(d).__name__
                cen[f'{nm}|model={getattr(getattr(d,"model",None),"name",None)}'
                    f'|vis={getattr(d,"visible",None)}|en={getattr(d,"enabled",None)}'] += 1
        print('--- ENTITY CENSUS ---')
        for k, v in cen.most_common(60):
            print(f'{v:5d}  {k}')
        print(f'--- total scene.children={len(_uscene.children)} ---')
        wr = getattr(g.world, 'entities', None) or getattr(g.world, 'tiles', None)
        print('world container:', type(wr).__name__ if wr is not None else None,
              len(wr) if hasattr(wr, '__len__') else '')

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    from panda3d.core import Filename
    img = base.win.getScreenshot()
    if img is None:
        print('CAPTURE_FAIL: no screenshot', file=sys.stderr)
        sys.exit(2)
    img.write(Filename.fromOsSpecific(str(out.resolve())))
    print(f'CAPTURE_OK {out.resolve()}')
    sys.stdout.flush()
    os._exit(0)


if __name__ == '__main__':
    main()
