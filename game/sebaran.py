"""sebaran.py — Semua benda kecil di tanah dirakit jadi SATU mesh per scene.

## Kenapa modul ini ada

Keluhan pemilik: "lingkungannya masih terlalu plain atau membosankan."
Dibandingkan `_bench/refs/farm_wide.jpg` pada jarak main yang sama, yang hilang
bukan poligon besar — rumah dan pagar sudah ada — melainkan BENDA KECIL:
rumpun rumput yang lebih tinggi dan lebih gelap, bunga liar bertaburan, kerikil,
ranting, semak di tepi jalan. Di patokan itu tidak pernah ada satu bidang warna
yang lebih lebar dari beberapa langkah tanpa sesuatu yang memecahnya.

`world._add_outdoor_deco()` sudah mencoba itu dan berhenti di tengah jalan: ia
membuat SATU Entity per benda. Itu plafon yang keras. Kepadatan yang dibutuhkan
patokan (~2 benda per ubin) berarti ~1.100 Entity tambahan di `town` saja —
dan `tools/regress.py` mengukur ms/frame sebagai pemeriksaan, karena scene
terberat (`mountain`, 2.249 entity) sudah 72 ms/frame. Jalur itu buntu.

## Cara yang dipakai

Satu Mesh untuk SELURUH benda kecil di satu scene, diwarnai lewat VERTEX COLOR.
Ongkosnya satu Entity dan satu draw call, berapa pun jumlah benda di dalamnya —
sementara jumlah segitiganya (~8.000 di scene terpadat) tidak berarti apa-apa
untuk GPU mana pun. Hasil bersihnya: kepadatan NAIK beberapa kali lipat
sementara jumlah Entity TURUN, karena versi per-Entity yang lama ikut dicabut.

Vertex color bisa dipakai karena `smooth_shader` v6 membaca `p3d_Color`:

    vec4 base = p3d_ColorScale * v_color;

(Catatan lama di kepala `meshes.py` yang menyebut vertex color "tidak bisa
dipakai" ditulis sebelum shader itu punya kolom warna. Untuk pagar cara palet-
lewat-UV tetap dipertahankan; di sini vertex color yang benar, karena tiap helai
rumput butuh gradasi pangkal-ke-ujung, bukan satu dari empat pita.)

## Kenapa ia ikut melambai

Entity hasil `bangun_entity()` didaftarkan ke `World3D._grass_ents`-nya sendiri
lalu diberi grass_shader. Vertex shader itu menggeser vertex berdasarkan
`world.y - 0.15`, jadi PANGKAL rumpun diam dan UJUNGnya bergoyang — persis
perilaku yang diinginkan, tanpa satu baris kode tambahan. Kerikil punya tinggi
di bawah ambang itu, jadi ia tidak ikut bergerak.

## Batas yang tidak boleh dilanggar

- Mesh Ursina adalah NodePath Panda3D dan hanya boleh punya SATU parent
  (BRIEF §8.1). Tiap panggilan `bangun_entity()` merakit Mesh BARU. Jangan
  pernah menyimpan hasilnya di cache modul.
- Semua koordinat di sini WORLD, dan entity pemakainya berdiri di origin dengan
  scale (1,1,1). Menskalakan entity itu akan menggepengkan seluruh sebaran.
"""
import math

# ─── Palet ──────────────────────────────────────────────────────────────────
# Nilai (terang-gelap) dipilih lebih dulu, warnanya belakangan: rumpun harus
# LEBIH GELAP daripada rumput di bawahnya supaya terbaca sebagai gumpalan,
# bukan sebagai noda terang. Di patokan AWL rumpun tinggi selalu bayangan.
_HIJAU_RUMPUN = (
    ((58, 92, 44),  (104, 152, 70)),   # pangkal gelap → ujung sedang
    ((50, 84, 40),  (92, 138, 62)),
    ((66, 100, 48), (118, 164, 78)),
    ((54, 80, 46),  (96, 130, 68)),    # sedikit kebiruan, rumput teduh
)
_HIJAU_SEMAK = (
    ((40, 70, 36), (78, 116, 54)),
    ((46, 76, 40), (88, 128, 60)),
    ((36, 62, 38), (72, 104, 56)),
)
# Bunga liar: kelopak terang, tangkai hijau tua. Warna diambil dari patokan —
# putih, kuning pucat, merah muda, ungu muda. TIDAK ada yang jenuh penuh:
# bunga yang lebih terang dari HUD akan menarik mata ke tempat yang salah.
# Kelopak juga diturunkan: warna di atas ~215 pasti mentok jadi putih setelah
# dikali cahaya siang, dan enam warna berbeda semuanya berakhir sebagai titik
# putih yang sama. Ini pita nilai yang masih menyisakan corak setelah dikali.
_KELOPAK = ((196, 192, 176), (204, 176,  84), (200, 118, 138),
            (158, 136, 196), (208, 150,  92), (186, 200, 186))
