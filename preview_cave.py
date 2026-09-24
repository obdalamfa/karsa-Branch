from pathlib import Path
from panda3d.core import loadPrcFileData
loadPrcFileData('', 'window-type offscreen\naudio-library-name null')
from ursina import Ursina, camera, color, Vec3, Vec4
color.rgb = lambda r,g,b,a=255: Vec4(r/255,g/255,b/255,a/255)
color.rgba = color.rgb
# This machine's Panda3D VFS cannot read physical files although Python can.
# A memory mount is used only by this preview, without changing the game loader.
from panda3d.core import VirtualFileSystem, VirtualFileMountRamdisk, Filename
import ursina
vfs = VirtualFileSystem.get_global_ptr()
vfs.mount(VirtualFileMountRamdisk(), '/c', 0)
roots = [Path(ursina.__file__).parent, Path('assets').resolve()]
for root in roots:
    for path in root.rglob('*'):
        if path.suffix.lower() in ('.png', '.jpg', '.obj', '.bam', '.ttf', '.egg', '.mtl'):
            fn = Filename.from_os_specific(str(path))
            vfs.make_directory_full(fn.get_dirname())
            vfs.write_file(fn, path.read_bytes(), False)
app=Ursina(window_type='offscreen', size=(1280,900))
from game.state import GameState
from game.world import World3D
from game.entities import EntitiesManager
s=GameState(scene_name='naga_cave',time_minutes=1200)
w=World3D(s); w.load_scene('naga_cave')
e=EntitiesManager(s); e.load_scene('naga_cave')
for _ in range(20): e.update(1/60)
camera.fov=65
camera.position=(14,24,42); camera.look_at(Vec3(14,0,11))
w.update_wall_cutaway(camera.position, Vec3(14,0,11))
for _ in range(8): app.graphicsEngine.renderFrame()
from panda3d.core import PNMImage
shot=PNMImage(); app.win.get_screenshot(shot)
# Save through the memory VFS, then export using Python's normal filesystem.
shot.write('/c/cave-preview.png')
Path('cave-preview.png').write_bytes(vfs.read_file('/c/cave-preview.png', False))
print('actors:',list(e.actors))

# Exercise the real manager across disappearance, appearance, and sleep/wake.
for minute, expected, activity in ((360, {'naga_bijak'}, 'meditating'),
                                    (1080, {'naga_bijak','banaspati'}, 'meditating'),
                                    (0, {'naga_bijak','banaspati'}, 'sleeping'),
                                    (300, {'naga_bijak','banaspati'}, 'meditating')):
    s.time_minutes = minute
    e._npc_sched_t = 30
    e.update(1/60)
    assert set(e.actors) == expected, (minute, set(e.actors))
    assert e.actors['naga_bijak'].activity == activity
    for actor in e.actors.values():
        assert (actor.logical_x, actor.logical_y) == (actor.sched_x, actor.sched_y)
        assert actor.rotation_x == 0
# Re-enter cave with an old saved wandering position.
s.npc_positions['naga_bijak']['x'] = 3
e.load_scene('naga_cave')
assert e.actors['naga_bijak'].logical_x == 7
print('PASS: real manager schedules, sleep/wake, old save restoration')
