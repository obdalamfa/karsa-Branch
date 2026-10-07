import bpy, os, math, mathutils, glob
import numpy as np

# ============================================================
# PROPS FARMING v2 — detail papan/bilah/band logam + BAKE tekstur
# (kayu/jerami/goni bernoise, bukan flat). Overwrite prop_*.obj.
# ============================================================
MAIN = "E:/Game Research/Lembah Karsa 3D/assets/models"
OUT_DIRS = [
    MAIN,
    "E:/Game Research/Lembah Karsa 3D/game/assets/models",
    "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd/assets/models",
]

def mat(name, col, rough=0.9, metal=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m

KAYU   = mat('F2_Kayu',   (0.40, 0.30, 0.19))
KAYU_T = mat('F2_KayuTua',(0.30, 0.22, 0.14))
KAYU_L = mat('F2_KayuMuda',(0.48, 0.38, 0.24))
JERAMI = mat('F2_Jerami', (0.58, 0.48, 0.26))
KAIN   = mat('F2_Kain',   (0.44, 0.40, 0.30))
KARAT  = mat('F2_Karat',  (0.38, 0.26, 0.17), 0.7, 0.3)
GONI   = mat('F2_Goni',   (0.50, 0.42, 0.28))
SENG   = mat('F2_Seng',   (0.44, 0.46, 0.47), 0.5, 0.4)
TANAH  = mat('F2_Tanah',  (0.28, 0.22, 0.15))
SAYUR  = mat('F2_Sayur',  (0.34, 0.40, 0.20))
SAYUR2 = mat('F2_Sayur2', (0.55, 0.38, 0.18))

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
def torus(loc, R, r, m, rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot)
    o = bpy.context.active_object
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o

DONE = []
def finish(name, tex=1024):
    """join → UV → noise per-material → bake → export single-mat textured."""
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
    # noise material-specific
    for mtl in obj.data.materials:
        if not mtl or not mtl.node_tree: continue
        nt = mtl.node_tree; b = nt.nodes.get('Principled BSDF')
        if not b: continue
        base = tuple(b.inputs['Base Color'].default_value)[:3]
        nm = mtl.name
        scale = 34.0 if 'Kayu' in nm else (26.0 if 'Jerami' in nm or 'Goni' in nm else 16.0)
        tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8.0
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        rp = nt.nodes.new('ShaderNodeValToRGB'); cr = rp.color_ramp
        dk = tuple(min(1,c*0.55) for c in base); br = tuple(min(1,c*1.28) for c in base)
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
    # mute ringan
    n = len(img.pixels); buf = np.empty(n, dtype=np.float32)
    img.pixels.foreach_get(buf); px = buf.reshape(-1,4)
    lum = px[:,:3] @ np.array([0.299,0.587,0.114], np.float32)
    px[:,:3] = np.clip((lum[:,None] + (px[:,:3]-lum[:,None])*0.72)*0.94+0.015, 0, 1)
    img.pixels.foreach_set(px.reshape(-1))
    for d in OUT_DIRS:
        img.filepath_raw = d + "/" + name + "_baked.png"; img.file_format='PNG'; img.save()
    mb = bpy.data.materials.new(name + '_mat'); mb.use_nodes = True
    bn = mb.node_tree.nodes['Principled BSDF']; bn.inputs['Roughness'].default_value = 0.88
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
    print("PROP v2:", name)

def clearall():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for im in list(bpy.data.images):
        if im.users == 0: bpy.data.images.remove(im)

clearall()

# ── SCARECROW v2 ──
cyl((0,0,0.95), 0.045, 1.9, KAYU)
cyl((0,0,1.45), 0.035, 1.0, KAYU_T, rot=(0,math.pi/2,0))
box((0,0,1.16), (0.34,0.22,0.52), KAIN)
box((0,0,0.92), (0.38,0.24,0.07), KAYU_T)                   # jahitan bawah baju
for s in (1,-1):
    box((s*0.36,0,1.45), (0.34,0.16,0.14), KAIN)
    box((s*0.54,0,1.45), (0.05,0.18,0.16), JERAMI)          # jerami ujung lengan
ico((0,0,1.72), 0.16, GONI, 2, (1,0.95,1.1))
cone((0,0,2.0), 0.32, 0.02, 0.30, JERAMI, v=14)
torus((0,0,1.90), 0.17, 0.022, KAYU_T)                      # tali leher
for s in (1,-1):
    box((s*0.06,0.145,1.74), (0.05,0.01,0.012), KAYU_T)
    box((s*0.06,0.145,1.74), (0.012,0.01,0.05), KAYU_T)     # mata silang X
box((0,0.15,1.66), (0.08,0.01,0.015), MERAH := mat('F2_Merah',(0.50,0.22,0.16)))  # mulut jahit
for i in range(7):
    a = i*(2*math.pi/7)
    cone((math.cos(a)*0.10, math.sin(a)*0.10, 0.86), 0.018, 0.002, 0.24,
         JERAMI, rot=(0.35*math.sin(a), 0.35*math.cos(a), 0), v=5)
finish('prop_scarecrow')

# ── KANDANG AYAM v2 (papan-papan + bilah) ──
for i, px in enumerate((-0.52,-0.17,0.17,0.52)):            # dinding papan vertikal
    box((px,0,0.55), (0.33,1.0,0.9), KAYU if i%2==0 else KAYU_L)
for z in (0.25, 0.85):                                      # bilah horizontal
    box((0,0.51,z), (1.42,0.03,0.07), KAYU_T)
    box((0,-0.51,z), (1.42,0.03,0.07), KAYU_T)
for s in (1,-1):
    box((s*0.37,0,1.14), (0.80,1.14,0.05), SENG, rot=(0, s*0.40, 0))
box((0,0,1.30), (0.06,1.16,0.06), KAYU_T)                   # bubungan
box((0,0.515,0.45), (0.36,0.06,0.42), KAYU_T)
box((0,0.53,0.43), (0.26,0.04,0.32), TANAH)
for s in (1,-1):
    for t in (1,-1):
        cyl((s*0.6, t*0.4, 0.07), 0.055, 0.16, KAYU_T)
cyl((0,0.66,0.20), 0.028, 0.72, KAYU, rot=(1.05,0,0))       # titian miring
for i in range(4):
    box((0, 0.55+i*0.075, 0.06+i*0.075), (0.17,0.022,0.022), KAYU_T)
finish('prop_kandang_ayam')

# ── GEROBAK v2 (papan + roda berjari) ──
box((0,0,0.52), (0.9,1.3,0.14), KAYU)
for i, px in enumerate((-0.30,0.0,0.30)):                   # papan dasar terlihat
    box((px,0,0.60), (0.27,1.28,0.025), KAYU_L if i%2 else KAYU)
for s in (1,-1):
    for j, pz in enumerate((0.62, 0.76)):                   # dinding bilah 2 tingkat
        box((s*0.44,0,pz), (0.04,1.3,0.115), KAYU_T if j%2 else KAYU)
box((0,0.64,0.69), (0.86,0.04,0.26), KAYU_T)
box((0,-0.64,0.69), (0.86,0.04,0.26), KAYU_T)
for s in (1,-1):                                            # roda berjari
    torus((s*0.50,0.12,0.30), 0.26, 0.045, KAYU_T, (0, math.pi/2, 0))
    for k in range(4):
        a = k*(math.pi/4)
        box((s*0.50,0.12,0.30), (0.035,0.50,0.035), KAYU_L,
            rot=(a, math.pi/2*0 if True else 0, 0))
    cyl((s*0.55,0.12,0.30), 0.055, 0.06, KARAT, rot=(0,math.pi/2,0))
for s in (1,-1):
    cyl((s*0.30,-0.95,0.56), 0.03, 0.75, KAYU, rot=(math.pi/2*0.94,0,0))
    ico((s*0.30,-1.28,0.62), 0.045, KAYU_T, 2)              # pegangan ujung
ico((0,0.1,0.74), 0.24, JERAMI, 2, (1.5,2.0,0.62))
for i in range(5):
    a = i*1.25
    cone((math.cos(a)*0.22, 0.1+math.sin(a)*0.3, 0.86), 0.02, 0.002, 0.16,
         JERAMI, rot=(0.5*math.sin(a), 0.4*math.cos(a), 0), v=5)
finish('prop_gerobak')

# ── CANGKUL v2 ──
cyl((0,0,0.55), 0.022, 1.1, KAYU, rot=(0.18,0,0))
cyl((0,0.085,1.02), 0.028, 0.10, KARAT, rot=(0.18,0,0))     # ferrule
box((0,0.12,1.07), (0.05,0.24,0.035), KARAT, rot=(0.55,0,0))
box((0,0.20,1.02), (0.045,0.10,0.02), SENG, rot=(0.55,0,0)) # mata tajam
finish('prop_cangkul')

# ── EMBER v2 ──
cone((0,0,0.17), 0.16, 0.125, 0.34, SENG, v=14)
for z in (0.08, 0.28):
    torus((0,0,z), 0.150 + z*0.03, 0.012, KARAT)            # band logam
cyl((0,0,0.40), 0.012, 0.30, KARAT, rot=(0,math.pi/2,0))
ico((0,0,0.30), 0.115, mat('F2_Air',(0.30,0.36,0.38), 0.2), 2, (1,1,0.1))  # air
finish('prop_ember')

# ── JERAMI v2 ──
cone((0,0,0.58), 0.75, 0.08, 1.16, JERAMI, v=16)
cone((0,0,1.05), 0.40, 0.05, 0.45, mat('F2_JeramiT',(0.50,0.40,0.20)), v=12)
for i in range(10):
    a = i*(2*math.pi/10)
    cone((math.cos(a)*0.58, math.sin(a)*0.58, 0.10), 0.05, 0.004, 0.34,
         JERAMI, rot=(1.0*math.sin(a), 1.0*math.cos(a), 0), v=5)
cyl((0,0,1.24), 0.025, 0.28, KAYU)
finish('prop_jerami')

# ── PETI SAYUR v2 (bilah renggang) ──
box((0,0,0.045), (0.56,0.42,0.05), KAYU_T)                  # alas
for s in (1,-1):                                            # bilah sisi panjang
    for z in (0.12, 0.24, 0.36):
        box((0, s*0.20, z), (0.56,0.035,0.085), KAYU if z!=0.24 else KAYU_L)
for s in (1,-1):                                            # bilah sisi pendek
    for z in (0.12, 0.24, 0.36):
        box((s*0.27, 0, z), (0.035,0.40,0.085), KAYU_T)
for s in (1,-1):                                            # tiang sudut
    for t in (1,-1):
        box((s*0.26, t*0.19, 0.21), (0.045,0.045,0.42), KAYU_T)
for i in range(6):                                          # isi sayur 2 warna
    a = i*1.1
    ico((math.cos(a)*0.14, math.sin(a)*0.11, 0.40), 0.075,
        SAYUR if i%2 else SAYUR2, 2)
finish('prop_peti_sayur')

# ── KARUNG v2 ──
ico((0,0,0.26), 0.24, GONI, 3, (1.0,0.9,1.05))
ico((0,0.18,0.16), 0.10, GONI, 2, (1.3,0.6,0.8))            # lipatan bawah
ico((0,0,0.50), 0.10, GONI, 2, (1.0,1.0,0.55))
torus((0,0,0.52), 0.085, 0.018, KAYU_T)                     # tali ikat
ico((0,0,0.58), 0.065, GONI, 2, (1.0,1.0,0.7))              # jumbai atas
finish('prop_karung')

# ── PAGAR KAYU v2 ──
for x in (-0.85, 0.0, 0.85):
    cyl((x,0,0.45), 0.05, 0.9, KAYU_T, v=8)
    cone((x,0,0.93), 0.05, 0.012, 0.08, KAYU_T, v=8)        # ujung runcing
for z in (0.35, 0.70):
    box((0,0,z), (2.0,0.045,0.085), KAYU, rot=(0,0.012,0))
for x in (-0.42, 0.42):                                     # paku karat
    for z in (0.35, 0.70):
        ico((x,0.035,z), 0.014, KARAT, 1)
finish('prop_pagar_kayu')

print("PROPS v2 DONE:", ", ".join(DONE))
clearall()
print("ALL DONE")
