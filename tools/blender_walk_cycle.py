"""Siklus jalan & seluruh aksi ter-rig untuk rig 29 tulang di characters_vitaboy.blend.

Menggantikan aksi <rig>_walk bawaan, yang lututnya menekuk ke depan (rotasi X
negatif pada L_LEG1/R_LEG1 melipat betis ke arah muka) dan telapaknya diam,
serta menambahkan aksi ekspresif untuk:
  - idle  (napas organik, pergeseran tumpuan pinggul, tolehan kepala halus)
  - walk  (siklus langkah dengan kontak tumit, dorong jari kaki, ayunan lengan)
  - hoe   (cangkul: ancang-ancang angkat tinggi, hantam dengan lutut menekuk ke belakang, tahanan, kembali)
  - swing (sabit/pedang/kapak: putaran bahu & pinggang, tebasan diagonal ber-follow-through)
  - water (siram: condong depan, angkat dua tangan, miringkan pergelangan menuang air)
  - talk  (percakapan hidup: anggukan kepala alami, gerakan tangan ekspresif bergantian, tubuh bernapas)
  - wave  (sapaan ramah: tangan kanan melambai di atas bahu, kepala miring hangat)
  - give  (memberi hadiah / memungut panen: bungkuk sopan / raih dengan dua tangan lalu sodorkan)

Konvensi rig ini (diukur dari matrix_local tulang): karakter menghadap -Y,
tulang kaki/lengan mengarah ke bawah dengan sumbu X lokal = +X dunia. Maka:
  - SPINE/NECK/HEAD: rx > 0 membungkuk/mengangguk ke DEPAN (-Y), rx < 0 mendongak ke BELAKANG (+Y).
                     ry > 0 menoleh/memutar badan, rz > 0 miring ke KIRI (+X).
  - L_ARM1/R_ARM1/L_ARM2/R_ARM2: rx < 0 mengayun lengan/sikunya ke DEPAN-ATAS (-Y, +Z).
  - R_ARM1: rz > 0 membuka lengan kanan ke luar (-X); L_ARM1: rz < 0 membuka lengan kiri ke luar (+X).
  - L_LEG/R_LEG: rx < 0 mengangkat paha ke DEPAN (-Y).
  - L_LEG1/R_LEG1: rx > 0 menekuk lutut ke BELAKANG (+Y). (Jangan pernah rx < 0 pada lutut!)
  - L_FOOT/R_FOOT: rx < 0 plantar, rx > 0 dorsifleksi.
"""
import math
import bpy

FRAMES = 24          # satu siklus jalan = dua langkah, 1 detik pada 24 fps


def _bump(p, pusat, lebar):
    d = (p - pusat + 0.5) % 1.0 - 0.5
    return math.exp(-(d / lebar) ** 2)


