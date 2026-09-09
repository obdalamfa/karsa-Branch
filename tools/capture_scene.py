"""
capture_scene.py — Harness penangkap-scene OFFSCREEN untuk iterasi visual cepat.

Boot game tanpa window, load scene + dunia + entitas + lighting + shader kamera,
render dari sudut 3rd-person, simpan ke tools/cap_<scene>.png.

Pakai:  python tools/capture_scene.py farm town house naga_cave swarga
Default: farm town
Ini memungkinkan developer (AI) MELIHAT hasil sendiri tanpa run interaktif.
"""
import sys, math, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from panda3d.core import loadPrcFileData, Filename
loadPrcFileData('', 'window-type offscreen')
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'audio-library-name null')

from ursina import Ursina, camera, color, Vec3, Vec4, DirectionalLight, AmbientLight, scene as ursina_scene
# Override warna ala app.py (cegah overflow putih)
color.rgb = lambda r, g, b, a=255: Vec4(r/255.0, g/255.0, b/255.0, a/255.0)
color.rgba = color.rgb

app = Ursina()
from ursina import window
window.color = color.rgb(118, 122, 125)   # sky overcast (samakan dgn game siang)
from direct.showbase.ShowBaseGlobal import base

from game.state import GameState
from game.world import World3D
from game.entities import EntitiesManager
from game.config import TILE_SIZE

# Lighting overcast (samakan dgn app.py siang)
sun = DirectionalLight(); sun.look_at(Vec3(-0.5, -0.8, -0.4))
amb = AmbientLight(color=color.rgb(82, 84, 88, 255))
sun.color = color.rgb(192, 188, 178)

def _sync_light():
    try:
        ursina_scene.set_shader_input('sm_sun_color', Vec3(0.75, 0.74, 0.70))
        ursina_scene.set_shader_input('sm_ambient', Vec3(0.32, 0.33, 0.34))
        ursina_scene.set_shader_input('sm_sun_dir', Vec3(-0.5, -0.8, -0.4))
        # Kabut atmosferik (samakan dgn game)
        ursina_scene.fog_color = color.rgb(118, 122, 125)
        ursina_scene.fog_density = 0.016
    except Exception:
        pass

# Shader kamera (pixelation + grade) — bisa dimatikan untuk diagnosa (CAP_NOSHADER)
if not os.environ.get('CAP_NOSHADER'):
    try:
        from game.shaders.vhs_bloom import vhs_bloom_shader
        camera.shader = vhs_bloom_shader
        camera.set_shader_input('time', 1.0)
    except Exception as e:
        print('cam shader skip:', e)

camera.fov = 60

state = GameState()
world = World3D(state)
ents = EntitiesManager(state)

# Opsional: render HUD/UI untuk verifikasi (CAP_HUD=1)
ui = None
if os.environ.get('CAP_HUD'):
    try:
        import game.panels as _panels
        _panels._FONT_NAME = 'VeraMono.ttf'
        ui = _panels.UIManager(state)
        ui.update(state, 0)
    except Exception as e:
        import traceback; traceback.print_exc()
        print('UI init skip:', e)


def capture(scene_name):
    # Dungeon perlu tiles — generate bila kosong
    if scene_name == 'dungeon' and not state.dungeon_tiles:
        try:
            from game.dungeon import generate_dungeon
            generate_dungeon(state)
        except Exception as e:
            print('dungeon gen skip:', e)
    state.scene_name = scene_name
    # CAP_HOUR: set jam + perbarui jadwal NPC supaya mob malam (genderuwo dll) muncul
    _hr = os.environ.get('CAP_HOUR')
    if _hr:
        state.time_minutes = float(_hr) * 60
        try:
            ents._update_npc_schedules()
        except Exception as e:
            print('sched update skip:', e)
    world.load_scene(scene_name)
    ents.load_scene(scene_name)
    _sync_light()

    # Fokus kamera: tengah scene (atau player)
    try:
        sc = world.scene_obj
        cx = (sc.w * 0.5) * TILE_SIZE
        cz = (sc.h * 0.5) * TILE_SIZE
    except Exception:
        cx, cz = state.player_x * TILE_SIZE, state.player_y * TILE_SIZE
    focus = Vec3(cx, 1.0, cz)
    if os.environ.get('CAP_TOPDOWN'):
        # Top-down untuk memetakan tile
        camera.position = Vec3(cx, max(sc.w, sc.h) * TILE_SIZE * 1.1, cz)
        camera.look_at(focus)
    else:
        if os.environ.get('CAP_FOCUS'):
            fx, fz = [float(v) for v in os.environ['CAP_FOCUS'].split(',')]
            focus = Vec3(fx, 0.5, fz)
        yaw = float(os.environ.get('CAP_YAW', 25.0))
        pitch = float(os.environ.get('CAP_PITCH', 32.0))
        dist = float(os.environ.get('CAP_DIST', 26.0))
        cy, cp = math.radians(yaw), math.radians(pitch)
        camera.position = focus + Vec3(math.sin(cy)*math.cos(cp), math.sin(cp),
                                       -math.cos(cy)*math.cos(cp)) * dist
        camera.look_at(focus)

    # Render beberapa frame (lerp/shader settle)
    for _ in range(4):
        base.graphicsEngine.renderFrame()
    out = f'tools/cap_{scene_name}.png'
    base.win.saveScreenshot(Filename.fromOsSpecific(out))
    print('CAPTURED', out)


scenes = sys.argv[1:] or ['farm', 'town']
for s in scenes:
    try:
        capture(s)
    except Exception as e:
        import traceback; traceback.print_exc()
        print('CAPTURE_FAIL', s, e)

print('DONE')
