# tools/export_tool_props.py
# Membuat dan meng-export model 3D prop alat pertanian & perlengkapan Vitaboy
import bpy, os, math
import numpy as np

OUT_DIR = "E:/Game Research/Lembah Karsa 3D/assets/models"
os.makedirs(OUT_DIR, exist_ok=True)

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m, do_unlink=True)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img, do_unlink=True)

def export_obj(obj, name):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.obj_export(
        filepath=f"{OUT_DIR}/{name}.obj",
        export_selected_objects=True,
        export_materials=True,
        apply_modifiers=True,
        forward_axis='NEGATIVE_Y',
        up_axis='Z',
        path_mode='STRIP'
    )
    print(f"Exported: {name}.obj")

# 1. Cangkul (Hoe)
def make_cangkul():
    clear_scene()
    # Handle (kayu silinder panjang ~0.9m)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.90, location=(0, 0, 0.45))
    handle = bpy.context.active_object
    handle.name = "handle"
    
    # Blade (lempeng besi miring tajam)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.10, 0.85), scale=(0.18, 0.22, 0.018))
    blade = bpy.context.active_object
    blade.rotation_euler = (math.radians(65), 0, 0)
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = handle
    bpy.ops.object.join()
    c = bpy.context.active_object
    c.name = "prop_cangkul"
    
    # Material
    mat = bpy.data.materials.new("mat_cangkul")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.42, 0.30, 0.18, 1.0) # warm wood/steel
        bsdf.inputs['Roughness'].default_value = 0.65
    c.data.materials.append(mat)
    
    export_obj(c, "prop_cangkul")

# 2. Gembor (Watering Can)
def make_gembor():
    clear_scene()
    # Body
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.26, location=(0, 0, 0.13))
    body = bpy.context.active_object
    
    # Spout (corong menyembur miring ke depan)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.38, location=(0, 0.18, 0.24))
    spout = bpy.context.active_object
    spout.rotation_euler = (math.radians(-42), 0, 0)
    
    # Rose tip (kepala penyiram berlubang)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.03, location=(0, 0.30, 0.36))
    rose = bpy.context.active_object
    rose.rotation_euler = (math.radians(-42), 0, 0)
    
    # Handle (pegangan lengkung atas)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.018, location=(0, -0.04, 0.24))
    handle = bpy.context.active_object
    handle.rotation_euler = (0, math.radians(90), 0)
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    g = bpy.context.active_object
    g.name = "prop_gembor"
    
    mat = bpy.data.materials.new("mat_gembor")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.28, 0.44, 0.38, 1.0) # vintage tin sage green
        bsdf.inputs['Metallic'].default_value = 0.30
        bsdf.inputs['Roughness'].default_value = 0.50
    g.data.materials.append(mat)
    
    export_obj(g, "prop_gembor")

# 3. Pedang / Golok (Sword)
def make_pedang():
    clear_scene()
    # Handle
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.20, location=(0, 0, 0.10))
    handle = bpy.context.active_object
    
    # Crossguard
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.21), scale=(0.12, 0.04, 0.025))
    guard = bpy.context.active_object
    
    # Blade (bilah baja tajam)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.65), scale=(0.045, 0.012, 0.85))
    blade = bpy.context.active_object
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = handle
    bpy.ops.object.join()
    s = bpy.context.active_object
    s.name = "prop_pedang"
    
    mat = bpy.data.materials.new("mat_pedang")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.75, 0.78, 0.82, 1.0) # steel
        bsdf.inputs['Metallic'].default_value = 0.85
        bsdf.inputs['Roughness'].default_value = 0.30
    s.data.materials.append(mat)
    
    export_obj(s, "prop_pedang")

# 4. Kapak (Axe)
def make_kapak():
    clear_scene()
    # Shaft
    bpy.ops.mesh.primitive_cylinder_add(radius=0.024, depth=0.75, location=(0, 0, 0.375))
    shaft = bpy.context.active_object
    
    # Axe Head (kepala kapak baja)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.08, 0.70), scale=(0.035, 0.22, 0.16))
    head = bpy.context.active_object
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = shaft
    bpy.ops.object.join()
    a = bpy.context.active_object
    a.name = "prop_kapak"
    
    mat = bpy.data.materials.new("mat_kapak")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.50, 0.40, 0.30, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.60
    a.data.materials.append(mat)
    
    export_obj(a, "prop_kapak")

# 5. Pickaxe (Beliung Tambang)
def make_pickaxe():
    clear_scene()
    # Shaft
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.80, location=(0, 0, 0.40))
    shaft = bpy.context.active_object
    
    # Curved pick head
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.76), scale=(0.04, 0.46, 0.05))
    pick = bpy.context.active_object
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = shaft
    bpy.ops.object.join()
    p = bpy.context.active_object
    p.name = "prop_pickaxe"
    
    mat = bpy.data.materials.new("mat_pickaxe")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.45, 0.48, 0.52, 1.0)
        bsdf.inputs['Metallic'].default_value = 0.60
        bsdf.inputs['Roughness'].default_value = 0.45
    p.data.materials.append(mat)
    
    export_obj(p, "prop_pickaxe")

# 6. Pancing (Fishing Rod)
def make_pancing():
    clear_scene()
    # Tapered bamboo rod
    bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=1.60, location=(0, 0, 0.80))
    rod = bpy.context.active_object
    rod.rotation_euler = (math.radians(-15), 0, 0)
    
    # Reel
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.06, location=(0, 0.05, 0.25))
    reel = bpy.context.active_object
    reel.rotation_euler = (0, math.radians(90), 0)
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = rod
    bpy.ops.object.join()
    f = bpy.context.active_object
    f.name = "prop_pancing"
    
    mat = bpy.data.materials.new("mat_pancing")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.68, 0.58, 0.32, 1.0) # bamboo
        bsdf.inputs['Roughness'].default_value = 0.70
    f.data.materials.append(mat)
    
    export_obj(f, "prop_pancing")

make_cangkul()
make_gembor()
make_pedang()
make_kapak()
make_pickaxe()
make_pancing()

print("=== ALL 3D PROPS EXPORTED SUCCESSFULLY ===")
