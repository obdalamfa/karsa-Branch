#!/usr/bin/env python3
"""Uji gerak telinga & ekor ternak.

Diukur, bukan dilihat, karena tiga hal yang membedakan gerak hidup dari motor
semuanya berupa ANGKA: rentang ayunan, simpangan baku jarak antar-kejadian
(nol = metronom), dan apakah sentuhan benar-benar mengubah sesuatu.

Tanpa argumen, hanya pengendalinya yang diuji — murni Python, tanpa jendela,
sekitar sedetik. Dengan `--rig` (perlu xvfb) rig sungguhannya ikut dibangun dan
letak tiap POROS diperiksa.

Kenapa poros diperiksa terpisah: kalau `ujung=` salah tanda, tampilan DIAM-nya
tetap identik — uji kotak-batas tidak akan menangkapnya sama sekali — tapi
ekornya akan berayun mengelilingi ujungnya sendiri dan pangkalnya yang terbang.

Keluar dengan kode 1 kalau ada yang gagal, supaya bisa jadi gerbang.
"""
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from game.gerak_ternak import GerakTernak


class Simpul:
    """Pengganti Entity: cuma menampung tiga sudut."""
    def __init__(self, sumbu='z', arah=1.0):
        self._sumbu, self._arah = sumbu, arah
        self.rotation_x = self.rotation_y = self.rotation_z = 0.0

    def sudut(self):
        return (self.rotation_y if self._sumbu == 'y' else self.rotation_z)


DT = 1.0 / 30.0


def jalan(g, detik, sikat=0.0, tidur=False, ekor=None, telinga=None):
    """Jalankan `detik` detik; kembalikan deret sudut ekor dan telinga."""
    de, dt_ = [], [[] for _ in (telinga or [])]
    for _ in range(int(detik / DT)):
        g.tick(DT, sikat, tidur)
        if ekor is not None:
            de.append(ekor.sudut())
        for i, t in enumerate(telinga or []):
            # Bertanda, dan satu sumbu saja: menjumlahkan nilai mutlak dua
            # sumbu membuat simpangan tidak bisa dihitung terhadap dasarnya.
            dt_[i].append(t.rotation_z if t._sumbu == 'z' else t.rotation_x)
    return de, dt_


def lintas_nol(deret):
    """Jarak (detik) antar-lintasan-nol arah naik."""
    out, akhir = [], None
    for i in range(1, len(deret)):
        if deret[i - 1] <= 0.0 < deret[i]:
            t = i * DT
            if akhir is not None:
                out.append(t - akhir)
            akhir = t
    return out


def kejadian(deret, ambang=4.0):
    """Waktu mulai tiap sentakan telinga.

    Diukur sebagai SIMPANGAN dari sudut duduk telinga, bukan dari nol. Versi
    pertama memakai |sudut| > ambang, dan itu berhenti benar begitu telinga
    punya sudut tetap: telinga yang layu 15 derajat saat hewan tidur terbaca
    sebagai satu kedutan yang tidak pernah selesai, padahal ia diam sempurna.
    Kedutan adalah gerakan sesaat, jadi yang diukur harus perubahannya.
    """
    if not deret:
        return []
    dasar = statistics.median(deret)
    out, naik = [], False
    for i, v in enumerate(deret):
        d = abs(v - dasar)
        if d > ambang and not naik:
            out.append(i * DT); naik = True
        elif d <= ambang * 0.4:
            naik = False
    return out


