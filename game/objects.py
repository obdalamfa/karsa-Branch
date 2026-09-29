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
                     DCK, W, GR, CRYS, BLOCKING)


def _i(name, adverts, duration=60.0, atten=0.3, autonomous=True, auto_first=False):
    return Interaction(name=name, adverts=adverts, duration=duration,
                       attenuation=atten, autonomous=autonomous,
                       auto_first=auto_first)


# ─── KATALOG INTERAKSI PER TILE ──────────────────────────
# `minimum` adalah GERBANG: iklan hanya berlaku kalau motif sim sudah di bawah
# nilai itu. Itulah yang mencegah sim tidur saat segar atau makan saat kenyang,
# tanpa satu pun aturan prioritas khusus.
OBJECT_INTERACTIONS: dict[int, list[Interaction]] = {

    BD: [
        _i('Tidur', [Advert('energi', 110, minimum=30),
                     Advert('nyaman', 40)], duration=420, auto_first=True),
        _i('Rebahan', [Advert('nyaman', 35, minimum=40),
                       Advert('energi', 20, minimum=60)], duration=60),
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
        _i('Nonton TV', [Advert('senang', 38, minimum=70),
                         Advert('nyaman', 12)], duration=90),
    ],

    BS: [
        _i('Baca Buku', [Advert('senang', 26, minimum=60)], duration=90),
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
        _i('Ambil Barang', [Advert('senang', 10, minimum=40)], duration=15),
    ],

    CH: [
        _i('Buka Peti', [Advert('senang', 12, minimum=50)], duration=15),
    ],

    PP: [
        _i('Siram Tanaman', [Advert('senang', 14, minimum=50),
                             Advert('ruang', 10)], duration=25),
    ],

    CL: [
        _i('Lihat Jam', [Advert('senang', 4, minimum=20)], duration=8),
    ],

    DCK: [
        _i('Duduk di Dermaga', [Advert('senang', 30, minimum=60),
                                Advert('nyaman', 18)], duration=90),
    ],

    W: [
        _i('Cuci Muka', [Advert('higiene', 26, minimum=60),
                         Advert('senang', 8)], duration=20),
    ],

    GR: [
        # Bukan penambah motif — pemicu cerita. Tidak pernah dipilih otonom.
        _i('Berdoa', [Advert('senang', 6, minimum=30)], duration=45,
           autonomous=False),
    ],
}


def interactions_for(tile_id: int) -> list[Interaction]:
    """Daftar interaksi untuk satu jenis tile. Kosong kalau bukan perabot."""
    return OBJECT_INTERACTIONS.get(tile_id, [])


def is_interactive(tile_id: int) -> bool:
    return tile_id in OBJECT_INTERACTIONS


def _kandidat(world, tx: int, ty: int, radius: int, jarak):
    """Semua perabot yang bisa dipakai di sekitar (tx, ty).

    Dua sumber: ubin di grid, dan objek terpasang bebas (`Scene.objects`).
    Digabung di SATU tempat supaya `find_nearby` dan `autonomy_candidates`
    tidak pernah punya gagasan berbeda tentang apa yang ada di sekitar --
    kalau keduanya memindai sendiri-sendiri, pemain dan NPC akan melihat dunia
    yang berbeda, dan yang satu akan bisa memasak di kompor yang tidak ada bagi
    yang lain.

    `jarak(dx, dy)` menentukan metriknya: Chebyshev untuk pemain (delapan
    tetangga), Euclidean untuk NPC (boleh menyeberang ruangan).

    Mengembalikan [(jarak, tx, ty, tile_id, interaksi), ...].
    """
    hasil = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = tx + dx, ty + dy
            tid = world.get_tile(nx, ny)
            acts = interactions_for(tid)
            if acts:
                hasil.append((jarak(dx, dy), nx, ny, tid, acts))

    # Objek terpasang. Posisinya FLOAT, jadi jaraknya dihitung dari posisi
    # sebenarnya, bukan dari ubin terdekat: pot yang ditanam setengah ubin dari
    # pemain memang harus terasa lebih dekat daripada ubin di sebelahnya.
    # `tx`/`ty` yang dikembalikan tetap bilangan bulat karena dipakai untuk
    # mencari jalan, dan pathfinder bekerja pada grid.
    objek = getattr(getattr(world, 'scene_obj', None), 'objects', None) or []
    for o in objek:
        tid = tile_dari_kind(o['kind'])
        acts = interactions_for(tid) if tid is not None else []
        if not acts:
            continue
        d = jarak(o['x'] - tx, o['y'] - ty)
        if d > radius:
            continue
        hasil.append((d, int(round(o['x'])), int(round(o['y'])), tid, acts))
    return hasil


