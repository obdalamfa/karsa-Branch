"""farm.py — Kebun Paman Arsa, dirombak mengikuti bentuk Stardew / Harvest Moon.

Rancangan lengkap dan alasannya ada di `docs/TATA_LETAK.md`. Ringkasnya, peta
lama 25x18 punya sebagian bahan tapi tidak punya ZONA: rumah menempel di pojok,
kandang melayang di tengah rumput, tidak ada kolam, tidak ada puing untuk
dibersihkan, dan yang paling parah — TIDAK ADA LADANG. Seluruh peta rumput, dan
rumput di sini juga bisa dicangkul, jadi tidak ada satu tempat pun yang berkata
"di sinilah kamu bertani". Itu kebalikan dari Stardew, yang justru memberi satu
petak besar telanjang sebagai perintah diam.

Peta sekarang 28x20, dibaca dari utara ke selatan sebagai tiga pita:

    y=0        pagar utara
    y=1..8     PEKARANGAN  rumah (barat) | kandang ternak (tengah) | rumah kaca (timur)
    y=9..10    JALAN UTAMA dua ubin: pintu rumah di ujung barat, gerbang desa di timur
    y=11..18   LAHAN       kolam (barat) | LADANG besar | kebun buah (timur)
    y=19       pagar selatan

Kenapa dibesarkan dari 450 jadi 560 ubin: dengan lima zona (rumah, kandang,
rumah kaca, ladang, kolam) di 25x18 tiap zona bersentuhan langsung dengan
tetangganya dan batas antar zona berhenti terbaca (TATA_LETAK P3). Ongkosnya
dibayar dengan mengganti rumput kosong (2,3 entity/ubin) jadi tanah — ladang
dan pekarangan sama-sama `D` (1 entity/ubin). Lihat TATA_LETAK §3: peta yang
lebih mirip Stardew di sini kebetulan juga peta yang lebih murah per ubin.
"""
from game.config import *
from game.scenes.scene_base import Scene
from game.scenes.layout import blank, rect, outline, border, hline, vline, scatter, put
from game.scenes.zone_paint import Zone, TANAH_LADANG, TANAH_HALAMAN, JERAMI

# ─── Ukuran peta ────────────────────────────────────────────────────────────
W_, H_ = 28, 20

# ─── Titik yang DIPAKAI KODE LAIN (jangan geser tanpa mengubah sana juga) ───
# game/data.py menaruh ternak di (16..20, 5..7), warga di (4,4) (5,5) (5,8)
# (12,12) (10,14) (7,16), kucing di (7,9), dan game/state.py memulai pemain di
# (8,8). Semua titik itu harus tetap bisa dijalani DAN tetap masuk akal secara
# zona — ternak di dalam kandang, warga di pekarangan dan ladang. Kandang dan
# ladang di bawah dipasang MENGELILINGI koordinat itu, bukan sebaliknya.
DOOR_HOUSE = (3, 4)                  # ambang pintu rumah      → scene 'house'
DOOR_GREEN = (25, 5)                 # ambang pintu rumah kaca → scene 'greenhouse'
GATE_OUT   = ((27, 9), (27, 10))     # gerbang timur           → scene 'town'


