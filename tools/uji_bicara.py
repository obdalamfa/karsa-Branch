#!/usr/bin/env python3
"""Uji animasi berbicara — mulut, kedipan yang tidak boleh berhenti, dan
anggukan yang harus dipimpin kepala.

"Berbicara" adalah satu dari tiga animasi yang diminta brief proyek ini, dan
sebelum berkas ini ada, tiga hal terukur salah selama kotak dialog terbuka:

    rentang tinggi mata warga     0,09881 -> 0,00000   (berhenti berkedip)
    rentang tinggi mulut warga    0,00000              (tidak pernah bergerak)
    rentang rotation_x kepala     0,00000              (yang terayun badannya)

Tanpa argumen: irama mulut saja — murni Python, tanpa jendela, sekitar sedetik.
Dengan `--game` (perlu xvfb): game dibuka, dialog sungguhan dijalankan, dan
kabelnya diperiksa.

Keluar dengan kode 1 kalau ada yang gagal, supaya bisa jadi gerbang.
"""
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DT = 1.0 / 30.0


class Bagian:
    """Pengganti Entity: cuma menampung skala dan enabled."""
    def __init__(self, sy=1.0, sx=1.0):
        self.scale_x, self.scale_y = sx, sy
        self.enabled = True


def buat_wajah(kunci='arya'):
    from game.wajah import Wajah
    mata = [Bagian(0.28), Bagian(0.28)]
    kilau = [Bagian(0.05), Bagian(0.05)]
    mulut = Bagian(0.016, 0.039)
    w = Wajah(mata, kilau, mulut, mata + kilau + [mulut])
    w.fase_awal(kunci)
    return w, mulut


def jalan(w, detik, mulut=None):
    deret = []
    for _ in range(int(detik / DT)):
        w.tick(DT)
        if mulut is not None:
            deret.append(mulut.scale_y)
    return deret


def puncak(deret, diam, ambang):
    """Waktu tiap puncak bukaan mulut (satu suku kata).

    Ambang turunnya diukur dari tinggi mulut DIAM, bukan dari ambang naiknya.
    Versi pertama memakai `ambang * 0,55`, yang jatuh DI BAWAH tinggi diam —
    dan tinggi mulut tidak pernah turun di bawah tinggi diam, jadi penanda
    "sudah turun" tidak pernah menyala dan seluruh 60 detik terbaca sebagai
    SATU suku kata. Tiga uji di bawahnya ikut gagal karena itu.
    """
    turun = diam + (ambang - diam) * 0.35
    out, naik = [], False
    for i, v in enumerate(deret):
        if v > ambang and not naik:
            out.append(i * DT); naik = True
        elif v <= turun:
            naik = False
    return out


