from game.config import *
from ursina import color
import math

TS = TILE_SIZE

# Roof texture variants
ROOF_TEXTURES = [
    ('roof/terracotta',      color.rgb(215,  88,  68)),
    ('roof/adobetile',       color.rgb(198, 145,  95)),
    ('roof/adobetile_red',   color.rgb(195,  72,  55)),
    ('roof/adobetile_green', color.rgb( 72, 155,  88)),
    ('roof/adobetile_blue',  color.rgb( 72, 105, 188)),
    ('roof/adobetile_gold',  color.rgb(215, 178,  65)),
    ('roof/slate_h',         color.rgb(118, 128, 148)),
    ('roof/composite_green', color.rgb( 78, 128,  88)),
    ('roof/composite_red',   color.rgb(188,  75,  65)),
    ('roof/composite_light', color.rgb(195, 185, 165)),
    ('roof/composite_tan',   color.rgb(188, 155, 108)),
    ('roof/composite_sea',   color.rgb( 85, 155, 155)),
    ('roof/asphaltshingle1', color.rgb(135, 128, 120)),
    ('roof/asphaltshingle3', color.rgb(158, 148, 136)),
    ('roof/conetile_red',    color.rgb(205,  85,  68)),
    ('roof/conetile_green',  color.rgb( 68, 148,  88)),
    ('roof/conetile_blue',   color.rgb( 68,  98, 195)),
    ('roof/metal_h',         color.rgb(148, 158, 165)),
    # Dinaikkan dari (55,52,58). Genteng hitam dikali tekstur gelap lalu dikali
    # pita bayangan menghasilkan bidang HITAM tanpa isi di sisi yang
    # membelakangi matahari — separuh atap tiap rumah yang kebetulan mendapat
    # varian ini. Abu tua masih terbaca sebagai genteng gelap dan masih jadi
    # nilai paling tua di deretan atap, tapi ia masih punya permukaan.
    ('roof/blacktile1',      color.rgb( 96,  92, 100)),
    ('roof/scalloped_h',     color.rgb(218, 108,  75)),
]

def tint_atap(c):
    """Naikkan tint atap sampai ia hampir berhenti menggelapkan teksturnya.

    Tabel di atas memasangkan tiap tekstur atap dengan warna yang KIRA-KIRA
    sama dengan warna rata-rata tekstur itu sendiri — `composite_green`
    (118,138,109) dengan tint (78,128,88), `adobetile` (180,115,83) dengan
    tint (198,145,95), dan seterusnya. Ursina MENGALIKAN keduanya, jadi
    coraknya masuk dua kali dan atap keluar di sekitar seperlima nilai
    teksturnya. Diukur: piksel atap (38,26,8) di layar — praktis hitam — pada
    rumah yang di tabel tercatat bergenteng cokelat terang.

    Aturannya: TEKSTUR membawa corak, TINT membawa nilai. Skala di bawah
    menaikkan tiap tint mendekati putih, tapi tidak sampai menyamakan
    semuanya — varian yang di tabel memang dipilih gelap tetap keluar sebagai
    atap paling tua di deretan.
    """
    m = max(c[0], c[1], c[2]) or 1.0
    target = 0.91 * (0.72 + 0.28 * m)
    k = target / m
    # c[:3] TIDAK boleh dipakai: warna Ursina adalah Vec4 Panda3D dan tidak
    # menerima slice — ia melempar TypeError saat scene dibangun.
    return color.rgb(*[max(0, min(255, int(round(c[i] * k * 255))))
                       for i in (0, 1, 2)])


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
    pole = world._create_entity('cylinder', (wx, OBJ_H * 0.45, wz),
              (TS * 0.08, OBJ_H * 0.90, TS * 0.08), 'wood_plank')
    lamp = world._create_entity('cube', (wx, OBJ_H * 0.95, wz),
              (TS * 0.38, 0.40, TS * 0.38), 'lamp_glow')
    world._obj_ents.extend([pole, lamp])

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


def _jendela(world, cx, cy, cz, lebar, tinggi, arah, kusen):
    """Satu jendela: bingkai gelap + kaca yang memantulkan langit.

    Dua entity, dan ia mengerjakan lebih banyak daripada dua entity mana pun
    lain di bangunan ini: sebuah kotak tanpa lubang tidak punya SKALA. Begitu
    ada jendela, mata tahu rumahnya setinggi berapa lantai dan sebesar apa
    dibanding orang di depannya.

    `arah` = +1 kalau muka jendela menghadap +z, -1 kalau -z.
    """
    frame = world._create_entity('cube', (cx, cy, cz),
               (lebar, tinggi, 0.09), 'wood_plank', kusen)
    kaca = world._create_entity('cube', (cx, cy, cz + arah * 0.055),
              (lebar * 0.74, tinggi * 0.70, 0.05), None, color.rgb(108, 138, 152))
    world._obj_ents.extend([frame, kaca])


