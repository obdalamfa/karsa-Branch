"""
wajah.py — Kepala chibi untuk avatar TSO: proporsinya dan wajahnya.

KENAPA MODUL INI ADA
====================
Tekstur kepala TSO adalah lukisan wajah dewasa 128x128 yang realistis: mata
kecil sebesar ~5% lebar tekstur, kerut, hidung berbayang, mulut berbibir penuh.
Pada jarak percakapan (kamera `--dist 5`) satu mata cuma memakan belasan piksel
layar, jadi yang sampai ke pemain bukan "wajah" melainkan noda gelap. Patokan
Story of Seasons: A Wonderful Life justru sebaliknya — mata besar gelap dengan
kilau, hidung nyaris tidak ada, mulut kecil, rahang lembut.

Perbedaannya BUKAN pada mesh. Kepala TSO sudah membulat. Yang membuatnya
terbaca dewasa adalah lukisannya. Jadi yang diganti lukisannya, bukan
geometrinya — dan karena diganti di tingkat tekstur, seluruh 218 kepala TSO
ikut berubah tanpa satu pun aset baru di `assets/`.

TATA LETAK UV KEPALA TSO
========================
Diukur dari empat keluarga mesh kepala yang berbeda (ross, baldfat, mercedes,
buzz) dengan menumpangkan kisi sepersepuluh pada teksturnya. Hasilnya nyaris
identik di keempatnya — kepala TSO dibuat dari satu template UV yang sama:

    mata kiri   x 0,437   mata kanan  x 0,576   (sumbu wajah x 0,506)
    tinggi mata y 0,51 - 0,545
    hidung      y 0,69
    mulut       y 0,78 - 0,85
    oval wajah  x 0,37 - 0,65   y 0,36 - 0,88

Karena itu satu tabel koordinat cukup untuk semua kepala; tidak perlu tabel
per-mesh, dan kepala TSO yang belum pernah kita lihat pun ikut benar.

Kulit TIDAK diseragamkan: warnanya diambil dari tekstur aslinya (dicuplik dari
pipi), jadi tiap warga desa tetap membawa rona kulitnya sendiri.

PROPORSI: DIUKUR DI PIKSEL, BUKAN DI TULANG
===========================================
Ronde 1 menskalakan kepala 1,95x dan MENGHITUNG dari `adult.skel` bahwa
hasilnya 4,12 kepala. Kritikus buta lalu MENGUKUR tangkapan layarnya dan
mendapat 5 kepala, dan memilih patokan. Angka tulang dan angka piksel memang
tidak akan pernah sama, dan alasannya ada tiga — semuanya sudah diukur ulang
di `_bench/shots/WAJAH.png` ronde 1 (kamera RESEP: dist 5, pitch 10):

  1. **"Kepala" di layar bukan mesh kepala.** Yang dilihat mata adalah oval
     KULIT: dari garis rambut di dahi (y=310 px) sampai ujung dagu (y=415 px),
     105 piksel. Mesh kepala TSO membentang jauh lebih tinggi dari itu — ubun-
     ubunnya tertutup rambut yang nilainya sama gelap dengan latar, jadi ia
     tidak ikut terbaca sebagai "kepala". Rumus tulang memakai tinggi MESH;
     kritikus memakai tinggi WAJAH. Selisihnya saja sudah 1,36x.
  2. **Sendi HEAD bukan dasar kepala.** Sendi ada di y=5,05 di ruang tulang,
     tapi dagu yang terlihat turun sampai 5,05-0,139s. Rumus ronde 1 memakai
     tinggi mesh 0,785s yang MASUK ke dalam leher dan bahu; bagian itu tidak
     pernah sampai ke layar.
  3. **Perspektif.** Pada dist 5 kepala lebih dekat ke kamera daripada kaki,
     jadi kepala terpotret sedikit lebih besar dari perbandingan ortografisnya.

Karena yang dinilai piksel, patokannya juga diukur di piksel — dengan definisi
yang sama, siluet kepala+rambut dari ubun-ubun ke dagu:

    `_bench/refs/character_midshot.jpg`, pemuda   kepala 180 px / sosok 535 px
                                                  = **2,97 kepala**
    `_bench/refs/character_midshot.jpg`, Takakura  kepala 160 px / sosok 412 px
                                                  = **2,58 kepala**
    `_bench/shots/WAJAH.png` ronde 1               kepala 143 px / sosok 510 px
                                                  = **3,57 kepala**
    (ukuran wajah-saja ronde 1: 105 px / 510 px    = 4,86 — angka kritikus)

Angkanya lalu DICARI dengan memotret dan mengukur ulang, bukan dengan rumus.
Skala kepala `s` masuk ke dua tempat sekaligus — geometri kepala dikali `s`,
dan skala akar dikali `SKALA_TINGGI = 5,696/(5,05+0,646 s)` supaya tinggi dunia
tidak berubah — jadi tinggi kepala DI LAYAR sebanding dengan

    f(s) = s / (5,05 + 0,646 s)

sementara tinggi sosok di layar tetap ~503 px berapa pun `s`. Dua tangkapan
layar yang benar-benar diukur mengunci konstantanya:

    s = 2,535  ->  kepala 166 px, wajah 115 px, sosok 508 px  (3,06 / 4,42)
    s = 2,90   ->  kepala 180 px, wajah 128 px, sosok 503 px  (2,79 / 3,93)

`SKALA_KEPALA` = **2,90**. Siluetnya 2,79 kepala — di antara Takakura (2,58)
dan pemuda (2,97) di patokan — dan ukuran wajah-saja 3,93 kepala, yaitu persis
"jadikan 4 kepala" yang diminta kritikus. Satu angka menutup dua ukuran.

Anggota badan TIDAK dipendekkan. Vertex TSO disimpan dalam ruang-tulang, jadi
memendekkan paha berarti mesh betis menembus mesh paha dan sambungannya robek.
Yang bisa diskalakan bersih hanya kepala, karena mesh kepala dan mesh rambut
adalah SATU-SATUNYA mesh yang seluruh vertexnya terikat ke tulang HEAD
(diperiksa: mesh badan mengikat 19 tulang dan HEAD bukan salah satunya). Karena
itu penskalaan dikunci pada nama tulang, bukan pada nama file .apr — kepala TSO
apa pun ikut benar tanpa daftar.

Skala akar avatar tetap dikali `SKALA_TINGGI` supaya tinggi DUNIA tidak
berubah: pintu, langit-langit, papan nama dan sudut kamera yang sudah disetel
tidak meleset. Rasio adalah besaran tanpa satuan, jadi ganti rugi ini tidak
mengubah 2,97 sedikit pun — yang ia ubah hanya berapa piksel yang jatuh ke
wajah, dan itu justru naik: 143 px jadi 172 px pada tinggi sosok yang sama.

VARIASI: GAYA YANG SERAGAM, ORANG YANG TIDAK
============================================
Ronde 1 memberi semua warga mata, alis dan mulut yang identik. Itu salah, dan
pemilik proyek menyebutnya langsung: "jangan lupakan variasinya". Patokannya
sendiri buktinya — di satu frame `character_closeup.png` ada Takakura beralis
raksasa, bermata sipit menukik, berkulit gelap, di samping pemuda bermata
hijau besar berkulit terang berambut merah. Yang seragam di sana adalah GAYA
(mata besar, hidung titik, mulut kecil), bukan orangnya.

`varian_wajah(kunci)` karena itu mengembalikan ciri yang dikunci pada nama
orang: ukuran mata, warna iris, tebal dan sudut alis, lebar dan lengkung
mulut, geseran warna kulit, warna rambut, dan sedikit variasi tinggi badan.
Deterministik lewat FNV-1a — BUKAN `hash()`, yang diacak per proses dan akan
membuat wajah warga berubah tiap kali game dibuka. Lihat `_bilang()` untuk
kenapa `sum(map(ord, ...))` yang dipakai `human_paint.py` tidak cukup di sini.

Variasi ini juga sampai ke jalur cadangan dan ke pemain: `varian_pemain()`
menyambungkan pilihan warna kulit dan rambut di layar buat-karakter ke wajah
chibi-nya, yang sebelum ini tidak berpengaruh sama sekali pada avatar TSO.
"""
from __future__ import annotations

