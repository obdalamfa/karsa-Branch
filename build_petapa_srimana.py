import bpy, os, math, mathutils

# ============================================================
# PETAPA SRIMANA — "Petapa Emas penjaga inti langit" (NPC swarga).
# Pertapa bermeditasi duduk sila di atas bantalan teratai:
# kulit emas, jubah saffron, janggut putih, tasbih, halo emas.
# Atomik: build -> export multi-mat -> save blend -> bake -> re-export -> render.
# ============================================================
WT = "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd"
EXPORT_DIRS = [WT + "/game/assets/models", WT + "/assets/models"]
for d in EXPORT_DIRS:
    os.makedirs(d, exist_ok=True)

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for m in list(bpy.data.materials):
    if m.users == 0: bpy.data.materials.remove(m)
for im in list(bpy.data.images):
    if im.users == 0: bpy.data.images.remove(im)

def mat(name, col, rough=0.7, metal=0.0, emit=0.0):
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

M_kulit  = mat('PS_KulitEmas', (0.88, 0.66, 0.28), 0.48, metal=0.40)
M_jubah  = mat('PS_Jubah',     (0.75, 0.38, 0.08), 0.88)
M_jubah2 = mat('PS_JubahTua',  (0.55, 0.26, 0.05), 0.92)
M_sash   = mat('PS_Selempang', (0.93, 0.80, 0.35), 0.38, metal=0.55)
M_rambut = mat('PS_Janggut',   (0.93, 0.91, 0.86), 0.95)
M_mata   = mat('PS_Mata',      (0.10, 0.06, 0.03), 0.6)
M_tasbih = mat('PS_Tasbih',    (0.46, 0.10, 0.08), 0.45)
M_halo   = mat('PS_Halo',      (1.0, 0.85, 0.40), 0.2, emit=3.5)
M_lotus  = mat('PS_Lotus',     (0.90, 0.58, 0.72), 0.75)
M_lotus2 = mat('PS_LotusMuda', (0.97, 0.78, 0.85), 0.70)
M_alas   = mat('PS_Alas',      (0.62, 0.48, 0.18), 0.45, metal=0.45)

