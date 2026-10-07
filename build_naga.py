import bpy, math, mathutils, os

# ============================================================
# BUILD CHINESE FOLKTALE DRAGON (NAGA) — atomic build+export+save
# ============================================================

def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for m in list(bpy.data.materials):
        if m.users == 0:
            bpy.data.materials.remove(m)

def mat(name, col, rough=0.45, metal=0.0, emit=0.0):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit > 0:
        b.inputs['Emission Color'].default_value = (*col, 1.0)
        b.inputs['Emission Strength'].default_value = emit
    return m

reset()

# ---- Materials (export to MTL) ----
M_gold   = mat('Naga_Gold',    (0.86, 0.60, 0.15), 0.32, metal=0.60)
M_goldDk = mat('Naga_GoldDk',  (0.62, 0.42, 0.10), 0.42, metal=0.45)
M_horn   = mat('Naga_Horn',    (0.80, 0.68, 0.32), 0.40, metal=0.30)
M_green  = mat('Naga_Green',   (0.22, 0.62, 0.10), 0.50)
M_greenD = mat('Naga_GreenDk', (0.10, 0.40, 0.06), 0.55)
M_greenL = mat('Naga_GreenLt', (0.48, 0.82, 0.18), 0.45)
M_red    = mat('Naga_Red',     (0.82, 0.14, 0.07), 0.50)
M_orange = mat('Naga_Orange',  (0.96, 0.46, 0.05), 0.40, emit=0.6)
M_teeth  = mat('Naga_Teeth',   (0.94, 0.92, 0.84), 0.28)
M_mouth  = mat('Naga_Mouth',   (0.55, 0.08, 0.08), 0.55)
M_tongue = mat('Naga_Tongue',  (0.82, 0.22, 0.24), 0.50)
M_eye    = mat('Naga_Eye',     (0.10, 0.35, 0.90), 0.10, emit=1.6)
M_eyerim = mat('Naga_EyeRim',  (0.80, 0.12, 0.06), 0.45)
M_pupil  = mat('Naga_Pupil',   (0.02, 0.00, 0.00), 0.50)
M_dark   = mat('Naga_DarkN',   (0.10, 0.07, 0.03), 0.70)

OBS = []

def ico(loc, r, m=None, sub=3, sc=(1, 1, 1), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.active_object
    o.scale = sc; o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    if m: o.data.materials.append(m)
    OBS.append(o); return o

def seg(p0, p1, rb, rt, m, v=7):
    p0 = mathutils.Vector(p0); p1 = mathutils.Vector(p1)
    d = p1 - p0; L = d.length
    if L < 1e-5: return None
    bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=rb, radius2=rt, depth=L, location=(p0 + p1) / 2)
    o = bpy.context.active_object
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    bpy.ops.object.transform_apply(rotation=True)
    if m: o.data.materials.append(m)
    OBS.append(o); return o

# ============================================================
# 1. BODY — tapered serpentine Bezier curve
# ============================================================
PTS = [
    (0.85, 0.75, 4.25, 0.40),
    (0.45, 0.05, 3.65, 0.47),
    (0.05, 0.45, 3.00, 0.53),
    (-0.20, -0.20, 2.40, 0.57),
    (0.20, 0.55, 1.80, 0.59),
    (0.70, 0.00, 1.30, 0.57),
    (0.30, -0.45, 0.90, 0.50),
    (-0.55, 0.25, 0.80, 0.42),
    (-1.35, -0.20, 1.20, 0.32),
    (-2.00, 0.30, 1.95, 0.22),
    (-2.45, -0.10, 2.65, 0.12),
    (-2.65, 0.20, 3.25, 0.04),
]
cu = bpy.data.curves.new('DragonSpine', 'CURVE')
cu.dimensions = '3D'; cu.resolution_u = 14
cu.bevel_depth = 1.0; cu.bevel_resolution = 8
cu.use_fill_caps = True
sp = cu.splines.new('BEZIER')
sp.bezier_points.add(len(PTS) - 1)
for i, (x, y, z, r) in enumerate(PTS):
    bp = sp.bezier_points[i]
    bp.co = (x, y, z); bp.radius = r
    bp.handle_left_type = 'AUTO'; bp.handle_right_type = 'AUTO'
