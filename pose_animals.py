import bpy, os, math, mathutils

# ============================================================
# POSE ANIMATION — generate idle/walk1/walk2 pose OBJs per animal
# via procedural vertex deformation (legs swing, body bob).
# Texture/UV preserved (only vertex positions change).
# Game swaps mesh per frame for a no-rig walk cycle.
# ============================================================
WT = "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd"
EXPORT_DIRS = [WT + "/game/assets/models", WT + "/assets/models"]
SRC = WT + "/assets/models"

NAMES = ['mob_ayam','mob_bebek','mob_kucing','mob_kambing','mob_sapi',
         'mob_kelinci','mob_domba','mob_kuda','mob_rubah','mob_jago']
POSES = {'idle': 0.0, 'walk1': 1.0, 'walk2': -1.0}

def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for im in list(bpy.data.images):
        if im.users == 0: bpy.data.images.remove(im)

def deform(me, phase, zmin, zmax):
    if abs(phase) < 1e-6:
        return  # idle = neutral
    H = max(zmax - zmin, 1e-4)
    body_z = zmin + 0.42 * H
    swing = 0.28 * H * phase
    for v in me.vertices:
        x, y, z = v.co
        if z < body_z:                              # legs
            lf = (body_z - z) / (body_z - zmin + 1e-6)   # 0 at body .. 1 at foot
            side = 1.0 if x >= 0 else -1.0
            v.co.y += swing * lf * side
            if side * phase > 0:                    # lift forward-swinging leg
                v.co.z += 0.14 * H * lf
        else:                                        # body
            bf = (z - body_z) / (zmax - body_z + 1e-6)
            v.co.z += 0.05 * H * abs(phase) * bf     # bob up while striding

done = []
for name in NAMES:
    clear()
    src_obj = SRC + "/" + name + ".obj"
    if not os.path.exists(src_obj):
        print("MISSING:", name); continue
    bpy.ops.wm.obj_import(filepath=src_obj, forward_axis='NEGATIVE_Y', up_axis='Z')
    base = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
    base.name = name + "_base"
    vs = [v.co.z for v in base.data.vertices]
    zmin, zmax = min(vs), max(vs)
    for pose, phase in POSES.items():
        dup = base.copy(); dup.data = base.data.copy(); dup.name = name + "_" + pose
        bpy.context.collection.objects.link(dup)
        deform(dup.data, phase, zmin, zmax)
        bpy.ops.object.select_all(action='DESELECT')
        dup.select_set(True); bpy.context.view_layer.objects.active = dup
        for d in EXPORT_DIRS:
            for attempt in range(3):
                try:
                    bpy.ops.wm.obj_export(filepath=d + "/" + name + "_" + pose + ".obj",
                        export_selected_objects=True, export_materials=True, apply_modifiers=True,
                        forward_axis='NEGATIVE_Y', up_axis='Z', path_mode='STRIP')
                    break
                except Exception as e:
                    print("  retry", attempt, name, pose, ":", e)
        bpy.data.objects.remove(dup, do_unlink=True)
    done.append(name)
    print("POSED:", name)

print("DONE POSES:", ", ".join(done))

# ============================================================
# DEMO RENDER — one animal's 3 poses side by side (mob_kambing)
# ============================================================
clear()
demo = 'mob_kambing'
for i, pose in enumerate(['idle','walk1','walk2']):
    bpy.ops.wm.obj_import(filepath=SRC + "/" + demo + "_" + pose + ".obj", forward_axis='NEGATIVE_Y', up_axis='Z')
    o = [m for m in bpy.context.selected_objects if m.type == 'MESH'][0]
    o.location = ((i - 1) * 1.8, 0, 0); o.rotation_euler = (0, 0, math.radians(125))

bpy.ops.mesh.primitive_plane_add(size=30, location=(0,0,0))
gp = bpy.context.active_object
gm = bpy.data.materials.new('PoseGnd'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.12,0.13,0.12,1)
gp.data.materials.append(gm)
for loc,e,c in [((5,-7,8),360,(1,0.95,0.85)),((-6,-5,6),220,(0.55,0.65,1)),((0,6,6),170,(1,0.72,0.5))]:
    bpy.ops.object.light_add(type='POINT',location=loc); l=bpy.context.active_object; l.data.energy=e; l.data.color=c
bpy.ops.object.light_add(type='SUN'); s=bpy.context.active_object; s.data.energy=0.8; s.rotation_euler=(0.6,0.1,-0.2)
def look_at(cam,t):
    d=mathutils.Vector(t)-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=56; sc.cycles.use_denoising=True
sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.08,0.085,0.10,1)
sc.render.resolution_x=1500; sc.render.resolution_y=620
bpy.ops.object.camera_add(location=(0,-7,2.6)); cam=bpy.context.active_object
look_at(cam,(0,0,0.55)); cam.data.lens=42; sc.camera=cam
sc.render.filepath="E:/Game Research/Lembah Karsa 3D/pose_demo.png"
bpy.ops.render.render(write_still=True)
print("Demo render done (idle | walk1 | walk2)")
