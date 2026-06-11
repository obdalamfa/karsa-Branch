import bpy, os, math, glob
import numpy as np

# ============================================================
# RESTANDARISASI ASET — skala meter (DESIGN_STANDARD.md) +
# palet muted Disco/Zomboid (desaturasi PNG bake & Kd MTL).
# Sumber & target utama: MAIN repo assets/models.
# ============================================================
MAIN = "E:/Game Research/Lembah Karsa 3D/assets/models"
OUT_DIRS = [
    MAIN,
    "E:/Game Research/Lembah Karsa 3D/game/assets/models",
    "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd/assets/models",
]
for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

# tinggi target (meter). (nama, target_z, punya_pose)
TARGETS = [
    ('mob_ayam',    0.50, True), ('mob_jago',   0.60, True),
    ('mob_bebek',   0.50, True), ('mob_kucing', 0.60, True),
    ('mob_kelinci', 0.40, True), ('mob_rubah',  0.65, True),
    ('mob_kambing', 1.00, True), ('mob_domba',  1.05, True),
    ('mob_sapi',    1.50, True), ('mob_kuda',   1.85, True),
    ('mob_kelelawar', 0.50, False), ('mob_tikus_gua', 0.80, False),
    ('mob_tuyul',   0.95, False), ('mob_demit',  1.60, False),
    ('mob_leak',    1.90, False), ('mob_pocong', 1.90, False),
    ('mob_banaspati', 2.00, False), ('mob_kuntilanak', 2.20, False),
    ('mob_wewe',    2.30, False), ('mob_jin',    2.50, False),
    ('mob_bidadari', 2.10, False), ('mob_genderuwo', 2.60, False),
    ('naga',        4.50, False),
]
ROTATE_UPRIGHT = {'mob_dewa': 2.60}   # model lama rebah (Y-up) → tegakkan + scale

def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()

def import_obj(path):
    bpy.ops.wm.obj_import(filepath=path, forward_axis='NEGATIVE_Y', up_axis='Z')
    ms = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    return ms[0] if ms else None

def export_all(obj, name):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for d in OUT_DIRS:
        for attempt in range(3):
            try:
                bpy.ops.wm.obj_export(filepath=d + "/" + name + ".obj",
                    export_selected_objects=True, export_materials=True,
                    apply_modifiers=True, forward_axis='NEGATIVE_Y', up_axis='Z',
                    path_mode='STRIP')
                break
            except Exception as e:
                print("  retry", attempt, d, name, ":", e)

def rescale_file(name, factor):
    clear()
    p = MAIN + "/" + name + ".obj"
    if not os.path.exists(p):
        print("MISSING:", name); return False
    o = import_obj(p)
    if not o: return False
    o.scale = (factor, factor, factor)
    bpy.ops.object.transform_apply(scale=True)
    # pastikan duduk di z=0
    zmin = min((o.matrix_world @ v.co).z for v in o.data.vertices)
    o.location.z -= zmin
    bpy.ops.object.transform_apply(location=True)
    export_all(o, name)
    return True

print("== RESCALE ==")
for name, tz, has_pose in TARGETS:
    p = MAIN + "/" + name + ".obj"
    if not os.path.exists(p):
        print("MISSING:", name); continue
    clear()
    o = import_obj(p)
    if not o: continue
    cur = o.dimensions.z
    if cur < 1e-4: continue
    f = tz / cur
    clear()
    rescale_file(name, f)
    print(f"{name}: {cur:.2f} -> {tz:.2f} (x{f:.3f})")
    if has_pose:
        for sfx in ('_idle', '_walk1', '_walk2'):
            if os.path.exists(MAIN + "/" + name + sfx + ".obj"):
                rescale_file(name + sfx, f)

print("== ROTATE+RESCALE (model rebah) ==")
for name, tz in ROTATE_UPRIGHT.items():
    p = MAIN + "/" + name + ".obj"
    if not os.path.exists(p):
        print("MISSING:", name); continue
    clear()
    o = import_obj(p)
    if not o: continue
    o.rotation_euler = (math.pi/2, 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    cur = o.dimensions.z
    f = tz / max(cur, 1e-4)
    o.scale = (f, f, f); bpy.ops.object.transform_apply(scale=True)
    zmin = min((o.matrix_world @ v.co).z for v in o.data.vertices)
    o.location.z -= zmin; bpy.ops.object.transform_apply(location=True)
    export_all(o, name)
    print(f"{name}: ditegakkan, {cur:.2f} -> {tz:.2f}")

# ============================================================
# MUTE PASS — desaturasi luminance-lerp (S x0.60), highlight turun
# ============================================================
SAT, VMUL, VADD = 0.60, 0.90, 0.02
LUM = np.array([0.299, 0.587, 0.114], dtype=np.float32)

def mute_png(path):
    try:
        img = bpy.data.images.load(path, check_existing=False)
    except Exception as e:
        print("  png skip:", path, e); return
    n = len(img.pixels)
    buf = np.empty(n, dtype=np.float32)
    img.pixels.foreach_get(buf)
    px = buf.reshape(-1, 4)
    rgb = px[:, :3]
    lum = rgb @ LUM
    rgb = lum[:, None] + (rgb - lum[:, None]) * SAT
    rgb = rgb * VMUL + VADD
    px[:, :3] = np.clip(rgb, 0.0, 1.0)
    img.pixels.foreach_set(px.reshape(-1))
    img.filepath_raw = path; img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)

def mute_mtl(path):
    """Desaturasi Kd HANYA pada material tanpa map_Kd (warna flat)."""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    # blok per newmtl
    blocks = []; cur = []
    for ln in lines:
        if ln.startswith('newmtl') and cur:
            blocks.append(cur); cur = []
        cur.append(ln)
    if cur: blocks.append(cur)
    out = []
    for blk in blocks:
        has_map = any(l.startswith('map_Kd') for l in blk)
        for ln in blk:
            if not has_map and ln.startswith('Kd '):
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

print("== MUTE PNG ==")
pngs = sorted(glob.glob(MAIN + "/*_baked.png"))
for p in pngs:
    mute_png(p)
    print("  muted:", os.path.basename(p))

print("== MUTE MTL (flat colors) ==")
for p in sorted(glob.glob(MAIN + "/mob_*.mtl")) + [MAIN + "/naga.mtl"]:
    if os.path.exists(p) and 'handmade' not in p:
        mute_mtl(p)
print("  mtl muted")

# salin PNG + MTL hasil mute ke dir lain
import shutil
for d in OUT_DIRS[1:]:
    for p in glob.glob(MAIN + "/*_baked.png"):
        shutil.copy2(p, d + "/" + os.path.basename(p))
print("PNG copied to all dirs")

# ── VERIFIKASI ──
clear()
print("== VERIFIKASI DIMENSI ==")
for name, tz, _ in TARGETS[:6] + TARGETS[-3:]:
    p = MAIN + "/" + name + ".obj"
    if not os.path.exists(p): continue
    clear(); o = import_obj(p)
    if o: print(f"  {name}: z={o.dimensions.z:.2f} (target {tz})")
clear()
print("RESTANDARD DONE")
