"""animal_models.py — Rig hewan desa low-poly, prosedural, berskala meter.

Kenapa modul ini ada: sebelumnya SEMUA hewan di ANIMAL_NPCS dipetakan ke
`humanoid.obj` lewat `entities.get_npc_model_name()` — sapi, ayam, kambing dan
kucing memakai mesh manusia yang sama. Pemilik melaporkannya sebagai "bentuk
binatang juga masih tidak terlihat", dan memang begitu: yang terlihat bukan
hewan.

Aturan bentuk (docs/READABILITY.md §3):
  - Yang membuat hewan terbaca dari kamera lot adalah SILUET dan RASIO UKURAN,
    bukan detail. Ayam = badan bulat kecil + kepala mungil + paruh + baji ekor.
    Kambing = badan kotak + kaki ramping + kepala bertanduk. Detail di bawah
    ~3 cm tidak pernah sampai ke layar, jadi tidak dibuat.
  - Ukuran ditulis dalam METER dan jujur terhadap hewan aslinya; 1 world unit =
    1 meter (WALL_H 2.8, karakter 1.6-1.9 — lihat READABILITY §3.4). Ayam 0,50 m
    di samping sapi 1,45 m harus langsung terbaca beda hanya dari ukuran.
  - Warna diambil dari palet muted dan dipisah lewat NILAI (luminans), bukan
    hue: rumput duduk di L~56, jadi tiap spesies dibuat jelas lebih terang
    (ayam/domba/sapi/kelinci) atau jelas lebih gelap (kambing/kuda/kucing/rubah)
    daripada rumput. Spesies bernilai-terang diberi bagian gelap (muka, kaki,
    belang) supaya tetap punya kontras internal saat kena bayangan cel shader.
  - Palet entitas (teal #3FB3A0, bronze #C79B45, cream glory, pink #E77E9A)
    HARAM dipakai di sini — READABILITY §3.2. Hewan biasa tidak boleh memakai
    kanal warna yang dipegang horor.

PENTING — jebakan mesh berbagi (BRIEF §8.1): Mesh Ursina adalah NodePath
Panda3D dan hanya boleh punya SATU parent. Semua bentuk di sini diambil lewat
getter di game/meshes.py yang sudah mengembalikan `_instance()`, jadi tiap part
memegang salinannya sendiri. Jangan pernah menyimpan hasil `_box()`/`_cone()`
ke variabel lalu memakainya untuk dua Entity.
"""
from ursina import Entity, color

from .meshes import creature_body_mesh, low_cone_mesh
from .smooth_shader import apply_smooth


# ─── PALET ───────────────────────────────────────────────────────────────────
# Muted, dipisah dari rumput lewat luminans (L = .299R+.587G+.114B, skala 0-100).
#
# Batas atas nilai ditahan di ~205, BUKAN 235. Alasannya sama dengan plester
# dinding di world.py:612-618: cel shader di smooth_shader.py menambah cahaya
# di tier terang, jadi warna dasar di atas ~210 terjepit jadi putih rata dan
# semua bentuk di dalamnya (belang sapi, muka domba, lipatan bulu) hilang.
# Diukur langsung di _bench/shots/ANIM_parade_profile.png ronde 1: badan sapi
# rgb(226,220,208) tampil sebagai gumpalan putih tanpa volume.
_C = {
    'bulu_krem':   color.rgb(203, 190, 158),   # L 75 — ayam
    'bulu_putih':  color.rgb(205, 203, 194),   # L 79 — bebek
    'jengger':     color.rgb(172,  58,  54),   # L 34 — jengger & pial ayam
    'paruh':       color.rgb(212, 144,  50),   # L 59 — paruh/kaki unggas
    'kepala_gelap':color.rgb( 62,  58,  52),   # L 23 — kepala bebek, muka domba
    'wol':         color.rgb(201, 194, 172),   # L 76 — bulu domba
    'kambing':     color.rgb(112,  88,  66),   # L 36 — badan kambing
    'tanduk':      color.rgb(186, 176, 150),   # L 69 — tanduk & kuku
    'sapi_terang': color.rgb(202, 196, 184),   # L 77 — badan sapi
    'sapi_belang': color.rgb( 52,  46,  44),   # L 19 — belang sapi
    'moncong':     color.rgb(178, 136, 132),   # L 57 — moncong sapi (S 26%, jauh
                                               #        dari flesh pink entitas)
    'kuda':        color.rgb(122,  78,  52),   # L 35 — badan kuda
    'surai':       color.rgb( 44,  34,  28),   # L 14 — surai & ekor kuda
    'kucing':      color.rgb(158,  88,  42),   # L 41 — kucing oren
    'rubah':       color.rgb(178,  96,  44),   # L 45 — rubah
    'kaki_hitam':  color.rgb( 40,  34,  32),   # L 14 — kaki rubah, kuku kambing
    'putih':       color.rgb(206, 202, 194),   # L 79 — dada/ujung ekor
    'kelinci':     color.rgb(196, 190, 180),   # L 74 — kelinci
    'telinga_dlm': color.rgb(180, 138, 134),   # L 58 — dalam telinga kelinci
    'hidung':      color.rgb( 46,  40,  40),   # L 16 — hidung/mata
}


