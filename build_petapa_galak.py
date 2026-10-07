import bpy, os, math, mathutils

# ============================================================
# PETAPA SRIMANA — MODE GALAK (fierce form).
# Upgrade Blender dari petapa_model.py (Ursina blocky):
# Iblis-Dewa Bertangan Banyak — wajah Kala menganga, 8 lengan
# (dhyana/lotus/vajra/api), mahkota api, halo prabhavali berapi.
# Ekspor: petapa_srimana_galak.obj (versi kalem tetap petapa_srimana.obj)
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

def mat(name, col, rough=0.6, metal=0.0, emit=0.0):
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

# Palet — mengikuti petapa_model.py
G  = mat('PG_Emas',      (1.00, 0.78, 0.16), 0.38, metal=0.65)
GM = mat('PG_EmasMid',   (0.86, 0.66, 0.20), 0.45, metal=0.55)
GD = mat('PG_EmasGelap', (0.62, 0.46, 0.13), 0.55, metal=0.45)
GW = mat('PG_EmasPutih', (1.00, 0.95, 0.55), 0.30, metal=0.70)
IV = mat('PG_Gading',    (0.94, 0.91, 0.82), 0.40)
ER = mat('PG_MataMerah', (0.85, 0.12, 0.10), 0.15, emit=2.5)
PL = mat('PG_Hitam',     (0.05, 0.02, 0.02), 0.70)
TG = mat('PG_Lidah',     (0.76, 0.14, 0.20), 0.55)
F1 = mat('PG_ApiOranye', (1.00, 0.55, 0.10), 0.25, emit=2.0)
F2 = mat('PG_ApiKuning', (1.00, 0.85, 0.25), 0.22, emit=3.0)
LP = mat('PG_Lotus',     (0.88, 0.58, 0.74), 0.70)
LC = mat('PG_LotusPusat',(0.97, 0.94, 0.82), 0.65)
VJ = mat('PG_Vajra',     (0.82, 0.87, 0.92), 0.25, metal=0.85)
RB = mat('PG_Rubi',      (0.74, 0.12, 0.26), 0.15, emit=0.8)
E3 = mat('PG_MataTiga',  (1.00, 0.97, 0.35), 0.10, emit=6.0)

