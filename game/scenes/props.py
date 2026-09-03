from game.config import *
from ursina import color
import math

TS = TILE_SIZE

# ── Bahan atap ──────────────────────────────────────────────────────────────
# DIHAPUS di sini: tabel `ROOF_TEXTURES` (20 entri) dan fungsi `tint_atap()`.
# Keduanya hanya dipakai oleh build_house_block dan digantikan tabel di bawah.
# Alasannya dua, dan keduanya terukur:
#
# 1. Dua puluh entri itu menghasilkan SATU bentuk — piramida dengan kemiringan
#    yang sama persis. Pada jarak main tekstur 32 px sudah tidak terbaca lagi,
#    jadi kedua puluh varian sampai ke mata sebagai "kerucut". Yang membedakan
#    atap pada jarak itu adalah KEMIRINGAN dan TEPI-nya.
#
# 2. `tint_atap()` menaikkan tint sampai ~0,79 nilai penuh TANPA melihat
#    teksturnya. Ursina mengalikan keduanya, jadi hasil layar ≈ tekstur × 0,79.
#    Untuk tekstur cerah itu benar; untuk `terracotta2` (97,96,112) hasilnya
#    (69,67,86) — dan itulah bidang HITAM di atas Balai Desa pada tangkapan
#    percobaan ronde 2 ini. Sekarang tint dihitung dari rata-rata teksturnya
#    (tint = 255 × warna_layar_yang_diinginkan / rata_rata_tekstur), jadi warna
#    layarnya adalah angka yang ditulis, bukan hasil sampingan.
#
# Empat bahan, dan tiap bahan membawa siluetnya sendiri:
#
#   genteng   piramida sedang, tepi tipis           — rumah bata/plester
#   sirap     piramida landai, tepi lebar menjorok  — papan kayu
#   jerami    piramida curam, tepi tebal            — gubuk/lumbung
#   tumpang   dua piramida bertingkat (joglo)       — bangunan umum desa
#
# Isi tuple: (curam, tebal_tepi, lebar_tepi, [(tekstur, tint), ...])
# `curam` dikali HOUSE_H untuk tinggi puncak; `lebar_tepi` dikali ukuran badan.
# Angka di komentar tiap varian = rata-rata tekstur → warna layar hasil kali.
PROFIL_ATAP = {
    'genteng': (0.60, 0.15, 1.20, [
        ('roof/adobetile',   color.rgb(238, 236, 232)),  # 180,115,83 -> 168,107,76
        ('roof/terracotta1', color.rgb(255, 255, 255)),  # 151, 79,48 -> 151, 79,48
        ('roof/terracotta4', color.rgb(250, 248, 246)),  # 148,127,76 -> 145,123,73
    ]),
    'sirap': (0.42, 0.11, 1.28, [
        ('roof/slate1',        color.rgb(250, 250, 250)),  # 155,145,141 -> 152,142,138
        ('roof/scalloped',     color.rgb(240, 240, 240)),  # 171,157,149 -> 161,148,140
        ('roof/composite_tan', color.rgb(250, 250, 250)),  # 150,134, 97 -> 147,131, 95
    ]),
    'jerami': (0.78, 0.26, 1.26, [
        ('roof/thatch',  color.rgb(255, 255, 255)),   # 185,114,60 -> 185,114,60
        ('roof/thatch3', color.rgb(248, 248, 248)),   # 192,124,58 -> 186,120,56
    ]),
    'tumpang': (0.55, 0.14, 1.22, [
        # scalloped_grey (166,171,185) cukup terang untuk DIREDAM jadi batu tua
        # tanpa pernah jatuh ke hitam — kebalikan dari terracotta2 yang gelap
        # sejak awal dan tidak bisa diselamatkan tint apa pun.
        ('roof/scalloped_grey',         color.rgb(200, 194, 182)),  # -> 130,130,132
        ('roof/fiberglasshoroz_ltgrey', color.rgb(194, 194, 200)),  # -> 131,131,128
    ]),
}