def find_nearby(world, tx: int, ty: int, radius: int = 1):
    """Perabot yang bisa dipakai di sekitar tile (tx, ty).

    Mengembalikan [(jarak, tx, ty, tile_id, interaksi), ...] terurut dari yang
    terdekat. Radius 1 = delapan tetangga plus tile itu sendiri, yang cocok
    dengan cara pemain berdiri tepat di depan benda.
    """
    hits = _kandidat(world, tx, ty, radius, lambda dx, dy: max(abs(dx), abs(dy)))
    hits.sort(key=lambda h: h[0])
    return hits


def autonomy_candidates(world, tx: int, ty: int, radius: int = 8):
    """Kandidat (objek, interaksi, jarak) untuk `motives.choose_action`.

    Dipakai NPC untuk memilih sendiri apa yang mau dilakukan. Radius sengaja
    jauh lebih besar daripada `find_nearby`: sim boleh berjalan menyeberangi
    ruangan demi sesuatu yang cukup berharga, dan falloff jarak di
    `score_interaction` yang memutuskan apakah itu sepadan.

    BELUM ADA PEMANGGILNYA. Ia melihat objek terpasang sejak Fase 5c supaya
    tidak menjadi jebakan bagi yang menyambungkannya nanti -- mesin autonomi di
    `behavior_vm.py` lengkap tetapi belum tersambung ke dunia, dan menyambungkan
    itu pekerjaan tersendiri.
    """
    out = []
    for dist, nx, ny, tid, acts in _kandidat(
            world, tx, ty, radius, lambda dx, dy: (dx * dx + dy * dy) ** 0.5):
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
}


def object_name(tile_id: int) -> str:
    return OBJECT_NAMES.get(tile_id, 'Benda')


# ─── PENEMPATAN BEBAS ───────────────────────────────────────────────────────
# Sampai sini perabot hanya bisa datang dari GRID: satu tile ID menempati satu
# sel. `Scene.objects` (game/scenes/scene_base.py) membolehkan perabot yang
# SAMA diletakkan di posisi bebas, dengan rotasi dan skala.
#
# Kuncinya: objek bebas TIDAK punya katalog sendiri. `kind`-nya memetakan ke
# TILE ID yang sudah ada, sehingga tekstur, nama pemain, interaksi, dan sifat
# memblokirnya semua diambil dari tabel di atas. Katalog kedua akan perlahan
# menyimpang dari yang pertama, dan pemain akan menemukan kompor yang bisa
# dimasak di grid tapi tidak bisa dimasak begitu dipindah ke halaman.
OBJECT_KINDS: dict[str, int] = {
    'kasur': BD, 'kompor': ST, 'meja': TB, 'kursi': CHR,
    'televisi': TV, 'rak_buku': BS, 'cermin': MR, 'tungku': FP,
    'konter': CT, 'rak': SH, 'peti': CH, 'pot': PP,
    'jam': CL, 'dermaga': DCK, 'nisan': GR,
}


def tile_dari_kind(kind: str):
    """Tile ID untuk sebuah jenis objek, atau None kalau jenisnya tak dikenal."""
    return OBJECT_KINDS.get(kind)


# Tinggi kotak objek dalam satuan ubin, dipakai perender sampai tiap jenis punya
# modelnya sendiri. Angkanya kasar dengan SENGAJA: yang perlu terbaca dari
# viewport adalah bahwa kasur lebih rendah daripada rak buku, bukan bahwa
# tingginya presisi. Model khusus per jenis adalah pekerjaan terpisah.
OBJECT_TINGGI: dict[str, float] = {
    'kasur': 0.30, 'kompor': 0.55, 'meja': 0.45, 'kursi': 0.55,
    'televisi': 0.40, 'rak_buku': 0.95, 'cermin': 0.90, 'tungku': 0.75,
    'konter': 0.55, 'rak': 0.95, 'peti': 0.45, 'pot': 0.35,
    'jam': 0.20, 'dermaga': 0.15, 'nisan': 0.75,
}


def tinggi_kind(kind: str) -> float:
    """Tinggi kotak sebuah jenis, dalam satuan ubin."""
    return OBJECT_TINGGI.get(kind, 0.6)


def kind_dari_tile(tile_id: int):
    """Kebalikan `tile_dari_kind`. Dipakai editor untuk menandai objek."""
    for kind, tid in OBJECT_KINDS.items():
        if tid == tile_id:
            return kind
    return None


def solid_kind(kind: str) -> bool:
    """Apakah objek jenis ini memblokir jalan.

    Diambil dari `BLOCKING` yang sama dengan yang dipakai grid, jadi tidak ada
    daftar kedua yang bisa berbeda diam-diam.
    """
    tid = OBJECT_KINDS.get(kind)
    return tid is not None and tid in BLOCKING
