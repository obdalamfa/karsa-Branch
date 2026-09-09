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
            kaki = _box(parent, (sx, top_y - h * 0.5, sz), (thick, h, thick), col)
            # Sumbu putar kaki ada di PANGKALnya, bukan di tengah. Tanpa ini
            # mengayunkan kaki memutarnya di titik tengah dan telapaknya
            # menembus tanah setengah langkah sekali.
            kaki.origin_y = 0.5
            kaki.y = top_y
            out.append(kaki)
    # Kaki disimpan di akar hewan supaya ada yang bisa mengayunkannya.
    # `_walk_t` sudah dihitung BaseActor sejak lama dan tidak pernah dibaca
    # siapa pun: hewan berjalan dengan keempat kakinya kaku, meluncur di atas
    # tanah. Patokan menuntut kaki kuda mengayun, dan itu tidak mungkin selama
    # kakinya bahkan tidak bisa ditemukan dari luar.
    if not hasattr(parent, '_kaki'):
        parent._kaki = []
    parent._kaki.extend(out)
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


# ── Entitas LIAR, digabung dari feature/3d-mobs ────────────────────────────
#
# Kedua sisi menyentuh berkas ini tapi nyaris tidak beririsan: sisi visual
# membangun HEWAN TERNAK (dan menyimpan kakinya supaya bisa diayun), sisi
# 3d-mobs membangun ENTITAS LIAR yang dipetik pemain — kunang-kunang, jamur,
# mandrake, beri, herbal. `entities.py` sisi 3d-mobs memanggil
# `build_wild_entity()` dan `update_anim_wild()`, jadi membuang blok ini akan
# mematikan seluruh sistem entitas liar, bukan sekadar menghilangkan model.

def get_animal_model_file(animal_type: str):
    """Return nama model aset bila tersedia, else None."""
    for ext in ('.glb', '.obj'):
        if (_MODELS_DIR / f'animal_{animal_type}{ext}').exists():
            return f'animal_{animal_type}'
    return None

def _c(r, g, b):
    return color.rgb(r, g, b)

def _soft_cube():
    from .meshes import soft_cube_mesh
    return soft_cube_mesh()

def build_wild_entity(actor, kind: str):
    """Rakit entitas liar cute sebagai child-parts pada `actor`."""
    from .smooth_shader import apply_smooth
    parts = []
    actor.model  = 'cube'
    actor.color  = color.clear
    actor.scale  = _WILD_SCALES.get(kind, 0.50)

    def part(model, pos, scale, c, **kw):
        e = Entity(parent=actor, model=model, position=pos, scale=scale, color=c, **kw)
        apply_smooth(e, has_texture=False)
        parts.append(e)
        return e

    sc = _soft_cube()

    if   kind == 'running_mushroom': _build_mushroom(part, sc)
    elif kind == 'firefly':          _build_firefly(part, sc)
    elif kind == 'mandrake':         _build_mandrake(part, sc)
    elif kind == 'wild_herb':        _build_wild_herb(part, sc)
    elif kind == 'wild_berry':       _build_wild_berry(part, sc)

    actor._wild_parts = parts
    return parts

def _build_mushroom(part, sc):
    """Jamur berlari chibi — topi merah bintik putih, wajah lucu di tangkai."""
    # Tangkai putih gemuk
    part(sc, (0, 0.22, 0), (0.24, 0.44, 0.24), _c(248, 242, 232))
    # Topi merah besar
    part(sc, (0, 0.52, 0), (0.62, 0.40, 0.62), _c(222, 62, 52))
    # Pinggiran topi (putih)
    part(sc, (0, 0.34, 0), (0.72, 0.10, 0.68), _c(248, 244, 238))
    # Bintik putih topi (5)
    for ox, oz, sz in ((0.14, 0.14, 0.11), (-0.16, 0.08, 0.09),
                       (0.06, -0.18, 0.10), (-0.04, 0.18, 0.08), (0.20, -0.06, 0.08)):
        part(sc, (ox, 0.58, oz + 0.32), (sz, 0.06, sz * 0.5), _c(255, 252, 248))
    # Mata chibi di tangkai
    for sx in (-1, 1):
        ex = sx * 0.08
        part('sphere', (ex,            0.28,  0.14), (0.09, 0.09, 0.05), _EYE_W)
        part('sphere', (ex,            0.28,  0.152), (0.068, 0.068, 0.04), _c(62, 168, 75))
        part('sphere', (ex,            0.28,  0.162), (0.042, 0.042, 0.04), _EYE_PU)
        part('sphere', (ex+sx*0.025,   0.302, 0.170), (0.025, 0.025, 0.02), _EYE_W)
    # Pipi blush
    for sx in (-1, 1):
        part(sc, (sx*0.12, 0.24, 0.12), (0.10, 0.06, 0.04), _BLUSH)
    # Senyum
    part(sc, (0, 0.21, 0.14), (0.09, 0.025, 0.025), _c(175, 78, 78))
    # Kaki kecil (2)
    for sx in (-1, 1):
        part(sc, (sx*0.10, 0.05, 0.02), (0.10, 0.12, 0.10), _c(238, 228, 215))

