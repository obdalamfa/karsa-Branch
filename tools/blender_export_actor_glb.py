"""Ekspor karakter ter-rig dari characters_vitaboy.blend ke .glb ber-animasi.

Pakai:
    blender --background --factory-startup assets/blend/characters_vitaboy.blend \
        --python tools/blender_export_actor_glb.py [-- player npc_arya ...]

Hasil: assets/models/actors/<nama>.glb berisi rig 29 tulang, mesh dengan
tekstur asli (bukan bake), dan animasi idle/walk/hoe/swing/water.
"""
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from blender_walk_cycle import buat_siklus_jalan  # noqa: E402
TEX_DIR = os.path.join(ROOT, 'assets', 'blend', 'tex')
OUT_DIR = os.path.join(ROOT, 'assets', 'models', 'actors')
ANIMS = ('idle', 'walk', 'hoe', 'swing', 'water')


def _remap_images():
    # Path tekstur di .blend menunjuk ke checkout lain; arahkan ke tex/ di repo ini.
    for img in bpy.data.images:
        p = os.path.join(TEX_DIR, os.path.basename(img.filepath))
        if os.path.exists(p):
            img.filepath = p
            img.reload()


def _export(name):
    rig = bpy.data.objects[name + '_rig']
    parts = [o for o in bpy.data.objects if o.parent == rig]
    buat_siklus_jalan(rig)

    ad = rig.animation_data or rig.animation_data_create()
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    for anim in ANIMS:
        act = bpy.data.actions.get(f'{name}_rig_{anim}')
        if act is None:
            continue
        tr = ad.nla_tracks.new()
        tr.name = anim
        strip = tr.strips.new(anim, int(act.frame_range[0]), act)
        if hasattr(strip, 'action_slot') and act.slots:
            strip.action_slot = act.slots[0]
    ad.action = None

    bpy.ops.object.select_all(action='DESELECT')
    for o in [rig] + parts:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig

    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(OUT_DIR, name + '.glb'),
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_animations=True,
        export_animation_mode='NLA_TRACKS',
        export_force_sampling=True,
        export_skins=True,
        export_yup=True,
    )
    print('EXPORTED', name, [t.name for t in ad.nla_tracks])


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    names = argv or sorted(o.name[:-4] for o in bpy.data.objects
                           if o.type == 'ARMATURE' and o.name.endswith('_rig'))
    _remap_images()
    for n in names:
        _export(n)


main()
