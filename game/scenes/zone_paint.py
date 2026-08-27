"""zone_paint.py — Memberi ZONA warnanya sendiri dengan satu entity.

## Masalah yang dipecahkan

`World3D._make_tile()` mewarnai hampir semua ubin luar ruang dengan papan catur
RUMPUT (`_cb()` → hijau 148,205,105 / 125,182,85). Untuk rumput itu benar. Untuk
ubin tanah `D` itu bencana: tekstur `sand_ground` (rata-rata 220,193,150) dikali
hijau menghasilkan hijau pucat, jadi **ladang tanah tidak bisa dibedakan dari
halaman rumput.** Diukur dari `_bench/shots/layout_farm_over.png`: petak ladang
16x8 terbaca persis seperti rumput di sebelahnya.

Itu mematikan prinsip terpenting `docs/TATA_LETAK.md`: P4 — ladang adalah
persegi terbesar di peta dan ia harus terbaca sebagai TANAH.

`game/world.py` dimiliki agen lain, jadi tint per-ubin tidak boleh diubah dari
sini. Yang bisa dilakukan dari sisi scene: **melapisi satu zona dengan satu
bidang datar** setelah ubin dibangun (`load_scene` memanggil `scene.builder()`
setelah `_build_tiles()`).

## Kenapa satu entity, bukan satu per ubin

Melapis per ubin akan menambah 120 entity hanya untuk ladang kebun — 12% dari
seluruh anggaran peta, untuk nol informasi baru. Sebagai gantinya lapisan ini
adalah SATU Mesh persegi dengan UV yang diulang, dan papan caturnya dibakar ke
dalam teksturnya (128x128 = 2x2 ubin). Hasilnya: petak catur tetap bisa
dihitung (READABILITY butir 1) dengan ongkos **1 entity per zona**.

## Kenapa tidak merusak apa pun di atasnya

Tinggi lapisan dipilih di bawah SEMUA hal lain yang menempel di tanah:

    0,200  permukaan ubin datar (D/SD/STR_T)   ← lapisan ini duduk tepat di atasnya
    0,206  LAPISAN ZONA
    0,224  permukaan slab jalan (P)
    0,240  permukaan tutup rumput (G)
    0,210  alas petak yang sudah dicangkul (soil)

Jadi jalan, rumput, dan petak cangkulan tetap menang secara visual, dan lapisan
ini hanya terlihat di ubin datar yang memang jadi sasarannya. Karena itu sebuah
zona boleh digambar sebagai persegi utuh tanpa perlu menghindari jalan setapak
yang membelahnya.
"""
from pathlib import Path

from game.config import TILE_SIZE, GROUND_H

TS = TILE_SIZE

# Tinggi lapisan zona. Lihat tabel di docstring — angka ini tidak boleh naik ke
# 0,224 atau jalan akan tertimbun, dan tidak boleh turun ke 0,200 atau ia akan
# ber-z-fight dengan permukaan ubin di bawahnya.
ZONE_Y = GROUND_H + 0.006

_ASSET_DIR = Path(__file__).resolve().parent.parent.parent / 'assets' / 'textures'
_TEX_CACHE: dict = {}


def _checker_texture(base_name, light, dark, parity):
    """Tekstur 2x2 ubin: tekstur dasar dikali dua warna berselang.

    `parity` = (x0 + y0) % 2 dari ubin pojok zona, supaya papan catur lapisan
    ini SEJAJAR dengan papan catur rumput di sekitarnya. Kalau tidak sejajar,
    tepi zona akan terlihat seperti kesalahan setengah ubin.
    """
    key = (base_name, light, dark, parity)
    if key in _TEX_CACHE:
        return _TEX_CACHE[key]

    from PIL import Image, ImageChops
    from ursina import Texture

    p = _ASSET_DIR / f'{base_name}.png'
    if not p.exists():
        return None
    base = Image.open(p).convert('RGB')
    n = base.size[0]

    def tinted(rgb):
        return ImageChops.multiply(base, Image.new('RGB', base.size, tuple(rgb)))

    a, b = tinted(light), tinted(dark)
    if parity:
        a, b = b, a

    # Susunan kuadran dalam ruang PIL (baris 0 = ATAS). Texture() membalik
    # gambar saat unggah, jadi baris BAWAH PIL yang jadi v=0 — yaitu ubin
    # (x0, y0). Paritas ubin (x0+i, y0+j) = (x0+y0+i+j) % 2, jadi diagonalnya
    # sewarna: kiri-bawah & kanan-atas dapat `a`, dua sisanya `b`.
    img = Image.new('RGB', (n * 2, n * 2))
    img.paste(a, (0, n))          # (i=0, j=0)
    img.paste(b, (n, n))          # (i=1, j=0)
    img.paste(b, (0, 0))          # (i=0, j=1)
    img.paste(a, (n, 0))          # (i=1, j=1)

    t = Texture(img)
    t.filtering = False           # ubin harus bertepi tajam supaya bisa dihitung
    _TEX_CACHE[key] = t
    return t


