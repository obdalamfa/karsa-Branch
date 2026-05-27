import os
import subprocess
import tempfile

BLENDER_PATH = r"E:\blender\blender.exe"
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "models")

def ensure_dir():
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)

def generate_cow_model():
    """Generates an organic realistic cow using Blender Metaballs."""
    ensure_dir()
    out_obj = os.path.join(ASSETS_DIR, "cow.obj")
    if os.path.exists(out_obj):
        return out_obj  # Already generated
        
    script = f"""
import bpy

# Clear existing
bpy.ops.wm.read_factory_settings(use_empty=True)

# Create Metaball base
mball = bpy.data.metaballs.new('CowMeta')
obj = bpy.data.objects.new('Cow', mball)
bpy.context.collection.objects.link(obj)

# Body
ele = mball.elements.new()
ele.co = (0, 0, 0)
ele.radius = 1.2
ele.type = 'ELLIPSOID'
ele.size_x = 1.0
ele.size_y = 1.8
ele.size_z = 0.9

# Head
ele2 = mball.elements.new()
ele2.co = (0, 2.0, 0.5)
ele2.radius = 0.7

# Legs
for lx, ly in [(-0.5, 1.0), (0.5, 1.0), (-0.5, -1.0), (0.5, -1.0)]:
    ele_leg = mball.elements.new()
    ele_leg.co = (lx, ly, -1.0)
    ele_leg.radius = 0.4
    ele_leg.type = 'CAPSULE'
    ele_leg.size_x = 0.2
    ele_leg.size_y = 0.2
    ele_leg.size_z = 1.0

# Convert Metaball to Mesh
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.convert(target='MESH')

# Add Displacement for realistic texture bumps
bpy.ops.object.modifier_add(type='DISPLACE')
tex = bpy.data.textures.new('CowNoise', type='CLOUDS')
tex.noise_scale = 0.2
obj.modifiers['Displace'].texture = tex
obj.modifiers['Displace'].strength = 0.1

# Apply Modifiers
bpy.ops.object.modifier_apply(modifier="Displace")

# Export to OBJ
bpy.ops.wm.obj_export(filepath=r"{out_obj}")
"""
    # Write script to temp
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.py') as f:
        f.write(script)
        script_path = f.name
        
    print(f"Generating Cow via Blender at {out_obj}...")
    subprocess.run([BLENDER_PATH, "-b", "-P", script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(script_path)
    return out_obj

def generate_ghost_model():
    """Generates an organic realistic ghost using Blender Cloth/Metaball."""
    ensure_dir()
    out_obj = os.path.join(ASSETS_DIR, "ghost.obj")
    if os.path.exists(out_obj):
        return out_obj
        
    script = f"""
import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

# Create capsule shape
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.6, depth=2.5, location=(0,0,1.25))
obj = bpy.context.active_object

# Smooth it
bpy.ops.object.shade_smooth()

# Subdivide
bpy.ops.object.modifier_add(type='SUBSURF')
obj.modifiers["Subdivision"].levels = 2
bpy.ops.object.modifier_apply(modifier="Subdivision")

# Displace for eerie flowing cloth shape
bpy.ops.object.modifier_add(type='DISPLACE')
tex = bpy.data.textures.new('GhostNoise', type='MARBLE')
tex.noise_scale = 0.5
obj.modifiers['Displace'].texture = tex
obj.modifiers['Displace'].strength = 0.3

# Apply
bpy.ops.object.modifier_apply(modifier="Displace")

bpy.ops.wm.obj_export(filepath=r"{out_obj}")
"""
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.py') as f:
        f.write(script)
        script_path = f.name
        
    print(f"Generating Ghost via Blender at {out_obj}...")
    subprocess.run([BLENDER_PATH, "-b", "-P", script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(script_path)
    return out_obj
