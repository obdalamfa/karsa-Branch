import bpy, os

# ============================================================
# TEXTURE BAKE — Naga: scales (Voronoi) on gold, fur (Noise) on mane,
# flame variation on fins -> bake DIFFUSE COLOR to one PNG, re-apply.
# ============================================================
WT = "E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd"
EXPORT_DIRS = [WT + "/game/assets/models", WT + "/assets/models"]
for d in EXPORT_DIRS:
    os.makedirs(d, exist_ok=True)

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
# append the ORIGINAL multi-material Naga from naga_dragon.blend (NOT the
# already-baked single-material OBJ). libraries.load keeps context intact.
BLEND = "E:/Game Research/Lembah Karsa 3D/naga_dragon.blend"
with bpy.data.libraries.load(BLEND) as (src, dst):
    dst.objects = [n for n in src.objects if n == 'Naga']
for o in dst.objects:
    if o is not None:
        bpy.context.collection.objects.link(o)
naga = bpy.data.objects['Naga']
bpy.ops.object.select_all(action='DESELECT')
naga.select_set(True)
bpy.context.view_layer.objects.active = naga
print("Naga appended:", len(naga.data.vertices), "v;", len(naga.data.materials), "mats")

# ---- UV unwrap (non-overlapping islands required for baking) ----
bpy.ops.object.select_all(action='DESELECT')
naga.select_set(True); bpy.context.view_layer.objects.active = naga
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.015)
bpy.ops.object.mode_set(mode='OBJECT')
print("UV unwrap done")

def bsdf_of(mat):
    return mat.node_tree.nodes.get('Principled BSDF')

def base_of(mat):
    b = bsdf_of(mat)
    return tuple(b.inputs['Base Color'].default_value)[:3] if b else (0.5,0.5,0.5)

def add_pattern(mat, kind, scale):
    """Inject procedural color variation into Base Color before baking."""
    nt = mat.node_tree; nodes = nt.nodes; links = nt.links
    b = bsdf_of(mat)
    if not b: return
    base = base_of(mat)
    tc = nodes.new('ShaderNodeTexCoord')
    ramp = nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    if kind == 'scale':
        tex = nodes.new('ShaderNodeTexVoronoi')
        tex.feature = 'DISTANCE_TO_EDGE'; tex.inputs['Scale'].default_value = scale
        links.new(tc.outputs['Generated'], tex.inputs['Vector'])
        dark = tuple(min(1,c*0.12) for c in base); brt = tuple(min(1,c*1.32) for c in base)
        cr.elements[0].position = 0.0;  cr.elements[0].color = (*dark,1)
        cr.elements[1].position = 0.05; cr.elements[1].color = (*base,1)
        e2 = cr.elements.new(0.42); e2.color = (*brt,1)
        links.new(tex.outputs['Distance'], ramp.inputs['Fac'])
    else:  # fur / flame : noise
        tex = nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = scale
        tex.inputs['Detail'].default_value = 8.0
        if 'Roughness' in tex.inputs: tex.inputs['Roughness'].default_value = 0.75
        links.new(tc.outputs['Object'], tex.inputs['Vector'])
        dark = tuple(min(1,c*0.45) for c in base); brt = tuple(min(1,c*1.40) for c in base)
        cr.elements[0].position = 0.34; cr.elements[0].color = (*dark,1)
        cr.elements[1].position = 0.66; cr.elements[1].color = (*brt,1)
        links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], b.inputs['Base Color'])

# ---- enhance materials by role ----
for mat in naga.data.materials:
    n = mat.name.lower()
    if 'gold' in n or 'horn' in n:
        add_pattern(mat, 'scale', 22.0)
    elif 'green' in n:
        add_pattern(mat, 'fur', 12.0)
    elif 'red' in n or 'orange' in n:
        add_pattern(mat, 'fur', 16.0)
print("Patterns injected")

