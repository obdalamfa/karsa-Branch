"""remodel.py — Bangun ulang model mob di Blender (socket 9876), preview clay,
lalu export .obj Y-up ke assets/models (gantikan placeholder kasar).

preview(name): bangun + render clay -> tools/icon3d/new_<name>.png (cek dulu)
export(name) : join semua mesh + export .obj (up_axis='Y') ke assets/models

Pakai:
  python tools/remodel.py preview dewa
  python tools/remodel.py export  dewa
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_rpc import run

ROOT = 'E:/Game Research/Lembah Karsa 3D'
MDIR = ROOT + '/assets/models'
OUTD = ROOT + '/tools/icon3d'
os.makedirs(OUTD.replace('/', os.sep), exist_ok=True)

SCENE_SETUP = '''
import bpy, math, mathutils
sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)
'''

# ─── Build deity: arca Hindu-Jawa berdiri di atas teratai, 4 lengan, mahkota ──
BUILD = {
'dewa': '''
def cyl(r,d,z,rgb=(0.7,0.68,0.66),rx=0,ry=0,x=0,y=0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=(x,y,z)); o=bpy.context.active_object
    o.rotation_euler=(rx,ry,0); bpy.ops.object.shade_smooth(); return o
def cone(r1,r2,d,z,x=0,y=0,rx=0,ry=0):
    bpy.ops.mesh.primitive_cone_add(radius1=r1,radius2=r2,depth=d,location=(x,y,z)); o=bpy.context.active_object
    o.rotation_euler=(rx,ry,0); return o
def sph(r,z,x=0,y=0,sx=1,sy=1,sz=1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r,location=(x,y,z)); o=bpy.context.active_object
    o.scale=(sx,sy,sz); bpy.ops.object.shade_smooth(); return o
# alas teratai
cyl(0.62,0.14,0.07)
for i in range(10):
    a=math.radians(i*36); cone(0.16,0.0,0.26, 0.12, x=math.cos(a)*0.5, y=math.sin(a)*0.5, rx=math.radians(70), ry=a)
# jubah bawah (dhoti) kerucut
cone(0.5,0.30,0.92, 0.62)
# pinggang
cyl(0.30,0.16,1.12)
# torso meruncing
cone(0.34,0.24,0.62,1.45)
# dada/bahu
sph(0.36,1.62, sz=0.62)
# leher + kepala
cyl(0.09,0.12,1.86)
sph(0.21,2.04)
# mahkota jata-mukuta bertingkat
cone(0.2,0.13,0.2,2.26); cone(0.13,0.07,0.18,2.42); cone(0.07,0.0,0.16,2.56)
# halo di belakang kepala (cincin, bidang X-Z)
bpy.ops.mesh.primitive_torus_add(major_radius=0.42, minor_radius=0.03, location=(0,0.12,2.04))
h=bpy.context.active_object; h.rotation_euler=(math.radians(90),0,0)
# 4 lengan dari bahu (x=+-0.34, z=1.6)
def arm(side, raised):
    sx=0.34*side
    if raised:
        # lengan terangkat: bahu->atas-samping memegang atribut
        cyl(0.07,0.5,1.78, x=sx*1.5, y=0, rx=0, ry=math.radians(40*side))
        sph(0.1, 2.0, x=sx*2.1)           # tangan + atribut (cakra/bola)
    else:
        # lengan turun di sisi
        cyl(0.08,0.62,1.32, x=sx*1.25, ry=math.radians(12*side))
        sph(0.09,1.02, x=sx*1.4)          # tangan bawah
for s in (1,-1):
    arm(s, True); arm(s, False)
''',

# ─── Build petapa: sosok berjubah, janggut, sanggul, tongkat, tasbih ──
'petapa': '''
def cyl(r,d,z,x=0,y=0,rx=0,ry=0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r,depth=d,location=(x,y,z)); o=bpy.context.active_object
    o.rotation_euler=(rx,ry,0); bpy.ops.object.shade_smooth(); return o
def cone(r1,r2,d,z,x=0,y=0,rx=0,ry=0):
    bpy.ops.mesh.primitive_cone_add(radius1=r1,radius2=r2,depth=d,location=(x,y,z)); o=bpy.context.active_object
    o.rotation_euler=(rx,ry,0); return o
def sph(r,z,x=0,y=0,sx=1,sy=1,sz=1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r,location=(x,y,z)); o=bpy.context.active_object
    o.scale=(sx,sy,sz); bpy.ops.object.shade_smooth(); return o
# jubah panjang (kerucut lebar) + sedikit alas
cone(0.46,0.0,0.06,0.03)             # tepi jubah menyentuh tanah
cone(0.44,0.22,1.2,0.62)             # badan jubah
# bahu/dada
sph(0.26,1.28, sz=0.6)
# leher + kepala
cyl(0.07,0.1,1.46)
sph(0.18,1.62)
# sanggul/topknot
sph(0.1,1.82, sz=0.9)
# janggut (kerucut ke bawah dari wajah)
cone(0.14,0.0,0.34,1.42, y=-0.16, rx=math.radians(8))
# dua lengan turun memegang (tangan di depan perut)
for s in (1,-1):
    cyl(0.06,0.5,1.16, x=0.26*s, ry=math.radians(18*s))
    sph(0.07,0.95, x=0.13*s, y=-0.12)     # tangan bertemu di depan
# tongkat di sisi kanan
cyl(0.028,1.5,0.78, x=0.5, y=-0.05)
sph(0.06,1.54, x=0.5, y=-0.05)            # kepala tongkat
''',

# ─── Build rumah panggung Indonesia: tiang, lantai, dinding, atap limasan ──
'rumah': '''
import math
def box(sx,sy,sz,z,x=0,y=0,rx=0,rz=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x,y,z)); o=bpy.context.active_object
    o.scale=(sx,sy,sz); o.rotation_euler=(rx,0,rz); return o
def cyl(r,d,z,x=0,y=0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r,depth=d,location=(x,y,z)); o=bpy.context.active_object
    bpy.ops.object.shade_smooth(); return o
# tiang panggung (6)
for ix in (-0.62,0,0.62):
    for iy in (-0.5,0.5):
        cyl(0.075,1.0,0.5, x=ix, y=iy)
# lantai panggung
box(0.78,0.66,0.07,1.04)
# dinding badan rumah
box(0.7,0.58,0.5,1.55)
# pintu (muka -Y)
box(0.16,0.04,0.32,1.42, y=-0.6)
# tangga (3 anak) ke pintu
for i in range(3):
    box(0.18,0.07,0.05, 0.2+i*0.18, y=-0.74-i*0.12)
# jendela kiri-kanan (muka -Y)
for sx in (-0.4,0.4):
    box(0.12,0.04,0.16,1.6, x=sx, y=-0.59)
# atap limasan (hip) = piramida 4-sisi melebar + tritisan
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.96, radius2=0.18, depth=0.6, location=(0,0,2.16))
r=bpy.context.active_object; r.rotation_euler=(0,0,math.radians(45)); r.scale=(1.0,0.86,1.0)
# tritisan (lapisan tepi atap)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.02, radius2=0.9, depth=0.08, location=(0,0,1.9))
r2=bpy.context.active_object; r2.rotation_euler=(0,0,math.radians(45)); r2.scale=(1.0,0.86,1.0)
# bubungan kecil di puncak
box(0.5,0.06,0.05,2.5)
''',

# ─── Build genderuwo: raksasa berotot berbulu, lengan besar, kepala besar ──
'genderuwo': '''
def cyl(r,d,z,x=0,y=0,rx=0,ry=0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r,depth=d,location=(x,y,z)); o=bpy.context.active_object
    o.rotation_euler=(rx,ry,0); bpy.ops.object.shade_smooth(); return o
def sph(r,z,x=0,y=0,sx=1,sy=1,sz=1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r,location=(x,y,z)); o=bpy.context.active_object
    o.scale=(sx,sy,sz); bpy.ops.object.shade_smooth(); return o
# kaki pendek tebal
for s in (1,-1):
    cyl(0.18,0.7,0.35, x=0.22*s)
    sph(0.2,0.08, x=0.22*s, sz=0.6)       # telapak
# torso besar (badan gempal)
sph(0.5,1.1, sx=1.05, sy=0.8, sz=1.0)
# perut buncit
sph(0.42,0.82, sy=0.85)
# bahu lebar
sph(0.58,1.4, sx=1.2, sy=0.7, sz=0.5)
# lengan besar menggantung
for s in (1,-1):
    cyl(0.16,0.8,1.05, x=0.62*s, ry=math.radians(10*s))
    sph(0.2,0.62, x=0.66*s)               # kepalan tangan
# leher tebal + kepala besar
cyl(0.18,0.12,1.62)
sph(0.34,1.86)
# taring/rahang (kerucut) + dua tanduk kecil
bpy.ops.mesh.primitive_cone_add(radius1=0.34,radius2=0.2,depth=0.18,location=(0,-0.08,1.66));
for s in (1,-1):
    bpy.ops.mesh.primitive_cone_add(radius1=0.06,radius2=0.0,depth=0.22,location=(0.16*s,0.04,2.12)); bpy.context.active_object.rotation_euler=(0,math.radians(12*s),0)
''',
}

PREVIEW_TAIL = '''
# clay material ke semua + frame kamera + render
objs=[o for o in bpy.data.objects if o.type=='MESH']
clay=bpy.data.materials.new('clay'); clay.use_nodes=True
b=clay.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value=(0.72,0.70,0.67,1); b.inputs['Roughness'].default_value=0.6
for o in objs:
    o.data.materials.clear(); o.data.materials.append(clay)
sc.render.resolution_x=300; sc.render.resolution_y=300; sc.render.film_transparent=True
sc.render.image_settings.color_mode='RGBA'
try: sc.eevee.taa_render_samples=24
except Exception: pass
world=bpy.data.worlds.get('World') or bpy.data.worlds.new('World'); sc.world=world; world.use_nodes=True
bgn=world.node_tree.nodes.get('Background')
if bgn: bgn.inputs[0].default_value=(0.32,0.32,0.34,1); bgn.inputs[1].default_value=0.6
bpy.context.view_layer.update()
mn=[1e9]*3; mx=[-1e9]*3
for o in objs:
    for v in o.bound_box:
        w=o.matrix_world @ mathutils.Vector(v)
        for i in range(3): mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=(mn[2]+mx[2])/2
size=max(mx[0]-mn[0],mx[1]-mn[1],mx[2]-mn[2],0.5)
cam_d=bpy.data.cameras.new('C'); cam_d.type='ORTHO'; cam_d.ortho_scale=size*1.4
cam=bpy.data.objects.new('C',cam_d); bpy.context.collection.objects.link(cam)
d=size*2.2; cam.location=(cx+d*0.5, cy-d*0.8, cz+d*0.28)
_dir=mathutils.Vector((cx,cy,cz))-cam.location; cam.rotation_euler=_dir.to_track_quat('-Z','Y').to_euler()
sc.camera=cam
sun_d=bpy.data.lights.new('S','SUN'); sun_d.energy=3.0
sun=bpy.data.objects.new('S',sun_d); bpy.context.collection.objects.link(sun); sun.rotation_euler=(math.radians(52),math.radians(6),math.radians(40))
sc.render.filepath=r"__OUT__"
bpy.ops.render.render(write_still=True)
print('PREVIEW_OK __NAME__ objs=%d' % len(objs))
'''

EXPORT_TAIL = '''
# join semua mesh -> export .obj Y-up
objs=[o for o in bpy.data.objects if o.type=='MESH']
for o in bpy.data.objects: o.select_set(False)
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
bpy.ops.object.join()
m=bpy.context.active_object
bpy.ops.object.shade_smooth()
bpy.ops.wm.obj_export(filepath=r"__OUT__", export_selected_objects=True, up_axis='Y', forward_axis='NEGATIVE_Z', export_materials=False)
print('EXPORT_OK __NAME__ -> __OUT__')
'''


def preview(name):
    out = (OUTD + f'/new_{name}.png').replace('/', os.sep)
    code = SCENE_SETUP + BUILD[name] + PREVIEW_TAIL.replace('__OUT__', out).replace('__NAME__', name)
    print(run(code).strip().splitlines()[-1])


def export(name):
    out = (MDIR + f'/{name if name.startswith("mob_") else "mob_"+name}.obj').replace('/', os.sep)
    code = SCENE_SETUP + BUILD[name] + EXPORT_TAIL.replace('__OUT__', out).replace('__NAME__', name)
    print(run(code).strip().splitlines()[-1])


if __name__ == '__main__':
    act = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    nm = sys.argv[2] if len(sys.argv) > 2 else 'dewa'
    (export if act == 'export' else preview)(nm)
