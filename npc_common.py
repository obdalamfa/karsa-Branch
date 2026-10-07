# Shared builder untuk NPC manusia Lembah Karsa — gaya Disco muted.
# Di-exec oleh build_npcs_1.py / build_npcs_2.py (bukan modul import).
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

# ── Palet muted (DESIGN_STANDARD.md) ─────────────────────────
SKIN  = (0.55, 0.42, 0.32)
SKIN_L= (0.62, 0.48, 0.36)
SKIN_D= (0.45, 0.34, 0.26)
OLIVE = (0.35, 0.36, 0.24)
RUST  = (0.48, 0.28, 0.18)
TEAL  = (0.24, 0.34, 0.34)
KREM  = (0.55, 0.52, 0.44)
COKLAT= (0.36, 0.27, 0.18)
NAVY  = (0.20, 0.24, 0.32)
ABU   = (0.42, 0.42, 0.40)
HITAM = (0.10, 0.10, 0.11)
RAMBUT= (0.12, 0.10, 0.08)
UBAN  = (0.62, 0.60, 0.56)
TAN   = (0.58, 0.48, 0.30)
P_PNK = (0.52, 0.40, 0.42)

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

P = []
def ico(loc, r, m, sub=3, sc=(1,1,1), rot=(0,0,0)):
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
def seg(p0, p1, rb, rt, m, v=9):
    p0 = mathutils.Vector(p0); p1 = mathutils.Vector(p1); d = p1 - p0; L = d.length
    if L < 1e-5: return None
    bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=rb, radius2=rt, depth=L, location=(p0+p1)/2)
    o = bpy.context.active_object
    o.rotation_euler = d.to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o

def clear_scene():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for im in list(bpy.data.images):
        if im.users == 0: bpy.data.images.remove(im)