def uji_keadaan(cek):
    """Sakit dan senang harus TERLIHAT, dan tidak boleh bisa tertukar.

    husbandry.py membuka dengan kalimatnya sendiri: "Aturan yang tidak bisa
    dilihat pemain bukan aturan." Ia memberi tiap hewan takaran kenyang, air,
    bersih, hitungan lalai dan jalur sakit — dan seluruhnya cuma muncul sebagai
    teks di panel. Uji ini menjaga supaya keadaan itu terbaca dari hewannya,
    dan supaya dua keadaan yang berlawanan arti tidak berakhir mirip.
    """
    from game.wajah import Wajah

    def telinga_tetap(**kw):
        t = Simpul('z', 1.0)
        g = GerakTernak([t], [], 'sapi_betsy')
        g.set_keadaan(**kw)
        for _ in range(int(6.0 / DT)):
            g.tick(DT, 0.0, False)
        return t.rotation_z

    def ekor_rentang(**kw):
        e = Simpul('z')
        g = GerakTernak([], [e], 'sapi_betsy')
        g.set_keadaan(**kw)
        jalan(g, 8.0, ekor=e)
        de, _ = jalan(g, 60.0, ekor=e)
        return max(de) - min(de)

    net_t = telinga_tetap()
    sakit_t = telinga_tetap(sakit=True)
    senang_t = telinga_tetap(senang=1.0)
    cek('sakit: telinga layu turun >= 20 derajat', sakit_t <= net_t - 20.0,
        'netral %+.1f -> sakit %+.1f' % (net_t, sakit_t))
    cek('senang: telinga tegak naik >= 10 derajat', senang_t >= net_t + 10.0,
        'netral %+.1f -> senang %+.1f' % (net_t, senang_t))
    cek('sakit dan senang menggerakkan telinga ke arah BERLAWANAN',
        (sakit_t - net_t) * (senang_t - net_t) < 0,
        'sakit %+.1f, senang %+.1f terhadap netral %+.1f'
        % (sakit_t - net_t, senang_t - net_t, net_t))

    net_e = ekor_rentang()
    sakit_e = ekor_rentang(sakit=True)
    senang_e = ekor_rentang(senang=1.0)
    cek('sakit: ekor melemah <= 60% rentang netral', sakit_e <= net_e * 0.60,
        '%.1f -> %.1f derajat' % (net_e, sakit_e))
    cek('senang: ekor menguat >= 1,3x rentang netral', senang_e >= net_e * 1.3,
        '%.1f -> %.1f derajat' % (net_e, senang_e))

    # ── mata ─────────────────────────────────────────────────────────────
    class B:
        def __init__(self, sy=1.0):
            self.scale_x = 1.0
            self.scale_y = sy
            self.enabled = True

    def mata(**kw):
        m = [B(0.28), B(0.28)]
        w = Wajah(m, [B(0.05)], None, m)
        w.fase_awal('sapi_betsy')
        w.set_keadaan(**kw)
        tinggi, kedip, tutup = [], [], False
        for i in range(int(90.0 / DT)):
            w.tick(DT)
            v = m[0].scale_y / 0.28
            tinggi.append(v)
            if v < 0.35 and not tutup:
                kedip.append(i * DT); tutup = True
            elif v > 0.75 * (max(tinggi) or 1):
                tutup = False
        buka = max(tinggi)
        jd = [b - a for a, b in zip(kedip, kedip[1:])]
        return buka, (statistics.mean(jd) if jd else 0.0)

    net_b, net_j = mata()
    sakit_b, sakit_j = mata(sakit=True)
    senang_b, _ = mata(senang=1.0)
    cek('sakit: kelopak berat (mata <= 70% tinggi netral)',
        sakit_b <= net_b * 0.70, '%.3f -> %.3f' % (net_b, sakit_b))
    cek('sakit: kedipan melambat >= 1,8x', sakit_j >= net_j * 1.8,
        'jeda %.2f s -> %.2f s' % (net_j, sakit_j))
    cek('senang: mata menyipit lebih rapat daripada sakit',
        senang_b < sakit_b, 'senang %.3f lawan sakit %.3f' % (senang_b, sakit_b))