def build_tree(world, wx, wz):
    """Pohon. Dulu ia berdiri di layar sebagai TIANG HITAM, dan itu bug tekstur.

    `tree_trunk.png` rata-ratanya (8,71,38) — hijau tua pekat, bukan kayu —
    dan `tree_leaf.png` (16,23,39) dengan alpha rata-rata 0,15, yaitu hampir
    kosong dan hampir hitam. Keduanya dikalikan tint gelap lagi
    ((100,70,40) untuk batang), jadi hasilnya (3,19,6): hitam.
    Diukur di `_bench/shots/HUD.png` — deretan pilar hitam di tepi kebun.

    Sekarang batangnya memakai `wood_plank` (130,90,56, kayu betulan) dan
    tajuknya `cloth_green` dengan tint yang TIDAK menggelapkan lagi. Tajuknya
    juga dipecah jadi empat gumpalan dengan NILAI berbeda — di patokan, yang
    membuat pohon terbaca sebagai pohon dari jauh adalah sisi atas yang kena
    matahari lebih pucat daripada sisi bawahnya, bukan bentuk daunnya.

    Warna dipilih dari posisi supaya sebaris pohon tidak terlihat di-copy.
    """
    v = abs(math.sin(wx * 17.3 + wz * 29.1))
    trunk = world._create_entity('cylinder', (wx, TREE_H * 0.40, wz),
               (TS * 0.34, TREE_H * 0.80, TS * 0.34), 'wood_plank',
               color.rgb(196 + int(v * 34), 176 + int(v * 30), 158 + int(v * 24)))
    # Tajuk: bawah teduh → atas kena matahari.
    gelap = color.rgb(74 + int(v * 18), 128 + int(v * 22), 62 + int(v * 14))
    sedang = color.rgb(96 + int(v * 20), 158 + int(v * 24), 76 + int(v * 16))
    terang = color.rgb(124 + int(v * 22), 186 + int(v * 20), 96 + int(v * 18))
    leaf1 = world._create_entity('sphere', (wx, TREE_H * 0.96, wz),
               (TS * 1.85, TS * 1.45, TS * 1.85), 'cloth_green', gelap)
    leaf2 = world._create_entity('sphere', (wx + TS*0.26, TREE_H * 1.22, wz - TS*0.22),
               (TS * 1.42, TS * 1.24, TS * 1.42), 'cloth_green', sedang)
    leaf3 = world._create_entity('sphere', (wx - TS*0.24, TREE_H * 1.18, wz + TS*0.26),
               (TS * 1.24, TS * 1.12, TS * 1.24), 'cloth_green', sedang)
    leaf4 = world._create_entity('sphere', (wx + TS*0.05, TREE_H * 1.46, wz + TS*0.02),
               (TS * 1.05, TS * 0.95, TS * 1.05), 'cloth_green', terang)
    world._obj_ents.extend([trunk, leaf1, leaf2, leaf3, leaf4])

def build_palm(world, wx, wz):
    # 'tree_trunk' dilepas di sini karena alasan yang sama seperti di
    # build_tree(): teksturnya (8,71,38) bukan kayu, dan batang pohon kelapa
    # keluar hitam kehijauan.
    trunk = world._create_entity('cylinder', (wx, TREE_H * 0.5, wz),
               (TS * 0.25, TREE_H * 1.1, TS * 0.25), 'wood_plank',
               color.rgb(214, 196, 176), rotation=(5, 0, 8))
    world._obj_ents.append(trunk)
    for i in range(5):
        rad = math.radians(i * 72)
        cx = wx + math.sin(rad) * 0.6
        cz = wz + math.cos(rad) * 0.6
        leaf = world._create_entity('cube', (cx, TREE_H * 1.05 - 0.1, cz),
                  (TS * 0.7, 0.05, TS * 0.3), 'cloth_green',
                  color.rgb(80, 220, 50), rotation=(15, -i * 72 + 90, 0))
        world._obj_ents.append(leaf)
    for i in range(3):
        rad = math.radians(i * 120)
        cx = wx + math.sin(rad) * 0.25
        cz = wz + math.cos(rad) * 0.25
        coconut = world._create_entity('sphere', (cx, TREE_H * 0.95, cz),
                     (0.25, 0.25, 0.25), 'wood_plank', color.rgb(190, 210, 60))
        world._obj_ents.append(coconut)

