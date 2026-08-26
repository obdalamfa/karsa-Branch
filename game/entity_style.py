"""
entity_style.py — Kosakata visual "entitas" Lembah Karsa.

Satu-satunya sumber warna & proporsi untuk segala manifestasi entitas:
tanaman terinfeksi, objek korup, wujud mob, HUD yang meleleh, lab, dan
langit yang salah. Spesifikasi lengkap: docs/ENTITY_VISUAL_LANGUAGE.md
Bentuk asli: docs/entity-logo.svg

Tesis desainnya satu kalimat: **akarnya adalah kabel.** Semua angka di
modul ini diukur langsung dari SVG logo, bukan dikira-kira.

Konvensi:
  LU  = "logo unit". Kanvas logo 1000x1000; 1000 LU = satu lebar emblem.
        Konversi ke meter dilakukan per penempatan (lihat dokumen §0).
  t   = jarak sepanjang sumbu daun / panjang total daun  (0 = pangkal, 1 = ujung)
  S   = skala seragam terhadap pusat motif

Pemakaian (dari props.py / mob.py / sky.py):
    from .entity_style import LEAF_TEAL, ursina_color, leaf_blade
    e = Entity(model=leaf_blade(0.4), color=ursina_color(LEAF_TEAL))

CATATAN IMPLEMENTASI: konstanta di modul ini sudah final dan benar.
Helper mesh masih berupa signature + docstring; body-nya sengaja raise
NotImplementedError supaya tidak ada yang diam-diam mengembalikan kubus.
"""
from __future__ import annotations

from typing import Iterable, Sequence


# ═══════════════════════════════════════════════════════════════════════════
#  PALET — hex mentah, persis seperti di docs/entity-logo.svg
# ═══════════════════════════════════════════════════════════════════════════
# Daun / tubuh hidup
LEAF_TEAL      = '#3FB3A0'   # ujung gradasi daun, tulang chevron
LEAF_MID       = '#12867A'   # gradasi 0.82
LEAF_DEEP      = '#0B5C51'   # gradasi 0.40
LEAF_ROOT      = '#06302A'   # gradasi 0.00 (pangkal)

# Garis luar — dipakai HAMPIR semua motif
OUTLINE_NAVY   = '#0E2033'   # outline gear, daun, mulut, cincin sucker

# Kehampaan / blot mata
CORE_BLACK     = '#05171B'   # iris tengah, pupil, tetesan, rongga mulut
VOID_DEEP      = '#02100F'   # iris tepi (stop terluar) — makin luar makin gelap
VOID_RIM       = '#0A3138'   # iris pusat, cakram luar sucker

# Cahaya krem (glory)
CREAM_LIGHT    = '#FBEFC6'   # glory + rays, kilau rivet, cincin halo
CREAM_TOOTH    = '#FBF7E8'   # HANYA gigi
CREAM_SCLERA   = '#F4F7F1'   # HANYA putih mata

# Perunggu (mesin)
BRONZE_DARK    = '#8A6428'   # gradasi gear bawah, badan rivet, arsir radial
BRONZE_MID     = '#C79B45'   # isi cincin dalam, gradasi tengah
BRONZE_LIGHT   = '#E8BC55'   # gradasi gear, ray bawah, pita mata #2
BRONZE_PALE    = '#EBD08A'   # gradasi gear atas

# Sulur / jalur PCB
VINE_GREEN     = '#0E6B4F'   # inti sulur, SELURUH circuit-tree
VINE_SHADOW    = '#08462F'   # pass bayangan sulur

# Daging — dijatah ketat (<0.4% piksel)
FLESH_PINK     = '#E77E9A'   # lidah, rona gusi, inti sucker, titik simpul

# Aksen sekali-pakai
CYAN_GLINT     = '#2AA8C4'   # pita mata #4, pendar bawah sklera
SIGNAL_BLUE    = '#1B4C9B'   # pita mata #3 — HANYA di sini
RUST           = '#B5652A'   # pita mata #1 — HANYA di sini

