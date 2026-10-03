# tools/blender_build_rigged_characters.py
# Membangun file kerja Blender karakter manusia Vitaboy yang TER-RIG:
#   - Armature dari skeleton 'adult' asli (29 tulang)
#   - Mesh body/head/hair dengan vertex group per tulang (skinning nyata)
#   - Tangan prosedural (telapak + 4 jari + jempol) ber-weight ke *_HAND/*_FINGER0
#   - Aksi animasi berbasis tulang: idle, walk, hoe, water, swing
# Jalankan di Blender:  exec(open(path).read())   (set ONLY = ['player'] untuk iterasi)
import bpy, bmesh, sys, io, os, math
from mathutils import Vector, Matrix

ROOT = r"E:\Game Research\Lembah Karsa 3D"
sys.path.insert(0, ROOT)
from game.vitaboy.registry import asset_registry
from game.vitaboy.appearance import Appearance, Binding
from game.vitaboy.mesh import VitaboyMesh, Vec3
from game.vitaboy.bcf_reader import BCFReader

TEX_DIR = os.path.join(ROOT, "assets", "blend", "tex")
BLEND_OUT = os.path.join(ROOT, "assets", "blend", "characters_vitaboy.blend")
os.makedirs(TEX_DIR, exist_ok=True)

reg = asset_registry()
SKEL = reg.load_skel('adult')