def build_dead_tree(world, wx, wz):
    """Tunggul kering. Ikut kena bug tekstur yang sama seperti build_tree, dan
    ikut diberi satu cabang — sebatang tiang gundul tidak terbaca sebagai
    apa pun, sementara tiang dengan satu cabang langsung terbaca sebagai
    pohon mati yang menunggu dikapak."""
    v = abs(math.sin(wx * 23.9 - wz * 11.7))
    kayu = color.rgb(150, 132, 116)
    trunk = world._create_entity('cylinder', (wx, TREE_H * 0.36, wz),
               (TS * 0.22, TREE_H * 0.72, TS * 0.22), 'wood_plank', kayu)
    cabang = world._create_entity('cube',
               (wx + TS * 0.20, TREE_H * 0.60, wz - TS * 0.06),
               (TS * 0.44, 0.10, 0.10), 'wood_plank', kayu,
               rotation=(0, v * 90.0, 28))
    world._obj_ents.extend([trunk, cabang])

def build_lantern(world, wx, wz):
    """Tiang lampu jalan. Dulu setinggi 1,08 m — setinggi PINGGANG orang.

    Diukur dari `_bench/shots/DESA.png`: lentera lama tenggelam di rumput dan
    tidak menyumbang satu garis tegak pun ke frame. Di
    `_bench/refs/village_wide.jpg` justru dua tiang lampu besi yang memberi
    kedalaman pada latar depan — keduanya membelah frame secara vertikal dan
    memberi mata skala untuk menilai tinggi orang di belakangnya.

    Empat entity, dan tiga di antaranya membayar garis tegak setinggi 3,2 m.
    """
    besi = color.rgb(96, 96, 104)
    alas = world._create_entity('cylinder', (wx, GROUND_H + 0.14, wz),
              (TS * 0.24, 0.28, TS * 0.24), 'wall_stone', color.rgb(128, 122, 116))
    tiang = world._create_entity('cylinder', (wx, GROUND_H + 1.62, wz),
              (TS * 0.075, 3.24, TS * 0.075), 'metal_grey', besi)
    kepala = world._create_entity('cube', (wx, GROUND_H + 3.42, wz),
              (TS * 0.30, 0.44, TS * 0.30), 'lamp_glow')
    topi = world._create_entity('cube', (wx, GROUND_H + 3.70, wz),
              (TS * 0.38, 0.12, TS * 0.38), 'metal_grey', besi)
    world._obj_ents.extend([alas, tiang, kepala, topi])

def build_ore(world, wx, wz, tex_name='crystal'):
    base = world._create_entity('cube', (wx, WALL_H / 2 + GROUND_H, wz),
              (TS * 0.98, WALL_H, TS * 0.98), 'wall_cave')
    gem  = world._create_entity('cube',
              (wx, WALL_H + GROUND_H + SMALL_OBJ_H * 0.4, wz),
              (TS * 0.45, SMALL_OBJ_H * 0.7, TS * 0.45),
              tex_name, rotation=(30, 45, 15))
    world._obj_ents.extend([base, gem])

def build_fireplace(world, wx, wz):
    base = world._create_entity('cube', (wx, OBJ_H * 0.5 + GROUND_H, wz),
              (TS * 0.85, OBJ_H, TS * 0.85), 'wall_stone', color.rgb(90, 80, 75))
    flame = world._create_entity('sphere', (wx, OBJ_H + GROUND_H + 0.22, wz),
               (TS * 0.40, 0.42, TS * 0.40), 'fire_orange')
    world._obj_ents.extend([base, flame])

def build_grave(world, wx, wz):
    vert  = world._create_entity('cube', (wx, OBJ_H * 0.50 + GROUND_H, wz),
               (TS * 0.16, OBJ_H * 0.90, TS * 0.14), 'grave_stone', color.rgb(112, 100, 122))
    horiz = world._create_entity('cube', (wx, OBJ_H * 0.68 + GROUND_H, wz),
               (TS * 0.52, TS * 0.14, TS * 0.12), 'grave_stone', color.rgb(112, 100, 122))
    world._obj_ents.extend([vert, horiz])

def build_tv(world, wx, wz):
    base = world._create_entity('cube', (wx, OBJ_H*0.2 + GROUND_H, wz), (TS*0.7, OBJ_H*0.4, TS*0.3), 'wood_plank', color.rgb(60,60,60))
    screen = world._create_entity('cube', (wx, OBJ_H*0.7 + GROUND_H, wz), (TS*0.8, OBJ_H*0.6, TS*0.1), None, color.rgb(20,20,30))
    glass = world._create_entity('cube', (wx, OBJ_H*0.7 + GROUND_H, wz - TS*0.06), (TS*0.7, OBJ_H*0.5, 0.05), None, color.rgb(150, 200, 255))
    world._obj_ents.extend([base, screen, glass])