P = []
def ico(loc, r, m, sub=3, sc=(1,1,1), rot=(0,0,0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.active_object; o.scale = sc; o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(m); P.append(o); return o
def cyl(loc, rad, depth, m, rot=(0,0,0), v=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=rad, depth=depth, location=loc)
    o = bpy.context.active_object; o.rotation_euler = rot
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o
def cone(loc, r1, r2, d, m, rot=(0,0,0), v=8):
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
def torus(loc, R, r, m, rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot)
    o = bpy.context.active_object
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o

# ── ALAS TERATAI ──────────────────────────────────────────────
cyl((0,0,0.06), 0.60, 0.12, M_alas)                       # dasar emas
for i in range(10):                                        # kelopak luar
    a = i * (2*math.pi/10)
    ico((math.cos(a)*0.52, math.sin(a)*0.52, 0.14), 0.15, M_lotus,
        2, (1.0, 2.1, 0.45), (0.32, 0, a - math.pi/2))
for i in range(8):                                         # kelopak dalam
    a = i * (2*math.pi/8) + math.pi/8
    ico((math.cos(a)*0.34, math.sin(a)*0.34, 0.20), 0.11, M_lotus2,
        2, (1.0, 1.9, 0.42), (0.45, 0, a - math.pi/2))
cyl((0,0,0.26), 0.38, 0.10, M_jubah2)                      # bantal duduk

# ── KAKI BERSILA (terbungkus jubah) ──────────────────────────
seg((0.30,-0.04,0.38), (-0.27, 0.20, 0.36), 0.105, 0.075, M_jubah)
seg((-0.30,-0.04,0.38), (0.27, 0.20, 0.36), 0.105, 0.075, M_jubah)
ico((0.27, 0.19, 0.37), 0.065, M_kulit, 2)                 # telapak kaki kiri
ico((-0.27, 0.19, 0.37), 0.065, M_kulit, 2)                # telapak kaki kanan
ico((0, 0.03, 0.45), 0.34, M_jubah, 3, (1.22, 1.10, 0.55)) # pangkuan jubah

# ── BADAN ─────────────────────────────────────────────────────
ico((0, -0.01, 0.80), 0.30, M_jubah, 3, (1.0, 0.80, 1.30)) # torso berjubah
ico((0, 0.15, 0.90), 0.17, M_kulit, 3, (0.88, 0.55, 1.05)) # dada terbuka
seg((0.21, 0.18, 1.04), (-0.20, 0.15, 0.56), 0.055, 0.055, M_sash)  # selempang emas

# Bahu
ico((0.27, 0.0, 1.02), 0.115, M_jubah, 2)
ico((-0.27, 0.0, 1.02), 0.115, M_jubah, 2)

# Lengan telanjang (tangan di lutut)
for s in (1, -1):
    seg((s*0.29, 0.02, 1.00), (s*0.34, 0.15, 0.70), 0.075, 0.062, M_kulit)   # lengan atas
    seg((s*0.34, 0.15, 0.70), (s*0.24, 0.26, 0.48), 0.060, 0.048, M_kulit)   # lengan bawah
    ico((s*0.23, 0.28, 0.46), 0.068, M_kulit, 2, (1.0, 1.15, 0.7))           # tangan di lutut

# ── TASBIH (kalung manik V di dada) ───────────────────────────
for s in (1, -1):
    for i in range(5):
        t = i / 4.0
        bx = s * (0.13 * (1-t))
        by = 0.165 + 0.075 * t
        bz = 1.05 - 0.25 * t
        ico((bx, by, bz), 0.023, M_tasbih, 1)
ico((0, 0.245, 0.78), 0.032, M_sash, 1)                    # liontin emas

# ── KEPALA ────────────────────────────────────────────────────
cyl((0, 0.0, 1.17), 0.085, 0.13, M_kulit)                  # leher
ico((0, 0.02, 1.33), 0.17, M_kulit, 4, (1.0, 0.95, 1.10))  # kepala botak emas
for s in (1, -1):                                          # telinga panjang (gaya arca)
    ico((s*0.165, 0.02, 1.28), 0.045, M_kulit, 2, (0.55, 0.8, 1.6))
ico((0, -0.02, 1.52), 0.075, M_rambut, 2, (1, 1, 1.25))    # gelung rambut putih
cyl((0, -0.02, 1.46), 0.058, 0.03, M_sash)                 # ikat gelung emas

# Wajah damai
for s in (1, -1):
    box((s*0.068, 0.155, 1.345), (0.055, 0.018, 0.011), M_mata)    # mata terpejam
    box((s*0.068, 0.158, 1.385), (0.060, 0.016, 0.018), M_rambut)  # alis putih
ico((0, 0.185, 1.31), 0.030, M_kulit, 2, (0.8, 0.9, 1.1))  # hidung
ico((0, 0.172, 1.405), 0.018, M_halo, 1)                   # tilaka (titik dahi)
for s in (1, -1):                                          # kumis putih
    cone((s*0.035, 0.185, 1.255), 0.018, 0.003, 0.10, M_rambut, (0.35, 0, s*0.5), 5)
cone((0, 0.165, 1.02), 0.085, 0.012, 0.46, M_rambut, (0.22, 0, 0))   # janggut panjang
cone((0.05, 0.16, 1.06), 0.04, 0.008, 0.30, M_rambut, (0.20, 0, 0.18), 5)
cone((-0.05, 0.16, 1.06), 0.04, 0.008, 0.30, M_rambut, (0.20, 0, -0.18), 5)

# ── HALO EMAS (di belakang kepala) ────────────────────────────
torus((0, -0.10, 1.34), 0.225, 0.018, M_halo, (math.pi/2, 0, 0))

# ── JOIN ──────────────────────────────────────────────────────
bpy.ops.object.select_all(action='DESELECT')
for o in P:
    if o and o.type == 'MESH': o.select_set(True)
bpy.context.view_layer.objects.active = P[0]
bpy.ops.object.join()
obj = bpy.context.active_object; obj.name = 'PetapaSrimana'
bpy.ops.object.shade_smooth()
print(f"Built: {len(obj.data.vertices)}v {len(obj.data.polygons)}f, {len(obj.data.materials)} mats")

# ── EXPORT multi-material (fallback) + SAVE BLEND sumber ──────
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
bpy.context.view_layer.objects.active = obj
for d in EXPORT_DIRS:
    bpy.ops.wm.obj_export(filepath=d + "/petapa_srimana.obj", export_selected_objects=True,
        export_materials=True, apply_modifiers=True, forward_axis='NEGATIVE_Y', up_axis='Z')
bpy.ops.wm.save_as_mainfile(filepath="E:/Game Research/Lembah Karsa 3D/petapa_srimana.blend")
print("Multi-mat OBJ exported + blend saved")

# ── BAKE: noise kain di jubah saja, lalu re-export bertekstur ─
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

def add_cloth(mtl, scale=18.0):
    nt = mtl.node_tree; b = nt.nodes.get('Principled BSDF')
    if not b: return
    base = tuple(b.inputs['Base Color'].default_value)[:3]
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    dark = tuple(min(1, c*0.55) for c in base); brt = tuple(min(1, c*1.30) for c in base)
    cr.elements[0].position = 0.34; cr.elements[0].color = (*dark, 1)
    cr.elements[1].position = 0.66; cr.elements[1].color = (*brt, 1)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])

