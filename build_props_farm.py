import bpy, os, math, mathutils
import numpy as np

# ============================================================
# PROPS FARMING & SIM-LIFE — muted Disco/Zomboid (DESIGN_STANDARD.md)
# scarecrow, kandang_ayam, gerobak, cangkul, ember, jerami,
# peti_sayur, karung, pagar_kayu
# ============================================================
MAIN = "E:/Game Research/Lembah Karsa 3D/assets/models"
OUT_DIRS = [
    MAIN,
    "E:/Game Research/Lembah Karsa 3D/game/assets/models",
    "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd/assets/models",
]
for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

def mat(name, col, rough=0.9, metal=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m

KAYU   = mat('FP_Kayu',   (0.34, 0.26, 0.17))
KAYU_T = mat('FP_KayuTua',(0.26, 0.20, 0.13))
JERAMI = mat('FP_Jerami', (0.52, 0.44, 0.24))
KAIN   = mat('FP_Kain',   (0.40, 0.36, 0.28))
KARAT  = mat('FP_Karat',  (0.35, 0.24, 0.16), 0.7, 0.25)
GONI   = mat('FP_Goni',   (0.45, 0.38, 0.26))
SENG   = mat('FP_Seng',   (0.40, 0.42, 0.43), 0.55, 0.35)
TANAH  = mat('FP_Tanah',  (0.30, 0.24, 0.16))

P = []
def ico(loc, r, m, sub=2, sc=(1,1,1), rot=(0,0,0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.active_object; o.scale = sc; o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(m); P.append(o); return o
def cyl(loc, rad, depth, m, rot=(0,0,0), v=9):
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

DONE = []
def finish(name):
    global P
    bpy.ops.object.select_all(action='DESELECT')
    for o in P:
        if o and o.type == 'MESH': o.select_set(True)
    bpy.context.view_layer.objects.active = P[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object; obj.name = name
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for d in OUT_DIRS:
        for att in range(3):
            try:
                bpy.ops.wm.obj_export(filepath=d + "/" + name + ".obj",
                    export_selected_objects=True, export_materials=True,
                    apply_modifiers=True, forward_axis='NEGATIVE_Y', up_axis='Z')
                break
            except Exception as e:
                print("  retry", att, name, e)
    bpy.data.objects.remove(obj, do_unlink=True)
    DONE.append(name); P = []

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()

# ── SCARECROW (orang-orangan sawah) — 2.1m ──
cyl((0,0,0.95), 0.045, 1.9, KAYU)                          # tiang
cyl((0,0,1.45), 0.035, 1.0, KAYU, rot=(0,math.pi/2,0))     # palang lengan
box((0,0,1.18), (0.34,0.22,0.55), KAIN)                    # baju lusuh
for s in (1,-1):                                           # lengan baju
    box((s*0.36,0,1.45), (0.34,0.16,0.14), KAIN)
ico((0,0,1.72), 0.16, GONI, 2, (1,0.95,1.1))               # kepala karung
cone((0,0,1.98), 0.30, 0.02, 0.28, JERAMI, v=12)           # caping jerami
for s in (1,-1):                                           # mata jahit silang
    box((s*0.06,0.145,1.74), (0.05,0.01,0.012), KAYU_T)
for i in range(7):                                         # jerami nongol bawah baju
    a = i*(2*math.pi/7)
    cone((math.cos(a)*0.10, math.sin(a)*0.10, 0.86), 0.018, 0.002, 0.22,
         JERAMI, rot=(0.3*math.sin(a), 0.3*math.cos(a), 0), v=5)
finish('prop_scarecrow')

# ── KANDANG AYAM (coop) — 1.5m ──
box((0,0,0.55), (1.4,1.0,0.9), KAYU)                        # badan
for s in (1,-1):                                            # atap seng miring
    box((s*0.36,0,1.12), (0.78,1.12,0.05), SENG, rot=(0, s*0.38, 0))
box((0,0.51,0.45), (0.34,0.06,0.4), KAYU_T)                 # pintu kecil
box((0,0.52,0.45), (0.26,0.04,0.32), TANAH)                 # lubang masuk
for s in (1,-1):                                            # kaki panggung
    for t in (1,-1):
        cyl((s*0.6, t*0.4, 0.06), 0.05, 0.14, KAYU_T)
cyl((0,0.62,0.18), 0.025, 0.7, KAYU, rot=(0,math.pi/2,0))   # tangga titian
for i in range(3):
    box((0, 0.56+i*0.07, 0.10+i*0.07), (0.16,0.02,0.02), KAYU_T)
finish('prop_kandang_ayam')

# ── GEROBAK (hand cart) — 1.0m ──
box((0,0,0.52), (0.9,1.3,0.16), KAYU)                       # bak
for s in (1,-1):
    box((s*0.44,0,0.66), (0.04,1.3,0.30), KAYU_T)           # dinding samping
box((0,0.64,0.66), (0.86,0.04,0.30), KAYU_T)                # dinding depan
box((0,-0.64,0.66), (0.86,0.04,0.30), KAYU_T)               # dinding belakang
for s in (1,-1):                                            # roda kayu
    cyl((s*0.50,0.12,0.30), 0.28, 0.07, KAYU_T, rot=(0,math.pi/2,0), v=12)
    cyl((s*0.55,0.12,0.30), 0.05, 0.05, KARAT, rot=(0,math.pi/2,0))
for s in (1,-1):                                            # gagang tarik
    cyl((s*0.30,-0.95,0.56), 0.03, 0.75, KAYU, rot=(math.pi/2*0.94,0,0))
ico((0,0.1,0.72), 0.22, JERAMI, 2, (1.5,2.0,0.6))           # muatan jerami
finish('prop_gerobak')

# ── CANGKUL (hoe, prop berdiri) — 1.1m ──
cyl((0,0,0.55), 0.022, 1.1, KAYU, rot=(0.18,0,0))
box((0,0.10,1.06), (0.05,0.22,0.04), KARAT, rot=(0.5,0,0))
finish('prop_cangkul')

# ── EMBER (bucket) — 0.35m ──
cone((0,0,0.17), 0.16, 0.13, 0.34, SENG, v=12)
cyl((0,0,0.33), 0.165, 0.02, KARAT, v=12)
cyl((0,0,0.40), 0.012, 0.28, KARAT, rot=(0,math.pi/2,0))    # gagang
finish('prop_ember')

# ── JERAMI (haystack) — 1.2m ──
cone((0,0,0.60), 0.75, 0.06, 1.2, JERAMI, v=14)
for i in range(8):
    a = i*(2*math.pi/8)
    cone((math.cos(a)*0.55, math.sin(a)*0.55, 0.10), 0.05, 0.005, 0.30,
         JERAMI, rot=(0.9*math.sin(a), 0.9*math.cos(a), 0), v=5)
cyl((0,0,1.22), 0.025, 0.25, KAYU)                          # tiang puncak
finish('prop_jerami')

# ── PETI SAYUR (crate) — 0.4m ──
box((0,0,0.20), (0.56,0.42,0.40), KAYU)
box((0,0,0.21), (0.50,0.36,0.40), KAYU_T)
for i in range(5):                                          # isi sayur
    a = i*1.3
    ico((math.cos(a)*0.12, math.sin(a)*0.10, 0.40), 0.07,
        mat('FP_Sayur', (0.30,0.36,0.18)), 2)
finish('prop_peti_sayur')

# ── KARUNG (sack) — 0.55m ──
ico((0,0,0.26), 0.24, GONI, 3, (1.0,0.9,1.1))
ico((0,0,0.50), 0.10, GONI, 2, (1.0,1.0,0.5))               # leher diikat
cyl((0,0,0.52), 0.045, 0.04, KAYU_T)
finish('prop_karung')

# ── PAGAR KAYU (fence section, tileable 2m) ──
for x in (-0.85, 0.0, 0.85):
    cyl((x,0,0.45), 0.05, 0.9, KAYU_T, v=7)
for z in (0.35, 0.70):
    box((0,0,z), (2.0,0.05,0.08), KAYU)
finish('prop_pagar_kayu')

print("PROPS DONE:", ", ".join(DONE))

# ── MTL mute pass (props pakai Kd flat — mute konsisten standar) ──
SAT, VMUL, VADD = 0.60, 0.90, 0.02
import glob
def mute_mtl(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    out = []
    for ln in lines:
        if ln.startswith('Kd '):
            try:
                r, g, b = [float(x) for x in ln.split()[1:4]]
                l = 0.299*r + 0.587*g + 0.114*b
                r = max(0, min(1, (l + (r-l)*SAT) * VMUL + VADD))
                g = max(0, min(1, (l + (g-l)*SAT) * VMUL + VADD))
                b = max(0, min(1, (l + (b-l)*SAT) * VMUL + VADD))
                ln = f"Kd {r:.6f} {g:.6f} {b:.6f}\n"
            except Exception:
                pass
        out.append(ln)
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(out)
for d in OUT_DIRS:
    for p in glob.glob(d + "/prop_*.mtl"):
        mute_mtl(p)
print("PROP MTL muted")

# ── CONTACT SHEET render ──
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for i, n in enumerate(DONE):
    bpy.ops.wm.obj_import(filepath=MAIN + "/" + n + ".obj",
                          forward_axis='NEGATIVE_Y', up_axis='Z')
    o = [m for m in bpy.context.selected_objects if m.type == 'MESH'][0]
    col = i % 5; row = i // 5
    o.location = ((col-2)*2.2, -row*2.6, 0)

bpy.ops.mesh.primitive_plane_add(size=40, location=(0,-1.3,0))
gp = bpy.context.active_object
gm = bpy.data.materials.new('FPGnd'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.12,0.12,0.11,1)
gp.data.materials.append(gm)
for loc,e,c in [((6,-9,9),700,(1,0.95,0.85)),((-8,-6,7),380,(0.55,0.65,1)),((0,6,7),280,(1,0.72,0.5))]:
    bpy.ops.object.light_add(type='POINT', location=loc); l=bpy.context.active_object
    l.data.energy=e; l.data.color=c
bpy.ops.object.light_add(type='SUN'); s=bpy.context.active_object
s.data.energy=0.8; s.rotation_euler=(0.55,0.1,-0.3)
def look_at(cam,t):
    d=mathutils.Vector(t)-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=48; sc.cycles.use_denoising=True
sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.07,0.075,0.09,1)
sc.render.resolution_x=1500; sc.render.resolution_y=760
bpy.ops.object.camera_add(location=(0,-11.5,4.6)); cam=bpy.context.active_object
look_at(cam,(0,-1.3,0.6)); cam.data.lens=44; sc.camera=cam
sc.render.filepath="E:/Game Research/Lembah Karsa 3D/props_farm.png"
bpy.ops.render.render(write_still=True)
print("PROPS render done")
