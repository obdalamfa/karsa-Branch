"""view_model.py — Render satu model .obj terisolasi untuk cek orientasi/warna.
Pakai: python tools/view_model.py pohon_bambu lantern sumur
Output: tools/vm_<name>.png  (kamera samping, grid lantai sbg acuan tegak)
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from panda3d.core import loadPrcFileData, Filename
loadPrcFileData('', 'window-type offscreen')
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'audio-library-name null')
from ursina import Ursina, camera, color, Vec3, Vec4, Entity, DirectionalLight, AmbientLight
color.rgb = lambda r, g, b, a=255: Vec4(r/255.0, g/255.0, b/255.0, a/255.0)
color.rgba = color.rgb
app = Ursina()
from ursina import window
window.color = color.rgb(90, 95, 100)
from direct.showbase.ShowBaseGlobal import base
sun = DirectionalLight(); sun.look_at(Vec3(-0.4, -0.7, -0.5)); sun.color = color.rgb(200, 196, 186)
amb = AmbientLight(color=color.rgb(120, 122, 126, 255))
from game.entities import load_model_file, make_obj_entity

def view(name):
    # lantai grid sebagai acuan "tegak"
    floor = Entity(model='plane', scale=10, color=color.rgb(70, 110, 70), y=0)
    e = make_obj_entity(name, (0, 0, 0), scale=1.0, rot_y=0)
    if e is None:
        print('NO MODEL', name); return
    # bingkai tinggi acuan (tiang merah 2m) untuk banding tegak
    pole = Entity(model='cube', scale=(0.06, 2, 0.06), position=(2.2, 1, 0), color=color.rgb(200, 60, 60))
    camera.fov = 50
    focus = Vec3(0, 1.2, 0)
    camera.position = focus + Vec3(math.sin(math.radians(35)), 0.35, -math.cos(math.radians(35))) * 7
    camera.look_at(focus)
    for _ in range(4):
        base.graphicsEngine.renderFrame()
    out = f'tools/vm_{name}.png'
    base.win.saveScreenshot(Filename.fromOsSpecific(out))
    print('CAPTURED', out)
    e.enabled = False; floor.enabled = False; pole.enabled = False

for n in (sys.argv[1:] or ['pohon_bambu']):
    view(n)
print('DONE')
