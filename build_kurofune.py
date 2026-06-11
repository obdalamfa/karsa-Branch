import bpy, os, math, mathutils
import numpy as np

# ============================================================
# KAPAL KUROFUNE — "Naga Hitam" Kapten Kuro.
# Referensi: ukiyo-e kapal hitam Commodore Perry — lambung hitam
# trim emas, WAJAH buritan bermata biru, roda dayung, cerobong
# berasap, 3 tiang layar gelap, bendera strip merah-putih.
# Panjang ~16m (sumbu X), siap ditaruh di laut scene beach.
# ============================================================
MAIN = "E:/Game Research/Lembah Karsa 3D/assets/models"
OUT_DIRS = [
    MAIN,
    "E:/Game Research/Lembah Karsa 3D/game/assets/models",
    "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd/assets/models",
]

def mat(name, col, rough=0.85, metal=0.0, emit=0.0):
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

HITAM  = mat('K_Hitam',  (0.07, 0.07, 0.08))
HITAM2 = mat('K_Hitam2', (0.12, 0.11, 0.12))
EMAS   = mat('K_Emas',   (0.62, 0.48, 0.18), 0.45, 0.5)
PUTIH  = mat('K_Putih',  (0.78, 0.76, 0.70))
MERAH  = mat('K_Merah',  (0.55, 0.16, 0.12))
BIRU   = mat('K_Biru',   (0.25, 0.45, 0.62), 0.3)
GELAP  = mat('K_Pupil',  (0.04, 0.03, 0.03))
LAYAR  = mat('K_Layar',  (0.24, 0.23, 0.22))
KAYU   = mat('K_Kayu',   (0.30, 0.22, 0.14))
ASAP   = mat('K_Asap',   (0.35, 0.34, 0.35), 1.0)
GIGI   = mat('K_Gigi',   (0.82, 0.79, 0.72), 0.4)