def build_chair(world, wx, wz):
    seat = world._create_entity('cube', (wx, OBJ_H*0.3 + GROUND_H, wz), (TS*0.4, 0.1, TS*0.4), 'wood_plank', color.rgb(130, 90, 50))
    leg1 = world._create_entity('cube', (wx-TS*0.15, OBJ_H*0.15 + GROUND_H, wz-TS*0.15), (0.08, OBJ_H*0.3, 0.08), 'wood_plank', color.rgb(130, 90, 50))
    leg2 = world._create_entity('cube', (wx+TS*0.15, OBJ_H*0.15 + GROUND_H, wz-TS*0.15), (0.08, OBJ_H*0.3, 0.08), 'wood_plank', color.rgb(130, 90, 50))
    leg3 = world._create_entity('cube', (wx-TS*0.15, OBJ_H*0.15 + GROUND_H, wz+TS*0.15), (0.08, OBJ_H*0.3, 0.08), 'wood_plank', color.rgb(130, 90, 50))
    leg4 = world._create_entity('cube', (wx+TS*0.15, OBJ_H*0.15 + GROUND_H, wz+TS*0.15), (0.08, OBJ_H*0.3, 0.08), 'wood_plank', color.rgb(130, 90, 50))
    back = world._create_entity('cube', (wx, OBJ_H*0.65 + GROUND_H, wz+TS*0.15), (TS*0.4, OBJ_H*0.6, 0.08), 'wood_plank', color.rgb(130, 90, 50))
    world._obj_ents.extend([seat, leg1, leg2, leg3, leg4, back])

def build_calendar(world, wx, wz):
    paper = world._create_entity('cube', (wx, WALL_H*0.6 + GROUND_H, wz), (TS*0.4, 0.6, 0.05), None, color.rgb(240, 240, 230))
    bind = world._create_entity('cube', (wx, WALL_H*0.6 + 0.3 + GROUND_H, wz), (TS*0.4, 0.05, 0.07), None, color.rgb(200, 50, 50))
    world._obj_ents.extend([paper, bind])

# ── Bahan dinding ───────────────────────────────────────────────────────────
# Sebelumnya SETIAP rumah di seluruh game punya badan yang sama: tekstur
# `house_wall` dikali (248,235,200). Tekstur itu rata-ratanya (234,220,191),
# jadi hasil kalinya nyaris putih — dan di bawah matahari siang ia terpotong
# jadi putih hangus tanpa tekstur (lihat catatan bahu_sorot di smooth_shader).
# Di layar: sederet kotak krem identik. Di `_bench/refs/village_wide.jpg` tidak
# ada dua bangunan yang sewarna, dan tidak satu pun yang pucat begitu.
#
# Lima bahan, dipilih dari hash posisi. Yang membedakannya NILAI lebih dulu
# (jati jauh lebih tua daripada kapur), corak belakangan — supaya deretan rumah
# terbaca sebagai deretan bangunan berbeda bahkan pada tangkapan hitam-putih.
#
# Isi tuple: (tekstur badan, tint badan, tint alas batu, tint kusen/tiang)
BAHAN_DINDING = (
    # kapur — plester putih kapur desa, tapi DIREDAM sampai bisa dipotret
    ('house_wall',  color.rgb(206, 199, 182), color.rgb(150, 142, 130), color.rgb(122,  92,  62)),
    # jati — papan kayu tua, bahan tergelap dan jangkar nilai deretan
    ('wood_plank',  color.rgb(238, 224, 204), color.rgb(142, 134, 122), color.rgb( 96,  72,  48)),
    # anyaman bambu — kuning jerami hangat
    ('house_wall',  color.rgb(214, 192, 146), color.rgb(148, 140, 126), color.rgb(108,  84,  56)),
    # bata merah
    ('brick_red',   color.rgb(228, 214, 206), color.rgb(146, 138, 128), color.rgb(102,  78,  54)),
    # batu kali diplester separuh
    ('wall_stone',  color.rgb(202, 196, 188), color.rgb(132, 126, 118), color.rgb(112,  86,  58)),
)


