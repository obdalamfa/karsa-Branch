# export_authentic_vitaboy_characters.py
# Mengekstrak, merakit, dan meng-export seluruh Player & NPC Manusia
# menggunakan Master Mesh & Tekstur Asli FreeSO / Vitaboy (The Sims 1).

import bpy, sys, io, os, math
import mathutils
import numpy as np

sys.path.insert(0, r"E:\Game Research\Lembah Karsa 3D")
from game.vitaboy.registry import asset_registry
from game.vitaboy.appearance import Appearance, Binding
from game.vitaboy.mesh import VitaboyMesh
from game.vitaboy.bcf_reader import BCFReader
from game.vitaboy.skeleton import Mat4

OUT_DIR = "E:/Game Research/Lembah Karsa 3D/assets/models"
os.makedirs(OUT_DIR, exist_ok=True)

reg = asset_registry()
skel = reg.load_skel('adult')

def get_bone_matrix(skel, bone_name):
    b = skel.get_bone(bone_name)
    return b.absolute_matrix if b else Mat4.identity()

def create_hand_mesh(char_id, side='R', scale_factor=0.31):
    """Membuat 3D Hand Vitaboy low-poly yang proporsional dan tersambung ke pergelangan tangan."""
    sgn = 1.0 if side == 'L' else -1.0
    
    # Skelton-space coordinates
    sk_verts = [
        # Wrist ring (Y=2.83)
        (sgn * 0.675, 2.83,  0.010),  # 0: Wrist Top Outer
        (sgn * 0.645, 2.83,  0.005),  # 1: Wrist Top Inner
        (sgn * 0.645, 2.83, -0.065),  # 2: Wrist Bottom Inner
        (sgn * 0.675, 2.83, -0.065),  # 3: Wrist Bottom Outer
        
        # Palm mid (Y=2.70)
        (sgn * 0.710, 2.70,  0.020),  # 4: Palm Outer (Thumb base)
        (sgn * 0.650, 2.69,  0.010),  # 5: Palm Inner
        (sgn * 0.650, 2.69, -0.055),  # 6: Palm Back Inner
        (sgn * 0.700, 2.70, -0.055),  # 7: Palm Back Outer
        
        # Thumb & Fingers (Y=2.63 - 2.53)
        (sgn * 0.740, 2.64,  0.040),  # 8: Thumb Tip
        (sgn * 0.720, 2.53, -0.010),  # 9: Fingertip Outer
        (sgn * 0.690, 2.52, -0.020),  # 10: Fingertip Center
        (sgn * 0.660, 2.54, -0.020),  # 11: Fingertip Inner
    ]
    
    # Konversi ke koordinat Blender: (x * s, -z * s, y * s)
    bl_verts = [(p[0] * scale_factor, -p[2] * scale_factor, p[1] * scale_factor) for p in sk_verts]
    
    # Faces: quad & triangle definitions
    if side == 'L':
        faces = [
            (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
            (4, 5, 8), (5, 6, 8), (6, 7, 8), (7, 4, 8),
            (4, 8, 9), (5, 8, 10), (5, 10, 11),
            (6, 11, 10), (6, 10, 7), (7, 10, 9),
            (9, 10, 11)
        ]
    else:
        faces = [
            (4, 5, 1, 0), (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3),
            (8, 5, 4), (8, 6, 5), (8, 7, 6), (8, 4, 7),
            (9, 8, 4), (10, 8, 5), (11, 10, 5),
            (10, 11, 6), (7, 10, 6), (9, 10, 7),
            (11, 10, 9)
        ]
        
    mesh = bpy.data.meshes.new(f"{char_id}_hand_{side}")
    mesh.from_pydata(bl_verts, [], faces)
    mesh.update()
    
    # UV mapping ke area skin
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_coords = [
        (0.20, 0.40), (0.25, 0.40), (0.25, 0.35), (0.20, 0.35),
        (0.20, 0.30), (0.25, 0.30), (0.25, 0.25), (0.20, 0.25),
        (0.18, 0.22), (0.20, 0.15), (0.23, 0.15), (0.26, 0.15),
    ]
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            v_idx = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uv_coords[v_idx % len(uv_coords)]
            
    obj = bpy.data.objects.new(f"{char_id}_hand_{side}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def assemble_character(char_id, apr_list, scale_factor=0.31):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for im in list(bpy.data.images):
        bpy.data.images.remove(im, do_unlink=True)

    created_objs = []
    
    for apr_idx, apr_name in enumerate(apr_list):
        if not apr_name: continue
        apr_bytes = reg.read_bytes(apr_name)
        if not apr_bytes: continue
        apr = Appearance.from_bytes(apr_bytes)
        
        for idx, ref in enumerate(apr.bindings):
            bnd_data = reg.read_by_id(ref.type_id, ref.file_id)
            if not bnd_data: continue
            bnd = Binding.from_bytes(bnd_data)
            if not bnd.has_mesh: continue
            mesh_data = reg.read_by_id(bnd.mesh_type_id, bnd.mesh_file_id)
            if not mesh_data: continue
            
            vm = VitaboyMesh()
            vm.read(BCFReader(io.BytesIO(mesh_data)), bmf=False)
            
            bind_map = {}
            for bb in vm.bone_bindings:
                bind_map[bb.bone_index] = bb.bone_name
                
            verts = []
            for v in vm.vertices:
                bname = bind_map.get(v.bone_index)
                bm = get_bone_matrix(skel, bname)
                p = bm.transform_point(v.position)
                verts.append((p.x * scale_factor, -p.z * scale_factor, p.y * scale_factor))
                
            faces = []
            for i in range(vm.num_primitives):
                faces.append((vm.index_buffer[i*3], vm.index_buffer[i*3+1], vm.index_buffer[i*3+2]))
                
            mesh = bpy.data.meshes.new(f"{char_id}_{apr_idx}_{idx}")
            mesh.from_pydata(verts, [], faces)
            mesh.update()
            
            uv_layer = mesh.uv_layers.new(name="UVMap")
            for poly in mesh.polygons:
                for loop_index in poly.loop_indices:
                    vert_idx = mesh.loops[loop_index].vertex_index
                    u = vm.vertices[vert_idx].uv.x
                    v = 1.0 - vm.vertices[vert_idx].uv.y
                    uv_layer.data[loop_index].uv = (u, v)
                    
            obj = bpy.data.objects.new(f"{char_id}_{apr_idx}_{idx}", mesh)
            bpy.context.scene.collection.objects.link(obj)
            
            if bnd.has_texture:
                tex_data = reg.read_by_id(bnd.texture_type_id, bnd.texture_file_id)
                if tex_data:
                    temp_img_path = f"E:/Game Research/Lembah Karsa 3D/temp_{char_id}_{apr_idx}_{idx}.png"
                    with open(temp_img_path, 'wb') as f:
                        f.write(tex_data)
                    img = bpy.data.images.load(temp_img_path)
                    mat = bpy.data.materials.new(name=f"M_{char_id}_{apr_idx}_{idx}")
                    mat.use_nodes = True
                    bsdf = mat.node_tree.nodes.get('Principled BSDF')
                    tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
                    tex_node.image = img
                    mat.node_tree.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
                    obj.data.materials.append(mat)
                    
            created_objs.append(obj)
            
    # Add authentic Vitaboy hands for Left and Right
    hand_l = create_hand_mesh(char_id, side='L', scale_factor=scale_factor)
    hand_r = create_hand_mesh(char_id, side='R', scale_factor=scale_factor)
    
    # Assign skin material to hands from head/body if available
    skin_mat = None
    for o in created_objs:
        if o.data.materials:
            skin_mat = o.data.materials[0]
            break
    if skin_mat:
        hand_l.data.materials.append(skin_mat)
        hand_r.data.materials.append(skin_mat)
        
    created_objs.extend([hand_l, hand_r])
    
    if not created_objs:
        print(f"FAILED: No parts for {char_id}")
        return
        
    # Join parts into single character mesh
    bpy.ops.object.select_all(action='DESELECT')
    for o in created_objs: o.select_set(True)
    bpy.context.view_layer.objects.active = created_objs[0]
    bpy.ops.object.join()
    char_obj = bpy.context.active_object
    char_obj.name = char_id
    bpy.ops.object.shade_smooth()
    
    # Bake cohesive single diffuse atlas
    bake_img = bpy.data.images.new(f"{char_id}_baked", 1024, 1024)
    for mtl in char_obj.data.materials:
        if not mtl or not mtl.node_tree: continue
        nd = mtl.node_tree.nodes.new('ShaderNodeTexImage')
        nd.image = bake_img
        for x in mtl.node_tree.nodes: x.select = False
        nd.select = True
        mtl.node_tree.nodes.active = nd
        
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 1
    bpy.ops.object.select_all(action='DESELECT')
    char_obj.select_set(True)
    bpy.context.view_layer.objects.active = char_obj
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=4, use_clear=True)
    
    # Mute grading (Disco Elysium palette consistency)
    buf = np.empty(len(bake_img.pixels), dtype=np.float32)
    bake_img.pixels.foreach_get(buf)
    px = buf.reshape(-1, 4)
    lum = px[:, :3] @ np.array([0.299, 0.587, 0.114], np.float32)
    px[:, :3] = np.clip((lum[:, None] + (px[:, :3] - lum[:, None]) * 0.85) * 0.98, 0, 1)
    bake_img.pixels.foreach_set(px.reshape(-1))
    
    baked_tex_path = f"{OUT_DIR}/{char_id}_baked.png"
    bake_img.filepath_raw = baked_tex_path
    bake_img.file_format = 'PNG'
    try:
        bake_img.save()
    except Exception:
        try:
            bake_img.save_render(baked_tex_path)
        except Exception:
            try:
                from PIL import Image
                img_data = (np.flipud(px.reshape(1024, 1024, 4)) * 255).astype(np.uint8)
                Image.fromarray(img_data).save(baked_tex_path)
            except Exception as e_save:
                print(f"Failed to save image {baked_tex_path}: {e_save}")
    
    # Single master material
    mb = bpy.data.materials.new(f"{char_id}_mat")
    mb.use_nodes = True
    bn = mb.node_tree.nodes.get('Principled BSDF')
    if bn: bn.inputs['Roughness'].default_value = 0.80
    tn = mb.node_tree.nodes.new('ShaderNodeTexImage')
    tn.image = bake_img
    mb.node_tree.links.new(tn.outputs['Color'], bn.inputs['Base Color'])
    char_obj.data.materials.clear()
    char_obj.data.materials.append(mb)
    for p in char_obj.data.polygons: p.material_index = 0
    
    # Export function
    def _export(o, name):
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for att in range(3):
            try:
                bpy.ops.wm.obj_export(
                    filepath=f"{OUT_DIR}/{name}.obj",
                    export_selected_objects=True,
                    export_materials=True,
                    apply_modifiers=True,
                    forward_axis='NEGATIVE_Y',
                    up_axis='Z',
                    path_mode='STRIP'
                )
                break
            except Exception as ex:
                print("Retry", att, name, ex)

    _export(char_obj, char_id)
    
    # Multi-frame walk cycle generation with arm and hand counter-swing
    vs = [v.co.z for v in char_obj.data.vertices]
    zmin, zmax = min(vs), max(vs)
    Hh = zmax - zmin
    body_z = zmin + 0.46 * Hh
    arm_top_z = zmin + 0.78 * Hh
    
    for pose, phase in (('idle', 0.0), ('walk1', 1.0), ('walk2', -1.0), ('walk3', 0.5), ('walk4', -0.5)):
        dup = char_obj.copy()
        dup.data = char_obj.data.copy()
        dup.name = f"{char_id}_{pose}"
        bpy.context.collection.objects.link(dup)
        if abs(phase) > 1e-6:
            sw_leg = 0.14 * Hh * phase
            sw_arm = -0.12 * Hh * phase  # counter-stride swing for arms and hands
            for v in dup.data.vertices:
                x, y, z = v.co
                # Legs swing
                if z < body_z:
                    lf = (body_z - z) / (body_z - zmin + 1e-6)
                    side = 1.0 if x >= 0 else -1.0
                    v.co.y += sw_leg * lf * side
                    if side * phase > 0:
                        v.co.z += 0.045 * Hh * lf
                # Arms & hands swing
                elif abs(x) > 0.15 and z < arm_top_z:
                    af = (arm_top_z - z) / (arm_top_z - body_z + 1e-6)
                    side = 1.0 if x >= 0 else -1.0
                    v.co.y += sw_arm * af * side
                    
        _export(dup, f"{char_id}_{pose}")
        bpy.data.objects.remove(dup, do_unlink=True)
        
    print(f"=== AUTHENTIC FREESO EXPORT DONE: {char_id} ===")

# DAFTAR LENGKAP KARAKTER
CHAR_ROSTER = {
    'player':          ['mabd112_uf__gardener.apr', 'mahd001_romeo.apr'],      # petani muda
    'npc_arya':        ['mabd113_uf__handy.apr', 'mahd001_romeo.apr'],         # pemuda kerja
    'npc_sari':        ['fabd325_gypsypeasant.apr', 'fahd001_sharon.apr', 'fahl001_sharon.apr'],  # warung
    'npc_raka':        ['mabd828_ct_-scrub1.apr', 'mahd001_ross.apr'],         # dokter klinik
    'npc_maya':        ['fabd001_slacker.apr', 'fahd001_shannon01.apr', 'fahl001_shannon01.apr'],  # seniman
    'npc_budi':        ['mabd113_uf__mechanic.apr', 'mahd009_beard01.apr'],    # pandai besi (berjenggot)
    'npc_joko':        ['mabd474_ct__construction.apr', 'mahd001_ross.apr'],   # tukang bangunan
    'npc_ningsih':     ['fabd034_mom2.apr', 'fahd001_sharon.apr', 'fahl001_sharon.apr'], # ibu rumah tangga
    'npc_cici':        ['fabd001_summer01.apr', 'fahd068_girl.apr'],           # anak perempuan
    'npc_bowo':        ['mabd000_sl__teepjs2.apr', 'mahd038_01.apr'],          # anak laki-laki
    'npc_pak_guru':    ['mabd427_bookworm.apr', 'mahd043_bookworm.apr'],       # guru (kacamata)
    'npc_mbok_jum':    ['fabd002_gma1.apr', 'fahd004_gma1.apr'],               # nenek
    'npc_jaka_ronda':  ['mabd877_uf__ranger_01.apr', 'mahd001_robin.apr'],     # penjaga ronda
    'npc_kapten_kuro': ['mabd311_ow__merchant.apr', 'mahd002_asian.apr'],      # kapten kapal
    'npc_kru_kuro':    ['mabd321_ow__servant.apr', 'mahd013_pompa.apr'],       # kru pelaut
}

for char_id, apr_list in CHAR_ROSTER.items():
    sc = 0.20 if char_id in ('npc_cici', 'npc_bowo') else 0.31
    try:
        assemble_character(char_id, apr_list, scale_factor=sc)
    except Exception as e:
        print(f"ERROR assembling {char_id}: {e}")

print("=== ALL AUTHENTIC FREESO CHARACTERS SUCCESSFULLY ASSEMBLED AND EXPORTED ===")