#: Semua warna entitas, untuk validator/tooling.
PALETTE = {
    'LEAF_TEAL': LEAF_TEAL, 'LEAF_MID': LEAF_MID, 'LEAF_DEEP': LEAF_DEEP,
    'LEAF_ROOT': LEAF_ROOT, 'OUTLINE_NAVY': OUTLINE_NAVY,
    'CORE_BLACK': CORE_BLACK, 'VOID_DEEP': VOID_DEEP, 'VOID_RIM': VOID_RIM,
    'CREAM_LIGHT': CREAM_LIGHT, 'CREAM_TOOTH': CREAM_TOOTH,
    'CREAM_SCLERA': CREAM_SCLERA, 'BRONZE_DARK': BRONZE_DARK,
    'BRONZE_MID': BRONZE_MID, 'BRONZE_LIGHT': BRONZE_LIGHT,
    'BRONZE_PALE': BRONZE_PALE, 'VINE_GREEN': VINE_GREEN,
    'VINE_SHADOW': VINE_SHADOW, 'FLESH_PINK': FLESH_PINK,
    'CYAN_GLINT': CYAN_GLINT, 'SIGNAL_BLUE': SIGNAL_BLUE, 'RUST': RUST,
}


# ═══════════════════════════════════════════════════════════════════════════
#  GRADASI — (offset, hex, alpha)
# ═══════════════════════════════════════════════════════════════════════════
#: Linear, pangkal→ujung daun, dimiringkan 8.5° dari sumbu.
#: Ujung SELALU paling terang, tak peduli arah matahari scene. Itu disengaja.
LEAF_GRAD = (
    (0.00, LEAF_ROOT, 1.0),
    (0.40, LEAF_DEEP, 1.0),
    (0.82, LEAF_MID,  1.0),
    (1.00, LEAF_TEAL, 1.0),
)
LEAF_GRAD_RAKE_DEG = 8.5

#: Radial, pusat (0.50, 0.42), radius 0.62.
#: Perhatikan: makin ke TEPI makin GELAP — mata ini disinari dari dalam.
BLOT_GRAD = (
    (0.00, VOID_RIM,   1.0),
    (0.60, CORE_BLACK, 1.0),
    (1.00, VOID_DEEP,  1.0),
)
BLOT_GRAD_CENTER = (0.50, 0.42)
BLOT_GRAD_RADIUS = 0.62

#: Linear (0.1,0) → (0.9,1) — diagonal, jadi gigi gear kiri-atas selalu terang.
GEAR_GRAD = (
    (0.00, BRONZE_PALE, 1.0),
    (0.50, BRONZE_MID,  1.0),
    (1.00, BRONZE_DARK, 1.0),
)

#: Radial. Satu-satunya motif yang boleh additive-blend.
GLORY_GRAD = (
    (0.00, CREAM_LIGHT,  0.55),
    (0.62, CREAM_LIGHT,  0.32),
    (1.00, BRONZE_LIGHT, 0.00),
)

#: Linear vertikal, untuk sirip cahaya.
RAY_GRAD = (
    (0.00, CREAM_LIGHT,  0.95),
    (1.00, BRONZE_LIGHT, 0.35),
)


# ═══════════════════════════════════════════════════════════════════════════
#  TABEL PROPORSI — hasil ukur dari SVG
# ═══════════════════════════════════════════════════════════════════════════

#: Radius acuan: ujung gigi gear luar. Tepi keras "mesin"-nya.
R_TIP_LU = 378.0

#: Siluet daun lanceolate: (t, half_width / max_half_width).
#: 8 titik, SEMUA segmen lurus, join miter. Tidak ada satu pun kurva.
LEAF_PROFILE = (
    (0.000, 0.000),
    (0.110, 0.580),
    (0.330, 1.000),   # titik terlebar
    (0.700, 0.465),
    (1.000, 0.000),
)
LEAF_WIDTH_RATIO   = 0.165   # max_half_width / length (bilah utama)
LEAF_RIB_ANGLE_DEG = 40.2    # chevron, diukur dari horizontal
LEAF_RIB_REACH     = 1.21    # x max_half_width — sengaja lewat siluet, lalu di-clip
LEAF_RIB_ALPHA     = 0.42
LEAF_RIB_FIRST_T   = 0.08
LEAF_SPEC_ALPHA    = 0.10    # baji putih separuh kanan, tepi keras, tanpa falloff