_TANGKAI = ((62, 96, 48), (96, 132, 68))

# Kerikil sengaja GELAP. Ronde pertama memakai (104..168) dan hasilnya di layar
# adalah kotak PUTIH: pengali cahaya siang 1,37 mengangkat 168 ke 230, lalu
# bahu sorot menahannya di ~214 — batu yang lebih terang daripada tanah tempat
# ia tergeletak. Batu di patokan selalu lebih GELAP daripada tanahnya; itu yang
# membuatnya terbaca sebagai batu dan bukan sebagai kilau.
_KERIKIL = (
    ((56, 54, 52),  (96, 92, 86)),
    ((62, 58, 50),  (104, 98, 88)),
    ((50, 50, 52),  (86, 86, 86)),
)
_RANTING = (((78, 60, 40), (122, 96, 62)),
            ((66, 52, 36), (108, 86, 58)))


# ─── Perakit ────────────────────────────────────────────────────────────────
class Perakit:
    """Penampung vertex/normal/uv/warna/segitiga untuk satu mesh gabungan."""
    __slots__ = ('v', 'n', 'u', 'c', 't')

    def __init__(self):
        self.v = []; self.n = []; self.u = []; self.c = []; self.t = []

    def kosong(self) -> bool:
        return not self.t

    def jml_verteks(self) -> int:
        return len(self.v)

    def mesh(self):
        """Mesh BARU tiap panggilan — lihat catatan NodePath di kepala modul."""
        from ursina import Mesh, Vec3, Vec2, Vec4
        if not self.t:
            raise ValueError('Perakit kosong — mesh tanpa geometri dilarang '
                             '(itu yang diburu cek geom_nol)')
        return Mesh(vertices=[Vec3(*p) for p in self.v],
                    triangles=list(self.t),
                    normals=[Vec3(*p) for p in self.n],
                    uvs=[Vec2(*p) for p in self.u],
                    colors=[Vec4(*p) for p in self.c],
                    mode='triangle', static=True)


def _w(rgb):
    """(0..255) → Vec4-siap (0..1) dengan alpha penuh."""
    return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, 1.0)


def _quad(acc, p0, p1, p2, p3, nrm, c_bawah, c_atas):
    """Satu segi empat, dua vertex bawah berwarna `c_bawah`, dua atas `c_atas`.

    Gradasi pangkal-ke-ujung ini yang membuat sehelai rumput terbaca sebagai
    helai, bukan sebagai potongan kertas warna. Ongkosnya nol: warnanya sudah
    harus ada di tiap vertex.
    """
    b = len(acc.v)
    for p, c, uv in ((p0, c_bawah, (0.0, 0.0)), (p1, c_bawah, (1.0, 0.0)),
                     (p2, c_atas, (1.0, 1.0)), (p3, c_atas, (0.0, 1.0))):
        acc.v.append(p); acc.n.append(nrm); acc.u.append(uv); acc.c.append(c)
    acc.t.append((b, b + 1, b + 2))
    acc.t.append((b, b + 2, b + 3))


def _norm_tegak(dx, dz):
    """Normal untuk bidang tegak yang menghadap (dx,dz), DIMIRINGKAN ke atas.

    Kalau normalnya benar-benar mendatar, separuh helai menghadap menjauhi
    matahari dan cel-shader menjatuhkannya ke pita paling gelap — sebaran jadi
    tampak setengah mati. Dicondongkan ke +Y supaya sebagian besar helai masuk
    pita terang, dan yang menghadap membelakangi matahari cuma turun satu pita.
    """
    L = math.hypot(dx, dz) or 1.0
    nx, nz = dx / L * 0.62, dz / L * 0.62
    ny = 0.80
    m = math.sqrt(nx * nx + ny * ny + nz * nz)
    return (nx / m, ny / m, nz / m)