def _sisi_pintu(scene, x0, y0, x1, y1):
    """Cari sisi mana yang punya ubin DR — itulah MUKA bangunan.

    Kenapa dicari, bukan ditetapkan: sampai sekarang pintu, teras, tiang, dan
    semua jendela digambar di sisi +z tanpa syarat. Kamera baku permainan
    berdiri di -z dan melihat ke +z (`Game3D._camera_offset()` dengan yaw 0),
    jadi SELURUH hiasan muka setiap bangunan di game ini menghadap menjauhi
    kamera. Itu persis keluhan kritikus ronde 1 tentang potongan DESA — "atap
    ... tidak punya jendela, pintu, atau ornamen" — dan ornamennya memang ada,
    cuma di sisi yang tidak pernah difoto.

    Ubin DR adalah tempat portal berdiri, jadi ia satu-satunya sumber
    kebenaran tentang di sisi mana pintunya: menaruh gambar pintu di sisi lain
    berarti menggambar pintu yang tidak bisa dimasuki.

    Balik ke +z kalau tidak ada DR sama sekali — itu perilaku lama, dan scene
    `farm` bergantung padanya (rumah petani punya teras di selatan tanpa DR).
    """
    for x in range(x0, x1 + 1):
        if scene.tiles[y0][x] == DR:
            return 'utara'
        if scene.tiles[y1][x] == DR:
            return 'selatan'
    for y in range(y0, y1 + 1):
        if scene.tiles[y][x0] == DR:
            return 'barat'
        if scene.tiles[y][x1] == DR:
            return 'timur'
    return 'selatan'


# Vektor keluar tiap sisi, dalam (dx, dz).
_ARAH = {'utara': (0, -1), 'selatan': (0, 1), 'barat': (-1, 0), 'timur': (1, 0)}


def _jendela_sisi(world, cx, cz, sx, sz, sisi, jy, jw, jh, kusen, n, lewati_tengah):
    """Sebaris jendela di satu sisi bangunan.

    `n` jendela dibagi rata sepanjang sisi itu. `lewati_tengah` menyisakan
    ruang untuk pintu — dipakai di sisi muka saja.
    """
    dx, dz = _ARAH[sisi]
    if dx:                      # sisi barat/timur → jendela berjajar pada z
        span, tebal = sz, sx
    else:                       # sisi utara/selatan → berjajar pada x
        span, tebal = sx, sz
    pasang = []
    for k in range(n):
        off = (k - (n - 1) / 2.0) * (span / max(1, n)) * 0.98
        if lewati_tengah and abs(off) < TS * 0.55:
            continue
        if dx:
            px, pz = cx + dx * (tebal * 0.5 + 0.02), cz + off
        else:
            px, pz = cx + off, cz + dz * (tebal * 0.5 + 0.02)
        pasang.append((px, pz))
    for px, pz in pasang:
        frame = world._create_entity('cube', (px, jy, pz),
                   (jw if not dx else 0.09, jh, 0.09 if not dx else jw),
                   'wood_plank', kusen)
        kaca = world._create_entity('cube',
                  (px + dx * 0.055, jy, pz + dz * 0.055),
                  (jw * 0.74 if not dx else 0.05, jh * 0.70,
                   0.05 if not dx else jw * 0.74),
                  None, color.rgb(108, 138, 152))
        world._obj_ents.extend([frame, kaca])