def build_house_block(world, scene, tx, ty, wx, wz):
    # Check if this is the top-left of an H block
    left_is_H = tx > 0 and scene.tiles[ty][tx-1] == H
    up_is_H = ty > 0 and scene.tiles[ty-1][tx] == H
    if left_is_H or up_is_H:
        return
    
    w_tiles = 1
    while tx + w_tiles < scene.w and scene.tiles[ty][tx + w_tiles] == H:
        w_tiles += 1
    h_tiles = 1
    while ty + h_tiles < scene.h and scene.tiles[ty + h_tiles][tx] == H:
        h_tiles += 1

    center_x = wx + (w_tiles - 1) * TS / 2.0
    center_z = wz + (h_tiles - 1) * TS / 2.0
    scale_x = TS * w_tiles * 0.94
    scale_z = TS * h_tiles * 0.94

    # Dua undian TERPISAH. Kalau atap dan dinding dipilih dari hash yang sama,
    # tiap bahan dinding selamanya berpasangan dengan satu atap dan jumlah
    # rumah yang benar-benar berbeda tinggal lima.
    h1 = abs(math.sin(wx * 31.7 + wz * 47.3))
    h2 = abs(math.sin(wx * 12.9 - wz * 78.233 + 2.4))
    ri = int(h1 * len(ROOF_TEXTURES)) % len(ROOF_TEXTURES)
    r_tex, r_col = ROOF_TEXTURES[ri]
    r_col = tint_atap(r_col)
    b_tex, b_col, alas_col, kusen = BAHAN_DINDING[int(h2 * len(BAHAN_DINDING))
                                                  % len(BAHAN_DINDING)]

    foundation = world._create_entity('cube', (center_x, GROUND_H + 0.10, center_z),
                    (scale_x * 1.03, 0.20, scale_z * 1.03), 'wall_stone', alas_col)
    body = world._create_entity('cube', (center_x, HOUSE_H * 0.40 + GROUND_H, center_z),
              (scale_x, HOUSE_H * 0.80, scale_z), b_tex, b_col)

    door = world._create_entity('cube', (center_x, HOUSE_H * 0.35 + GROUND_H, center_z + scale_z * 0.5 + 0.02),
              (TS * 0.8, HOUSE_H * 0.6, 0.1), 'wood_plank', color.rgb(100, 60, 30))

    porch = world._create_entity('cube', (center_x, HOUSE_H * 0.65 + GROUND_H, center_z + scale_z * 0.5 + TS * 0.4),
               (TS * 1.2, 0.15, TS * 0.8), r_tex, r_col)

    pillar1 = world._create_entity('cylinder', (center_x - TS*0.5, HOUSE_H * 0.32 + GROUND_H, center_z + scale_z * 0.5 + TS * 0.7),
                 (0.1, HOUSE_H * 0.64, 0.1), 'wood_plank', color.rgb(150, 110, 70))
    pillar2 = world._create_entity('cylinder', (center_x + TS*0.5, HOUSE_H * 0.32 + GROUND_H, center_z + scale_z * 0.5 + TS * 0.7),
                 (0.1, HOUSE_H * 0.64, 0.1), 'wood_plank', color.rgb(150, 110, 70))

    roof_y = HOUSE_H * 0.80 + GROUND_H
    from ursina.models.procedural.cone import Cone
    roof1 = world._create_entity(Cone(resolution=4), (center_x, roof_y + HOUSE_H * 0.45, center_z),
               (scale_x * 1.45, HOUSE_H * 0.90, scale_z * 1.45), r_tex, r_col, rotation=(0, 45, 0))

    chimney = world._create_entity('cube', (center_x + scale_x * 0.3, HOUSE_H * 1.14 + GROUND_H, center_z - scale_z * 0.2),
                 (TS * 0.2, HOUSE_H * 0.34, TS * 0.2), 'wall_stone', color.rgb(158, 142, 122))
    chimney_cap = world._create_entity('cube', (center_x + scale_x * 0.3, HOUSE_H * 1.30 + GROUND_H, center_z - scale_z * 0.2),
                     (TS * 0.26, 0.08, TS * 0.26), None, color.rgb(90, 80, 72))
    world._obj_ents.extend([foundation, body, door, porch, pillar1, pillar2, roof1, chimney, chimney_cap])

    # ── Yang membuat kotak berhenti jadi kotak ──────────────────────────────
    # Tiang sudut dan papan pinggang: dua garis gelap tegak di tiap sudut dan
    # satu pita mendatar setinggi pinggang. Ongkosnya lima entity dan ia
    # menghapus bidang datar terbesar yang tersisa di frame `town`.
    y_badan = HOUSE_H * 0.40 + GROUND_H
    for sx in (-1, 1):
        for sz in (-1, 1):
            world._obj_ents.append(world._create_entity(
                'cube',
                (center_x + sx * scale_x * 0.5, y_badan, center_z + sz * scale_z * 0.5),
                (0.13, HOUSE_H * 0.80, 0.13), 'wood_plank', kusen))
    world._obj_ents.append(world._create_entity(
        'cube', (center_x, GROUND_H + HOUSE_H * 0.33, center_z),
        (scale_x * 1.012, 0.10, scale_z * 1.012), 'wood_plank', kusen))

    # ── Jendela ─────────────────────────────────────────────────────────────
    # Hanya di muka depan (+z) dan sisi kanan (+x): dua sisi itulah yang
    # terlihat dari orbit kamera default, dan jendela di sisi yang tidak pernah
    # terlihat cuma entity yang dibayar tanpa dilihat.
    jw, jh = TS * 0.46, HOUSE_H * 0.30
    jy = GROUND_H + HOUSE_H * 0.50
    zf = center_z + scale_z * 0.5 + 0.02
    for k in range(max(1, w_tiles - 1)):
        jx = center_x + (k - (max(1, w_tiles - 1) - 1) / 2.0) * TS * 1.15
        if abs(jx - center_x) < TS * 0.55:      # ruang pintu, jangan ditimpa
            continue
        _jendela(world, jx, jy, zf, jw, jh, +1, kusen)

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