def _helai(acc, x, y, z, tinggi, lebar, sudut, condong, c_bawah, c_atas):
    """Sehelai daun/rumput: segi empat tegak yang meruncing dan sedikit rebah."""
    ca, sa = math.cos(sudut), math.sin(sudut)
    # Sumbu melintang helai (mendatar, tegak lurus arah hadapnya).
    sx, sz = -sa, ca
    hw = lebar * 0.5
    tw = lebar * 0.14          # ujung meruncing, tidak nol supaya tetap terlihat
    lx, lz = ca * condong, sa * condong
    nrm = _norm_tegak(ca, sa)
    _quad(acc,
          (x - sx * hw, y, z - sz * hw),
          (x + sx * hw, y, z + sz * hw),
          (x + lx + sx * tw, y + tinggi, z + lz + sz * tw),
          (x + lx - sx * tw, y + tinggi, z + lz - sz * tw),
          nrm, c_bawah, c_atas)


def _bidang_datar(acc, x, y, z, r, sudut, warna):
    """Segi empat mendatar kecil (kepala bunga, daun rebah)."""
    ca, sa = math.cos(sudut), math.sin(sudut)
    ax, az = ca * r, sa * r
    bx, bz = -sa * r, ca * r
    _quad(acc,
          (x - ax - bx, y, z - az - bz),
          (x + ax - bx, y, z + az - bz),
          (x + ax + bx, y, z + az + bz),
          (x - ax + bx, y, z - az + bz),
          (0.0, 1.0, 0.0), warna, warna)


def _kotak(acc, x, y, z, hx, hy, hz, sudut, c_bawah, c_atas):
    """Balok tanpa alas (5 sisi) — alasnya tertanam di tanah, tidak pernah dilihat."""
    ca, sa = math.cos(sudut), math.sin(sudut)

    def P(u, v, w):
        return (x + u * ca - w * sa, y + v, z + u * sa + w * ca)

    # atas
    _quad(acc, P(-hx, hy, -hz), P(hx, hy, -hz), P(hx, hy, hz), P(-hx, hy, hz),
          (0.0, 1.0, 0.0), c_atas, c_atas)
    for dx, dz, nx, nz in ((hx, 0.0, 1.0, 0.0), (-hx, 0.0, -1.0, 0.0),
                           (0.0, hz, 0.0, 1.0), (0.0, -hz, 0.0, -1.0)):
        ux, uz = (0.0, hz) if dx else (hx, 0.0)
        nrm = _norm_tegak(nx * ca - nz * sa, nx * sa + nz * ca)
        _quad(acc,
              P(dx - ux, -hy, dz - uz), P(dx + ux, -hy, dz + uz),
              P(dx + ux, hy, dz + uz), P(dx - ux, hy, dz - uz),
              nrm, c_bawah, c_atas)


# ─── Benda ──────────────────────────────────────────────────────────────────
def rumpun(acc, x, y, z, r, skala=1.0):
    """Gumpalan rumput tinggi: dua-tiga helai dari satu titik.

    Ini benda yang paling banyak dipakai, dan yang paling banyak berpengaruh:
    di patokan, apa yang membedakan rumput yang hidup dari bidang hijau adalah
    gumpalan yang lebih TINGGI dan lebih GELAP, bukan warna rumputnya sendiri.
    """
    cb, ca_ = _HIJAU_RUMPUN[int(r(11) * len(_HIJAU_RUMPUN)) % len(_HIJAU_RUMPUN)]
    wb, wa = _w(cb), _w(ca_)
    # Empat sampai lima helai, bukan dua sampai tiga. Ronde pertama memakai dua
    # dan hasilnya di layar adalah JARUM tunggal yang berdiri sendiri-sendiri —
    # terbaca sebagai artefak, bukan sebagai rumput. Yang dicari adalah gumpalan
    # dengan siluet, dan siluet baru muncul kalau helainya saling menutupi.
    n = 4 + (1 if r(12) > 0.5 else 0)
    dasar = r(13) * math.tau
    for i in range(n):
        a = dasar + i * (math.tau / n) + (r(14 + i) - 0.5) * 0.8
        jr = (0.02 + r(20 + i) * 0.085) * skala
        t = (0.26 + r(23 + i) * 0.30) * skala
        _helai(acc, x + math.cos(a) * jr, y, z + math.sin(a) * jr,
               t, 0.10 * skala, a, t * (0.24 + r(26 + i) * 0.34), wb, wa)


def semak(acc, x, y, z, r):
    """Semak tepi: sama seperti rumpun tapi lebih besar, lebih lebar, lebih tua.

    Dipasang di batas zona (rumput bertemu tanah/air). Batas material yang
    ditumbuhi jauh lebih terbaca daripada batas yang dipotong lurus — itu satu
    dari sedikit hal yang paling jelas beda antara frame kita dan patokan.
    """
    cb, ca_ = _HIJAU_SEMAK[int(r(31) * len(_HIJAU_SEMAK)) % len(_HIJAU_SEMAK)]
    wb, wa = _w(cb), _w(ca_)
    dasar = r(32) * math.tau
    for i in range(4):
        a = dasar + i * (math.tau / 4) + (r(33 + i) - 0.5) * 0.7
        jr = 0.05 + r(38 + i) * 0.16
        t = 0.42 + r(42 + i) * 0.34
        _helai(acc, x + math.cos(a) * jr, y, z + math.sin(a) * jr,
               t, 0.17, a, t * 0.36, wb, wa)


