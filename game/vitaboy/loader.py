"""
loader.py — Konversi VitaboyMesh + Skeleton → Ursina Mesh.

Pemakaian:
    from .vitaboy.loader import load_vitaboy_static
    mesh = load_vitaboy_static("path/to/file.mesh")
    Entity(model=mesh, scale=0.1)

Catatan tentang bind pose:
- File .mesh menyimpan vertex dalam coordinate space BONE-nya masing-masing.
- Saat ada skeleton, tiap vertex di-transform oleh bone.absolute_matrix.
- Tanpa skeleton (skel=None), semua vertex di-render apa adanya → mesh fragments
  overlap di origin, terlihat "remuk". Itu hanya berguna sebagai sanity-check parser.

Lisensi: porting kode FreeSO (GPL v3).
"""
from __future__ import annotations
from typing import Optional, List
import math

from .mesh import VitaboyMesh, Vec3
from .skeleton import Skeleton, Mat4


def _bake_to_world(vmesh: VitaboyMesh, skel: Optional[Skeleton]):
    """Transform tiap vertex ke world space pakai bone.absolute_matrix (kalau ada).

    Return (positions, normals, uvs, triangles) — semuanya list Python primitives,
    ready untuk Ursina Mesh.
    """
    n_verts = len(vmesh.vertices)
    positions: List[tuple] = [None] * n_verts
    normals:   List[tuple] = [None] * n_verts
    uvs:       List[tuple] = [None] * n_verts

    # Build per-vertex bone index dari bindings (sudah diset di mesh.read)
    # Tapi kita ulang juga lewat bindings untuk redundancy
    bone_idx_per_vertex = [v.bone_index for v in vmesh.vertices]

    # Build name → matrix map (kalau ada skeleton)
    bone_matrices = {}
    if skel:
        for b in skel.bones:
            bone_matrices[b.name] = b.absolute_matrix

    # Map binding bone_index ke matrix via bone_name
    bind_index_to_matrix = {}
    for b in vmesh.bone_bindings:
        m = bone_matrices.get(b.bone_name) if skel else None
        bind_index_to_matrix[b.bone_index] = m

    identity = Mat4.identity()
    for i, v in enumerate(vmesh.vertices):
        bm = bind_index_to_matrix.get(v.bone_index)
        if bm is None:
            bm = identity
        p = bm.transform_point(v.position)
        n = bm.transform_direction(v.normal)
        positions[i] = (p.x, p.y, p.z)
        normals[i]   = (n.x, n.y, n.z)
        uvs[i]       = (v.uv.x, 1.0 - v.uv.y)  # flip V (FreeSO Y-down → Ursina Y-up UV)

    # Triangles dari index buffer (FreeSO sudah triangle list)
    # FreeSO X-flip mengubah winding → balik order tiap triangle agar normal menghadap benar
    tris = []
    ib = vmesh.index_buffer
    for f in range(vmesh.num_primitives):
        a, b, c = ib[f*3], ib[f*3+1], ib[f*3+2]
        tris.append((a, c, b))  # reversed winding to compensate X-negation

    return positions, normals, uvs, tris


def load_vitaboy_static(mesh_path: str, skel_path: Optional[str] = None,
                        use_default_skel: bool = True,
                        bmf: bool = False):
    """Load .mesh + skeleton → Ursina Mesh.

    Args:
        mesh_path: Path ke .mesh Vitaboy.
        skel_path: Path ke .skel kalau ada. Kalau None, otomatis cari
                   adult.skel di TSO install. Fallback ke default synthetic.
        use_default_skel: True (default) pakai synthetic skeleton sebagai
                          fallback terakhir kalau TSO tidak ada.
        bmf: True kalau file format BMF (bukan TSO standar .mesh).
    """
    from ursina import Mesh, Vec3 as UVec3
    vmesh = VitaboyMesh.from_file(mesh_path, bmf=bmf)
    skel = None
    if skel_path:
        skel = Skeleton.from_file(skel_path, bcf=False)
    else:
        # Coba auto-discover skeleton TSO asli
        from .tso_paths import skeleton_path
        real_skel = skeleton_path('adult')
        if real_skel:
            skel = Skeleton.from_file(str(real_skel), bcf=False)
        elif use_default_skel:
            from .default_skeleton import default_adult_skeleton
            skel = default_adult_skeleton()
    pos, nrm, uvs, tris = _bake_to_world(vmesh, skel)

    verts  = [UVec3(*p) for p in pos]
    norms  = [UVec3(*n) for n in nrm]

    return Mesh(vertices=verts, triangles=tris,
                normals=norms, uvs=uvs, mode='triangle', static=True)


def vitaboy_stats(mesh_path: str, bmf: bool = False) -> dict:
    """Return dict statistik mesh (untuk debugging/parser-verification)."""
    vmesh = VitaboyMesh.from_file(mesh_path, bmf=bmf)
    return {
        'bones':      len(vmesh.bone_names),
        'bone_names': vmesh.bone_names[:5] + (['...'] if len(vmesh.bone_names) > 5 else []),
        'faces':      vmesh.num_primitives,
        'vertices':   len(vmesh.vertices),
        'blend_verts':len(vmesh.blend_verts),
        'bindings':   len(vmesh.bone_bindings),
        'skin_name':  vmesh.skin_name,
        'texture_name': vmesh.texture_name,
    }
