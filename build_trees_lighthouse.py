import bpy, os, math, mathutils
import numpy as np

# ============================================================
# POHON v2 (skala meter, muted) + MERCUSUAR rusak/jadi — baked.
# pohon_tropis 4.6m | pohon_kelapa 5.2m | pohon_mati 3.2m
# prop_mercusuar_rusak / prop_mercusuar 7.5m
# ============================================================
MAIN = "E:/Game Research/Lembah Karsa 3D/assets/models"
OUT_DIRS = [
    MAIN,
    "E:/Game Research/Lembah Karsa 3D/game/assets/models",
    "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd/assets/models",
]

def mat(name, col, rough=0.9, metal=0.0, emit=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit > 0:
        b.inputs['Emission Color'].default_value = (*col, 1.0)
        b.inputs['Emission Strength'].default_value = emit
    return m

BARK   = mat('T2_Bark',  (0.26, 0.19, 0.12))
BARK_K = mat('T2_BarkK', (0.36, 0.27, 0.16))
DAUN1  = mat('T2_Daun1', (0.18, 0.26, 0.13))
DAUN2  = mat('T2_Daun2', (0.24, 0.31, 0.15))
DAUN3  = mat('T2_Daun3', (0.14, 0.21, 0.11))
PELEPAH= mat('T2_Pelepah',(0.22, 0.30, 0.13))
KELAPA = mat('T2_Buah',  (0.35, 0.27, 0.14))
MATI   = mat('T2_Mati',  (0.22, 0.17, 0.12))
PUTIH  = mat('M2_Putih', (0.72, 0.69, 0.62))
MERAH  = mat('M2_Merah', (0.48, 0.22, 0.16))
KARAT  = mat('M2_Karat', (0.36, 0.24, 0.16), 0.75, 0.25)
KAYU   = mat('M2_Kayu',  (0.34, 0.26, 0.17))
KACA_R = mat('M2_KacaRusak', (0.20, 0.22, 0.23), 0.4)
LAMPU  = mat('M2_Lampu', (1.0, 0.78, 0.35), 0.2, emit=4.0)
BATU   = mat('M2_Batu',  (0.40, 0.38, 0.34))

P = []
def ico(loc, r, m, sub=2, sc=(1,1,1), rot=(0,0,0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.active_object; o.scale = sc; o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(m); P.append(o); return o
def cyl(loc, rad, depth, m, rot=(0,0,0), v=10):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=rad, depth=depth, location=loc)
    o = bpy.context.active_object; o.rotation_euler = rot
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o
def cone(loc, r1, r2, d, m, rot=(0,0,0), v=10):
    bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=r1, radius2=r2, depth=d, location=loc)
    o = bpy.context.active_object; o.rotation_euler = rot
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o
def box(loc, sc, m, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.scale = sc; o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(m); P.append(o); return o
def seg(p0, p1, rb, rt, m, v=8):
    p0 = mathutils.Vector(p0); p1 = mathutils.Vector(p1); d = p1 - p0; L = d.length
    if L < 1e-5: return None
    bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=rb, radius2=rt, depth=L, location=(p0+p1)/2)
    o = bpy.context.active_object
    o.rotation_euler = d.to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o

DONE = []
def finish(name, tex=1024):
    global P
    bpy.ops.object.select_all(action='DESELECT')
    for o in P:
        if o and o.type == 'MESH': o.select_set(True)
    bpy.context.view_layer.objects.active = P[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object; obj.name = name
    bpy.ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    for mtl in obj.data.materials:
        if not mtl or not mtl.node_tree: continue
        nt = mtl.node_tree; b = nt.nodes.get('Principled BSDF')
        if not b: continue
        if 'Lampu' in mtl.name: continue
        base = tuple(b.inputs['Base Color'].default_value)[:3]
        nm = mtl.name
        scale = 18.0 if 'Daun' in nm or 'Pelepah' in nm else 30.0
        tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8.0
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        rp = nt.nodes.new('ShaderNodeValToRGB'); cr = rp.color_ramp
        dk = tuple(min(1,c*0.55) for c in base); br = tuple(min(1,c*1.30) for c in base)
        cr.elements[0].position = 0.33; cr.elements[0].color = (*dk,1)
        cr.elements[1].position = 0.67; cr.elements[1].color = (*br,1)
        nt.links.new(nz.outputs['Fac'], rp.inputs['Fac'])
        nt.links.new(rp.outputs['Color'], b.inputs['Base Color'])
    img = bpy.data.images.new(name + '_baked', tex, tex)
    for mtl in obj.data.materials:
        if not mtl or not mtl.node_tree: continue
        nd = mtl.node_tree.nodes.new('ShaderNodeTexImage'); nd.image = img
        for x in mtl.node_tree.nodes: x.select = False
        nd.select = True; mtl.node_tree.nodes.active = nd
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 1
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=4, use_clear=True)
    n = len(img.pixels); buf = np.empty(n, dtype=np.float32)
    img.pixels.foreach_get(buf); px = buf.reshape(-1,4)
    lum = px[:,:3] @ np.array([0.299,0.587,0.114], np.float32)
    px[:,:3] = np.clip((lum[:,None] + (px[:,:3]-lum[:,None])*0.72)*0.94+0.015, 0, 1)
    img.pixels.foreach_set(px.reshape(-1))
    for d in OUT_DIRS:
        img.filepath_raw = d + "/" + name + "_baked.png"; img.file_format='PNG'; img.save()
    mb = bpy.data.materials.new(name + '_mat'); mb.use_nodes = True
    bn = mb.node_tree.nodes['Principled BSDF']; bn.inputs['Roughness'].default_value = 0.9
    tn = mb.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = img
    mb.node_tree.links.new(tn.outputs['Color'], bn.inputs['Base Color'])
    obj.data.materials.clear(); obj.data.materials.append(mb)
    for p in obj.data.polygons: p.material_index = 0
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for d in OUT_DIRS:
        for att in range(3):
            try:
                bpy.ops.wm.obj_export(filepath=d + "/" + name + ".obj",
                    export_selected_objects=True, export_materials=True,
                    apply_modifiers=True, forward_axis='NEGATIVE_Y', up_axis='Z',
                    path_mode='STRIP')
                break
            except Exception as e:
                print("  retry", att, name, e)
    bpy.data.objects.remove(obj, do_unlink=True)
    DONE.append(name); P = []
    print("DONE:", name)

def clearall():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for im in list(bpy.data.images):
        if im.users == 0: bpy.data.images.remove(im)

clearall()

# ── POHON TROPIS (4.6m, kanopi gumpal organik) ──
seg((0,0,0), (0.06,0.10,2.3), 0.20, 0.115, BARK, v=9)
for i in range(3):                                          # akar banir
    a = i*(2*math.pi/3)+0.4
    seg((math.cos(a)*0.26, math.sin(a)*0.26, 0.02), (math.cos(a)*0.05, math.sin(a)*0.05, 0.55),
        0.075, 0.05, BARK, v=6)
br_tips = []
for i in range(4):                                          # cabang
    a = i*(2*math.pi/4)+0.7
    tip = (math.cos(a)*0.85, math.sin(a)*0.85, 2.6+0.25*(i%2))
    seg((0.05,0.08,2.2), tip, 0.085, 0.04, BARK_K, v=6)
    br_tips.append(tip)
ico((0.05,0.10,3.45), 1.05, DAUN1, 3, (1.25,1.18,0.78))     # kanopi utama
for j,(tx,ty,tz) in enumerate(br_tips):                     # gumpal satelit
    ico((tx*1.05, ty*1.05, tz+0.55), 0.62, (DAUN2 if j%2 else DAUN3), 2, (1.15,1.05,0.72))
ico((-0.5,-0.4,4.05), 0.55, DAUN2, 2, (1.1,1.0,0.7))
ico((0.55,0.35,4.15), 0.50, DAUN3, 2, (1.1,1.0,0.7))
finish('pohon_tropis')

# ── POHON KELAPA (5.2m, batang lengkung) ──
pts = [(0,0,0),(0.14,0.05,1.1),(0.34,0.10,2.2),(0.62,0.13,3.3),(0.95,0.15,4.3)]
for i in range(len(pts)-1):
    seg(pts[i], pts[i+1], 0.14-(i*0.02), 0.12-(i*0.02), BARK_K, v=8)
for i in range(5):                                          # ruas ring
    t=(i+1)/5.0
    bx=0.95*t*t; bz=4.3*t
    cyl((bx*0.92, 0.15*t, bz*0.96), 0.135-(t*0.02), 0.05, BARK)
top=(0.98,0.16,4.42)
for i in range(8):                                          # pelepah melengkung
    a = i*(2*math.pi/8)
    mid=(top[0]+math.cos(a)*1.0, top[1]+math.sin(a)*1.0, top[2]+0.42)
    tip=(top[0]+math.cos(a)*2.0, top[1]+math.sin(a)*2.0, top[2]-0.45)
    seg(top, mid, 0.055, 0.04, PELEPAH, v=5)
    seg(mid, tip, 0.04, 0.008, PELEPAH, v=5)
    ico(mid, 0.30, DAUN2, 2, (1.6, 0.55, 0.16), (0.0, 0.55, a))
    ico(((mid[0]+tip[0])/2,(mid[1]+tip[1])/2,(mid[2]+tip[2])/2), 0.26, DAUN1, 2,
        (1.5, 0.5, 0.13), (0.0, 0.85, a))
for i in range(4):                                          # buah kelapa
    a = i*1.55
    ico((top[0]+math.cos(a)*0.22, top[1]+math.sin(a)*0.22, top[2]-0.18), 0.13, KELAPA, 2)
finish('pohon_kelapa')

# ── POHON MATI (3.2m, ranting gnarled) ──
seg((0,0,0), (0.10,-0.06,1.9), 0.16, 0.07, MATI, v=8)
seg((0.10,-0.06,1.9), (0.42,0.10,2.9), 0.07, 0.015, MATI, v=6)
seg((0.10,-0.06,1.9), (-0.35,-0.25,2.7), 0.06, 0.012, MATI, v=6)
seg((0.05,-0.03,1.3), (0.55,-0.45,2.0), 0.05, 0.010, MATI, v=6)
seg((0.42,0.10,2.9), (0.62,0.35,3.2), 0.018, 0.004, MATI, v=5)
seg((-0.35,-0.25,2.7), (-0.6,-0.2,3.05), 0.015, 0.004, MATI, v=5)
seg((0.0,0.0,0.8), (-0.5,0.35,1.35), 0.045, 0.008, MATI, v=5)
finish('pohon_mati')

# ── MERCUSUAR (menara strip 7.5m) — builder dipakai 2× ──
def mercusuar(broken):
    # fondasi batu
    cyl((0,0,0.25), 1.15, 0.5, BATU, v=14)
    # menara tirus strip merah-putih (5 band)
    for i in range(5):
        z0 = 0.5 + i*1.05
        r  = 0.92 - i*0.115
        col = PUTIH if i % 2 == 0 else MERAH
        cyl((0,0,z0+0.525), r, 1.05, col, v=14)
    # galeri + lampu
    cyl((0,0,5.85), 0.62, 0.12, KARAT, v=12)               # dek galeri
    for i in range(8):                                      # pagar galeri
        a = i*(2*math.pi/8)
        cyl((math.cos(a)*0.56, math.sin(a)*0.56, 6.05), 0.022, 0.36, KARAT, v=5)
    cyl((0,0,6.45), 0.40, 0.62, KACA_R if broken else LAMPU, v=10)   # ruang lampu
    for i in range(4):                                      # rangka kaca
        a = i*(2*math.pi/4)
        box((math.cos(a)*0.39, math.sin(a)*0.39, 6.45), (0.05,0.05,0.62), KARAT)
    cone((0,0,6.95), 0.50, 0.04, 0.45, MERAH, v=12)         # atap kerucut
    if broken:
        # papan kayu menyilang + bekas karat + puing
        box((0, 0.88, 3.2), (1.3, 0.07, 0.16), KAYU, (0, 0, 0.5))
        box((0, 0.88, 3.0), (1.3, 0.07, 0.16), KAYU, (0, 0, -0.5))
        box((0, 0.80, 1.6), (1.1, 0.06, 0.14), KAYU, (0, 0, 0.35))
        ico((0.7, 0.5, 0.55), 0.28, BATU, 2, (1.3, 1.0, 0.6))   # puing
        ico((-0.6, 0.7, 0.52), 0.20, BATU, 2, (1.2, 1.0, 0.55))
        seg((0.3, 0.85, 4.2), (0.3, 1.0, 2.6), 0.05, 0.05, KARAT, v=6)  # bekas tetesan karat
    else:
        ico((0,0,6.45), 0.30, LAMPU, 2)                     # bohlam menyala

mercusuar(broken=True);  finish('prop_mercusuar_rusak')
mercusuar(broken=False); finish('prop_mercusuar')

print("ALL:", ", ".join(DONE))
clearall()