body = bpy.data.objects.new('DragonBody', cu)
bpy.context.collection.objects.link(body)
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.convert(target='MESH')
body = bpy.context.active_object; body.name = 'DragonBody'
body.data.materials.append(M_gold)
OBS.append(body)

def dorsal(i):
    a = mathutils.Vector(PTS[max(0, i - 1)][:3])
    b = mathutils.Vector(PTS[min(len(PTS) - 1, i + 1)][:3])
    t = (b - a).normalized()
    up = mathutils.Vector((0, 0, 1))
    d = up - up.dot(t) * t
    if d.length < 1e-4: d = mathutils.Vector((0, 1, 0))
    return d.normalized(), t

# ============================================================
# 2. HEAD
# ============================================================
ico((0.95, 1.35, 4.62), 0.42, M_gold, 4, (1.05, 1.1, 0.95))            # cranium
ico((0.95, 2.05, 4.55), 0.34, M_gold, 4, (0.95, 1.7, 0.78))           # upper jaw/snout
ico((0.95, 2.62, 4.60), 0.20, M_gold, 3, (1.0, 0.9, 0.85))            # nose
ico((0.95, 2.25, 4.40), 0.30, M_red, 3, (1.05, 1.55, 0.32))           # upper lip
ico((0.95, 1.95, 4.18), 0.27, M_gold, 4, (0.92, 1.65, 0.62), (-0.32, 0, 0))  # lower jaw
ico((0.95, 2.45, 4.02), 0.17, M_gold, 3, (0.9, 0.9, 0.5))             # jaw front
ico((0.95, 2.35, 3.86), 0.12, M_red, 2, (1.0, 1.0, 1.3))              # chin
ico((0.95, 2.05, 4.33), 0.24, M_mouth, 3, (0.85, 1.5, 0.45))          # mouth interior
ico((0.95, 2.30, 4.20), 0.13, M_tongue, 2, (0.7, 1.3, 0.35))          # tongue

# teeth rows
for sx in [-1, 1]:
    for j in range(6):
        ty = 1.84 + j * 0.15
        seg((sx * 0.19, ty, 4.36), (sx * 0.19, ty, 4.24), 0.026, 0.004, M_teeth, v=5)
        seg((sx * 0.17, ty + 0.03, 4.24), (sx * 0.17, ty + 0.03, 4.35), 0.024, 0.004, M_teeth, v=5)
    # front fangs (big)
    seg((sx * 0.21, 2.42, 4.36), (sx * 0.21, 2.50, 4.05), 0.05, 0.006, M_teeth, v=6)

# nostrils
for sx in [-1, 1]:
    ico((sx * 0.13, 2.74, 4.66), 0.05, M_dark, 2)
# eyes
for sx in [-1, 1]:
    ico((sx * 0.40, 1.62, 4.80), 0.16, M_eyerim, 3)
    ico((sx * 0.42, 1.74, 4.82), 0.12, M_eye, 3)
    ico((sx * 0.46, 1.84, 4.84), 0.05, M_pupil, 2, (1.0, 1.0, 1.4))
    seg((sx * 0.30, 1.55, 4.95), (sx * 0.52, 1.45, 5.12), 0.12, 0.02, M_gold, v=6)  # brow

# ============================================================
# 3. ANTLERS + WHISKERS + MANE
# ============================================================
for sx in [-1, 1]:
    base = (sx * 0.24, 1.05, 4.92); elbow = (sx * 0.40, 0.72, 5.45); top = (sx * 0.55, 0.55, 5.95)
    seg(base, elbow, 0.075, 0.05, M_horn)
    seg(elbow, top, 0.05, 0.018, M_horn)
    seg(elbow, (sx * 0.30, 1.25, 5.55), 0.04, 0.012, M_horn)
    seg((sx * 0.47, 0.63, 5.7), (sx * 0.78, 0.85, 5.95), 0.035, 0.01, M_horn)
    seg((sx * 0.5, 0.6, 5.78), (sx * 0.7, 0.25, 6.1), 0.03, 0.008, M_horn)
    ico(base, 0.09, M_gold, 2)

