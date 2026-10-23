"""probe_gerak.py — animasi kerja pemain dan mob dungeon, lewat jalur asli.

Sebelum 23 Okt 2026, saat pemain bekerja bobot klip langsung lompat dari 0 ke 1
lalu balik ke 0 dalam satu frame. Aksi tanpa klip (bend/gosok/bicara) tidak
menggerakkan rig sama sekali. Mob tidak dianimasikan: mereka meluncur
seperti patung, kilat kena pukulnya tidak berbuat apa-apa (kedua cabangnya
putih), dan mob yang mati lenyap dalam satu frame. Probe ini menjaga
supaya semua itu tidak kembali:

  pemain  SPACE (cangkul) lewat g.app.input -> lapisan jus aktif, pinggang
          condong ke belakang LALU ke depan, bobot klip dibaur (ada nilai
          antara), pose kembali tegak sesudahnya; bend tanpa klip tetap
          menggerakkan pinggang dan memendekkan tubuh
  mob     napas saat diam, kemerahan saat ancang-ancang, kilat saat HP
          turun, mati = berputar/menyusut lalu dihapus ~0,6 dtk kemudian,
          sementara s.mobs sudah diperbarui di frame kematian

    python tools/probe_gerak.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))

from probe_batin import boot, ke_hud, langkah, tekan, jalan, tunggu_detik  # noqa: E402

hasil: list[tuple[str, bool, str]] = []


def cek(nama, ok, ket=''):
    hasil.append((nama, bool(ok), str(ket)))


def _pitch(char):
    return char.pinggang.getHpr()[1]


def uji_pemain(g):
    p = g.player
    char = getattr(p, '_char', None)
    if char is None:
        cek('pemain memakai rig CharActor', False, 'p._char None')
        return
    # Kurva bobot sendiri: ramp masuk dan keluar, bukan banting.
    if char.mainkan_sekali('hoe'):
        d = char._sekali_dur
        sampel = []
        for t in (0.0, 0.03, 0.2, d - 0.1, d - 0.01):
            char._sekali_t = t
            sampel.append(round(char.bobot_kerja(), 2))
        antara = [w for w in sampel if 0.05 < w < 0.95]
        cek('bobot klip dibaur masuk-keluar', len(antara) >= 2 and max(sampel) >= 0.99,
            f'w={sampel}')
        char._sekali_t = d + 1.0
        langkah(2)

    # Cangkul sungguhan: tile (10,11) farm, alat 1, SPACE.
    jalan(g, 10, 11, 'up')
    tekan(g, '1', 3)
    langkah(10)
    J = p._jus
    pitch, bobot = [], []
    tekan(g, 'space', 1)
    mode_awal = J.mode
    t0 = time.time()
    while time.time() - t0 < 3.0:
        langkah(1)
        pitch.append(_pitch(char))
        bobot.append(char.bobot_kerja())
        if J.mode is None and char._sekali is None:
            break
    cek('SPACE cangkul menyalakan lapisan gerak', mode_awal in ('hoe', 'down'),
        f'jus.mode={mode_awal}')
    # Rig menghadap -Z: condong ke belakang = P positif, ke depan = P negatif.
    belakang, depan = max(pitch or [0]), min(pitch or [0])
    cek('pinggang condong ke belakang lalu ke depan', belakang > 3.0 and depan < -3.0,
        f'P {depan:.1f}..{belakang:.1f} dlm {len(pitch)} frame')
    cek('bobot klip kerja naik ke penuh', max(bobot or [0]) > 0.9,
        f'maks {max(bobot or [0]):.2f}')
    langkah(5)
    hpr = char.pinggang.getHpr()
    sk = char.poros.getScale()
    cek('pose kembali tegak sesudah kerja',
        J.mode is None and abs(hpr[1]) < 0.01 and abs(sk[1] - 1.0) < 0.01,
        f'mode={J.mode} P={hpr[1]:.2f} sy={sk[1]:.3f}')

    # Aksi tanpa klip: bend (panen/petik) dulu membiarkan tokoh berdiri diam.
    p._play_tool_anim('bend')
    maks_p, min_sy = 0.0, 1.0
    t0 = time.time()
    while time.time() - t0 < 2.0 and J.mode is not None:
        langkah(1)
        maks_p = max(maks_p, abs(_pitch(char)))
        min_sy = min(min_sy, char.poros.getScale()[1])
    cek('bend tanpa klip tetap menggerakkan tubuh', maks_p > 8.0 and min_sy < 0.9,
        f'|P| maks {maks_p:.1f}, sy min {min_sy:.2f}')


def uji_mob(g):
    s = g.state
    s.scene_name = 'dungeon'
    langkah(60)
    px, py = int(round(s.player_x)), int(round(s.player_y))
    spek = [dict(kind=k, x=px + dx, y=py + 4, hp=40, max_hp=40, damage=1, speed=1.5)
            for k, dx in (('pocong', -2), ('genderuwo', 0), ('kelelawar', 2))]
    g.entities.spawn_mobs([dict(d) for d in spek])
    langkah(3)
    mobs = [a for a in g.entities.actors.values() if type(a).__name__ == 'Monster']
    if len(mobs) < 3:
        cek('mob dungeon muncul', False, f'{len(mobs)} mob')
        return
    # Jauhkan pemain supaya AI tidak langsung menyerang dan menimpa fase lain.
    for m in mobs:
        m.attack_cooldown_ms = 99999

    # Napas: transform model berubah walau mob tidak disentuh.
    m0 = mobs[1]
    sy = []
    t0 = time.time()
    while time.time() - t0 < 1.2:
        langkah(1)
        sy.append(m0.model.getScale()[1])
    cek('mob bernapas saat diam', max(sy) - min(sy) > 0.004,
        f'{m0.kind} sy {min(sy):.3f}..{max(sy):.3f}')

    # Ancang-ancang: kemerahan dan condong.
    m0.windup_total = 600
    m0.windup_ms = 520
    langkah(1)
    langkah(1)
    cs = m0.model.getColorScale()
    cek('ancang-ancang terlihat (kemerahan)', m0.windup_ms > 0 and cs[0] > cs[1] + 0.05,
        f'windup {m0.windup_ms:.0f} cs=({cs[0]:.2f},{cs[1]:.2f},{cs[2]:.2f})')

    # Kena pukul: HP turun -> kilat putih.
    m1 = mobs[0]
    m1.hp -= 5
    langkah(1)
    cs = m1.model.getColorScale()
    cek('kena pukul berkilat', cs[0] > 1.5 and cs[1] > 1.5,
        f'cs=({cs[0]:.2f},{cs[1]:.2f},{cs[2]:.2f})')

    # Mati: logika di frame itu, model menghilang bertahap, lalu dihapus.
    m2 = mobs[2]
    spec = m2.mob_spec
    sc_awal = m2.model.getScale()[0]
    m2.hp = 0
    langkah(1)
    masih = m2 in g.entities.actors.values()
    cek('mob mati dikeluarkan dari s.mobs di frame kematian',
        spec not in s.mobs, f'spec di s.mobs={spec in s.mobs}')
    langkah(1)
    sc_mati = m2.model.getScale()[0] if masih else 0.0
    cek('mob mati tidak lenyap dalam satu frame (animasi mati)',
        masih and getattr(m2, 'dying', False) and sc_mati < sc_awal,
        f'masih={masih} dying={getattr(m2, "dying", None)} sx {sc_awal:.2f}->{sc_mati:.2f}')
    tunggu_detik(1.0)
    cek('mob mati dihapus sesudah animasinya',
        m2 not in g.entities.actors.values(), 'masih di actors')


def main():
    kerja = Path(tempfile.mkdtemp(prefix='probe_gerak_'))
    try:
        g = boot(kerja / 'save.json')
        if not ke_hud(g):
            cek('mencapai HUD', False, 'sinema/chargen tidak selesai')
        else:
            # Modal PAGI PERTAMA menelan cangkul pertama; diuji probe_batin.
            b = list(getattr(g.state, 'batin_sekali', []) or [])
            g.state.batin_sekali = b + ['pagi_pertama']
            uji_pemain(g)
            uji_mob(g)
    except Exception:
        traceback.print_exc()
        cek('probe berjalan tanpa pengecualian', False, 'lihat traceback')
    gagal = [h for h in hasil if not h[1]]
    for nama, ok, ket in hasil:
        print(f'  {"LULUS" if ok else "GAGAL"}  {nama:52s} {ket}')
    print(f'{len(hasil) - len(gagal)}/{len(hasil)} lulus')
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