P = []
def ico(loc, r, m, sub=3, sc=(1,1,1), rot=(0,0,0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.active_object; o.scale = sc; o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(m); P.append(o); return o
def cyl(loc, rad, depth, m, rot=(0,0,0), v=14):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=rad, depth=depth, location=loc)
    o = bpy.context.active_object; o.rotation_euler = rot
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o
def cone(loc, r1, r2, d, m, rot=(0,0,0), v=9):
    bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=r1, radius2=r2, depth=d, location=loc)
    o = bpy.context.active_object; o.rotation_euler = rot
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o
def box(loc, sc, m, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.scale = sc; o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(m); P.append(o); return o
def seg(p0, p1, rb, rt, m, v=10):
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

# ── 1. SINGGASANA LOTUS (3 tier emas + kelopak) ──────────────
cyl((0,0,0.08), 1.05, 0.16, GD, v=18)
cyl((0,0,0.23), 0.90, 0.14, GM, v=18)
cyl((0,0,0.36), 0.74, 0.12, G,  v=18)
for i in range(10):
    a = i * (2*math.pi/10)
    ico((math.cos(a)*0.92, math.sin(a)*0.92, 0.28), 0.18, LP,
        2, (1.0, 2.0, 0.42), (0.30, 0, a - math.pi/2))
for i in range(8):
    a = i * (2*math.pi/8) + math.pi/8
    ico((math.cos(a)*0.62, math.sin(a)*0.62, 0.40), 0.13, LC,
        2, (1.0, 1.8, 0.40), (0.42, 0, a - math.pi/2))
cyl((0,0,0.47), 0.50, 0.10, GD, v=16)        # bantal

# ── 2. KAKI PADMASANA ────────────────────────────────────────
for s in (1, -1):
    seg((s*0.12, 0.05, 0.64), (s*0.54, 0.16, 0.60), 0.17, 0.12, GM)       # paha
    seg((s*0.54, 0.16, 0.58), (-s*0.30, 0.44, 0.54), 0.115, 0.085, GD)    # betis menyilang
    ico((-s*0.30, 0.46, 0.54), 0.10, G, 2, (1.25, 0.85, 0.62))            # telapak kaki

# ── 3. TORSO LEBAR ───────────────────────────────────────────
ico((0, 0.00, 0.74), 0.40, GD, 3, (1.15, 0.85, 0.72))   # pinggul
ico((0, 0.02, 0.97), 0.40, GM, 3, (1.06, 0.82, 0.92))   # perut
ico((0, 0.04, 1.30), 0.44, GM, 3, (1.18, 0.80, 0.95))   # dada
for s in (1, -1):
    ico((s*0.20, 0.30, 1.40), 0.15, G, 2, (1.25, 0.62, 0.95))  # otot dada
torus((0, 0, 0.80), 0.42, 0.05, GW)                      # sabuk
seg((0.27, 0.20, 1.52), (-0.25, 0.24, 0.82), 0.035, 0.035, GW)  # upavita
torus((0, 0.02, 1.52), 0.27, 0.035, GW, (0.28, 0, 0))    # kalung
ico((0, 0.32, 1.38), 0.06, RB, 2)                        # liontin rubi

# ── 4. LEHER ─────────────────────────────────────────────────
cyl((0, 0.0, 1.64), 0.17, 0.16, GD)

# ── 5. KEPALA KALA (galak) ───────────────────────────────────
HZ = 1.94
ico((0, 0.04, HZ), 0.34, GM, 4, (1.25, 0.95, 1.05))      # tengkorak lebar
ico((0, -0.16, HZ), 0.30, GD, 3, (1.08, 0.72, 0.95))     # belakang kepala
box((0, 0.28, HZ+0.17), (0.64, 0.16, 0.13), GD)          # tonjolan dahi (brow ridge)
for s in (1, -1):
    ico((s*0.30, 0.20, HZ-0.10), 0.145, GD, 2, (1.0, 0.9, 1.1))  # pipi gembung
ico((0, 0.30, HZ-0.28), 0.12, GD, 2, (1.45, 0.9, 0.68))  # dagu menonjol

# Mata melotot
for s in (1, -1):
    ico((s*0.17, 0.295, HZ+0.05), 0.085, IV, 3, (1.25, 0.70, 1.25))
    ico((s*0.17, 0.345, HZ+0.05), 0.050, ER, 2)
    ico((s*0.17, 0.375, HZ+0.05), 0.024, PL, 2)
# Alis marah (ujung dalam turun)
for s in (1, -1):
    box((s*0.17, 0.345, HZ+0.155), (0.21, 0.05, 0.05), GD, (0, -s*0.42, 0))
# Hidung lebar + lubang
box((0, 0.37, HZ-0.03), (0.21, 0.10, 0.10), GD)
for s in (1, -1):
    ico((s*0.065, 0.42, HZ-0.045), 0.026, PL, 1)
# Mulut menganga
box((0, 0.335, HZ-0.205), (0.46, 0.11, 0.15), PL)
ico((0, 0.375, HZ-0.235), 0.10, TG, 2, (1.7, 0.75, 0.50))
for gx in (-0.145, -0.05, 0.05, 0.145):                  # gigi atas
    box((gx, 0.385, HZ-0.145), (0.05, 0.045, 0.075), IV)
for s in (1, -1):                                        # taring atas besar (turun, keluar)
    cone((s*0.205, 0.385, HZ-0.255), 0.047, 0.006, 0.22, IV, (math.pi*0.97, -s*0.22, 0), 7)
for s in (1, -1):                                        # taring bawah (naik)
    cone((s*0.135, 0.40, HZ-0.245), 0.035, 0.005, 0.15, IV, (0.10, s*0.12, 0), 7)

# Tanduk iblis melengkung (3 segmen per sisi)
for s in (1, -1):
    seg((s*0.295, 0.06, HZ+0.22), (s*0.45, -0.10, HZ+0.42), 0.072, 0.050, GD)
    seg((s*0.45, -0.10, HZ+0.42), (s*0.55, -0.27, HZ+0.58), 0.050, 0.025, GD)
    seg((s*0.55, -0.27, HZ+0.58), (s*0.59, -0.40, HZ+0.70), 0.025, 0.007, GD)
# Telinga besar + anting
for s in (1, -1):
    ico((s*0.42, 0.02, HZ-0.02), 0.085, GM, 2, (0.55, 0.95, 1.85))
    torus((s*0.435, 0.02, HZ-0.24), 0.062, 0.016, GW, (0, math.pi/2, 0))

# ── 6. MATA KETIGA (trinayana, vertikal menyala) ─────────────
ico((0, 0.355, HZ+0.205), 0.062, E3, 2, (0.55, 0.55, 1.45))
ico((0, 0.395, HZ+0.205), 0.024, PL, 1, (0.55, 0.55, 1.25))

# ── 7. MAHKOTA API ───────────────────────────────────────────
KZ = HZ + 0.42
cyl((0, 0, KZ), 0.355, 0.15, G, v=16)                    # pita mahkota
for mx in (-0.24, -0.12, 0.0, 0.12, 0.24):               # 5 rubi
    my = math.sqrt(max(0.34**2 - mx**2, 0.0)) * 1.0
    box((mx, my+0.015, KZ+0.02), (0.055, 0.045, 0.075), RB)
for i in range(8):                                       # cincin api keliling
    a = i * (2*math.pi/8)
    fc = F2 if i % 2 == 0 else F1
    cone((math.cos(a)*0.275, math.sin(a)*0.275, KZ+0.21), 0.062, 0.005, 0.26, fc,
         (0.18*math.sin(a), -0.18*math.cos(a), 0), 7)
cone((0, 0, KZ+0.38), 0.085, 0.006, 0.52, F1, (0, 0.07, 0), 8)   # api tengah tinggi
ico((0, 0, KZ+0.70), 0.135, F2, 2)                       # bola api puncak
ico((0, 0, KZ+0.80), 0.075, GW, 2)

# ── 8. DELAPAN LENGAN (4 pasang) ─────────────────────────────
HUBX, HUBZ = 0.50, 1.42
ARM_CFG = [   # (sudut dari vertikal-atas, panjang, tebal)
    (148, 0.95, 0.090),   # bawah — dhyana ke lutut
    (100, 0.85, 0.078),   # tengah-bawah — lotus
    ( 65, 0.80, 0.072),   # tengah-atas — vajra
    ( 32, 0.72, 0.065),   # atas — api suci
]
HANDS = {}
for ang_deg, L, t in ARM_CFG:
    ang = math.radians(ang_deg)
    dx, dz = math.sin(ang), math.cos(ang)
    for s in (1, -1):
        hub  = (s*HUBX, 0.02, HUBZ)
        elb  = (s*(HUBX + dx*L*0.55), 0.10, HUBZ + dz*L*0.55)
        hand = (s*(HUBX + dx*L), 0.22, HUBZ + dz*L)
        seg(hub, elb, t, t*0.88, GM)                      # lengan atas
        seg(elb, hand, t*0.88, t*0.70, GM)                # lengan bawah
        ico(elb, t*1.05, GD, 2)                           # siku
        # gelang emas dekat pangkal
        gp = (s*(HUBX + dx*L*0.22), 0.05, HUBZ + dz*L*0.22)
        ico(gp, t*1.25, GW, 2, (1, 1, 0.55))
        ico(hand, t*1.15, G, 2)                           # tangan
        HANDS[(ang_deg, s)] = hand

# Benda sakral per pasang
for s in (1, -1):
    hx, hy, hz = HANDS[(148, s)]                          # dhyana — telapak terbuka
    ico((hx, hy+0.04, hz), 0.085, G, 2, (1.35, 1.1, 0.5))
    ico((hx, hy+0.10, hz+0.05), 0.035, GW, 1)
for s in (1, -1):
    hx, hy, hz = HANDS[(100, s)]                          # lotus pink
    seg((hx, hy, hz), (hx, hy, hz+0.13), 0.022, 0.018, GM)
    ico((hx, hy, hz+0.17), 0.095, LP, 2, (1.15, 1.15, 0.8))
    ico((hx, hy, hz+0.225), 0.048, LC, 2)
for s in (1, -1):
    hx, hy, hz = HANDS[(65, s)]                           # vajra perak
    cyl((hx, hy, hz+0.02), 0.024, 0.24, VJ, v=8)
    ico((hx, hy, hz+0.02), 0.055, VJ, 2)
    for e in (1, -1):
        ico((hx, hy, hz+0.02+e*0.13), 0.045, VJ, 2)
        cone((hx, hy, hz+0.02+e*0.21), 0.035, 0.004, 0.09, VJ, (0 if e>0 else math.pi, 0, 0), 6)
for s in (1, -1):
    hx, hy, hz = HANDS[(32, s)]                           # api suci
    ico((hx, hy, hz+0.04), 0.075, F2, 2)
    cone((hx, hy, hz+0.16), 0.068, 0.006, 0.24, F1, (0, s*0.12, 0), 7)

# ── 9. HALO PRABHAVALI BERAPI (di belakang) ──────────────────
HALO_Y, HALO_Z = -0.44, 2.02
torus((0, HALO_Y, HALO_Z), 0.95, 0.045, G,  (math.pi/2, 0, 0))
torus((0, HALO_Y-0.06, HALO_Z), 1.30, 0.035, GM, (math.pi/2, 0, 0))
for j in range(8):                                       # sinar mandorla
    a = j * (2*math.pi/8)
    box((math.sin(a)*0.85, HALO_Y-0.03, HALO_Z + math.cos(a)*0.85),
        (0.05, 0.04, 0.80), GW, (0, a, 0))
for j in range(16):                                      # api keliling tepi halo
    a = j * (2*math.pi/16)
    fc = F1 if j % 2 == 0 else F2
    cone((math.sin(a)*1.42, HALO_Y-0.06, HALO_Z + math.cos(a)*1.42),
         0.055, 0.004, 0.26, fc, (0, a, 0), 6)

# ── JOIN ─────────────────────────────────────────────────────
bpy.ops.object.select_all(action='DESELECT')
for o in P:
    if o and o.type == 'MESH': o.select_set(True)
bpy.context.view_layer.objects.active = P[0]
bpy.ops.object.join()
obj = bpy.context.active_object; obj.name = 'PetapaSrimanaGalak'
bpy.ops.object.shade_smooth()
print(f"Built: {len(obj.data.vertices)}v {len(obj.data.polygons)}f, {len(obj.data.materials)} mats")

# ── EXPORT multi-mat + SAVE BLEND (sumber) ───────────────────
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
bpy.context.view_layer.objects.active = obj
for d in EXPORT_DIRS:
    bpy.ops.wm.obj_export(filepath=d + "/petapa_srimana_galak.obj", export_selected_objects=True,
        export_materials=True, apply_modifiers=True, forward_axis='NEGATIVE_Y', up_axis='Z')
bpy.ops.wm.save_as_mainfile(filepath="E:/Game Research/Lembah Karsa 3D/petapa_srimana_galak.blend")
print("Multi-mat OBJ + blend saved")

# ── BAKE: ukiran emas (Voronoi) + variasi api ────────────────
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.012)
bpy.ops.object.mode_set(mode='OBJECT')