#: Gear ring: dua pangkat yang tersedia. Rasio, bukan angka absolut.
GEAR_OUTER = {
    'teeth': 16, 'tip_ratio': 1.174, 'hole_ratio': 0.832,
    'duty': 0.368, 'root_flare': 1.065,
    'rivets': 24, 'rivet_r_ratio': 0.0217,      # x r_body
    'rivet_band_t': 0.52,                        # antara hole..body
    'rivet_hi_ratio': 0.41, 'rivet_hi_offset': 0.30,  # x rivet_r, ke arah PUSAT
    'hatch': 80, 'hatch_alpha': 0.40,
    'outline_w_ratio': 0.0248,
}
GEAR_INNER = {
    'teeth': 36, 'tip_ratio': 1.059, 'hole_ratio': 0.966,
    'duty': 0.335, 'root_flare': 1.000,
    'rivets': 0, 'hatch': 0,
    'outline_w_ratio': 0.0170,
}

#: Tumpukan pita mata, terluar dulu: (skala, jenis, warna, lebar/H, alpha).
#: Rasio radius 1.00 / 0.80 / 0.66 — jangan menambah pita keempat.
EYE_BANDS = (
    (1.00, 'fill',   None,         0.000, 1.00),   # BLOT_GRAD
    (1.00, 'stroke', RUST,         0.034, 0.85),
    (1.00, 'stroke', BRONZE_LIGHT, 0.021, 0.80),
    (0.80, 'stroke', SIGNAL_BLUE,  0.055, 0.55),
    (0.66, 'stroke', CYAN_GLINT,   0.038, 0.45),
)
EYE_ASPECT       = 0.740   # lebar / tinggi — lebih jangkung daripada lebar
EYE_LOBES        = 16      # 16 segmen kuadratik, 32 anchor
EYE_WOBBLE       = 0.06    # ±6% jitter radius anchor — kentang, bukan oval
EYE_LENS_HALF    = 0.494   # x half-width iris
EYE_LENS_UPPER   = 0.583   # puncak kelopak atas, di ATAS garis sudut
EYE_LENS_LOWER   = 0.221   # puncak kelopak bawah, juga di ATAS — sabit, bukan almond
EYE_LENS_GLOW    = 1.083   # sklera digambar 0.923 dari lens cyan → rim 7.7%
EYE_PUPIL_RATIO  = 0.19    # x half-width lens
EYE_DRIPS = (              # (root_x / W_eye, root_width / H, length / H)
    (-0.50, 0.115, 0.42),
    (-0.11, 0.149, 0.68),
    (+0.38, 0.126, 0.50),
)
EYE_DRIP_ROOT_T  = 0.90    # dari dasar iris
EYE_ON_BLADE_T   = 0.60    # pusat mata utama pada sumbu daun
EYE_ON_BLADE_FILL = 0.91   # lebar mata / lebar maksimum daun
EYE_SECONDARY_T  = 0.40
EYE_SECONDARY_S  = 0.35
EYE_SECONDARY_DX = 0.44    # x max_half_width, keluar sumbu

#: Mulut. Semua rasio terhadap W = setengah lebar mulut, +y ke bawah.
MOUTH_PROFILE = {
    'lower_ctrl':   1.028,   # kontrol kuadratik bibir bawah
    'upper_ctrl':   0.349,
    'gap':          0.339,   # bukaan di tengah
    'teeth':        6,
    'tooth_w':      1 / 3,   # x W  (lebar sisi atas segitiga)
    'tooth_h':      0.473,   # x W  — LEBIH PANJANG dari gap; sengaja tembus bibir
    'tongue_half':  0.301,
    'tongue_top':   0.487,
    'tongue_apex':  0.744,
    'gum_x':        0.914,
    'gum_y':        0.171,
    'gum_rx':       0.325,
    'gum_ry':       0.161,
    'gum_alpha':    0.45,
    'outline_w':    0.089,
    'outline_alpha': 0.80,
    'on_blade_t':   0.28,    # garis sudut mulut pada sumbu daun
    'on_blade_w':   0.68,    # W / max_half_width daun
}