def _halus(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def _kurva_kunci(f, titik):
    """Interpolasi halus dari daftar [(frame, nilai), ...]."""
    if f <= titik[0][0]:
        return titik[0][1]
    if f >= titik[-1][0]:
        return titik[-1][1]
    for i in range(1, len(titik)):
        f0, v0 = titik[i - 1]
        f1, v1 = titik[i]
        if f <= f1:
            u = (f - f0) / max(1e-6, f1 - f0)
            return v0 + (v1 - v0) * _halus(u)
    return titik[-1][1]


def _kaki(p):
    """-> (paha, lutut, telapak) dalam derajat 'anatomis' untuk fase p."""
    paha = 25.0 * math.cos(2 * math.pi * p)                    # + = ke depan
    lutut = 12.0 * _bump(p, 0.10, 0.07) + 62.0 * _bump(p, 0.70, 0.13)
    telapak = (10.0 * _bump(p, 0.0, 0.06)                      # tumit menapak
               - 22.0 * _bump(p, 0.47, 0.07)                   # dorong ujung kaki
               + 6.0 * _bump(p, 0.78, 0.10))                   # ujung naik saat ayun
    return paha, lutut, telapak


def _kunci(pb, frame, rx=0.0, ry=0.0, rz=0.0):
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
    pb.keyframe_insert('rotation_euler', frame=frame)


def _kunci_pos(pb, frame, x=0.0, y=0.0, z=0.0):
    pb.location = (x, y, z)
    pb.keyframe_insert('location', frame=frame)


def _reset_pose(rig):
    pb = rig.pose.bones
    for pbone in pb:
        pbone.rotation_mode = 'XYZ'
        pbone.rotation_euler = (0, 0, 0)
        pbone.location = (0, 0, 0)
    return pb


def _siapkan_action(rig, suffix):
    nama = f'{rig.name}_{suffix}'
    lama = bpy.data.actions.get(nama)
    if lama is not None:
        bpy.data.actions.remove(lama)
    ad = rig.animation_data or rig.animation_data_create()
    simpan = ad.action
    act = bpy.data.actions.new(nama)
    act.use_fake_user = True
    ad.action = act
    pb = _reset_pose(rig)
    return act, ad, simpan, pb


def buat_siklus_jalan(rig):
    act, ad, simpan, pb = _siapkan_action(rig, 'walk')

    for f in range(FRAMES + 1):
        p = f / FRAMES
        frame = f + 1
        for sisi, fase in (('L', p), ('R', (p + 0.5) % 1.0)):
            paha, lutut, telapak = _kaki(fase)
            _kunci(pb[f'{sisi}_LEG'], frame, rx=-paha)
            _kunci(pb[f'{sisi}_LEG1'], frame, rx=lutut)
            _kunci(pb[f'{sisi}_FOOT'], frame, rx=-telapak)
            # Lengan berlawanan dengan kaki sisi yang sama.
            ayun = -20.0 * math.cos(2 * math.pi * fase)
            buka = -4.0 if sisi == 'L' else 4.0
            _kunci(pb[f'{sisi}_ARM1'], frame, rx=-ayun, rz=buka)
            _kunci(pb[f'{sisi}_ARM2'], frame, rx=-(14.0 + 12.0 * max(0.0, ayun) / 20.0))

        putar = 4.5 * math.cos(2 * math.pi * p)
        goyang = 2.2 * math.sin(2 * math.pi * p)
        _kunci(pb['PELVIS'], frame, ry=putar, rz=goyang)
        _kunci(pb['SPINE'], frame, rx=3.5, ry=-putar * 1.1, rz=-goyang * 0.7)
        _kunci(pb['SPINE1'], frame, rx=2.0 + 1.5 * math.sin(4 * math.pi * p), ry=-putar * 0.5)
        _kunci(pb['HEAD'], frame, rx=-2.0 + 1.5 * math.cos(4 * math.pi * p), ry=putar * 0.35)
        # Pinggul terendah saat kaki menapak (p=0, 0,5), tertinggi di tengah tumpuan.
        _kunci_pos(pb['PELVIS'], frame, 0.0, 0.018 * (1 - math.cos(4 * math.pi * p)) / 2 - 0.012, 0.0)

    ad.action = simpan
    return act


def buat_siklus_diam(rig):
    """Animasi idle 72 frame (3 detik @24fps): napas dada, tumpuan pinggul santai, tolehan halus."""
    act, ad, simpan, pb = _siapkan_action(rig, 'idle')
    N = 72
    for f in range(N + 1):
        p = f / N
        frame = f + 1
        # Napas utama (2 siklus per 3 detik) + variasi tumpuan (1 siklus per 3 detik)
        napas = math.sin(2 * math.pi * p * 2.0)
        tumpu = math.sin(2 * math.pi * p)
        toleh = math.sin(2 * math.pi * p - 0.6)

        _kunci(pb['PELVIS'], frame, ry=1.8 * tumpu, rz=1.5 * tumpu)
        _kunci_pos(pb['PELVIS'], frame, 0.004 * tumpu, -0.003 * (1.0 - napas), 0.0)
        _kunci(pb['SPINE'], frame, rx=1.2 + 1.4 * napas, rz=-1.2 * tumpu)
        _kunci(pb['SPINE1'], frame, rx=1.0 + 1.8 * napas, ry=-1.2 * tumpu)
        _kunci(pb['NECK'], frame, rx=-0.8 * napas, ry=2.2 * toleh)
        _kunci(pb['HEAD'], frame, rx=-1.2 * napas + 1.5 * math.cos(2 * math.pi * p),
               ry=3.8 * toleh, rz=1.6 * tumpu)

        # Lengan rileks bernapas, siku sedikit tertekuk alami (tidak lurus kaku seperti robot)
        _kunci(pb['R_ARM1'], frame, rx=-3.0 - 2.0 * napas, rz=5.0 + 1.2 * napas)
        _kunci(pb['L_ARM1'], frame, rx=-3.0 + 1.8 * napas, rz=-5.0 - 1.2 * napas)
        _kunci(pb['R_ARM2'], frame, rx=-11.0 - 2.5 * napas)
        _kunci(pb['L_ARM2'], frame, rx=-11.0 - 2.0 * napas)
        _kunci(pb['R_HAND'], frame, rx=-4.0 * napas)
        _kunci(pb['L_HAND'], frame, rx=-4.0 * napas)

        # Lutut sedikit relaks mengikuti tumpuan
        _kunci(pb['R_LEG'], frame, rx=-2.5 * max(0.0, tumpu))
        _kunci(pb['R_LEG1'], frame, rx=5.0 * max(0.0, tumpu))
        _kunci(pb['L_LEG'], frame, rx=-2.5 * max(0.0, -tumpu))
        _kunci(pb['L_LEG1'], frame, rx=5.0 * max(0.0, -tumpu))

    ad.action = simpan
    return act


def buat_aksi_cangkul(rig):
    """Animasi hoe 28 frame: antisipasi angkat tinggi -> ayun bungkuk + lutut menekuk -> tahanan -> balik."""
    act, ad, simpan, pb = _siapkan_action(rig, 'hoe')
    N = 28
    for f in range(1, N + 1):
        # SPINE: tarik ke belakang saat angkat (f=7), membungkuk kuat saat menghantam tanah (f=14..18)
        spine_rx = _kurva_kunci(f, [(1, 0), (7, -16), (13, 32), (18, 28), (24, -3), (28, 0)])
        spine1_rx = _kurva_kunci(f, [(1, 0), (7, -12), (13, 18), (18, 15), (24, -2), (28, 0)])
        head_rx = _kurva_kunci(f, [(1, 0), (7, -8), (13, 12), (18, 14), (28, 0)])
        # Lengan: angkat tinggi di atas kepala (-145), lalu menghantam ke bawah (-45)
        arm1_rx = _kurva_kunci(f, [(1, -4), (7, -142), (13, -52), (18, -48), (24, -12), (28, -4)])
        arm2_rx = _kurva_kunci(f, [(1, -12), (7, -48), (13, -18), (18, -22), (28, -12)])
        # Kaki & lutut: lutut menekuk ke BELAKANG (+rx) dan paha ke DEPAN (-rx) supaya kuda-kuda kokoh!
        leg_rx = _kurva_kunci(f, [(1, 0), (7, -6), (13, -24), (18, -22), (28, 0)])
        knee_rx = _kurva_kunci(f, [(1, 0), (7, 12), (13, 42), (18, 38), (28, 0)])
        pelvis_y = _kurva_kunci(f, [(1, 0.0), (7, 0.01), (13, -0.06), (18, -0.05), (28, 0.0)])

        _kunci(pb['SPINE'], f, rx=spine_rx)
        _kunci(pb['SPINE1'], f, rx=spine1_rx)
        _kunci(pb['HEAD'], f, rx=head_rx)
        _kunci(pb['R_ARM1'], f, rx=arm1_rx, rz=4.0)
        _kunci(pb['L_ARM1'], f, rx=arm1_rx, rz=-4.0)
        _kunci(pb['R_ARM2'], f, rx=arm2_rx)
        _kunci(pb['L_ARM2'], f, rx=arm2_rx)
        _kunci(pb['R_LEG'], f, rx=leg_rx)
        _kunci(pb['L_LEG'], f, rx=leg_rx * 0.7)
        _kunci(pb['R_LEG1'], f, rx=knee_rx)
        _kunci(pb['L_LEG1'], f, rx=knee_rx * 0.7)
        _kunci_pos(pb['PELVIS'], f, 0.0, pelvis_y, 0.0)

    ad.action = simpan
    return act


def buat_aksi_ayun(rig):
    """Animasi swing 22 frame (pedang/sabit/kapak): antisipasi putar pinggang -> tebasan cepat -> follow-through."""
    act, ad, simpan, pb = _siapkan_action(rig, 'swing')
    N = 22
    for f in range(1, N + 1):
        putar = _kurva_kunci(f, [(1, 0), (6, -26), (11, 28), (15, 22), (22, 0)])
        bungkuk = _kurva_kunci(f, [(1, 0), (6, -8), (11, 18), (15, 14), (22, 0)])
        r_arm1_rx = _kurva_kunci(f, [(1, -4), (6, -115), (11, -38), (15, -28), (22, -4)])
        r_arm1_rz = _kurva_kunci(f, [(1, 5), (6, 32), (11, -18), (15, -12), (22, 5)])
        r_arm2_rx = _kurva_kunci(f, [(1, -12), (6, -52), (11, -10), (15, -16), (22, -12)])
        l_arm1_rx = _kurva_kunci(f, [(1, -4), (6, -25), (11, 18), (15, 12), (22, -4)])
        leg_rx = _kurva_kunci(f, [(1, 0), (6, -10), (11, -22), (15, -18), (22, 0)])
        knee_rx = _kurva_kunci(f, [(1, 0), (6, 18), (11, 36), (15, 30), (22, 0)])

        _kunci(pb['PELVIS'], f, ry=putar * 0.5)
        _kunci(pb['SPINE'], f, rx=bungkuk, ry=putar * 0.7)
        _kunci(pb['SPINE1'], f, rx=bungkuk * 0.6, ry=putar)
        _kunci(pb['HEAD'], f, rx=bungkuk * 0.4, ry=-putar * 0.4)
        _kunci(pb['R_ARM1'], f, rx=r_arm1_rx, rz=r_arm1_rz)
        _kunci(pb['R_ARM2'], f, rx=r_arm2_rx)
        _kunci(pb['L_ARM1'], f, rx=l_arm1_rx, rz=-12.0)
        _kunci(pb['L_ARM2'], f, rx=-20.0)
        _kunci(pb['R_LEG'], f, rx=leg_rx)
        _kunci(pb['R_LEG1'], f, rx=knee_rx)
        _kunci(pb['L_LEG'], f, rx=leg_rx * 0.5)
        _kunci(pb['L_LEG1'], f, rx=knee_rx * 0.5)

    ad.action = simpan
    return act


def buat_aksi_siram(rig):
    """Animasi water 32 frame: angkat gembor -> condong depan & tuang bergoyang -> tegak kembali."""
    act, ad, simpan, pb = _siapkan_action(rig, 'water')
    N = 32
    for f in range(1, N + 1):
        bungkuk = _kurva_kunci(f, [(1, 0), (7, -5), (13, 18), (23, 21), (28, -2), (32, 0)])
        arm1_rx = _kurva_kunci(f, [(1, -4), (7, -48), (13, -68), (23, -72), (28, -20), (32, -4)])
        arm2_rx = _kurva_kunci(f, [(1, -12), (7, -38), (13, -28), (23, -25), (32, -12)])
        tuang = _kurva_kunci(f, [(1, 0), (10, 0), (15, 28), (23, 34), (28, 0), (32, 0)])
        goyang = 4.0 * math.sin((f - 12) * 0.6) if 12 <= f <= 24 else 0.0
        knee_rx = _kurva_kunci(f, [(1, 0), (13, 18), (23, 20), (32, 0)])

        _kunci(pb['SPINE'], f, rx=bungkuk * 0.65, rz=goyang * 0.3)
        _kunci(pb['SPINE1'], f, rx=bungkuk * 0.45)
        _kunci(pb['HEAD'], f, rx=bungkuk * 0.5, rz=-goyang * 0.2)
        _kunci(pb['R_ARM1'], f, rx=arm1_rx, rz=4.0 + goyang)
        _kunci(pb['R_ARM2'], f, rx=arm2_rx)
        _kunci(pb['R_HAND'], f, rx=tuang, rz=-tuang * 0.7)
        _kunci(pb['L_ARM1'], f, rx=arm1_rx * 0.75, rz=-4.0)
        _kunci(pb['L_ARM2'], f, rx=arm2_rx * 0.85)
        _kunci(pb['R_LEG'], f, rx=-knee_rx * 0.5)
        _kunci(pb['L_LEG'], f, rx=-knee_rx * 0.5)
        _kunci(pb['R_LEG1'], f, rx=knee_rx)
        _kunci(pb['L_LEG1'], f, rx=knee_rx)

    ad.action = simpan
    return act


def buat_aksi_bicara(rig):
    """Animasi talk 48 frame (2 detik loop/sekali): anggukan kepala hangat + gestur tangan bergantian."""
    act, ad, simpan, pb = _siapkan_action(rig, 'talk')
    N = 48
    for f in range(N + 1):
        p = f / N
        frame = f + 1
        napas = math.sin(2 * math.pi * p * 2.0)
        sway = math.sin(2 * math.pi * p)
        # Dua anggukan lembut selama 2 detik
        angguk = 6.5 * (_bump(p, 0.22, 0.09) + 0.75 * _bump(p, 0.68, 0.10))
        # Gestur tangan kanan di paruh pertama, tangan kiri ikut di paruh kedua
        gest_r = _bump(p, 0.28, 0.16)
        gest_l = _bump(p, 0.72, 0.16)

        _kunci(pb['PELVIS'], frame, ry=2.5 * sway, rz=1.5 * sway)
        _kunci(pb['SPINE'], frame, rx=2.0 + 1.5 * napas + angguk * 0.25, ry=-2.0 * sway, rz=-1.2 * sway)
        _kunci(pb['SPINE1'], frame, rx=1.5 + 1.5 * napas + angguk * 0.25, ry=-2.5 * sway)
        _kunci(pb['NECK'], frame, rx=angguk * 0.35, ry=4.0 * sway)
        _kunci(pb['HEAD'], frame, rx=angguk * 0.85 - 1.5 * napas,
               ry=5.5 * math.sin(2 * math.pi * p + 0.4),
               rz=3.2 * math.cos(2 * math.pi * p))

        _kunci(pb['R_ARM1'], frame, rx=-8.0 - 38.0 * gest_r, rz=6.0 + 12.0 * gest_r)
        _kunci(pb['R_ARM2'], frame, rx=-18.0 - 42.0 * gest_r)
        _kunci(pb['R_HAND'], frame, rx=-12.0 * gest_r, rz=-15.0 * gest_r)

        _kunci(pb['L_ARM1'], frame, rx=-8.0 - 32.0 * gest_l, rz=-6.0 - 10.0 * gest_l)
        _kunci(pb['L_ARM2'], frame, rx=-18.0 - 36.0 * gest_l)
        _kunci(pb['L_HAND'], frame, rx=-10.0 * gest_l, rz=12.0 * gest_l)

    ad.action = simpan
    return act


def buat_aksi_sapa(rig):
    """Animasi wave 32 frame: angkat tangan kanan menyapa hangat + goyang telapak + angguk ramah."""
    act, ad, simpan, pb = _siapkan_action(rig, 'wave')
    N = 32
    for f in range(1, N + 1):
        angkat = _kurva_kunci(f, [(1, 0.0), (7, 1.0), (24, 1.0), (32, 0.0)])
        lambai = math.sin((f - 7) * 0.75) * angkat if 6 <= f <= 26 else 0.0
        angguk = _kurva_kunci(f, [(1, 0.0), (6, 8.0), (14, -2.0), (24, 3.0), (32, 0.0)])

        _kunci(pb['SPINE'], f, rx=2.5 * angkat, rz=-3.5 * angkat)
        _kunci(pb['SPINE1'], f, rx=2.0 * angkat, ry=-6.0 * angkat)
        _kunci(pb['HEAD'], f, rx=angguk, ry=-4.0 * angkat, rz=5.0 * angkat)

        _kunci(pb['R_ARM1'], f, rx=-4.0 - 105.0 * angkat, rz=5.0 + 28.0 * angkat + 14.0 * lambai)
        _kunci(pb['R_ARM2'], f, rx=-12.0 - 38.0 * angkat + 18.0 * lambai)
        _kunci(pb['R_HAND'], f, rz=16.0 * lambai)
        _kunci(pb['L_ARM1'], f, rx=-4.0, rz=-6.0)
        _kunci(pb['L_ARM2'], f, rx=-14.0)

    ad.action = simpan
    return act


def buat_aksi_beri(rig):
    """Animasi give/pickup 30 frame: merunduk/meraih dengan dua tangan lalu menyodorkan ke depan."""
    act, ad, simpan, pb = _siapkan_action(rig, 'give')
    N = 30
    for f in range(1, N + 1):
        # f=1..10 merunduk meraih, f=10..20 tegak & sodorkan dua tangan ke depan, f=20..30 kembali
        bungkuk = _kurva_kunci(f, [(1, 0), (9, 28), (17, 10), (23, 12), (30, 0)])
        knee_rx = _kurva_kunci(f, [(1, 0), (9, 44), (17, 10), (23, 8), (30, 0)])
        leg_rx = _kurva_kunci(f, [(1, 0), (9, -24), (17, -6), (23, -5), (30, 0)])
        arm1_rx = _kurva_kunci(f, [(1, -4), (9, -62), (17, -58), (23, -54), (30, -4)])
        arm2_rx = _kurva_kunci(f, [(1, -12), (9, -25), (17, -42), (23, -38), (30, -12)])
        pelvis_y = _kurva_kunci(f, [(1, 0.0), (9, -0.08), (17, -0.01), (30, 0.0)])

        _kunci(pb['SPINE'], f, rx=bungkuk * 0.65)
        _kunci(pb['SPINE1'], f, rx=bungkuk * 0.45)
        _kunci(pb['HEAD'], f, rx=bungkuk * 0.5)
        _kunci(pb['R_ARM1'], f, rx=arm1_rx, rz=-4.0)
        _kunci(pb['L_ARM1'], f, rx=arm1_rx, rz=4.0)
        _kunci(pb['R_ARM2'], f, rx=arm2_rx)
        _kunci(pb['L_ARM2'], f, rx=arm2_rx)
        _kunci(pb['R_LEG'], f, rx=leg_rx)
        _kunci(pb['L_LEG'], f, rx=leg_rx)
        _kunci(pb['R_LEG1'], f, rx=knee_rx)
        _kunci(pb['L_LEG1'], f, rx=knee_rx)
        _kunci_pos(pb['PELVIS'], f, 0.0, pelvis_y, 0.0)

    ad.action = simpan
    return act


def bangun_semua_aksi(rig):
    """Bangun seluruh 8 aksi untuk satu rig karakter."""
    buat_siklus_diam(rig)
    buat_siklus_jalan(rig)
    buat_aksi_cangkul(rig)
    buat_aksi_ayun(rig)
    buat_aksi_siram(rig)
    buat_aksi_bicara(rig)
    buat_aksi_sapa(rig)
    buat_aksi_beri(rig)