def bunga(acc, x, y, z, r):
    """Rumpun bunga liar: tiga sampai empat kuntum kecil dari satu titik.

    Versi pertama: SATU kuntum, sebuah segi empat mendatar berjari-jari 5-8 cm.
    Di layar 1920x1080 itu keluar sebagai persegi putih atau merah muda yang
    RATA menghadap kamera — terbaca sebagai sobekan kertas yang tergeletak di
    rumput, bukan sebagai bunga. Dua hal yang salah, dan keduanya diperbaiki di
    sini: kuntumnya terlalu BESAR, dan ia sendirian.

    Bunga liar tumbuh bergerombol. Beberapa kuntum kecil di ketinggian yang
    berbeda-beda terbaca sebagai bunga pada ukuran berapa pun, karena yang
    dikenali mata adalah sebarannya, bukan bentuk satu kelopak.
    """
    tb, ta = _w(_TANGKAI[0]), _w(_TANGKAI[1])
    kel = _KELOPAK[int(r(53) * len(_KELOPAK)) % len(_KELOPAK)]
    wk = _w(kel)
    n = 3 + (1 if r(50) > 0.5 else 0)
    dasar = r(52) * math.tau
    for i in range(n):
        a = dasar + i * (math.tau / n) + (r(55 + i) - 0.5) * 0.7
        jr = (0.03 + r(41 + i) * 0.075)
        bx, bz = x + math.cos(a) * jr, z + math.sin(a) * jr
        t = 0.15 + r(51 + i) * 0.15
        _helai(acc, bx, y, bz, t, 0.028, a, t * 0.20, tb, ta)
        # Kuntum dimiringkan mengikuti tangkainya, bukan mendatar. Bidang datar
        # sempurna memantulkan cahaya seragam dan itulah yang membuatnya tampak
        # seperti kertas.
        kx = bx + math.cos(a) * t * 0.20
        kz = bz + math.sin(a) * t * 0.20
        rr = 0.022 + r(45 + i) * 0.014
        _bidang_datar(acc, kx, y + t, kz, rr, a * 1.9, wk)
        _helai(acc, kx, y + t - rr * 0.7, kz, rr * 1.7, rr * 1.5, a + 1.57, 0.0, wk, wk)


def kerikil(acc, x, y, z, r):
    """Batu kecil setengah tertanam."""
    cb, ca_ = _KERIKIL[int(r(61) * len(_KERIKIL)) % len(_KERIKIL)]
    s = 0.55 + r(62) * 0.55
    _kotak(acc, x, y + 0.030 * s, z, 0.085 * s, 0.038 * s, 0.072 * s,
           r(63) * math.tau, _w(cb), _w(ca_))


def ranting(acc, x, y, z, r):
    """Ranting rebah — satu-satunya benda mendatar di sebaran, dan itu gunanya:
    semua yang lain berdiri, jadi ranting memberi arah yang berbeda."""
    cb, ca_ = _RANTING[int(r(71) * len(_RANTING)) % len(_RANTING)]
    a = r(72) * math.tau
    p = 0.20 + r(73) * 0.18
    ca2, sa2 = math.cos(a), math.sin(a)
    _kotak(acc, x, y + 0.028, z, p, 0.026, 0.030, a, _w(cb), _w(ca_))
    if r(74) > 0.5:
        a2 = a + 0.9
        _kotak(acc, x + ca2 * p * 0.6, y + 0.026, z + sa2 * p * 0.6,
               p * 0.45, 0.020, 0.024, a2, _w(cb), _w(ca_))


# ─── Pemakaian dari World3D ─────────────────────────────────────────────────
def bangun_entity(acc, world):
    """Ubah Perakit jadi satu Entity di dunia, atau None kalau tidak ada isi.

    Entity-nya double_sided: helai rumput adalah bidang tanpa tebal, dan
    separuhnya menghadap menjauhi kamera pada sudut orbit mana pun.
    """
    if acc.kosong():
        return None
    from ursina import color
    from .world import _e
    e = _e(acc.mesh(), (0, 0, 0), (1, 1, 1), None, color.white,
           soft=False, double_sided=True)
    world._obj_ents.append(e)
    return e
