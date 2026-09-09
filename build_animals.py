import bpy, math, mathutils, os

# ============================================================
# BUILD KAMPUNG ANIMALS — atomic: build each, export OBJ, group render
# ============================================================
WT = "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd"
EXPORT_DIRS = [WT + "/game/assets/models", WT + "/assets/models"]
for d in EXPORT_DIRS:
    os.makedirs(d, exist_ok=True)

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for m in list(bpy.data.materials):
    if m.users == 0: bpy.data.materials.remove(m)

def mat(name, col, rough=0.7, emit=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1.0)
    b.inputs['Roughness'].default_value = rough
    if emit > 0:
        b.inputs['Emission Color'].default_value = (*col, 1.0)
        b.inputs['Emission Strength'].default_value = emit
    return m

# palette
C = dict(
    white=mat('A_White',(0.90,0.89,0.85)), cream=mat('A_Cream',(0.86,0.78,0.60)),
    brown=mat('A_Brown',(0.45,0.30,0.16)), dbrown=mat('A_DBrown',(0.28,0.18,0.10)),
    gray=mat('A_Gray',(0.52,0.52,0.55)), dgray=mat('A_DGray',(0.30,0.30,0.32)),
    tan=mat('A_Tan',(0.72,0.58,0.38)), black=mat('A_Black',(0.06,0.06,0.07)),
    orange=mat('A_Orange',(0.92,0.55,0.10)), red=mat('A_Red',(0.78,0.14,0.10)),
    pink=mat('A_Pink',(0.92,0.62,0.62)), yellow=mat('A_Yellow',(0.95,0.80,0.20)),
    green=mat('A_EyeGrn',(0.30,0.70,0.25),0.2,0.4), eye=mat('A_Eye',(0.05,0.05,0.06),0.2),
)

