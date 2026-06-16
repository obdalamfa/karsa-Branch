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


def emat(name, rgb, strength=2.5, rough=0.5):
    r, g, b = [c / 255.0 for c in rgb]
    return f'''
m = bpy.data.materials.new("{name}"); m.use_nodes = True
bsdf = m.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = ({r:.3f}, {g:.3f}, {b:.3f}, 1)
bsdf.inputs['Roughness'].default_value = {rough}
try:
    bsdf.inputs['Emission Color'].default_value = ({r:.3f}, {g:.3f}, {b:.3f}, 1)
    bsdf.inputs['Emission Strength'].default_value = {strength}
except Exception:
    pass
obj.data.materials.append(m)
'''


def _sword(blade_rgb, metallic, grip_rgb=(96, 64, 40)):
    # Pedang tegak (broad-face menghadap kamera), parts DI-JOIN jadi satu mesh
    # lalu dimiringkan sbg rigid body → tetap menyatu, blade kebaca jelas.
    bro = (0.25 if metallic else 0.55)
    return f'''
import math
parts=[]
# bilah (broad face di bidang X-Z menghadap kamera)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.44)); obj=bpy.context.active_object; obj.scale=(0.085,0.024,0.46)
''' + mat('blade', blade_rgb, rough=bro, metallic=metallic) + '''
parts.append(obj)
# ujung lancip (apex ke atas)
bpy.ops.mesh.primitive_cone_add(radius1=0.085, radius2=0.0, depth=0.18, location=(0,0,0.98)); obj=bpy.context.active_object; obj.scale=(1,0.28,1)
''' + mat('tip', blade_rgb, rough=bro, metallic=metallic) + '''
parts.append(obj)
# guard melintang
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,-0.02)); obj=bpy.context.active_object; obj.scale=(0.30,0.07,0.055)
''' + mat('guard', (88, 76, 58), rough=0.4, metallic=metallic) + '''
parts.append(obj)
# grip
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.32, location=(0,0,-0.24)); obj=bpy.context.active_object
''' + mat('grip', grip_rgb, rough=0.75) + '''
parts.append(obj)
# pommel
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(0,0,-0.44)); obj=bpy.context.active_object; bpy.ops.object.shade_smooth()
''' + mat('pommel', (88, 76, 58), rough=0.4, metallic=metallic) + '''
parts.append(obj)
# JOIN semua jadi 1 mesh, lalu miringkan diagonal sbg rigid body
for o in bpy.data.objects: o.select_set(False)
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
sw = bpy.context.active_object
sw.rotation_euler = (0, math.radians(26), 0)
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
    # Body + ekor + sirip + mata, semua DI-JOIN jadi satu mesh (sirip nempel).
    return f'''
import math
parts=[]
# badan ikan (lonjong sepanjang X, profil menghadap kamera -Y)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0.46)); obj=bpy.context.active_object; obj.scale=(0.6,0.30,0.36); bpy.ops.object.shade_smooth()
''' + mat('fish_body', body_rgb, rough=0.42) + '''
parts.append(obj)
# ekor: kipas, base lebar di -X, apex ke badan
bpy.ops.mesh.primitive_cone_add(radius1=0.3, radius2=0.0, depth=0.32, location=(-0.46,0,0.46)); obj=bpy.context.active_object; obj.rotation_euler=(0,math.radians(90),0); obj.scale=(1,0.16,1)
''' + mat('fish_tail', accent_rgb, rough=0.5) + '''
parts.append(obj)
# sirip punggung (di atas badan, base nempel)
bpy.ops.mesh.primitive_cone_add(radius1=0.18, radius2=0.0, depth=0.26, location=(0.02,0,0.66)); obj=bpy.context.active_object; obj.scale=(1,0.1,1)
''' + mat('fish_fin', accent_rgb, rough=0.5) + '''
parts.append(obj)
# mata (sisi -Y menghadap kamera)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.062, location=(0.28,-0.2,0.54)); obj=bpy.context.active_object; bpy.ops.object.shade_smooth()
''' + mat('fish_eye', (28, 26, 28), rough=0.3) + '''
parts.append(obj)
# JOIN jadi satu
for o in bpy.data.objects: o.select_set(False)
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
'''


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

B_ITEMS = {
 'wild_herb': '''
