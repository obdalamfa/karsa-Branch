"""
petapa_model.py — Petapa Srimana: Iblis-Dewa Bertangan Banyak.
Pose padmasana (sila), wajah Kala, 8 lengan memancar, emas bersinar.
Terinspirasi: Mahakala, Kala Bhairava, Avalokitesvara Tantra.
"""
from ursina import Entity, color
import math as _m


# ── Palet warna ──────────────────────────────────────────────────────────────
_G  = color.rgb(255, 220, 48)    # emas terang bersinar
_GM = color.rgb(235, 192, 58)    # emas tengah
_GD = color.rgb(188, 150, 45)    # emas gelap / bayangan
_GW = color.rgb(255, 250, 145)   # emas-putih mengilat (highlight)
_IV = color.rgb(245, 238, 215)   # gading (taring / mata putih)
_ER = color.rgb(220, 45, 38)     # iris merah iblis
_PL = color.rgb(18,   8,  8)     # pupil hitam
_TG = color.rgb(200, 42, 55)     # lidah merah
_F1 = color.rgb(255, 175, 38)    # api mahkota oranye
_F2 = color.rgb(255, 228, 72)    # api mahkota kuning
_LP = color.rgb(230, 162, 195)   # lotus merah muda
_LC = color.rgb(250, 244, 215)   # pusat lotus
_VJ = color.rgb(215, 228, 240)   # vajra / perak
_RB = color.rgb(192, 45, 75)     # rubi merah aksen
_E3 = color.rgb(255, 252, 90)    # mata ketiga bersinar


def _try_obj_form(actor, model_name, scale=1.0):
    """Pasang model OBJ (aset Blender) ke actor. Return True jika berhasil.
    Membersihkan parts prosedural lama bila ada (ganti wujud)."""
    try:
        from .entities import load_model_file
        mdl = load_model_file(model_name)
    except Exception:
        mdl = None
    if not mdl:
        return False
    parts = getattr(actor, '_petapa_parts', None)
    if parts:
        from ursina import destroy
        for p in parts:
            try: destroy(p)
            except Exception: pass
        actor._petapa_parts = None
    actor.model = mdl
    actor.color = color.white
    actor.scale = scale
    return True


def petapa_transform_galak(actor):
    """Wujud murka: arca yang mematung bangkit jadi Iblis-Dewa Bertangan Banyak.
    Dipanggil saat pemain pertama kali berinteraksi. Return True jika berubah."""
    if getattr(actor, '_petapa_form', '') == 'galak':
        return False
    if _try_obj_form(actor, 'petapa_srimana_galak', scale=1.0):
        actor._petapa_form = 'galak'
        return True
    return False


