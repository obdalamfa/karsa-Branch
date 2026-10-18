"""potret_penunggu.py — Potret dialog untuk penunggu prosedural (naga_bijak).

`tools/potret.py` merender wajah dari GLB di assets/models/actors/. Penunggu
gua tidak punya GLB: tubuhnya dirakit `game.guardian_models.build_guardian`
saat runtime. Tanpa potret, kotak dialog Sang Hyang Naga menampilkan bingkai
kosong.

Dirender DI DALAM game, bukan di jendela Ursina kosong: percobaan pertama
begitu menghasilkan siluet putih rata, karena material naga butuh cahaya dan
shader yang dipasang game. Latarnya gua itu sendiri, jadi potretnya sewarna
dengan tempat pemain bertemu naga.

    python tools/potret_penunggu.py            # naga_bijak di naga_cave
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData, Filename, getModelPath
loadPrcFileData('', 'window-type onscreen')
loadPrcFileData('', 'sync-video false')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'depth-bits 24')

from ursina import application
application.asset_folder = ROOT
application.fonts_folder = ROOT / 'assets' / 'fonts'
getModelPath().append_path(str(ROOT))

import game.config as cfg
cfg.SCREEN_W, cfg.SCREEN_H = 1280, 720

OUT = ROOT / 'assets' / 'textures' / 'potret'
PENUNGGU = {'naga_bijak': 'naga_cave'}


def main(kind):
    from game.app import Game3D
    from game.cutscene import NASKAH
    from ursina import camera, Vec3
    g = Game3D()
    from direct.showbase.ShowBaseGlobal import base   # ada setelah Game3D

    def step(n):
        for _ in range(n):
            base.taskMgr.step()

    g.state.sinema_selesai = list(NASKAH)
    if g.panels.mode == 'chargen':
        step(5); g.input('enter'); step(30)
    g.state.scene_name = PENUNGGU[kind]
    step(60)
    aktor = g.entities.actors.get(kind)
    if aktor is None:
        print('GAGAL: aktor', kind, 'tidak ada di', g.world.scene_name)
        return 1
    g.panels.set_hud_visible(False)
    for e in getattr(g.panels, '_label_ents', ()) or ():
        e.enabled = False

    # Kamera milik game (orbit di sekitar pemain) yang dipakai: menimpa
    # `camera.position` langsung bertabrakan dengan pivot orbit dan pernah
    # menghasilkan foto altar, bukan naga. Pemain berdiri di depan naga,
    # kamera diputar menghadapnya, lalu tubuh pemain disembunyikan.
    ax, ay = round(aktor.world_x / cfg.TILE_SIZE), round(aktor.world_z / cfg.TILE_SIZE)
    g.state.player_x, g.state.player_y = float(ax), float(ay + 3)
    g.player.set_tile_pos(ax, ay + 3)
    g.camera_yaw, g.camera_pitch, g.camera_dist = 180.0, 14.0, 9.0
    g._snap_camera_to_player()
    step(20)
    g.player.visible = False
    for anak in g.player.children:
        anak.visible = False
    lo, hi = aktor.getTightBounds(base.render)
    kepala = Vec3((lo.x + hi.x) / 2, hi.y - (hi.y - lo.y) * 0.2, (lo.z + hi.z) / 2)
    camera.look_at(kepala)
    for _ in range(3):
        base.graphicsEngine.renderFrame()
    tmp = OUT / f'_{kind}_mentah.png'
    base.win.getScreenshot().write(Filename.fromOsSpecific(str(tmp)))

    from PIL import Image
    im = Image.open(tmp).convert('RGBA')
    w, h = im.size
    # Dengan kamera di atas (yaw 180, pitch 14, jarak 9) kepala naga jatuh di
    # sekitar 68% tinggi layar; kotak 42% tinggi memuat tanduk sampai leher.
    s, cx, cy = int(h * 0.42), w // 2, int(h * 0.68)
    kotak = (cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2)
    p = OUT / f'{kind}.png'
    im.crop(kotak).resize((256, 256), Image.LANCZOS).save(p)
    if os.environ.get('SIMPAN_MENTAH'):
        print('MENTAH', tmp)
    else:
        tmp.unlink()
    print('TULIS', p)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'naga_bijak'))
