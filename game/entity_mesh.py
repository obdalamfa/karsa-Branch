"""
entity_mesh.py — Tukang mesh untuk kosakata rupa entitas.

Pembagian kerja dengan entity_style.py:
  entity_style.py  memegang ANGKA — palet, rasio hasil ukur dari logo, tangga
                   eskalasi, dan lima helper motif yang dipakai scene.
  entity_mesh.py   memegang TUKANG — cara mengubah poligon datar jadi
                   ursina.Mesh. Tidak tahu apa-apa soal entitas; kalau dipakai
                   untuk menggambar bendera, dia akan menggambar bendera.

KENAPA SEMUA DATAR
    docs/entity-logo.svg adalah seni vektor datar: tidak ada satu motif pun yang
    bervolume. Jadi semua dibangun di bidang XY lokal dan z dipakai HANYA sebagai
    nomor lapisan (biar tidak z-fighting), bukan sebagai kedalaman bentuk.
    Pemanggil yang memutar/menempatkan pelatnya di dunia.

KENAPA WARNA DIPANGGANG KE VERTEKS
    Diukur, bukan dinalar — _bench/probes/probe_entity_vertexcolor.py, quad
    setengah teal setengah perunggu:

        varian                    kiri            kanan
        tanpa shader eksplisit    (85,180,150)    (210,187,95)   warna hidup
        unlit_shader              (85,180,150)    (210,187,95)   warna hidup
        smooth_shader proyek      (168,168,170)   (168,168,170)  warna MATI
        unlit=True                (85,180,150)    (210,187,95)   warna hidup

    smooth_shader membaca `base = p3d_ColorScale` saja, jadi warna per-verteks
    dibuang total dan gradasi daun keluar abu-abu rata. Konsekuensinya keras:
    entity motif entitas WAJIB unlit dan TIDAK BOLEH lewat apply_smooth().
    Itu juga yang diminta spesifikasi (docs §M3: ujung daun selalu paling terang
    "tak peduli arah matahari scene"; §M8: void tidak menerima ambient).

KENAPA TIDAK ADA CACHE MESH DI SINI
    Mesh Ursina adalah NodePath Panda3D dan sebuah NodePath hanya boleh punya
    SATU parent. Mesh cache yang dibagikan ke banyak Entity membuat semua kecuali
    yang TERAKHIR kehilangan geometri — bug itu sudah menggigit proyek ini dua
    kali (meshes.py, entities.py). Di sini setiap panggilan membangun Mesh baru;
    tidak ada yang bisa dibagi karena tidak ada yang disimpan. Dibuktikan di
    _bench/probes/probe_entity_geom.py dengan menghitung GeomNode tiap entity.
"""
from __future__ import annotations

import math

# Normal menghadap -Z. Semua pelat digambar double_sided, jadi ini cuma supaya
# jalur ber-lampu (kalau ada yang nekat) tidak menghitung normal nol.
_FRONT_N = (0.0, 0.0, -1.0)

TAU = math.pi * 2.0


# ═══════════════════════════════════════════════════════════════════════════
#  WARNA
# ═══════════════════════════════════════════════════════════════════════════
def mix4(c0, c1, f: float):
    """Campur dua RGBA float linear pada f ∈ [0,1]."""
    if f <= 0.0:
        return tuple(c0)
    if f >= 1.0:
        return tuple(c1)
    return (c0[0] + (c1[0] - c0[0]) * f,
            c0[1] + (c1[1] - c0[1]) * f,
            c0[2] + (c1[2] - c0[2]) * f,
            c0[3] + (c1[3] - c0[3]) * f)


def fade(c, a: float):
    """Salinan warna dengan alpha diganti (bukan dikali) — alpha spesifikasi
    selalu absolut, jadi mengalikan akan menggeser semua angka di dokumen."""
    return (c[0], c[1], c[2], a)


# ═══════════════════════════════════════════════════════════════════════════
#  GEOMETRI 2D — kurva, rel, resample
# ═══════════════════════════════════════════════════════════════════════════
def arc_points(cx: float, cy: float, r: float, a0: float, a1: float, seg: int):
    """Titik-titik busur, inklusif di kedua ujung."""
    seg = max(1, int(seg))
    return [(cx + math.cos(a0 + (a1 - a0) * i / seg) * r,
             cy + math.sin(a0 + (a1 - a0) * i / seg) * r) for i in range(seg + 1)]