def _build_firefly(part, sc):
    """Kunang-kunang chibi — tubuh hijau-kuning berkilau, sayap transparan."""
    # Tubuh oval kuning-hijau berkilau
    part(sc, (0, 0.28, 0), (0.28, 0.22, 0.22), _c(185, 228, 78))
    # Lingkaran cahaya (glow — solid warna lebih terang)
    part(sc, (0, 0.28, 0), (0.48, 0.38, 0.38), _c(225, 255, 140))
    # Kepala kuning cerah
    part(sc, (0, 0.44, 0), (0.22, 0.20, 0.20), _c(232, 248, 102))
    # Mata besar bulat
    for sx in (-1, 1):
        ex = sx * 0.07
        part('sphere', (ex,           0.46,  0.12), (0.088, 0.088, 0.05), _EYE_W)
        part('sphere', (ex,           0.46,  0.132),(0.065, 0.065, 0.04), _c(30, 160, 65))
        part('sphere', (ex,           0.46,  0.142),(0.040, 0.040, 0.03), _EYE_PU)
        part('sphere', (ex+sx*0.022,  0.476, 0.150),(0.024, 0.024, 0.02), _EYE_W)
    # Pipi kuning terang
    for sx in (-1, 1):
        part(sc, (sx*0.10, 0.44, 0.10), (0.08, 0.05, 0.03), _c(255, 232, 100))
    # Senyum kecil
    part(sc, (0, 0.43, 0.12), (0.07, 0.022, 0.022), _c(80, 150, 55))
    # Sayap (2 pasang kecil)
    for sx in (-1, 1):
        part(sc, (sx*0.28, 0.36, 0.00), (0.20, 0.12, 0.32), _c(215, 248, 205),
             rotation=(0, sx*28, 0))
        part(sc, (sx*0.24, 0.28, 0.02), (0.16, 0.08, 0.22), _c(228, 255, 185),
             rotation=(0, sx*22, 12))
    # Antena (2)
    for sx in (-1, 1):
        part(sc, (sx*0.07, 0.58, 0.04), (0.025, 0.16, 0.025), _c(155, 195, 68),
             rotation=(0, 0, sx*-25))
        part('sphere', (sx*0.10, 0.66, 0.04), (0.065, 0.065, 0.065), _c(248, 255, 108))

def _build_mandrake(part, sc):
    """Mandrake chibi — akar gemuk coklat, wajah teriak lucu, mahkota daun hijau."""
    # Akar tubuh coklat bulat
    part(sc, (0, 0.28, 0), (0.44, 0.56, 0.44), _c(185, 148, 100))
    # Garis tekstur akar
    part(sc, (0, 0.18, 0.23), (0.38, 0.42, 0.04), _c(165, 128, 82))
    # Kaki-akar (2 tonjolan bawah)
    for sx in (-1, 1):
        part(sc, (sx*0.14, 0.06, 0.02), (0.14, 0.18, 0.14), _c(158, 122, 80))
    # Kepala bulat hijau
    part(sc, (0, 0.65, 0), (0.46, 0.46, 0.46), _c(145, 188, 112))
    # Mata melotot besar (mandrake kaget)
    for sx in (-1, 1):
        ex = sx * 0.12
        part('sphere', (ex,           0.70,  0.24), (0.115, 0.115, 0.06), _EYE_W)
        part('sphere', (ex,           0.70,  0.255),(0.086, 0.086, 0.05), _c(48, 138, 58))
        part('sphere', (ex,           0.70,  0.268),(0.055, 0.055, 0.04), _EYE_PU)
        part('sphere', (ex+sx*0.032,  0.720, 0.278),(0.026, 0.026, 0.025),_EYE_W)
    # Mulut terbuka teriak
    part(sc, (0, 0.61, 0.24), (0.22, 0.18, 0.05), _c(22, 18, 22))
    part(sc, (0, 0.61, 0.245),(0.14, 0.08, 0.04), _c(185, 72, 72))
    # Pipi
    for sx in (-1, 1):
        part(sc, (sx*0.18, 0.64, 0.22), (0.12, 0.07, 0.04), _BLUSH)
    # Tangan kecil (opsional, ekspresi dramatis)
    for sx in (-1, 1):
        part(sc, (sx*0.30, 0.42, 0.10), (0.10, 0.08, 0.10), _c(158, 122, 80),
             rotation=(0, 0, sx*55))
    # Daun mahkota di atas (4 daun berbeda)
    for ox, rot_y, sz in ((0.00, 0, 0.26), (-0.15, -38, 0.20), (0.14, 32, 0.18), (0.02, 15, 0.15)):
        part(sc, (ox, 0.95, 0.04), (sz, sz*1.75, sz*0.12),
             _c(82, 162, 68), rotation=(0, rot_y, 0))