ROSTER = {   # pakaian & kepala dipilih sesuai peran (tanpa proxy mannequin)
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
CHILD = {'npc_cici', 'npc_bowo'}
ONLY = globals().get('ONLY')  # opsional: list id untuk iterasi cepat


def sk2bl(p, s):
    """Skeleton space (Y-up) -> Blender (Z-up), meter."""
    return Vector((p.x * s, -p.z * s, p.y * s))


def bone_world(name, s):
    b = SKEL.get_bone(name)
    return sk2bl(b.absolute_matrix.transform_point(Vec3(0, 0, 0)), s)


# ─── ARMATURE ────────────────────────────────────────────────────────────────
def build_armature(cid, s, coll):
    arm = bpy.data.armatures.new(f"{cid}_rig")
    ob = bpy.data.objects.new(f"{cid}_rig", arm)
    coll.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    heads = {b.name: bone_world(b.name, s) for b in SKEL.bones}
    kids = {}
    for b in SKEL.bones:
        kids.setdefault(b.parent_name, []).append(b.name)
    for b in SKEL.bones:
        eb = arm.edit_bones.new(b.name)
        h = heads[b.name]
        ch = [c for c in kids.get(b.name, []) if (heads[c] - h).length > 1e-3]
        # Tulang tulang belakang/leher: arahkan ke anak tengah, bukan lengan
        pref = {'NECK': 'HEAD', 'PELVIS': 'SPINE', 'ROOT': 'PELVIS'}.get(b.name)
        if pref and pref in heads:
            t = heads[pref]
        elif ch:
            t = heads[ch[0]]
        else:
            par = heads.get(b.parent_name, h - Vector((0, 0, 0.05)))
            d = (h - par).normalized() if (h - par).length > 1e-4 else Vector((0, 0, 1))
            t = h + d * 0.05 * (s / 0.31)
        if (t - h).length < 1e-3:
            t = h + Vector((0, 0, 0.03))
        eb.head, eb.tail = h, t
    for b in SKEL.bones:
        if b.parent_name in arm.edit_bones:
            arm.edit_bones[b.name].parent = arm.edit_bones[b.parent_name]
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.show_in_front = True
    return ob


# ─── MESH PARTS (skinned) ────────────────────────────────────────────────────
def load_parts(cid, apr_list, s, coll, rig):
    parts = []
    for ai, apr_name in enumerate(apr_list):
        data = reg.read_bytes(apr_name)
        if not data:
            continue
        apr = Appearance.from_bytes(data)
        for bi, ref in enumerate(apr.bindings):
            bd = reg.read_by_id(ref.type_id, ref.file_id)
            if not bd:
                continue
            bnd = Binding.from_bytes(bd)
            if not bnd.has_mesh:
                continue
            md = reg.read_by_id(bnd.mesh_type_id, bnd.mesh_file_id)
            if not md:
                continue
            vm = VitaboyMesh()
            vm.read(BCFReader(io.BytesIO(md)), bmf=False)
            bmap = {bb.bone_index: bb.bone_name for bb in vm.bone_bindings}
            verts, vgroup = [], []
            for v in vm.vertices:
                bn = bmap.get(v.bone_index)
                b = SKEL.get_bone(bn) if bn else None
                p = b.absolute_matrix.transform_point(v.position) if b else v.position
                verts.append(sk2bl(p, s))
                vgroup.append(bn or 'PELVIS')
            faces = [tuple(vm.index_buffer[i*3:i*3+3]) for i in range(vm.num_primitives)]
            kind = ['body', 'head', 'hair'][min(ai, 2)]
            me = bpy.data.meshes.new(f"{cid}_{kind}")
            me.from_pydata(verts, [], faces)
            me.update()
            uv = me.uv_layers.new(name="UVMap")
            for poly in me.polygons:
                for li in poly.loop_indices:
                    vi = me.loops[li].vertex_index
                    uv.data[li].uv = (vm.vertices[vi].uv.x, 1.0 - vm.vertices[vi].uv.y)
            ob = bpy.data.objects.new(f"{cid}_{kind}", me)
            coll.objects.link(ob)
            for i, g in enumerate(vgroup):
                vg = ob.vertex_groups.get(g) or ob.vertex_groups.new(name=g)
                vg.add([i], 1.0, 'REPLACE')
            # Material bertekstur asli
            if bnd.has_texture:
                td = reg.read_by_id(bnd.texture_type_id, bnd.texture_file_id)
                if td:
                    tp = os.path.join(TEX_DIR, f"{cid}_{kind}.png")
                    with open(tp, 'wb') as f:
                        f.write(td)
                    img = bpy.data.images.load(tp, check_existing=True)
                    m = bpy.data.materials.new(f"M_{cid}_{kind}")
                    m.use_nodes = True
                    bs = m.node_tree.nodes['Principled BSDF']
                    bs.inputs['Roughness'].default_value = 0.85
                    tn = m.node_tree.nodes.new('ShaderNodeTexImage')
                    tn.image = img
                    tn.interpolation = 'Closest'
                    m.node_tree.links.new(tn.outputs['Color'], bs.inputs['Base Color'])
                    me.materials.append(m)
            mod = ob.modifiers.new("Armature", 'ARMATURE')
            mod.object = rig
            ob.parent = rig
            bpy.ops.object.select_all(action='DESELECT')
            ob.select_set(True)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.shade_smooth()
            parts.append(ob)
    return parts


def skin_tone(parts):
    """Warna kulit = rata-rata tekstur badan pada UV vertex lengan bawah (L/R_ARM2)."""
    for ob in parts:
        if not ob.name.endswith('_body') or not ob.data.materials:
            continue
        img = next((n.image for n in ob.data.materials[0].node_tree.nodes
                    if n.type == 'TEX_IMAGE' and n.image), None)
        if not img:
            continue
        gi = {g.index for g in ob.vertex_groups if g.name in ('L_ARM2', 'R_ARM2', 'L_HAND', 'R_HAND')}
        me = ob.data
        wv = {v.index for v in me.vertices if any(g.group in gi for g in v.groups)}
        W, H = img.size
        px = img.pixels[:]
        acc, cnt = [0.0, 0.0, 0.0], 0
        uvl = me.uv_layers.active.data
        for lp in me.loops:
            if lp.vertex_index not in wv:
                continue
            u, v = uvl[lp.index].uv
            x = min(W - 1, max(0, int(u * W))); y = min(H - 1, max(0, int(v * H)))
            i = (y * W + x) * 4
            acc[0] += px[i]; acc[1] += px[i+1]; acc[2] += px[i+2]; cnt += 1
        if cnt:
            c = [a / cnt for a in acc]
            # tekstur image di Blender sRGB → nilai Base Color linear
            return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
    return (0.40, 0.25, 0.16)


# ─── TANGAN ──────────────────────────────────────────────────────────────────
def _box(bm, center, size, axes):
    """Kotak berorientasi: axes = (ax, ay, az) unit vectors."""
    ax, ay, az = axes
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    vs = []
    for sz in (-1, 1):
        for sy in (-1, 1):
            for sx in (-1, 1):
                vs.append(bm.verts.new(center + ax * sx * hx + ay * sy * hy + az * sz * hz))
    idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for f in idx:
        bm.faces.new([vs[i] for i in f])
    return vs


def build_hand(cid, side, s, coll, rig, skin):
    k = s / 0.31                      # skala relatif (anak lebih kecil)
    wrist = bone_world(f'{side}_HAND', s)
    tip = bone_world(f'{side}_FINGER0', s)
    down = (tip - wrist).normalized()             # arah jari
    out = Vector((1 if side == 'L' else -1, 0, 0))  # sisi luar (punggung tangan menghadap luar)
    out = (out - down * out.dot(down)).normalized()
    fwd = down.cross(out).normalized()
    if fwd.y > 0:                                  # pastikan jempol ke depan (-Y)
        fwd = -fwd
    bm = bmesh.new()
    palm_len, palm_w, palm_t = 0.075 * k, 0.070 * k, 0.026 * k
    pc = wrist + down * (palm_len / 2 + 0.005 * k)
    _box(bm, pc, (palm_t, palm_w, palm_len), (out, fwd, down))
    fingers = []
    # 4 jari: 2 ruas, sedikit menekuk ke dalam (rileks)
    for i in range(4):
        off = (i - 1.5) * (palm_w / 4.0)
        ln = [0.030, 0.034, 0.032, 0.026][i] * k
        base = wrist + down * (palm_len + 0.005 * k) + fwd * off
        curl = -out * 0.006 * k
        c1 = base + down * (ln / 2)
        _box(bm, c1, (palm_t * 0.75, palm_w / 4.6, ln), (out, fwd, down))
        d2 = (down + (-out) * 0.45).normalized()
        c2 = base + down * ln + d2 * (ln * 0.4) + curl
        _box(bm, c2, (palm_t * 0.68, palm_w / 5.0, ln * 0.8), (out.cross(fwd).cross(fwd) * -1 if False else out, fwd, d2))
        fingers.append(c1)
    # Jempol: dari pangkal telapak, menyerong ke depan-dalam
    tb = wrist + down * (palm_len * 0.30) + fwd * (palm_w * 0.5)
    td = (down * 0.55 + fwd * 0.65 + (-out) * 0.35).normalized()
    tside = td.cross(out).normalized()
    _box(bm, tb + td * 0.018 * k, (palm_t * 0.8, 0.020 * k, 0.036 * k), (out, tside, td))
    _box(bm, tb + td * 0.045 * k, (palm_t * 0.7, 0.018 * k, 0.026 * k), (out, tside, td))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(f"{cid}_hand_{side}")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(f"{cid}_hand_{side}", me)
    coll.objects.link(ob)
    # Bevel + subdiv ringan supaya organik tapi tetap low-poly
    bv = ob.modifiers.new("Bevel", 'BEVEL'); bv.width = 0.004 * k; bv.segments = 2
    sd = ob.modifiers.new("Subsurf", 'SUBSURF'); sd.levels = 1; sd.render_levels = 1
    # Weights: telapak -> HAND, jari -> FINGER0 (bobot gradasi sepanjang arah jari)
    vh = ob.vertex_groups.new(name=f'{side}_HAND')
    vf = ob.vertex_groups.new(name=f'{side}_FINGER0')
    for v in me.vertices:
        t = (v.co - wrist).dot(down) / (palm_len + 0.06 * k)
        w = max(0.0, min(1.0, (t - 0.45) / 0.4))
        vh.add([v.index], 1.0 - w, 'REPLACE')
        vf.add([v.index], w, 'REPLACE')
    m = bpy.data.materials.get(f"M_{cid}_skin") or bpy.data.materials.new(f"M_{cid}_skin")
    m.use_nodes = True
    bs = m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*skin, 1)
    bs.inputs['Roughness'].default_value = 0.7
    me.materials.append(m)
    am = ob.modifiers.new("Armature", 'ARMATURE'); am.object = rig
    ob.parent = rig
    for p in me.polygons:
        p.use_smooth = True
    return ob


