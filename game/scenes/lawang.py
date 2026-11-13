"""lawang.py — Dukuh Lawang, dusun peternak di balik lereng.

Bagian dari Cerita Dua Desa (docs/CERITA_DUA_DESA.md), babak 1 "Datang".
Desa Karsa hidup dari kebun dan sawah; Dukuh Lawang dari kerbau dan kambing.
Jalan lama yang dulu menghubungkan keduanya lewat Gua Sang Hyang tertutup
longsor, jadi satu-satunya jalan masuk sekarang adalah jalur timur Lereng
Gunung yang memutar jauh. Longsor itu sengaja TERLIHAT di peta: jalan lama
berujung tumpukan batu di kaki tebing — janji untuk babak 2, ketika jalur gua
dibuka lagi.

Peta 28x21, dibaca dari utara ke selatan (prinsip P-nomor dari
docs/TATA_LETAK.md):

    y=0..1     tebing lereng — dusun ini duduk di kaki gunung
    y=2..8     jalan lama + longsor (barat) | rumah Mbah Rukmi | rumah Sekar |
               kandang kerbau (timur)
    y=9..10    JALAN DUKUH dua ubin, gapura di tepi barat (portal ke lereng)
    y=11..18   kubangan kerbau (barat) | LAPANGAN kosong | kandang kambing (timur)
    y=19..20   barisan pohon selatan

P1: maksud peta terbaca dari materialnya — dua kandang berlantai jerami dan
kubangan lumpur, bukan ladang. P13: lapangan di tengah dibiarkan KOSONG; di
sanalah Lomba Antar-Desa digelar (data.SEASONAL_EVENTS). P16: satu-satunya
pintu masuk adalah gapura yang diapit dua lentera.

Hewan di kandang adalah PROPERTI scene, bukan ANIMAL_NPCS: setiap entri di
sana dihitung husbandry.py/economy.py sebagai ternak milik pemain, sedangkan
kerbau dan kambing ini milik warga Lawang.

Babak 2 "Menjembatani" menambah dua hal: Papan Titipan warga di antara
gapura dan lapangan, dan kait `sesuaikan_lawang()` yang membuka jalan lama
setelah gotong royong dua desa (state.jalan_lama_terbuka): batu longsor jadi
jalan, tebing di ujungnya jadi mulut gua ke Gua Sang Hyang (naga_cave).
"""
from game.config import *
from game.scenes.scene_base import Scene
from game.scenes.layout import blank, rect, outline, hline, vline, scatter, put, belt
from game.scenes.zone_paint import Zone, TANAH_HALAMAN, TANAH_LADANG, JERAMI

# ─── Ukuran peta ────────────────────────────────────────────────────────────
W_, H_ = 28, 21

# ─── Titik yang DIPAKAI KODE LAIN (jangan geser tanpa mengubah sana juga) ───
# game/scenes/mountain.py mendaratkan pemain di (1,9)/(1,10). game/data.py
# (SCHEDULES) menaruh Mbah Rukmi di (23,8) (11,7) (12,14) dan Sekar di (23,15)
# (17,8) (17,7). Semua titik itu harus tetap bisa dijalani. Babak 2 menambah:
# naga_cave.py mendaratkan pemain di (4,3)/(5,3), dan data.JADWAL_* memakai
# lapangan (11,12) (12,12) (14,15) (9,15), longsor (5,6) (4,5) (6,4) (3,5),
# serta (12,10) (8,12).
GAPURA = ((0, 9), (0, 10))           # gapura dukuh → ujung jalur timur 'mountain'

# Properti hewan: (x, y, rotation_y). Di ubin jerami, menjauhi ubin tepat di
# balik gerbang supaya jalan masuk kandang tidak tertutup badan hewan.
KERBAU  = ((20, 4, 70), (23, 4, -110), (25, 6, 200))
KAMBING = ((20, 14, 30), (24, 14, -60), (21, 17, 160), (25, 16, 250))

# Papan Titipan warga Lawang (babak 2): di antara gapura dan lapangan, di tepi
# jalan dukuh, jadi setiap orang yang masuk dusun melewatinya.
PAPAN = (3, 11)