#: Sulur. Kurva halus; ini satu-satunya motif yang BOLEH melengkung bebas.
VINE = {
    'shadow_w_ratio':  1.36,
    'shadow_alpha':    0.55,
    'min_bend_factor': 4.0,      # min radius belok >= 4 x lebar inti
    'min_bend_emblem': 0.04,     # dan >= 4% lebar emblem
    'turn_min_deg':    30.0,
    'turn_max_deg':    150.0,
    'sample_points':   47,
    'suckers':         3,
    'sucker_r_ratio':  0.58,     # x lebar inti
    'sucker_core':     0.42,     # x radius sucker
    'sucker_ring_w':   0.19,     # x lebar inti
    'sucker_alpha':    0.80,
    'sucker_spacing':  7.0,      # x lebar inti, untuk pemakaian prosedural
    'tip_len_ratio':   (0.19, 0.28),   # x panjang bilah utama
}

#: Circuit-tree. Tangga lebar 15 → 11 → 8 → 6 LU; rasio ~0.735 per pangkat.
WIDTH_LADDER      = (15.0, 11.0, 8.0, 6.0)
WIDTH_LADDER_RATIO = 0.735
CIRCUIT = {
    'max_ranks':     4,
    'run_ratio':     9.5,     # panjang lari tegak lurus, x lebar sendiri
    'stub_ratio':    4.5,     # panjang stub setelah belokan 90°
    'corner_ratio':  3.25,
    'pad_ratio':     9.7,     # panjang bantalan terminal, x lebar sendiri
    'pad_w_ratio':   0.75,    # x lebar cabang yang memberi makan
    'len_range':     (3.0, 16.0),   # panjang segmen, x lebar sendiri
    'module_m':      0.25,    # kuantisasi panjang di skala dunia (meter)
    'turn_deg':      90.0,
    'turn_tol_deg':  0.25,
    'fillet':        0.0,     # miter keras. Nol. Tanpa kompromi.
    'node_r_ratio':  0.58,
    'exceptions':    ('root_flare_bezier', 'corner_stub_35_8_deg'),
}
CIRCUIT_EXCEPTION_ANGLE_DEG = 35.8   # dua stub sudut palang, mirror

#: Berapa sendi yang di-"taint" per tahap eskalasi (docs §4).
#: -1 = semua. Pemilihan sendi di-seed dari id objek → STABIL antar frame.
TAINT_JOINTS = (0, 1, 3, 8, 24, -1)

#: Anggaran kepadatan per tahap (docs §3). Melanggar ini = merusak efeknya.
STAGE_BUDGET = (
    {'elements': 0,  'eyes': 0, 'pink': 0, 'screen_area': 0.0000},
    {'elements': 3,  'eyes': 0, 'pink': 0, 'screen_area': 0.0015},
    {'elements': 12, 'eyes': 1, 'pink': 0, 'screen_area': 0.0150},
    {'elements': 40, 'eyes': 4, 'pink': 3, 'screen_area': 0.0800},
    {'elements': -1, 'eyes': -1, 'pink': -1, 'screen_area': 1.0000},
    {'elements': -1, 'eyes': -1, 'pink': -1, 'screen_area': 1.0000},
)

#: Kecepatan rotasi cincin gear saat manifestasi penuh (derajat/detik).
#: Berlawanan arah. Ini SATU-SATUNYA gerak entitas di tahap 5.
GEAR_SPIN_DPS = 0.6


# ═══════════════════════════════════════════════════════════════════════════
#  UTILITAS WARNA
# ═══════════════════════════════════════════════════════════════════════════
def hex_to_rgb(h: str) -> tuple[int, int, int]:
    """'#3FB3A0' → (63, 179, 160). Terima dengan atau tanpa '#'."""
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def hex_to_rgbf(h: str, a: float = 1.0) -> tuple[float, float, float, float]:
    """'#3FB3A0' → (0.247, 0.702, 0.627, 1.0) — untuk uniform shader."""
    r, g, b = hex_to_rgb(h)
    return (r / 255.0, g / 255.0, b / 255.0, a)