# whiskers (long curling)
for sx in [-1, 1]:
    p = [(sx * 0.18, 2.62, 4.55), (sx * 0.55, 3.1, 4.7), (sx * 0.85, 3.6, 4.55),
         (sx * 0.95, 4.05, 4.2), (sx * 0.80, 4.4, 3.85), (sx * 0.55, 4.55, 3.6)]
    for j in range(len(p) - 1):
        seg(p[j], p[j + 1], 0.035 * (1 - j * 0.13), 0.035 * (1 - (j + 1) * 0.13), M_horn, v=5)
    ico(p[-1], 0.03, M_horn, 1)
# chin beard
for sx in [-1, 1]:
    p = [(sx * 0.12, 2.35, 3.85), (sx * 0.18, 2.5, 3.45), (sx * 0.12, 2.55, 3.05)]
    for j in range(len(p) - 1):
        seg(p[j], p[j + 1], 0.03, 0.02, M_horn, v=5)

# green mane down the neck
mane = [(0.95, 1.0, 4.95), (0.85, 0.6, 4.6), (0.55, 0.1, 4.05), (0.2, 0.3, 3.4),
        (-0.05, -0.1, 2.85), (0.05, 0.4, 2.3)]
for i, (mx, my, mz) in enumerate(mane):
    s = 1.0 - i * 0.08
    seg((mx, my, mz), (mx, my - 0.55 * s, mz + 0.45 * s), 0.18 * s, 0.02, M_green, v=6)
    for sx in [-1, 1]:
        seg((mx + sx * 0.18 * s, my, mz), (mx + sx * 0.42 * s, my - 0.4 * s, mz + 0.3 * s), 0.12 * s, 0.015, M_greenD, v=5)
# cheek frills
for sx in [-1, 1]:
    ico((sx * 0.5, 1.35, 4.5), 0.22, M_green, 2, (0.5, 1.1, 1.3), (0, sx * 0.4, 0))
    seg((sx * 0.52, 1.5, 4.45), (sx * 0.75, 1.2, 4.2), 0.12, 0.02, M_greenL, v=5)

# ============================================================
# 4. RED SPINE FINS along the back (dorsal ridge of flames)
# ============================================================
for i in range(2, len(PTS) - 1):
    p = mathutils.Vector(PTS[i][:3]); r = PTS[i][3]
    d, t = dorsal(i)
    root = p + d * (r * 0.3)
    tip = p + d * (r + 0.45) - t * 0.12
    seg(root, tip, 0.10, 0.01, M_red, v=5)
    # side mini fins
    side = t.cross(d).normalized()
    for sx in [-1, 1]:
        seg(p + side * sx * r * 0.5, p + d * (r + 0.22) + side * sx * r * 0.7 - t * 0.1, 0.05, 0.008, M_orange, v=4)

# ============================================================
# 5. FOUR LEGS (gold, clawed) + red fur tufts
# ============================================================
def claw_foot(foot, fwd, m_claw=M_teeth):
    fwd = mathutils.Vector(fwd).normalized()
    side = fwd.cross(mathutils.Vector((0, 0, 1)))
    if side.length < 1e-3: side = mathutils.Vector((1, 0, 0))
    side = side.normalized()
    foot = mathutils.Vector(foot)
    for k in (-1, 0, 1):
        toe = foot + fwd * 0.18 + side * k * 0.14
        tip = toe + fwd * 0.16 - mathutils.Vector((0, 0, 0.12)) + side * k * 0.05
        seg(foot, toe, 0.07, 0.05, M_gold, v=5)
        seg(toe, tip, 0.045, 0.006, m_claw, v=5)
    # dewclaw back
    bt = foot - fwd * 0.10
    seg(bt, bt - fwd * 0.08 - mathutils.Vector((0, 0, 0.10)), 0.03, 0.005, m_claw, v=4)