import math
ml = bpy.data.materials.new('herb'); ml.use_nodes=True
_h=ml.node_tree.nodes.get('Principled BSDF'); _h.inputs['Base Color'].default_value=(0.35,0.59,0.32,1); _h.inputs['Roughness'].default_value=0.55
ml2 = bpy.data.materials.new('herb2'); ml2.use_nodes=True
_h2=ml2.node_tree.nodes.get('Principled BSDF'); _h2.inputs['Base Color'].default_value=(0.30,0.50,0.28,1); _h2.inputs['Roughness'].default_value=0.55
# daun memanjang menyebar dari pangkal (kipas)
for i,a in enumerate((-0.6,-0.3,0.0,0.3,0.6)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(math.sin(a)*0.22,0,0.42+math.cos(a)*0.16))
    lf=bpy.context.active_object; lf.scale=(0.07,0.03,0.42); lf.rotation_euler=(0,a,0); bpy.ops.object.shade_smooth()
    lf.data.materials.append(ml if i%2 else ml2)
# batang
bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.3, location=(0,0,0.12)); obj=bpy.context.active_object
''' + mat('herb_stem',(120,98,60),rough=0.7),

 'obor': '''
# gagang kayu
bpy.ops.mesh.primitive_cylinder_add(radius=0.075, depth=0.8, location=(0,0,0.35))
obj=bpy.context.active_object
''' + mat('obor_kayu',(140,100,60),rough=0.75) + '''
# kain di ujung
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(0,0,0.78)); obj=bpy.context.active_object; obj.scale=(1,1,0.8)
''' + mat('obor_kain',(86,70,54),rough=0.8) + '''
# api luar (oranye menyala) — base color fiery + emission tinggi
bpy.ops.mesh.primitive_cone_add(radius1=0.26, radius2=0.0, depth=0.62, location=(0,0,1.18))
obj=bpy.context.active_object; bpy.ops.object.shade_smooth()
''' + emat('api_luar',(235,104,34),strength=1.15,rough=0.4) + '''
# api dalam (kuning lebih terang)
bpy.ops.mesh.primitive_cone_add(radius1=0.13, radius2=0.0, depth=0.42, location=(0,0,1.06))
obj=bpy.context.active_object; bpy.ops.object.shade_smooth()
''' + emat('api_dalam',(255,214,96),strength=1.7,rough=0.4),

 'mandrake': '''
import math
# umbi utama lonjong
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(0,0,0.5)); obj=bpy.context.active_object; obj.scale=(0.82,0.72,0.95); bpy.ops.object.shade_smooth()
''' + mat('mand_body',(168,128,86),rough=0.7) + '''
# dua akar kaki bawah
for sx in (-0.13,0.14):
    bpy.ops.mesh.primitive_cone_add(radius1=0.12, radius2=0.0, depth=0.34, location=(sx,0,0.12))
    rt=bpy.context.active_object; rt.rotation_euler=(0,(0.5 if sx>0 else -0.5),math.pi); obj=rt
''' + mat('mand_root',(150,112,72),rough=0.75) + '''
# daun hijau di atas (kipas kecil)
mg = bpy.data.materials.new('mleaf'); mg.use_nodes=True
_mg=mg.node_tree.nodes.get('Principled BSDF'); _mg.inputs['Base Color'].default_value=(0.36,0.55,0.30,1); _mg.inputs['Roughness'].default_value=0.6
for a in (-0.5,-0.2,0.2,0.5):
    bpy.ops.mesh.primitive_cone_add(radius1=0.07, radius2=0.0, depth=0.4, location=(math.sin(a)*0.12,0,0.92+math.cos(a)*0.1))
    lf=bpy.context.active_object; lf.rotation_euler=(0,a,0); lf.data.materials.append(mg)
''',
}

def _prasasti(seed):
    # Pecahan batu prasasti — slab pipih + guratan aksara; bentuk beda per seed.
    import math as _m
    tilt = [(-8, 0.06), (10, -0.05), (-4, 0.1)][seed % 3]
    return f'''