def build_petapa_srimana(actor):
    """
    Rakit Petapa Srimana sebagai child-Entity parts pada ``actor``.
    Setelah dipanggil: actor.model='cube', actor.color=clear, actor.scale=1.4.
    Aman dipanggil berulang (pool reuse): hanya reset warna jika sudah dibangun.

    Wujud awal = arca kalem "mematung" (petapa_srimana.obj, buatan Blender).
    Saat interaksi pertama, interaction_controller memanggil
    petapa_transform_galak() → ganti ke petapa_srimana_galak.obj.
    Bila aset OBJ tak ada, jatuh ke build prosedural lama di bawah.
    """
    if _try_obj_form(actor, 'petapa_srimana', scale=1.2):
        actor._petapa_form = 'kalem'
        return []

    if getattr(actor, '_petapa_parts', None):
        # Actor dari pool — cukup pastikan parent cube tetap tersembunyi
        actor.model = 'cube'
        actor.color = color.clear
        actor.scale = 1.40
        return actor._petapa_parts

    try:
        from .smooth_shader import apply_smooth
    except ImportError:
        def apply_smooth(e, **_):
            try: e.setLightOff()
            except Exception: pass

    parts = []

    def part(mdl, pos, scl, c, rx=0, ry=0, rz=0):
        e = Entity(parent=actor, model=mdl, position=pos, scale=scl,
                   color=c, rotation=(rx, ry, rz))
        apply_smooth(e, has_texture=False)
        parts.append(e)
        return e

    # ────────────────────────────────────────────────────────────────────────
    # 1. ASANA LOTUS (dudukan teratai, tiga lapisan)
    # ────────────────────────────────────────────────────────────────────────
    part('cube', (0, 0.07, 0), (2.10, 0.14, 1.90), _GD)   # alas bawah
    part('cube', (0, 0.22, 0), (1.82, 0.14, 1.64), _GM)   # tier tengah
    part('cube', (0, 0.36, 0), (1.52, 0.12, 1.35), _G)    # tier atas
    # Kelopak lotus merah muda di 8 arah
    for i in range(8):
        a = _m.radians(i * 45)
        part('cube', (_m.sin(a)*0.84, 0.24, _m.cos(a)*0.76),
             (0.32, 0.13, 0.24), _LP, ry=i * 45)
    part('cube', (0, 0.42, 0), (0.62, 0.07, 0.56), _LC)   # pusat lotus

    # ────────────────────────────────────────────────────────────────────────
    # 2. KAKI BERSILA (padmasana / lotus pose)
    # ────────────────────────────────────────────────────────────────────────
    for sx in (-1, 1):
        # Paha horizontal ke samping
        part('cube', (sx*0.44, 0.55, 0.16), (0.65, 0.30, 0.78), _GD)
        # Kaki terlipat (menyilang ke depan)
        part('cube', (sx*0.22, 0.44, 0.62), (0.42, 0.26, 0.42), _GM, ry=sx*-18)
        # Telapak kaki tampak di depan
        part('cube', (sx*0.14, 0.40, 0.84), (0.36, 0.21, 0.26), _G)

    # ────────────────────────────────────────────────────────────────────────
    # 3. TORSO (lebar, berlapis — tampung banyak lengan)
    # ────────────────────────────────────────────────────────────────────────
    TY = 0.88   # pusat torso
    part('cube', (0, TY - 0.12, 0.02), (1.10, 0.52, 0.92), _GD)   # perut bawah
    part('cube', (0, TY + 0.18, 0.02), (1.15, 0.58, 0.90), _GM)   # dada atas
    part('cube', (0, TY + 0.12, 0.48), (0.90, 0.58, 0.10), _G)    # dada depan highlight
    # Benang suci upavita (dari bahu kiri ke pinggang kanan)
    part('cube', (-0.12, TY + 0.30, 0.48), (0.07, 0.76, 0.06), _GW, rz=28)
    # Kalung necklace
    part('cube', (0, TY + 0.62, 0.48), (0.78, 0.07, 0.06), _GW)
    # Sabuk pinggang
    part('cube', (0, TY - 0.35, 0.04), (1.08, 0.12, 0.88), _GW)

    # ────────────────────────────────────────────────────────────────────────
    # 4. LEHER
    # ────────────────────────────────────────────────────────────────────────
    NY = TY + 0.68
    part('cube', (0, NY, 0.04), (0.40, 0.28, 0.36), _GD)

    # ────────────────────────────────────────────────────────────────────────
    # 5. KEPALA IBLIS KALA (wajah lebar, brutal, sakral)
    # ────────────────────────────────────────────────────────────────────────
    HY = NY + 0.65
    # Kepala utama
    part('cube', (0, HY, 0.06),        (1.12, 1.00, 0.94), _GM)
    # Punggung kepala (lebih gelap)
    part('cube', (0, HY, -0.26),       (1.05, 0.92, 0.44), _GD)
    # Dahi menonjol ke depan (brow ridge Kala)
    part('cube', (0, HY + 0.28, 0.50), (1.02, 0.24, 0.30), _GD)
    # Pipi gembung iblis
    for sx in (-1, 1):
        part('cube', (sx*0.54, HY - 0.06, 0.38), (0.28, 0.48, 0.36), _GD)
    # Dagu menonjol
    part('cube', (0, HY - 0.40, 0.46), (0.66, 0.24, 0.32), _GD)

    # ── Mata iblis melotot ──
    for sx in (-1, 1):
        ex, ey, ez = sx * 0.31, HY + 0.10, 0.54
        part('sphere', (ex, ey,         ez      ), (0.29, 0.29, 0.13), _IV)
        part('sphere', (ex, ey,         ez+0.02 ), (0.20, 0.20, 0.10), _ER)
        part('sphere', (ex, ey,         ez+0.04 ), (0.11, 0.11, 0.07), _PL)
        part('sphere', (ex+sx*0.08, ey+0.09, ez+0.07), (0.042, 0.042, 0.03), _IV)

    # ── Alis tebal miring (ekspresi marah) ──
    for sx in (-1, 1):
        part('cube', (sx*0.25, HY + 0.35, 0.52),
             (0.34, 0.07, 0.055), _GD, rz=sx*-26)

    # ── Hidung lebar gepeng ──
    part('cube', (0, HY - 0.04, 0.54), (0.34, 0.20, 0.12), _GD)
    for sx in (-1, 1):
        part('cube', (sx*0.12, HY - 0.06, 0.58), (0.07, 0.07, 0.05), _PL)

    # ── Mulut menganga lebar (Kala) ──
    part('cube', (0, HY - 0.26, 0.52), (0.74, 0.24, 0.11), _PL)   # rongga
    part('cube', (0, HY - 0.26, 0.54), (0.60, 0.14, 0.09), _TG)   # lidah
    # Gigi atas (4 buah)
    for gx in (-0.22, -0.07, 0.07, 0.22):
        part('cube', (gx, HY - 0.16, 0.58), (0.08, 0.16, 0.06), _IV)
    # Taring atas besar (menonjol ke bawah, sudut keluar)
    for sx in (-1, 1):
        part('cube', (sx*0.30, HY - 0.24, 0.56), (0.10, 0.30, 0.08), _IV, rz=sx*-24)
    # Taring bawah (runcing ke atas)
    for sx in (-1, 1):
        part('cube', (sx*0.24, HY - 0.35, 0.54), (0.09, 0.20, 0.07), _IV, rz=sx*15)

    # ── Tanduk iblis (melengkung ke belakang–atas, 2 segmen per sisi) ──
    for sx in (-1, 1):
        part('cube', (sx*0.54, HY + 0.24, 0.10),  (0.14, 0.44, 0.13), _GD, rz=sx*-38)
        part('cube', (sx*0.68, HY + 0.58, 0.05),  (0.10, 0.32, 0.10), _GD, rz=sx*-55)
    # Telinga besar + anting emas
    for sx in (-1, 1):
        part('cube',   (sx*0.60, HY + 0.00, 0.04), (0.09, 0.40, 0.14), _GM)
        part('sphere', (sx*0.60, HY - 0.26, 0.04), (0.11, 0.11, 0.09), _GW)

    # ────────────────────────────────────────────────────────────────────────
    # 6. MATA KETIGA (trinayana — dahi bersinar kuning)
    # ────────────────────────────────────────────────────────────────────────
    part('sphere', (0, HY + 0.20, 0.54),         (0.18, 0.15, 0.08), _GW)
    part('sphere', (0, HY + 0.20, 0.56),         (0.12, 0.12, 0.06), _E3)
    part('sphere', (0, HY + 0.20, 0.59),         (0.07, 0.07, 0.04), _PL)

    # ────────────────────────────────────────────────────────────────────────
    # 7. MAHKOTA API (kiritas mukuta + lidah-lidah api)
    # ────────────────────────────────────────────────────────────────────────
    KY = HY + 0.62
    part('cube', (0, KY, 0.06), (1.14, 0.18, 1.02), _G)      # pita mahkota
    # Permata di pita (5 buah rubi)
    for mx in (-0.38, -0.19, 0.0, 0.19, 0.38):
        part('cube', (mx, KY + 0.13, 0.54), (0.11, 0.14, 0.07), _RB)
    # Lidah api (7 buah, tinggi bertahap — tengah paling tinggi)
    flame_pairs = [
        (-0.44, 0.32), (-0.28, 0.46), (-0.13, 0.60),
        ( 0.00, 0.70),
        ( 0.13, 0.60), ( 0.28, 0.46), ( 0.44, 0.32),
    ]
    for i, (fx, fh) in enumerate(flame_pairs):
        fc = _F2 if i % 2 == 0 else _F1
        part('cube', (fx, KY + fh*0.5, 0.04), (0.13, fh, 0.10), fc)
    # Bola api puncak
    part('sphere', (0, KY + 0.80, 0.04), (0.28, 0.28, 0.24), _F2)
    part('sphere', (0, KY + 0.98, 0.04), (0.17, 0.17, 0.15), _GW)

    # ────────────────────────────────────────────────────────────────────────
    # 8. DELAPAN LENGAN (4 pasang, memancar dari bahu secara simetris)
    #
    #  Sudut diukur dari sumbu vertikal ke atas (0°=atas, 90°=horizontal):
    #   Pasang 0: ~148° → ke bawah (dhyana mudra di pangkuan)
    #   Pasang 1: ~100° → sedikit di bawah horizontal (pegang lotus)
    #   Pasang 2: ~65°  → ke atas-samping (pegang vajra)
    #   Pasang 3: ~32°  → hampir tegak ke atas (abhaya / pegang api)
    # ────────────────────────────────────────────────────────────────────────
    OX, OY = 0.60, TY + 0.56   # titik awal bahu (sebelum sisi kiri/kanan)

    # (sudut_dari_atas_deg, panjang_lengan, warna_lengan, tebal_lengan)
    ARM_CFG = [
        (148, 0.92, _GM, 0.19),   # pasang 0 — dhyana
        (100, 0.84, _GM, 0.16),   # pasang 1 — lotus
        ( 65, 0.80, _GM, 0.15),   # pasang 2 — vajra
        ( 32, 0.74, _GM, 0.14),   # pasang 3 — abhaya/api
    ]

    for ang_deg, arm_len, arm_col, arm_t in ARM_CFG:
        ang = _m.radians(ang_deg)
        dx  = _m.sin(ang)          # komponen horizontal (selalu +, sx akan membaliknya)
        dy  = _m.cos(ang)          # komponen vertikal (negatif = ke bawah)
        for sx in (-1, 1):
            mx  = sx * (OX + dx * arm_len * 0.5)
            my  = OY + dy * arm_len * 0.5
            rz  = sx * ang_deg
            # Segmen lengan (kubus panjang ditilt sesuai sudut)
            part('cube', (mx, my, 0.02), (arm_t, arm_len, arm_t), arm_col, rz=rz)
            # Gelang di pangkal lengan
            part('cube', (sx*OX, OY, 0.08), (0.15, 0.08, 0.17), _GW)
            # Ujung tangan / benda sakral
            hx = sx * (OX + dx * arm_len)
            hy = OY + dy * arm_len

    # — Tangan utama (pasang 0) — telapak tangan dhyana mudra di lutut —
    for sx in (-1, 1):
        ang = _m.radians(148)
        hx  = sx * (OX + _m.sin(ang) * 0.92)
        hy  = OY + _m.cos(ang) * 0.92
        part('cube',   (hx, hy,        0.56), (0.30, 0.11, 0.34), _G)      # telapak
        part('cube',   (hx, hy + 0.07, 0.65), (0.07, 0.09, 0.18), _GW)    # jari mudra

    # — Tangan pasang 1 — lotus —
    for sx in (-1, 1):
        ang = _m.radians(100)
        hx  = sx * (OX + _m.sin(ang) * 0.84)
        hy  = OY + _m.cos(ang) * 0.84
        part('sphere', (hx, hy,        0.06), (0.14, 0.14, 0.12), _LP)    # bunga lotus
        part('sphere', (hx, hy + 0.15, 0.06), (0.09, 0.09, 0.09), _LC)   # pusat lotus
        part('cube',   (hx, hy - 0.07, 0.06), (0.05, 0.16, 0.05), _GM)   # tangkai

    # — Tangan pasang 2 — vajra (thunderbolt) —
    for sx in (-1, 1):
        ang = _m.radians(65)
        hx  = sx * (OX + _m.sin(ang) * 0.80)
        hy  = OY + _m.cos(ang) * 0.80
        part('cube',   (hx, hy,        0.06), (0.07, 0.34, 0.07), _VJ)   # batang vajra
        part('sphere', (hx, hy + 0.20, 0.06), (0.13, 0.13, 0.11), _VJ)   # kepala vajra
        part('sphere', (hx, hy - 0.20, 0.06), (0.11, 0.11, 0.10), _VJ)   # ekor vajra

    # — Tangan pasang 3 — api suci —
    for sx in (-1, 1):
        ang = _m.radians(32)
        hx  = sx * (OX + _m.sin(ang) * 0.74)
        hy  = OY + _m.cos(ang) * 0.74
        part('cube',   (hx, hy,        0.06), (0.12, 0.28, 0.10), _F1)   # badan api
        part('sphere', (hx, hy + 0.18, 0.06), (0.13, 0.13, 0.11), _F2)   # bola api

    # ────────────────────────────────────────────────────────────────────────
    # 9. HALO PRABHAVALI (lingkaran cahaya besar di belakang kepala)
    #    Disimulasikan dengan titik-titik kubus kecil membentuk 3 cincin
    # ────────────────────────────────────────────────────────────────────────
    N_DOTS = 20
    rings = [
        (1.20, 0.10, _G,  -0.12),   # cincin dalam
        (1.46, 0.08, _GM, -0.18),   # cincin tengah
        (1.68, 0.06, _GW, -0.22),   # cincin luar
    ]
    for r, thick, rc, zdep in rings:
        for j in range(N_DOTS):
            a   = _m.radians(j * (360 / N_DOTS))
            hx  = _m.sin(a) * r
            hy  = HY + 0.14 + _m.cos(a) * r
            part('cube', (hx, hy, zdep), (thick, thick, 0.05), rc)

    # Sinar mandorla (8 batang memancar dari pusat halo ke luar)
    for j in range(8):
        a   = _m.radians(j * 45)
        for ri, (r_s, r_e) in enumerate(((0.72, 1.10), (1.10, 1.48))):
            rm  = (r_s + r_e) * 0.5
            hx  = _m.sin(a) * rm
            hy  = HY + 0.14 + _m.cos(a) * rm
            t   = 0.05 - ri * 0.01
            part('cube', (hx, hy, -0.10 - ri*0.04), (t, r_e - r_s, t), _GW)

    # ────────────────────────────────────────────────────────────────────────
    # Selesai — bersihkan model induk (actor jadi invisible container)
    # ────────────────────────────────────────────────────────────────────────
    actor.model  = 'cube'
    actor.color  = color.clear
    actor.scale  = 1.40
    actor._petapa_parts = parts
    return parts
