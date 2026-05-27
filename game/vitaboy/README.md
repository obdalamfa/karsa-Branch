# Vitaboy Port — Lembah Karsa 3D

Python port modular dari sistem karakter Vitaboy FreeSO (TSOClient) ke
Ursina/Panda3D. Membaca file `.mesh` standar TSO dan merakit ke world space
pakai skeleton T-pose synthetic.

## Sumber

Lokasi FreeSO TSO content (di mesin user):
```
E:/Documents/Panda demo/panda_atb_demo/FreeSO/TSOClient/FSO.Content.TSO/bin/Debug/Content/Avatar/
  ├── Animations/   (1000+ .anim — belum di-port)
  ├── Appearances/  (.apr — set kombinasi mesh/texture)
  ├── Bindings/     (.bnd — pemetaan body part)
  ├── Meshes/       (~116 .mesh STANDALONE — sudah bisa di-load)
  └── Textures/     (.png — UV-mapped ke mesh)
```

Skeleton `.skel` original ada di TSO `.dat` archive yang **TIDAK** ada di
install FreeSO ini. Sebagai pengganti, modul `default_skeleton.py` memberikan
T-pose adult synthetic dengan bone hierarchy standar.

## Struktur Modul

| File | Fungsi |
|------|--------|
| `bcf_reader.py` | Pembaca binary mixed-endian (int big, float little — FreeSO quirk) |
| `mesh.py` | Parser `.mesh`: vertex (pos+norm+UV), bindings, blend data |
| `skeleton.py` | Parser `.skel`: bone tree + compute world matrices |
| `default_skeleton.py` | Adult T-pose hardcoded — pengganti `adult.skel` |
| `loader.py` | Bake VitaboyMesh + Skeleton → Ursina Mesh siap di-render |
| `__init__.py` | Public API |

## Quick Usage

```python
from game.vitaboy import load_vitaboy_static, vitaboy_stats

# Inspect tanpa render
stats = vitaboy_stats('path/to/au-blue.mesh')
# → {'bones': 6, 'faces': 1084, 'vertices': 685, ...}

# Render di Ursina dengan synthetic skeleton
from ursina import Entity
mesh = load_vitaboy_static('path/to/au-blue.mesh')
Entity(model=mesh, scale=1.0, color=color.white)
```

## Standalone Viewer

```bash
cd 3d/
python test_vitaboy.py
```

Tombol `1-9` untuk ganti sample mesh. Kamera EditorCamera (drag mouse).

## Format `.mesh` (Big-Endian + Little-Endian floats)

Quirk penting: FreeSO `IoBuffer` flag `BIG_ENDIAN` hanya berlaku untuk integer.
`ReadFloat` selalu pakai `BinaryReader.ReadSingle()` → **little-endian**.
Karena itu `BCFReader.read_int*` pakai `>` tapi `read_float` pakai `<`.

Layout:
```
int32   version (= 2)
int32   bone_count
pascal  bone_names[bone_count]
int32   face_count
int32[] index_buffer[face_count * 3]
int32   binding_count
struct  bindings[binding_count]:
  int32 bone_index, first_real, real_count, first_blend, blend_count
int32   real_vertex_count
float[] uvs[real_vertex_count * 2]    (LITTLE-ENDIAN floats)
int32   blend_vertex_count
struct  blend_data[blend_vertex_count]:
  int32 weight_raw (/0x8000), int32 other_vertex
int32   real_vertex_count2 (duplicate)
float[] positions[real_vertex_count * 6]  (pos.x.y.z + norm.x.y.z, X negated)
float[] blend_verts_normals[blend_vertex_count * 6]
```

## TODO / Belum diport

- **Animation `.anim`** — keyframe per bone (quat + vec3). Parser belum dibuat.
- **Vertex skinning** — sekarang mesh di-bake static di T-pose. Untuk animasi
  perlu skinning per-frame (sampling animasi → re-compute bone matrices → re-bake).
- **Appearance `.apr` + Binding `.bnd`** — gabungan multiple meshes (head, body,
  hands, shoes) jadi satu karakter.
- **FAR3 archive reader** — buka `.dat` archive untuk dapat skeleton + animasi
  original (kalau user nanti install TSO content lengkap).
- **Texture binding** — auto-map `au-*.png` ke mesh `au-*.mesh`.

## Lisensi

Port dari kode FreeSO C# (GPL v3) → Python. Modul ini juga dilisensikan
GPL v3 sesuai inheritance. Sumber asli: <https://github.com/riperiperi/FreeSO>