import math
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.46)); obj=bpy.context.active_object
obj.scale=(0.52,0.10,0.6); obj.rotation_euler=(0,math.radians({tilt[0]}),{tilt[1]})
bpy.ops.object.modifier_add(type='BEVEL'); obj.modifiers['Bevel'].width=0.03; obj.modifiers['Bevel'].segments=2
''' + mat('prasasti', (150, 146, 138), rough=0.85) + f'''
# guratan aksara (garis horizontal gelap di muka -Y)
mg = bpy.data.materials.new('ukir'); mg.use_nodes=True
_g=mg.node_tree.nodes.get('Principled BSDF'); _g.inputs['Base Color'].default_value=(0.30,0.28,0.25,1); _g.inputs['Roughness'].default_value=0.9
for i,zz in enumerate(({0.62 if seed%2 else 0.66}, 0.5, 0.38, 0.26)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,-0.11,zz)); g=bpy.context.active_object
    g.scale=(0.3 - i*0.03, 0.012, 0.018); g.rotation_euler=(0,math.radians({tilt[0]}),{tilt[1]})
    g.data.materials.append(mg)
'''

EXTRA = {
 'peti_kayu': '''
import math
# badan peti kayu (kubus ber-bevel, tanpa tiang menonjol)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.44)); obj=bpy.context.active_object; obj.scale=(0.46,0.46,0.42)
bpy.ops.object.modifier_add(type='BEVEL'); obj.modifiers['Bevel'].width=0.035; obj.modifiers['Bevel'].segments=2
''' + mat('peti_kayu',(150,112,70),rough=0.7) + '''
# seam papan (alur gelap) di muka -Y dan +X, dalam batas kubus
md = bpy.data.materials.new('peti_dark'); md.use_nodes=True
_d=md.node_tree.nodes.get('Principled BSDF'); _d.inputs['Base Color'].default_value=(0.40,0.28,0.16,1); _d.inputs['Roughness'].default_value=0.78
for zz in (0.58,0.30):                      # 2 alur horizontal
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,-0.465,zz)); s=bpy.context.active_object; s.scale=(0.47,0.012,0.025); s.data.materials.append(md)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.465,0,zz)); s=bpy.context.active_object; s.scale=(0.012,0.47,0.025); s.data.materials.append(md)
# diagonal X-brace di muka -Y
for ang in (32,-32):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,-0.47,0.44)); b=bpy.context.active_object; b.scale=(0.012,0.012,0.5); b.rotation_euler=(0,math.radians(ang),0); b.data.materials.append(md)
# lid rim atas (tipis, sebatas kubus)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.86)); r=bpy.context.active_object; r.scale=(0.47,0.47,0.04); r.data.materials.append(md)
''',

 'pagar_kayu': '''
import math
mw = bpy.data.materials.new('pagar'); mw.use_nodes=True
_w=mw.node_tree.nodes.get('Principled BSDF'); _w.inputs['Base Color'].default_value=(0.58,0.44,0.28,1); _w.inputs['Roughness'].default_value=0.8
# 3 tiang vertikal
for px in (-0.42,0.0,0.42):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(px,0,0.5)); t=bpy.context.active_object; t.scale=(0.08,0.08,0.62)
    bpy.ops.object.modifier_add(type='BEVEL'); t.modifiers['Bevel'].width=0.02; t.data.materials.append(mw)
# 2 palang horizontal
for pz in (0.34,0.74):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,pz)); r=bpy.context.active_object; r.scale=(0.56,0.06,0.06); r.data.materials.append(mw)
''',

 'buku_paman_arsa': '''
import math
# sampul (coklat-merah)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.4)); obj=bpy.context.active_object; obj.scale=(0.42,0.56,0.09)
bpy.ops.object.modifier_add(type='BEVEL'); obj.modifiers['Bevel'].width=0.02; obj.modifiers['Bevel'].segments=2
''' + mat('buku_sampul',(140,78,58),rough=0.6) + '''
# halaman (krem, sedikit lebih kecil, di antara sampul)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.02,0,0.4)); obj=bpy.context.active_object; obj.scale=(0.40,0.52,0.07)
''' + mat('buku_hal',(226,214,184),rough=0.85) + '''
# punggung buku (spine, gelap)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.40,0,0.4)); obj=bpy.context.active_object; obj.scale=(0.05,0.57,0.10)
''' + mat('buku_spine',(98,52,40),rough=0.6) + '''
# miringkan sedikit utk perspektif dinamis
for o in bpy.data.objects:
    if o.type=='MESH': o.rotation_euler=(math.radians(-18),0,math.radians(12))
