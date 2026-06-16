"""blender_icons.py — Render ikon item 3D via Blender (socket langsung 9876).

Setup scene ikon (kamera ortho 3/4, sun+ambient, film transparan, EEVEE),
lalu bangun model crop sederhana dari primitif + material muted, render tiap
item ke tools/icon3d/<id>.png (128px RGBA). Review dulu sebelum ganti yg PIL.

Pakai: python tools/blender_icons.py [item ...]   (default: semua crop)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_rpc import run

ROOT = 'E:/Game Research/Lembah Karsa 3D'
OUTDIR = ROOT + '/tools/icon3d'
os.makedirs(OUTDIR.replace('/', os.sep), exist_ok=True)

SETUP = f'''
import bpy, math
sc = bpy.context.scene
# Hapus semua objek
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
# Render settings
sc.render.resolution_x = 256
sc.render.resolution_y = 256
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
try:
    sc.eevee.taa_render_samples = 24
except Exception: pass
# World ambient lembut (abu netral, muted)
world = bpy.data.worlds.get('World') or bpy.data.worlds.new('World')
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
if bg:
    bg.inputs[0].default_value = (0.30, 0.30, 0.32, 1.0)
    bg.inputs[1].default_value = 0.6
# Target empty utk aim kamera
tgt = bpy.data.objects.new('TGT', None); bpy.context.collection.objects.link(tgt)
tgt.location = (0, 0, 0.35)
# Kamera ortho 3/4
cam_d = bpy.data.cameras.new('Cam'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 1.6
cam = bpy.data.objects.new('Cam', cam_d); bpy.context.collection.objects.link(cam)
cam.location = (2.2, -2.2, 1.9)
con = cam.constraints.new('TRACK_TO'); con.target = tgt
con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
sc.camera = cam
# Sun dari kiri-atas-depan + fill
sun_d = bpy.data.lights.new('Sun', 'SUN'); sun_d.energy = 3.2
sun = bpy.data.objects.new('Sun', sun_d); bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), math.radians(8), math.radians(40))
print('SETUP ok engine=' + sc.render.engine)
'''


def mat(name, rgb, rough=0.6, metallic=0.0):
    r, g, b = [c / 255.0 for c in rgb]
    return f'''
m = bpy.data.materials.new("{name}"); m.use_nodes = True
bsdf = m.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = ({r:.3f}, {g:.3f}, {b:.3f}, 1)
bsdf.inputs['Roughness'].default_value = {rough}
bsdf.inputs['Metallic'].default_value = {metallic}
obj.data.materials.append(m)
'''


def _sword(blade_rgb, metallic, grip_rgb=(96, 64, 40)):
    # Pedang diagonal (ujung kanan-atas), bilah + guard + grip + pommel.
    return f'''
import math
# bilah
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.35))
obj=bpy.context.active_object; obj.scale=(0.05,0.012,0.5)
''' + mat('blade', blade_rgb, rough=(0.25 if metallic else 0.6), metallic=metallic) + '''
# ujung bilah (lancip)
bpy.ops.mesh.primitive_cone_add(radius1=0.05, radius2=0.0, depth=0.18, location=(0,0,0.94))
obj=bpy.context.active_object
''' + mat('tip', blade_rgb, rough=(0.25 if metallic else 0.6), metallic=metallic) + f'''
# guard (melintang)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,-0.18))
obj=bpy.context.active_object; obj.scale=(0.22,0.05,0.04)
''' + mat('guard', (90, 78, 60), rough=0.4, metallic=metallic) + f'''
# grip
bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.3, location=(0,0,-0.36))
obj=bpy.context.active_object
''' + mat('grip', grip_rgb, rough=0.7) + '''
# pommel
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(0,0,-0.52))
obj=bpy.context.active_object
''' + mat('pommel', (90, 78, 60), rough=0.4, metallic=metallic) + '''
# miringkan seluruh pedang biar diagonal dinamis
for o in bpy.data.objects:
    if o.type=='MESH': o.rotation_euler=(0,math.radians(28),0)
'''

# Builder per crop: kode bpy yang membuat objek "obj" lalu set material.
CROPS = {
 'lobak': '''
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0.45))
obj = bpy.context.active_object; obj.scale=(0.55,0.55,0.7)
''' + mat('lobak_body',(216,96,116)) + '''
bpy.ops.mesh.primitive_cone_add(radius1=0.16, radius2=0.0, depth=0.5, location=(0.1,0,0.95))
lf=bpy.context.active_object; lf.rotation_euler=(0.2,0.3,0)
''' + 'obj=lf\n' + mat('lobak_leaf',(95,165,80)),

 'wortel': '''
bpy.ops.mesh.primitive_cone_add(radius1=0.28, radius2=0.02, depth=1.1, location=(0,0,0.45))
obj=bpy.context.active_object; obj.rotation_euler=(3.14159,0,0)
''' + mat('wortel_body',(232,138,52)) + '''
for i in range(3):
    bpy.ops.mesh.primitive_cone_add(radius1=0.07, radius2=0.0, depth=0.5, location=(0.06*(i-1),0,1.05))
    lf=bpy.context.active_object; lf.rotation_euler=(0.15*(i-1),0.2*(i-1),0); obj=lf
''' + mat('wortel_leaf',(90,158,78)),

 'jagung': '''
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0.55))
obj=bpy.context.active_object; obj.scale=(0.42,0.42,0.95)
''' + mat('jagung_body',(234,198,72)) + '''
bpy.ops.mesh.primitive_cone_add(radius1=0.16, radius2=0.0, depth=0.6, location=(0,0,0.2))
hk=bpy.context.active_object; hk.rotation_euler=(3.14159,0,0); obj=hk
''' + mat('jagung_husk',(120,150,70)),

 'tomat': '''
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0.5))
obj=bpy.context.active_object; obj.scale=(0.62,0.62,0.52)
''' + mat('tomat_body',(210,72,56)) + '''
bpy.ops.mesh.primitive_cone_add(radius1=0.18, radius2=0.0, depth=0.18, location=(0,0,0.82))
cal=bpy.context.active_object; obj=cal
''' + mat('tomat_calyx',(95,150,70)),

 'stroberi': '''
bpy.ops.mesh.primitive_cone_add(radius1=0.42, radius2=0.08, depth=0.8, location=(0,0,0.45))
obj=bpy.context.active_object; obj.rotation_euler=(3.14159,0,0)
''' + mat('stroberi_body',(208,58,62)) + '''
bpy.ops.mesh.primitive_cone_add(radius1=0.22, radius2=0.0, depth=0.16, location=(0,0,0.82))
cal=bpy.context.active_object; obj=cal
''' + mat('stroberi_calyx',(90,155,72)),

 'labu': '''
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=(0,0,0.45))
obj=bpy.context.active_object; obj.scale=(0.7,0.7,0.5)
''' + mat('labu_body',(210,120,46)) + '''
bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.22, location=(0,0,0.82))
st=bpy.context.active_object; obj=st
''' + mat('labu_stem',(110,95,55)),

 'bayam': '''
import math as _m
ml = bpy.data.materials.new('bayam_leaf'); ml.use_nodes=True
_b = ml.node_tree.nodes.get('Principled BSDF')
_b.inputs['Base Color'].default_value=(0.337,0.596,0.290,1); _b.inputs['Roughness'].default_value=0.6
for i in range(6):
    a=_m.radians(i*60)
    bpy.ops.mesh.primitive_cone_add(radius1=0.17, radius2=0.0, depth=0.8, location=(0.16*_m.cos(a),0.16*_m.sin(a),0.5))
    lf=bpy.context.active_object; lf.rotation_euler=(0.55*_m.cos(a),0.55*_m.sin(a),0)
    lf.data.materials.append(ml)
obj=lf
''',

 'jamur': '''
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0.6))
cap=bpy.context.active_object; cap.scale=(0.6,0.6,0.42)
bpy.ops.mesh.bisect(plane_co=(0,0,0.6), plane_no=(0,0,-1), clear_inner=True) if False else None
obj=cap
''' + mat('jamur_cap',(190,120,90)) + '''
bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=0.5, location=(0,0,0.3))
st=bpy.context.active_object; obj=st
''' + mat('jamur_stem',(228,216,196)),
}


WEAPONS = {
    'sword_kayu':    _sword((170, 135, 90), 0.0, grip_rgb=(120, 88, 52)),
    'sword_besi':    _sword((178, 186, 198), 1.0),
    'sword_emas':    _sword((214, 182, 92), 1.0, grip_rgb=(120, 60, 48)),
    'sword_mithril': _sword((158, 200, 214), 1.0),
}

def _fish(body_rgb, accent_rgb):
    return f'''
import math
# badan ikan (lonjong sepanjang X)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0.45))
obj=bpy.context.active_object; obj.scale=(0.62,0.30,0.34)
''' + mat('fish_body', body_rgb, rough=0.45) + '''
# ekor (kipas di -X)
bpy.ops.mesh.primitive_cone_add(radius1=0.26, radius2=0.0, depth=0.34, location=(-0.62,0,0.45))
obj=bpy.context.active_object; obj.rotation_euler=(0,math.radians(-90),0); obj.scale=(1,0.18,1)
''' + mat('fish_tail', accent_rgb, rough=0.5) + '''
# sirip punggung
bpy.ops.mesh.primitive_cone_add(radius1=0.16, radius2=0.0, depth=0.3, location=(0.0,0,0.78))
obj=bpy.context.active_object; obj.scale=(1,0.12,1)
''' + mat('fish_fin', accent_rgb, rough=0.5) + '''
# mata
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(0.34,0.16,0.55))
obj=bpy.context.active_object
''' + mat('fish_eye', (30, 28, 30), rough=0.3)


FISH = {
    'ikan_laut':       _fish((120, 150, 170), (96, 124, 145)),
    'ikan_legendaris': _fish((222, 186, 92), (200, 150, 70)),
}

ORGANIC = {
 'mutiara': '''
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.46, location=(0,0,0.5))
obj=bpy.context.active_object
bpy.ops.object.shade_smooth()
''' + mat('mutiara', (236, 232, 226), rough=0.12) + '''
# alas cangkang abu di bawah
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0.18))
obj=bpy.context.active_object; obj.scale=(1.1,1.1,0.32)
''' + mat('cangkang', (150, 150, 156), rough=0.5),

 'mithril': '''
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.5, location=(0,0,0.55))
obj=bpy.context.active_object; obj.scale=(0.7,0.7,1.0); bpy.ops.object.shade_flat()
''' + mat('mithril', (158, 200, 214), rough=0.18, metallic=0.4) + '''
# batu dasar gelap
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.36, location=(0.05,0,0.18))
obj=bpy.context.active_object; obj.scale=(1.1,1.1,0.5); bpy.ops.object.shade_flat()
''' + mat('mithril_rock', (96, 100, 104), rough=0.7),

 'wild_berry': '''
import math as _m
mb = bpy.data.materials.new('berry'); mb.use_nodes=True
_bb=mb.node_tree.nodes.get('Principled BSDF'); _bb.inputs['Base Color'].default_value=(0.55,0.24,0.36,1); _bb.inputs['Roughness'].default_value=0.35
for dx,dy,dz in [(-0.18,0,0.4),(0.18,0,0.4),(0,0.16,0.4),(0,-0.05,0.62),(-0.02,0,0.2)]:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(dx,dy,dz)); bpy.ops.object.shade_smooth()
    bpy.context.active_object.data.materials.append(mb)
bpy.ops.mesh.primitive_cone_add(radius1=0.14,radius2=0.0,depth=0.3,location=(0.1,0,0.8)); obj=bpy.context.active_object; obj.rotation_euler=(0.3,0.4,0)
''' + mat('berry_leaf',(95,160,82)),

 'running_mushroom': '''
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0.62))
obj=bpy.context.active_object; obj.scale=(0.62,0.62,0.45); bpy.ops.object.shade_smooth()
''' + mat('rm_cap',(196,92,84),rough=0.45) + '''
bpy.ops.mesh.primitive_cylinder_add(radius=0.17, depth=0.42, location=(0,0,0.32))
obj=bpy.context.active_object
''' + mat('rm_stem',(228,216,196),rough=0.6) + '''
for sx in (-0.12,0.12):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.22, location=(sx,0.0,0.06))
    lg=bpy.context.active_object; lg.rotation_euler=(0,0.4 if sx>0 else -0.4,0); obj=lg
''' + mat('rm_leg',(210,200,180),rough=0.6),
}

MODELS = {**CROPS, **WEAPONS, **FISH, **ORGANIC}


def render_item(item):
    body = MODELS.get(item)
    if not body:
        print('skip (no builder):', item); return
    path = f'{OUTDIR}/{item}.png'
    code = f'''
import bpy
# hapus mesh lama (sisakan kamera/sun/target)
for o in list(bpy.data.objects):
    if o.type == 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)
{body}
bpy.context.scene.render.filepath = r"{path}"
bpy.ops.render.render(write_still=True)
print("RENDERED {item}")
'''
    print(run(code, recv_timeout=120))


if __name__ == '__main__':
    print(run(SETUP))
    items = sys.argv[1:] or list(MODELS.keys())
    for it in items:
        render_item(it)
    print('DONE ->', OUTDIR)
