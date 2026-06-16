"""blender_hud.py — Render bingkai panel HUD 'chrome' 3D via Blender (socket 9876).

Bingkai logam kuningan ber-bevel (pencahayaan nyata → highlight bevel kaya)
+ isi parchment gelap, dirender TOP-DOWN ortho dengan latar transparan →
tekstur panel yang menggantikan panel_chrome.png (PIL).

Pakai: python tools/blender_hud.py        (-> tools/icon3d/panel_chrome3d.png)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_rpc import run

ROOT = 'E:/Game Research/Lembah Karsa 3D'
OUT = ROOT + '/tools/icon3d/panel_chrome3d.png'
os.makedirs((ROOT + '/tools/icon3d').replace('/', os.sep), exist_ok=True)

CODE = r'''
import bpy, math
sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
sc.render.resolution_x = 512; sc.render.resolution_y = 512
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
try: sc.eevee.taa_render_samples = 48
except Exception: pass
# world ambient netral
world = bpy.data.worlds.get('World') or bpy.data.worlds.new('World')
sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value=(0.34,0.34,0.36,1); bg.inputs[1].default_value=0.5

def matn(obj, rgb, rough, metal):
    m = bpy.data.materials.new('m'); m.use_nodes=True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(rgb[0],rgb[1],rgb[2],1)
    b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal
    obj.data.materials.append(m)

# Pelat kuningan (bingkai penuh) — bevel sudut + tepi
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
plate = bpy.context.active_object; plate.scale=(1.0,1.0,0.06)
bpy.ops.object.modifier_add(type='BEVEL')
bv = plate.modifiers['Bevel']; bv.width=0.06; bv.segments=4
matn(plate, (0.82,0.62,0.30), 0.42, 0.0)   # kuningan hangat (non-metalik → warna emas jelas)

# Isi parchment gelap (lebih kecil, sedikit di atas → sisakan border kuningan
# sbg lip ber-bevel = garis kilau). Sengaja gelap pekat.
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.055))
inset = bpy.context.active_object; inset.scale=(0.82,0.82,0.06)
bpy.ops.object.modifier_add(type='BEVEL')
bv2 = inset.modifiers['Bevel']; bv2.width=0.025; bv2.segments=3
matn(inset, (0.085,0.07,0.058), 0.95, 0.0)  # parchment gelap pekat

# Kamera TOP-DOWN ortho
cam_d = bpy.data.cameras.new('Cam'); cam_d.type='ORTHO'; cam_d.ortho_scale=2.18
cam = bpy.data.objects.new('Cam', cam_d); bpy.context.collection.objects.link(cam)
cam.location=(0,0,4); cam.rotation_euler=(0,0,0)
sc.camera = cam

# Sun miring dari kiri-atas → highlight bevel; + sun fill lembut
s1 = bpy.data.lights.new('S1','SUN'); s1.energy=2.4
o1 = bpy.data.objects.new('S1', s1); bpy.context.collection.objects.link(o1)
o1.rotation_euler=(math.radians(38), math.radians(0), math.radians(35))
s2 = bpy.data.lights.new('S2','SUN'); s2.energy=0.8
o2 = bpy.data.objects.new('S2', s2); bpy.context.collection.objects.link(o2)
o2.rotation_euler=(math.radians(20), math.radians(0), math.radians(-150))

sc.render.filepath = r"__OUT__"
bpy.ops.render.render(write_still=True)
print('HUD_RENDERED')
'''.replace('__OUT__', OUT.replace('/', os.sep))

out = run(CODE)
print(out)