# Jalan lama ke Gua Sang Hyang (babak 2). Selama tertutup: batu longsor di
# (4..5,2) dan tebing utuh di (4..5,1). Setelah gotong royong: batu jadi jalan,
# tebing jadi mulut gua berportal ke naga_cave, dan dua pohon tumbang diganti
# lentera (P16: ambang yang baru dibuka ditandai, sama seperti gapura).
JALAN_LONGSOR = ((4, 2), (5, 2))
MULUT_GUA     = ((4, 1), (5, 1))
TUNGGUL       = ((3, 3), (6, 3))
# Pendaratan SATU ubin di dalam gua, bukan tepat di sebelah portal baliknya,
# supaya tombol yang masih ditahan tidak memantulkan pemain kembali ke Lawang.
# Bukaan gua di (14,3)/(14,4) — lihat PINTU_LAWANG di naga_cave.py.
PORTAL_GUA    = ((4, 1, 'naga_cave', 12, 3), (5, 1, 'naga_cave', 12, 4))


def build_lawang():
    m = blank(W_, H_, G)

    # ── 1. Tebing utara ─────────────────────────────────────────────────────
    # "Di balik lereng": dusun ini terjepit di kaki gunung, dan tebingnya
    # memakai ubin yang sama dengan dinding gua di peta lereng.
    rect(m, 0, 0, W_ - 1, 1, CV_W)

    # ── 2. Jalan dukuh dan gapura ───────────────────────────────────────────
    # P10: jalan dua ubin dari gapura barat sampai simpang kedua kandang, jadi
    # kedua ujungnya tujuan nyata. P16: perpindahan peta terjadi di gapura.
    hline(m, 0, 23, 9, P, thick=2)
    for gx, gy in GAPURA:
        put(m, gx, gy, GT)
    scatter(m, [(1, 8), (1, 11)], LN)
    put(m, PAPAN[0], PAPAN[1], PPN)

    # ── 3. Jalan lama ke gua, tertimbun longsor ─────────────────────────────
    # Satu-satunya jalan buntu di peta, dan buntunya disengaja: batu longsor
    # menjorok dari tebing dan dua pohon tumbang. Ini bukan "jalan yang
    # berbohong" (P10) — ia menunjukkan dengan jelas KENAPA jalannya terputus.
    vline(m, 4, 3, 8, P, thick=2)
    rect(m, 3, 2, 6, 2, CV_W)
    scatter(m, [(3, 3), (6, 3)], DT)

    # ── 4. Pekarangan dan rumah ─────────────────────────────────────────────
    # P11: kedua rumah menghadap jalan (props.build_house_block selalu
    # menggambar pintu di sisi selatan). P14: rumah sesepuh paling besar.
    rect(m, 7, 2, 18, 8, D)
    rect(m, 8, 3, 12, 6, H)              # rumah Mbah Rukmi
    vline(m, 10, 7, 8, P)
    rect(m, 15, 4, 17, 6, H)             # rumah Sekar
    vline(m, 16, 7, 8, P)
    scatter(m, [(7, 2), (14, 2)], TR)    # peneduh pekarangan

    # ── 5. Kandang kerbau (timur laut) ──────────────────────────────────────
    # P7: sub-petak berpagar dengan gerbang sendiri yang menghadap jalan.
    rect(m, 20, 3, 25, 6, STR_T)
    outline(m, 19, 2, 26, 7, PEN)
    put(m, 22, 7, GT)
    put(m, 22, 8, P)

    # ── 6. Lapangan dukuh ───────────────────────────────────────────────────
    # P13: persegi terbuka yang menempel ke jalan, tengahnya kosong. Lentera
    # di kedua sudut depan menandai "ini tempat berkumpul", bukan rumput sisa.
    rect(m, 7, 11, 16, 17, D)
    scatter(m, [(6, 11), (17, 11)], LN)

    # ── 7. Kubangan kerbau (barat daya) ─────────────────────────────────────
    # P8: air sebagai tujuan, dengan tepian lumpur yang bisa diinjak keliling.
    rect(m, 0, 12, 5, 18, D)
    rect(m, 1, 13, 4, 17, W)

    # ── 8. Kandang kambing (tenggara) ───────────────────────────────────────
    rect(m, 20, 13, 25, 17, STR_T)
    outline(m, 19, 12, 26, 18, PEN)
    put(m, 22, 12, GT)
    put(m, 22, 11, P)

    # ── 9. Batas peta ───────────────────────────────────────────────────────
    # Pohon BERSELANG, bukan rapat: pohon berharga 5 entity per ubin
    # (TATA_LETAK §3), dan barisan jarang sudah cukup terbaca sebagai tepi.
    belt(m, 0, 19, W_ - 1, 20, TR, step=3)
    belt(m, W_ - 1, 2, W_ - 1, 18, TR, step=2)
    belt(m, 0, 2, 0, 8, TR, step=2)

    # ── 10. Cat zona ────────────────────────────────────────────────────────
    # Alasannya sama dengan farm.py: tanpa lapisan ini ubin tanah dan jerami
    # ikut tertimpa papan catur rumput dari world.py. Kubangan dicat sebagai
    # cincin empat sisi, karena satu persegi utuh akan menutupi airnya.
    paint = [
        Zone(7, 2, 18, 8, **TANAH_HALAMAN),     # pekarangan
        Zone(7, 11, 16, 17, **TANAH_HALAMAN),   # lapangan
        Zone(20, 3, 25, 6, **JERAMI),           # lantai kandang kerbau
        Zone(20, 13, 25, 17, **JERAMI),         # lantai kandang kambing
        Zone(0, 12, 5, 12, **TANAH_LADANG),     # tepian kubangan: utara
        Zone(0, 18, 5, 18, **TANAH_LADANG),     #                  selatan
        Zone(0, 13, 0, 17, **TANAH_LADANG),     #                  barat
        Zone(5, 13, 5, 17, **TANAH_LADANG),     #                  timur
    ]

    # builder_name ikut tersimpan di lawang.json: berkas scene tidak bisa memuat
    # fungsi, jadi kerbau dan kambing warga dipasang ulang lewat namanya
    # (scene_base.resolve_builder).
    return Scene('lawang', 'Dukuh Lawang', m, paint=paint, builder=lawang_builder,
                 builder_name='lawang',
                 portals=[
                     (GAPURA[0][0], GAPURA[0][1], 'mountain', 28, 12),
                     (GAPURA[1][0], GAPURA[1][1], 'mountain', 28, 13),
                 ])


