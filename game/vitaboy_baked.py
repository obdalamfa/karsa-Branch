"""
vitaboy_baked.py — Avatar Vitaboy sebagai Character Panda3D asli (skinning di C++).

KENAPA MODUL INI ADA
====================
`game/vitaboy/avatar.py` men-skin mesh di Python: tiap re-bake ia memanggil
`Mat4.transform_point()` dan `transform_direction()` sekali per vertex, lalu
menulis ulang seluruh vertex buffer Ursina. Diukur (`_bench/probes/probe_baked_glb.py`):

    8 VitaboyAvatar, 471 vertex/avatar, di-update tiap frame  -> 3.467 ms per avatar
    8 Character Panda3D, 1537 vertex/avatar, animasi penuh    -> 0.517 ms per avatar

Enam kali lebih murah walau vertex-nya tiga kali lebih banyak — karena deformasi
dan interpolasi keyframe-nya dikerjakan C++, bukan Python.

VERSI LAMA MODUL INI MEMUAT ASET YANG RUSAK
===========================================
Modul ini dulu memuat 25 file `.glb` hasil `tools/bake_vitaboy.py` (Blender).
File-file itu ADA di `assets/models/`, memuat tanpa error, punya 29 joint dan
animasi yang benar-benar jalan — tapi geometrinya gumpalan, bukan manusia
(lihat `_bench/shots/baked_glb_alone.png`: bounding box 7.3 x 4.1 x 4.7 unit
untuk satu badan, tanpa material sama sekali). Bake Blender-nya salah bobot.
Karena itu jalur GLB TIDAK dipakai lagi sebagai sumber karakter; ia disimpan
sebagai `load_baked_actor()` untuk aset GLB lain yang mungkin benar.

Gantinya, karakter dirakit langsung dari data TSO ke Character Panda3D di
memori — tanpa Blender, tanpa file perantara. Kesetaraan matematisnya diukur di
`_bench/probes/probe_native_char.py`:

    net-transform bind vs Vitaboy absolute_matrix : selisih 0.000000
    net-transform frame 7 (AnimBundle vs FK Python): selisih 0.000001
    posisi vertex hasil skinning, 29 bone          : selisih 0.000003

DASAR KONVERSINYA
=================
Mesh Vitaboy menyimpan vertex dalam RUANG-BONE (posisi relatif terhadap satu
bone; makanya `avatar.py` cukup `bm.transform_point(v.position)` tanpa inverse
bind matrix). Panda3D memakai konvensi berbeda: vertex disimpan dalam ruang
bind, dan matriks skinning-nya `initial_net_transform_inverse * net_transform`.
Jembatannya satu baris: pindahkan vertex ke ruang bind sekali saat build,

    v_bind = v_bone * bindAbsoluteMatrix

lalu Panda3D menghitung `v_bind * inv(bindAbs) * net = v_bone * net` — persis
yang dihitung `avatar.py`, tapi di C++ dan hanya saat geometri terlihat.

Baik Vitaboy maupun Panda3D memakai matriks row-major dengan konvensi
row-vector (v * M) dan komposisi lokal `R * T`, jadi tidak ada transpose atau
tukar sumbu di mana pun. Itu yang membuat selisihnya nol.

PEMAKAIAN
=========
    from game.vitaboy_baked import build_native_avatar
    av = build_native_avatar(npc_entity, ['mabd002_casual.apr', 'mahd001_ross.apr'])
    av.set_animation('a2o-walking-loop')
    av.update(dt)      # no-op; ada supaya API-nya sama dengan VitaboyAvatar

Gagal-lunak: semua fungsi mengembalikan None kalau aset TSO tidak ada.
"""
from __future__ import annotations

import io as _io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Direktori GLB baked lama (jalur legacy, lihat docstring di atas)
_VITABOY_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'models'

# Animasi yang dipakai game. Di-bake sekali, dipakai bersama semua karakter.
DEFAULT_ANIMS: Tuple[str, ...] = (
    'a2a-talk-idle-loop',
    'a2o-walking-loop',
    'a2o-slide-normal',
    'a2o-broom-fly-leftside',
    # Klip kerja. Tanpa ini avatar TSO tidak punya gerak apa pun untuk aksi
    # alat: `_play_tool_anim` memutar `_pivot_shoulder_r`, dan pivot itu milik
    # humanoid prosedural — pada avatar TSO ia tidak menggerakkan satu vertex
    # pun. Diukur pada strip enam ubin: gerak antar-ubin 0,0% untuk GOSOK dan
    # PANEN, melawan 46,1% dan 40,5% pada strip patokan. Enam ubin identik.
    'a2o-fso-outsideshower-scrub',   # menggosok — sapuan tangan bolak-balik
    'a2o-lever-pull-start',          # menarik/mengayun — dipakai kerja alat
    'a2o-kart-ride',                 # duduk menunggang
)