def uji_irama(cek):
    w, mulut = buat_wajah()
    diam = mulut.scale_y

    # ── diam: mulut tidak bergerak sama sekali ───────────────────────────
    d0 = jalan(w, 8.0, mulut)
    cek('tidak bicara: mulut diam', max(d0) - min(d0) < 1e-9,
        'rentang %.7f' % (max(d0) - min(d0)))

    # ── bicara: mulut bergerak, dan bergerak BANYAK ──────────────────────
    w.set_bicara(True)
    d1 = jalan(w, 60.0, mulut)
    r = (max(d1) - min(d1)) / diam
    cek('bicara: mulut membuka >= 1,5x tinggi diam', r >= 1.5,
        'rentang %.2fx tinggi diam' % r)

    # ── laju suku kata masuk akal, dan tidak berirama ────────────────────
    p = puncak(d1, diam, diam * 1.6)
    jeda = [b - a for a, b in zip(p, p[1:])]
    laju = len(p) / 60.0
    cek('laju suku kata 2,5-7 per detik', 2.5 <= laju <= 7.0,
        '%d suku kata / 60 s = %.2f per detik' % (len(p), laju))
    # Simpangan baku SELURUH jarak tidak bisa dipakai di sini, dan itu terukur:
    # dengan panjang suku kata dibuat TETAP, sd seluruh jarak tetap 0,170 s —
    # nyaris sama dengan 0,170 s versi yang benar — karena jeda antar-frasa
    # yang memang bervariasi mendominasi angkanya. Uji mutasi meloloskan
    # metronom karena itu. Yang memisahkan keduanya adalah jarak DI DALAM
    # frasa saja: 0,0312 s lawan 0,0122 s.
    med = statistics.median(jeda) if jeda else 0.0
    dalam = [j for j in jeda if j < med * 1.5]
    sd = statistics.pstdev(dalam) if len(dalam) > 2 else 0.0
    cek('irama di DALAM frasa tidak tetap (sd > 0,022 s)', sd > 0.022,
        '%d jarak, rata2 %.3f s, sd %.4f s'
        % (len(dalam), statistics.mean(dalam) if dalam else 0, sd))

    # ── ada jeda antar-frasa, bukan dengung tanpa henti ──────────────────
    panjang = max(jeda) if jeda else 0.0
    cek('ada jeda antar-frasa (jeda terpanjang >= 1,8x rata2)',
        panjang >= (statistics.mean(jeda) if jeda else 1) * 1.8,
        'terpanjang %.3f s lawan rata2 %.3f s'
        % (panjang, statistics.mean(jeda) if jeda else 0))

    # ── bukaan tiap suku kata berbeda-beda ───────────────────────────────
    tinggi = sorted(set(round(v, 4) for v in d1 if v > diam * 1.9))
    cek('bukaan tiap suku kata berbeda', len(tinggi) > 20,
        '%d tinggi puncak berbeda' % len(tinggi))

    # ── berhenti bicara: mulut pulang ke diam, tidak memotong ────────────
    # Dihentikan saat mulut sedang TERBUKA. Versi pertama berhenti kapan saja,
    # dan kalau kebetulan mulutnya sudah tertutup, "pulang" memang selesai
    # dalam satu frame — yang terbaca seperti cacat padahal bukan.
    for _ in range(400):
        w.tick(DT)
        if mulut.scale_y > diam * 2.6:
            break
    sebelum = mulut.scale_y
    w.set_bicara(False)
    d2 = jalan(w, 1.0, mulut)
    cek('berhenti bicara: mulut kembali ke tinggi diam',
        abs(d2[-1] - diam) < 1e-6, 'selisih akhir %.7f' % abs(d2[-1] - diam))
    # Rumusan pertama menghitung JUMLAH TRANSISI dan menuntut > 1, dan itu
    # bukan yang dimaksud: pulang selama 90 ms pada 30 fps memang cuma melewati
    # dua nilai, jadi transisinya satu. Yang benar-benar mau dijamin adalah
    # mulut tidak MEMOTONG — frame pertama sesudah berhenti harus mendarat di
    # ANTARA tinggi terbuka dan tinggi diam, bukan langsung di tinggi diam.
    tengah = diam + 1e-9 < d2[0] < sebelum - 1e-9
    cek('mulut pulang bertahap, tidak memotong', tengah,
        'terbuka %.4f -> frame berikut %.4f -> diam %.4f'
        % (sebelum, d2[0], diam))

    # ── kedipan tetap jalan selama bicara ────────────────────────────────
    w2, m2 = buat_wajah()
    w2.set_bicara(True)
    tinggi_mata = []
    for _ in range(int(30.0 / DT)):
        w2.tick(DT)
        tinggi_mata.append(w2.mata[0].scale_y)
    cek('masih berkedip sambil bicara',
        max(tinggi_mata) - min(tinggi_mata) > 0.05,
        'rentang tinggi mata %.4f' % (max(tinggi_mata) - min(tinggi_mata)))

    # ── dua orang tidak bicara serempak ──────────────────────────────────
    wa, ma = buat_wajah('arya')
    wb, mb = buat_wajah('ningsih')
    wa.set_bicara(True); wb.set_bicara(True)
    da = jalan(wa, 40.0, ma)
    db = jalan(wb, 40.0, mb)
    sama = sum(1 for x, y in zip(da, db) if abs(x - y) < 1e-9)
    cek('dua warga tidak membuka mulut serempak', sama < len(da) * 0.5,
        '%d dari %d frame identik' % (sama, len(da)))


