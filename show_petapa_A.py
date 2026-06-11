"""Viewer sekali-jalan: render Petapa Srimana versi feature/3d-mobs (petapa_model.py)
lalu simpan screenshot dan keluar. Dipakai untuk preview, bukan bagian game."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ursina import Ursina, Entity, camera, window, color
from panda3d.core import Filename

app = Ursina(title='Preview Petapa A', borderless=False)
window.color = color.rgb(16, 16, 26)
window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False
window.exit_button.visible = False

from game.petapa_model import build_petapa_srimana

actor = Entity(position=(0, 0, 0))
build_petapa_srimana(actor)
actor.rotation_y = 22          # 3/4 view

camera.position = (5.0, 4.6, -19.0)
camera.look_at((0, 2.3, 0))
camera.fov = 33

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'petapa_A_preview.png')

frame = {'n': 0}
def update():
    frame['n'] += 1
    if frame['n'] == 12:        # beri waktu window & render stabil
        base.win.saveScreenshot(Filename.fromOsSpecific(OUT))
        print('SCREENSHOT SAVED:', OUT)
        os._exit(0)

app.run()