# ---- bake target image + add image node (active) to EVERY material ----
img = bpy.data.images.new('naga_baked', 2048, 2048)
for mat in naga.data.materials:
    nt = mat.node_tree
    node = nt.nodes.new('ShaderNodeTexImage'); node.image = img
    for nd in nt.nodes: nd.select = False
    node.select = True; nt.nodes.active = node

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
try: sc.cycles.device = 'GPU'
except Exception: pass
sc.cycles.samples = 1
bpy.ops.object.select_all(action='DESELECT'); naga.select_set(True)
bpy.context.view_layer.objects.active = naga
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=6, use_clear=True)
print("BAKE done")

# ---- save PNG into export dirs ----
for d in EXPORT_DIRS:
    img.filepath_raw = d + "/naga_baked.png"; img.file_format = 'PNG'; img.save()
print("PNG saved")

# ---- rebuild single textured material, assign all faces ----
m = bpy.data.materials.new('Naga_Baked'); m.use_nodes = True
bn = m.node_tree.nodes['Principled BSDF']
bn.inputs['Roughness'].default_value = 0.42
bn.inputs['Metallic'].default_value = 0.25
tnode = m.node_tree.nodes.new('ShaderNodeTexImage'); tnode.image = img
m.node_tree.links.new(tnode.outputs['Color'], bn.inputs['Base Color'])
naga.data.materials.clear()
naga.data.materials.append(m)
for p in naga.data.polygons: p.material_index = 0
# point image to relative filename for MTL
img.filepath_raw = "//naga_baked.png"

# ---- export OBJ (+MTL referencing naga_baked.png) ----
for d in EXPORT_DIRS:
    img.filepath_raw = d + "/naga_baked.png"
    bpy.ops.wm.obj_export(filepath=d + "/naga.obj", export_selected_objects=True,
        export_materials=True, apply_modifiers=True, forward_axis='NEGATIVE_Y',
        up_axis='Z', path_mode='STRIP')
print("OBJ exported with baked texture")

# ---- save bake blend + render preview ----
bpy.ops.wm.save_as_mainfile(filepath="E:/Game Research/Lembah Karsa 3D/naga_baked.blend")

import math, mathutils
for o in list(bpy.data.objects):
    if o.type in ('LIGHT','CAMERA'): bpy.data.objects.remove(o, do_unlink=True)
g = bpy.data.objects.get('Gnd')
if not g:
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,-3.1)); g=bpy.context.active_object; g.name='Gnd'
def look_at(cam,t):
    d=mathutils.Vector(t)-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
vs=[naga.matrix_world@v.co for v in naga.data.vertices]
xs=[v.x for v in vs]; ys=[v.y for v in vs]; zs=[v.z for v in vs]
cen=mathutils.Vector(((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,(min(zs)+max(zs))/2))
diag=math.sqrt((max(xs)-min(xs))**2+(max(ys)-min(ys))**2+(max(zs)-min(zs))**2)
for loc,e,c in [((diag*0.8,-diag,diag*0.8),80,(1,0.93,0.78)),((-diag,diag*0.4,diag*0.7),48,(0.5,0.62,1))]:
    bpy.ops.object.light_add(type='POINT',location=(cen.x+loc[0],cen.y+loc[1],cen.z+loc[2]))
    l=bpy.context.active_object; l.data.energy=e*diag; l.data.color=c
bpy.ops.object.light_add(type='SUN'); s=bpy.context.active_object; s.data.energy=1.3; s.rotation_euler=(0.4,0.1,0.5)
sc.cycles.samples=64
sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.12,0.13,0.15,1)
sc.render.resolution_x=820; sc.render.resolution_y=1040
camloc=mathutils.Vector((cen.x+diag*0.72,cen.y-diag*1.0,cen.z+diag*0.18))
bpy.ops.object.camera_add(location=camloc); cam=bpy.context.active_object
look_at(cam,cen); cam.data.lens=48; sc.camera=cam
sc.render.filepath="E:/Game Research/Lembah Karsa 3D/naga_baked_preview.png"
bpy.ops.render.render(write_still=True)
print("PREVIEW render done. diag=%.1f"%diag)
