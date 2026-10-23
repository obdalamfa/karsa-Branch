"""probe_pohon_tumbang.py — menebang pohon lewat jalur input app.py.

Kenapa probe ini ada
────────────────────
`_animate_falling_tree` memanggil `animate_rotation(curve='ease_in_out')`.
Ursina mengharapkan FUNGSI kurva, bukan string; TypeError-nya ditelan
`except Exception: pass` di interaction_controller.use_tool_at. Akibatnya
replika tidak pernah rebah, `invoke(destroy, ...)` tidak pernah dijadwalkan,
dan setiap tebangan meninggalkan "pohon hantu" yang berdiri selamanya --
induknya scene, jadi ikut terbawa ke scene lain.

Jalur: Kapak dipilih, pemain menghadap ubin pohon, g.input('space') ->
app.input -> player.handle_input -> interaction_controller.use_tool_at ->
_animate_falling_tree + world.load_scene. Replika ditangkap dengan
membungkus _animate_falling_tree (yang tetap dipanggil apa adanya) dan
mencatat entity yang diberi animate_rotation.

Diperiksa per scene (cemetery = DT Blender, mountain = TR Blender,
farm = TR prosedural):
  1. tebang     ubin berubah, kayu +1
  2. replika    rupa replika = rupa yang berdiri (model Blender bila ubinnya
                Blender), dan modelnya tergantung di bawah entity-nya sendiri;
                replika prosedural punya batang + 3 tajuk (dulu batangnya
                model 'cylinder' yang tidak ada di Ursina 8.3)
  3. rebah      rotasi replika berubah setelah ~0,5 detik
  4. lenyap     replika sudah dihancurkan setelah 4 detik nyata

Pakai: xvfb-run -a python _bench/probes/probe_pohon_tumbang.py   (keluar 1 = gagal)
"""
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData, getModelPath  # noqa: E402
loadPrcFileData('', 'window-type onscreen')
loadPrcFileData('', 'sync-video false')
loadPrcFileData('', 'audio-library-name null')

from ursina import application  # noqa: E402
application.asset_folder = ROOT
application.fonts_folder = ROOT / 'assets' / 'fonts'
getModelPath().append_path(str(ROOT.resolve()))

import game.state as gs  # noqa: E402
_tmp = Path(tempfile.mkdtemp()) / 'save.json'
shutil.copyfile(ROOT / 'tools' / 'fixtures' / 'regress_save.json', _tmp)
gs.SAVE_FILE = str(_tmp)

from game.app import Game3D  # noqa: E402
from game.cutscene import NASKAH  # noqa: E402
from game.config import TOOLS  # noqa: E402
g = Game3D()
from direct.showbase.ShowBaseGlobal import base  # noqa: E402
g.state.sinema_selesai = list(NASKAH)
for _ in range(10):
    base.taskMgr.step()

tangkap = []
_asli = g.player._animate_falling_tree


def _bungkus(wx, wz, tid):
    # falling_root = entity pertama yang di-animate_rotation selama fungsi ini.
    # Dicatat SEBELUM animasinya jalan, supaya replika tetap tertangkap
    # walau animate_rotation sendiri melempar.
    from ursina import Entity
    asli_rot = Entity.animate_rotation
    akar = []

    def _rot(self, *a, **k):
        akar.append(self)
        return asli_rot(self, *a, **k)
    Entity.animate_rotation = _rot
    try:
        _asli(wx, wz, tid)
    finally:
        Entity.animate_rotation = asli_rot
        tangkap.append(akar[0] if akar else None)


g.player._animate_falling_tree = _bungkus

KASUS = (('cemetery', (7, 5), (7, 4), 'pohon_mati.obj'),
         ('mountain', (2, 12), (2, 11), 'pohon_tropis.obj'),
         ('farm', None, None, 'BATANG'))
gagal = []


def _model_anak(r):
    out = []
    for c in getattr(r, 'children', []):
        m = getattr(c, 'model', None)
        if m is not None:
            out.append((m.getName(), m.getParent() == c))
    return out


for sc, tile, berdiri, harap in KASUS:
    g.state.scene_name = sc
    for _ in range(30):
        base.taskMgr.step()
    if tile is None:                       # cari TR pertama dengan ubin jalan di bawahnya
        from game.config import TR
        w = g.world
        cari = [(x, y) for y in range(1, w.scene_obj.h - 1) for x in range(1, w.scene_obj.w - 1)
                if w.get_tile(x, y) == TR and w.is_walkable(x, y - 1)]
        if not cari:
            gagal.append(f'{sc}: tidak ada TR yang bisa didekati')
            continue
        tile = cari[0]
        berdiri = (tile[0], tile[1] - 1)
    del tangkap[:]
    g.state.tool_index = TOOLS.index('Kapak')
    g.state.energy = 100
    tid0 = g.world.get_tile(*tile)
    kayu0 = g.state.inventory.get('kayu', 0)
    g.player.set_tile_pos(*berdiri)
    g.player.facing = 'up'
    for _ in range(2):
        base.taskMgr.step()
    g.input('space')
    tid1 = g.world.get_tile(*tile)
    kayu1 = g.state.inventory.get('kayu', 0)
    r = tangkap[0] if tangkap else None
    anak = _model_anak(r) if r is not None else []
    rot0 = tuple(r.rotation) if r is not None else None
    t0 = time.time()
    while time.time() - t0 < 0.5:
        base.taskMgr.step()
    rot1 = tuple(r.rotation) if r else None
    while time.time() - t0 < 4.0:
        base.taskMgr.step()
    hidup = r is not None and not r.is_empty()
    print(f'{sc}: ubin {tile} {tid0}->{tid1} kayu {kayu0}->{kayu1} | anak {anak[:3]} | '
          f'rot {rot0} -> {rot1} | masih hidup 4 s: {hidup}')
    if tid1 == tid0 or kayu1 != kayu0 + 1:
        gagal.append(f'{sc}: tebang tidak terjadi')
    if r is None:
        gagal.append(f'{sc}: replika tidak terbentuk')
        continue
    if harap == 'BATANG':                  # replika prosedural: batang + 3 tajuk
        if len(anak) < 4:
            gagal.append(f'{sc}: replika prosedural kurang bagian ({anak})')
    elif harap and not any(n == harap and own for n, own in anak):
        gagal.append(f'{sc}: replika bukan {harap} milik sendiri ({anak})')
    if rot1 is None or rot1 == rot0:
        gagal.append(f'{sc}: replika tidak rebah (rot {rot0} -> {rot1})')
    if hidup:
        gagal.append(f'{sc}: replika masih berdiri setelah 4 s (pohon hantu)')

print('GAGAL:\n  ' + '\n  '.join(gagal) if gagal else 'LULUS')
os._exit(1 if gagal else 0)