def add_engrave(mtl, scale=52.0):
    nt = mtl.node_tree; b = nt.nodes.get('Principled BSDF')
    if not b: return
    base = tuple(b.inputs['Base Color'].default_value)[:3]
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Generated'], vor.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    dark = tuple(min(1, c*0.55) for c in base); brt = tuple(min(1, c*1.22) for c in base)
    cr.elements[0].position = 0.0;  cr.elements[0].color = (*dark, 1)
    cr.elements[1].position = 0.06; cr.elements[1].color = (*base, 1)
    e2 = cr.elements.new(0.5); e2.color = (*brt, 1)
    nt.links.new(vor.outputs['Distance'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])

def add_flicker(mtl, scale=14.0):
    nt = mtl.node_tree; b = nt.nodes.get('Principled BSDF')
    if not b: return
    base = tuple(b.inputs['Base Color'].default_value)[:3]
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 7.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    dark = tuple(min(1, c*0.62) for c in base); brt = tuple(min(1, c*1.35) for c in base)
    cr.elements[0].position = 0.32; cr.elements[0].color = (*dark, 1)
    cr.elements[1].position = 0.68; cr.elements[1].color = (*brt, 1)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])

for mtl in obj.data.materials:
    n = mtl.name if mtl else ''
    if 'Emas' in n:
        add_engrave(mtl)
    elif 'Api' in n or 'Lidah' in n:
        add_flicker(mtl)