P = []  # current animal parts
def ico(loc,r,m,sub=2,sc=(1,1,1),rot=(0,0,0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=r,location=loc)
    o=bpy.context.active_object; o.scale=sc; o.rotation_euler=rot
    bpy.ops.object.transform_apply(scale=True,rotation=True)
    o.data.materials.append(m); P.append(o); return o
def cyl(loc,rad,depth,m,rot=(0,0,0),v=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=rad,depth=depth,location=loc)
    o=bpy.context.active_object; o.rotation_euler=rot
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o
def cone(loc,r1,r2,d,m,rot=(0,0,0),v=7):
    bpy.ops.mesh.primitive_cone_add(vertices=v,radius1=r1,radius2=r2,depth=d,location=loc)
    o=bpy.context.active_object; o.rotation_euler=rot
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o
def seg(p0,p1,rb,rt,m,v=6):
    p0=mathutils.Vector(p0); p1=mathutils.Vector(p1); d=p1-p0; L=d.length
    if L<1e-5: return
    bpy.ops.mesh.primitive_cone_add(vertices=v,radius1=rb,radius2=rt,depth=L,location=(p0+p1)/2)
    o=bpy.context.active_object; o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(m); P.append(o); return o

DONE = []
def finish(name, x_off):
    global P
    bpy.ops.object.select_all(action='DESELECT')
    for o in P: o.select_set(True)
    bpy.context.view_layer.objects.active = P[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object; obj.name = name
    bpy.ops.object.shade_smooth()
    # export centered at origin
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for d in EXPORT_DIRS:
        bpy.ops.wm.obj_export(filepath=d+"/"+name+".obj", export_selected_objects=True,
            export_materials=True, apply_modifiers=True, forward_axis='NEGATIVE_Y', up_axis='Z')
    obj.location.x = x_off  # move for group render
    DONE.append(name); P = []
    return obj

# ============================================================
# AYAM (chicken)
# ============================================================
def build_ayam():
    for sx in (-1,1):
        cyl((sx*0.10,0.02,0.13),0.035,0.26,C['orange'])
        ico((sx*0.10,0.10,0.02),0.05,C['orange'],1,(1.4,1,1))  # foot
    ico((0,0,0.42),0.30,C['white'],3,(1.0,1.35,1.05))          # body
    for sx in (-1,1): ico((sx*0.27,-0.02,0.44),0.16,C['white'],2,(0.5,1.1,1.0))  # wings
    ico((0,0.26,0.64),0.165,C['white'],2)                       # head
    cone((0,0.45,0.63),0.06,0.005,0.16,C['orange'],(math.pi/2*-1,0,0))  # beak (+Y)
    ico((0,0.36,0.52),0.05,C['red'],1,(1,1,1.4))                # wattle
    for k in (-1,0,1): cone((k*0.05,0.24,0.80),0.04,0.005,0.12,C['red'],(0.2*k,0,0))  # comb
    for sx in (-1,1): ico((sx*0.07,0.34,0.68),0.025,C['eye'],1)
    for k in (-1,0,1):                                           # tail feathers
        cone((k*0.06,-0.30,0.58),0.05,0.01,0.34,C['dbrown'],(-0.9,0,k*0.2))
    return finish('mob_ayam', -6.5)

# ============================================================
# BEBEK (duck)
# ============================================================
def build_bebek():
    for sx in (-1,1):
        cyl((sx*0.10,0.02,0.10),0.03,0.20,C['orange'])
        ico((sx*0.10,0.12,0.01),0.07,C['orange'],1,(1.6,1.3,0.4))  # webbed foot
    ico((0,0,0.36),0.32,C['white'],3,(1.0,1.5,0.92))            # body
    cone((0,-0.34,0.5),0.13,0.01,0.3,C['white'],(-2.4,0,0))     # upturned tail
    seg((0,0.22,0.46),(0,0.34,0.64),0.12,0.13,C['white'])       # neck
    ico((0,0.36,0.66),0.16,C['white'],2)                        # head
    box((0,0.54,0.62),(0.18,0.20,0.05),C['orange'])             # bill
    for sx in (-1,1): ico((sx*0.08,0.40,0.70),0.025,C['eye'],1)
    return finish('mob_bebek', -3.9)

def box(loc,sc,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.active_object; o.scale=sc; o.rotation_euler=rot
    bpy.ops.object.transform_apply(scale=True,rotation=True)
    o.data.materials.append(m); P.append(o); return o

# ============================================================
# KUCING (cat)
# ============================================================
def build_kucing():
    for sx in (-1,1):
        for sy in (-1,1):
            cyl((sx*0.14,sy*0.26,0.18),0.04,0.36,C['gray'])
    ico((0,0,0.42),0.26,C['gray'],3,(1.0,1.7,0.92))            # body
    ico((0,0.42,0.56),0.20,C['gray'],2)                         # head
    for sx in (-1,1):                                           # ears
        cone((sx*0.12,0.42,0.74),0.09,0.005,0.16,C['gray'],(0,0,0))
        cone((sx*0.12,0.44,0.73),0.05,0.004,0.12,C['pink'],(0,0,0))
    ico((0,0.58,0.50),0.10,C['gray'],2,(1,1,0.8))               # snout
    ico((0,0.66,0.50),0.03,C['pink'],1)                         # nose
    for sx in (-1,1): ico((sx*0.09,0.56,0.60),0.04,C['green'],1)
    for sx in (-1,1):                                           # whiskers
        seg((sx*0.06,0.62,0.50),(sx*0.30,0.70,0.52),0.006,0.002,C['white'],4)
    p=[(0,-0.34,0.45),(0,-0.55,0.55),(0,-0.62,0.78),(0,-0.5,0.95)]  # tail curl
    for j in range(len(p)-1): seg(p[j],p[j+1],0.05-j*0.01,0.045-j*0.01,C['gray'])
    return finish('mob_kucing', -1.3)

# ============================================================
# KAMBING (goat)
# ============================================================
def build_kambing():
    for sx in (-1,1):
        for sy in (-1,1):
            cyl((sx*0.16,sy*0.28,0.30),0.05,0.60,C['cream'])
            cyl((sx*0.16,sy*0.28,0.03),0.06,0.08,C['dgray'])   # hoof
    ico((0,0,0.66),0.30,C['cream'],3,(1.0,1.6,0.95))           # body
    ico((0,0.40,0.80),0.17,C['cream'],2)                        # head
    ico((0,0.56,0.74),0.11,C['cream'],2,(0.9,1.1,0.8))          # snout
    cone((0,0.64,0.66),0.04,0.02,0.10,C['white'],(-1.3,0,0))    # beard
    for sx in (-1,1):                                           # horns curving back
        p=[(sx*0.08,0.30,0.94),(sx*0.10,0.10,1.04),(sx*0.10,-0.10,1.02)]
        for j in range(len(p)-1): seg(p[j],p[j+1],0.04,0.02,C['dgray'])
    for sx in (-1,1): cone((sx*0.18,0.40,0.80),0.07,0.01,0.16,C['cream'],(0,sx*1.2,0))  # ears
    for sx in (-1,1): ico((sx*0.09,0.50,0.82),0.028,C['eye'],1)
    cone((0,-0.34,0.66),0.05,0.01,0.18,C['cream'],(2.4,0,0))    # tail
    return finish('mob_kambing', 1.3)

# ============================================================
# SAPI (cow)
# ============================================================
def build_sapi():
    for sx in (-1,1):
        for sy in (-1,1):
            cyl((sx*0.26,sy*0.42,0.42),0.08,0.84,C['brown'])
            cyl((sx*0.26,sy*0.42,0.04),0.09,0.10,C['dgray'])   # hoof
    ico((0,0,0.92),0.46,C['brown'],3,(1.0,1.55,0.95))          # body
    for (px,py,pz,s) in [(0.2,0.3,1.1,0.22),(-0.25,-0.2,1.0,0.26)]:
        ico((px,py,pz),s,C['white'],2,(1.0,0.9,0.6))           # white patches
    ico((0,0.62,0.98),0.26,C['brown'],2)                        # head
    ico((0,0.86,0.90),0.16,C['pink'],2,(1.1,0.8,0.9))           # muzzle
    for sx in (-1,1): ico((sx*0.06,0.95,0.90),0.03,C['dgray'],1)  # nostrils
    for sx in (-1,1):                                           # horns
        seg((sx*0.16,0.55,1.16),(sx*0.30,0.60,1.22),0.04,0.01,C['cream'])
    for sx in (-1,1): cone((sx*0.28,0.55,1.02),0.09,0.01,0.18,C['brown'],(0,sx*1.4,0))  # ears
    for sx in (-1,1): ico((sx*0.12,0.74,1.04),0.035,C['eye'],1)
    p=[(0,-0.5,0.9),(0,-0.62,0.6),(0,-0.6,0.3)]                 # tail
    for j in range(len(p)-1): seg(p[j],p[j+1],0.04,0.03,C['brown'])
    ico((0,-0.58,0.22),0.06,C['dbrown'],1)                      # tail tuft
    ico((0,-0.1,0.55),0.13,C['pink'],2,(1.0,1.0,0.7))           # udder
    return finish('mob_sapi', 4.0)

# ============================================================
# KELINCI (rabbit)
# ============================================================
def build_kelinci():
    ico((0,0,0.30),0.26,C['white'],3,(1.0,1.25,1.05))          # body
    ico((0,0.24,0.46),0.17,C['white'],2)                        # head
    for sx in (-1,1):                                           # long ears
        cone((sx*0.07,0.20,0.78),0.06,0.02,0.40,C['white'],(-0.2,0,sx*0.12))
        cone((sx*0.07,0.23,0.78),0.035,0.01,0.34,C['pink'],(-0.2,0,sx*0.12))
    ico((0,0.38,0.42),0.04,C['pink'],1)                         # nose
    for sx in (-1,1): ico((sx*0.08,0.34,0.48),0.03,C['red'],1)  # eyes
    for sx in (-1,1): ico((sx*0.16,0.05,0.20),0.12,C['white'],2,(1.0,1.3,0.9))  # haunches
    for sx in (-1,1): cyl((sx*0.10,0.20,0.12),0.035,0.22,C['white'])  # front legs
    ico((0,-0.28,0.30),0.10,C['white'],2)                       # fluffy tail
    return finish('mob_kelinci', 6.5)

# build order — note: box() defined after build_bebek uses it, so define earlier
build_ayam()
build_bebek()
build_kucing()
build_kambing()
build_sapi()
build_kelinci()

print("ANIMALS DONE:", ", ".join(DONE))

# ============================================================
# GROUP RENDER + SAVE BLEND
# ============================================================
bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,0))
gp=bpy.context.active_object
gm=bpy.data.materials.new('GA_Gnd'); gm.use_nodes=True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.10,0.11,0.10,1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=0.95
gp.data.materials.append(gm)

for loc,e,c in [((6,-9,10),900,(1,0.95,0.85)),((-8,-6,7),500,(0.5,0.6,1.0)),((0,9,7),400,(1,0.7,0.5))]:
    bpy.ops.object.light_add(type='POINT',location=loc); l=bpy.context.active_object; l.data.energy=e; l.data.color=c
bpy.ops.object.light_add(type='SUN'); s=bpy.context.active_object; s.data.energy=0.7; s.rotation_euler=(0.5,0.1,0.3)

sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=48; sc.cycles.use_denoising=True
sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.05,0.05,0.07,1)
sc.render.resolution_x=1600; sc.render.resolution_y=480
import mathutils
def look_at(cam,t):
    d=mathutils.Vector(t)-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,-9,3.2)); cam=bpy.context.active_object
look_at(cam,(0,0,0.55)); cam.data.lens=55; sc.camera=cam
sc.render.filepath="E:/Game Research/Lembah Karsa 3D/kampung_animals.png"
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath="E:/Game Research/Lembah Karsa 3D/kampung_animals.blend")
print("Group render + blend saved.")