# ─── PRIMITIF ────────────────────────────────────────────────────────────────
def _box(parent, pos, scale, col, rot=(0, 0, 0)):
    """Kotak bersudut bevel. `scale` = ukuran penuh dalam meter."""
    e = Entity(parent=parent, model=creature_body_mesh(),
               position=pos, scale=scale, rotation=rot, color=col)
    apply_smooth(e)
    return e


def _cone(parent, pos, scale, col, rot=(0, 0, 0)):
    """Kerucut 8 sisi; puncak ke +Y sebelum dirotasi. Untuk paruh/tanduk/telinga."""
    e = Entity(parent=parent, model=low_cone_mesh(),
               position=pos, scale=scale, rotation=rot, color=col)
    apply_smooth(e)
    return e


def _legs(parent, col, x, z, top_y, h, thick):
    """Empat kaki simetris. Kaki tipis adalah separuh siluet hewan berkuku —
    tanpa itu badan kotak terbaca sebagai peti, bukan binatang."""
    out = []
    for sx in (-x, x):
        for sz in (-z, z):
            out.append(_box(parent, (sx, top_y - h * 0.5, sz), (thick, h, thick), col))
    return out


def _shadow(parent, w, d):
    """Bayangan kontak (READABILITY §3.5). Tanpa ini, di proyeksi miring hewan
    kecil terlihat melayang dan mata tidak tahu ia berdiri di tile mana."""
    return Entity(parent=parent, model='circle', rotation_x=90,
                  position=(0, 0.02, 0), scale=(w, d, 1),
                  color=color.rgba(0, 0, 0, 105),
                  unlit=True, transparent=True, double_sided=True)


# ─── SPESIES ─────────────────────────────────────────────────────────────────
# Tiap builder membangun hewan menghadap +Z (rotation_y = 0 di base_actor
# berarti menghadap +Z), berdiri di y = 0, dan mengembalikan tinggi total meter.

def _ayam(r):
    """Ayam jago — 0,63 m sampai ujung jengger, panjang 0,36 m.

    Ronde 1 badannya menempel tanah dan hilang di tekstur rumput yang ramai.
    Kaki dinaikkan ke 0,18 m dan ekor dibuat baji tegak: pada ~30 px yang
    sampai ke mata pemain cuma tiga hal — badan bulat, ekor menjulang ke
    belakang-atas, dan jengger merah kecil di puncak. Itu saja sudah cukup."""
    _shadow(r, 0.40, 0.44)
    for sx in (-0.075, 0.075):                                            # kaki
        _box(r, (sx, 0.09, 0.01), (0.04, 0.18, 0.04), _C['paruh'])
        _box(r, (sx, 0.015, 0.05), (0.06, 0.03, 0.11), _C['paruh'])       # cakar
    _box(r,  (0, 0.31,  0.00), (0.22, 0.25, 0.30), _C['bulu_krem'])       # badan
    _box(r,  (0, 0.44, -0.16), (0.15, 0.21, 0.13), _C['bulu_krem'], (-48, 0, 0))  # ekor
    _box(r,  (0, 0.40,  0.09), (0.11, 0.15, 0.11), _C['bulu_krem'])       # leher
    _box(r,  (0, 0.49,  0.10), (0.16, 0.15, 0.16), _C['bulu_krem'])       # kepala
    _box(r,  (0, 0.585, 0.09), (0.035, 0.09, 0.12), _C['jengger'])        # jengger
    _box(r,  (0, 0.425, 0.16), (0.045, 0.08, 0.035), _C['jengger'])       # pial
    _cone(r, (0, 0.485, 0.20), (0.065, 0.10, 0.065), _C['paruh'], (90, 0, 0))
    return 0.63