img = bpy.data.images.new('petapa_srimana_galak_baked', 2048, 2048)
for mtl in obj.data.materials:
    if not mtl or not mtl.node_tree: continue
    node = mtl.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img
    for nd in mtl.node_tree.nodes: nd.select = False
    node.select = True; mtl.node_tree.nodes.active = node

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 1
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=5, use_clear=True)
for d in EXPORT_DIRS:
    img.filepath_raw = d + "/petapa_srimana_galak_baked.png"; img.file_format = 'PNG'; img.save()

mb = bpy.data.materials.new('petapa_srimana_galak_mat'); mb.use_nodes = True
bn = mb.node_tree.nodes['Principled BSDF']
bn.inputs['Roughness'].default_value = 0.45
bn.inputs['Metallic'].default_value = 0.40
tn = mb.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = img
mb.node_tree.links.new(tn.outputs['Color'], bn.inputs['Base Color'])
obj.data.materials.clear(); obj.data.materials.append(mb)
for p in obj.data.polygons: p.material_index = 0
for d in EXPORT_DIRS:
    img.filepath_raw = d + "/petapa_srimana_galak_baked.png"
    for attempt in range(3):
        try:
            bpy.ops.wm.obj_export(filepath=d + "/petapa_srimana_galak.obj", export_selected_objects=True,
                export_materials=True, apply_modifiers=True, forward_axis='NEGATIVE_Y',
                up_axis='Z', path_mode='STRIP')
            break
        except Exception as e:
            print("  export retry", attempt, d, ":", e)