import io
import logging
from typing import Tuple

import math

from ursina import Entity, Vec3, color

# Warna wajah voxel (kelas Wajah: kedip, mulut bicara). Disalin dari cabang
# livestock bersama kelasnya; impor dan konstanta ini tertinggal saat merge.
MATA_WARNA  = (46, 36, 42)
MULUT_WARNA = (168, 108, 100)
PIPI_WARNA  = (243, 176, 172)

# ─── PROPORSI CHIBI ─────────────────────────────────────────────────────────
TULANG_KEPALA   = 'HEAD'
# Lihat "PROPORSI: DIUKUR DI PIKSEL" di docstring — angkanya dicari dengan
# MENGUKUR tangkapan layar, bukan dengan rumus tulang.
SKALA_KEPALA    = 2.90

# Tiang leher pada mesh BADAN TSO menembus separuh bawah wajah, dan itu bukan
# akibat pembesaran kepala: difoto pada skala kepala 1,00 dengan tekstur kisi
# penanda (`_bench/shots/_wajah_dbg1.png`), gumpalan coklat yang sama menutupi
# ~60% kepala. Angkanya, diukur di ruang bind:
#
#     tiang leher (10 vertex, terikat NECK)  y 4,77 - 5,15   x +-0,15
#     mesh kepala                            y 4,86 - 5,65   x +-0,28
#     ujung dagu mesh kepala                 z depan hanya 0,063
#     tiang leher                            z depan       0,140
#
# Leher naik 0,29 unit ke dalam kepala DAN menonjol 0,08 lebih ke depan
# daripada ujung dagu, jadi ia menang di depth buffer tepat di tempat mulut
# seharusnya. Membesarkan kepala tidak menyembunyikannya: dagu ikut turun ke
# wilayah leher.
#
# Sepuluh vertex itu dikerutkan jadi tunggul 25% terhadap sendi NECK — tinggi
# 4,68-4,78, jari-jari 0,04 — sehingga ia hilang seluruhnya di dalam kepala.
# Tidak ada lubang yang terbuka: kerah baju (terikat SPINE2) mencapai y 4,77
# dan dasar kepala pada skala 2,90 turun sampai 4,65, jadi keduanya saling
# tembus. Ini juga yang benar untuk chibi — patokannya tidak punya leher.
SKALA_LEHER     = 0.25

SKALA_TULANG = {TULANG_KEPALA: SKALA_KEPALA, 'NECK': SKALA_LEHER}

# 5,696 / (5,05 + 0,646 * SKALA_KEPALA) — menjaga tinggi dunia tidak berubah
SKALA_TINGGI    = 5.696 / (5.05 + 0.646 * SKALA_KEPALA)


def skala_vertex(nama_tulang: str) -> float:
    """Faktor skala vertex terhadap titik asal tulangnya."""
    return SKALA_TULANG.get(nama_tulang, 1.0)


def apr_kepala(nama_apr: str) -> bool:
    """True kalau .apr ini KEPALA (mis. `mahd001_ross.apr`), bukan rambut/badan.

    Konvensi nama TSO: `<m|f><a><bd|hd|hl><nomor>_<nama>.apr` — `hd` kepala,
    `hl` rambut, `bd` badan. Rambut juga terikat ke tulang HEAD, jadi
    pembedanya harus nama file: melukis mata di atas tekstur RAMBUT akan
    menaruh sepasang mata di tengah gumpalan rambut.
    """
    n = (nama_apr or '').lower()
    return len(n) > 4 and n[2:4] == 'hd'


def apr_rambut(nama_apr: str) -> bool:
    """True kalau .apr ini mesh RAMBUT terpisah (`fahl003_longhair02.apr`).

    Ia tidak boleh dapat wajah, tapi ia HARUS ikut diganti warna: kalau tidak,
    warga yang rambutnya mesh terpisah tetap berambut sama semua sementara
    warga yang rambutnya menyatu di tekstur kepala sudah berubah warna.
    """
    n = (nama_apr or '').lower()
    return len(n) > 4 and n[2:4] == 'hl'


# ─── VARIASI PER-ORANG ──────────────────────────────────────────────────────
# Daftar ditulis tangan, bukan diacak dari ruang warna penuh: acak menghasilkan
# rambut ungu dan kulit hijau. Tiap baris warna yang sudah dipilih supaya tetap
# satu keluarga dengan patokan Story of Seasons — hangat, jenuh sedang, dan
# nilainya jelas terpisah dari kulit dan pakaian.
_RAMBUT = (
    (46, 34, 30),      # hitam kecoklatan
    (82, 50, 32),      # coklat tua
    (132, 84, 44),     # coklat madu
    (172, 132, 72),    # pirang gandum
    (140, 52, 40),     # merah bata (pemuda di patokan)
    (36, 34, 42),      # hitam kebiruan
    (108, 96, 92),     # abu — warga tua
)
_IRIS = (
    (74, 46, 28),      # coklat
    (44, 96, 62),      # hijau (pemuda di patokan)
    (48, 76, 116),     # biru kelabu
    (108, 78, 38),     # madu
    (34, 28, 32),      # nyaris hitam
    (126, 72, 44),     # tembaga
)
# Geseran kulit, BUKAN warna kulit: dasarnya tetap dicuplik dari tekstur kepala
# TSO orang itu sendiri, jadi ciri aslinya tidak hilang. Yang digeser cuma
# terang dan hangatnya.
_KULIT_GESER = (
    (0, 0, 0), (16, 8, -2), (-22, -18, -14), (10, -2, -12), (-10, 2, 8), (24, 14, 2),
)
_MATA_SKALA   = (0.84, 0.92, 1.00, 1.09, 1.18, 1.28)
_ALIS_TEBAL   = (0.55, 0.80, 1.00, 1.30, 1.80, 2.50)   # 2,50 = alis Takakura
_ALIS_SUDUT   = (-14, -7, 0, 6, 13)                    # negatif = menukik marah
_MULUT_LEBAR  = (0.026, 0.032, 0.038, 0.046)
_MULUT_SENYUM = (-1, 0, 1, 1)                          # -1 cemberut, 1 senyum
_TINGGI       = (0.90, 0.95, 1.00, 1.00, 1.06, 1.12)


