# NPC builder v2 — gaya THE SIMS: proporsi manusia bersih, wajah lengkap,
# rambut bershape, pakaian color-block dengan kerah/sabuk/sepatu.
import bpy, os, math, mathutils
import numpy as np

MAIN = "E:/Game Research/Lembah Karsa 3D/assets/models"
OUT_DIRS = [
    MAIN,
    "E:/Game Research/Lembah Karsa 3D/game/assets/models",
    "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd/assets/models",
]
for _d in OUT_DIRS:
    os.makedirs(_d, exist_ok=True)

# Palet — Sims-clean tapi tetap kalem
SKIN  = (0.72, 0.55, 0.42)
SKIN_L= (0.80, 0.63, 0.49)
SKIN_D= (0.58, 0.43, 0.32)
OLIVE = (0.42, 0.45, 0.27)
RUST  = (0.62, 0.34, 0.20)
TEAL  = (0.26, 0.44, 0.44)
KREM  = (0.78, 0.74, 0.62)
PUTIH = (0.85, 0.84, 0.80)
COKLAT= (0.42, 0.31, 0.20)
BATIK = (0.38, 0.27, 0.16)
NAVY  = (0.22, 0.28, 0.40)
ABU   = (0.52, 0.52, 0.50)
HITAM = (0.12, 0.12, 0.13)
RAMBUT= (0.15, 0.12, 0.09)
R_COK = (0.32, 0.22, 0.13)
UBAN  = (0.70, 0.68, 0.64)
TAN   = (0.66, 0.54, 0.33)
PINK  = (0.72, 0.45, 0.50)
MERAH = (0.55, 0.20, 0.16)

