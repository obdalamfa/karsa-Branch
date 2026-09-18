"""objects.py — Interaksi yang diiklankan oleh perabot.

Ini yang menutup loop permainan. Sebelum modul ini, motif hanya bisa TURUN:
tidak ada satu pun cara menaikkannya, jadi tekanan yang dibangun mesin motif
tidak punya jalan keluar dan permainan tidak punya loop sama sekali.

Arsitektur mengikuti The Sims: **iklan menempel pada INTERAKSI, bukan pada
objek.** Kompor tidak "memberi +45 lapar"; interaksi *Masak* pada kompor yang
mengiklankan lapar, sementara *Bersihkan* pada kompor yang sama mengiklankan
higiene ruangan. Satu objek menawarkan beberapa janji berbeda, dan sim memilih
di antaranya lewat skor — lihat `motives.score_interaction`.

Kebutuhan mengikuti The Sims 3, enam buah: lapar, kandung, energi, sosial,
higiene, senang. Nyaman dan ruang tetap ada di mesin tapi tidak lagi menjadi
kebutuhan yang ditampilkan — keduanya akan menjadi moodlet.
"""
from __future__ import annotations

from .motives import Advert, Interaction
from .config import (BD, ST, TB, CHR, TV, CH, BS, MR, FP, CT, SH, PP, CL,
                     DCK, W, GR, CRYS, WC)


def _i(name, adverts, duration=60.0, atten=0.3, autonomous=True, auto_first=False):
    return Interaction(name=name, adverts=adverts, duration=duration,
                       attenuation=atten, autonomous=autonomous,
                       auto_first=auto_first)