def _bangun_atap(world, cx, cz, sx, sz, alas_y, jenis, tinggi, undian):
    """Atap sebagai BAHAN, bukan sebagai satu bentuk dengan dua puluh corak.

    Lihat PROFIL_ATAP: tiap bahan membawa kemiringan dan tebal tepinya sendiri,
    jadi genteng, sirap, dan jerami masih bisa dibedakan pada jarak di mana
    teksturnya sudah jadi bubur.

    `tumpang` (joglo) menumpuk dua piramida — satu-satunya siluet di sini yang
    tidak bisa disalahartikan sebagai salah satu dari tiga lainnya, jadi ia
    dipakai untuk bangunan umum yang harus terbaca sebagai penanda.
    """
    from ursina.models.procedural.cone import Cone
    curam, tebal, lebar = PROFIL_ATAP[jenis][0:3]
    daftar = PROFIL_ATAP[jenis][3]
    tex, col = daftar[undian % len(daftar)]
    ents = []

    # Tepi atap: pelat datar yang menjorok keluar dinding. Ia yang membuat
    # "kotak dengan topi" berhenti terbaca sebagai kotak — bayangan garis di
    # bawah tepi memberi bangunan satu batas mendatar yang tegas.
    ents.append(world._create_entity(
        'cube', (cx, alas_y + tebal * 0.5, cz),
        (sx * lebar, tebal, sz * lebar), tex, col))

    puncak = HOUSE_H * curam * (0.75 + 0.25 * tinggi)
    y0 = alas_y + tebal
    if jenis == 'tumpang':
        # Tingkat bawah landai dan lebar, tingkat atas curam dan sempit.
        h1 = puncak * 0.46
        ents.append(world._create_entity(
            Cone(resolution=4), (cx, y0 + h1 * 0.5, cz),
            (sx * lebar * 0.99, h1, sz * lebar * 0.99), tex, col,
            rotation=(0, 45, 0)))
        h2 = puncak * 0.86
        ents.append(world._create_entity(
            'cube', (cx, y0 + h1 + 0.07, cz),
            (sx * 0.70, 0.14, sz * 0.70), tex, col))
        ents.append(world._create_entity(
            Cone(resolution=4), (cx, y0 + h1 + 0.14 + h2 * 0.5, cz),
            (sx * 0.72, h2, sz * 0.72), tex, col, rotation=(0, 45, 0)))
    else:
        ents.append(world._create_entity(
            Cone(resolution=4), (cx, y0 + puncak * 0.5, cz),
            (sx * lebar * 0.99, puncak, sz * lebar * 0.99), tex, col,
            rotation=(0, 45, 0)))
    world._obj_ents.extend(ents)
    return tex, col