print("BAKED + exported")

# ── RENDER PREVIEW ───────────────────────────────────────────
bpy.ops.mesh.primitive_plane_add(size=30, location=(0,0,-0.01))
gp = bpy.context.active_object
gm2 = bpy.data.materials.new('PG_Gnd'); gm2.use_nodes = True
gm2.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.06,0.05,0.08,1)
gp.data.materials.append(gm2)
for loc, e, c in [((3.5,5.5,3.6),300,(1,0.88,0.65)),((-4.0,2.5,3.0),150,(0.5,0.55,1)),((0,-3.5,2.5),130,(1,0.6,0.3))]:
    bpy.ops.object.light_add(type='POINT', location=loc); l = bpy.context.active_object
    l.data.energy = e; l.data.color = c
bpy.ops.object.light_add(type='SUN'); s = bpy.context.active_object
s.data.energy = 0.5; s.rotation_euler = (0.5, 0.1, 2.7)
def look_at(cam, t):
    d = mathutils.Vector(t) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
sc.cycles.samples = 72; sc.cycles.use_denoising = True
sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.045,0.04,0.07,1)
sc.render.resolution_x = 820; sc.render.resolution_y = 1060
bpy.ops.object.camera_add(location=(2.6, 4.4, 2.3)); cam = bpy.context.active_object
look_at(cam, (0, 0.0, 1.55)); cam.data.lens = 46; sc.camera = cam
sc.render.filepath = "E:/Game Research/Lembah Karsa 3D/petapa_galak_preview.png"
bpy.ops.render.render(write_still=True)
print("PREVIEW done")