def _build_wild_herb(part, sc):
    """Herba liar chibi — gundukan hijau segar, daun memancar, wajah kecil."""
    # Gundukan tanah
    part(sc, (0, 0.07, 0), (0.44, 0.14, 0.44), _c(132, 105, 72))
    # Batang utama
    part(sc, (0, 0.26, 0), (0.07, 0.32, 0.07), _c(85, 158, 68))
    # 6 daun memancar ke berbagai arah
    leaf_data = [
        ( 0.20,  0.00,  22,  15, 0.16),
        (-0.20,  0.00, -22, -15, 0.16),
        ( 0.00,  0.22,   0,  12, 0.18),
        ( 0.14, -0.14,  45, -10, 0.14),
        (-0.14, -0.14, -45,  10, 0.14),
        ( 0.08,  0.16,  12,  -8, 0.13),
    ]
    for ox, oz, ry, rz, sz in leaf_data:
        g = int(165 + abs(ox) * 25)
        part(sc, (ox, 0.38, oz), (sz, sz*2.0, sz*0.11),
             _c(62, g, 55), rotation=(0, ry, rz))
    # Wajah di batang
    for sx in (-1, 1):
        part('sphere', (sx*0.046, 0.295, 0.05), (0.048, 0.048, 0.032), _EYE_PU)
    part(sc, (0, 0.268, 0.05), (0.065, 0.020, 0.020), _c(68, 145, 58))  # senyum
    # Bunga kecil di ujung batang
    part(sc, (0, 0.46, 0), (0.18, 0.18, 0.18), _c(245, 205, 75))
    part(sc, (0, 0.47, 0), (0.09, 0.09, 0.09), _c(248, 130, 48))

def _build_wild_berry(part, sc):
    """Beri liar chibi — buah bulat ungu-merah cerah, wajah ceria."""
    # Buah berry bulat besar
    part('sphere', (0, 0.26, 0), (0.45, 0.45, 0.45), _c(182, 58, 148))
    # Kilap buah
    part('sphere', (0.12, 0.36, 0.18), (0.14, 0.14, 0.12), _c(238, 175, 228))
    # Tangkai
    part(sc, (0, 0.50, 0), (0.05, 0.14, 0.05), _c(72, 142, 58))
    # Daun (3 kecil)
    for ox, rot_y in ((0.09, 35), (-0.09, -35), (0.00, 0)):
        part(sc, (ox, 0.54, 0.04), (0.16, 0.22, 0.09),
             _c(68, 165, 60), rotation=(0, rot_y, 0))
    # Mata chibi
    for sx in (-1, 1):
        ex = sx * 0.11
        part('sphere', (ex,          0.28,  0.23), (0.088, 0.088, 0.05), _EYE_W)
        part('sphere', (ex,          0.28,  0.242),(0.065, 0.065, 0.04), _c(135, 45, 175))
        part('sphere', (ex,          0.28,  0.252),(0.040, 0.040, 0.03), _EYE_PU)
        part('sphere', (ex+sx*0.025, 0.302, 0.260),(0.024, 0.024, 0.02), _EYE_W)
    # Pipi
    for sx in (-1, 1):
        part(sc, (sx*0.16, 0.24, 0.21), (0.10, 0.062, 0.04), _BLUSH)
    # Senyum
    part(sc, (0, 0.23, 0.23), (0.09, 0.026, 0.026), _c(188, 95, 155))


import math as _math

def update_anim_wild(actor, kind: str, t: float):
    """Animasikan entitas liar setiap frame — bob, goyang, melayang."""
    base_y = getattr(actor, '_base_y', 0.25)
    if kind == 'running_mushroom':
        # Lompat-lompat + condong kiri-kanan saat berlari
        actor.y = base_y + abs(_math.sin(t * 4.5)) * 0.14
        actor.rotation_z = _math.sin(t * 4.5) * 10
    elif kind == 'firefly':
        # Melayang naik-turun + putaran lambat
        actor.y = base_y + _math.sin(t * 1.8) * 0.20
        actor.rotation_y = t * 45 % 360
    elif kind == 'mandrake':
        # Bergoyang panik + memantul ringan
        actor.rotation_z = _math.sin(t * 3.2) * 8
        actor.y = base_y + abs(_math.sin(t * 3.2)) * 0.05
    elif kind == 'wild_herb':
        # Melambai tertiup angin
        actor.rotation_z = _math.sin(t * 1.4) * 5
        actor.rotation_x = _math.sin(t * 1.1) * 3
    elif kind == 'wild_berry':
        # Bob perlahan + sedikit ayun
        actor.y = base_y + _math.sin(t * 1.3) * 0.06
        actor.rotation_z = _math.sin(t * 0.9) * 4