def _bilang(kunci: str, garam: int = 0) -> int:
    """Angka stabil dari sebuah nama — FNV-1a 32-bit, bukan `hash()`.

    `hash()` Python diacak per proses, jadi wajah warga desa akan berubah tiap
    kali game dibuka dan tangkapan layar regresi ikut berubah tanpa ada yang
    diubah. `human_paint.py` memakai `sum(map(ord, ...))` untuk alasan yang
    sama, tapi di sini `sum` tidak cukup: nama-nama warga panjangnya mirip, jadi
    jumlahnya berdempetan dan tiap `n // p % len` yang dibagi angka besar
    menjatuhkan setengah desa ke laci yang sama. Diperiksa dengan `sum`: dari 13
    warga, 6 dapat warna rambut yang persis sama dan 7 dapat tinggi yang sama.
    FNV menyebar bit rendahnya, jadi `garam` yang berbeda benar-benar memberi
    undian yang berbeda.
    """
    h = 2166136261 ^ (garam * 16777619)
    for ch in (kunci or 'x'):
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def varian_wajah(kunci: str) -> dict:
    """Ciri wajah deterministik untuk satu orang.

    Tiap ciri diundi dengan `garam` sendiri, bukan dari satu angka yang dibagi-
    bagi. Kalau semua diambil dari satu undian, ciri-cirinya bergerak bersama:
    semua orang bermata besar juga beralis tebal juga berkulit terang, dan
    variasinya runtuh jadi satu sumbu saja.
    """
    def pilih(tabel, garam):
        return tabel[_bilang(kunci, garam) % len(tabel)]
    return {
        'id':            kunci or 'x',
        'mata_skala':    pilih(_MATA_SKALA, 1),
        'iris':          pilih(_IRIS, 2),
        'alis_tebal':    pilih(_ALIS_TEBAL, 3),
        'alis_sudut':    pilih(_ALIS_SUDUT, 4),
        'mulut_lebar':   pilih(_MULUT_LEBAR, 5),
        'mulut_senyum':  pilih(_MULUT_SENYUM, 6),
        'kulit_geser':   pilih(_KULIT_GESER, 7),
        'rambut':        pilih(_RAMBUT, 8),
        'tinggi':        pilih(_TINGGI, 9),
    }


# Rona kulit "netral" yang keluar dari `_cuplik_kulit() + campur krem 26%` pada
# kepala TSO laki-laki standar. Dipakai sebagai titik nol untuk menerjemahkan
# pilihan SKIN_PRESETS pemain jadi geseran — diukur, bukan ditebak: dicetak
# dari `mahd001_ross.apr` lewat `_cuplik_kulit()`.
_KULIT_NETRAL = (232, 196, 158)


def varian_pemain(indeks_kulit: int = 0, indeks_rambut: int = 0) -> dict:
    """Varian wajah pemain, disambungkan ke pilihan di layar buat-karakter.

    Pemain sudah memilih warna kulit dan rambut di `chargen.py`, tapi sebelum
    ini pilihan itu cuma sampai ke mesh voxel cadangan — pada avatar TSO ia
    tidak berpengaruh sama sekali. Sekarang keduanya masuk ke wajah chibi, jadi
    pemain benar-benar mendapat orang yang ia buat, dan tetap punya ciri lain
    (mata, alis, mulut) yang membedakannya dari warga desa.
    """
    v = varian_wajah('pemain')
    try:
        from .chargen import SKIN_PRESETS, HAIR_PRESETS
        if 0 <= indeks_rambut < len(HAIR_PRESETS):
            v['rambut'] = tuple(HAIR_PRESETS[indeks_rambut][1])
        if 0 <= indeks_kulit < len(SKIN_PRESETS):
            t = SKIN_PRESETS[indeks_kulit][1]
            v['kulit_geser'] = tuple(
                max(-70, min(70, t[i] - _KULIT_NETRAL[i])) for i in range(3))
    except Exception as e:
        logging.warning(f"wajah: varian pemain jatuh ke bawaan ({e})")
    # Kunci cache harus ikut berubah, kalau tidak pemain yang mengganti warna
    # rambut akan tetap mendapat tekstur kepala yang lama.
    v['id'] = f'pemain-{indeks_kulit}-{indeks_rambut}'
    return v


def tinggi_varian(kunci: str) -> float:
    """Pengali tinggi badan untuk satu orang (0,90 - 1,12).

    Dipisah dari `varian_wajah()` karena pemanggilnya (`entities.py`) cuma
    butuh satu angka dan tidak perlu memuat PIL untuk mendapatkannya.
    """
    return _TINGGI[_bilang(kunci, 9) % len(_TINGGI)]


# ─── KOORDINAT WAJAH (fraksi lebar/tinggi tekstur) ──────────────────────────
MATA_X_KIRI   = 0.437
MATA_X_KANAN  = 0.576
MATA_Y        = 0.528
MATA_RX       = 0.044      # setengah lebar bola mata pada varian 1,00
MATA_RY       = 0.059      # setengah tinggi bola mata pada varian 1,00
ALIS_Y        = 0.428
MULUT_Y       = 0.795
HIDUNG_Y      = 0.700
WAJAH_CX      = 0.506
WAJAH_CY      = 0.620
WAJAH_RX      = 0.150
WAJAH_RY      = 0.270

# Ukuran kanvas kerja. Tekstur TSO 128x128; dinaikkan supaya lengkung mata
# tidak jadi tangga piksel saat kepala diperbesar 2,5x di layar.
KANVAS = 512

_cache: dict = {}


