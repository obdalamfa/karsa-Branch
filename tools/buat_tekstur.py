#!/usr/bin/env python3
"""buat_tekstur.py — Bangun ulang tiga tekstur yang isinya tekstur DEBUG.

Dipindai dari 73 tekstur di assets/textures, EMPAT di antaranya bukan gambar
bahan sama sekali melainkan pola uji yang tidak pernah diganti:

    tekstur      rata-rata RGB        isinya
    tree_trunk   (  7,5  71,2  37,5)  hitam bergaris HIJAU NEON tegak
    tree_leaf    ( 15,7  23,0  38,7)  hitam dengan wajik CYAN dan MAGENTA
    dirt         ( 46,2  42,3  60,7)  hitam dengan garis cyan/magenta/putih acak
    grass        ( 44,1  13,6  46,2)  hitam dengan KISI MAGENTA

Empat tekstur kayu lain di proyek ini semuanya coklat wajar — boat_wood
(183,136,86), chest_wood (140,96,56), floor_wood (155,109,69), wood_plank
(130,90,56) — jadi ketiganya memang ganjil, bukan gaya.

Akibatnya terlihat di setiap frame: batang pohon dikalikan tint coklat
rgb(100,70,40) menghasilkan ~(3,20,6), yaitu HITAM kehijauan. Dan kontras
hitam-pekat lawan rumput terang itulah yang memicu aberasi kromatik di
post-process, sehingga di layar muncul garis magenta dan cyan di sekitar
pangkal tiap pohon — yang mudah disalahartikan sebagai "tekstur hilang".

Dibuat lewat skrip, bukan digambar tangan, karena tiga alasan: hasilnya bisa
dibangun ulang persis, alasan tiap angka bisa ditulis di sebelahnya, dan
kecerahannya bisa dipilih dari perhitungan — tiap tekstur di sini DIKALIKAN
tint entitasnya, jadi tekstur yang terlalu gelap akan hilang berapa pun
cahayanya.

Jalankan: python tools/buat_tekstur.py
"""
import math
import sys
from pathlib import Path

from PIL import Image

AKAR = Path(__file__).resolve().parent.parent
TUJUAN = AKAR / 'assets' / 'textures'
N = 64


def _derau(x, y, benih):
    """Derau deterministik 0..1. Bukan random(): hasil skrip ini harus sama
    persis tiap kali dijalankan, supaya perubahan tekstur terbaca di diff."""
    v = math.sin((x * 12.9898 + y * 78.233 + benih * 37.719)) * 43758.5453
    return abs(v % 1.0)


def _campur(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def kulit_kayu():
    """Batang: alur tegak, coklat.

    Rata-rata dibidik ~(176,136,99) — jauh lebih terang daripada coklat batang
    yang diinginkan, KARENA ia dikalikan tint. build_tree memakai tint
    rgb(100,70,40), jadi hasil layarnya ~(69,37,15) sebelum cahaya; build_palm
    memakai (160,120,80) dan keluar lebih pucat, seperti batang kelapa.
    """
    im = Image.new('RGB', (N, N))
    px = im.load()
    gelap, terang = (past := (120, 86, 58)), (206, 168, 128)
    for x in range(N):
        # Alur tegak: beberapa pita lebar, bukan garis satu piksel — garis
        # setipis itu berkedip (aliasing) begitu pohonnya menjauh.
        alur = 0.5 + 0.5 * math.sin(x * math.tau / 11.0 + math.sin(x * 0.31) * 1.4)
        for y in range(N):
            t = alur * 0.78 + _derau(x, y, 3) * 0.22
            c = _campur(gelap, terang, t)
            # Simpul kayu sesekali, supaya tidak terbaca sebagai kain bergaris.
            if _derau(x // 7, y // 9, 11) > 0.93:
                c = _campur(c, gelap, 0.55)
            px[x, y] = c
    return im


def daun():
    """Tajuk: bintik daun bertumpuk, hijau.

    Dibuat BURAM penuh. Versi debug-nya 85% tembus pandang, dan `_e()` di
    world.py sengaja tidak menyalakan transparansi otomatis — jadi alpha itu
    tidak pernah dipakai dan yang tampil justru wajik cyan-magenta buram.
    """
    im = Image.new('RGB', (N, N))
    px = im.load()
    gelap, terang = (86, 118, 62), (168, 198, 118)
    for x in range(N):
        for y in range(N):
            # Dua lapis bintik berbeda ukuran: satu lapis saja terbaca
            # sebagai kain bertitik, bukan sebagai dedaunan.
            a = _derau(x // 3, y // 3, 5)
            b = _derau(x // 6, y // 5, 17)
            t = a * 0.55 + b * 0.45
            px[x, y] = _campur(gelap, terang, t)
    return im


def tanah():
    """Tanah: butiran coklat, sedikit berkerikil."""
    im = Image.new('RGB', (N, N))
    px = im.load()
    gelap, terang = (108, 82, 58), (178, 148, 112)
    for x in range(N):
        for y in range(N):
            t = _derau(x, y, 7) * 0.6 + _derau(x // 4, y // 4, 23) * 0.4
            c = _campur(gelap, terang, t)
            if _derau(x // 2, y // 2, 31) > 0.965:      # kerikil
                c = _campur(c, (198, 186, 170), 0.6)
            px[x, y] = c
    return im


def rumput():
    """Rumput: helai pendek, hijau.

    grass.png versi debug adalah HITAM BERGARIS MAGENTA, rata-rata (44,14,46).
    Sesudah `world.py` berhenti memakainya sebagai `default_tex` luar ruang ia
    memang tidak dipanggil siapa pun lagi — tapi berkas bernama grass.png yang
    isinya kisi magenta adalah ranjau yang menunggu pemakai berikutnya.
    """
    im = Image.new('RGB', (N, N))
    px = im.load()
    gelap, terang = (74, 116, 48), (146, 186, 88)
    for x in range(N):
        for y in range(N):
            # Helai tegak pendek: derau yang dipanjangkan di sumbu y.
            t = _derau(x, y // 3, 13) * 0.62 + _derau(x // 5, y // 7, 29) * 0.38
            px[x, y] = _campur(gelap, terang, t)
    return im


BUATAN = {
    'tree_trunk': kulit_kayu,
    'tree_leaf':  daun,
    'dirt':       tanah,
    'grass':      rumput,
}


def main():
    import numpy as np
    TUJUAN.mkdir(parents=True, exist_ok=True)
    print('%-12s %-22s %s' % ('tekstur', 'rata-rata RGB baru', 'lama'))
    for nama, fn in BUATAN.items():
        f = TUJUAN / (nama + '.png')
        lama = '-'
        if f.exists():
            a = np.array(Image.open(f).convert('RGB')).astype(int).reshape(-1, 3)
            lama = str(a.mean(axis=0).round(1))
        im = fn().convert('RGBA')
        # RGBA, bukan RGB. Seluruh tekstur lain di assets/textures bermode
        # RGBA, dan versi pertama skrip ini menyimpan RGB — akibatnya batang
        # pohon HILANG SAMA SEKALI dari layar (terukur: kolom hitam ada dengan
        # tekstur lama, tidak ada dengan yang baru, pada frame yang sama persis).
        im.save(f)
        b = np.array(im.convert("RGB")).astype(int).reshape(-1, 3)
        print('%-12s %-22s %s' % (nama, str(b.mean(axis=0).round(1)), lama))
    return 0


if __name__ == '__main__':
    sys.exit(main())