def circle_points(cx: float, cy: float, r: float, seg: int):
    """Titik lingkaran tertutup (titik terakhir TIDAK mengulang yang pertama)."""
    seg = max(3, int(seg))
    return [(cx + math.cos(TAU * i / seg) * r,
             cy + math.sin(TAU * i / seg) * r) for i in range(seg)]


def quad_bezier(p0, p1, p2, n: int):
    """Bézier kuadratik — dipakai kelopak sabit mata dan bibir mulut."""
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1.0 - t
        out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return out


def cubic_bezier(p0, p1, p2, p3, n: int):
    """Bézier kubik — SATU-SATUNYA kurva yang boleh ada di circuit-tree
    (root flare, docs §M7 aturan 4). Jangan dipakai untuk yang lain di sana."""
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1.0 - t
        out.append((u**3 * p0[0] + 3*u*u*t * p1[0] + 3*u*t*t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3*u*u*t * p1[1] + 3*u*t*t * p2[1] + t**3 * p3[1]))
    return out


def catmull_rom(pts, samples_per_span: int = 8):
    """Kurva halus lewat semua titik kontrol. Dipakai sulur (M6) dan iris mata."""
    p = [tuple(q[:2]) for q in pts]
    if len(p) < 3:
        return list(p)
    ext = [p[0]] + p + [p[-1]]
    out = []
    for i in range(len(ext) - 3):
        p0, p1, p2, p3 = ext[i], ext[i+1], ext[i+2], ext[i+3]
        for s in range(samples_per_span):
            t = s / samples_per_span
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * ((2*p1[0]) + (-p0[0]+p2[0])*t
                       + (2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2
                       + (-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3),
                0.5 * ((2*p1[1]) + (-p0[1]+p2[1])*t
                       + (2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2
                       + (-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)))
    out.append(p[-1])
    return out


def polyline_length(pts) -> float:
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def resample(pts, n: int):
    """Sampel ulang polyline jadi tepat n titik berjarak busur sama."""
    n = max(2, int(n))
    if len(pts) < 2:
        return [tuple(pts[0][:2])] * n
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(segs)
    if total <= 1e-9:
        return [tuple(pts[0][:2])] * n
    out, i, acc = [], 0, 0.0
    for k in range(n):
        target = total * k / (n - 1)
        while i < len(segs) - 1 and acc + segs[i] < target:
            acc += segs[i]
            i += 1
        f = 0.0 if segs[i] <= 1e-12 else (target - acc) / segs[i]
        a, b = pts[i], pts[i + 1]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def total_turning_deg(pts) -> float:
    """Jumlah belokan bertanda sepanjang polyline, derajat."""
    tot = 0.0
    for i in range(1, len(pts) - 1):
        ax, ay = pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1]
        bx, by = pts[i+1][0] - pts[i][0], pts[i+1][1] - pts[i][1]
        if (ax or ay) and (bx or by):
            tot += math.degrees(math.atan2(ax * by - ay * bx, ax * bx + ay * by))
    return tot


def min_bend_radius(pts) -> float:
    """Radius lingkaran-luar terkecil pada tiga titik berurutan.

    Dipakai sebagai penjaga aturan kelengkungan sulur (docs §M6): sulur yang
    membelok terlalu tajam berhenti terbaca sebagai tumbuh dan mulai terbaca
    sebagai kabel yang tertekuk — register yang salah untuk tahap 1–3.
    """
    best = float('inf')
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i-1], pts[i], pts[i+1]
        ab, bc, ca = math.dist(a, b), math.dist(b, c), math.dist(c, a)
        area2 = abs((b[0]-a[0]) * (c[1]-a[1]) - (b[1]-a[1]) * (c[0]-a[0]))
        if area2 < 1e-12 or ab * bc * ca < 1e-12:
            continue
        best = min(best, ab * bc * ca / (2.0 * area2))
    return best