def _bebek(r):
    """Bebek — 0,60 m, panjang 0,48 m. Beda dari ayam lewat paruh LEBAR pipih,
    leher tegak panjang, kepala gelap, dan badan yang lebih memanjang rendah.
    Kontras kepala-gelap di atas badan terang itulah tanda bacanya dari jauh."""
    _shadow(r, 0.42, 0.52)
    for sx in (-0.07, 0.07):                                              # kaki
        _box(r, (sx, 0.065, 0.02), (0.045, 0.13, 0.045), _C['paruh'])
        _box(r, (sx, 0.015, 0.08), (0.08, 0.03, 0.14), _C['paruh'])       # selaput
    _box(r,  (0, 0.26,  0.00), (0.24, 0.22, 0.38), _C['bulu_putih'])      # badan
    _box(r,  (0, 0.32, -0.22), (0.14, 0.11, 0.17), _C['bulu_putih'], (-26, 0, 0))
    _box(r,  (0, 0.41,  0.11), (0.12, 0.24, 0.12), _C['kepala_gelap'])    # leher
    _box(r,  (0, 0.53,  0.13), (0.16, 0.15, 0.18), _C['kepala_gelap'])    # kepala
    _box(r,  (0, 0.505, 0.26), (0.14, 0.055, 0.16), _C['paruh'])          # paruh pipih
    return 0.60


def _kucing(r):
    """Kucing — 0,70 m sampai ujung ekor, panjang badan 0,55 m.

    Ronde 1 ekornya nyaris mendatar dan hewannya terbaca seperti roti. Ekor
    kini hampir TEGAK: satu garis vertikal di belakang badan rendah adalah
    tanda kucing yang paling murah dan paling terbaca di siluet sekecil ini."""
    _shadow(r, 0.32, 0.56)
    _legs(r, _C['kucing'], 0.08, 0.14, 0.21, 0.21, 0.065)
    for sz in (-0.14, 0.14):
        for sx in (-0.08, 0.08):
            _box(r, (sx, 0.03, sz), (0.075, 0.06, 0.10), _C['putih'])     # kaus kaki
    _box(r,  (0, 0.31,  0.00), (0.18, 0.18, 0.38), _C['kucing'])          # badan
    _box(r,  (0, 0.25,  0.19), (0.15, 0.12, 0.12), _C['putih'])           # dada putih
    _box(r,  (0, 0.42,  0.25), (0.18, 0.17, 0.16), _C['kucing'])          # kepala
    _box(r,  (0, 0.39,  0.33), (0.11, 0.09, 0.07), _C['putih'])           # moncong
    _box(r,  (0, 0.405, 0.375),(0.045, 0.04, 0.035), _C['hidung'])
    for sx in (-0.06, 0.06):
        _cone(r, (sx, 0.535, 0.245), (0.075, 0.12, 0.055), _C['kucing'])  # telinga
    _box(r,  (0, 0.50, -0.24), (0.08, 0.34, 0.08), _C['kucing'], (-14, 0, 0))
    _box(r,  (0, 0.665, -0.28), (0.075, 0.11, 0.075), _C['putih'])        # ujung ekor
    return 0.70