# ─── KATALOG INTERAKSI PER TILE ──────────────────────────
# `minimum` adalah GERBANG: iklan hanya berlaku kalau motif sim sudah di bawah
# nilai itu. Itulah yang mencegah sim tidur saat segar atau makan saat kenyang,
# tanpa satu pun aturan prioritas khusus.
#
# LAJU EFEKTIF sebuah interaksi adalah delta/duration, poin per menit-sim —
# `ActionQueue` membayar `ad.delta * frac` seiring aksinya berjalan, dan
# `attenuation` hanya mempengaruhi PEMILIHAN (falloff jarak di
# score_interaction), bukan bayarannya. Jadi durasi sama pentingnya dengan
# delta, dan menaikkan delta sambil memanjangkan durasi tidak mengubah apa pun.
#
# Knop C (#6): sebelum putaran ini, empat kegiatan santai yang memang DIRANCANG
# sebagai kegiatan semuanya membayar di bawah median katalog 0,47 — Nonton TV
# 0,42, Duduk di Dermaga 0,33, Baca Buku 0,29, Berdoa 0,13 — sementara tiga
# interaksi SAMBIL LALU membayar paling baik: Buka Peti 0,80, Ambil Barang
# 0,67, Lihat Jam 0,50. Sumber Senang paling efisien di seluruh permainan
# adalah membuka peti berulang kali, dan pemain yang memilih bersantai membayar
# lebih banyak WAKTU untuk poin yang sama. Keempatnya dinaikkan ke puncak
# katalog dan ketiganya diturunkan — bukan supaya bersantai jadi optimal, tapi
# supaya ia berhenti jadi pilihan yang merugikan.
#
# Yang TIDAK berubah karenanya, dan ini perlu ditulis supaya tidak ada yang
# mengklaim lebih: pilihan otonom warga hampir tidak bergeser. Diukur dengan
# sim ber-Senang -60 dan peti diletakkan paling dekat, 400 pilihan berturut:
# sebelum TV 155 / Baca 105 / Dermaga 81 / Peti 59; sesudah 157 / 123 / 89 / 31.
# Sebabnya `score_interaction` tidak pernah membaca `duration` sama sekali —
# ia menilai DELTA setelah falloff jarak, jadi Nonton TV +38 sudah mengalahkan
# Buka Peti +12 sejak dulu. Knop C memperbaiki ongkos WAKTU yang dibayar
# pemain, bukan pilihan mesinnya. Bahwa mesin itu buta terhadap durasi —
# sehingga aksi 420 menit bisa dipilih di atas aksi 12 menit demi delta yang
# sedikit lebih besar — adalah cacat tersendiri, belum diperbaiki di sini.
OBJECT_INTERACTIONS: dict[int, list[Interaction]] = {

    BD: [
        # Gerbang energi diturunkan 30 -> -40, dan itu perbaikan cacat yang
        # bisa diukur. `score_interaction` tidak pernah membaca `duration`, jadi
        # Tidur menang lewat delta +110 tanpa ada yang menghitung bahwa ia makan
        # 420 menit — tujuh jam. Dengan gerbang 30 dan energi cuma -20 (baru
        # agak lelah), terukur: 400 dari 400 pilihan otonom jatuh ke Tidur,
        # kapan pun siangnya. Bikin Kopi (20 menit, +25) tidak pernah terpilih
        # satu kali pun, dan Rebahan juga tidak.
        #
        # Gerbangnya, bukan skornya, yang diperbaiki: warga yang AGAK lelah
        # sekarang tidak melihat kasur sama sekali dan mengambil kopi; yang
        # benar-benar habis (di bawah -40) melihatnya dan tidur. Memperbaiki
        # mesin skornya supaya menghitung durasi adalah perkara tersendiri dan
        # menyentuh setiap pilihan di permainan — lihat tiket durasi-buta.
        # Nyaman ikut digerbangi, dengan alasan yang sama. `minimum` hanya
        # mempengaruhi PEMILIHAN — `ActionQueue._apply` membayar tiap advert
        # tanpa memeriksa gerbangnya — jadi tidur tetap terasa nyaman, ia cuma
        # berhenti menjadi ALASAN untuk tidur. Tanpa ini, warga yang cuma agak
        # lelah masih memilih Tidur 13% dari waktunya lewat jalur Nyaman, dan
        # tujuh jam adalah harga yang mahal untuk sebuah bantal.
        _i('Tidur', [Advert('energi', 110, minimum=-40),
                     Advert('nyaman', 40, minimum=-50)],
           duration=420, auto_first=True),
        _i('Rebahan', [Advert('nyaman', 35, minimum=40),
                       Advert('energi', 20, minimum=60)], duration=60),
    ],

    WC: [
        # Kamar Kecil adalah satu-satunya motif yang meluruh SETIAP HARI tanpa
        # satu pun interaksi yang mengiklankannya — 234,4 poin/hari terhadap
        # suplai nol, terukur di tools/neraca_motif.py. Motif dengan permintaan
        # tapi tanpa suplai bukan tekanan, ia cuma pajak: mesin iklan tidak
        # punya apa pun untuk ditawarkan, jadi warga tidak pernah bisa
        # mengurusnya dan mood mereka tertahan ke bawah selamanya.
        #
        # +60 dalam 12 menit = 5,0 poin/menit, jadi 234,4 poin/hari terbayar
        # dalam 47 menit-sim — sekitar empat kali pakai sehari. Itu sengaja
        # jauh di atas laju katalog lain: mengurus kamar kecil harus CEPAT,
        # kalau tidak ia memakan hari yang seharusnya dipakai bertani.
        _i('Pakai Kamar Kecil', [Advert('kandung', 60, minimum=60)],
           duration=12, auto_first=True),
        _i('Bersihkan', [Advert('ruang', 14, minimum=40),
                         Advert('higiene', -6)], duration=30),
    ],

    ST: [
        _i('Masak', [Advert('lapar', 55, minimum=50)], duration=60),
        _i('Bikin Kopi', [Advert('energi', 25, minimum=50),
                          Advert('senang', 8)], duration=20),
    ],

    TB: [
        _i('Makan', [Advert('lapar', 45, minimum=60),
                     Advert('nyaman', 12)], duration=45),
        _i('Duduk Ngobrol', [Advert('sosial', 30, minimum=60),
                             Advert('nyaman', 15)], duration=60),
    ],

    CHR: [
        _i('Duduk', [Advert('nyaman', 40, minimum=50)], duration=60),
    ],

    TV: [
        _i('Nonton TV', [Advert('senang', 60, minimum=70),
                         Advert('nyaman', 12)], duration=75),
    ],

    BS: [
        _i('Baca Buku', [Advert('senang', 48, minimum=60)], duration=70),
    ],

    MR: [
        _i('Rapikan Diri', [Advert('higiene', 22, minimum=60),
                            Advert('senang', 6)], duration=25),
    ],

    FP: [
        _i('Hangatkan Diri', [Advert('nyaman', 32, minimum=40)], duration=45),
    ],

    CT: [
        _i('Cuci Tangan', [Advert('higiene', 30, minimum=60)], duration=15),
        _i('Siapkan Makanan', [Advert('lapar', 35, minimum=50)], duration=40),
    ],

    SH: [
        _i('Ambil Barang', [Advert('senang', 6, minimum=40)], duration=18),
    ],

    CH: [
        _i('Buka Peti', [Advert('senang', 8, minimum=50)], duration=20),
    ],

    PP: [
        _i('Siram Tanaman', [Advert('senang', 14, minimum=50),
                             Advert('ruang', 10)], duration=25),
    ],

    CL: [
        _i('Lihat Jam', [Advert('senang', 2, minimum=20)], duration=10),
    ],

    DCK: [
        _i('Duduk di Dermaga', [Advert('senang', 52, minimum=60),
                                Advert('nyaman', 18)], duration=70),
    ],

    W: [
        _i('Cuci Muka', [Advert('higiene', 26, minimum=60),
                         Advert('senang', 8)], duration=20),
    ],

    GR: [
        # Bukan penambah motif — pemicu cerita. Tidak pernah dipilih otonom.
        _i('Berdoa', [Advert('senang', 24, minimum=30)], duration=45,
           autonomous=False),
    ],
}