def sesuaikan_lawang(scene, state):
    """Buka atau tutup jalan lama menurut save yang dimuat.

    Dipanggil scenes.sesuaikan_scene() dari World3D.load_scene(). Ditulis dua
    arah dengan sengaja: SCENES hanya dibangun sekali per proses, jadi kalau
    hanya bisa membuka, memuat save lama (F9) sesudah save yang jalannya sudah
    terbuka akan mewarisi jalan itu.
    """
    buka = bool(getattr(state, 'jalan_lama_terbuka', False))
    m = scene.tiles
    for x, y in JALAN_LONGSOR:
        m[y][x] = P if buka else CV_W
    for x, y in MULUT_GUA:
        m[y][x] = CV_F if buka else CV_W
    for x, y in TUNGGUL:
        m[y][x] = LN if buka else DT
    scene.portals[:] = [p for p in scene.portals if tuple(p) not in PORTAL_GUA]
    if buka:
        scene.portals.extend(PORTAL_GUA)


def lawang_builder(world):
    """Prop standar, lalu kerbau dan kambing warga di kandangnya."""
    from ursina import Entity
    from game.animal_models import build_animal
    from .props import default_prop_builder
    default_prop_builder(world, world.scene_obj)

    for jenis, daftar in (('kerbau', KERBAU), ('kambing', KAMBING)):
        for tx, ty, rot in daftar:
            # Berdiri DI ATAS permukaan jerami (GROUND_H), dan didaftarkan ke
            # _obj_ents supaya ikut dibersihkan World3D._clear() saat pindah scene.
            induk = Entity(position=(tx * TILE_SIZE, GROUND_H, ty * TILE_SIZE),
                           rotation_y=rot)
            build_animal(induk, jenis)
            world._obj_ents.append(induk)