def _kelinci(r):
    """Kelinci — 0,70 m sampai ujung telinga, panjang 0,38 m.

    Ronde 1 telinganya terlalu tipis dan hilang di antara rumput. Sekarang
    telinga dibuat 0,08 x 0,28 m — dua batang tegak kembar di atas badan
    membungkuk; tidak ada hewan lain di desa ini yang punya siluet itu."""
    _shadow(r, 0.32, 0.40)
    for sx in (-0.09, 0.09):
        _box(r, (sx, 0.07,  0.13), (0.06, 0.14, 0.065), _C['kelinci'])    # kaki depan
        _box(r, (sx, 0.075, -0.09),(0.085, 0.15, 0.18), _C['kelinci'])    # kaki belakang
    _box(r,  (0, 0.24,  0.02), (0.19, 0.22, 0.28), _C['kelinci'])         # badan
    _box(r,  (0, 0.28, -0.10), (0.21, 0.25, 0.19), _C['kelinci'])         # pinggul
    _box(r,  (0, 0.37,  0.16), (0.16, 0.16, 0.17), _C['kelinci'])         # kepala
    _box(r,  (0, 0.34,  0.25), (0.10, 0.09, 0.07), _C['kelinci'])
    _box(r,  (0, 0.35,  0.285),(0.045, 0.04, 0.035), _C['telinga_dlm'])   # hidung
    for sx in (-0.055, 0.055):
        _box(r, (sx, 0.575, 0.12), (0.08, 0.30, 0.045), _C['kelinci'], (-12, 0, 0))
        _box(r, (sx, 0.575, 0.095),(0.042, 0.23, 0.025), _C['telinga_dlm'], (-12, 0, 0))
    _box(r,  (0, 0.27, -0.21), (0.11, 0.11, 0.10), _C['putih'])           # ekor
    return 0.70


def _rubah(r):
    """Rubah — 0,72 m, panjang 0,74 m. Dibedakan dari kucing lewat moncong
    runcing panjang, kaki hitam sampai lutut, dan ekor tebal MENDATAR berujung
    putih — kebalikan persis dari ekor tegak kucing, disengaja."""
    _shadow(r, 0.36, 0.74)
    _legs(r, _C['kaki_hitam'], 0.10, 0.18, 0.26, 0.26, 0.075)
    _box(r,  (0, 0.36,  0.00), (0.22, 0.21, 0.46), _C['rubah'])           # badan
    _box(r,  (0, 0.31,  0.20), (0.18, 0.14, 0.18), _C['putih'])           # dada
    _box(r,  (0, 0.48,  0.31), (0.20, 0.19, 0.19), _C['rubah'])           # kepala
    _cone(r, (0, 0.44,  0.45), (0.115, 0.19, 0.115), _C['rubah'], (90, 0, 0))
    _box(r,  (0, 0.445, 0.535),(0.055, 0.045, 0.045), _C['hidung'])
    for sx in (-0.08, 0.08):
        _cone(r, (sx, 0.62, 0.30), (0.095, 0.16, 0.065), _C['rubah'])     # telinga
        _box(r,  (sx * 1.35, 0.45, 0.32), (0.055, 0.11, 0.11), _C['putih'])  # pipi
    _box(r,  (0, 0.38, -0.36), (0.18, 0.18, 0.36), _C['rubah'], (-12, 0, 0))
    _box(r,  (0, 0.34, -0.54), (0.15, 0.15, 0.13), _C['putih'])           # ujung ekor
    return 0.72


def _kambing(r):
    """Kambing — 1,02 m sampai ujung tanduk, panjang 1,00 m. Siluet: badan
    kotak di atas kaki ramping, kepala bertanduk melengkung ke belakang,
    ditambah jenggot — itulah yang memisahkannya dari domba pada jarak jauh."""
    _shadow(r, 0.50, 1.00)
    _box(r,  (0, 0.56,  0.00), (0.31, 0.35, 0.72), _C['kambing'])         # badan
    _box(r,  (0, 0.69,  0.34), (0.19, 0.24, 0.22), _C['kambing'], (-28, 0, 0))
    _box(r,  (0, 0.81,  0.47), (0.20, 0.20, 0.31), _C['kambing'])         # kepala
    _box(r,  (0, 0.76,  0.62), (0.14, 0.12, 0.09), _C['tanduk'])          # moncong
    _box(r,  (0, 0.70,  0.55), (0.07, 0.15, 0.06), _C['tanduk'], (22, 0, 0))  # jenggot
    for sx in (-0.07, 0.07):
        _cone(r, (sx, 0.97, 0.38), (0.085, 0.31, 0.085), _C['tanduk'], (-46, 0, 0))
        _box(r, (sx * 2.0, 0.84, 0.42), (0.15, 0.05, 0.10), _C['kambing'],
             (0, 0, -26 if sx < 0 else 26))                               # telinga
    _box(r,  (0, 0.64, -0.38), (0.08, 0.14, 0.08), _C['kambing'], (28, 0, 0))
    _legs(r, _C['kambing'], 0.135, 0.245, 0.40, 0.40, 0.09)
    for sx in (-0.135, 0.135):
        for sz in (-0.245, 0.245):
            _box(r, (sx, 0.03, sz), (0.10, 0.06, 0.11), _C['kaki_hitam'])  # kuku
    return 1.02