# ── Builder manusia parametrik (Z-up, hadap +Y, kaki di z=0) ──
def build_human(spec):
    """spec: dict — H, skin, shirt, pants, sleeve('long'/'short'),
    bottom('pants'/'sarong'/'skirt'), hair('short'/'ponytail'/'buns'/
    'sanggul'/'bald'/'bandana'), hair_col, hat(None/'caping'/'peci'/
    'kerudung'/'captain'), hat_col, beard(None/col), apron(None/col),
    sash(None/col), slouch(0..1), stick(None/'kentongan')"""
    H      = spec['H']
    skin   = mat('N_Skin_'+spec['id'], spec.get('skin', SKIN), 0.80)
    shirt  = mat('N_Shirt_'+spec['id'], spec['shirt'], 0.90)
    pants  = mat('N_Pants_'+spec['id'], spec['pants'], 0.92)
    haircl = mat('N_Hair_'+spec['id'], spec.get('hair_col', RAMBUT), 0.95)
    dark   = mat('N_Dark', HITAM, 0.9)
    slouch = spec.get('slouch', 0.25)
    fwd    = 0.05 * slouch          # condong lelah ke depan
    # proporsi
    hipz   = 0.50 * H
    chestz = 0.72 * H
    shz    = 0.815 * H              # bahu
    neckz  = 0.855 * H
    headz  = 0.925 * H
    headr  = 0.077 * H

    # kaki
    bottom = spec.get('bottom', 'pants')
    if bottom == 'pants':
        for s in (1, -1):
            cyl((s*0.055*H, 0.0, hipz*0.52), 0.040*H, hipz*0.96, pants)
            ico((s*0.055*H, 0.012*H, 0.018*H), 0.030*H, dark, 2, (1.1, 1.6, 0.62))  # sepatu
    else:   # sarong / rok panjang
        cone((0, 0, hipz*0.55), 0.115*H, 0.090*H, hipz*1.05, pants, v=12)
        for s in (1, -1):
            ico((s*0.045*H, 0.018*H, 0.015*H), 0.028*H, skin, 2, (1.1, 1.5, 0.6))
    # pinggul & torso (slouch: dada maju)
    ico((0, 0.0, hipz), 0.085*H, pants, 3, (1.12, 0.78, 0.62))
    ico((0, fwd*0.4, (hipz+chestz)/2), 0.082*H, shirt, 3, (1.06, 0.74, 1.05))
    ico((0, fwd, chestz), 0.090*H, shirt, 3, (1.18, 0.80, 0.92))
    # bahu turun
    for s in (1, -1):
        ico((s*0.105*H, fwd, shz - 0.008*H), 0.040*H, shirt, 2)
    # lengan menggantung sedikit ke depan
    sleeve = spec.get('sleeve', 'long')
    arm_m  = shirt if sleeve == 'long' else skin
    for s in (1, -1):
        sh  = (s*0.115*H, fwd, shz - 0.01*H)
        el  = (s*0.125*H, fwd + 0.015*H, 0.63*H)
        hn  = (s*0.120*H, fwd + 0.045*H, 0.50*H)
        seg(sh, el, 0.026*H, 0.023*H, arm_m)
        seg(el, hn, 0.022*H, 0.018*H, skin if sleeve != 'long' else arm_m)
        ico(hn, 0.022*H, skin, 2)
    # leher + kepala
    cyl((0, fwd, neckz), 0.026*H, 0.05*H, skin)
    head = ico((0, fwd + 0.01*H, headz), headr, skin, 3, (1.0, 0.94, 1.12))
    # wajah lelah: mata slit gelap + alis + hidung + mulut
    fy = fwd + 0.01*H + headr*0.78
    for s in (1, -1):
        box((s*headr*0.42, fy, headz + headr*0.10), (headr*0.30, 0.008*H, 0.012*H), dark)
        box((s*headr*0.42, fy, headz + headr*0.34), (headr*0.34, 0.007*H, 0.009*H), haircl)
    ico((0, fy + 0.004*H, headz - headr*0.05), 0.012*H, skin, 1, (0.8, 1.0, 1.2))
    box((0, fy, headz - headr*0.45), (headr*0.36, 0.006*H, 0.008*H), dark)
    # rambut
    hair = spec.get('hair', 'short')
    if hair != 'bald':
        ico((0, fwd - headr*0.15, headz + headr*0.35), headr*0.95, haircl, 2, (1.04, 1.0, 0.78))
    if hair == 'ponytail':
        ico((0, fwd - headr*0.9, headz - headr*0.1), headr*0.34, haircl, 2, (0.8, 0.8, 1.7))
    elif hair == 'buns':
        for s in (1, -1):
            ico((s*headr*0.75, fwd - headr*0.35, headz + headr*0.75), headr*0.32, haircl, 2)
    elif hair == 'sanggul':
        ico((0, fwd - headr*0.85, headz + headr*0.15), headr*0.40, haircl, 2)
    elif hair == 'bandana':
        cyl((0, fwd, headz + headr*0.45), headr*1.02, headr*0.5, mat('N_Band_'+spec['id'], spec.get('hat_col', RUST), 0.9), v=12)
    # janggut
    if spec.get('beard'):
        bm = mat('N_Beard_'+spec['id'], spec['beard'], 0.95)
        ico((0, fy - 0.004*H, headz - headr*0.62), headr*0.42, bm, 2, (1.0, 0.7, 1.0))
    # topi
    hat = spec.get('hat')
    hc  = mat('N_Hat_'+spec['id'], spec.get('hat_col', HITAM), 0.88)
    if hat == 'caping':
        cone((0, fwd, headz + headr*1.15), headr*2.2, headr*0.15, headr*1.0, hc, v=14)
    elif hat == 'peci':
        cyl((0, fwd, headz + headr*0.95), headr*0.80, headr*0.55, hc, v=12)
    elif hat == 'kerudung':
        ico((0, fwd - headr*0.1, headz + headr*0.25), headr*1.12, hc, 3, (1.05, 1.05, 1.0))
        cone((0, fwd - headr*0.3, headz - headr*1.3), headr*1.25, headr*0.7, headr*2.2, hc, v=12)
    elif hat == 'captain':
        cyl((0, fwd, headz + headr*0.95), headr*0.85, headr*0.55, hc, v=12)
        cyl((0, fwd + headr*0.55, headz + headr*0.72), headr*0.95, headr*0.10, dark, v=12)
        box((0, fwd + headr*0.86, headz + headr*0.98), (headr*0.30, 0.004*H, headr*0.18),
            mat('N_Badge', (0.62, 0.55, 0.30), 0.4, metal=0.5))
    # apron / celemek
    if spec.get('apron'):
        am = mat('N_Apron_'+spec['id'], spec['apron'], 0.92)
        box((0, fwd + 0.085*H, (hipz+chestz)/2 - 0.02*H), (0.13*H, 0.012*H, 0.22*H), am)
    # selempang sarung
    if spec.get('sash'):
        sm = mat('N_Sash_'+spec['id'], spec['sash'], 0.92)
        seg((0.09*H, fwd + 0.07*H, shz), (-0.08*H, fwd + 0.06*H, hipz), 0.022*H, 0.022*H, sm)
    # kentongan (tongkat ronda) di tangan kanan
    if spec.get('stick') == 'kentongan':
        wood = mat('N_Wood', COKLAT, 0.9)
        cyl((0.13*H, fwd + 0.05*H, 0.46*H), 0.012*H, 0.30*H, wood, rot=(0.2, 0, 0))
        ico((0.13*H, fwd + 0.07*H, 0.56*H), 0.030*H, wood, 2, (1.0, 0.8, 1.3))