# ─── ANIMASI (aksi berbasis tulang) ──────────────────────────────────────────
def _key(rig, frame, poses):
    for bn, (rx, ry, rz) in poses.items():
        pb = rig.pose.bones.get(bn)
        if not pb:
            continue
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
        pb.keyframe_insert('rotation_euler', frame=frame)


def _loc(rig, frame, bn, z):
    pb = rig.pose.bones[bn]
    pb.location = (0, z, 0)          # Y lokal tulang ≈ sepanjang tulang (naik-turun pinggul)
    pb.keyframe_insert('location', frame=frame)


def make_action(rig, name, keys, loop=True):
    rig.animation_data_create()
    act = bpy.data.actions.new(f"{rig.name}_{name}")
    act.use_fake_user = True
    rig.animation_data.action = act
    for pb in rig.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)
    for f, poses, bob in keys:
        _key(rig, f, poses)
        if bob is not None:
            _loc(rig, f, 'PELVIS', bob)
    act['loop'] = loop
    return act


def build_actions(rig):
    # Sumbu X lokal tulang anggota badan ≈ ayun depan-belakang.
    A = 20   # ayunan kaki (dulu 28 → terlihat menendang)
    B = 18   # ayunan lengan
    walk = [
        (1,  {'L_LEG': (A,0,0), 'R_LEG': (-A,0,0), 'L_LEG1': (-5,0,0), 'R_LEG1': (-30,0,0),
              'L_ARM1': (-B,0,0), 'R_ARM1': (B,0,0), 'L_ARM2': (-10,0,0), 'R_ARM2': (-18,0,0),
              'SPINE': (0,4,0)}, 0.0),
        (7,  {'L_LEG': (0,0,0), 'R_LEG': (0,0,0), 'L_LEG1': (-8,0,0), 'R_LEG1': (-45,0,0),
              'L_ARM1': (0,0,0), 'R_ARM1': (0,0,0), 'L_ARM2': (-12,0,0), 'R_ARM2': (-12,0,0),
              'SPINE': (0,0,0)}, 0.02),
        (13, {'L_LEG': (-A,0,0), 'R_LEG': (A,0,0), 'L_LEG1': (-30,0,0), 'R_LEG1': (-5,0,0),
              'L_ARM1': (B,0,0), 'R_ARM1': (-B,0,0), 'L_ARM2': (-18,0,0), 'R_ARM2': (-10,0,0),
              'SPINE': (0,-4,0)}, 0.0),
        (19, {'L_LEG': (0,0,0), 'R_LEG': (0,0,0), 'L_LEG1': (-45,0,0), 'R_LEG1': (-8,0,0),
              'L_ARM1': (0,0,0), 'R_ARM1': (0,0,0), 'L_ARM2': (-12,0,0), 'R_ARM2': (-12,0,0),
              'SPINE': (0,0,0)}, 0.02),
        (25, {'L_LEG': (A,0,0), 'R_LEG': (-A,0,0), 'L_LEG1': (-5,0,0), 'R_LEG1': (-30,0,0),
              'L_ARM1': (-B,0,0), 'R_ARM1': (B,0,0), 'L_ARM2': (-10,0,0), 'R_ARM2': (-18,0,0),
              'SPINE': (0,4,0)}, 0.0),
    ]
    idle = [
        (1,  {'SPINE1': (0,0,0), 'HEAD': (0,0,0), 'L_ARM2': (-6,0,0), 'R_ARM2': (-6,0,0)}, 0.0),
        (30, {'SPINE1': (2,0,0), 'HEAD': (-2,3,0), 'L_ARM2': (-9,0,0), 'R_ARM2': (-9,0,0)}, -0.004),
        (60, {'SPINE1': (0,0,0), 'HEAD': (0,0,0), 'L_ARM2': (-6,0,0), 'R_ARM2': (-6,0,0)}, 0.0),
    ]
    hoe = [  # angkat dua tangan ke atas kepala -> hantam ke tanah
        (1,  {'SPINE': (0,0,0), 'R_ARM1': (0,0,0), 'L_ARM1': (0,0,0), 'R_ARM2': (0,0,0), 'L_ARM2': (0,0,0)}, 0.0),
        (8,  {'SPINE': (-12,0,0), 'R_ARM1': (-150,0,0), 'L_ARM1': (-150,0,0), 'R_ARM2': (-40,0,0), 'L_ARM2': (-40,0,0)}, 0.0),
        (13, {'SPINE': (30,0,0), 'R_ARM1': (-55,0,0), 'L_ARM1': (-55,0,0), 'R_ARM2': (-5,0,0), 'L_ARM2': (-5,0,0),
              'L_LEG1': (-20,0,0), 'R_LEG1': (-20,0,0)}, -0.05),
        (22, {'SPINE': (0,0,0), 'R_ARM1': (0,0,0), 'L_ARM1': (0,0,0), 'R_ARM2': (0,0,0), 'L_ARM2': (0,0,0),
              'L_LEG1': (0,0,0), 'R_LEG1': (0,0,0)}, 0.0),
    ]
    water = [
        (1,  {'SPINE': (0,0,0), 'R_ARM1': (0,0,0), 'R_ARM2': (0,0,0), 'R_HAND': (0,0,0)}, 0.0),
        (8,  {'SPINE': (12,0,0), 'R_ARM1': (-60,0,0), 'R_ARM2': (-25,0,0), 'R_HAND': (0,0,0)}, 0.0),
        (16, {'SPINE': (16,0,0), 'R_ARM1': (-60,0,0), 'R_ARM2': (-25,0,0), 'R_HAND': (0,0,-35)}, 0.0),
        (26, {'SPINE': (0,0,0), 'R_ARM1': (0,0,0), 'R_ARM2': (0,0,0), 'R_HAND': (0,0,0)}, 0.0),
    ]
    swing = [
        (1,  {'SPINE1': (0,0,0), 'R_ARM1': (0,0,0), 'R_ARM2': (0,0,0)}, 0.0),
        (5,  {'SPINE1': (0,-30,0), 'R_ARM1': (-120,0,40), 'R_ARM2': (-30,0,0)}, 0.0),
        (9,  {'SPINE1': (8,35,0), 'R_ARM1': (-50,0,-30), 'R_ARM2': (-5,0,0)}, -0.02),
        (16, {'SPINE1': (0,0,0), 'R_ARM1': (0,0,0), 'R_ARM2': (0,0,0)}, 0.0),
    ]
    acts = {}
    for n, k, lp in (('idle', idle, True), ('walk', walk, True), ('hoe', hoe, False),
                     ('water', water, False), ('swing', swing, False)):
        acts[n] = make_action(rig, n, k, lp)
    rig.animation_data.action = acts['idle']
    return acts


# ─── MAIN ────────────────────────────────────────────────────────────────────
def build_character(cid, apr_list, col_x):
    s = 0.20 if cid in CHILD else 0.31
    coll = bpy.data.collections.new(cid)
    bpy.context.scene.collection.children.link(coll)
    rig = build_armature(cid, s, coll)
    parts = load_parts(cid, apr_list, s, coll, rig)
    skin = skin_tone(parts)
    for side in ('L', 'R'):
        build_hand(cid, side, s, coll, rig, skin)
    build_actions(rig)
    rig.location.x = col_x
    print(f"[OK] {cid}: {len(parts)} part + 2 tangan, rig {len(rig.data.bones)} tulang")
    return rig


def main():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.armatures, bpy.data.actions,
                 bpy.data.materials, bpy.data.images):
        for d in list(coll):
            coll.remove(d)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    ids = ONLY or list(ROSTER)
    for i, cid in enumerate(ids):
        try:
            build_character(cid, ROSTER[cid], i * 1.0)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"[ERR] {cid}: {e}")
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 25
    sc.render.fps = 24
    os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print("SAVED", BLEND_OUT)


main()