''',

 'perahu': '''
import math
# lambung (setengah ellipsoid memanjang)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0.42)); obj=bpy.context.active_object
obj.scale=(0.66,0.30,0.34); bpy.ops.object.shade_smooth()
''' + mat('perahu_luar',(146,104,64),rough=0.7) + '''
# rongga dalam (gelap) - sphere lebih kecil di atas garis air
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0.6)); obj=bpy.context.active_object
obj.scale=(0.58,0.22,0.3); bpy.ops.object.shade_smooth()
''' + mat('perahu_dalam',(70,52,36),rough=0.85) + '''
# dayung
bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.7, location=(0.2,0.18,0.62)); obj=bpy.context.active_object; obj.rotation_euler=(math.radians(60),0,math.radians(20))
''' + mat('dayung',(120,92,58),rough=0.7),

 'fragmen_prasasti_1': _prasasti(0),
 'fragmen_prasasti_2': _prasasti(1),
 'fragmen_prasasti_3': _prasasti(2),
}

EXTRA2 = {
 'air_keabadian': '''
import math
# badan botol = cairan bercahaya cyan (botol 'penuh')
bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.46, location=(0,0,0.34)); obj=bpy.context.active_object; bpy.ops.object.shade_smooth()
bpy.ops.object.modifier_add(type='BEVEL'); obj.modifiers['Bevel'].width=0.04; obj.modifiers['Bevel'].segments=3
''' + emat('air_cairan',(58,196,224),strength=1.9,rough=0.2) + '''
# bahu botol (taper) - kerucut pendek pucat glossy
bpy.ops.mesh.primitive_cone_add(radius1=0.22, radius2=0.09, depth=0.14, location=(0,0,0.64)); obj=bpy.context.active_object; bpy.ops.object.shade_smooth()
''' + emat('air_bahu',(80,200,224),strength=1.4,rough=0.15) + '''
# leher kaca pucat
bpy.ops.mesh.primitive_cylinder_add(radius=0.085, depth=0.16, location=(0,0,0.78)); obj=bpy.context.active_object
''' + mat('air_leher',(188,216,222),rough=0.12) + '''
# sumbat gabus
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.1, location=(0,0,0.9)); obj=bpy.context.active_object
''' + mat('air_gabus',(150,112,72),rough=0.7),

 'peta_mimpi_maya': '''
import math
# lembar peta (kertas krem) - cube pipih sedikit miring
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.42)); obj=bpy.context.active_object; obj.scale=(0.52,0.40,0.03); obj.rotation_euler=(math.radians(-14),0,math.radians(6))
''' + mat('peta_kertas',(222,206,168),rough=0.85) + '''
# garis peta (jejak ungu mistis) + rute
mp = bpy.data.materials.new('peta_garis'); mp.use_nodes=True
_p=mp.node_tree.nodes.get('Principled BSDF'); _p.inputs['Base Color'].default_value=(0.42,0.30,0.52,1); _p.inputs['Roughness'].default_value=0.7
import math as _m
for (gx,gy,sx,sy) in [(-0.1,0.08,0.34,0.014),(0.06,-0.05,0.26,0.014),(0.0,0.0,0.014,0.3)]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=(gx,gy,0.45)); g=bpy.context.active_object; g.scale=(sx,sy,0.012); g.rotation_euler=(math.radians(-14),0,math.radians(6)); g.data.materials.append(mp)
# titik tujuan (bercahaya)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0.16,-0.12,0.48)); obj=bpy.context.active_object
''' + emat('peta_titik',(150,110,210),strength=1.0,rough=0.4) + '''
# dua gulungan di sisi (silinder krem sepanjang Y)
for gx in (-0.56,0.56):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.92, location=(gx,0,0.42)); r=bpy.context.active_object; r.rotation_euler=(math.radians(90+(-14)),0,math.radians(6)); bpy.ops.object.shade_smooth()
    r.data.materials.append(bpy.data.materials.get('peta_kertas'))
''',
}

MODELS = {**CROPS, **WEAPONS, **FISH, **ORGANIC, **B_ITEMS, **EXTRA, **EXTRA2}


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
