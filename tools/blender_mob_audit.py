"""blender_mob_audit.py — Render clay netral tiap model mob/NPC via Blender socket
untuk MENILAI GEOMETRI (lepas dari warna/tekstur). → tools/icon3d/clay_<name>.png

Pakai: python tools/blender_mob_audit.py mob_pocong mob_genderuwo ...
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_rpc import run

ROOT = 'E:/Game Research/Lembah Karsa 3D'
MDIR = ROOT + '/assets/models'
OUTD = ROOT + '/tools/icon3d'
os.makedirs(OUTD.replace('/', os.sep), exist_ok=True)

TPL = r'''
import bpy, math, mathutils
sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
sc.render.resolution_x = 240; sc.render.resolution_y = 240
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
try: sc.eevee.taa_render_samples = 24
except Exception: pass
world = bpy.data.worlds.get('World') or bpy.data.worlds.new('World'); sc.world = world; world.use_nodes=True
bgn = world.node_tree.nodes.get('Background')
if bgn: bgn.inputs[0].default_value=(0.32,0.32,0.34,1); bgn.inputs[1].default_value=0.6
# import (file Y-up)
bpy.ops.wm.obj_import(filepath=r"__PATH__", up_axis='Y', forward_axis='NEGATIVE_Z')
objs=[o for o in bpy.data.objects if o.type=='MESH']
clay=bpy.data.materials.new('clay'); clay.use_nodes=True
b=clay.node_tree.nodes.get('Principled BSDF')
b.inputs['Base Color'].default_value=(0.72,0.70,0.67,1); b.inputs['Roughness'].default_value=0.65
tris=0
for o in objs:
    o.data.materials.clear(); o.data.materials.append(clay)
    tris += len(o.data.polygons)
bpy.context.view_layer.update()
mn=[1e9]*3; mx=[-1e9]*3
for o in objs:
    for v in o.bound_box:
        w=o.matrix_world @ mathutils.Vector(v)
        for i in range(3): mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
print('BBOX mn=%s mx=%s' % (mn, mx))
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=(mn[2]+mx[2])/2
size=max(mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2], 0.5)
cam_d=bpy.data.cameras.new('C'); cam_d.type='ORTHO'; cam_d.ortho_scale=size*1.45
cam=bpy.data.objects.new('C',cam_d); bpy.context.collection.objects.link(cam)
d=size*2.2
cam.location=(cx+d*0.55, cy-d*0.75, cz+d*0.35)
# Arah pandang LANGSUNG via to_track_quat (constraint TRACK_TO tak dievaluasi headless)
_dir = mathutils.Vector((cx,cy,cz)) - cam.location
cam.rotation_euler = _dir.to_track_quat('-Z','Y').to_euler()
sc.camera=cam
sun_d=bpy.data.lights.new('S','SUN'); sun_d.energy=3.0
sun=bpy.data.objects.new('S',sun_d); bpy.context.collection.objects.link(sun)
sun.rotation_euler=(math.radians(52), math.radians(6), math.radians(40))
sc.render.filepath=r"__OUT__"
bpy.ops.render.render(write_still=True)
print('CLAY_OK __NAME__ tris=%d size=%.2f' % (tris, size))
'''

names = sys.argv[1:] or ['mob_pocong']
for nm in names:
    path = (MDIR + f'/{nm}.obj').replace('/', os.sep)
    out = (OUTD + f'/clay_{nm}.png').replace('/', os.sep)
    if not os.path.exists(path):
        print('SKIP (no file)', nm); continue
    code = TPL.replace('__PATH__', path).replace('__OUT__', out).replace('__NAME__', nm)
    r = run(code)
    print(nm, '->', (r.strip().splitlines()[-1] if r.strip() else 'no-output'))
print('DONE')