def uji_rig(cek):
    """Bangun rig sungguhan, periksa tiap poros duduk di PANGKAL bagiannya.

    Definisi "pangkal" di sini bukan "lebih dekat ke pusat badan" — itu versi
    pertama pemeriksaan ini, dan uji mutasi membuktikannya BOCOR: memindahkan
    poros ekor sapi ke ujung bawah tetap lolos, karena ekor yang menggantung
    ke belakang punya dua ujung yang berjarak nyaris sama dari pusat badan
    (0,800 m vs 0,852 m).

    Yang dipakai sekarang definisi yang memang saya maksud: pangkal adalah
    ujung yang MENEMPEL pada bagian lain dari hewannya. Pangkal ekor menyentuh
    pantat; ujung ekor tidak menyentuh apa pun.
    """
    from panda3d.core import loadPrcFileData, Point3
    for k in ('load-display pandagl', 'window-type offscreen',
              'audio-library-name null'):
        loadPrcFileData('', k)
    import logging
    logging.basicConfig(level=logging.CRITICAL)
    from ursina import Ursina, Entity, application
    application.asset_folder = Path(__file__).resolve().parent.parent
    Ursina(development_mode=False)
    from game.animal_models import build_animal, _BUILDERS

    def kotak_lain(r, kecuali):
        """Kotak batas tiap part rig, kecuali keturunan simpul `kecuali`."""
        out = []

        def turun(e):
            if e is kecuali:
                return
            if getattr(e, 'model', None) is not None:
                lo, hi = e.getTightBounds(r)
                out.append((tuple(lo), tuple(hi)))
            for c in list(e.children):
                turun(c)
        turun(r)
        return out

    def jarak_ke(kotak, titik):
        d = float('inf')
        for lo, hi in kotak:
            dx = max(lo[0] - titik[0], 0.0, titik[0] - hi[0])
            dy = max(lo[1] - titik[1], 0.0, titik[1] - hi[1])
            dz = max(lo[2] - titik[2], 0.0, titik[2] - hi[2])
            d = min(d, math.sqrt(dx * dx + dy * dy + dz * dz))
        return d

    salah, n = [], 0
    for sp in sorted(_BUILDERS):
        r = Entity(position=(0, 0, 0))
        build_animal(r, sp, kunci=sp)
        for jenis in ('ekor', 'telinga'):
            for pv in getattr(r, '_pivot_' + jenis):
                n += 1
                anak = [c for c in pv.children if getattr(c, 'model', None)][0]
                u = pv._ujung
                a = r.getRelativePoint(anak, Point3(*u))
                b = r.getRelativePoint(anak, Point3(*[-v for v in u]))
                lain = kotak_lain(r, pv)
                da, db = jarak_ke(lain, a), jarak_ke(lain, b)
                # Dua syarat, dan keduanya perlu. Rumusan pertama memakai
                # margin tunggal `da > db - 0.02` dan itu salah: pada bagian
                # yang lebih pendek daripada marginnya sendiri, pangkal yang
                # MENEMPEL SEMPURNA (0,000 m) pun ikut dijatuhkan — telinga
                # kuda gagal dengan pangkal 0,000 m lawan ujung 0,015 m.
                #   (1) pangkal memang menempel ke bagian lain, dan
                #   (2) pangkal tidak lebih jauh daripada ujungnya.
                # Ekor buntut domba menempel di KEDUA ujungnya karena terbenam
                # di bulu; itu memang tidak bisa dibedakan, dan syarat ini
                # meloloskannya tanpa berpura-pura tahu.
                if da > 0.035 or da > db + 0.005:
                    salah.append('%s/%s (pangkal %.3f m vs ujung %.3f m)'
                                 % (sp, jenis, da, db))
    cek('tiap poros duduk di ujung yang menempel ke badan', not salah,
        '%d poros diperiksa%s' % (n, '' if not salah else '; SALAH: '
                                  + '; '.join(salah)))


