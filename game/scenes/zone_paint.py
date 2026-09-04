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
# Naik dari 0,006 ke 0,016. Tabel di docstring di atas menyebut permukaan slab
# jalan ada di 0,224 — itu SUDAH TIDAK BENAR: world.py sekarang menggambar
# ubin `P` sebagai satu kubus setinggi GROUND_H saja, slab jalannya dicabut
# bersama tileset aspal FreeSO. Yang tersisa di atas lapisan ini cuma tutup
# rumput (0,240) dan alas petak cangkulan (dasar 0,210, puncak 0,310).
#
# Jarak 6 mm terlalu tipis untuk buffer kedalaman pada jarak pandang peta ini:
# di `_bench/shots/HUD.png` lantai kandang tampil sebagai pita bergaris karena
# lapisan zona dan ubin di bawahnya bergantian menang piksel per piksel.
ZONE_Y = GROUND_H + 0.016

_ASSET_DIR = Path(__file__).resolve().parent.parent.parent / 'assets' / 'textures'
_TEX_CACHE: dict = {}


# Berapa banyak ubin yang boleh dibakar ke dalam SATU tekstur zona sebelum ia
# diulang. 16 ubin = 1024 px pada tekstur dasar 64 px: cukup untuk memuat
# seluruh ladang kebun (16x8) tanpa pengulangan sama sekali, dan cukup besar
# supaya zona yang lebih besar dari itu pun tidak terbaca berulang.
_MAKS_UBIN = 16