# ─── CACHE MODUL ─────────────────────────────────────────────────────────────
# AnimBundle tidak bergantung pada outfit — skeleton-nya sama untuk semua avatar
# dewasa. Jadi di-bake SEKALI lalu dipakai bersama; tiap Character mendapat
# AnimControl sendiri saat bind, sehingga frame counternya tidak saling ganggu.
# (Ini bukan bug NodePath-bersama: AnimBundle bukan NodePath dan tidak pernah
# di-reparent — yang di-share hanya tabel keyframe read-only.)
_ANIM_CACHE: Dict[str, object] = {}
_MESH_CACHE: Dict[Tuple[int, int], object] = {}
_TEX_CACHE: Dict[Tuple[int, int], object] = {}
_APR_CACHE: Dict[str, list] = {}
_native_failed = False


def native_available() -> bool:
    """True kalau aset TSO ada dan skeleton dewasa bisa dimuat."""
    if _native_failed:
        return False
    try:
        from .vitaboy import asset_registry
        return asset_registry().load_skel('adult') is not None
    except Exception:
        return False


# ─── MATEMATIKA ──────────────────────────────────────────────────────────────
def _to_lmat(m):
    """Mat4 Vitaboy (row-major) -> LMatrix4f Panda3D. Tanpa transpose: kedua
    sisi memakai konvensi row-vector yang sama (dibuktikan di
    _bench/probes/probe_native_char.py, selisih 0.000000)."""
    from panda3d.core import LMatrix4f
    r = m.m
    return LMatrix4f(r[0][0], r[0][1], r[0][2], r[0][3],
                     r[1][0], r[1][1], r[1][2], r[1][3],
                     r[2][0], r[2][1], r[2][2], r[2][3],
                     r[3][0], r[3][1], r[3][2], r[3][3])


def _local_matrix(bone):
    """Transform lokal satu bone: R * T (urutan FreeSO)."""
    from .vitaboy.skeleton import Mat4
    return Mat4.from_quat(bone.rotation) * Mat4.from_translation(bone.translation)


# ─── BAKE ANIMASI (sekali per proses) ────────────────────────────────────────
def _bake_anim_bundle(name: str):
    """Ubah satu Animation Vitaboy jadi AnimBundle Panda3D.

    Tiap frame dipose dengan FK Python persis seperti `avatar.py`, lalu matriks
    lokalnya diurai jadi 12 komponen (skala/shear/hpr/translasi) yang diminta
    AnimChannelMatrixXfmTable. Uraiannya pakai `decomposeMatrix` bawaan Panda3D
    supaya tidak ada konvensi quaternion yang perlu ditebak sendiri.
    """
    if name in _ANIM_CACHE:
        return _ANIM_CACHE[name]

    from panda3d.core import (AnimBundle, AnimChannelMatrixXfmTable,
                              PTAFloat, CPTAFloat, LVecBase3f, decomposeMatrix)
    from .vitaboy import asset_registry
    from .vitaboy.mesh import Vec3 as VVec3
    from .vitaboy.skeleton import Quat as VQuat

    reg = asset_registry()
    skel = reg.load_skel('adult')
    anim = reg.load_anim(name)
    if skel is None or anim is None or anim.num_frames <= 0:
        _ANIM_CACHE[name] = None
        return None

    # Pose bind harus dipulihkan tiap frame; skeleton dari registry di-cache
    # dan dipakai bersama, jadi kita tidak boleh meninggalkannya dalam pose
    # animasi terakhir.
    bind = {b.name: (VVec3(b.translation.x, b.translation.y, b.translation.z),
                     VQuat(b.rotation.x, b.rotation.y, b.rotation.z, b.rotation.w))
            for b in skel.bones}

    nf = anim.num_frames
    comp = {b.name: {c: [0.0] * nf for c in 'xyzhprijkabc'} for b in skel.bones}
    sc, sh, hpr, pos = LVecBase3f(), LVecBase3f(), LVecBase3f(), LVecBase3f()

    for f in range(nf):
        for b in skel.bones:
            t, r = bind[b.name]
            b.translation = VVec3(t.x, t.y, t.z)
            b.rotation = VQuat(r.x, r.y, r.z, r.w)
        for m in anim.motions:
            b = skel.get_bone(m.bone_name)
            if b is None or m.frame_count <= 0:
                continue
            if m.has_translation:
                i = m.first_translation_index + min(f, m.frame_count - 1)
                if 0 <= i < len(anim.translations):
                    t = anim.translations[i]
                    b.translation = VVec3(t.x, t.y, t.z)
            if m.has_rotation:
                i = m.first_rotation_index + min(f, m.frame_count - 1)
                if 0 <= i < len(anim.rotations):
                    q = anim.rotations[i]
                    b.rotation = VQuat(q.x, q.y, q.z, q.w)
        for b in skel.bones:
            decomposeMatrix(_to_lmat(_local_matrix(b)), sc, sh, hpr, pos)
            d = comp[b.name]
            d['x'][f], d['y'][f], d['z'][f] = pos[0], pos[1], pos[2]
            d['h'][f], d['p'][f], d['r'][f] = hpr[0], hpr[1], hpr[2]
            d['i'][f], d['j'][f], d['k'][f] = sc[0], sc[1], sc[2]
            d['a'][f], d['b'][f], d['c'][f] = sh[0], sh[1], sh[2]

    # Kembalikan skeleton bersama ke pose bind — instance ini di-cache registry.
    for b in skel.bones:
        t, r = bind[b.name]
        b.translation = VVec3(t.x, t.y, t.z)
        b.rotation = VQuat(r.x, r.y, r.z, r.w)
    skel.recompute_absolute_matrices()

    bundle = AnimBundle(name, float(anim.fps or 30), nf)

    def add_chan(bone, parent_group):
        ch = AnimChannelMatrixXfmTable(parent_group, bone.name)
        d = comp[bone.name]
        for c in 'xyzhprijkabc':
            pta = PTAFloat.emptyArray(nf)
            for f in range(nf):
                pta.setElement(f, d[c][f])
            ch.setTable(c, CPTAFloat(pta))
        for k in bone.children:
            add_chan(k, ch)

    add_chan(skel.root, bundle)
    _ANIM_CACHE[name] = bundle
    return bundle