def mat(name, col, rough=0.8, metal=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m

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
def cone(loc, r1, r2, d, m, rot=(0,0,0), v=12):
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

def clear_scene():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for im in list(bpy.data.images):
        if im.users == 0: bpy.data.images.remove(im)

# ════════════════════════════════════════════════════════════
def build_human(spec):
    sid    = spec['id']
    H      = spec['H']
    kid    = spec.get('kid', False)
    skin   = mat('S_Skin_'+sid, spec.get('skin', SKIN), 0.72)
    shirt  = mat('S_Shirt_'+sid, spec['shirt'], 0.86)
    pants  = mat('S_Pants_'+sid, spec['pants'], 0.88)
    shoes  = mat('S_Shoe_'+sid, spec.get('shoe_col', HITAM), 0.65)
    haircl = mat('S_Hair_'+sid, spec.get('hair_col', RAMBUT), 0.88)
    coll   = mat('S_Coll_'+sid, spec.get('collar_col', tuple(min(1,c*1.35) for c in spec['shirt'])), 0.86)
    belt   = mat('S_Belt_'+sid, spec.get('belt_col', COKLAT), 0.7)
    dark   = mat('S_Dark', HITAM, 0.85)
    white  = mat('S_White', (0.92,0.92,0.90), 0.4)
    iris   = mat('S_Iris_'+sid, spec.get('eye_col', (0.25,0.18,0.12)), 0.3)
    lips   = mat('S_Lips_'+sid, (0.58,0.34,0.30), 0.6)

    # ── proporsi Sims: kepala 1/7 (anak 1/5), bahu 2 lebar kepala ──
    headH  = H/5.2 if kid else H/7.0
    headR  = headH * 0.42
    hipZ   = 0.50*H
    waistZ = 0.60*H
    chestZ = 0.74*H
    shZ    = 0.815*H
    neckZ  = 0.845*H
    headZ  = 0.875*H + headR*0.85
    shW    = headR*2.05            # setengah lebar bahu
    bottom = spec.get('bottom', 'pants')
    sleeve = spec.get('sleeve', 'long')

    # ── KAKI + SEPATU ──
    legR = 0.052*H if not kid else 0.060*H
    if bottom == 'pants':
        for s in (1,-1):
            seg((s*0.40*shW, 0, hipZ), (s*0.42*shW, 0.005*H, 0.26*H), legR, legR*0.82, pants)
            seg((s*0.42*shW, 0.005*H, 0.26*H), (s*0.42*shW, 0.01*H, 0.05*H), legR*0.82, legR*0.66, pants)
            ico((s*0.42*shW, 0.030*H, 0.035*H), legR*0.95, shoes, 2, (1.0, 1.85, 0.72))
    elif bottom == 'shorts':
        for s in (1,-1):
            seg((s*0.40*shW, 0, hipZ), (s*0.42*shW, 0.004*H, 0.33*H), legR, legR*0.85, pants)
            seg((s*0.42*shW, 0.004*H, 0.33*H), (s*0.42*shW, 0.01*H, 0.05*H), legR*0.70, legR*0.55, skin)
            ico((s*0.42*shW, 0.030*H, 0.035*H), legR*0.92, shoes, 2, (1.0, 1.8, 0.70))
    else:   # 'skirt' (selutut) / 'long_skirt' (semata kaki)
        lo = 0.32*H if bottom == 'skirt' else 0.07*H
        rb = 0.135*H if bottom == 'skirt' else 0.165*H
        cone((0, 0, (waistZ+lo)/2), rb, 0.100*H, waistZ-lo, pants, v=14)
        if bottom == 'skirt':
            for s in (1,-1):
                seg((s*0.35*shW, 0.005*H, lo), (s*0.36*shW, 0.01*H, 0.05*H), legR*0.62, legR*0.5, skin)
        for s in (1,-1):
            ico((s*0.36*shW, 0.028*H, 0.032*H), legR*0.88, shoes, 2, (1.0, 1.75, 0.68))

    # ── TUBUH (pinggang ramping, dada, bahu) ──
    if bottom in ('pants','shorts'):
        ico((0, 0, hipZ), 0.105*H, pants, 3, (1.30, 0.85, 0.72))
        torus((0, 0, waistZ - 0.012*H), 0.090*H, 0.013*H, belt)   # sabuk
    ico((0, 0, waistZ), 0.088*H, shirt, 3, (1.22, 0.82, 0.86))
    ico((0, 0.004*H, chestZ), 0.105*H, shirt, 3, (1.34, 0.84, 1.02))
    # garis-garis (pelaut) — band tipis melilit torso
    if spec.get('stripes'):
        smat = mat('S_Stripe_'+sid, spec['stripes'], 0.86)
        for sz in (waistZ+0.015*H, (waistZ+chestZ)/2, chestZ-0.005*H):
            torus((0, 0.004*H, sz), 0.103*H, 0.008*H, smat)
    # kerah V
    for s in (1,-1):
        box((s*0.045*H, 0.075*H, shZ - 0.012*H), (0.055*H, 0.012*H, 0.020*H), coll, (0, 0, s*0.5))
    # kancing
    if spec.get('buttons'):
        for bz in (waistZ+0.02*H, (waistZ+chestZ)/2+0.01*H, chestZ):
            ico((0, 0.096*H, bz), 0.008*H, dark, 1)
    # ── BAHU + LENGAN (menggantung natural, sedikit keluar) ──
    armR = 0.034*H
    for s in (1,-1):
        ico((s*shW, 0, shZ), 0.048*H, shirt, 2)
        el  = (s*(shW+0.015*H), 0.008*H, 0.645*H)
        hn  = (s*(shW+0.018*H), 0.030*H, 0.50*H)
        am  = shirt if sleeve == 'long' else skin
        seg((s*shW, 0, shZ), el, armR, armR*0.85, am)
        if sleeve == 'short':
            cyl(((s*shW*1.01), 0.004*H, shZ - 0.055*H), armR*1.12, 0.03*H, shirt)
        seg(el, hn, armR*0.85, armR*0.62, am if sleeve == 'long' else skin)
        if sleeve == 'long':
            cyl((hn[0], hn[1], hn[2]+0.012*H), armR*0.75, 0.015*H, coll)  # manset
        ico(hn, armR*0.78, skin, 2, (1.0, 1.25, 1.1))                     # tangan
        ico((hn[0]+s*armR*0.4, hn[1]+armR*0.5, hn[2]+0.01*H), armR*0.30, skin, 1)  # jempol

    # ── LEHER + KEPALA ──
    cyl((0, 0.004*H, neckZ), 0.030*H, 0.045*H, skin)
    ico((0, 0.004*H, headZ), headR, skin, 4, (0.95, 0.92, 1.10))
    ico((0, 0.012*H, headZ - headR*0.62), headR*0.50, skin, 3, (0.82, 0.78, 0.62))  # rahang/dagu
    for s in (1,-1):   # telinga
        ico((s*headR*0.94, 0.004*H, headZ - headR*0.06), headR*0.20, skin, 2, (0.5, 0.85, 1.0))

    # ── WAJAH (The Sims: mata besar jelas, alis, hidung, bibir) ──
    fy = 0.004*H + headR*0.80
    eyeZ = headZ + headR*0.06
    for s in (1,-1):
        ico((s*headR*0.40, fy, eyeZ), headR*0.195, white, 2, (1.0, 0.55, 1.15))
        ico((s*headR*0.40, fy + headR*0.10, eyeZ), headR*0.105, iris, 2, (1.0, 0.6, 1.0))
        ico((s*headR*0.40, fy + headR*0.16, eyeZ), headR*0.048, dark, 1)
        ico((s*headR*0.33, fy + headR*0.18, eyeZ + headR*0.07), headR*0.026, white, 1)
        # alis
        box((s*headR*0.40, fy + headR*0.06, eyeZ + headR*0.34),
            (headR*0.36, headR*0.07, headR*0.085), haircl, (0, -s*0.18, 0))
    # hidung
    ico((0, fy + headR*0.16, headZ - headR*0.18), headR*0.115, skin, 2, (0.72, 0.85, 1.05))
    # bibir
    box((0, fy + headR*0.10, headZ - headR*0.52), (headR*0.42, headR*0.07, headR*0.075), lips)
    if spec.get('blush'):
        bm = mat('S_Blush', (0.78, 0.50, 0.46), 0.8)
        for s in (1,-1):
            ico((s*headR*0.62, fy - headR*0.04, headZ - headR*0.30), headR*0.11, bm, 1, (1, 0.5, 0.7))
    # kacamata
    if spec.get('glasses'):
        gm = mat('S_Glass', (0.16, 0.16, 0.17), 0.4, 0.3)
        for s in (1,-1):
            torus((s*headR*0.40, fy + headR*0.13, eyeZ), headR*0.23, headR*0.030, gm, (math.pi/2, 0, 0))
        box((0, fy + headR*0.13, eyeZ + headR*0.05), (headR*0.36, headR*0.03, headR*0.03), gm)
        for s in (1,-1):
            box((s*headR*0.85, fy - headR*0.45, eyeZ), (headR*0.04, headR*0.85, headR*0.04), gm)

    # ── RAMBUT (shaped) ──
    hair = spec.get('hair', 'short')
    if hair not in ('bald', 'none'):
        ico((0, -headR*0.10, headZ + headR*0.30), headR*1.04, haircl, 3, (1.0, 1.02, 0.85))
        ico((0, -headR*0.55, headZ - headR*0.05), headR*0.78, haircl, 2, (1.0, 0.62, 1.05))  # belakang
    if hair == 'short':
        box((0, fy - headR*0.10, headZ + headR*0.88), (headR*1.3, headR*0.5, headR*0.22), haircl)
    elif hair == 'spiky':
        for i in range(5):
            a = (i-2)*0.32
            cone((math.sin(a)*headR*0.55, -headR*0.05, headZ + headR*1.02),
                 headR*0.14, headR*0.02, headR*0.42, haircl, (0.2*abs(a), 0, a), 6)
    elif hair == 'bob':
        for s in (1,-1):
            ico((s*headR*0.85, -headR*0.05, headZ - headR*0.30), headR*0.42, haircl, 2, (0.55, 0.9, 1.5))
    elif hair == 'ponytail':
        ico((0, -headR*0.95, headZ + headR*0.25), headR*0.26, haircl, 2)
        seg((0, -headR*1.05, headZ + headR*0.1), (0, -headR*1.35, headZ - headR*1.1),
            headR*0.22, headR*0.06, haircl)
    elif hair == 'buns':
        for s in (1,-1):
            ico((s*headR*0.72, -headR*0.30, headZ + headR*0.85), headR*0.34, haircl, 2)
    elif hair == 'sanggul':
        ico((0, -headR*0.90, headZ + headR*0.05), headR*0.40, haircl, 2)
        torus((0, -headR*0.90, headZ + headR*0.05), headR*0.42, headR*0.05, belt, (math.pi/2*0.5, 0, 0))
    elif hair == 'bandana':
        bm = mat('S_Band_'+sid, spec.get('hat_col', RUST), 0.86)
        ico((0, -headR*0.05, headZ + headR*0.42), headR*1.06, bm, 2, (1.0, 1.0, 0.72))
        box((0, -headR*1.0, headZ + headR*0.1), (headR*0.22, headR*0.35, headR*0.40), bm)

    # ── JANGGUT / KUMIS ──
    if spec.get('beard'):
        bm = mat('S_Beard_'+sid, spec['beard'], 0.92)
        ico((0, fy - headR*0.08, headZ - headR*0.66), headR*0.58, bm, 2, (0.95, 0.62, 0.85))
    if spec.get('mustache'):
        mm = mat('S_Mus_'+sid, spec['mustache'], 0.92)
        box((0, fy + headR*0.10, headZ - headR*0.40), (headR*0.46, headR*0.08, headR*0.09), mm)

    # ── TOPI ──
    hat = spec.get('hat')
    hc  = mat('S_Hat_'+sid, spec.get('hat_col', HITAM), 0.85)
    if hat == 'caping':
        cone((0, 0, headZ + headR*1.05), headR*2.3, headR*0.12, headR*1.0, hc, v=16)
        torus((0, 0, headZ + headR*0.78), headR*0.85, headR*0.05, mat('S_CapTali', COKLAT, 0.85))
    elif hat == 'peci':
        cyl((0, 0.004*H, headZ + headR*0.82), headR*0.86, headR*0.55, hc, v=14)
    elif hat == 'kerudung':
        ico((0, -headR*0.06, headZ + headR*0.18), headR*1.16, hc, 3, (1.04, 1.06, 1.05))
        cone((0, -headR*0.25, headZ - headR*1.4), headR*1.45, headR*0.75, headR*2.4, hc, v=14)
    elif hat == 'captain':
        cyl((0, 0.004*H, headZ + headR*0.85), headR*0.92, headR*0.50, hc, v=14)
        cyl((0, 0.004*H, headZ + headR*1.12), headR*0.98, headR*0.10, dark, v=14)
        cyl((0, headR*0.70, headZ + headR*0.62), headR*0.55, headR*0.10, dark, v=12,
            rot=(0.35, 0, 0))                                        # pet/visor
        box((0, headR*0.92, headZ + headR*0.90), (headR*0.34, headR*0.04, headR*0.20),
            mat('S_Badge', (0.72, 0.62, 0.32), 0.4, 0.5))

    # ── AKSESORI ──
    if spec.get('apron'):
        am = mat('S_Apron_'+sid, spec['apron'], 0.88)
        box((0, 0.092*H, (waistZ+chestZ)/2 - 0.03*H), (0.115*H, 0.012*H, 0.17*H), am)
        box((0, 0.094*H, hipZ - 0.045*H), (0.135*H, 0.010*H, 0.13*H), am)
        seg((0.05*H, 0.085*H, chestZ+0.02*H), (-0.05*H, 0.085*H, chestZ+0.02*H), 0.008*H, 0.008*H, am)
    if spec.get('sash'):
        sm = mat('S_Sash_'+sid, spec['sash'], 0.88)
        seg((0.085*H, 0.085*H, shZ), (-0.075*H, 0.075*H, hipZ + 0.02*H), 0.024*H, 0.024*H, sm)
    if spec.get('stick') == 'kentongan':
        wood = mat('S_Wood', COKLAT, 0.88)
        cyl((shW+0.02*H, 0.05*H, 0.42*H), 0.013*H, 0.30*H, wood, rot=(0.15, 0, 0))
        ico((shW+0.02*H, 0.065*H, 0.52*H), 0.032*H, wood, 2, (1.0, 0.8, 1.35))
    elif spec.get('stick') == 'tongkat':
        wood = mat('S_Wood', COKLAT, 0.88)
        cyl((shW+0.015*H, 0.06*H, 0.30*H), 0.011*H, 0.58*H, wood, rot=(0.06, 0, 0))

# ════════════════════════════════════════════════════════════
def bake_and_export(npc_id):
    bpy.ops.object.select_all(action='DESELECT')
    for o in P:
        if o and o.type == 'MESH': o.select_set(True)
    bpy.context.view_layer.objects.active = P[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object; obj.name = npc_id
    bpy.ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.015)
    bpy.ops.object.mode_set(mode='OBJECT')
    # noise kain halus hanya pada pakaian
    for mtl in obj.data.materials:
        if not mtl or not mtl.node_tree: continue
        if any(k in mtl.name for k in ('Shirt','Pants','Apron','Sash','Hat','Band','Stripe')):
            nt = mtl.node_tree; b = nt.nodes.get('Principled BSDF')
            base = tuple(b.inputs['Base Color'].default_value)[:3]
            tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
            nz.inputs['Scale'].default_value = 22.0; nz.inputs['Detail'].default_value = 6.0
            nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
            rp = nt.nodes.new('ShaderNodeValToRGB'); cr = rp.color_ramp
            dk = tuple(min(1,c*0.72) for c in base); br = tuple(min(1,c*1.16) for c in base)
            cr.elements[0].position = 0.35; cr.elements[0].color = (*dk,1)
            cr.elements[1].position = 0.65; cr.elements[1].color = (*br,1)
            nt.links.new(nz.outputs['Fac'], rp.inputs['Fac'])
            nt.links.new(rp.outputs['Color'], b.inputs['Base Color'])
    img = bpy.data.images.new(npc_id + '_baked', 1024, 1024)
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
    # mute ringan (Sims tetap hidup, dunia tetap kalem)
    n = len(img.pixels); buf = np.empty(n, dtype=np.float32)
    img.pixels.foreach_get(buf); px = buf.reshape(-1,4)
    lum = px[:,:3] @ np.array([0.299,0.587,0.114], np.float32)
    px[:,:3] = np.clip((lum[:,None] + (px[:,:3]-lum[:,None])*0.78)*0.96+0.01, 0, 1)
    img.pixels.foreach_set(px.reshape(-1))
    for d in OUT_DIRS:
        img.filepath_raw = d + "/" + npc_id + "_baked.png"; img.file_format='PNG'; img.save()
    mb = bpy.data.materials.new(npc_id + '_mat'); mb.use_nodes = True
    bn = mb.node_tree.nodes['Principled BSDF']; bn.inputs['Roughness'].default_value = 0.78
    tn = mb.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = img
    mb.node_tree.links.new(tn.outputs['Color'], bn.inputs['Base Color'])
    obj.data.materials.clear(); obj.data.materials.append(mb)
    for p in obj.data.polygons: p.material_index = 0
    def _export(o, name):
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for d in OUT_DIRS:
            for att in range(3):
                try:
                    bpy.ops.wm.obj_export(filepath=d + "/" + name + ".obj",
                        export_selected_objects=True, export_materials=True,
                        apply_modifiers=True, forward_axis='NEGATIVE_Y',
                        up_axis='Z', path_mode='STRIP')
                    break
                except Exception as e:
                    print("  retry", att, name, e)
    _export(obj, npc_id)
    vs = [v.co.z for v in obj.data.vertices]
    zmin, zmax = min(vs), max(vs); Hh = zmax - zmin
    body_z = zmin + 0.46 * Hh
    for pose, phase in (('idle',0.0), ('walk1',1.0), ('walk2',-1.0)):
        dup = obj.copy(); dup.data = obj.data.copy(); dup.name = npc_id + '_' + pose
        bpy.context.collection.objects.link(dup)
        if abs(phase) > 1e-6:
            sw = 0.15 * Hh * phase
            for v in dup.data.vertices:
                x, y, z = v.co
                if z < body_z:
                    lf = (body_z - z) / (body_z - zmin + 1e-6)
                    side = 1.0 if x >= 0 else -1.0
                    v.co.y += sw * lf * side
                    if side * phase > 0:
                        v.co.z += 0.045 * Hh * lf
        _export(dup, npc_id + '_' + pose)
        bpy.data.objects.remove(dup, do_unlink=True)
    print("NPC v2 DONE:", npc_id)

def make_npc(spec):
    global P
    clear_scene(); P = []
    build_human(spec)
    bake_and_export('npc_' + spec['id'])