def main():
    gagal, jumlah = [], []

    def cek(nama, ok, catatan):
        jumlah.append(nama)
        print('  %-44s %-7s %s' % (nama, 'LULUS' if ok else 'GAGAL', catatan))
        if not ok:
            gagal.append(nama)

    print('uji gerak telinga & ekor ternak')
    print('-' * 78)

    # ── 1. ekor diam: berayun, dan BUKAN metronom ───────────────────────
    ek = Simpul('z')
    g = GerakTernak([], [ek], 'sapi_betsy')
    de, _ = jalan(g, 120.0, ekor=ek)
    rentang = max(de) - min(de)
    jarak = lintas_nol(de)
    sd = statistics.pstdev(jarak) if len(jarak) > 2 else 0.0
    cek('ekor diam berayun (rentang >= 6 derajat)', rentang >= 6.0,
        'rentang %.1f derajat' % rentang)
    cek('ekor diam tidak berirama (sd > 0,02 s)', sd > 0.02,
        '%d ayunan, sd %.3f s' % (len(jarak), sd))

    # ── 2. disikat: ayunan MELEBAR ──────────────────────────────────────
    ek2 = Simpul('z')
    g2 = GerakTernak([], [ek2], 'sapi_betsy')
    jalan(g2, 6.0, ekor=ek2)
    diam, _ = jalan(g2, 20.0, sikat=0.0, ekor=ek2)
    jalan(g2, 2.0, sikat=1.0, ekor=ek2)          # beri waktu amplitudo menyusul
    rawat, _ = jalan(g2, 20.0, sikat=1.0, ekor=ek2)
    r_diam = max(diam) - min(diam)
    r_rawat = max(rawat) - min(rawat)
    cek('disikat: ayunan >= 2,5x lebih lebar', r_rawat >= r_diam * 2.5,
        '%.1f -> %.1f derajat (%.1fx)' % (r_diam, r_rawat, r_rawat / max(r_diam, 1e-6)))

    # ── 3. amplitudo naik BERTAHAP, bukan melompat ──────────────────────
    ek3 = Simpul('z')
    g3 = GerakTernak([], [ek3], 'sapi_betsy')
    jalan(g3, 5.0, ekor=ek3)
    a0 = abs(ek3.sudut())
    g3.tick(DT, 1.0, False)
    lompat = abs(abs(ek3.sudut()) - a0)
    cek('amplitudo tidak melompat di frame pertama (< 3 derajat)', lompat < 3.0,
        'lompatan %.2f derajat' % lompat)

    # ── 4. telinga berkedut, tidak berirama, tidak serempak ─────────────
    t1, t2 = Simpul('z', 1.0), Simpul('z', -1.0)
    g4 = GerakTernak([t1, t2], [], 'sapi_betsy')
    _, dt_ = jalan(g4, 180.0, telinga=[t1, t2])
    k1, k2 = kejadian(dt_[0]), kejadian(dt_[1])
    j1 = [b - a for a, b in zip(k1, k1[1:])]
    sd1 = statistics.pstdev(j1) if len(j1) > 2 else 0.0
    cek('telinga berkedut (>= 15 kali / 180 s)', len(k1) >= 15,
        'kiri %d, kanan %d' % (len(k1), len(k2)))
    cek('kedutan tidak berirama (sd > 0,3 s)', sd1 > 0.3,
        'jeda rata2 %.2f s, sd %.2f s' % (statistics.mean(j1) if j1 else 0, sd1))
    bareng = sum(1 for a in k1 if any(abs(a - b) < 0.12 for b in k2))
    cek('dua telinga tidak serempak (< 25% bareng)',
        bareng < max(1, len(k1)) * 0.25, '%d dari %d bareng' % (bareng, len(k1)))

    # ── 5. sentuhan memicu sentakan dalam < 150 ms ──────────────────────
    t3 = Simpul('z', 1.0)
    g5 = GerakTernak([t3], [], 'sapi_betsy')
    jalan(g5, 1.0, telinga=[t3])
    g5.sentuh()
    puncak, saat = 0.0, None
    for i in range(int(0.5 / DT)):
        g5.tick(DT, 1.0, False)
        v = abs(t3.rotation_z)
        if v > puncak:
            puncak, saat = v, (i + 1) * DT
    cek('sentuhan memicu sentakan telinga (>= 15 derajat)', puncak >= 15.0,
        'puncak %.1f derajat pada %.0f ms' % (puncak, (saat or 0) * 1000))

    # ── 6. malam: ekor melambat-menyempit, telinga berhenti ─────────────
    ek6 = Simpul('z')
    t6 = Simpul('z', 1.0)
    g6 = GerakTernak([t6], [ek6], 'sapi_betsy')
    jalan(g6, 8.0, tidur=True, ekor=ek6)
    de6, dt6 = jalan(g6, 120.0, tidur=True, ekor=ek6, telinga=[t6])
    r6 = max(de6) - min(de6)
    cek('malam: ekor menyempit (<= 40% rentang siang)', r6 <= rentang * 0.40,
        '%.1f vs %.1f derajat' % (r6, rentang))
    cek('malam: telinga berhenti berkedut', len(kejadian(dt6[0])) == 0,
        '%d kedutan' % len(kejadian(dt6[0])))

    # ── 7. fase per-ekor berbeda ────────────────────────────────────────
    sudut = []
    for kunci in ('sapi_betsy', 'kambing_jenggot', 'domba_woolly', 'kuda_pegasus'):
        e = Simpul('z')
        gg = GerakTernak([], [e], kunci)
        jalan(gg, 2.0, ekor=e)
        sudut.append(round(e.sudut(), 3))
    cek('fase ekor tiap ekor berbeda', len(set(sudut)) == len(sudut),
        'sudut pada t=2 s: %s' % sudut)

    uji_keadaan(cek)

    if '--rig' in sys.argv:
        uji_rig(cek)

    print('-' * 78)
    if gagal:
        print('%d uji GAGAL: %s' % (len(gagal), ', '.join(gagal)))
        return 1
    print('SEMUA %d UJI LULUS' % len(jumlah))
    return 0


if __name__ == '__main__':
    sys.exit(main())