def ursina_color(h: str, a: float = 1.0):
    """Konversi hex → warna Ursina.

    Import Ursina di dalam fungsi supaya modul ini tetap bisa di-import oleh
    tooling (validator palet, generator atlas) tanpa membuka window Panda3D.
    """
    from ursina import color as _color  # noqa: PLC0415 — lazy on purpose
    r, g, b = hex_to_rgb(h)
    return _color.rgb(r, g, b, int(round(a * 255)))


def lerp_gradient(grad: Sequence[tuple], t: float) -> tuple[float, float, float, float]:
    """Sampel gradasi (offset, hex, alpha) pada t ∈ [0,1] → RGBA float.

    Interpolasi linear di ruang sRGB — sama seperti yang dilakukan renderer SVG,
    jadi hasilnya cocok dengan logo. Jangan diganti ke linear-light; nanti
    gradasi daun jadi terlalu terang di tengah dan hilang kesan datar-nya.
    """
    if not grad:
        raise ValueError('gradasi kosong')
    t = min(1.0, max(0.0, float(t)))
    if t <= grad[0][0]:
        return hex_to_rgbf(grad[0][1], grad[0][2])
    if t >= grad[-1][0]:
        return hex_to_rgbf(grad[-1][1], grad[-1][2])
    for i in range(len(grad) - 1):
        o0, h0, a0 = grad[i]
        o1, h1, a1 = grad[i + 1]
        if o0 <= t <= o1:
            f = 0.0 if o1 == o0 else (t - o0) / (o1 - o0)
            c0 = hex_to_rgbf(h0, a0)
            c1 = hex_to_rgbf(h1, a1)
            return tuple(c0[k] + (c1[k] - c0[k]) * f for k in range(4))  # type: ignore[return-value]
    return hex_to_rgbf(grad[-1][1], grad[-1][2])


def snap_length(length: float, module: float = CIRCUIT['module_m']) -> float:
    """Kuantisasi panjang segmen ke kelipatan modul (default 0.25 m).

    Dipakai oleh aturan ORTHOGONALITY INTRUSION (docs §4 langkah 4).
    """
    return module * round(length / module)


def ladder_width(rank: int, base: float = WIDTH_LADDER[0]) -> float:
    """Lebar cabang pada pangkat ke-`rank` dari tangga 0.735.

    rank 0 = batang. Maksimum 4 pangkat: pangkat kelima hilang di jarak main.
    """
    if rank < 0:
        raise ValueError('rank negatif')
    if rank >= CIRCUIT['max_ranks']:
        raise ValueError(f'maks {CIRCUIT["max_ranks"]} pangkat, diminta {rank}')
    return base * (WIDTH_LADDER_RATIO ** rank)


# ═══════════════════════════════════════════════════════════════════════════
#  HELPER MESH PROSEDURAL  (signature final; implementasi menyusul)
# ═══════════════════════════════════════════════════════════════════════════
def gear_ring(r_body: float, *, teeth: int = 16,
              tip_ratio: float = GEAR_OUTER['tip_ratio'],
              hole_ratio: float = GEAR_OUTER['hole_ratio'],
              duty: float = GEAR_OUTER['duty'],
              rivets: int = 0,
              thickness: float = 0.02,
              segments_per_flank: int = 1):
    """Annulus pipih dengan gigi persegi (crenellation), bukan gigi involute.

    Crest gigi RATA (tali busur) dan sudutnya miter keras. Gigi involute
    membaca sebagai "permesinan"; crenellation persegi membaca sebagai
    "mahkota yang dilas orang". Perbedaan itu penting.

    Args:
        r_body: radius badan cincin, dalam unit dunia. Semua radius lain
            diturunkan dari sini lewat rasio, supaya cincin di ukuran
            berapa pun tetap proporsional dengan logo.
        teeth: jumlah gigi. Logo memakai 16 (pangkat luar) dan 36 (dalam).
        tip_ratio: r_tip / r_body. 1.174 luar, 1.059 dalam.
        hole_ratio: r_hole / r_body. 0.832 luar, 0.966 dalam.
        duty: lebar sudut crest / pitch. 0.335–0.37. Di atas 0.5 jadi roda
            gigi dan berhenti terbaca sebagai halo; di bawah 0.25 jadi
            sunburst.
        rivets: jumlah paku keling di pita tengah badan cincin (t=0.52 antara
            hole..body). 24 untuk pangkat luar, 0 untuk dalam. Setiap rivet
            punya kilau krem yang di-offset ke arah PUSAT emblem — bukan ke
            arah matahari scene. Itu cara termurah bilang "benda ini punya
            sumber cahaya sendiri".
        thickness: tebal ekstrusi (0 = quad datar untuk decal/billboard).
        segments_per_flank: subdivisi sisi gigi. 1 sudah cukup; naikkan hanya
            kalau cincin dipakai sebagai geometri sorotan lampu.

    Returns:
        ursina.Mesh dengan mode 'triangle'. UV di-generate polar (u=sudut
        ternormalisasi, v=radius ternormalisasi) supaya GEAR_GRAD bisa
        dipasang lewat tekstur 1D.

    Raises:
        NotImplementedError: implementasi belum ditulis.
    """
    raise NotImplementedError('gear_ring belum diimplementasikan — lihat docs/ENTITY_VISUAL_LANGUAGE.md §M1')