def polyline_rails(pts, half_w):
    """Dua rel sejajar polyline, sambungan miter (fillet NOL — itu tellnya).

    half_w boleh skalar atau daftar sepanjang pts (untuk pita yang meruncing).
    """
    n = len(pts)
    if not isinstance(half_w, (list, tuple)):
        half_w = [half_w] * n
    left, right = [], []
    for i in range(n):
        if i == 0:
            tx, ty = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        elif i == n - 1:
            tx, ty = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
        else:
            tx = pts[i+1][0] - pts[i-1][0]
            ty = pts[i+1][1] - pts[i-1][1]
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        # Kompensasi miter: di tikungan, rel harus melebar 1/cos(θ/2) supaya
        # lebar tegak lurus pita tetap konstan. Dibatasi 3x biar sudut tajam
        # tidak meledak jadi duri.
        scale = 1.0
        if 0 < i < n - 1:
            ax, ay = pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1]
            bx, by = pts[i+1][0] - pts[i][0], pts[i+1][1] - pts[i][1]
            la, lb = math.hypot(ax, ay) or 1.0, math.hypot(bx, by) or 1.0
            cosang = (ax * bx + ay * by) / (la * lb)
            cosang = max(-1.0, min(1.0, cosang))
            half = math.acos(cosang) * 0.5
            scale = min(3.0, 1.0 / max(0.34, math.cos(half)))
        w = half_w[i] * scale
        left.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
        right.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    return left, right