def interactions_for(tile_id: int) -> list[Interaction]:
    """Daftar interaksi untuk satu jenis tile. Kosong kalau bukan perabot."""
    return OBJECT_INTERACTIONS.get(tile_id, [])


def is_interactive(tile_id: int) -> bool:
    return tile_id in OBJECT_INTERACTIONS


def find_nearby(world, tx: int, ty: int, radius: int = 1):
    """Perabot yang bisa dipakai di sekitar tile (tx, ty).

    Mengembalikan [(jarak_tile, tx, ty, tile_id, interaksi), ...] terurut dari
    yang terdekat. Radius 1 = delapan tetangga plus tile itu sendiri, yang
    cocok dengan cara pemain berdiri tepat di depan benda.
    """
    hits = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = tx + dx, ty + dy
            tid = world.get_tile(nx, ny)
            acts = interactions_for(tid)
            if not acts:
                continue
            dist = max(abs(dx), abs(dy))
            hits.append((dist, nx, ny, tid, acts))
    hits.sort(key=lambda h: h[0])
    return hits


def autonomy_candidates(world, tx: int, ty: int, radius: int = 8):
    """Kandidat (objek, interaksi, jarak) untuk `motives.choose_action`.

    Dipakai NPC untuk memilih sendiri apa yang mau dilakukan. Radius sengaja
    jauh lebih besar daripada `find_nearby`: sim boleh berjalan menyeberangi
    ruangan demi sesuatu yang cukup berharga, dan falloff jarak di
    `score_interaction` yang memutuskan apakah itu sepadan.
    """
    out = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = tx + dx, ty + dy
            tid = world.get_tile(nx, ny)
            acts = interactions_for(tid)
            if not acts:
                continue
            dist = (dx * dx + dy * dy) ** 0.5
            for act in acts:
                out.append(((nx, ny, tid), act, dist))
    return out


# Nama tampilan perabot. TILE_NAMES di config.py berbahasa Inggris dan dipakai
# untuk pencarian tekstur, jadi nama untuk pemain disimpan terpisah di sini.
OBJECT_NAMES: dict[int, str] = {
    BD: 'Kasur',      ST: 'Kompor',    TB: 'Meja',       CHR: 'Kursi',
    TV: 'Televisi',   BS: 'Rak Buku',  MR: 'Cermin',     FP: 'Tungku',
    CT: 'Konter',     SH: 'Rak',       CH: 'Peti',       PP: 'Pot Tanaman',
    CL: 'Jam',        DCK: 'Dermaga',  W: 'Air',         GR: 'Nisan',
    WC: 'Kamar Kecil',
}


def object_name(tile_id: int) -> str:
    return OBJECT_NAMES.get(tile_id, 'Benda')
