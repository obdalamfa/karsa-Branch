"""Siklus jalan prosedural untuk rig 29 tulang di characters_vitaboy.blend.

Menggantikan aksi <rig>_walk bawaan, yang lututnya menekuk ke depan (rotasi X
negatif pada L_LEG1/R_LEG1 melipat betis ke arah muka) dan telapaknya diam.

Konvensi rig ini (diukur dari matrix_local tulang): karakter menghadap -Y,
tulang kaki/lengan mengarah ke bawah dengan sumbu X lokal = +X dunia. Maka
rotasi X negatif mengayun paha/lengan ke DEPAN, rotasi X positif menekuk
lutut ke BELAKANG dan menekuk telapak ke bawah (plantar).
"""
import math

import bpy

FRAMES = 24          # satu siklus = dua langkah, 1 detik pada 24 fps


def _bump(p, pusat, lebar):
    d = (p - pusat + 0.5) % 1.0 - 0.5
    return math.exp(-(d / lebar) ** 2)


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


def buat_siklus_jalan(rig):
    nama = f'{rig.name}_walk'
    lama = bpy.data.actions.get(nama)
    if lama is not None:
        bpy.data.actions.remove(lama)
    ad = rig.animation_data or rig.animation_data_create()
    simpan = ad.action
    act = bpy.data.actions.new(nama)
    act.use_fake_user = True
    ad.action = act

    pb = rig.pose.bones
    for pbone in pb:
        pbone.rotation_mode = 'XYZ'
        pbone.rotation_euler = (0, 0, 0)
        pbone.location = (0, 0, 0)

    for f in range(FRAMES + 1):
        p = f / FRAMES
        frame = f + 1
        for sisi, fase in (('L', p), ('R', (p + 0.5) % 1.0)):
            paha, lutut, telapak = _kaki(fase)
            _kunci(pb[f'{sisi}_LEG'], frame, rx=-paha)
            _kunci(pb[f'{sisi}_LEG1'], frame, rx=lutut)
            _kunci(pb[f'{sisi}_FOOT'], frame, rx=-telapak)
            # Lengan berlawanan dengan kaki sisi yang sama.
            ayun = -18.0 * math.cos(2 * math.pi * fase)
            _kunci(pb[f'{sisi}_ARM1'], frame, rx=-ayun)
            _kunci(pb[f'{sisi}_ARM2'], frame, rx=-(12.0 + 10.0 * max(0.0, ayun) / 18.0))

        putar = 4.0 * math.cos(2 * math.pi * p)
        _kunci(pb['PELVIS'], frame, ry=putar)
        _kunci(pb['SPINE'], frame, rx=3.0, ry=-putar * 1.2)
        # Pinggul terendah saat kaki menapak (p=0, 0,5), tertinggi di tengah tumpuan.
        pb['PELVIS'].location = (0.0, 0.018 * (1 - math.cos(4 * math.pi * p)) / 2 - 0.012, 0.0)
        pb['PELVIS'].keyframe_insert('location', frame=frame)

    ad.action = simpan
    return act
