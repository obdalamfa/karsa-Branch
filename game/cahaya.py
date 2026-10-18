"""cahaya.py — Satu sumber kebenaran untuk cahaya siang-malam.

Dulu tabel warnanya ada DUA: target lerp di `Game3D.update()` dan nilai snap di
`Game3D._init_env()` (dipanggil saat boot dan tiap ganti scene). Isinya sudah
berbeda: `_init_env` masih memakai angka sebelum pengali diturunkan ke batas
1,0 (siang sun 255,248,215 + ambient 95,90,78 = 1,33 di kanal merah), sedangkan
update menuju 185,180,156 + 70,66,57 = 1,00.

Terukur di jalur asli (ganti farm -> town jam 10, mesin sesi ~100 ms/frame,
_bench/probes/probe_lonjakan_scene.py): frame yang dirender tepat sesudah
scene dimuat membawa sun+amb merah 1,33 (p50 dunia 93,8 lawan 74,4 setelah
tenang), lalu lerp dengan dt pemuatan scene (>1 detik) MELEWATI target ke
0,91 (p50 68,8) dan merangkak naik lagi ke 1,00 selama ~30 frame. Seberapa
jauh ia melonjak dan terjun bergantung pada dt, jadi warna tangkapan
bergantung pada kecepatan mesin.

Sekarang keduanya membaca `target_cahaya()` di sini, dan arah matahari yang
dipakai fragmen (`sm_sun_dir`) dibaca dari node `DirectionalLight` itu sendiri,
bukan konstanta terpisah yang bisa berbeda dari arah lampu.
"""
from __future__ import annotations

from ursina import Vec3, Vec4


def _w(r, g, b, a=255):
    # Sama dengan `color.rgb` yang ditimpa app.py (skala 0-255 -> Vec4 0-1).
    # Ditulis ulang di sini supaya modul ini tidak bergantung pada urutan impor.
    return Vec4(r / 255.0, g / 255.0, b / 255.0, a / 255.0)


def target_cahaya(hour: float, indoor: bool, hujan: bool):
    """Warna target (sun, ambient, langit, awan) untuk jam dan keadaan ini.

    Satu-satunya tabel. `update()` me-lerp ke sini, `_init_env()` menyalinnya
    langsung -- jadi tidak ada lagi frame pertama yang memakai angka lain.
    """
    if indoor:
        # Indoor: lampu hangat yang cukup terang (cave/rumah tidak gelap total)
        return (_w(60, 55, 45), _w(190, 180, 200), _w(20, 15, 25), _w(0, 0, 0, 0))
    # ambient + sun <= 100% supaya warna tidak overflow jadi putih.
    # ambient max 70, sun max 185 (70/255 + 185/255 = 1,00; di
    # floor dot~0.82 jadi ~87%).
    #
    # Batas itu SUDAH tertulis di app.py sejak lama, dan nilainya dulu
    # melanggarnya: siang memakai sun 255 dan ambient 95, jumlahnya 1,373.
    # Akibatnya terukur -- apa pun di atas 186 dari 255 pasti terpotong jadi
    # putih. Kulit bawaan "Cerah" (255,225,180) jadi bidang putih rata tanpa
    # satu pun detail wajah tersisa, dan dinding rumah krem (248,235,200) ikut.
    #
    # HANGAT LAWAN SEJUK. Jumlah sun+ambient tetap ~1,0 per kanal, tapi kini
    # dibagi berlawanan rona: matahari kuning-jingga, ambient biru langit.
    # Sisi yang kena matahari jadi hangat, sisi gelap -- yang cuma menerima
    # ambient plus sisa matahari di pita gelap -- jadi sejuk. Itu yang
    # dilakukan patokan (rumput teduh B/G 0,92-0,98 lawan tersinar
    # 0,67-0,69); dulu keduanya serona hangat (R/B 1,19 dan 1,23) dan sisi
    # gelap cuma lebih redup. probe_cahaya, farm jam 10 setelah post:
    #
    #                          dulu (185,180,156)+(70,66,57)   kini
    #   geser B/G gelap, putih       -0,039                    +0,116
    #   geser B/G gelap, kelabu      +0,001                    +0,135
    #   terang/gelap, kelabu          1,528                     1,644
    #
    # Muka atas yang tersinar (tanah) tetap hangat-netral (B/G 0,96-0,98):
    # ambient hemisfer di smooth_shader cuma menambah sedikit biru dari atas.
    if 6 <= hour < 17:
        # Siang: sinar matahari hangat keemasan (Animal Crossing golden feel)
        if hujan:
            return (_w(145, 145, 158), _w(62, 62, 72), _w(88, 98, 115),
                    _w(145, 148, 162, 215))
        return (_w(222, 188, 122), _w(46, 68, 110), _w(128, 205, 248),
                _w(248, 248, 255, 175))
    if 17 <= hour < 19:
        # Senja: matahari jingga rendah, ambient ungu-biru dari langit yang
        # sudah meredup. Dulu ambient senja cokelat kemerahan (70,44,36), jadi
        # bayangan senja cuma versi gelap dari sinarnya; patokan evening_light
        # punya bayangan yang jelas lebih biru dari sinarnya. Diukur jam 17,6:
        # geser B/G sisi gelap +0,065 -> +0,197 setelah post.
        if hujan:
            return (_w(148, 95, 72), _w(55, 38, 35), _w(115, 82, 82),
                    _w(135, 108, 102, 195))
        return (_w(200, 122, 52), _w(52, 46, 80), _w(248, 138, 88),
                _w(255, 195, 148, 145))
    # Malam: biru rembulan. Angka lamanya (35,48,92 / 28,28,52) ditulis dengan
    # komentar "bukan hitam total" -- dan tidak pernah terbukti salah, karena
    # sampai saat itu cahaya adegan TIDAK PERNAH sampai ke satu entitas pun.
    # Begitu jalurnya dibuka, terukur: rumput jatuh ke 21,29,8 pada 22:00 dan
    # hewannya nyaris tidak terlihat. Malam harus redup, bukan buta.
    return (_w(62, 82, 140), _w(54, 58, 95), _w(18, 12, 42), _w(45, 45, 72, 75))


# Arah sinar matahari (dari matahari KE permukaan). Nilainya sama persis dengan
# konstanta yang dulu dikode mati di `_sync_smooth_lighting`, supaya penyatuan
# ini tidak mengubah satu piksel pun.
ARAH_AWAL = Vec3(-0.5, -0.8, -0.4)


def arah_lampu(sun) -> Vec3:
    """Arah sinar `DirectionalLight` Ursina di ruang dunia, ternormalisasi.

    Lampu Panda menyinari sepanjang sumbu maju node-nya, dan `look_at` Ursina
    mengarahkan sumbu maju itu ke sasarannya -- jadi ini arah yang sama yang
    dipakai kamera bayangan, bukan salinan yang bisa menyimpang darinya.
    """
    try:
        f = sun.forward
        v = Vec3(f[0], f[1], f[2])
        if v.length() > 1e-6:
            return v.normalized()
    except Exception:
        pass
    return ARAH_AWAL.normalized()