# ─── BANGUN GEOMETRI ─────────────────────────────────────────────────────────
def _read_apr_parts(apr_name: str):
    """Resolve satu .apr -> [(VitaboyMesh, texture_bytes, texture_key)]."""
    if apr_name in _APR_CACHE:
        return _APR_CACHE[apr_name]

    from .vitaboy import asset_registry
    from .vitaboy.appearance import Appearance, Binding
    from .vitaboy.bcf_reader import BCFReader
    from .vitaboy.mesh import VitaboyMesh

    reg = asset_registry()
    out = []
    apr_bytes = reg.read_bytes(apr_name)
    if apr_bytes is None:
        _APR_CACHE[apr_name] = out
        return out
    apr = Appearance.from_bytes(apr_bytes)
    for ref in apr.bindings:
        bnd_data = reg.read_by_id(ref.type_id, ref.file_id)
        if bnd_data is None:
            continue
        bnd = Binding.from_bytes(bnd_data)
        if not bnd.has_mesh:
            continue
        key = (bnd.mesh_type_id, bnd.mesh_file_id)
        mesh = _MESH_CACHE.get(key)
        if mesh is None:
            mesh_data = reg.read_by_id(*key)
            if mesh_data is None:
                continue
            mesh = VitaboyMesh()
            try:
                mesh.read(BCFReader(_io.BytesIO(mesh_data)), bmf=False)
            except Exception as e:
                logging.warning(f"vitaboy_baked: mesh parse gagal ({apr_name}): {e}")
                continue
            _MESH_CACHE[key] = mesh
        tex_key = None
        if bnd.has_texture:
            tex_key = (bnd.texture_type_id, bnd.texture_file_id)
        out.append((mesh, tex_key))
    _APR_CACHE[apr_name] = out
    return out


def _texture_for(tex_key, wajah_chibi: bool = False,
                 rambut_chibi: bool = False, varian=None):
    """Texture Panda3D dari entri registry TSO, di-cache per (type_id, file_id).

    Texture BOLEH dipakai bersama banyak Entity — ia bukan NodePath, jadi tidak
    kena bug satu-parent yang dua kali menghantam proyek ini.

    `wajah_chibi=True` melewatkan tekstur lewat `wajah.lukis_wajah_chibi()`
    dulu: mata besar beriris, hidung sekadar titik, mulut segaris. Dipakai
    HANYA untuk .apr kepala — lihat `wajah.apr_kepala()` untuk kenapa mesh
    rambut tidak boleh dapat wajah. `rambut_chibi=True` untuk mesh rambut
    terpisah: warnanya saja yang diganti.

    Kunci cache ikut membawa `varian['id']`. Tanpa itu dua warga yang memakai
    .apr kepala yang sama akan berbagi satu tekstur, dan yang dibangun lebih
    dulu mewariskan wajah DAN warna rambutnya ke yang kedua — persis kegagalan
    "semua warga bermata sama" yang dicatat ronde 1.
    """
    if tex_key is None:
        return None
    vid = (varian or {}).get('id', '') if isinstance(varian, dict) else ''
    if wajah_chibi:
        kunci = (tex_key, 'chibi', vid)
    elif rambut_chibi:
        kunci = (tex_key, 'rambut', vid)
    else:
        kunci = tex_key
    if kunci in _TEX_CACHE:
        return _TEX_CACHE[kunci]
    tex = None
    try:
        from PIL import Image
        from ursina import Texture
        from .vitaboy import asset_registry
        data = asset_registry().read_by_id(*tex_key)
        if data:
            img = None
            if wajah_chibi:
                from .wajah import tekstur_kepala_chibi
                img = tekstur_kepala_chibi(data, kunci=kunci, varian=varian)
            elif rambut_chibi:
                from .wajah import tekstur_rambut_chibi
                img = tekstur_rambut_chibi(data, kunci=kunci, varian=varian)
            if img is None:
                img = Image.open(_io.BytesIO(data))
            tex = Texture(img)
            tex.filtering = True
    except Exception as e:
        logging.warning(f"vitaboy_baked: texture gagal {tex_key}: {e}")
        tex = None
    _TEX_CACHE[kunci] = tex
    return tex