def eye_disc(height: float, *,
             bands: Sequence[tuple] = EYE_BANDS,
             pupil: bool = True,
             lobes: int = EYE_LOBES,
             wobble: float = EYE_WOBBLE,
             aspect: float = EYE_ASPECT,
             drips: int = 3,
             seed: int = 0):
    """Mata bertumpuk: ladang iris berlobus + pita konsentris + sabit sklera.

    Bentuk iris adalah kentang, bukan oval: 16 segmen kuadratik yang radius
    anchor-nya bergoyang ±6% dari elips aspek 0.740. Isinya BLOT_GRAD, yang
    makin GELAP ke arah tepi — mata ini disinari dari dalam. Itu salah satu
    fakta terpenting di seluruh spesifikasi.

    Sklera adalah SABIT, bukan almond: kedua kelopak melengkung ke ATAS, jadi
    mata membaca sebagai terbalik ke belakang, bukan menatap. Mata yang
    menatap adalah jump-scare dan jump-scare dilarang (docs §5.1).

    Args:
        height: tinggi mata (H) dalam unit dunia. Lebar = height * aspect.
        bands: tumpukan pita, terluar dulu. Default EYE_BANDS — rasio radius
            1.00 / 0.80 / 0.66. JANGAN menambah pita keempat.
        pupil: True = cakram CORE_BLACK ber-radius 0.19 x setengah-lebar lens.
            Di logo 7 dari 14 mata punya pupil. Pilihan per-instance harus
            STABIL (seed dari id objek) — pupil yang berkedip-kedip adalah
            jump-scare.
        lobes: jumlah lobus siluet iris.
        wobble: amplitudo jitter radius anchor, fraksi.
        aspect: lebar / tinggi.
        drips: jumlah tetesan gelap yang menggantung dari dasar iris (0–3).
            Menggantung lurus di frame LOKAL mata — kalau asetnya miring,
            tetesannya ikut miring. Bukan gravitasi dunia.
        seed: menentukan fase wobble dan pilihan pupil. Harus deterministik
            per objek.

    Returns:
        list[ursina.Entity] terurut dari belakang ke depan (iris, pita, lens,
        pupil, drips). Dikembalikan sebagai list dan bukan satu mesh karena
        tiap lapis punya blend/alpha berbeda dan harus bisa dianimasikan
        terpisah (pita cyan berputar pelan di tahap 4+).

    Raises:
        NotImplementedError: implementasi belum ditulis.
    """
    raise NotImplementedError('eye_disc belum diimplementasikan — lihat docs/ENTITY_VISUAL_LANGUAGE.md §M4')


