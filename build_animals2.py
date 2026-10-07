import bpy, math, mathutils, os

# ============================================================
# BUILD KAMPUNG ANIMALS (batch 2): domba, kuda, rubah, jago
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

C = dict(
    white=mat('A_White',(0.90,0.89,0.85)), cream=mat('A_Cream',(0.86,0.78,0.60)),
    brown=mat('A_Brown',(0.45,0.30,0.16)), dbrown=mat('A_DBrown',(0.26,0.16,0.09)),
    gray=mat('A_Gray',(0.52,0.52,0.55)), dgray=mat('A_DGray',(0.24,0.24,0.26)),
    tan=mat('A_Tan',(0.72,0.58,0.38)), black=mat('A_Black',(0.06,0.06,0.07)),
    orange=mat('A_FoxOrange',(0.82,0.40,0.12)), red=mat('A_Red',(0.80,0.13,0.09)),
    pink=mat('A_Pink',(0.92,0.62,0.62)), yellow=mat('A_Yellow',(0.95,0.78,0.18)),
    eye=mat('A_Eye',(0.05,0.05,0.06),0.2), irid=mat('A_Irid',(0.06,0.22,0.17)),
)

P = []
def box(loc,sc,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.active_object; o.scale=sc; o.rotation_euler=rot
    bpy.ops.object.transform_apply(scale=True,rotation=True)
    o.data.materials.append(m); P.append(o); return o
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

DONE=[]
def finish(name,x_off):
    global P
    bpy.ops.object.select_all(action='DESELECT')
    for o in P: o.select_set(True)
    bpy.context.view_layer.objects.active=P[0]
    bpy.ops.object.join()
    obj=bpy.context.active_object; obj.name=name
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    for d in EXPORT_DIRS:
        bpy.ops.wm.obj_export(filepath=d+"/"+name+".obj",export_selected_objects=True,
            export_materials=True,apply_modifiers=True,forward_axis='NEGATIVE_Y',up_axis='Z')
    obj.location.x=x_off
    DONE.append(name); P=[]
    return obj

# ---------- DOMBA (sheep) ----------
def domba():
    for sx in (-1,1):
        for sy in (-1,1):
            cyl((sx*0.14,sy*0.22,0.18),0.04,0.36,C['dgray'])
    ico((0,0,0.52),0.34,C['white'],3,(1.0,1.4,1.05))
    for (dx,dy,dz,r) in [(0.2,0.22,0.64,0.17),(-0.2,0.22,0.64,0.17),(0.2,-0.22,0.64,0.17),
                         (-0.2,-0.22,0.64,0.17),(0,0,0.76,0.20),(0.24,0,0.5,0.15),(-0.24,0,0.5,0.15),
                         (0,0.28,0.6,0.15)]:
        ico((dx,dy,dz),r,C['white'],2)
    ico((0,0.44,0.54),0.15,C['dgray'],2,(0.9,1.05,1.1))     # face
    for sx in (-1,1): cone((sx*0.15,0.44,0.56),0.055,0.008,0.15,C['dgray'],(0,sx*1.4,0))  # ears
    for sx in (-1,1): ico((sx*0.07,0.54,0.57),0.025,C['eye'],1)
    ico((0,-0.34,0.52),0.09,C['white'],2)
    return finish('mob_domba',-3.75)

# ---------- KUDA (horse) ----------
def kuda():
    for sx in (-1,1):
        for sy in (-1,1):
            cyl((sx*0.16,sy*0.34,0.36),0.055,0.72,C['brown'])
            cyl((sx*0.16,sy*0.34,0.05),0.06,0.12,C['dgray'])
    ico((0,0,0.82),0.35,C['brown'],3,(1.0,1.7,0.95))
    seg((0,0.46,0.92),(0,0.72,1.30),0.20,0.13,C['brown'])           # neck
    ico((0,0.80,1.36),0.15,C['brown'],2,(0.85,1.45,0.95))          # head
    ico((0,0.96,1.28),0.10,C['brown'],2)                           # muzzle
    for sx in (-1,1): ico((sx*0.05,1.04,1.26),0.02,C['black'],1)
    for sx in (-1,1): cone((sx*0.07,0.68,1.46),0.045,0.005,0.13,C['brown'],(-0.2,0,sx*0.15))
    for sx in (-1,1): ico((sx*0.10,0.86,1.38),0.03,C['black'],1)
    # mane
    for t in range(6):
        f=t/5.0; mx=0; my=0.5+0.30*f; mz=0.95+0.42*f
        cone((mx,my-0.06,mz),0.08,0.01,0.16,C['dgray'],(0.5,0,0))
    # tail
    p=[(0,-0.52,0.85),(0,-0.62,0.5),(0,-0.58,0.18)]
    for j in range(len(p)-1): seg(p[j],p[j+1],0.07-j*0.01,0.06-j*0.01,C['dgray'])
    return finish('mob_kuda',-1.25)

# ---------- RUBAH (fox) ----------
def rubah():
    for sx in (-1,1):
        for sy in (-1,1):
            cyl((sx*0.13,sy*0.24,0.18),0.035,0.36,C['orange'])
            cyl((sx*0.13,sy*0.24,0.05),0.038,0.12,C['black'])
    ico((0,0,0.42),0.24,C['orange'],3,(1.0,1.6,0.9))
    ico((0,0.22,0.32),0.15,C['white'],2,(1.0,1.0,0.75))            # white chest
    ico((0,0.42,0.50),0.17,C['orange'],2)                          # head
    cone((0,0.60,0.46),0.10,0.015,0.24,C['white'],(-math.pi/2,0,0))# snout
    ico((0,0.72,0.46),0.03,C['black'],1)                           # nose
    for sx in (-1,1):
        cone((sx*0.10,0.40,0.70),0.07,0.004,0.22,C['orange'],(0,0,sx*0.10))
        cone((sx*0.10,0.41,0.76),0.035,0.003,0.12,C['black'],(0,0,sx*0.10))
    for sx in (-1,1): ico((sx*0.08,0.52,0.55),0.03,C['eye'],1)
    # bushy tail
    p=[(0,-0.28,0.42),(0,-0.52,0.5),(0,-0.74,0.64)]
    seg(p[0],p[1],0.14,0.15,C['orange']); seg(p[1],p[2],0.15,0.09,C['orange'])
    ico((0,-0.80,0.68),0.10,C['white'],2)                          # white tip
    return finish('mob_rubah',1.25)

# ---------- JAGO (rooster) ----------
def jago():
    for sx in (-1,1):
        cyl((sx*0.11,0.0,0.17),0.035,0.34,C['yellow'])
        ico((sx*0.11,0.10,0.01),0.05,C['yellow'],1,(1.4,1.5,0.6))
        cone((sx*0.11,-0.04,0.10),0.02,0.004,0.10,C['yellow'],(0.5,0,0))  # spur
    ico((0,0,0.50),0.32,C['dbrown'],3,(1.0,1.25,1.15))             # body
    for sx in (-1,1): ico((sx*0.30,-0.02,0.52),0.17,C['brown'],2,(0.5,1.0,1.25))  # wings
    seg((0,0.20,0.64),(0,0.26,0.86),0.16,0.10,C['yellow'])         # golden hackle neck
    ico((0,0.30,0.94),0.15,C['brown'],2)                           # head
    for k in (-1.5,-0.5,0.5,1.5):                                  # tall comb
        cone((k*0.045,0.24,1.12),0.05,0.006,0.20,C['red'],(0.15*k,0,0))
    ico((0,0.40,0.82),0.07,C['red'],2,(1,1,1.6))                   # wattle
    cone((0,0.47,0.92),0.05,0.005,0.15,C['yellow'],(-math.pi/2,0,0))  # beak
    for sx in (-1,1): ico((sx*0.07,0.39,0.97),0.025,C['eye'],1)
    # long arching sickle tail
    tail=[(0,-0.30,0.62),(0,-0.55,0.9),(0,-0.62,1.25),(0,-0.42,1.55)]
    for ox in (-0.07,0.0,0.07):
        for j in range(len(tail)-1):
            a=(tail[j][0]+ox,tail[j][1],tail[j][2]); b=(tail[j+1][0]+ox,tail[j+1][1],tail[j+1][2])
            seg(a,b,0.05-j*0.008,0.045-j*0.008,C['irid'])
    return finish('mob_jago',3.75)

domba(); kuda(); rubah(); jago()
print("BATCH2 DONE:", ", ".join(DONE))

# ---------- GROUP RENDER + SAVE ----------
order=DONE[:]
for i,n in enumerate(order):
    o=bpy.data.objects[n]; o.location=( (i-1.5)*2.6, 0, 0); o.rotation_euler=(0,0,math.pi)
bpy.ops.mesh.primitive_plane_add(size=40,location=(0,0,0))
gp=bpy.context.active_object
gm=bpy.data.materials.new('GA2_Gnd'); gm.use_nodes=True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.10,0.11,0.10,1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=0.95
gp.data.materials.append(gm)
for loc,e,c in [((5,-8,8),360,(1,0.96,0.88)),((-7,-6,6),200,(0.55,0.65,1.0)),((0,7,6),170,(1,0.7,0.5))]:
    bpy.ops.object.light_add(type='POINT',location=loc); l=bpy.context.active_object; l.data.energy=e; l.data.color=c
bpy.ops.object.light_add(type='SUN'); s=bpy.context.active_object; s.data.energy=0.6; s.rotation_euler=(0.5,0.1,-0.3)
def look_at(cam,t):
    d=mathutils.Vector(t)-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=56; sc.cycles.use_denoising=True
sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.05,0.055,0.07,1)
sc.render.resolution_x=1400; sc.render.resolution_y=620
bpy.ops.object.camera_add(location=(0,-11,3.4)); cam=bpy.context.active_object
look_at(cam,(0,0,0.7)); cam.data.lens=42; sc.camera=cam
sc.render.filepath="E:/Game Research/Lembah Karsa 3D/kampung_animals2.png"
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath="E:/Game Research/Lembah Karsa 3D/kampung_animals2.blend")
print("Batch2 render + blend saved.")