def _build_geom(mesh, bind_abs, joints, name: str):
    """VitaboyMesh -> GeomNode ber-skinning (TransformBlendTable).

    Vertex dipindah ke ruang bind di sini, SEKALI. Setelah itu Panda3D yang
    mendeformasinya tiap frame, di C++.
    """
    from panda3d.core import (Geom, GeomNode, GeomTriangles, GeomVertexArrayFormat,
                              GeomVertexAnimationSpec, GeomVertexData,
                              GeomVertexFormat, GeomVertexWriter, InternalName,
                              JointVertexTransform, SparseArray, TransformBlend,
                              TransformBlendTable)

    n_v = len(mesh.vertices)
    if n_v == 0 or mesh.num_primitives == 0:
        return None

    arr = GeomVertexArrayFormat()
    arr.addColumn(InternalName.getVertex(), 3, Geom.NTFloat32, Geom.CPoint)
    arr.addColumn(InternalName.getNormal(), 3, Geom.NTFloat32, Geom.CNormal)
    arr.addColumn(InternalName.getTexcoord(), 2, Geom.NTFloat32, Geom.CTexcoord)
    blend_arr = GeomVertexArrayFormat()
    blend_arr.addColumn(InternalName.getTransformBlend(), 1, Geom.NTUint16, Geom.CIndex)

    fmt = GeomVertexFormat()
    fmt.addArray(arr)
    fmt.addArray(blend_arr)
    spec = GeomVertexAnimationSpec()
    spec.setPanda()          # skinning di CPU oleh Panda3D (C++), bukan Python
    fmt.setAnimation(spec)
    fmt = GeomVertexFormat.registerFormat(fmt)

    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vdata.setNumRows(n_v)
    tbt = TransformBlendTable()

    # Satu baris blend per bone yang dipakai; vertex Vitaboy selalu terikat ke
    # satu bone dengan bobot penuh (mesh.py mengisi vertex.bone_index dari
    # bone_bindings), jadi tidak ada bobot pecahan yang perlu dinormalkan.
    idx_to_bone = {}
    for b in mesh.bone_bindings:
        idx_to_bone[b.bone_index] = b.bone_name
    blend_row: Dict[str, int] = {}
    for bone_name in set(idx_to_bone.values()):
        j = joints.get(bone_name)
        if j is None:
            continue
        blend_row[bone_name] = tbt.addBlend(TransformBlend(JointVertexTransform(j), 1.0))
    if not blend_row:
        return None
    fallback_row = next(iter(blend_row.values()))

    vw = GeomVertexWriter(vdata, InternalName.getVertex())
    nw = GeomVertexWriter(vdata, InternalName.getNormal())
    tw = GeomVertexWriter(vdata, InternalName.getTexcoord())
    bw = GeomVertexWriter(vdata, InternalName.getTransformBlend())

    from .vitaboy.skeleton import Mat4
    from .vitaboy.mesh import Vec3 as VVec3
    from .wajah import skala_vertex
    identity = Mat4.identity()
    for v in mesh.vertices:
        bone_name = idx_to_bone.get(v.bone_index)
        bm = bind_abs.get(bone_name, identity)
        # Proporsi chibi. Vertex TSO tersimpan dalam RUANG-TULANG, jadi
        # mengalikannya di sini sama persis dengan menskalakan bagian itu
        # terhadap titik asal tulangnya — di pose bind maupun di tiap frame
        # animasi, karena posisi akhir selalu `v.position * net(tulang)`.
        # Skalanya seragam, jadi arah normal tidak berubah dan tidak perlu
        # matriks normal terpisah.
        s = skala_vertex(bone_name)
        pos = v.position if s == 1.0 else VVec3(v.position.x * s,
                                                v.position.y * s,
                                                v.position.z * s)
        p = bm.transform_point(pos)
        n = bm.transform_direction(v.normal)
        vw.addData3(p.x, p.y, p.z)
        nw.addData3(n.x, n.y, n.z)
        tw.addData2(v.uv.x, 1.0 - v.uv.y)
        bw.addData1i(blend_row.get(bone_name, fallback_row))

    tbt.setRows(SparseArray.lowerOn(n_v))
    vdata.setTransformBlendTable(tbt)

    tris = GeomTriangles(Geom.UHStatic)
    ib = mesh.index_buffer
    for f in range(mesh.num_primitives):
        a, b, c = ib[f * 3], ib[f * 3 + 1], ib[f * 3 + 2]
        if a >= n_v or b >= n_v or c >= n_v:
            continue
        tris.addVertices(a, c, b)     # winding dibalik: sumbu X di-negate saat parse
    tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    gnode = GeomNode(name)
    gnode.addGeom(geom)
    return gnode