def _petak_texture(base_name, light, dark, x0, y0, nx, ny):
    """Tekstur zona: satu petak per UBIN, warnanya dari noise, bukan paritas.

    Yang lama 2x2 ubin dengan dua warna berselang — papan catur berperiode DUA,
    pola paling teratur yang bisa dibuat, dan persis yang dilarang cek
    `rumput_catur` untuk rumput. Di ladang kebun 16x8 hasilnya satu bidang
    kuning-cokelat dengan kisi teratur di atasnya: dari jarak main ia terbaca
    sebagai satu warna datar, karena dua nilai yang berselang rapat saling
    meniadakan di mata.

    Sekarang tiap ubin mengambil nilainya dari `world.tint_mix()` — fungsi yang
    sama yang dipakai rumput, dievaluasi di KOORDINAT UBIN SEBENARNYA — plus
    sumbu kelembapan dari `world.kekeringan()`. Petaknya tetap bisa dihitung
    satu per satu (itu syaratnya, pemain mencangkul per ubin), tapi tidak ada
    lagi periode pendek untuk dikunci mata.

    Sebuah petak selang-seling tipis ±3% tetap dipertahankan di atas noise:
    itu yang menjaga garis batas antar ubin tetap terbaca saat noise kebetulan
    memberi dua tetangga nilai yang sama.
    """
    key = (base_name, light, dark, x0, y0, nx, ny)
    if key in _TEX_CACHE:
        return _TEX_CACHE[key]

    from PIL import Image, ImageChops
    from ursina import Texture
    from game.world import tint_mix, kekeringan

    p = _ASSET_DIR / f'{base_name}.png'
    if not p.exists():
        return None
    base = Image.open(p).convert('RGB')
    n = base.size[0]

    ux = min(nx, _MAKS_UBIN)
    uy = min(ny, _MAKS_UBIN)
    img = Image.new('RGB', (n * ux, n * uy))

    # Warna "kering" satu langkah lebih pucat dan lebih kuning dari `light`.
    kering = tuple(min(255, int(light[i] * (1.10 if i < 2 else 0.92)))
                   for i in range(3))

    for j in range(uy):
        for i in range(ux):
            tx, ty = x0 + i, y0 + j
            t = tint_mix(tx, ty)
            ker = kekeringan(tx, ty)
            rgb = []
            for c in range(3):
                v = dark[c] + (light[c] - dark[c]) * t
                if ker > 0.0:
                    v += (kering[c] - v) * min(1.0, ker * 0.55)
                # Selang-seling tipis: cukup untuk memberi tepi, tidak cukup
                # untuk menjadi pola.
                v *= 1.03 if (tx + ty) % 2 else 0.97
                rgb.append(max(0, min(255, int(round(v)))))
            # Tekstur dasar DIPUTAR/DICERMIN per ubin sebelum diwarnai.
            #
            # Tanpa ini tiap ubin memasang susunan batu yang IDENTIK, dan
            # warnanya boleh se-acak apa pun — mata tetap mengunci pengulangan
            # berperiode SATU UBIN dari bentuknya. Itu persis yang membuat
            # patokan Story of Seasons KALAH melawan kita di potongan TANAH;
            # kritikus buta di sana menulis "sekitar 5x3 kotak tanah identik
            # dengan parit gelap di antaranya, periode persis 1 ubin, dan tidak
            # ada satu pun kotak yang berbeda rona ATAU ARAH TEKSTURNYA — itu
            # kisi, bukan tanah." Kita menang justru karena permukaan kita
            # menerus; alun-alun batu yang baru mengulangi kesalahan itu.
            #
            # Delapan transformasi dihedral dipilih dari hash koordinat ubin,
            # jadi dua ubin bersebelahan hampir tidak pernah sama arahnya. Untuk
            # batu dan tanah yang tidak punya arah alami ini gratis: tidak ada
            # entity baru, tidak ada tekstur baru, dan hasilnya di-cache sama
            # seperti sebelumnya.
            d = (tx * 73856093 ^ ty * 19349663) & 7
            sisi = base
            if d & 3:
                sisi = sisi.rotate(90 * (d & 3))
            if d & 4:
                sisi = sisi.transpose(Image.FLIP_LEFT_RIGHT)
            ubin = ImageChops.multiply(sisi, Image.new('RGB', base.size, tuple(rgb)))
            # Baris 0 PIL = atas, dan Texture() membalik gambar saat unggah,
            # jadi ubin (x0+i, y0+j) harus dipasang di baris (uy-1-j).
            img.paste(ubin, (i * n, (uy - 1 - j) * n))

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

    nx, ny = x1 - x0 + 1, y1 - y0 + 1
    tex = _petak_texture(base_name, light, dark, x0, y0, nx, ny)
    if tex is None:
        return None
    ux, uy = min(nx, _MAKS_UBIN), min(ny, _MAKS_UBIN)
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
        uvs=[Vec2(0, 0), Vec2(nx / float(ux), 0),
             Vec2(nx / float(ux), ny / float(uy)), Vec2(0, ny / float(uy))],
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


def patch_tile(world, tx, ty, base_name=None, tint=None):
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
    from game.world import _e, _cb, TEX_RUMPUT

    if base_name is None:
        base_name = TEX_RUMPUT
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
# Jarak light-dark SENGAJA dilebarkan (dulu cuma ~15% dan itu tidak cukup).
# Sebuah zona diwarnai per ubin dari noise; kalau kedua ujung skalanya
# berdekatan, noise-nya tidak menghasilkan apa-apa dan zona kembali jadi satu
# bidang datar — persis keluhan yang sedang dikerjakan. Sekarang ~1,6x, kira-
# kira sebesar sebaran nilai tanah ladang di `_bench/refs/farm_closeup.jpg`.
TANAH_LADANG  = dict(base='tanah_garap', light=(232, 220, 204), dark=(140, 130, 120))
TANAH_HALAMAN = dict(base='tanah_garap', light=(248, 240, 228), dark=(172, 162, 150))
JERAMI        = dict(base='jerami_lantai', light=(238, 232, 218), dark=(158, 152, 142))
PASIR_PANTAI  = dict(base='sand_ground', light=(246, 230, 198), dark=(192, 176, 148))
BATU_ALUN     = dict(base='rock_ground', light=(214, 210, 202), dark=(158, 154, 146))