def leaf_blade(length: float, *,
               width_ratio: float = LEAF_WIDTH_RATIO,
               ribs: int | None = None,
               midrib: bool = True,
               specular_wedge: bool = True):
    """Bilah tombak lanceolate — sisi LURUS, sudut miter.

    Ini inti dari "mesin yang memakai kehidupan": margin daun asli itu
    kontinu-C1; yang ini bersudut. Profil siluet ada di LEAF_PROFILE
    (8 verteks, semua segmen garis lurus).

    Args:
        length: panjang bilah pangkal→ujung, unit dunia.
        width_ratio: setengah-lebar maksimum / panjang. 0.165 untuk bilah
            mahkota; sampai 0.26 untuk ujung sulur kecil.
        ribs: jumlah pasang tulang chevron. None = otomatis,
            clamp(round(length_LU / 31), 4, 8). Tiap tulang keluar dari
            sumbu pada 40.2° dari horizontal, menjangkau 1.21 x setengah-lebar
            (sengaja lewat siluet lalu di-clip).
        midrib: garis tengah OUTLINE_NAVY dari t=0.012 sampai t=0.93.
        specular_wedge: baji putih rata α0.10 di separuh kanan. Tepi keras,
            tanpa falloff. Sengaja tidak fisis.

    Returns:
        ursina.Mesh. UV v = t sepanjang sumbu, supaya LEAF_GRAD bisa dipasang
        sebagai ramp 1D. Ingat gradasinya miring 8.5° (LEAF_GRAD_RAKE_DEG),
        jadi u ikut dipakai sedikit.

    Catatan penempatan: bilah mahkota di logo semuanya rotate(0) — berdiri
    tegak lurus di mana pun ditanam. Bilah ujung sulur diputar ke sudut acak
    yang TIDAK ada hubungannya dengan tangen sulur. Daun yang tumbuh sejajar
    batangnya; yang ini ditempelkan. Pertahankan dua perilaku itu.

    Raises:
        NotImplementedError: implementasi belum ditulis.
    """
    raise NotImplementedError('leaf_blade belum diimplementasikan — lihat docs/ENTITY_VISUAL_LANGUAGE.md §M3')


def vine_curve(points: Iterable[Sequence[float]], *,
               core_width: float,
               suckers: int = VINE['suckers'],
               shadow: bool = True,
               min_bend_factor: float = VINE['min_bend_factor']):
    """Sulur: polyline tersampel, dua pass (bayangan lalu inti), tutup bulat.

    Sulur adalah satu-satunya motif yang boleh melengkung bebas — dan justru
    itu yang membuat pembalikannya di tahap 4 bekerja: begitu sulur meluruskan
    diri jadi konduit ortogonal, penonton mengerti bahwa sulur itu memang
    selalu kabel.

    Args:
        points: titik kontrol (x, y, z) atau (x, y). Akan di-resample ke
            VINE['sample_points'] (47) titik.
        core_width: lebar pass inti (VINE_GREEN). Pass bayangan
            (VINE_SHADOW, α0.55) digambar 1.36x lebih lebar di belakangnya.
        suckers: jumlah pengisap. Logo memakai tepat 3 per untai pada
            t ≈ 0.25 / 0.50 / 0.75. Untuk untai prosedural pakai jarak busur
            tetap 6–8 x lebar inti, maksimum 5. Inti merah muda-nya cuma
            beberapa piksel — kelangkaan itulah efeknya.
        shadow: gambar pass bayangan.
        min_bend_factor: radius belok minimum = faktor x core_width. Di bawah
            4.0 sulur terlihat seperti kabel yang tertekuk, bukan tumbuh.

    Returns:
        list[ursina.Mesh]: [shadow, core] + satu mesh per sucker.

    Raises:
        ValueError: kalau kurva melanggar min_bend_factor atau total belokan
            keluar dari rentang 30°–150° (di luar itu sulur membaca sebagai
            besi tempa dekoratif atau sebagai kabel — dua-duanya register
            yang salah untuk tahap 1–3).
        NotImplementedError: implementasi belum ditulis.
    """
    raise NotImplementedError('vine_curve belum diimplementasikan — lihat docs/ENTITY_VISUAL_LANGUAGE.md §M6')