# ─── AVATAR NATIVE ───────────────────────────────────────────────────────────
class NativeAvatar:
    """Avatar Vitaboy sebagai Character Panda3D.

    API-nya sengaja dibuat sama dengan `vitaboy.VitaboyAvatar` (`set_animation`,
    `update`, `speed`, `root_entity`, `parts`) supaya `player.py` dan
    `entities.py` bisa memegang salah satu dari keduanya tanpa percabangan.

    Bedanya: `update()` di sini tidak melakukan apa-apa. Interpolasi keyframe
    dan deformasi vertex dikerjakan Panda3D di C++ saat cull — dan hanya untuk
    karakter yang benar-benar terlihat.
    """

    # `_ujung` WAJIB ada di sini. Kelas ini pakai __slots__, jadi menulis
    # atribut yang tidak terdaftar melempar AttributeError — dan pemanggilnya
    # menangkap SEMUA exception lalu turun diam-diam ke jalur avatar berikutnya.
    # Akibatnya bukan "tutup tangan tidak muncul", tapi "seluruh avatar TSO
    # diganti sosok lain" tanpa satu pun pesan yang menyebut penyebabnya.
    __slots__ = ('root_entity', 'char_np', 'parts', '_controls', '_current',
                 '_speed', '_char', '_head_np', '_head_ctrl', '_ujung')

    def __init__(self, parent_entity, apr_list: List[str],
                 scale: float = 0.30, tint=None,
                 anims: Tuple[str, ...] = DEFAULT_ANIMS,
                 varian=None):
        from panda3d.core import Character, CharacterJoint, NodePath
        from ursina import Entity, color
        from .vitaboy import asset_registry
        from .vitaboy.skeleton import Mat4

        reg = asset_registry()
        skel = reg.load_skel('adult')
        if skel is None:
            raise RuntimeError("NativeAvatar: adult.skel tidak ada di registry")

        # Salin absolute matrix pose-bind SEBELUM apa pun mem-pose skeleton
        # bersama ini. Registry mengembalikan instance yang sama untuk semua
        # pemanggil, jadi "muat ulang untuk dapat yang bersih" tidak bekerja.
        bind_abs = {b.name: Mat4([row[:] for row in b.absolute_matrix.m])
                    for b in skel.bones}

        # Ganti rugi tinggi untuk kepala chibi yang diperbesar: lihat
        # `wajah.py`. Tanpa ini setiap warga desa jadi 11% lebih jangkung dan
        # semua yang sudah disetel untuk tinggi lama (papan nama, tinggi
        # pintu, sudut kamera) meleset — padahal yang diminta cuma proporsi.
        from .wajah import SKALA_TINGGI
        self.root_entity = Entity(parent=parent_entity, scale=scale * SKALA_TINGGI)
        char = Character('vitaboy')
        bundle = char.getBundle(0)
        joints: Dict[str, object] = {}

        def add_joint(bone, parent_part):
            j = CharacterJoint(char, bundle, parent_part, bone.name,
                               _to_lmat(_local_matrix(bone)))
            joints[bone.name] = j
            for c in bone.children:
                add_joint(c, j)

        add_joint(skel.root, bundle)

        self._char = char
        self.char_np = NodePath(char)
        self.char_np.reparentTo(self.root_entity)
        if tint is not None and tint != color.white:
            self.char_np.setColor(tint.r, tint.g, tint.b, tint.a)

        from .wajah import apr_kepala, apr_rambut, varian_wajah
        if varian is None:
            varian = varian_wajah('')
        self.parts = []
        for apr_name in apr_list:
            if not apr_name:
                continue
            kepala = apr_kepala(apr_name)
            rambut = apr_rambut(apr_name)
            for k, (mesh, tex_key) in enumerate(_read_apr_parts(apr_name)):
                gnode = _build_geom(mesh, bind_abs, joints, f'{apr_name}#{k}')
                if gnode is None:
                    continue
                np_ = self.char_np.attachNewNode(gnode)
                tex = _texture_for(tex_key, wajah_chibi=kepala,
                                   rambut_chibi=rambut, varian=varian)
                if tex is not None:
                    np_.setTexture(tex._texture if hasattr(tex, '_texture') else tex, 1)
                self.parts.append((mesh, np_))

        if not self.parts:
            self.root_entity.disable()
            raise RuntimeError("NativeAvatar: tidak ada part yang berhasil di-load")

        self._controls: Dict[str, object] = {}
        for a in anims:
            ab = _bake_anim_bundle(a)
            if ab is None:
                continue
            try:
                self._controls[a] = bundle.bindAnim(ab, -1)
            except Exception as e:
                logging.warning(f"NativeAvatar: bind '{a}' gagal: {e}")
        self._current: Optional[str] = None
        self._speed = 1.0
        # Head-seek dibuat MALAS: karakter yang tidak pernah
        # memandang apa pun tidak membayar sepeser pun.
        self._head_np = None
        self._head_ctrl = None

        # Tangan dan kaki dipasang di sini, dan alasannya bukan gaya.
        #
        # Kritikus buta ronde 3 mengukurnya di crop 6x: kedua lengan meruncing
        # lalu BERHENTI di pinggul tanpa kepalan dan tanpa jari, dan kedua pipa
        # celana terpotong rata sebagai TABUNG BERONGGA yang bagian dalam
        # gelapnya terlihat, melayang di atas rumput tanpa sepatu. Badan TSO
        # `mabd002_casual.apr` memang tidak membawa mesh tangan maupun sepatu —
        # keduanya aset terpisah yang tidak pernah ikut dimuat.
        #
        # Menutupnya di ujung tulang, bukan dengan menambal mesh badannya,
        # supaya ia ikut animasi apa pun tanpa perlu di-bake ulang: joint
        # di-expose sekali, lalu bentuknya menempel sebagai anak node itu.
        self._ujung = []
        self._pasang_ujung()

    # Mitten dan bot. Radius dalam satuan tulang; nilainya dipilih supaya
    # lebarnya kira-kira sama dengan lengan/pipa celana yang ditutupinya,
    # bukan gumpalan yang menempel di ujungnya.
    # (nama joint, radius, geser lokal, warna). Warna DIPASANG di sini dan
    # tidak diwariskan: tanpa itu tutupnya keluar putih polos dan terbaca
    # sebagai titik terang yang menempel, bukan sebagai tangan.
    # Hanya TANGAN. Tutup kaki sudah dicoba dan sengaja TIDAK dipasang.
    #
    # Diukur, bukan disimpulkan: tutup kaki dibesarkan sampai radius 0,34
    # (dua kali lebih besar dari yang wajar) dan diwarnai merah menyala supaya
    # tidak mungkin terlewat. Yang sampai ke layar 14 piksel; digeser +0,55 di
    # sumbu ketiga, tinggal 8. Joint R_FOOT/L_FOOT pada kerangka ini duduk di
    # atau di bawah bidang tanah, jadi apa pun yang digantung di sana terkubur.
    #
    # Celah yang disebut kritikus buta — "pipa celana terpotong rata sebagai
    # tabung berongga tanpa sepatu" — karena itu MASIH TERBUKA. Perbaikannya
    # bukan di sini: mesh celananya sendiri yang harus dipendekkan lalu bot
    # dipasang di atas mata kaki, dan itu perubahan di ruang bind, bukan
    # penambahan node di ujung tulang.
    UJUNG = (
        ('R_HAND', 0.115, (0.0, 0.0, 0.0), (196, 148, 108)),
        ('L_HAND', 0.115, (0.0, 0.0, 0.0), (196, 148, 108)),
    )

    def _pasang_ujung(self):
        """Tutup ujung lengan dan kaki yang menganga dengan bentuk membulat.

        Diam-diam tidak melakukan apa pun kalau joint-nya tidak ada: kerangka
        yang berbeda tidak boleh membuat avatar gagal dimuat sama sekali.
        """
        try:
            from panda3d.core import NodePath
            from ursina import color
            from .meshes import soft_cube_mesh
        except Exception:
            return
        bundle = self._char.getBundle(0)
        for nama, r, geser, warna in self.UJUNG:
            try:
                sendi = self.char_np.attachNewNode(nama + '_ujung')
                # `exposeJoint` itu milik direct.actor.Actor, bukan Character
                # mentah — dan avatar ini dibangun tanpa Actor. Jalur yang ada
                # di Panda mentah: temukan CharacterJoint-nya, lalu minta ia
                # menyalin transform net-nya ke node kita tiap frame.
                joint = bundle.findChild(nama)
                if joint is None or not hasattr(joint, 'addNetTransform'):
                    sendi.removeNode()
                    continue
                joint.addNetTransform(sendi.node())
                bentuk = NodePath(soft_cube_mesh()._instance()
                                  if hasattr(soft_cube_mesh(), '_instance')
                                  else soft_cube_mesh())
                bentuk.reparentTo(sendi)
                bentuk.setScale(r * 2.0, r * 2.6 if 'FOOT' in nama else r * 2.0,
                                r * 2.0)
                bentuk.setPos(*geser)
                bentuk.setColorScale(warna[0] / 255.0, warna[1] / 255.0,
                                     warna[2] / 255.0, 1.0)
                self._ujung.append(sendi)
            except Exception:
                continue

    # ── API yang sama dengan VitaboyAvatar ──
    def set_animation(self, name: str) -> bool:
        if name == self._current:
            return True
        ctrl = self._controls.get(name)
        if ctrl is None:
            ab = _bake_anim_bundle(name)
            if ab is None:
                return False
            try:
                ctrl = self._char.getBundle(0).bindAnim(ab, -1)
            except Exception:
                return False
            self._controls[name] = ctrl
        for other in self._controls.values():
            if other is not ctrl:
                other.stop()
        ctrl.setPlayRate(self._speed)
        ctrl.loop(True)
        self._current = name
        return True

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, v: float):
        self._speed = v
        ctrl = self._controls.get(self._current) if self._current else None
        if ctrl is not None:
            ctrl.setPlayRate(v)

    # ── Head-seek: satu joint diambil alih Python, sisanya tetap C++ ──
    HEAD_JOINT = 'HEAD'

    def look_at_world(self, world_pos) -> bool:
        """Suruh kepala menoleh ke satu titik dunia. None = kembali lurus.

        Ini satu-satunya bagian karakter yang dianimasikan dari Python, dan
        sengaja: ia SATU joint, bukan 471 vertex. `control_joint()` Panda3D
        menyerahkan joint HEAD ke kita sementara seluruh badan tetap
        dianimasikan C++ — dibuktikan di `_bench/probes/probe_headseek.py`
        (joint kepala berputar: 14,40% piksel berubah; animasi badan tetap
        jalan sesudahnya: 59.951 piksel berubah antar frame).

        Return False kalau joint kepala tidak bisa diambil alih; pemanggil
        boleh mengabaikannya — karakternya cuma tidak menoleh.
        """
        if self._head_np is None:
            if world_pos is None:
                return False          # tidak perlu bangun apa pun
            from panda3d.core import NodePath
            from .animator import HeadSeekController
            np_ = NodePath('head_seek')
            try:
                ok = self._char.getBundle(0).controlJoint(self.HEAD_JOINT,
                                                          np_.node())
            except Exception:
                ok = False
            if not ok:
                logging.warning(
                    f"NativeAvatar: joint '{self.HEAD_JOINT}' tidak bisa "
                    f"dikendalikan; head-seek dimatikan untuk avatar ini.")
                self._head_np = False      # False = sudah dicoba dan gagal
                return False
            self._head_np = np_
            self._head_ctrl = HeadSeekController()
        if self._head_np is False:
            return False
        self._head_ctrl.look_at(
            None if world_pos is None
            else (world_pos[0], world_pos[1], world_pos[2]))
        return True

    def update(self, dt: float):
        """Nyaris tidak melakukan apa-apa — dan itulah intinya.

        VitaboyAvatar.update() menulis ulang ratusan vertex dari Python tiap
        kali dipanggil. Di sini deformasi dan interpolasi keyframe dikerjakan
        Panda3D di C++ saat cull, dan hanya untuk karakter yang benar-benar
        terlihat.

        Yang tersisa untuk Python cuma head-seek, itu pun hanya kalau kepalanya
        memang sedang menoleh atau sedang kembali lurus. Selebihnya method ini
        keluar di baris pertama.
        """
        ctrl = self._head_ctrl
        if ctrl is None or not ctrl.aktif:
            return
        np_ = self._head_np
        if not np_:
            return
        root = self.root_entity
        try:
            # Kepala kira-kira 1,7 m di atas kaki avatar. Presisinya tidak
            # penting: yang dipakai cuma ARAH, dan targetnya hampir selalu jauh
            # lebih jauh daripada galat setinggi kepala.
            kepala = (root.world_x,
                      root.world_y + 1.7 * float(root.world_scale_y or 1.0),
                      root.world_z)
            yaw = float(root.world_rotation_y or 0.0)
        except Exception:
            return
        h, v = ctrl.update(dt, kepala, yaw)
        np_.setHpr(h, v, 0)

    @property
    def playing(self) -> bool:
        ctrl = self._controls.get(self._current) if self._current else None
        return bool(ctrl and ctrl.isPlaying())

    def cleanup(self):
        for ctrl in self._controls.values():
            try:
                ctrl.stop()
            except Exception:
                pass
        self._controls.clear()
        # Lepas joint kepala kalau sempat diambil alih, supaya
        # bundle tidak memegang node yang sudah dibuang.
        if self._head_np:
            try:
                self._char.getBundle(0).releaseJoint(self.HEAD_JOINT)
            except Exception:
                pass
            try:
                self._head_np.removeNode()
            except Exception:
                pass
        self._head_np = None
        self._head_ctrl = None
        try:
            self.char_np.removeNode()
        except Exception:
            pass