def build_house_block(world, scene, tx, ty, wx, wz):
    """Satu bangunan dari satu blok ubin H.

    Tiga hal bisa disetel per bangunan lewat `scene.rumah[(tx, ty)]` —
    `atap` (genteng/sirap/jerami/tumpang), `tinggi` (kelipatan satu lantai),
    dan `muka` (utara/selatan/barat/timur). Tanpa entri, semuanya diundi dari
    posisi seperti dulu dan mukanya diambil dari ubin DR.

    Kenapa boleh disetel per bangunan, bukan diundi saja: undian posisi bisa
    memberi dua tetangga bahan yang sama, dan seluruh gunanya deretan rumah
    adalah dua tetangga TIDAK boleh sama. Sebuah frame yang harus memuat empat
    bangunan berbeda tidak boleh bergantung pada nasib.
    """
    # Ubin DR ikut dihitung sebagai bagian blok. Tanpa ini, pintu yang berdiri
    # di tepi UTARA memotong pemindaian lebar di tengah jalan dan bangunan
    # 4x3 dibangun sebagai kotak 1x3.
    def _blok(x, y):
        if not (0 <= y < scene.h and 0 <= x < scene.w):
            return False
        return scene.tiles[y][x] in (H, DR)

    if _blok(tx - 1, ty) or _blok(tx, ty - 1):
        return

    w_tiles = 1
    while _blok(tx + w_tiles, ty):
        w_tiles += 1
    h_tiles = 1
    while _blok(tx, ty + h_tiles):
        h_tiles += 1

    setelan = (getattr(scene, 'rumah', None) or {}).get((tx, ty), {})

    center_x = wx + (w_tiles - 1) * TS / 2.0
    center_z = wz + (h_tiles - 1) * TS / 2.0
    scale_x = TS * w_tiles * 0.94
    scale_z = TS * h_tiles * 0.94

    # Dua undian TERPISAH. Kalau atap dan dinding dipilih dari hash yang sama,
    # tiap bahan dinding selamanya berpasangan dengan satu atap dan jumlah
    # rumah yang benar-benar berbeda tinggal lima.
    h1 = abs(math.sin(wx * 31.7 + wz * 47.3))
    h2 = abs(math.sin(wx * 12.9 - wz * 78.233 + 2.4))
    jenis_atap = setelan.get('atap')
    if jenis_atap not in PROFIL_ATAP:
        jenis_atap = ('genteng', 'sirap', 'jerami')[int(h1 * 3) % 3]
    tinggi = float(setelan.get('tinggi', 1.0))
    muka = setelan.get('muka') or _sisi_pintu(scene, tx, ty,
                                              tx + w_tiles - 1, ty + h_tiles - 1)
    b_tex, b_col, alas_col, kusen = BAHAN_DINDING[
        setelan.get('dinding', int(h2 * len(BAHAN_DINDING))) % len(BAHAN_DINDING)]

    badan_h = HOUSE_H * 0.80 * tinggi
    y_badan = badan_h * 0.5 + GROUND_H
    dx, dz = _ARAH[muka]
    # Jarak dari pusat ke permukaan sisi muka.
    tepi = (scale_x if dx else scale_z) * 0.5

    foundation = world._create_entity('cube', (center_x, GROUND_H + 0.10, center_z),
                    (scale_x * 1.03, 0.20, scale_z * 1.03), 'wall_stone', alas_col)
    body = world._create_entity('cube', (center_x, y_badan, center_z),
              (scale_x, badan_h, scale_z), b_tex, b_col)
    world._obj_ents.extend([foundation, body])

    # ── Muka: pintu, teras, tiang teras ─────────────────────────────────────
    pintu_h = min(HOUSE_H * 0.60, badan_h * 0.66)
    px = center_x + dx * (tepi + 0.02)
    pz = center_z + dz * (tepi + 0.02)
    door = world._create_entity('cube', (px, pintu_h * 0.5 + GROUND_H, pz),
              (TS * 0.8 if not dx else 0.1, pintu_h, 0.1 if not dx else TS * 0.8),
              'wood_plank', color.rgb(100, 60, 30))
    world._obj_ents.append(door)

    atap_y = badan_h + GROUND_H
    r_tex, r_col = _bangun_atap(world, center_x, center_z, scale_x, scale_z,
                                atap_y, jenis_atap, tinggi, int(h1 * 977))

    porch = world._create_entity(
        'cube', (center_x + dx * (tepi + TS * 0.4),
                 min(pintu_h + 0.35, badan_h * 0.92) + GROUND_H,
                 center_z + dz * (tepi + TS * 0.4)),
        (TS * 1.2 if not dx else TS * 0.8, 0.15, TS * 0.8 if not dx else TS * 1.2),
        r_tex, r_col)
    world._obj_ents.append(porch)
    for s in (-1, 1):
        ox = -dz * s * TS * 0.5
        oz = dx * s * TS * 0.5
        world._obj_ents.append(world._create_entity(
            'cylinder',
            (center_x + dx * (tepi + TS * 0.7) + ox,
             min(pintu_h + 0.35, badan_h * 0.92) * 0.5 + GROUND_H,
             center_z + dz * (tepi + TS * 0.7) + oz),
            (0.1, min(pintu_h + 0.35, badan_h * 0.92), 0.1),
            'wood_plank', color.rgb(150, 110, 70)))

    chimney = world._create_entity('cube', (center_x + scale_x * 0.3, atap_y + HOUSE_H * 0.34, center_z - scale_z * 0.2),
                 (TS * 0.2, HOUSE_H * 0.34, TS * 0.2), 'wall_stone', color.rgb(158, 142, 122))
    chimney_cap = world._create_entity('cube', (center_x + scale_x * 0.3, atap_y + HOUSE_H * 0.50, center_z - scale_z * 0.2),
                     (TS * 0.26, 0.08, TS * 0.26), None, color.rgb(90, 80, 72))
    world._obj_ents.extend([chimney, chimney_cap])

    # ── Yang membuat kotak berhenti jadi kotak ──────────────────────────────
    # Tiang sudut dan papan pinggang: dua garis gelap tegak di tiap sudut dan
    # satu pita mendatar setinggi pinggang. Ongkosnya lima entity dan ia
    # menghapus bidang datar terbesar yang tersisa di frame `town`.
    for sx in (-1, 1):
        for sz in (-1, 1):
            world._obj_ents.append(world._create_entity(
                'cube',
                (center_x + sx * scale_x * 0.5, y_badan, center_z + sz * scale_z * 0.5),
                (0.13, badan_h, 0.13), 'wood_plank', kusen))
    # Papan pinggang. Untuk bangunan dua lantai ia jadi papan LANTAI — satu
    # garis mendatar tepat di batas tingkat, dan itulah yang membuat mata
    # menghitungnya sebagai dua lantai, bukan sebagai satu tembok tinggi.
    for frac in ((0.41,) if tinggi < 1.35 else (0.34, 0.66)):
        world._obj_ents.append(world._create_entity(
            'cube', (center_x, GROUND_H + badan_h * frac, center_z),
            (scale_x * 1.012, 0.10, scale_z * 1.012), 'wood_plank', kusen))

    # ── Jendela ─────────────────────────────────────────────────────────────
    # Sisi MUKA dan sisi UTARA. Utara selalu ikut karena kamera baku permainan
    # berdiri di -z: sisi itu yang difoto, dan sebuah dinding tanpa lubang
    # tidak punya skala — begitu ada jendela, mata tahu bangunannya setinggi
    # berapa lantai dibanding orang yang berdiri di depannya.
    jw, jh = TS * 0.46, min(HOUSE_H * 0.30, badan_h * 0.30)
    n_muka = max(2, (w_tiles if not dx else h_tiles))
    sisi_jendela = [(muka, True)]
    if muka != 'utara':
        sisi_jendela.append(('utara', False))
    for sisi, sisakan in sisi_jendela:
        for baris in ((0.52,) if tinggi < 1.35 else (0.24, 0.76)):
            _jendela_sisi(world, center_x, center_z, scale_x, scale_z, sisi,
                          GROUND_H + badan_h * baris, jw, jh, kusen,
                          n_muka, sisakan and baris < 0.6)