for mtl in obj.data.materials:
    if mtl and ('Jubah' in mtl.name or 'Janggut' in mtl.name):
        add_cloth(mtl)

img = bpy.data.images.new('petapa_srimana_baked', 1024, 1024)
for mtl in obj.data.materials:
    if not mtl or not mtl.node_tree: continue
    node = mtl.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img
    for nd in mtl.node_tree.nodes: nd.select = False
    node.select = True; mtl.node_tree.nodes.active = node

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 1
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=4, use_clear=True)
for d in EXPORT_DIRS:
    img.filepath_raw = d + "/petapa_srimana_baked.png"; img.file_format = 'PNG'; img.save()

mb = bpy.data.materials.new('petapa_srimana_mat'); mb.use_nodes = True
bn = mb.node_tree.nodes['Principled BSDF']
bn.inputs['Roughness'].default_value = 0.55
bn.inputs['Metallic'].default_value = 0.25
tn = mb.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = img
mb.node_tree.links.new(tn.outputs['Color'], bn.inputs['Base Color'])
obj.data.materials.clear(); obj.data.materials.append(mb)
for p in obj.data.polygons: p.material_index = 0
for d in EXPORT_DIRS:
    img.filepath_raw = d + "/petapa_srimana_baked.png"
    for attempt in range(3):
        try:
            bpy.ops.wm.obj_export(filepath=d + "/petapa_srimana.obj", export_selected_objects=True,
                export_materials=True, apply_modifiers=True, forward_axis='NEGATIVE_Y',
                up_axis='Z', path_mode='STRIP')
            break
        except Exception as e:
            print("  export retry", attempt, d, ":", e)
print("BAKED + exported")

# ── RENDER PREVIEW ────────────────────────────────────────────
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,-0.01))
gp = bpy.context.active_object
gm = bpy.data.materials.new('PS_Gnd'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.10,0.10,0.12,1)
gp.data.materials.append(gm)
for loc, e, c in [((2.5,3.5,2.6),130,(1,0.92,0.75)),((-2.6,1.5,2.2),70,(0.55,0.65,1)),((0,-2.5,2.0),60,(1,0.8,0.55))]:
    bpy.ops.object.light_add(type='POINT', location=loc); l = bpy.context.active_object
    l.data.energy = e; l.data.color = c
bpy.ops.object.light_add(type='SUN'); s = bpy.context.active_object
s.data.energy = 0.7; s.rotation_euler = (0.5, 0.1, 2.6)
def look_at(cam, t):
    d = mathutils.Vector(t) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.07,0.075,0.10,1)
sc.render.resolution_x = 760; sc.render.resolution_y = 980
bpy.ops.object.camera_add(location=(1.35, 2.3, 1.35)); cam = bpy.context.active_object
look_at(cam, (0, 0.05, 0.75)); cam.data.lens = 50; sc.camera = cam
sc.render.filepath = "E:/Game Research/Lembah Karsa 3D/petapa_srimana_preview.png"
bpy.ops.render.render(write_still=True)
print("PREVIEW done")
