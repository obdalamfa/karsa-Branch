"""probe_entity_mesh.py — Buktikan entity_mesh.py benar-benar bekerja.

Kenapa probe ini ada
────────────────────
`entity_mesh.py` (458 baris) tidak punya satu pun pemanggil, dan aturan Tahap 2
berbunyi: tidak ada fitur baru sampai yang ada terbukti jalan ATAU ditandai
jujur. Masalahnya "nol pemanggil" biasanya berarti "tidak ada yang tahu apakah
isinya berfungsi" — dan modul yang diam-diam rusak lebih berbahaya daripada
modul yang belum dibuat.

Probe ini menutup separuh pertanyaan itu: isinya berfungsi, diukur. Separuh
kedua (siapa yang akan memakainya) adalah Tahap 7, dan itu memang disengaja
ditaruh belakangan.

Diperiksa:
  1. kurva      bezier, catmull-rom, resample -> jumlah titik & panjang benar
  2. rel        polyline_rails menghasilkan dua sisi dengan lebar yang diminta
  3. geometri   PolyBuilder (disc, ring, ribbon, band) -> ursina.Mesh punya
                verteks, warna per-verteks, dan triangle
  4. NodePath   dua Entity dari dua Mesh = dua GeomNode terpisah (bug
                NodePath-bersama tidak kambuh di jalur ini)
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from panda3d.core import loadPrcFileData
loadPrcFileData('', 'window-type offscreen')
loadPrcFileData('', 'audio-library-name null')

from ursina import Ursina, Entity, application  # noqa: E402
application.asset_folder = ROOT
app = Ursina(size=(320, 180))

from game import entity_mesh as em  # noqa: E402

gagal = []


def cek(nama, ok, detail):
    print(f'{"LULUS" if ok else "GAGAL":6s} {nama:34s} {detail}')
    if not ok:
        gagal.append(nama)


# 1 ── kurva ────────────────────────────────────────────────────────────
# n adalah jumlah SEGMEN, jadi titiknya n+1 (ujung inklusif di kedua sisi) --
# dibaca dari sumbernya, bukan ditebak: probe versi pertama menebak n titik
# dan "GAGAL"-nya adalah ekspektasi probe, bukan cacat modul.
q = em.quad_bezier((0, 0), (1, 2), (2, 0), 16)
c = em.cubic_bezier((0, 0), (0, 1), (1, 1), (1, 0), 16)
cr = em.catmull_rom([(0, 0), (1, 1), (2, 0), (3, 1)], samples_per_span=8)
cek('quad_bezier titik', len(q) == 17, f'{len(q)} titik (16 segmen + 1)')
cek('cubic_bezier titik', len(c) == 17, f'{len(c)} titik (16 segmen + 1)')
cek('catmull_rom menghaluskan', len(cr) > 4, f'{len(cr)} titik dari 4 kontrol')
# Bézier kuadratik harus menyentuh kedua ujung kontrol, tidak titik tengahnya.
cek('quad_bezier ujung tepat',
    q[0] == (0.0, 0.0) and abs(q[-1][0] - 2.0) < 1e-12 and abs(q[-1][1]) < 1e-12,
    f'{q[0]} .. {q[-1]}')

lurus = [(0, 0), (3, 4)]          # panjang 5 tepat
cek('polyline_length', abs(em.polyline_length(lurus) - 5.0) < 1e-9,
    f'{em.polyline_length(lurus):.6f} (harap 5)')

rs = em.resample(lurus, 11)
jarak = [math.dist(rs[i], rs[i + 1]) for i in range(len(rs) - 1)]
cek('resample jarak seragam', len(rs) == 11 and max(jarak) - min(jarak) < 1e-6,
    f'{len(rs)} titik, selisih jarak {max(jarak) - min(jarak):.2e}')

# Fungsinya menjumlahkan belokan di titik DALAM saja (tidak menganggap
# polyline tertutup), jadi keliling kotak memberi 3 x 90 = 270, bukan 360.
kotak = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
cek('total_turning_deg kotak', abs(em.total_turning_deg(kotak) - 270) < 1e-6,
    f'{em.total_turning_deg(kotak):.1f} derajat (3 belokan dalam x 90)')
cek('total_turning_deg lurus', abs(em.total_turning_deg([(0, 0), (1, 0), (2, 0)])) < 1e-9,
    'garis lurus = 0 derajat')

# 2 ── rel ──────────────────────────────────────────────────────────────
kiri, kanan = em.polyline_rails([(0, 0), (1, 0), (2, 0)], 0.25)
lebar = [math.dist(a, b) for a, b in zip(kiri, kanan)]
cek('polyline_rails lebar', max(abs(w - 0.5) for w in lebar) < 1e-6,
    f'lebar {min(lebar):.4f}..{max(lebar):.4f} (harap 0,5)')

# 3 ── geometri ─────────────────────────────────────────────────────────
def bangun():
    pb = em.PolyBuilder()
    pb.add_disc((0, 0), 1.0, (0.30, 0.70, 0.60, 1.0), seg=24, z=0.0)
    pb.add_ring((0, 0), 0.8, 0.08, (0.82, 0.73, 0.37, 1.0), seg=48, z=0.01)
    pb.add_ribbon(em.catmull_rom([(-1, -1), (0, 0), (1, -0.5), (1.5, 0.5)]),
                  0.09, (0.33, 0.71, 0.59, 1.0), z=0.02)
    pb.add_band(*em.polyline_rails([(0, 0), (1, 0), (2, 0.4)], 0.12),
                (0.1, 0.1, 0.12, 1.0), (0.1, 0.1, 0.12, 0.0), z=0.03)
    return pb


pb = bangun()
cek('tri_count terisi', pb.tri_count() > 0, f'{pb.tri_count()} segitiga')
bb = pb.bounds()
cek('bounds masuk akal', bb is not None, f'{bb}')
mesh = pb.mesh()
nv = len(mesh.vertices)
nt = len(mesh.triangles) if getattr(mesh, 'triangles', None) else 0
ncol = len(mesh.colors) if getattr(mesh, 'colors', None) else 0
cek('PolyBuilder verteks', nv > 0, f'{nv} verteks')
cek('PolyBuilder warna per-verteks', ncol == nv, f'{ncol} warna untuk {nv} verteks')
cek('PolyBuilder triangle', nt > 0, f'{nt} indeks triangle')

e1 = em.style_entity(bangun().mesh(), position=(0, 0, 0))
e2 = em.style_entity(bangun().mesh(), position=(2, 0, 0))
g1, g2 = em.geom_nodes(e1), em.geom_nodes(e2)
cek('dua entity, geometri sendiri', g1 >= 1 and g2 >= 1,
    f'GeomNode {g1} dan {g2} (nol berarti bug NodePath-bersama kambuh)')
cek('style_entity unlit', bool(getattr(e1, 'unlit', False)),
    f'unlit={getattr(e1, "unlit", None)} (warna per-verteks mati kalau False)')

print()
print(f'{"SEMUA LULUS" if not gagal else "GAGAL: " + ", ".join(gagal)}')
sys.exit(1 if gagal else 0)
