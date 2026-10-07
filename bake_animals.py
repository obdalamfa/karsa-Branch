import bpy, os, math, mathutils

# ============================================================
# TEXTURE BAKE — animals: fur/skin (Noise) -> diffuse PNG.
# Bakes from the ORIGINAL multi-material objects in the source .blend
# (NOT the already-baked single-material OBJs) via libraries.load append.
# ============================================================
WT = "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd"
EXPORT_DIRS = [WT + "/game/assets/models", WT + "/assets/models"]
SRC = WT + "/assets/models"
for d in EXPORT_DIRS:
    os.makedirs(d, exist_ok=True)

ROOT = "E:/Game Research/Lembah Karsa 3D"
SOURCES = [
    (ROOT + "/kampung_animals.blend",  ['mob_ayam','mob_bebek','mob_kucing','mob_kambing','mob_sapi','mob_kelinci']),
    (ROOT + "/kampung_animals2.blend", ['mob_domba','mob_kuda','mob_rubah','mob_jago']),
]

def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for im in list(bpy.data.images):
        if im.users == 0: bpy.data.images.remove(im)
    for mt in list(bpy.data.materials):
        if mt.users == 0: bpy.data.materials.remove(mt)

def add_fur(mat, scale):
    nt = mat.node_tree
    if not nt: return
    b = nt.nodes.get('Principled BSDF')
    if not b: return
    base = tuple(b.inputs['Base Color'].default_value)[:3]
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale
    nz.inputs['Detail'].default_value = 8.0
    if 'Roughness' in nz.inputs: nz.inputs['Roughness'].default_value = 0.8
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    dark = tuple(min(1, c*0.48) for c in base); brt = tuple(min(1, c*1.38) for c in base)
    cr.elements[0].position = 0.34; cr.elements[0].color = (*dark, 1)
    cr.elements[1].position = 0.66; cr.elements[1].color = (*brt, 1)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])

def process(name, src_blend):
    clear()
    # append ORIGINAL multi-material object (real per-part colors)
    with bpy.data.libraries.load(src_blend) as (s, d):
        d.objects = [n for n in s.objects if n == name]
    for o in d.objects:
        if o is not None:
            bpy.context.collection.objects.link(o)
    obj = bpy.data.objects.get(name)
    if not obj:
        print("MISSING in", src_blend, ":", name); return False
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    print(name, "->", len(obj.data.materials), "mats (source)")
    # UV unwrap
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    # fur/skin pattern on every material except eyes
    for mat in obj.data.materials:
        if mat and 'eye' not in mat.name.lower():
            add_fur(mat, 16.0)
    # bake target image on every material
    img = bpy.data.images.new(name + '_baked', 1024, 1024)
    for mat in obj.data.materials:
        if not mat or not mat.node_tree: continue
        node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img
        for nd in mat.node_tree.nodes: nd.select = False
        node.select = True; mat.node_tree.nodes.active = node
    # bake
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 1
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=4, use_clear=True)
    # save PNG
    for dd in EXPORT_DIRS:
        img.filepath_raw = dd + "/" + name + "_baked.png"; img.file_format = 'PNG'; img.save()
    # single textured material
    m = bpy.data.materials.new(name + '_mat'); m.use_nodes = True
    bn = m.node_tree.nodes['Principled BSDF']; bn.inputs['Roughness'].default_value = 0.7
    tn = m.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = img
    m.node_tree.links.new(tn.outputs['Color'], bn.inputs['Base Color'])
    obj.data.materials.clear(); obj.data.materials.append(m)
    for p in obj.data.polygons: p.material_index = 0
    # export (resilient)
    for dd in EXPORT_DIRS:
        img.filepath_raw = dd + "/" + name + "_baked.png"
        for attempt in range(3):
            try:
                bpy.ops.wm.obj_export(filepath=dd + "/" + name + ".obj", export_selected_objects=True,
                    export_materials=True, apply_modifiers=True, forward_axis='NEGATIVE_Y',
                    up_axis='Z', path_mode='STRIP')
                break
            except Exception as e:
                print("  export retry", attempt, dd, name, ":", e)
    print("BAKED:", name)
    return True

ok = []
for src_blend, names in SOURCES:
    for n in names:
        try:
            if process(n, src_blend): ok.append(n)
        except Exception as e:
            print("FAIL", n, ":", e)
print("DONE BAKING:", ", ".join(ok))

# ============================================================
# GROUP RENDER (reimport baked OBJs) — toned-down lighting
# ============================================================
clear()
for i, n in enumerate(ok):
    bpy.ops.wm.obj_import(filepath=SRC + "/" + n + ".obj")
    o = [m for m in bpy.context.selected_objects if m.type == 'MESH'][0]
    col = i % 5; row = i // 5
    o.location = ((col - 2) * 2.7, -row * 3.0, 0)
    o.rotation_euler = (0, 0, math.pi)

bpy.ops.mesh.primitive_plane_add(size=60, location=(0, -1.5, 0))
gp = bpy.context.active_object
gm = bpy.data.materials.new('BA_Gnd'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.12,0.13,0.12,1)
gp.data.materials.append(gm)
for loc, e, c in [((8,-11,12),520,(1,0.95,0.85)),((-10,-8,9),320,(0.55,0.65,1.0)),((0,7,9),240,(1,0.72,0.5))]:
    bpy.ops.object.light_add(type='POINT', location=loc); l=bpy.context.active_object; l.data.energy=e; l.data.color=c
bpy.ops.object.light_add(type='SUN'); s=bpy.context.active_object; s.data.energy=0.8; s.rotation_euler=(0.6,0.1,-0.2)
def look_at(cam,t):
    d=mathutils.Vector(t)-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sc = bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=64; sc.cycles.use_denoising=True
sc.view_settings.view_transform='Filmic' if 'Filmic' in [v.name for v in bpy.data.scenes[0].view_settings.bl_rna.properties['view_transform'].enum_items] else sc.view_settings.view_transform
sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.08,0.085,0.10,1)
sc.render.resolution_x=1600; sc.render.resolution_y=820
bpy.ops.object.camera_add(location=(0,-14,6.0)); cam=bpy.context.active_object
look_at(cam,(0,-1.5,0.5)); cam.data.lens=44; sc.camera=cam
sc.render.filepath="E:/Game Research/Lembah Karsa 3D/animals_baked.png"
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath="E:/Game Research/Lembah Karsa 3D/animals_baked.blend")
print("GROUP render + blend saved.")