def build_native_avatar(parent_entity, apr_list: List[str],
                        scale: float = 0.30, tint=None,
                        anims: Tuple[str, ...] = DEFAULT_ANIMS,
                        varian=None) -> Optional[NativeAvatar]:
    """Bangun NativeAvatar; None kalau aset TSO tidak ada atau gagal.

    Gagal-lunak disengaja: pemanggil (vitaboy_npc.py) turun ke jalur berikutnya
    tanpa membuat load_scene() ikut mati.
    """
    global _native_failed
    if _native_failed:
        return None
    try:
        return NativeAvatar(parent_entity, apr_list, scale=scale, tint=tint,
                            anims=anims, varian=varian)
    except Exception as e:
        logging.warning(f"NativeAvatar gagal ({e}); turun ke jalur berikutnya.")
        return None


# ─── JALUR LAMA: GLB HASIL BAKE BLENDER ──────────────────────────────────────
# Disimpan untuk aset GLB lain yang mungkin benar. JANGAN dipakai untuk
# karakter: 25 file au-*.glb di assets/models/ terbukti rusak (lihat docstring
# modul dan _bench/shots/baked_glb_alone.png).
def load_baked_actor(path: str, play: Optional[str] = None,
                     loop: bool = True):
    """Load .glb/.bam sebagai Actor Panda3D. None kalau gagal."""
    from panda3d.core import Filename
    from direct.actor.Actor import Actor

    p = Path(path)
    if not p.is_absolute():
        p = _VITABOY_DIR.parent.parent / path
    if not p.exists():
        logging.warning(f"Vitaboy baked tidak ada: {p}")
        return None

    try:
        actor = Actor(Filename.fromOsSpecific(str(p)))
    except Exception as e:
        logging.warning(f"Actor load failed: {e}")
        return None

    if play:
        anim_names = actor.getAnimNames()
        target = play if play in anim_names else (anim_names[0] if anim_names else None)
        if target is None:
            logging.warning(f"Tidak ada anim di {p.name}")
        elif loop:
            actor.loop(target)
        else:
            actor.play(target)
    return actor