def _domba(r):
    """Domba — 0,86 m, panjang 1,00 m. Sengaja sekelas ukuran dengan kambing;
    yang memisahkan keduanya adalah KONTRAS INTERNAL — bulu krem tebal dengan
    muka dan kaki nyaris hitam, terbaca bahkan dalam grayscale (checklist §10)."""
    _shadow(r, 0.58, 1.00)
    _box(r,  (0, 0.55,  0.00), (0.46, 0.44, 0.78), _C['wol'])             # badan berbulu
    _box(r,  (0, 0.74,  0.02), (0.39, 0.22, 0.62), _C['wol'])             # punuk bulu
    _box(r,  (0, 0.66,  0.38), (0.20, 0.22, 0.24), _C['wol'])             # leher berbulu
    _box(r,  (0, 0.70,  0.50), (0.19, 0.21, 0.26), _C['kepala_gelap'])    # muka gelap
    _box(r,  (0, 0.65,  0.62), (0.13, 0.12, 0.09), _C['kepala_gelap'])
    for sx in (-0.135, 0.135):
        _box(r, (sx, 0.745, 0.46), (0.15, 0.05, 0.10), _C['kepala_gelap'],
             (0, 0, -22 if sx < 0 else 22))                               # telinga
    _box(r,  (0, 0.60, -0.40), (0.11, 0.11, 0.10), _C['wol'])             # ekor pendek
    _legs(r, _C['kepala_gelap'], 0.155, 0.245, 0.36, 0.36, 0.085)
    return 0.86


def _sapi(r):
    """Sapi — 1,45 m sampai kepala, panjang 2,00 m, lebar 0,72 m. Ini hewan
    terbesar di kandang dan harus terbaca sebagai itu dari ukuran saja: 2,9x
    tinggi ayam dan 5,9x panjangnya. Belang gelap dipasang di kedua sisi badan
    supaya tidak hilang menjadi gumpalan putih di rumput terang."""
    _shadow(r, 0.95, 2.00)
    _box(r,  (0, 1.00,  0.00), (0.72, 0.74, 1.36), _C['sapi_terang'])     # badan
    _box(r,  (0, 1.10,  0.74), (0.46, 0.48, 0.34), _C['sapi_terang'])     # leher
    _box(r,  (0, 1.06,  1.02), (0.38, 0.38, 0.46), _C['sapi_terang'])     # kepala
    _box(r,  (0, 0.98,  1.28), (0.30, 0.24, 0.14), _C['moncong'])         # moncong
    for sx in (-0.185, 0.185):
        _cone(r, (sx, 1.28, 0.94), (0.08, 0.18, 0.08), _C['tanduk'],
              (0, 0, -58 if sx < 0 else 58))                              # tanduk
        _box(r, (sx * 1.45, 1.17, 0.94), (0.21, 0.07, 0.13), _C['sapi_terang'],
             (0, 0, -20 if sx < 0 else 20))                               # telinga
    for sx in (-0.365, 0.365):                                            # belang
        _box(r, (sx, 1.16,  0.34), (0.06, 0.34, 0.44), _C['sapi_belang'])
        _box(r, (sx, 0.88, -0.34), (0.06, 0.40, 0.36), _C['sapi_belang'])
    # Belang punggung dibuat lebih terang daripada belang sisi: dari kamera
    # miring bidang atas hampir tegak lurus pandangan, dan warna L 19 di situ
    # terbaca sebagai LUBANG di badan sapi, bukan sebagai corak.
    _box(r,  (0, 1.365, -0.16), (0.34, 0.05, 0.44), color.rgb(92, 84, 78))
    _box(r,  (0, 0.62, -0.28), (0.30, 0.24, 0.32), _C['moncong'])         # ambing
    _box(r,  (0, 1.02, -0.72), (0.09, 0.56, 0.09), _C['sapi_terang'], (16, 0, 0))
    _box(r,  (0, 0.72, -0.80), (0.10, 0.16, 0.10), _C['sapi_belang'])     # jumbai ekor
    _legs(r, _C['sapi_terang'], 0.265, 0.47, 0.66, 0.66, 0.17)
    for sx in (-0.265, 0.265):
        for sz in (-0.47, 0.47):
            _box(r, (sx, 0.05, sz), (0.19, 0.10, 0.20), _C['sapi_belang'])  # kuku
    return 1.46