def _cuplik_kulit(im, w: int, h: int) -> Tuple[int, int, int]:
    """Ambil warna kulit rata-rata dari dua petak pipi.

    Pipi dipilih karena ia satu-satunya bagian wajah yang bebas rambut, mata,
    dan bayangan hidung di keempat keluarga mesh. Diambil rata-rata dua sisi
    supaya pencahayaan miring pada lukisan aslinya saling meniadakan.
    """
    petak = []
    for fx in (0.415, 0.600):
        x0 = int((fx - 0.020) * w); x1 = int((fx + 0.020) * w)
        y0 = int(0.640 * h);        y1 = int(0.690 * h)
        for x in range(max(0, x0), min(w, x1)):
            for y in range(max(0, y0), min(h, y1)):
                petak.append(im.getpixel((x, y))[:3])
    if not petak:
        return (222, 178, 140)
    n = len(petak)
    return (sum(p[0] for p in petak) // n,
            sum(p[1] for p in petak) // n,
            sum(p[2] for p in petak) // n)


def _geser(c, d: int):
    """Geser satu warna lebih terang (d>0) atau lebih gelap (d<0), aman di 0-255."""
    return tuple(max(0, min(255, v + d)) for v in c)


def _geser_rgb(c, d):
    """Geser tiap kanal sendiri-sendiri (untuk `kulit_geser`)."""
    return tuple(max(0, min(255, c[i] + d[i])) for i in range(3))


def _campur(a, b, t: float):
    """Campur dua warna; t=0 -> a, t=1 -> b."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _warnai_rambut(img, warna, ambang_kulit=None, batas_y=None):
    """Cat ulang piksel GELAP sebuah tekstur ke `warna`, luminansinya dijaga.

    Kenapa lewat luminansi dan bukan mask bentuk: tata letak UV rambut berbeda
    di tiap keluarga mesh TSO, tapi rambut selalu jauh lebih gelap daripada
    kulit di tekstur yang SAMA. Ambangnya karena itu relatif terhadap kulit
    orang itu, bukan angka mutlak — kepala berkulit gelap tidak ikut tercat.

    Rasio luminansi aslinya dijaga, jadi helai terang dan bayangan yang sudah
    dilukis Maxis tetap ada; yang berubah cuma warnanya. Kalau dicat rata,
    rambut jadi topi karet.
    """
    try:
        import numpy as np
    except Exception:
        return img
    from PIL import Image
    arr = np.asarray(img.convert('RGB'), dtype=np.float32)
    lum = arr[:, :, 0] * 0.299 + arr[:, :, 1] * 0.587 + arr[:, :, 2] * 0.114
    if ambang_kulit is None:
        ambang_kulit = float(lum.mean())
    mask = lum < ambang_kulit * 0.58
    if batas_y is not None:
        # Di bawah garis ini tidak ada rambut pada tata letak UV kepala TSO —
        # yang gelap di sana adalah bayangan dagu, leher, dan tepi tekstur.
        # Tanpa batas ini seorang warga berambut merah bata mendapat gumpalan
        # merah menyala di bawah dagunya (terlihat jelas pada `jaka_ronda` dan
        # `joko` saat pertama dicoba).
        baris = np.arange(arr.shape[0])[:, None] / float(arr.shape[0])
        mask &= (baris < batas_y)
    frac = float(mask.mean())
    # Pengaman: kalau lebih dari 62% tekstur lolos ambang, yang gelap itu bukan
    # rambut melainkan seluruh kepalanya (tekstur yang memang dilukis gelap).
    # Mengecatnya akan menghapus wajahnya, jadi lebih baik tidak disentuh.
    if frac < 0.012 or frac > 0.62:
        return img
    l_rerata = max(float(lum[mask].mean()), 1.0)
    # Batas atas 1,35 dan bukan 1,85: pada rambut merah bata, helai yang paling
    # terang melewati 255 di kanal merah saja dan jadi bercak menyala.
    skala = np.clip(lum[mask] / l_rerata, 0.40, 1.35)[:, None]
    target = np.array(warna, dtype=np.float32)[None, :] * skala
    arr[mask] = np.clip(target * 0.82 + arr[mask] * 0.18, 0, 255)
    return Image.fromarray(arr.astype('uint8'), 'RGB')


def lukis_wajah_chibi(img, varian=None):
    """Kembalikan salinan PIL Image tekstur kepala dengan wajah chibi.

    Bentuk rambut, telinga dan leher pada tekstur asli DIPERTAHANKAN — hanya
    oval wajah yang dicat ulang dan rambutnya diganti warna. Itu yang menjaga
    tiap kepala tetap punya potongan rambut dan siluetnya sendiri.

    `varian` (lihat `varian_wajah()`) yang membuat dua warga tidak berwajah
    kembar: ukuran mata, warna iris, tebal dan sudut alis, lengkung mulut,
    rona kulit dan warna rambut semuanya diambil dari sana.
    """
    from PIL import Image, ImageDraw, ImageFilter

    v = varian or varian_wajah('')
    src = img.convert('RGB').resize((KANVAS, KANVAS), Image.LANCZOS)
    W = H = KANVAS

    # Warna kulit asli dipertahankan sebagai dasar, diangkat 26% ke arah krem
    # hangat, LALU digeser lagi per-orang. Pengangkatan bersama bukan untuk
    # menyeragamkan: beberapa kepala TSO dilukis sangat gelap dan pada jarak
    # percakapan wajah segelap itu melebur dengan rambut hitam jadi satu noda.
    # Geseran per-orang di atasnya yang mengembalikan perbedaannya — dan ia
    # ditambahkan SESUDAH, jadi jarak antar warga tidak ikut termampatkan.
    kulit_asli = _cuplik_kulit(src, W, H)
    kulit = _geser_rgb(_campur(kulit_asli, (255, 219, 178), 0.38), v['kulit_geser'])

    # ── 0. Rambut: warna per-orang, bayangan aslinya dijaga ──────────────────
    lum_kulit = kulit_asli[0] * 0.299 + kulit_asli[1] * 0.587 + kulit_asli[2] * 0.114
    src = _warnai_rambut(src, v['rambut'], ambang_kulit=lum_kulit, batas_y=0.80)

    hasil = src.copy()

    # ── 1. Ratakan oval wajah ────────────────────────────────────────────────
    # Lukisan aslinya penuh kerut, bayangan hidung dan lipatan mulut dewasa.
    # Semuanya dihapus dengan menimpa oval wajah memakai warna kulit datar,
    # lewat mask yang tepinya dikaburkan supaya sambungannya ke dahi dan leher
    # tidak berupa garis.
    kanvas_kulit = Image.new('RGB', (W, H), kulit)
    mask = Image.new('L', (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([(WAJAH_CX - WAJAH_RX) * W, (WAJAH_CY - WAJAH_RY) * H,
                (WAJAH_CX + WAJAH_RX) * W, (WAJAH_CY + WAJAH_RY) * H], fill=245)
    mask = mask.filter(ImageFilter.GaussianBlur(W * 0.045))
    hasil = Image.composite(kanvas_kulit, hasil, mask)

    # Bayangan halus di bawah pipi supaya wajah tidak jadi keping datar.
    bayang = Image.new('RGB', (W, H), _geser(kulit, -26))
    mb = Image.new('L', (W, H), 0)
    mbd = ImageDraw.Draw(mb)
    mbd.ellipse([(WAJAH_CX - WAJAH_RX * 0.98) * W, (WAJAH_CY + WAJAH_RY * 0.10) * H,
                 (WAJAH_CX + WAJAH_RX * 0.98) * W, (WAJAH_CY + WAJAH_RY * 1.02) * H],
                fill=70)
    mb = mb.filter(ImageFilter.GaussianBlur(W * 0.05))
    hasil = Image.composite(bayang, hasil, mb)

    d = ImageDraw.Draw(hasil, 'RGBA')

    # ── 2. Hidung: satu titik bayangan, bukan hidung berbentuk ───────────────
    hid = _geser(kulit, -30)
    d.ellipse([(WAJAH_CX - 0.022) * W, (HIDUNG_Y - 0.012) * H,
               (WAJAH_CX + 0.022) * W, (HIDUNG_Y + 0.014) * H],
              fill=hid + (150,))

    # ── 3. Rona pipi ─────────────────────────────────────────────────────────
    rona = _campur(kulit, (214, 118, 108), 0.45)
    for fx in (0.410, 0.605):
        d.ellipse([(fx - 0.040) * W, (0.660 - 0.028) * H,
                   (fx + 0.040) * W, (0.660 + 0.028) * H],
                  fill=rona + (68,))

    # ── 4. Mulut: garis lengkung kecil, tanpa bibir ──────────────────────────
    # Lengkungnya dibalik untuk yang cemberut. Di patokan, Takakura bermulut
    # turun di samping pemuda bermulut naik langsung terbaca sebagai dua watak
    # yang berbeda, dari jarak percakapan, tanpa satu kata pun.
    mulut = (96, 46, 46)
    lm = v['mulut_lebar']
    senyum = v['mulut_senyum']
    if senyum > 0:
        busur = (18, 162)
    elif senyum < 0:
        busur = (200, 340)
    else:
        busur = (0, 180)      # garis nyaris lurus
    d.arc([(WAJAH_CX - lm) * W, (MULUT_Y - 0.026) * H,
           (WAJAH_CX + lm) * W, (MULUT_Y + 0.026) * H],
          start=busur[0], end=busur[1], fill=mulut + (255,),
          width=max(3, int(W * 0.013)))

    # ── 5. Mata ──────────────────────────────────────────────────────────────
    # Bentuk patokan: bola besar, iris berwarna yang mengisi hampir seluruh
    # bola, pupil gelap, batas atas tebal (bulu mata), satu kilau putih besar
    # di kiri-atas dan satu kilau kecil di kanan-bawah.
    putih = (250, 248, 244)
    iris = tuple(v['iris'])
    # Pupil dulu `iris - 46`. Pada 512 piksel kanvas selisih itu terlihat; di
    # layar, tempat wajah cuma ~60 piksel, iris dan pupil melebur jadi SATU
    # tempelan warna datar — kritikus buta menyebutnya persis begitu: "dua
    # tempelan hijau-teal datar". Yang membuat mata terbaca sebagai mata dari
    # jarak percakapan adalah kontras gelap-terang di dalam bola matanya,
    # bukan gradasi halus di dalam satu rona.
    pupil = _campur(iris, (16, 12, 20), 0.78)
    ms = v['mata_skala']
    rx, ry = MATA_RX * ms, MATA_RY * ms
    for fx in (MATA_X_KIRI, MATA_X_KANAN):
        x0, y0 = (fx - rx) * W, (MATA_Y - ry) * H
        x1, y1 = (fx + rx) * W, (MATA_Y + ry) * H
        # sclera sedikit lebih besar dari iris, memberi tepi terang tipis
        d.ellipse([x0 - W * 0.006, y0 - H * 0.004, x1 + W * 0.006, y1 + H * 0.004],
                  fill=putih + (255,))
        d.ellipse([x0, y0, x1, y1], fill=iris + (255,))
        d.ellipse([(fx - rx * 0.62) * W, (MATA_Y - ry * 0.64) * H,
                   (fx + rx * 0.62) * W, (MATA_Y + ry * 0.64) * H],
                  fill=pupil + (255,))
        # kilau besar kiri-atas
        kx, ky = fx - rx * 0.38, MATA_Y - ry * 0.40
        kr = 0.014 * ms
        d.ellipse([(kx - kr) * W, (ky - kr * 1.15) * H,
                   (kx + kr) * W, (ky + kr * 1.15) * H], fill=putih + (255,))
        # kilau kecil kanan-bawah
        kx2, ky2 = fx + rx * 0.42, MATA_Y + ry * 0.34
        kr2 = 0.007 * ms
        d.ellipse([(kx2 - kr2) * W, (ky2 - kr2 * 1.15) * H,
                   (kx2 + kr2) * W, (ky2 + kr2 * 1.15) * H], fill=putih + (190,))
        # garis bulu mata di tepi atas
        d.arc([x0 - W * 0.006, y0 - H * 0.010, x1 + W * 0.006, y1 + H * 0.004],
              start=185, end=355, fill=(28, 22, 26, 255),
              width=max(2, int(W * 0.009 * ms)))

    # ── 6. Alis ──────────────────────────────────────────────────────────────
    # Tebalnya sampai 2,5x, dan sudutnya boleh menukik ke dalam. Ini ciri
    # tunggal yang paling banyak menceritakan watak pada patokan: alis Takakura
    # sendiri hampir sebesar matanya.
    # Dulu `campur(rambut, hitam, 0.30)`. Untuk warga berambut hitam itu berarti
    # alis hitam di atas dahi cokelat gelap: kritikus buta melaporkan "tanpa
    # alis" karena memang tidak ada yang bisa dilihat. Sekarang alis selalu
    # dibawa jauh ke gelap, jadi kontrasnya datang dari NILAI, bukan dari rona.
    alis = _campur(v['rambut'], (14, 10, 12), 0.62)
    tebal = v['alis_tebal']
    sud = v['alis_sudut']
    for sisi, fx in ((-1, MATA_X_KIRI), (1, MATA_X_KANAN)):
        miring = sisi * sud
        d.arc([(fx - 0.052) * W, (ALIS_Y - 0.030) * H,
               (fx + 0.052) * W, (ALIS_Y + 0.046) * H],
              start=200 + miring, end=340 + miring, fill=alis + (255,),
              width=max(4, int(W * 0.019 * tebal)))

    # ── 7. Lembutkan ─────────────────────────────────────────────────────────
    # "Lebih halus" pada patokan bukan cuma bentuk, tapi juga tidak adanya
    # detail 128px yang berkedip. Kabur tipis membuat lukisannya menyatu tanpa
    # menghapus mata — mata sudah jauh lebih besar dari radius kabur ini.
    hasil = hasil.filter(ImageFilter.GaussianBlur(W * 0.0035))
    return hasil


def tekstur_kepala_chibi(data: bytes, kunci=None, varian=None):
    """bytes JPEG kepala TSO -> PIL Image wajah chibi. None kalau gagal.

    Di-cache per `kunci` karena pengecatan memakai kanvas 512x512 dan tidak
    murah. `kunci` HARUS ikut membawa identitas varian: dua warga yang memakai
    .apr kepala yang sama tapi varian berbeda adalah dua tekstur berbeda, dan
    tanpa itu yang dibangun lebih dulu akan mewariskan wajahnya ke yang kedua.
    """
    if kunci is not None and kunci in _cache:
        return _cache[kunci]
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        out = lukis_wajah_chibi(img, varian)
    except Exception as e:
        logging.warning(f"wajah: gagal melukis wajah chibi ({e}); pakai tekstur asli.")
        out = None
    if kunci is not None:
        _cache[kunci] = out
    return out


def tekstur_rambut_chibi(data: bytes, kunci=None, varian=None):
    """bytes tekstur mesh RAMBUT terpisah -> PIL Image yang sudah diganti warna.

    Tidak ada wajah yang dilukis di sini — lihat `apr_rambut()`.
    """
    if kunci is not None and kunci in _cache:
        return _cache[kunci]
    out = None
    try:
        from PIL import Image
        v = varian or varian_wajah('')
        img = Image.open(io.BytesIO(data)).convert('RGB')
        img = img.resize((KANVAS, KANVAS), Image.LANCZOS)
        out = _warnai_rambut(img, v['rambut'])
    except Exception as e:
        logging.warning(f"wajah: gagal mewarnai rambut ({e}); pakai tekstur asli.")
        out = None
    if kunci is not None:
        _cache[kunci] = out
    return out


# ─── JALUR CADANGAN: humanoid.obj ───────────────────────────────────────────
# Warga desa di mesin TANPA instalasi TSO, dan mob yang tidak punya mesh
# sendiri (`tikus_gua`, `banaspati`, `kuntilanak`, `leak`), jatuh ke
# `assets/models/humanoid.obj`. Kalau hanya avatar TSO yang dibuat chibi, dua
# jalur itu akan menampilkan sosok berproporsi dewasa di samping sosok chibi —
# gaya yang pecah, persis yang diminta untuk TIDAK terjadi.
#
# Angka diambil dari `_PROFILE` di `tools/gen_humanoid_obj.py`, bukan ditebak:
#     neck_bot 2,28 | neck_top 2,36 | jaw 2,46 | crown 2,94 | apex 3,00
# Kepala = semua vertex di atas neck_top; pivotnya di neck_bot supaya dagu
# tidak melayang lepas dari lehernya.
Y_LEHER_HUMANOID  = 2.32     # tengah neck_bot..neck_top
TINGGI_HUMANOID   = 3.00
# 3,00/0,64 = 4,7 kepala; 1,32 membawanya ke ~3,5 — sepadan dengan avatar TSO
SKALA_KEPALA_OBJ  = 1.32


def chibikan_humanoid(np_) -> bool:
    """Besarkan kepala `humanoid.obj` di tempat; tinggi totalnya tetap 3,00.

    `np_` adalah NodePath hasil `load_model_file('humanoid')` — sudah salinan
    lepas per-actor, jadi mengubahnya tidak ikut mengubah actor lain
    (`modifyVertexData()` memicu copy-on-write Panda).

    Mengembalikan True kalau ada vertex yang benar-benar digeser.
    """
    try:
        from panda3d.core import GeomVertexReader, GeomVertexWriter
    except Exception:
        return False
    if np_ is None:
        return False
    puncak = Y_LEHER_HUMANOID + (TINGGI_HUMANOID - Y_LEHER_HUMANOID) * SKALA_KEPALA_OBJ
    # Ganti rugi tinggi, alasannya sama dengan SKALA_TINGGI di jalur TSO: yang
    # diminta proporsi, bukan warga desa yang tiba-tiba lebih jangkung.
    c = TINGGI_HUMANOID / puncak
    k = SKALA_KEPALA_OBJ
    digeser = 0
    try:
        for gn in np_.findAllMatches('**/+GeomNode'):
            node = gn.node()
            for i in range(node.getNumGeoms()):
                vdata = node.modifyGeom(i).modifyVertexData()
                # Dibaca HABIS dulu, baru ditulis. Membuka reader dan writer
                # pada kolom yang sama lalu memakainya berselang-seling
                # bergantung pada apakah keduanya memegang array yang sama
                # setelah copy-on-write Panda — perilaku yang tidak dijamin.
                r = GeomVertexReader(vdata, 'vertex')
                titik = []
                while not r.isAtEnd():
                    p = r.getData3()
                    titik.append((p[0], p[1], p[2]))
                w = GeomVertexWriter(vdata, 'vertex')
                for x, y, z in titik:
                    if y > Y_LEHER_HUMANOID:
                        y = Y_LEHER_HUMANOID + (y - Y_LEHER_HUMANOID) * k
                        x *= k
                        z *= k
                        digeser += 1
                    w.setData3(x * c, y * c, z * c)
    except Exception as e:
        logging.warning(f"wajah: chibikan_humanoid gagal ({e})")
        return False
    return digeser > 0


# ── Wajah & rambut dari KOTAK, digabung dari cabang livestock ──────────────
#
# Dua sesi membangun `game/wajah.py` secara terpisah dan keduanya benar untuk
# sasarannya masing-masing:
#
#   - Yang di ATAS melukis wajah di tingkat TEKSTUR untuk avatar TSO. Itu jalur
#     yang benar-benar dirender untuk pemain dan warga desa, dan kritikus buta
#     menyebut matanya "benar secara anatomi" — sklera, iris, pupil, kilau.
#   - Yang di BAWAH membangun wajah dan rambut dari KOTAK geometri, untuk
#     humanoid prosedural.
#
# Tidak satu pun nama fungsinya bertabrakan, dan `entities.py` serta `player.py`
# hasil merge ini memanggil KEDUANYA. Jadi keduanya tinggal.

def derau(n: int, benih: int) -> float:
    """Derau 0..1 yang deterministik tapi tidak berirama, diumpani NOMOR.

    Diambil ke sini karena dipakai dua tempat (kedipan wajah dan kedutan
    telinga ternak) dan karena cara memanggilnya yang salah sudah sekali
    meloloskan metronom: versi pertama `Wajah._acak_jeda` mengumpaninya dengan
    `self._t`, yang di-nol-kan TEPAT SEBELUM pemanggilan, jadi deraunya selalu
    dievaluasi di sin(0) = 0 dan jaraknya selalu sama. Umpannya harus sesuatu
    yang memang berubah tiap kali — nomor kejadian — dan tanda tangan fungsi
    ini memaksanya.
    """
    return abs((math.sin((n + benih) * 12.9898) * 43758.5453) % 1.0)


def _kotak(induk, pos, skala, warna):
    e = Entity(model='cube', position=Vec3(*pos), scale=skala,
               color=warna, parent=induk)
    from .smooth_shader import apply_smooth
    apply_smooth(e, has_texture=False)
    return e

def bangun_rambut(induk, hw: float, ht: float, warna, maju: float = 0.0):
    """Batok, poni, tuft sisi dan belakang kepala. Return daftar entity.

    `hw` setengah-lebar kepala, `ht` setengah-tinggi kepala, keduanya dalam
    satuan induk. `maju` menggeser seluruh rambut ke depan (dipakai saat
    kepala di bawahnya bukan kotak, melainkan bola yang lebih ramping).
    """
    out = []
    def r(pos, skala):
        out.append(_kotak(induk, pos, skala, warna))
    # Poni sengaja menonjol lebih maju daripada bidang muka supaya ia
    # MENGGANTUNG di atas dahi, bukan menempel rata seperti stiker.
    out_hw = hw * 1.06
    r((0.0,  ht * 0.67, -hw * 0.07 + maju), (out_hw * 2, ht * 0.85, out_hw * 2))
    r((0.0,  ht * 0.35,  hw * 0.86 + maju), (out_hw * 2, ht * 0.56, hw * 0.55))
    r((-hw * 1.03, ht * 0.04, -hw * 0.06 + maju), (hw * 0.28, ht * 1.33, hw * 1.97))
    r(( hw * 1.03, ht * 0.04, -hw * 0.06 + maju), (hw * 0.28, ht * 1.33, hw * 1.97))
    r((0.0, -ht * 0.09, -hw * 1.05 + maju), (hw * 1.94, ht * 1.47, hw * 0.29))
    return out

def bangun_wajah(induk, hw: float, ht: float, muka_z: float):
    """Mata, kilau, mulut dan rona pipi pada bidang muka.

    `muka_z` adalah jarak bidang muka dari pusat kepala, dalam satuan induk.
    Semua fitur ditempel sedikit di depannya supaya tidak berkedip melawan
    permukaan kepala (z-fighting).

    Pemain DAN NPC sama-sama berkepala kotak-membulat (`chibi_head_mesh`),
    jadi satu bidang muka datar cukup untuk keduanya. Varian bola sempat ada
    untuk kepala manekin NPC — lengkap dengan perhitungan kedalaman per fitur
    dari persamaan bola, karena di bidang datar rona pipi di x = 0,71R
    melayang lepas dari permukaan dan menjulur seperti dua batang merah muda.
    Varian itu dibuang begitu kepala NPC ikut memakai bentuk yang sama:
    bola Ursina bersegi rendah, dan cel-shader di sini memotong terang-gelap
    pada ambang keras, jadi batas bayangannya membentuk tangga yang terlihat
    di pipi dari jarak dekat.
    """
    out, mata, kilau, pipi = [], [], [], []
    from .meshes import permukaan

    def kedalaman(x, y, maju):
        """Kedalaman satu fitur, MENGIKUTI lengkung kepala.

        Versi pertama mengembalikan `muka_z + maju` — satu bidang datar untuk
        semua fitur. Itu benar selama kepala hampir kubus: pada eksponen 0,10
        permukaannya memang datar sempurna sampai ~0,8 setengah-lebar. Begitu
        bentuknya dibuat melengkung, bidang datar itu berbohong makin jauh ke
        arah sudut — terukur, pada eksponen 0,60 mulut melayang 11% dan rona
        pipi 8% setengah-lebar di depan muka.
        """
        return muka_z * permukaan(abs(x) / max(hw, 1e-6),
                                  abs(y) / max(ht, 1e-6)) + maju
    for sx in (-1, 1):
        x, y = sx * hw * 0.41, -ht * 0.26
        e = _kotak(induk, (x, y, kedalaman(x, y, 0.0)),
                   (hw * 0.34, ht * 0.28, hw * 0.08), color.rgb(*MATA_WARNA))
        mata.append(e); out.append(e)
        # Kilau di sudut yang SAMA pada kedua mata: satu arah cahaya.
        kx, ky = x - hw * 0.09, -ht * 0.19
        k = _kotak(induk, (kx, ky, kedalaman(kx, ky, hw * 0.046)),
                   (hw * 0.10, ht * 0.08, hw * 0.046), color.rgb(255, 255, 255))
        kilau.append(k); out.append(k)
    my = -ht * 0.71
    mulut = _kotak(induk, (0.0, my, kedalaman(0.0, my, 0.0)),
                   (hw * 0.22, ht * 0.07, hw * 0.069), color.rgb(*MULUT_WARNA))
    out.append(mulut)
    for sx in (-1, 1):
        # 0,60 bukan 0,71: pada kepala yang dibingkai rambut di kedua sisi,
        # 0,71 mendarat tepat di batas rambut dan separuh rona menggantung
        # keluar dari pipi.
        px, py = sx * hw * 0.60, -ht * 0.50
        e = _kotak(induk, (px, py, kedalaman(px, py, -hw * 0.023)),
                   (hw * 0.30, ht * 0.12, hw * 0.046),
                   color.rgb(*PIPI_WARNA))
        pipi.append(e); out.append(e)
    return Wajah(mata, kilau, mulut, out, pipi=pipi)


class Wajah:
    """Pengendali wajah: kedipan, dan mata lelah.

    Wajah yang TIDAK PERNAH BERKEDIP adalah salah satu tanda uncanny yang
    paling tua dan paling murah dihilangkan — dan ia tersisa persis setelah
    karakter di sini akhirnya punya mata. Mata dan kilau sudah entity
    terpisah sejak awal, jadi kedipan cuma soal menyekakan tingginya.

    Tiga hal yang membuat kedipan terbaca sebagai kedipan, bukan kedutan:

      * CEPAT. Mata manusia menutup-membuka dalam 100-150 ms. Kedipan yang
        lebih lambat terbaca sebagai mengantuk, bukan berkedip.
      * TIDAK BERIRAMA. Jarak antar-kedip diacak 2,4-5,8 detik. Kedipan
        berjarak tetap adalah metronom, dan metronom terbaca sebagai mesin —
        cacat yang sama persis dengan `irama_sd_ms = 0` pada animasi aksi.
      * KILAU IKUT HILANG. Kilau yang tetap melayang saat mata tertutup
        terbaca sebagai dua titik putih di atas kelopak.

    Fase awalnya diambil dari `sum(ord(id))`, BUKAN `hash()` — Python mengacak
    hash string tiap proses, dan jebakan itu sudah dua kali memakan proyek ini
    (entities.py:262, lalu fase anggukan NPC dan napas hewan). Tanpa fase
    per-karakter, semua orang di layar berkedip serempak seperti pasukan.
    """

    TUTUP_MS   = 60.0      # menutup
    TAHAN_MS   = 25.0      # tertutup penuh
    BUKA_MS    = 75.0      # membuka, sedikit lebih lambat daripada menutup
    JEDA_MIN   = 2.4
    JEDA_MAKS  = 5.8
    LELAH_BUKA = 0.55      # tinggi mata saat energi habis

    # Dua keadaan yang harus terbaca dari MATANYA, dan sengaja dibuat berbeda
    # ke dua arah supaya tidak bisa tertukar: sakit = kelopak berat DAN
    # kedipan yang melambat; senang = mata menyipit rapat dengan kedipan
    # normal. Kalau keduanya cuma "mata lebih pendek", pemain tidak bisa
    # membedakan hewan yang bahagia dari hewan yang mau roboh.
    SAKIT_BUKA  = 0.62
    SAKIT_JEDA  = 2.2      # pengali jarak antar-kedipan
    SENANG_BUKA = 0.38

    # ── kehangatan: seberapa dekat warga ini dengan pemain ──────────────
    # `npc_hearts` 0-10 sudah menggerakkan cabang dialog, hadiah dan gerbang
    # aksi — tapi wajah warga tidak pernah menunjukkannya. Warga yang baru
    # dikenal dan warga yang sudah 10 hati menatap pemain dengan rupa yang
    # sama persis. Tandanya sengaja dibuat HALUS: rona pipi melebar dan mata
    # melembut sedikit. Senyum lebar permanen terbaca sebagai topeng.
    HATI_PIPI   = 1.42     # lebar rona pipi pada 10 hati
    HATI_MATA   = 0.93     # mata melembut sedikit, bukan menyipit

    # ── mulut saat bicara ───────────────────────────────────────────────
    # Sebelum ini mulut tiap karakter TIDAK PERNAH bergerak — terukur, rentang
    # scale_y-nya 0,00000 sepanjang percakapan 20 detik. Salah satu dari tiga
    # animasi yang diminta brief ini bernama "berbicara", dan mulutnya diam.
    #
    # Yang dihindari: mulut yang membuka-menutup satu sinus. Bicara manusia
    # bukan getaran berperiode tetap — ia deret SUKU KATA yang panjangnya
    # berbeda-beda, dikelompokkan jadi frasa, dengan jeda di antaranya.
    # Sinus murni akan punya simpangan baku jarak nol, cacat metronom yang
    # sama yang sudah dua kali ditutup di proyek ini (kedipan §7, ekor §9).
    SUKU_MIN     = 0.115   # detik, suku kata tercepat
    SUKU_MAKS    = 0.235   # detik, suku kata terlambat  (~4-9 suku/detik)
    SUKU_BUKA    = 3.1     # kelipatan tinggi mulut diam saat terbuka penuh
    SUKU_LEBAR   = 1.18    # mulut ikut melebar sedikit, tidak cuma menganga
    FRASA_MIN    = 4       # suku kata per frasa
    FRASA_MAKS   = 9
    FRASA_JEDA_MIN = 0.22  # detik diam di antara frasa — tempat orang menarik
    FRASA_JEDA_MAKS = 0.58 # napas; tanpa ini bicaranya terbaca sebagai dengung
    MULUT_PULANG_MS = 90.0 # mulut kembali diam sesudah berhenti bicara

    def __init__(self, mata, kilau, mulut, semua, pipi=None):
        self.mata, self.kilau, self.mulut, self.semua = mata, kilau, mulut, semua
        self.pipi = list(pipi or [])
        self._pipi0 = []
        for e in self.pipi:
            try:
                self._pipi0.append((float(e.scale_x), float(e.scale_y)))
            except Exception:
                self._pipi0.append((1.0, 1.0))
        self._hati = 0.0
        self._tinggi0 = [float(e.scale_y) for e in mata]
        self._t = 0.0
        self._jeda = self.JEDA_MIN
        self._kedip_t = None
        self._lelah = 0.0
        self._tidur = False
        self._sakit = False
        self._senang = 0.0
        self._n = 0                 # nomor kedipan, umpan derau
        self._bicara = False
        self._suku_n = 0            # nomor suku kata, umpan derau
        self._suku_t = 0.0
        self._suku_lama = self.SUKU_MIN
        self._suku_tinggi = 1.0
        self._sisa_frasa = 0
        self._jeda_t = 0.0
        self._buka_mulut = 0.0      # 0 = diam, 1 = terbuka penuh
        self._mulut0 = None
        if mulut is not None:
            try:
                self._mulut0 = (float(mulut.scale_x), float(mulut.scale_y))
            except Exception:
                self._mulut0 = None

    def fase_awal(self, kunci: str) -> None:
        """Sebar fase dari id karakter supaya tidak berkedip serempak."""
        self._benih = sum(map(ord, kunci)) % 997
        u = self._benih / 997.0
        self._t = u * self.JEDA_MAKS
        self._acak_jeda()

    def _acak_jeda(self) -> None:
        """Jarak ke kedipan berikutnya: deterministik, tapi tidak berirama.

        Versi pertama memakai `sin(self._t * 12,9898)` — dan `self._t` di-nol-kan
        TEPAT SEBELUM fungsi ini dipanggil, jadi deraunya selalu dievaluasi di
        sin(0) = 0 dan jaraknya selalu JEDA_MIN. Terukur: 12 kedipan dalam 30
        detik, semuanya berjarak 2,40 detik, simpangan baku 0,00 — metronom,
        yaitu persis cacat yang tabel ambang proyek ini sendiri sebut mesin.
        Umpannya sekarang NOMOR kedipan, yang memang berubah tiap kali.
        """
        self._n += 1
        u = derau(self._n, getattr(self, '_benih', 0))
        self._jeda = self.JEDA_MIN + u * (self.JEDA_MAKS - self.JEDA_MIN)

    def set_lelah(self, lelah: float) -> None:
        """0 = segar, 1 = habis. Mata menyipit, tidak menutup."""
        self._lelah = max(0.0, min(1.0, float(lelah)))

    def set_bicara(self, aktif: bool) -> None:
        """Nyalakan/matikan mulut bicara.

        Di tepi naiknya frasa dimulai dari awal: tiap baris dialog baru adalah
        ucapan baru, dan ucapan yang dimulai di tengah frasa sebelumnya
        terbaca sebagai potongan.
        """
        aktif = bool(aktif)
        if aktif and not self._bicara:
            self._suku_t = 0.0
            self._jeda_t = 0.0
            self._sisa_frasa = 0
            self._suku_lama = self.SUKU_MIN
        self._bicara = aktif

    def _suku_berikut(self) -> None:
        """Panjang dan bukaan suku kata berikutnya — berbeda-beda, tidak acak.

        Umpannya NOMOR suku kata, bukan waktu: jebakan umpan-waktu sudah sekali
        meloloskan kedipan metronom di modul ini sendiri.
        """
        self._suku_n += 1
        b = getattr(self, '_benih', 0)
        u = derau(self._suku_n, b)
        self._suku_lama = self.SUKU_MIN + u * (self.SUKU_MAKS - self.SUKU_MIN)
        # Bukaan tiap suku kata berbeda: deret suku kata yang sama tingginya
        # terbaca sebagai rahang berengsel, bukan orang berbicara.
        self._suku_tinggi = 0.42 + derau(self._suku_n, b + 517) * 0.58
        self._suku_t = 0.0
        if self._sisa_frasa <= 0:
            n = derau(self._suku_n, b + 823)
            self._sisa_frasa = int(self.FRASA_MIN
                                   + n * (self.FRASA_MAKS - self.FRASA_MIN))
        self._sisa_frasa -= 1

    def _tick_mulut(self, dt: float) -> None:
        if self.mulut is None or self._mulut0 is None:
            return
        if not self._bicara:
            # Pulang ke diam, tidak memotong: mulut yang menutup dalam satu
            # frame di akhir kalimat terbaca sebagai gambar yang diganti.
            self._buka_mulut = max(
                0.0, self._buka_mulut - dt * 1000.0 / self.MULUT_PULANG_MS)
        elif self._jeda_t > 0.0:
            self._jeda_t = max(0.0, self._jeda_t - dt)
            self._buka_mulut = max(0.0, self._buka_mulut - dt * 6.0)
        else:
            self._suku_t += dt
            if self._suku_t >= self._suku_lama:
                if self._sisa_frasa <= 0:
                    j = derau(self._suku_n, getattr(self, '_benih', 0) + 311)
                    self._jeda_t = (self.FRASA_JEDA_MIN
                                    + j * (self.FRASA_JEDA_MAKS
                                           - self.FRASA_JEDA_MIN))
                self._suku_berikut()
            v = self._suku_t / max(1e-6, self._suku_lama)
            # Kosinus terangkat: tertutup -> terbuka -> tertutup tanpa sudut
            # tajam di kedua ujungnya.
            self._buka_mulut = self._suku_tinggi * (
                0.5 - 0.5 * math.cos(math.tau * v))
        x0, y0 = self._mulut0
        b = self._buka_mulut
        try:
            self.mulut.scale_y = y0 * (1.0 + (self.SUKU_BUKA - 1.0) * b)
            self.mulut.scale_x = x0 * (1.0 + (self.SUKU_LEBAR - 1.0) * b)
        except Exception:
            pass

    def set_hati(self, tingkat: float) -> None:
        """0 = baru kenal, 1 = 10 hati. Kehangatan, bukan kegembiraan."""
        self._hati = max(0.0, min(1.0, float(tingkat)))

    def _tick_pipi(self) -> None:
        if not self.pipi:
            return
        k = 1.0 + (self.HATI_PIPI - 1.0) * self._hati
        for e, (x0, y0) in zip(self.pipi, self._pipi0):
            try:
                e.scale_x = x0 * k
                e.scale_y = y0 * (1.0 + (k - 1.0) * 0.55)
            except Exception:
                pass

    def set_keadaan(self, sakit: bool = False, senang: float = 0.0) -> None:
        """Keadaan yang terbaca dari mata. `senang` 0..1 dan meluruh sendiri."""
        self._sakit = bool(sakit)
        self._senang = max(0.0, min(1.0, float(senang)))

    def set_tidur(self, tidur: bool) -> None:
        """Mata terpejam penuh selama yang punya sedang tidur.

        Dipakai hewan ternak, yang memang tidur di kandang tiap malam dan
        sebelum ini tetap membelalak sepanjang malam. Beda dari `set_lelah`:
        lelah MENYIPIT (0,55 terbuka), tidur MENUTUP.
        """
        self._tidur = bool(tidur)

    def tick(self, dt: float) -> None:
        self._tick_pipi()
        self._tick_mulut(dt)
        self._t += dt
        if self._kedip_t is None:
            # Hewan sakit berkedip lebih jarang — kelopak yang berat bergerak
            # lebih malas, dan itu tanda kedua yang memisahkannya dari senang.
            jeda = self._jeda * (self.SAKIT_JEDA if self._sakit else 1.0)
            if self._t >= jeda:
                self._kedip_t = 0.0
                self._t = 0.0
                self._acak_jeda()
        else:
            self._kedip_t += dt
            ms = self._kedip_t * 1000.0
            total = self.TUTUP_MS + self.TAHAN_MS + self.BUKA_MS
            if ms >= total:
                self._kedip_t = None
        # Bagian mata yang terbuka: 1 = penuh, 0 = tertutup.
        buka = 1.0
        if self._kedip_t is not None:
            ms = self._kedip_t * 1000.0
            if ms < self.TUTUP_MS:
                buka = 1.0 - ms / self.TUTUP_MS
            elif ms < self.TUTUP_MS + self.TAHAN_MS:
                buka = 0.0
            else:
                buka = (ms - self.TUTUP_MS - self.TAHAN_MS) / self.BUKA_MS
        buka *= 1.0 - (1.0 - self.LELAH_BUKA) * self._lelah
        if getattr(self, '_sakit', False):
            buka *= self.SAKIT_BUKA
        elif getattr(self, '_senang', 0.0) > 0.0:
            buka *= 1.0 - (1.0 - self.SENANG_BUKA) * self._senang
        else:
            buka *= 1.0 - (1.0 - self.HATI_MATA) * getattr(self, '_hati', 0.0)
        if getattr(self, '_tidur', False):
            buka = 0.0
        for e, h0 in zip(self.mata, self._tinggi0):
            try:
                e.scale_y = max(0.02, h0 * buka)
            except Exception:
                pass
        for k in self.kilau:
            try:
                k.enabled = buka > 0.45
            except Exception:
                pass

def warna_rambut(state, indeks_default: int = 0):
    from .chargen import HAIR_PRESETS
    i = getattr(state, 'char_hair', indeks_default) or indeks_default
    rgb = HAIR_PRESETS[i][1] if i < len(HAIR_PRESETS) else HAIR_PRESETS[0][1]
    return color.rgb(*rgb)