def uji_game(cek):
    """Buka game, jalankan dialog sungguhan, periksa kabelnya."""
    import os
    ROOT = Path(__file__).resolve().parent.parent
    os.chdir(ROOT)
    from panda3d.core import loadPrcFileData
    for k in ('load-display pandagl', 'window-type offscreen',
              'audio-library-name null'):
        loadPrcFileData('', k)
    import logging
    logging.basicConfig(level=logging.CRITICAL)
    from ursina import application
    application.asset_folder = ROOT
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))
    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = 320, 320
    from game.app import Game3D
    g = Game3D()
    from direct.showbase.ShowBaseGlobal import base
    from panda3d.core import ClockObject
    c = ClockObject.getGlobalClock()
    c.setMode(ClockObject.MNonRealTime)
    c.setDt(DT)

    def step(n=1):
        for _ in range(n):
            base.taskMgr.step()

    step(10)
    g.state.scene_name = 'town'
    g.world.load_scene('town')
    step(40)
    g.state.time_minutes = 12 * 60

    pilih = [(k, a) for k, a in g.entities.actors.items()
             if getattr(a, '_wajah', None) is not None
             and getattr(a, '_kepala', None) is not None]
    if not pilih:
        cek('ada warga berwajah untuk diajak bicara', False, 'tidak ada')
        return
    nid, npc = pilih[0]
    p = g.player
    pos = g.state.npc_positions.get(nid) or {}
    p.set_tile_pos(pos.get('x', npc.logical_x) + 1.0, pos.get('y', npc.logical_y))
    step(6)

    def rekam(n):
        kol = {k: [] for k in ('mata_npc', 'mata_pemain', 'mulut_npc',
                               'mulut_pemain', 'badan_rx', 'kepala_rx')}
        for _ in range(n):
            step(1)
            kol['mata_npc'].append(float(npc._wajah.mata[0].scale_y))
            kol['mulut_npc'].append(float(npc._wajah.mulut.scale_y))
            kol['badan_rx'].append(float(npc.rotation_x))
            kol['kepala_rx'].append(float(npc._kepala.rotation_x))
            pw = getattr(p, '_wajah', None)
            kol['mata_pemain'].append(float(pw.mata[0].scale_y) if pw else 0.0)
            kol['mulut_pemain'].append(float(pw.mulut.scale_y) if pw else 0.0)
        return {k: max(v) - min(v) for k, v in kol.items()}

    # Ambang kedipan HARUS relatif terhadap tinggi mata masing-masing. Versi
    # pertama memakai angka mati 0,05, yang dipatok dari ukuran mata warga —
    # dan menjatuhkan pemain, yang matanya lebih kecil dan rentang penuhnya
    # memang 0,043, sama persis seperti saat main biasa. Itu uji yang salah,
    # bukan pemain yang berhenti berkedip.
    t_npc = float(npc._wajah._tinggi0[0])
    _pw = getattr(p, '_wajah', None)
    t_pem = float(_pw._tinggi0[0]) if _pw else 1.0

    g.panels.start_dialog(nid, g.state)
    g.mulai_pose_bicara(nid)
    step(2)
    r = rekam(600)
    cek('dialog: warga tetap berkedip', r['mata_npc'] > t_npc * 0.6,
        'rentang %.5f dari tinggi mata %.5f' % (r['mata_npc'], t_npc))
    cek('dialog: pemain tetap berkedip', r['mata_pemain'] > t_pem * 0.6,
        'rentang %.5f dari tinggi mata %.5f' % (r['mata_pemain'], t_pem))
    cek('dialog: mulut warga bergerak', r['mulut_npc'] > 1e-4,
        'rentang tinggi mulut %.5f' % r['mulut_npc'])
    cek('dialog: mulut pemain DIAM (ia mendengarkan)',
        r['mulut_pemain'] < 1e-6, 'rentang %.7f' % r['mulut_pemain'])
    cek('dialog: kepala memimpin anggukan, bukan badan',
        r['kepala_rx'] > r['badan_rx'] * 2.0,
        'kepala %.3f lawan badan %.3f derajat' % (r['kepala_rx'], r['badan_rx']))

    # Giliran pemain memilih: mulut warga berhenti.
    g.panels._dlg_choices_active = True
    step(12)
    r2 = rekam(120)
    cek('pilihan aktif: mulut warga berhenti', r2['mulut_npc'] < 1e-6,
        'rentang %.7f' % r2['mulut_npc'])
    g.panels._dlg_choices_active = False

    # Tutup lewat jalur game sendiri, bukan dengan menyetel mode ke None —
    # gerbang main normal adalah mode == 'hud', jadi None membekukan segalanya
    # dan ronde pertama probe ini sempat melaporkannya sebagai cacat game.
    g.panels.close_all()
    g.akhiri_pose_bicara()
    step(8)
    r3 = rekam(300)
    cek('sesudah dialog: kedipan kembali jalan', r3['mata_npc'] > t_npc * 0.6,
        'rentang %.5f dari tinggi mata %.5f' % (r3['mata_npc'], t_npc))
    cek('sesudah dialog: mulut warga diam lagi', r3['mulut_npc'] < 1e-6,
        'rentang %.7f' % r3['mulut_npc'])
    cek('sesudah dialog: kepala kembali lurus',
        abs(float(npc._kepala.rotation_x)) < 1e-6,
        'rotation_x kepala %.7f' % abs(float(npc._kepala.rotation_x)))


def main():
    gagal, jumlah = [], []

    def cek(nama, ok, catatan):
        jumlah.append(nama)
        print('  %-46s %-7s %s' % (nama, 'LULUS' if ok else 'GAGAL', catatan))
        if not ok:
            gagal.append(nama)

    print('uji animasi berbicara')
    print('-' * 82)
    uji_irama(cek)
    if '--game' in sys.argv:
        uji_game(cek)
    print('-' * 82)
    if gagal:
        print('%d uji GAGAL: %s' % (len(gagal), ', '.join(gagal)))
        return 1
    print('SEMUA %d UJI LULUS' % len(jumlah))
    return 0


if __name__ == '__main__':
    sys.exit(main())