def bake_and_export(npc_id):
    """join → UV → noise kain → bake 1024 → export base + 3 pose."""
    bpy.ops.object.select_all(action='DESELECT')
    for o in P:
        if o and o.type == 'MESH': o.select_set(True)
    bpy.context.view_layer.objects.active = P[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object; obj.name = npc_id
    bpy.ops.object.shade_smooth()
    # UV + noise kain
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    for mtl in obj.data.materials:
        if not mtl or not mtl.node_tree: continue
        nm = mtl.name
        if any(k in nm for k in ('Shirt','Pants','Apron','Sash','Hat','Band')):
            nt = mtl.node_tree; b = nt.nodes.get('Principled BSDF')
            base = tuple(b.inputs['Base Color'].default_value)[:3]
            tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
            nz.inputs['Scale'].default_value = 18.0; nz.inputs['Detail'].default_value = 7.0
            nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
            rp = nt.nodes.new('ShaderNodeValToRGB'); cr = rp.color_ramp
            dk = tuple(min(1,c*0.55) for c in base); br = tuple(min(1,c*1.25) for c in base)
            cr.elements[0].position = 0.33; cr.elements[0].color = (*dk,1)
            cr.elements[1].position = 0.67; cr.elements[1].color = (*br,1)
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
    # mute langsung saat save (konsisten standar)
    n = len(img.pixels); buf = np.empty(n, dtype=np.float32)
    img.pixels.foreach_get(buf); px = buf.reshape(-1,4)
    lum = px[:,:3] @ np.array([0.299,0.587,0.114], np.float32)
    px[:,:3] = np.clip((lum[:,None] + (px[:,:3]-lum[:,None])*0.62)*0.92+0.02, 0, 1)
    img.pixels.foreach_set(px.reshape(-1))
    for d in OUT_DIRS:
        img.filepath_raw = d + "/" + npc_id + "_baked.png"; img.file_format='PNG'; img.save()
    mb = bpy.data.materials.new(npc_id + '_mat'); mb.use_nodes = True
    bn = mb.node_tree.nodes['Principled BSDF']; bn.inputs['Roughness'].default_value = 0.85
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
    # pose idle/walk1/walk2 (deformasi kaki)
    vs = [v.co.z for v in obj.data.vertices]
    zmin, zmax = min(vs), max(vs); Hh = zmax - zmin
    body_z = zmin + 0.46 * Hh
    for pose, phase in (('idle',0.0), ('walk1',1.0), ('walk2',-1.0)):
        dup = obj.copy(); dup.data = obj.data.copy(); dup.name = npc_id + '_' + pose
        bpy.context.collection.objects.link(dup)
        if abs(phase) > 1e-6:
            sw = 0.16 * Hh * phase
            for v in dup.data.vertices:
                x, y, z = v.co
                if z < body_z:
                    lf = (body_z - z) / (body_z - zmin + 1e-6)
                    side = 1.0 if x >= 0 else -1.0
                    v.co.y += sw * lf * side
                    if side * phase > 0:
                        v.co.z += 0.05 * Hh * lf
        _export(dup, npc_id + '_' + pose)
        bpy.data.objects.remove(dup, do_unlink=True)
    print("NPC DONE:", npc_id)

def make_npc(spec):
    global P
    clear_scene(); P = []
    build_human(spec)
    bake_and_export('npc_' + spec['id'])