P = []
def ico(loc, r, m, sub=2, sc=(1,1,1), rot=(0,0,0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.active_object; o.scale = sc; o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(m); P.append(o); return o
def cyl(loc, rad, depth, m, rot=(0,0,0), v=12):
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
def seg(p0, p1, rb, rt, m, v=6):
    p0 = mathutils.Vector(p0); p1 = mathutils.Vector(p1); d = p1 - p0; L = d.length
    if L < 1e-5: return None
    bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=rb, radius2=rt, depth=L, location=(p0+p1)/2)
    o = bpy.context.active_object
    o.rotation_euler = d.to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o
def torus(loc, R, r, m, rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot)
    o = bpy.context.active_object
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for im in list(bpy.data.images):
    if im.users == 0: bpy.data.images.remove(im)

# ── LAMBUNG (haluan di +X, buritan di -X; waterline z=0) ──
box((0, 0, 1.1), (13.5, 4.4, 2.2), HITAM)                       # badan utama
box((0, 0, 2.35), (14.5, 4.7, 0.35), HITAM2)                    # gunwale deck rim
ico((6.9, 0, 1.35), 1.6, HITAM, 3, (1.6, 1.25, 0.95))           # haluan membulat
ico((-6.9, 0, 1.45), 1.7, HITAM, 3, (1.5, 1.30, 1.05))          # buritan membulat
box((0, 0, 2.55), (12.8, 3.9, 0.10), KAYU)                      # lantai dek
# trim emas sepanjang lambung + ukiran gulung di haluan
box((0, 2.26, 1.95), (14.2, 0.07, 0.16), EMAS)
box((0, -2.26, 1.95), (14.2, 0.07, 0.16), EMAS)
torus((7.4, 1.45, 1.6), 0.45, 0.08, EMAS, (math.pi/2, 0, 0))    # scroll haluan
torus((7.4, -1.45, 1.6), 0.45, 0.08, EMAS, (math.pi/2, 0, 0))
# buih ombak putih waterline
for i in range(7):
    bx = -6.0 + i*2.0
    ico((bx, 2.30, 0.18), 0.38, PUTIH, 2, (1.5, 0.35, 0.5))
    ico((bx, -2.30, 0.18), 0.38, PUTIH, 2, (1.5, 0.35, 0.5))
# haluan naik + cula emas (seperti ukiyo-e)
seg((7.5, 0, 1.8), (9.6, 0, 3.4), 0.42, 0.10, HITAM, v=8)
seg((9.4, 0, 3.3), (11.2, 0, 4.15), 0.10, 0.012, EMAS, v=7)     # cula/bowsprit
# wajah kecil haluan (mata putih)
for s in (1, -1):
    ico((8.0, s*0.75, 2.45), 0.22, PUTIH, 2)
    ico((8.12, s*0.75, 2.50), 0.10, GELAP, 1)

# ── RUMAH BURITAN + WAJAH BESAR (ikon ukiyo-e) ──
box((-6.4, 0, 3.3), (3.2, 4.0, 1.8), HITAM2)                    # kastil buritan
box((-6.4, 0, 4.25), (3.5, 4.3, 0.25), EMAS)                    # mahkota emas
ico((-7.9, 0, 3.3), 1.45, HITAM, 3, (0.8, 1.35, 1.15))          # wajah membulat
for s in (1, -1):                                                # mata biru besar
    ico((-8.55, s*0.62, 3.55), 0.34, PUTIH, 2, (0.55, 1.0, 1.0))
    ico((-8.72, s*0.62, 3.55), 0.20, BIRU, 2, (0.5, 1.0, 1.0))
    ico((-8.82, s*0.62, 3.55), 0.09, GELAP, 1)
ico((-8.75, 0, 3.05), 0.42, GELAP, 2, (0.5, 1.3, 0.55))         # mulut menyeringai
for gx in (-0.45, -0.15, 0.15, 0.45):                            # gigi
    box((-8.85, gx, 3.12), (0.10, 0.16, 0.14), GIGI)
box((-6.4, 0, 2.9), (3.0, 3.6, 0.08), EMAS)                     # plakat emas
# jendela kabin emas
for wy in (-1.2, 0.0, 1.2):
    box((-5.2, wy, 3.4), (0.10, 0.5, 0.5), EMAS)

# ── RODA DAYUNG (paddle wheel) kiri-kanan tengah ──
for s in (1, -1):
    torus((0.8, s*2.55, 1.0), 1.35, 0.16, HITAM2, (0, math.pi/2, 0))
    torus((0.8, s*2.55, 1.0), 0.55, 0.10, EMAS, (0, math.pi/2, 0))   # hub spiral emas
    for k in range(6):
        a = k*(math.pi/3)
        box((0.8, s*2.55, 1.0), (0.10, 0.16, 2.5), KAYU, (a, 0, 0))
    # rumah roda setengah lingkar
    box((0.8, s*2.85, 2.45), (3.1, 0.5, 0.9), HITAM)
    box((0.8, s*2.85, 2.95), (2.6, 0.45, 0.35), EMAS)

# ── CEROBONG + ASAP ──
cyl((2.6, 0, 4.5), 0.55, 3.6, HITAM, rot=(0, -0.06, 0))
torus((2.6, 0, 6.2), 0.56, 0.09, EMAS)
for i, (dx, dz, r) in enumerate([(0.3, 0.7, 0.55), (0.9, 1.5, 0.75), (1.8, 2.3, 0.95)]):
    ico((2.6 - dx, 0.1*i, 6.3 + dz), r, ASAP, 2, (1.2, 1.0, 0.85))

# ── 3 TIANG + LAYAR GELAP + SARANG GAGAK ──
for mx, mh in ((5.0, 8.5), (-0.9, 9.5), (-4.8, 8.0)):
    cyl((mx, 0, mh/2 + 2.4), 0.16, mh, HITAM2, v=8)
    # yard + layar tergulung miring sedikit
    for fy, fw in ((0.72, 3.6), (0.45, 2.9)):
        zy = 2.4 + mh*fy
        cyl((mx, 0, zy), 0.07, fw, KAYU, rot=(math.pi/2, 0, 0), v=6)
        ico((mx, 0, zy - 0.22), 0.30, LAYAR, 2, (0.30, fw/2*0.52, 0.28))
    cyl((mx, 0, 2.4 + mh - 0.5), 0.30, 0.35, KAYU, v=8)          # crow nest
    cone((mx, 0, 2.4 + mh + 0.25), 0.06, 0.01, 0.5, MERAH, v=5)  # pennant
# rigging tali
for (x0, z0, x1, z1) in ((5.0, 10.6, 9.0, 3.2), (-0.9, 11.6, 5.0, 10.4),
                          (-4.8, 10.1, -0.9, 11.4), (-4.8, 10.1, -7.8, 4.4)):
    seg((x0, 0, z0), (x1, 0, z1), 0.022, 0.022, HITAM2, v=4)

# ── BENDERA STRIP MERAH-PUTIH di buritan ──
cyl((-8.6, 0, 5.6), 0.06, 2.6, KAYU, v=6)
for i in range(4):
    col = MERAH if i % 2 == 0 else PUTIH
    box((-9.35, 0, 6.55 - i*0.22), (1.30, 0.04, 0.22), col)

# ── JOIN + BAKE + EXPORT ──
bpy.ops.object.select_all(action='DESELECT')
for o in P:
    if o and o.type == 'MESH': o.select_set(True)
bpy.context.view_layer.objects.active = P[0]
bpy.ops.object.join()
obj = bpy.context.active_object; obj.name = 'Kurofune'
bpy.ops.object.shade_smooth()
print(f"Kurofune: {len(obj.data.vertices)}v {len(obj.data.polygons)}f")

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.012)
bpy.ops.object.mode_set(mode='OBJECT')
for mtl in obj.data.materials:
    if not mtl or not mtl.node_tree: continue
    nt = mtl.node_tree; b = nt.nodes.get('Principled BSDF')
    if not b: continue
    base = tuple(b.inputs['Base Color'].default_value)[:3]
    scale = 26.0 if 'Hitam' in mtl.name or 'Kayu' in mtl.name else 14.0
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 7.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); cr = rp.color_ramp
    dk = tuple(min(1,c*0.62) for c in base); br = tuple(min(1,c*1.30) for c in base)
    cr.elements[0].position = 0.34; cr.elements[0].color = (*dk,1)
    cr.elements[1].position = 0.66; cr.elements[1].color = (*br,1)
    nt.links.new(nz.outputs['Fac'], rp.inputs['Fac'])
    nt.links.new(rp.outputs['Color'], b.inputs['Base Color'])