def _kuda(r):
    """Kuda — 1,90 m sampai telinga, panjang 2,10 m. Yang membuatnya bukan sapi
    adalah leher panjang menanjak + kepala sempit memanjang + kaki jauh lebih
    tinggi; badan justru dibuat lebih ramping daripada sapi."""
    _shadow(r, 0.80, 2.10)
    _box(r,  (0, 1.22,  0.00), (0.58, 0.68, 1.30), _C['kuda'])            # badan
    # Leher dan kepala sengaja dibuat tumpang tindih tebal. Ronde 1 keduanya
    # hanya bersentuhan di ujung dan dari kamera lot terlihat sebagai dua bongkah
    # terpisah dengan celah — leher terputus itu justru merusak satu-satunya
    # tanda yang membedakan kuda dari sapi.
    _box(r,  (0, 1.44,  0.56), (0.36, 0.76, 0.40), _C['kuda'], (-30, 0, 0))  # leher
    _box(r,  (0, 1.46,  0.42), (0.13, 0.74, 0.22), _C['surai'], (-30, 0, 0))  # surai
    _box(r,  (0, 1.70,  0.84), (0.27, 0.32, 0.56), _C['kuda'], (26, 0, 0))   # kepala
    _box(r,  (0, 1.55,  1.04), (0.23, 0.21, 0.20), _C['kuda'])            # pipi/moncong
    _box(r,  (0, 1.50,  1.13), (0.19, 0.13, 0.10), _C['surai'])           # ujung moncong
    for sx in (-0.09, 0.09):
        _cone(r, (sx, 1.90, 0.76), (0.085, 0.15, 0.065), _C['kuda'], (-14, 0, 0))
    _box(r,  (0, 1.12, -0.70), (0.15, 0.62, 0.15), _C['surai'], (22, 0, 0))  # ekor
    _legs(r, _C['kuda'], 0.225, 0.48, 0.90, 0.90, 0.14)
    for sx in (-0.225, 0.225):
        for sz in (-0.48, 0.48):
            _box(r, (sx, 0.05, sz), (0.16, 0.10, 0.17), _C['surai'])      # kuku
    return 1.90


_BUILDERS = {
    'ayam':    _ayam,
    'bebek':   _bebek,
    'kucing':  _kucing,
    'kelinci': _kelinci,
    'rubah':   _rubah,
    'kambing': _kambing,
    'domba':   _domba,
    'sapi':    _sapi,
    'kuda':    _kuda,
}

# Tinggi total tiap spesies dalam meter — dipakai entities.py untuk menaruh
# nameplate tepat di atas hewan, bukan di ketinggian manusia.
HEIGHTS = {
    'ayam': 0.63, 'bebek': 0.60, 'kucing': 0.70, 'kelinci': 0.70,
    'rubah': 0.72, 'kambing': 1.02, 'domba': 0.86, 'sapi': 1.46, 'kuda': 1.90,
}


def build_animal(parent, species: str) -> float:
    """Pasang rig hewan `species` sebagai anak `parent`. Return tinggi meter.

    Spesies tak dikenal jatuh ke kambing — bentuk berkaki empat generik masih
    terbaca sebagai hewan, sedangkan mesh manusia (perilaku lama) tidak.
    """
    fn = _BUILDERS.get(species, _kambing)
    return fn(parent)