# ═══════════════════════════════════════════════════════════════════════════
#  AKUMULATOR POLIGON
# ═══════════════════════════════════════════════════════════════════════════
class PolyBuilder:
    """Kumpulkan segitiga datar berwarna-verteks, lalu panggil .mesh().

    z SELALU nomor lapisan, bukan kedalaman bentuk. Urutan penambahan =
    urutan gambar di dalam satu Geom, jadi tambahkan dari BELAKANG ke DEPAN
    supaya alpha blending menumpuk benar tanpa perlu sortir per-frame.
    """

    __slots__ = ('v', 't', 'c', 'n', 'uv', 'with_uv', 'has_alpha')

    def __init__(self, with_uv: bool = False):
        self.v: list = []
        self.t: list = []
        self.c: list = []
        self.n: list = []
        self.uv: list = []
        self.with_uv = with_uv
        self.has_alpha = False

    # ─── primitif ────────────────────────────────────────
    def _p(self, x: float, y: float, z: float, col, uv=(0.0, 0.0)) -> int:
        i = len(self.v)
        self.v.append((x, y, z))
        self.c.append((col[0], col[1], col[2], col[3]))
        self.n.append(_FRONT_N)
        if self.with_uv:
            self.uv.append(uv)
        if col[3] < 0.999:
            self.has_alpha = True
        return i

    def add_tri(self, p0, p1, p2, cols, z: float = 0.0, uvs=None):
        if not isinstance(cols, (list, tuple)) or len(cols) != 3 \
                or not isinstance(cols[0], (list, tuple)):
            cols = (cols, cols, cols)
        uvs = uvs or ((0, 0), (0, 0), (0, 0))
        a = self._p(p0[0], p0[1], z, cols[0], uvs[0])
        b = self._p(p1[0], p1[1], z, cols[1], uvs[1])
        c = self._p(p2[0], p2[1], z, cols[2], uvs[2])
        self.t.append((a, b, c))

    def add_quad(self, p0, p1, p2, p3, cols, z: float = 0.0, uvs=None):
        """p0..p3 berurutan keliling. Digambar dua segitiga."""
        if not isinstance(cols, (list, tuple)) or len(cols) != 4 \
                or not isinstance(cols[0], (list, tuple)):
            cols = (cols, cols, cols, cols)
        uvs = uvs or ((0, 0), (1, 0), (1, 1), (0, 1))
        a = self._p(p0[0], p0[1], z, cols[0], uvs[0])
        b = self._p(p1[0], p1[1], z, cols[1], uvs[1])
        c = self._p(p2[0], p2[1], z, cols[2], uvs[2])
        d = self._p(p3[0], p3[1], z, cols[3], uvs[3])
        self.t.append((a, b, c))
        self.t.append((a, c, d))

    def add_quad3(self, p0, p1, p2, p3, col):
        """Quad dengan titik 3D penuh — dipakai HANYA untuk sisi tebal (rim)
        cincin gear yang diekstrusi. Motif lain semuanya sebidang."""
        a = self._p(p0[0], p0[1], p0[2], col)
        b = self._p(p1[0], p1[1], p1[2], col)
        c = self._p(p2[0], p2[1], p2[2], col)
        d = self._p(p3[0], p3[1], p3[2], col)
        self.t.append((a, b, c))
        self.t.append((a, c, d))

    def add_band(self, rail_a, rail_b, cols_a, cols_b, z: float = 0.0,
                 uv_a=None, uv_b=None, closed: bool = False):
        """Pita quad antara dua rel sepanjang-sama. Tulang punggung modul ini:
        annulus, goresan cincin, pita sulur, badan daun, dan garis luar semuanya
        adalah pita."""
        n = min(len(rail_a), len(rail_b))
        if n < 2:
            return
        if not isinstance(cols_a, (list, tuple)) or not isinstance(cols_a[0], (list, tuple)):
            cols_a = [cols_a] * n
        if not isinstance(cols_b, (list, tuple)) or not isinstance(cols_b[0], (list, tuple)):
            cols_b = [cols_b] * n
        rng = range(n) if closed else range(n - 1)
        for i in rng:
            j = (i + 1) % n
            ua = uv_a[i] if uv_a else (0.0, i / (n - 1))
            ub = uv_a[j] if uv_a else (0.0, j / (n - 1))
            va = uv_b[i] if uv_b else (1.0, i / (n - 1))
            vb = uv_b[j] if uv_b else (1.0, j / (n - 1))
            self.add_quad(rail_a[i], rail_a[j], rail_b[j], rail_b[i],
                          (cols_a[i], cols_a[j], cols_b[j], cols_b[i]), z,
                          (ua, ub, vb, va))

    def add_fan(self, center, ring, col_center, cols_ring, z: float = 0.0,
                closed: bool = True):
        """Kipas dari satu titik pusat. Sah untuk poligon berbentuk bintang
        terhadap pusatnya — cakram, ladang iris berlobus, glow disc."""
        n = len(ring)
        if n < 3:
            return
        if not isinstance(cols_ring, (list, tuple)) or not isinstance(cols_ring[0], (list, tuple)):
            cols_ring = [cols_ring] * n
        last = n if closed else n - 1
        for i in range(last):
            j = (i + 1) % n
            self.add_tri(center, ring[i], ring[j],
                         (col_center, cols_ring[i], cols_ring[j]), z)

    def add_disc(self, c, r: float, col, seg: int = 20, z: float = 0.0,
                 col_edge=None):
        self.add_fan(c, circle_points(c[0], c[1], r, seg), col,
                     col_edge if col_edge is not None else col, z)

    def add_ring(self, c, r: float, w: float, col, seg: int = 48, z: float = 0.0):
        """Goresan cincin berpusat di r, tebal w."""
        inner = circle_points(c[0], c[1], r - w * 0.5, seg)
        outer = circle_points(c[0], c[1], r + w * 0.5, seg)
        self.add_band(inner, outer, col, col, z, closed=True)

    def add_segment(self, p0, p1, w: float, col, z: float = 0.0,
                    round_cap: bool = False, cap_seg: int = 6):
        """Satu ruas lurus tebal w, sambungan miter tidak berlaku (satu ruas)."""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(dx, dy)
        if ln < 1e-9:
            return
        nx, ny = -dy / ln * w * 0.5, dx / ln * w * 0.5
        self.add_quad((p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
                      (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny), col, z)
        if round_cap:
            self.add_disc(p0, w * 0.5, col, cap_seg, z)
            self.add_disc(p1, w * 0.5, col, cap_seg, z)

    def add_ribbon(self, pts, w, col, z: float = 0.0, round_cap: bool = True,
                   cap_seg: int = 6, cols=None):
        """Pita bertebal w mengikuti polyline. w boleh daftar (meruncing)."""
        if len(pts) < 2:
            return
        hw = [x * 0.5 for x in w] if isinstance(w, (list, tuple)) else w * 0.5
        left, right = polyline_rails(pts, hw)
        self.add_band(left, right, cols or col, cols or col, z)
        if round_cap:
            r0 = hw[0] if isinstance(hw, list) else hw
            r1 = hw[-1] if isinstance(hw, list) else hw
            c0 = cols[0] if cols else col
            c1 = cols[-1] if cols else col
            self.add_disc(pts[0], r0, c0, cap_seg, z)
            self.add_disc(pts[-1], r1, c1, cap_seg, z)

    # ─── komposisi ───────────────────────────────────────
    def merge(self, other: 'PolyBuilder', offset=(0.0, 0.0, 0.0),
              rot_deg: float = 0.0, scale: float = 1.0):
        """Tempel builder lain dengan transform 2D. Inilah cara emblem penuh
        dirakit jadi SATU mesh: satu draw call, bukan seratus entity."""
        if not other.v:
            return self
        ca, sa = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
        base = len(self.v)
        for (x, y, z), col, nrm in zip(other.v, other.c, other.n):
            x, y = x * scale, y * scale
            self.v.append((x * ca - y * sa + offset[0],
                           x * sa + y * ca + offset[1],
                           z * scale + offset[2]))
            self.c.append(col)
            self.n.append(nrm)
            if col[3] < 0.999:
                self.has_alpha = True
        if self.with_uv:
            if other.with_uv and len(other.uv) == len(other.v):
                self.uv.extend(other.uv)
            else:
                self.uv.extend([(0.0, 0.0)] * len(other.v))
        self.t.extend([(a + base, b + base, c + base) for a, b, c in other.t])
        return self

    # ─── keluaran ────────────────────────────────────────
    def bounds(self):
        if not self.v:
            return (0.0, 0.0, 0.0, 0.0)
        xs = [p[0] for p in self.v]
        ys = [p[1] for p in self.v]
        return (min(xs), min(ys), max(xs), max(ys))

    def tri_count(self) -> int:
        return len(self.t)

    def mesh(self):
        """Bangun ursina.Mesh baru. TIDAK di-cache: lihat catatan modul soal
        NodePath-bersama. Import Ursina ditunda supaya modul ini bisa diimpor
        oleh tooling tanpa membuka window Panda3D."""
        from ursina import Mesh  # noqa: PLC0415 — lazy disengaja
        if not self.v:
            # Mesh kosong = entity tanpa GeomNode = tepat yang diburu
            # cek `geom_nol` di tools/regress.py. Jangan pernah kembalikan itu.
            raise ValueError('PolyBuilder kosong — mesh tanpa geometri dilarang')
        kw = dict(vertices=list(self.v), triangles=list(self.t),
                  colors=list(self.c), normals=list(self.n), mode='triangle')
        if self.with_uv and len(self.uv) == len(self.v):
            kw['uvs'] = list(self.uv)
        return Mesh(**kw)


# ═══════════════════════════════════════════════════════════════════════════
#  PABRIK ENTITY
# ═══════════════════════════════════════════════════════════════════════════
def style_entity(mesh, position=(0, 0, 0), *, rotation=(0, 0, 0), scale=1.0,
                 billboard: bool = False, transparent: bool = True,
                 name: str = 'entity_taint', parent=None):
    """Entity standar untuk motif entitas: unlit, dua sisi, warna dari verteks.

    unlit WAJIB — lihat catatan modul. Kalau ini diganti jadi apply_smooth,
    seluruh gradasi hilang dan motifnya keluar abu-abu rata.
    """
    from ursina import Entity, color as _color, scene as _scene  # noqa: PLC0415
    e = Entity(model=mesh, position=position, rotation=rotation, scale=scale,
               color=_color.white, double_sided=True, unlit=True,
               parent=parent if parent is not None else _scene)
    if transparent:
        e.transparent = True
    e.name = name
    if billboard:
        e.billboard = True
    return e


def geom_nodes(entity_or_np) -> int:
    """Hitung GeomNode di bawah sebuah NodePath. Nol = korban NodePath-bersama.
    Dipakai probe & laporan; sama persis dengan cek `geom_nol` di regress.py."""
    m = getattr(entity_or_np, 'model', entity_or_np)
    if m is None:
        return 0
    try:
        return len(m.findAllMatches('**/+GeomNode'))
    except Exception:
        return -1