img = bpy.data.images.new('prop_kurofune_baked', 2048, 2048)
for mtl in obj.data.materials:
    if not mtl or not mtl.node_tree: continue
    nd = mtl.node_tree.nodes.new('ShaderNodeTexImage'); nd.image = img
    for x in mtl.node_tree.nodes: x.select = False
    nd.select = True; mtl.node_tree.nodes.active = nd
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 1
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=5, use_clear=True)
n = len(img.pixels); buf = np.empty(n, dtype=np.float32)
img.pixels.foreach_get(buf); px = buf.reshape(-1,4)
lum = px[:,:3] @ np.array([0.299,0.587,0.114], np.float32)
px[:,:3] = np.clip((lum[:,None] + (px[:,:3]-lum[:,None])*0.74)*0.95+0.012, 0, 1)
img.pixels.foreach_set(px.reshape(-1))
for d in OUT_DIRS:
    img.filepath_raw = d + "/prop_kurofune_baked.png"; img.file_format='PNG'; img.save()
mb = bpy.data.materials.new('prop_kurofune_mat'); mb.use_nodes = True
bn = mb.node_tree.nodes['Principled BSDF']; bn.inputs['Roughness'].default_value = 0.82
tn = mb.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = img
mb.node_tree.links.new(tn.outputs['Color'], bn.inputs['Base Color'])
obj.data.materials.clear(); obj.data.materials.append(mb)
for p in obj.data.polygons: p.material_index = 0
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
bpy.context.view_layer.objects.active = obj
for d in OUT_DIRS:
    for att in range(3):
        try:
            bpy.ops.wm.obj_export(filepath=d + "/prop_kurofune.obj",
                export_selected_objects=True, export_materials=True,
                apply_modifiers=True, forward_axis='NEGATIVE_Y', up_axis='Z',
                path_mode='STRIP')
            break
        except Exception as e:
            print("  retry", att, e)
print("KUROFUNE exported")

# render preview
bpy.ops.mesh.primitive_plane_add(size=80, location=(0,0,-0.05))
gp = bpy.context.active_object
gm = bpy.data.materials.new('Laut'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.10,0.16,0.20,1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.25
gp.data.materials.append(gm)
for loc, e, c in [((14,-16,14),2600,(1,0.94,0.85)),((-16,-10,10),1300,(0.55,0.65,1.0)),((0,14,10),900,(1,0.7,0.5))]:
    bpy.ops.object.light_add(type='POINT', location=loc); l = bpy.context.active_object
    l.data.energy = e; l.data.color = c
bpy.ops.object.light_add(type='SUN'); s = bpy.context.active_object
s.data.energy = 0.9; s.rotation_euler = (0.5, 0.12, -0.4)
def look_at(cam, t):
    d = mathutils.Vector(t) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.09,0.10,0.13,1)
sc.render.resolution_x = 1500; sc.render.resolution_y = 850
bpy.ops.object.camera_add(location=(13, -17, 7.5)); cam = bpy.context.active_object
look_at(cam, (-0.5, 0, 3.4)); cam.data.lens = 42; sc.camera = cam
sc.render.filepath = "E:/Game Research/Lembah Karsa 3D/kurofune_preview.png"
bpy.ops.render.render(write_still=True)
print("PREVIEW done")