def paint_zone(world, x0, y0, x1, y1, base_name='sand_ground',
               light=(150, 122, 92), dark=(128, 102, 76), y=None):
    """Lapisi persegi ubin (x0,y0)–(x1,y1) inklusif dengan satu bidang.

    Mengembalikan Entity-nya (sudah didaftarkan ke `world._obj_ents` supaya
    ikut dibersihkan `_clear()` saat ganti scene).
    """
    from ursina import Mesh, Vec2, Vec3, color
    from game.world import _e

    tex = _checker_texture(base_name, light, dark, (x0 + y0) % 2)
    if tex is None:
        return None

    nx, ny = x1 - x0 + 1, y1 - y0 + 1
    wx0, wx1 = (x0 - 0.5) * TS, (x1 + 0.5) * TS
    wz0, wz1 = (y0 - 0.5) * TS, (y1 + 0.5) * TS
    yy = ZONE_Y if y is None else y

    # Mesh dibangun DI SINI, bukan diambil dari cache mana pun. Mesh Ursina
    # adalah NodePath Panda3D dan hanya boleh punya satu parent (BRIEF §8.1);
    # tiap panggilan paint_zone() membuat Mesh barunya sendiri.
    m = Mesh(
        vertices=[Vec3(wx0, yy, wz0), Vec3(wx1, yy, wz0),
                  Vec3(wx1, yy, wz1), Vec3(wx0, yy, wz1)],
        triangles=[(0, 1, 2), (0, 2, 3)],
        uvs=[Vec2(0, 0), Vec2(nx / 2.0, 0),
             Vec2(nx / 2.0, ny / 2.0), Vec2(0, ny / 2.0)],
        normals=[Vec3(0, 1, 0)] * 4,
        mode='triangle',
    )
    # Lewat _e(), bukan Entity() mentah: seluruh permukaan tanah lain di peta
    # memakai smooth_shader (apply_smooth). Entity tanpa shader itu diterangi
    # jalur bawaan Panda3D dan hasilnya PUTIH POLOS di tengah peta — terlihat
    # di `_bench/shots/layout_farm_over2.png`. Permukaan tanah harus disinari
    # dengan cara yang sama, kalau tidak ia tidak akan pernah menyatu.
    e = _e(m, (0, 0, 0), (1, 1, 1), None, color.white,
           soft=False, tex_obj=tex, double_sided=True)
    world._obj_ents.append(e)
    return e


def patch_tile(world, tx, ty, base_name='grass_tso', tint=None):
    """Tambal SATU ubin yang berada di luar zona apa pun.

    Kenapa perlu: `_make_tile()` memberi ubin penghalang (pohon, tunggul,
    lentera, peti) tekstur `default_tex` = **'grass'**, dan `grass.png` di repo
    ini rata-ratanya (44,14,46) — hampir hitam. Akibatnya tiap pohon berdiri di
    atas kotak hitam. Diukur dari `_bench/shots/layout_farm_over.png`.
    Ubin pagar tidak kena karena `_make_tile()` sudah punya cabang khusus yang
    memakai 'grass_tso'; yang lain tidak.

    Ini TAMBALAN, bukan perbaikan. Perbaikan sebenarnya satu baris di
    `game/world.py` (pakai 'grass_tso'/'sand_ground' sebagai default_tex luar
    ruang). Begitu itu dikerjakan pemilik world.py, seluruh fungsi ini boleh
    dihapus beserta pemanggilnya di props.py.
    """
    from ursina import color
    from game.world import _e, _cb

    if tint is None:
        tint = _cb(tx, ty)
    # Tinggi & skala disamakan PERSIS dengan tutup rumput tetangga di
    # world.py (cap_y = GROUND_H + 0.02, tebal 0.04, skala TS*1.005), supaya
    # tidak ada garis jahitan di antara tambalan dan rumput sekitarnya.
    e = _e('cube', (tx * TS, GROUND_H + 0.021, ty * TS),
           (TS * 1.005, 0.042, TS * 1.005), base_name, tint, soft=False)
    world._obj_ents.append(e)
    return e


class Zone:
    """Satu persegi ubin yang dicat ulang oleh SATU entity.

    Dipegang oleh `Scene.paint` dan dieksekusi `props.default_prop_builder()`.
    Palet default sengaja bukan cokelat pekat: READABILITY §4.1 menaruh tanah
    di kelas "ground" — ia harus MUNDUR (saturasi rendah, nilai di pita tanah)
    supaya tanaman, alat, dan karakter yang berdiri di atasnya tetap menonjol.
    """

    __slots__ = ('x0', 'y0', 'x1', 'y1', 'base', 'light', 'dark')

    def __init__(self, x0, y0, x1, y1, base='sand_ground',
                 light=(150, 122, 92), dark=(128, 102, 76)):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.base, self.light, self.dark = base, light, dark

    def covers(self, tx, ty):
        return self.x0 <= tx <= self.x1 and self.y0 <= ty <= self.y1


# Palet zona baku. Semua diambil dari satu keluarga tanah supaya peta tidak
# berubah jadi tambal sulam warna; yang membedakan zona adalah NILAI (terang
# gelap) dan tekstur dasarnya, bukan corak warna yang berbeda-beda.
TANAH_LADANG  = dict(base='sand_ground', light=(148, 120, 90),  dark=(126, 100, 74))
TANAH_HALAMAN = dict(base='sand_ground', light=(170, 150, 122), dark=(148, 128, 102))
JERAMI        = dict(base='straw',       light=(210, 195, 150), dark=(186, 170, 126))
PASIR_PANTAI  = dict(base='sand_ground', light=(232, 214, 176), dark=(212, 194, 156))
BATU_ALUN     = dict(base='rock_ground', light=(198, 194, 186), dark=(176, 172, 164))