def circuit_branch(origin: Sequence[float], direction: Sequence[float], *,
                   rank: int = 0,
                   run_ratio: float = CIRCUIT['run_ratio'],
                   stub_ratio: float = CIRCUIT['stub_ratio'],
                   pad: bool = True,
                   node_dot: bool = False):
    """Satu cabang circuit-tree: lari tegak lurus, belok TEPAT 90°, bantalan.

    Aturan percabangan (docs §M7):
      1. cabang meninggalkan induk tegak lurus, sepanjang run_ratio x lebarnya
      2. belok tepat 90.0° ± 0.25° ke arah ujung, panjang stub_ratio x lebar
      3. join miter, fillet NOL — tanpa bevel, tanpa smoothing group
      4. belokan diambil terhadap sumbu DUNIA, bukan frame lokal induk.
         Ini yang membuatnya terlihat dipaksakan, bukan tumbuh: sepetak
         semak yang ter-taint semuanya membelok ke arah dunia yang sama,
         tak peduli tiap tanaman diputar bagaimana.
      5. berakhir di bantalan (pad) tegak lurus, panjang 9.7 x lebar sendiri,
         tebal 0.75 x lebar cabang pemberi makan. Bilah daun lalu ditanam di
         tengah bantalan — komponen di atas solder pad.

    Args:
        origin: titik tolak di induk, unit dunia.
        direction: arah lari awal. Akan di-snap ke sumbu dunia terdekat
            (±X, ±Z, +Y).
        rank: pangkat tangga lebar (0..3). Lebar = ladder_width(rank).
        run_ratio: panjang lari pertama, x lebar sendiri.
        stub_ratio: panjang stub setelah belokan, x lebar sendiri.
        pad: gambar bantalan terminal.
        node_dot: kalau belokan bukan terminal, taruh titik simpul di sudut —
            cakram VOID_RIM r = 0.58 x lebar, inti FLESH_PINK 0.42 dari itu.

    Returns:
        list[ursina.Mesh]: [run, stub] (+ pad) (+ node_dot).

    PENTING — pengecualian yang disahkan. Circuit-tree punya TEPAT DUA tempat
    di mana ia boleh tidak ortogonal, dan keduanya ada di pangkal:
      * root flare — kurva Bézier kubik di dasar batang. Satu-satunya kurva
        di seluruh pohon. Di situlah mesin berpura-pura ditanam.
      * corner stub — dua stub 35.8° di ujung luar palang, mirror.
    Kalau ada yang menambah pengecualian ketiga, motifnya mati. Dan setiap
    aset ter-taint HARUS menyisakan satu kurva di pangkalnya: itu kebohongan
    yang diceritakan objek tentang dirinya yang hidup. Tanpa itu objeknya
    cuma mesin, dan tidak ada yang merasa terganggu oleh mesin.

    Raises:
        ValueError: rank di luar 0..3.
        NotImplementedError: implementasi belum ditulis.
    """
    raise NotImplementedError('circuit_branch belum diimplementasikan — lihat docs/ENTITY_VISUAL_LANGUAGE.md §M7')


# ═══════════════════════════════════════════════════════════════════════════
#  VALIDATOR RINGAN — dipakai oleh builder & reviewer
# ═══════════════════════════════════════════════════════════════════════════
def check_stage_budget(stage: int, *, elements: int, eyes: int, pink: int,
                       screen_area: float) -> list[str]:
    """Kembalikan daftar pelanggaran anggaran kepadatan untuk satu frame.

    List kosong = lolos. Anggaran di STAGE_BUDGET bukan saran; cara paling
    umum merusak efek ini adalah menempelkan circuit-tree kecil di setiap
    prop ketiga karena helper-nya menyenangkan dipanggil. Tiga elemen di
    tahap 1. Tiga.
    """
    if not 0 <= stage < len(STAGE_BUDGET):
        raise ValueError(f'stage {stage} di luar 0..{len(STAGE_BUDGET) - 1}')
    b = STAGE_BUDGET[stage]
    out: list[str] = []
    for key, val in (('elements', elements), ('eyes', eyes), ('pink', pink)):
        cap = b[key]
        if cap >= 0 and val > cap:
            out.append(f'{key}: {val} > {cap} (tahap {stage})')
    if screen_area > b['screen_area']:
        out.append(f'screen_area: {screen_area:.4f} > {b["screen_area"]:.4f} (tahap {stage})')
    return out


def is_entity_palette(hex_color: str) -> bool:
    """True kalau warna ini bagian resmi dari palet entitas."""
    h = '#' + hex_color.lstrip('#').upper()
    return h in {v.upper() for v in PALETTE.values()}