def leg(chain, foot, fwd):
    for j in range(len(chain) - 1):
        rb = 0.20 - j * 0.03; rt = 0.20 - (j + 1) * 0.03
        seg(chain[j], chain[j + 1], max(rb, 0.08), max(rt, 0.07), M_gold, v=7)
    # red fur tuft at shoulder
    sh = mathutils.Vector(chain[0])
    for a in range(4):
        ang = a * math.pi / 2
        off = mathutils.Vector((math.cos(ang) * 0.18, math.sin(ang) * 0.18, 0.12))
        seg(sh, sh + off, 0.07, 0.008, M_red, v=4)
    claw_foot(foot, fwd)

# front legs (near chest z~2.4)
leg([(-0.45, 0.10, 2.25), (-0.85, 0.55, 1.75), (-0.98, 1.0, 1.25), (-0.98, 1.30, 0.98)],
    (-0.98, 1.30, 0.98), (0.1, 1.0, -0.5))
leg([(0.55, 0.05, 2.30), (0.95, 0.50, 1.80), (1.05, 0.95, 1.30), (1.05, 1.25, 1.02)],
    (1.05, 1.25, 1.02), (-0.1, 1.0, -0.5))
# back legs (near hip z~1.0)
leg([(0.55, -0.35, 1.15), (0.95, -0.05, 0.70), (1.02, 0.40, 0.40), (1.02, 0.72, 0.20)],
    (1.02, 0.72, 0.20), (-0.1, 1.0, -0.4))
leg([(-0.50, -0.45, 1.05), (-0.92, -0.15, 0.62), (-1.0, 0.30, 0.35), (-1.0, 0.62, 0.18)],
    (-1.0, 0.62, 0.18), (0.1, 1.0, -0.4))

# ============================================================
# 6. FLAME TAIL TUFT
# ============================================================
ttip = mathutils.Vector(PTS[-1][:3])
tdir = (ttip - mathutils.Vector(PTS[-3][:3])).normalized()
fan_side = tdir.cross(mathutils.Vector((0, 0, 1))).normalized()
for k in (-2, -1, 0, 1, 2):
    base = ttip
    flame_dir = (tdir + fan_side * k * 0.35 + mathutils.Vector((0, 0, 0.3))).normalized()
    L = 0.9 - abs(k) * 0.12
    mid = base + flame_dir * L * 0.55
    tip = base + flame_dir * L
    seg(base, mid, 0.16, 0.10, M_red, v=6)
    seg(mid, tip, 0.10, 0.01, M_orange, v=6)

# ============================================================
# 7. GREEN BELLY BANDS (accent rings near lower body / tail)
# ============================================================
for i in (5, 6, 8, 9):
    p = mathutils.Vector(PTS[i][:3]); r = PTS[i][3]
    d, t = dorsal(i)
    ico(p - d * r * 0.5, r * 0.95, M_greenL, 2, (1.0, 0.35, 1.0),
        t.to_track_quat('Z', 'Y').to_euler())

# ============================================================
# JOIN ALL -> 'Naga'
# ============================================================
bpy.ops.object.select_all(action='DESELECT')
for o in OBS:
    if o and o.name in bpy.data.objects:
        o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
naga = bpy.context.active_object
naga.name = 'Naga'
bpy.ops.object.shade_smooth()
# origin to geometry, sit near origin
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
naga.location = (0, 0, 0)

print("NAGA built:", len(naga.data.vertices), "v", len(naga.data.polygons), "f")

# ============================================================
# EXPORT OBJ (both locations) + SAVE BLEND
# ============================================================
for p in ["E:/Game Research/Lembah Karsa 3D/assets/models/naga.obj",
          "E:/Game Research/Lembah Karsa 3D/game/assets/models/naga.obj"]:
    bpy.ops.wm.obj_export(filepath=p, export_selected_objects=True, export_materials=True,
                          apply_modifiers=True, forward_axis='NEGATIVE_Y', up_axis='Z')
bpy.ops.wm.save_as_mainfile(filepath="E:/Game Research/Lembah Karsa 3D/naga_dragon.blend")
print("Exported OBJ + saved naga_dragon.blend")