# Ubin penghalang yang ubinnya TIDAK diurus benar oleh world.py di luar ruang.
# Cabang `_make_tile()` untuk penghalang memakai `default_tex` = 'grass', dan
# grass.png di repo ini hampir hitam (rata-rata 44,14,46) — jadi tiap pohon,
# tunggul, lentera, dan peti berdiri di atas kotak hitam. Pagar TIDAK ikut
# terdaftar di sini: world.py sudah punya cabang khusus yang memakai
# 'grass_tso' untuk FN/GT/PEN. Dinding dan bangunan juga tidak: massanya
# menutupi ubinnya sendiri.
# Lihat zone_paint.patch_tile() — ini tambalan sementara, bukan perbaikan.
_TILE_TAMBALAN = (TR, PALM, DT, LN, CH, MB, PP, CL, MR, BS, SH, CT, TB, BD,
                  ST, FP, GR, TV, CHR, CAL, BOT, DR)


def default_prop_builder(world, scene):
    from game.world import OBJ_TEX
    from game.scenes.zone_paint import paint_zone, patch_tile

    outdoor = not getattr(scene, 'indoor', False)

    # ── Lapisan zona ────────────────────────────────────────────────────────
    # Dijalankan LEBIH DULU dari prop supaya urutan gambar tanah → prop, dan
    # supaya daftar zona sudah siap dipakai sebagai penyaring tambalan di bawah.
    zones = getattr(scene, 'paint', None) or ()
    for z in zones:
        paint_zone(world, z.x0, z.y0, z.x1, z.y1, z.base, z.light, z.dark)

    # Scan tiles and place complex props
    for ty in range(scene.h):
        for tx in range(scene.w):
            tid = scene.tiles[ty][tx]
            wx, wz = tx * TS, ty * TS

            # Ubin di dalam zona TIDAK ditambal: lapisan zona sudah menutupi
            # kotak hitamnya, dan menambal di sana justru akan menempelkan
            # petak RUMPUT di tengah ladang tanah.
            if outdoor and tid in _TILE_TAMBALAN and \
                    not any(z.covers(tx, ty) for z in zones):
                patch_tile(world, tx, ty)

            if tid == TR: build_tree(world, wx, wz)
            elif tid == PALM: build_palm(world, wx, wz)
            elif tid == DT: build_dead_tree(world, wx, wz)
            elif tid == LN: build_lantern(world, wx, wz)
            elif tid == FP: build_fireplace(world, wx, wz)
            elif tid == GR: build_grave(world, wx, wz)
            elif tid == TV: build_tv(world, wx, wz)
            elif tid == CHR: build_chair(world, wx, wz)
            elif tid == CAL: build_calendar(world, wx, wz)
            elif tid == H: build_house_block(world, scene, tx, ty, wx, wz)
            elif tid in (ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH, CRYS):
                ore_tex = OBJ_TEX.get(tid, 'crystal')
                build_ore(world, wx, wz, ore_tex)
