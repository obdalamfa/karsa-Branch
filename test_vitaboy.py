"""
test_vitaboy.py — Vitaboy avatar viewer + animation player.

Run dari folder `3d/`:
    python test_vitaboy.py

Kontrol:
    N        — next animation
    SPACE    — pause/play
    1-9      — ganti body mesh
    Mouse drag + scroll — kamera (EditorCamera)
    R        — reset kamera
"""
import sys
import logging
import os

# Paksa pipeline GL sebelum import ursina
from panda3d.core import loadPrcFileData
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'aux-display pandadx9')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

from ursina import (Ursina, Entity, EditorCamera, color, Vec3, time as utime,
                    DirectionalLight, AmbientLight, window, Text)


def main():
    from game.vitaboy import VitaboyActor, find_meshes, find_animations

    bodies = find_meshes('bodies')
    anims = find_animations()
    if not bodies:
        print('Tidak ada body mesh ditemukan.'); sys.exit(1)
    if not anims:
        print('Tidak ada anim ditemukan.'); sys.exit(1)
    print(f"Found {len(bodies)} bodies, {len(anims)} animations")

    app = Ursina(size=(1100, 720), title='Vitaboy Viewer + Animator', borderless=False)
    window.color = color.rgb(40, 50, 75) / 255

    DirectionalLight(direction=Vec3(-1, -1.2, -0.6), color=color.rgb(255, 248, 220)/255)
    AmbientLight(color=color.rgb(95, 95, 120)/255)

    # Ground
    Entity(model='quad', scale=10, rotation=(90, 0, 0),
           color=color.rgb(70, 80, 105)/255, position=(0, -0.01, 0))

    state = {
        'body_idx': 0,
        'anim_idx': 0,
        'actor': None,
    }

    info_text = Text(text='', origin=(-0.5, 0.5), position=(-0.85, 0.45),
                     scale=0.85, color=color.white, background=True)

    def load_body(idx: int):
        # destroy previous actor if any
        if state['actor']:
            from ursina import destroy
            destroy(state['actor'].entity)
        idx = idx % len(bodies)
        state['body_idx'] = idx
        actor = VitaboyActor(str(bodies[idx]), entity_kwargs={
            'color': color.rgb(245, 215, 175)/255,
            'double_sided': True,
        })
        actor.set_animation_file(str(anims[state['anim_idx']]))
        state['actor'] = actor
        update_info()

    def cycle_anim(direction: int = 1):
        state['anim_idx'] = (state['anim_idx'] + direction) % len(anims)
        if state['actor']:
            state['actor'].set_animation_file(str(anims[state['anim_idx']]))
        update_info()

    def update_info():
        a = state['actor']
        if a and a.animation:
            info_text.text = (
                f"Body [{state['body_idx']+1}/{len(bodies)}]: {bodies[state['body_idx']].name[:40]}\n"
                f"Anim [{state['anim_idx']+1}/{len(anims)}]: {a.animation.name}\n"
                f"  frames={a.animation.num_frames} duration={a.animation.duration:.2f}s fps={a.fps}\n"
                f"  motions={len(a.animation.motions)}\n"
                f"[N]ext anim [SPACE] pause [1-9] ganti body"
            )

    cam = EditorCamera()
    cam.target = Vec3(0, 3, 0)
    cam.distance = 9.0

    def update():
        if state['actor']:
            state['actor'].update(utime.dt)

    def input(key):
        if key == 'n':
            cycle_anim(1)
        elif key == 'space':
            if state['actor']:
                state['actor'].playing = not state['actor'].playing
        elif key.isdigit() and 1 <= int(key) <= min(9, len(bodies)):
            load_body(int(key) - 1)
        elif key == 'r':
            cam.target = Vec3(0, 3, 0)
            cam.distance = 9.0

    handler = Entity()
    handler.update = update
    handler.input = input

    load_body(0)
    app.run()


if __name__ == '__main__':
    main()