def list_baked() -> List[Path]:
    """List semua .glb/.bam di assets/models/."""
    if not _VITABOY_DIR.exists():
        return []
    return sorted(list(_VITABOY_DIR.glob('*.glb')) + list(_VITABOY_DIR.glob('*.bam')))


def bake_status() -> dict:
    """Diagnostik untuk probe dan laporan."""
    baked = list_baked()
    return {
        'glb_legacy': len(baked),
        'glb_total_kb': sum(b.stat().st_size for b in baked) // 1024,
        'glb_usable_for_characters': False,   # terbukti gumpalan, lihat docstring
        'native_available': native_available(),
        'anims_baked': sorted(k for k, v in _ANIM_CACHE.items() if v is not None),
    }


class BakedNPCActor:
    """Dua Actor GLB (idle + walk) yang ditukar saat NPC bergerak.

    STATUS: jalur legacy. Kodenya jalan — 8 Actor dari file yang sama semuanya
    dapat geometri (`_bench/probes/probe_baked_glb.py`), jadi tidak ada bug
    NodePath-bersama di sini — tetapi FILE GLB-nya rusak, sehingga kelas ini
    tidak dipakai untuk karakter. Dibiarkan utuh supaya kalau suatu saat ada
    GLB dua-state yang benar, tinggal dipakai lagi.
    """

    def __init__(self, color_name: str, parent=None, scale: float = 0.32):
        self.color = color_name
        self.idle_actor = load_baked_actor(
            str(_VITABOY_DIR / f'au-{color_name}_idle.glb'))
        self.walk_actor = load_baked_actor(
            str(_VITABOY_DIR / f'au-{color_name}_walk.glb'))
        for a in (self.idle_actor, self.walk_actor):
            if a:
                a.set_scale(scale)
                if parent is not None:
                    try:
                        a.reparent_to(parent)
                    except Exception:
                        pass
        self._state = None
        if self.idle_actor:
            self.set_idle()
        elif self.walk_actor:
            self.set_walk()

    def _swap(self, show, hide, state):
        if self._state == state:
            return
        if hide:
            hide.hide()
        if show:
            show.show()
            names = show.getAnimNames()
            if names:
                show.loop(names[0])
        self._state = state

    def set_idle(self):
        self._swap(self.idle_actor, self.walk_actor, 'idle')

    def set_walk(self):
        self._swap(self.walk_actor, self.idle_actor, 'walk')

    def cleanup(self):
        for a in (self.idle_actor, self.walk_actor):
            if a:
                try:
                    a.cleanup()
                    a.remove_node()
                except Exception:
                    pass