def build_farm():
    m = blank(W_, H_, G)

    # ── 1. Batas milik ──────────────────────────────────────────────────────
    # TATA_LETAK P2: kebun harus punya "dalam" dan "luar", dan lubangnya TEPAT
    # SATU. Pagar keliling penuh, lalu dua ubin gerbang di timur — gerbang itu
    # sekaligus portalnya, jadi ambang yang DILIHAT pemain dan ambang yang
    # DIEKSEKUSI kode adalah benda yang sama. Peta lama memindahkan pemain dari
    # sepotong jalan biasa di tepi peta; tidak ada yang menandainya.
    border(m, FN)
    for gx, gy in GATE_OUT:
        put(m, gx, gy, GT)

    # ── 2. Jalan utama ──────────────────────────────────────────────────────
    # P10: jalan adalah kompas. Dua ubin lebar — dari pitch 34 jalan satu ubin
    # terbaca sebagai garis, bukan sebagai sesuatu yang dilalui. Ia membentang
    # dari teras rumah (x=3) sampai gerbang desa (x=26), jadi KEDUA ujungnya
    # tujuan nyata dan tidak ada ujung yang buntu.
    hline(m, 3, 26, 9, P, thick=2)

    # ── 3. Rumah dan pekarangan (barat) ─────────────────────────────────────
    # P5: rumah di TEPI lahan, menghadap sisi kerja. props.build_house_block()
    # selalu menggambar pintu di sisi +z (selatan), jadi blok rumah wajib punya
    # ruang kosong di selatannya — di situlah teras dan portalnya duduk.
    rect(m, 2, 1, 5, 3, H)
    rect(m, 2, 4, 5, 4, P)               # teras selebar muka rumah
    vline(m, 3, 5, 8, P)                 # setapak teras → jalan utama

    # Pekarangan tanah padat, bukan rumput: halaman rumah petani yang diinjak
    # tiap hari memang tidak berumput. Sekaligus memisahkan "pekarangan" dari
    # "rumput yang belum dipakai" tanpa menambah ongkos (D=1, G=2,3).
    for y in range(4, 11):
        for x in range(1, 8):
            if m[y][x] == G:
                m[y][x] = D

    # P6: peti kirim menempel teras, DI ATAS jalur keluar. Pemain melewatinya
    # tiap pagi; menemukannya tidak boleh butuh usaha. Kotak surat di sisi
    # seberang jalan setapak supaya keduanya terbaca sebagai sepasang.
    put(m, 4, 5, CH)
    put(m, 2, 5, MB)
    put(m, 6, 8, LN)                     # lentera sudut pekarangan
    scatter(m, [(1, 2), (7, 2)], TR)     # dua pohon peneduh mengapit rumah

    # ── 4. Kandang ternak (tengah) ──────────────────────────────────────────
    # P7: sub-petak berpagar sendiri, lantai jerami, gaya pagar BEDA dari pagar
    # keliling (PEN → meshes 'kandang', FN → 'bambu'), gerbang sendiri yang
    # menghadap jalan utama. Sengaja LEBAR — padang gembala berpagar seperti
    # Harvest Moon, bukan kotak sempit. Jerami (1 entity) menggantikan rumput
    # (2,3), jadi memperluas kandang justru MENURUNKAN ongkos frame.
    rect(m, 13, 3, 21, 7, STR_T)
    outline(m, 12, 2, 22, 8, PEN)
    put(m, 17, 8, GT)                    # gerbang kandang langsung ke jalan

    # ── 5. Rumah kaca (timur) ───────────────────────────────────────────────
    # Dipindah dari desa ke kebun. Di Stardew maupun Harvest Moon rumah kaca
    # adalah milik PETANI dan berdiri di petaknya sendiri; menaruhnya di antara
    # ruko desa membuat satu-satunya bangunan bertani di game ini terasa seperti
    # fasilitas umum. Perubahannya satu baris di sini dan satu baris di
    # greenhouse.py — mudah dikembalikan kalau pemilik tidak setuju.
    rect(m, 24, 2, 26, 4, H)
    for y in range(5, 9):                # halaman muka rumah kaca
        for x in range(24, 27):
            if m[y][x] == G:
                m[y][x] = D
    vline(m, 25, 5, 8, P)                # setapak rumah kaca → jalan utama
    put(m, 26, 8, LN)                    # lentera penanda gerbang keluar

    # ── 6. Ladang (jantung peta) ────────────────────────────────────────────
    # P4: persegi TERBESAR di peta, dan sengaja kosong. 16x8 ubin tanah yang
    # menempel langsung ke jalan utama di utara dan ke pagar selatan — pemain
    # melangkah dari jalan ke tanah garapan tanpa perantara.
    rect(m, 8, 11, 23, 18, D)
    # Satu lorong tegak membelah ladang jadi dua bedeng. Inilah yang membuat
    # petak terbaca sebagai LADANG YANG DIRANCANG, bukan bidang tanah kosong;
    # di Harvest Moon bedeng juga selalu dipisah jalan kerja.
    vline(m, 15, 11, 18, P)

    # P9: puing adalah tutorial, dan tempatnya DI DALAM ladang. Semuanya di
    # separuh selatan supaya bedeng utara terbaca "sudah bersih sampai sini" —
    # rasa kemajuan sebelum pemain menebang apa pun.
    scatter(m, [(9, 16), (11, 17), (13, 18), (18, 16), (20, 15), (21, 18)], DT)

    # ── 7. Kolam (barat daya) ───────────────────────────────────────────────
    # P8: air sebagai tujuan, bukan tekstur. Gumpalan padat bertepi tidak rata,
    # dikelilingi tepian RUMPUT — pergantian material itulah batas zona antara
    # kolam dan ladang (P3). Dermaga menjorok ke air dari tepi timur supaya ada
    # ubin yang bisa diinjak di atas air.
    rect(m, 2, 12, 6, 12, W)
    rect(m, 2, 13, 5, 13, W)
    rect(m, 2, 14, 5, 14, W)
    rect(m, 2, 15, 6, 15, W)
    rect(m, 3, 16, 5, 16, W)
    put(m, 6, 13, DCK)
    put(m, 6, 14, DCK)

    # ── 8. Kebun buah (tenggara) ────────────────────────────────────────────
    # Pohon BERSELANG, bukan rapat: berselang terbaca sebagai kebun yang ditanam
    # orang, rapat terbaca sebagai hutan. Enam pohon = 30 entity — jumlah yang
    # dipilih, bukan hasil rng seperti di peta gunung lama.
    scatter(m, [(24, 12), (26, 12), (24, 14), (26, 14), (24, 16), (26, 16)], TR)

    # ── 9. Cat zona ─────────────────────────────────────────────────────────
    # world.py mewarnai HAMPIR SEMUA ubin luar ruang dengan papan catur rumput,
    # jadi ubin tanah `D` terbaca sebagai halaman hijau pucat — diukur di
    # `_bench/shots/layout_farm_over.png`. Empat lapisan di bawah mengembalikan
    # warna tiap zona dengan ongkos 1 entity per zona. Rinciannya di
    # game/scenes/zone_paint.py.
    paint = [
        Zone(8, 11, 23, 18, **TANAH_LADANG),    # ladang: tanah garapan
        Zone(1, 4, 7, 10, **TANAH_HALAMAN),     # pekarangan rumah
        Zone(24, 5, 26, 8, **TANAH_HALAMAN),    # halaman rumah kaca
        Zone(13, 3, 21, 7, **JERAMI),           # lantai kandang
    ]

    return Scene('farm', 'Kebun Paman Arsa', m, paint=paint, portals=[
        (DOOR_HOUSE[0], DOOR_HOUSE[1], 'house', 7, 9),
        (DOOR_GREEN[0], DOOR_GREEN[1], 'greenhouse', 7, 10),
        (GATE_OUT[0][0], GATE_OUT[0][1], 'town', 1, 14),
        (GATE_OUT[1][0], GATE_OUT[1][1], 'town', 1, 15),
    ])
