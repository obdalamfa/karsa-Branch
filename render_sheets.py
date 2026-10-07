import bpy, math, mathutils

MAIN = "E:/Game Research/Lembah Karsa 3D/assets/models"

def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for im in list(bpy.data.images):
        if im.users == 0: bpy.data.images.remove(im)

def look_at(cam, t):
    d = mathutils.Vector(t) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()

def setup_scene(bgcol=(0.10,0.10,0.115,1)):
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0,0,0))
    gp = bpy.context.active_object
    gm = bpy.data.materials.new('SheetGnd'); gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.14,0.14,0.13,1)
    gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.95
    gp.data.materials.append(gm)
    for loc, e, c in [((8,-12,12),900,(1,0.96,0.88)),((-10,-8,9),520,(0.6,0.68,1.0)),((0,8,9),380,(1,0.75,0.55))]:
        bpy.ops.object.light_add(type='POINT', location=loc); l = bpy.context.active_object
        l.data.energy = e; l.data.color = c
    bpy.ops.object.light_add(type='SUN'); s = bpy.context.active_object
    s.data.energy = 1.0; s.rotation_euler = (0.55, 0.1, -0.3)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 56; sc.cycles.use_denoising = True
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = bgcol
    return sc

# ── SHEET 1: 14 NPC v2 ──
clear()
NPCS = ['npc_arya','npc_sari','npc_raka','npc_maya','npc_budi','npc_joko','npc_ningsih',
        'npc_cici','npc_bowo','npc_pak_guru','npc_mbok_jum','npc_jaka_ronda',
        'npc_kapten_kuro','npc_kru_kuro']
for i, n in enumerate(NPCS):
    try:
        bpy.ops.wm.obj_import(filepath=MAIN + "/" + n + ".obj",
                              forward_axis='NEGATIVE_Y', up_axis='Z')
        o = [m for m in bpy.context.selected_objects if m.type == 'MESH'][0]
        col = i % 7; row = i // 7
        o.location = ((col - 3) * 1.15, -row * 2.0, 0)
        o.rotation_euler = (0, 0, 0)
    except Exception as e:
        print("skip", n, e)
sc = setup_scene()
sc.render.resolution_x = 1700; sc.render.resolution_y = 760
bpy.ops.object.camera_add(location=(0, -9.5, 2.4)); cam = bpy.context.active_object
look_at(cam, (0, -1.0, 0.95)); cam.data.lens = 50; sc.camera = cam
sc.render.filepath = "E:/Game Research/Lembah Karsa 3D/npcs_v2_sheet.png"
bpy.ops.render.render(write_still=True)
print("SHEET NPC done")

# ── SHEET 2: 9 props v2 ──
clear()
PROPS = ['prop_scarecrow','prop_kandang_ayam','prop_gerobak','prop_cangkul','prop_ember',
         'prop_jerami','prop_peti_sayur','prop_karung','prop_pagar_kayu']
for i, n in enumerate(PROPS):
    try:
        bpy.ops.wm.obj_import(filepath=MAIN + "/" + n + ".obj",
                              forward_axis='NEGATIVE_Y', up_axis='Z')
        o = [m for m in bpy.context.selected_objects if m.type == 'MESH'][0]
        col = i % 5; row = i // 5
        o.location = ((col - 2) * 2.1, -row * 2.4, 0)
        o.rotation_euler = (0, 0, math.pi*0.12)
    except Exception as e:
        print("skip", n, e)
sc = setup_scene()
sc.render.resolution_x = 1700; sc.render.resolution_y = 740
bpy.ops.object.camera_add(location=(0, -8.5, 3.4)); cam = bpy.context.active_object
look_at(cam, (0, -1.2, 0.65)); cam.data.lens = 48; sc.camera = cam
sc.render.filepath = "E:/Game Research/Lembah Karsa 3D/props_v2_sheet.png"
bpy.ops.render.render(write_still=True)
print("SHEET PROPS done")
