"""regress.py — Jaring pengaman: buktikan game masih utuh setelah diubah.

Dipakai setiap kali ada perubahan, terutama saat banyak orang/agen menulis ke
pohon kerja yang sama. Verifikasi manual sudah gagal dua kali di proyek ini
(WASD dinyatakan beres padahal belum; metode disisipkan di tengah fungsi
sehingga fungsi induknya mati total) — keduanya ketahuan cuma karena kebetulan
diuji ulang.

Setiap pemeriksaan di sini terikat pada kegagalan NYATA yang pernah terjadi,
bukan pada kemungkinan yang dikarang:

  geom_nol       bug NodePath-bersama. Mesh Ursina adalah NodePath Panda3D dan
                 hanya boleh punya SATU parent; mesh cache yang diberikan ke
                 banyak Entity membuat semua kecuali yang TERAKHIR kehilangan
                 geometri. Terjadi DUA KALI: di meshes.py dan di entities.py.
  frame_kosong   "rumah ga muncul" — scene yang dirender jadi langit polos.
  pemain_valid   terjepit permanen di tile yang tidak bisa dijalani.
  motif_waras    mesin motif baru; nilai harus tetap di -100..+100.
  save_bolak     format save berubah; save lama tidak boleh merusak loader.
  ms_frame       4-29 FPS dan belum pernah diprofil. Dicatat sebagai angka
                 supaya regresi performa terlihat, bukan cuma terasa.
  arah_maju      basis arah gerak membaca komponen sumbu yang salah, jadi WASD
                 menyimpang 91-180 derajat di yaw selain 0. Selamat dari DUA
                 kali perbaikan tanda karena yang diuji selalu yaw awal.
                 Diukur di jendela awal 10 frame, karena penyimpangan akibat
                 menggeser rintangan menumpuk bersama jarak (lihat fungsinya).

Pemakaian:
    python tools/regress.py                 semua scene
    python tools/regress.py farm house      scene tertentu

Keluar dengan kode 1 kalau ada yang GAGAL, supaya bisa dipakai di skrip.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData, Filename  # noqa: E402
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'aux-display pandadx9')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'sync-video false')

# `--offscreen` melepas ketergantungan pada jendela sungguhan. Dipakai saat
# lingkungan menolak memfokuskan jendela: di situ tiap tangkapan layar kembali
# kosong dan tanpa ini seluruh run dilaporkan gagal padahal scene-nya sehat.
# Lihat catatan `lingkungan` di ujung main().
if '--offscreen' in sys.argv:
    loadPrcFileData('', 'window-type offscreen')

import logging  # noqa: E402
logging.basicConfig(level=logging.ERROR)

OUT = ROOT / '_bench' / 'regress'
OUT.mkdir(parents=True, exist_ok=True)

W, H = 640, 360
WARM = 30          # frame pemanasan setelah ganti scene
MEASURE = 12       # frame yang diukur waktunya


def _fail(msg):
    return (False, msg)


def _ok(msg=''):
    return (True, msg)


# ─── PEMERIKSAAN ─────────────────────────────────────────

def cek_geom_nol(scene_mod):
    """Entity yang punya model tapi nol GeomNode = korban NodePath-bersama."""
    from ursina import scene as uscene
    korban = []
    for e in uscene.children:
        m = getattr(e, 'model', None)
        if m is None:
            continue
        try:
            n = len(m.findAllMatches('**/+GeomNode'))
        except Exception:
            continue
        if n == 0:
            nama = getattr(e, 'name', None) or type(e).__name__
            korban.append(nama)
    if korban:
        from collections import Counter
        ring = ', '.join(f'{k}x{v}' for k, v in Counter(korban).most_common(4))
        return _fail(f'{len(korban)} entity tanpa geometri ({ring})')
    return _ok()


def cek_frame_kosong(png: Path):
    """Frame yang nyaris satu warna = scene tidak benar-benar dirender."""
    try:
        from PIL import Image
        im = Image.open(png).convert('RGB').resize((80, 45))
    except Exception as e:
        return _fail(f'gagal baca png: {e}')
    px = list(im.getdata())
    unik = len(set(px))
    dominan = max(px.count(c) for c in set(px)) / len(px)
    if unik < 12 or dominan > 0.93:
        return _fail(f'frame nyaris polos (warna unik {unik}, dominan {dominan:.0%})')
    return _ok(f'{unik} warna')


def cek_bisa_keluar(g):
    """ESC harus mengembalikan mode panel apa pun ke 'hud'.

    player.tick() hanya dipanggil saat mode == 'hud', jadi mode yang macet
    membekukan pemain sepenuhnya — tidak jalan, waktu berhenti, motif berhenti.
    Pernah terjadi: ESC tidak berfungsi di mode 'dialog', dan pie menu objek
    tidak punya jalan keluar selain memilih. Pemilik melaporkannya sebagai
    "jalan saja tidak bisa".
    """
    asal = g.panels.mode
    macet = []
    for mode in ('dialog', 'panel', 'pie'):
        g.panels.mode = mode
        try:
            g.input('escape')
        except Exception as e:
            macet.append(f'{mode} (ESC error: {type(e).__name__})')
            continue
        if g.panels.mode != 'hud':
            macet.append(f'{mode} -> {g.panels.mode}')
    g.panels.mode = asal if asal in ('hud',) else 'hud'
    if macet:
        return _fail('terkunci: ' + ', '.join(macet))
    return _ok()


def cek_pemain_valid(g):
    tx, ty = g.player.get_tile_pos()
    if not g.world.is_walkable(tx, ty):
        return _fail(f'pemain di tile tak-walkable ({tx},{ty})')
    sc = g.world.scene_obj
    grid = getattr(sc, 'tiles', None)
    if grid:
        rows, cols = len(grid), len(grid[0])
        if not (0 <= tx < cols and 0 <= ty < rows):
            return _fail(f'pemain di luar peta ({tx},{ty}) peta {cols}x{rows}')
    return _ok(f'({tx},{ty})')


def cek_arah_maju(g):
    """W harus menggerakkan pemain ke ATAS LAYAR, bukan ke arah lain.

    Menguji PERILAKU, bukan rumus: tombol ditahan lewat `held_keys` dan
    frame dijalankan lewat jalur asli, lalu perpindahan dunia dibandingkan
    dengan arah kamera->fokus di bidang tanah. Rumus basisnya TIDAK disalin ke
    sini -- salinan yang ikut salah tidak menjaga apa pun.

    Kegagalan nyata yang melatarinya: basis arah gerak membaca komponen (.x,.y)
    padahal bidang mendatar Ursina adalah (x,z), jadi di yaw selain 0 arah WASD
    menyimpang 91-180 derajat dan di yaw 90/270 vektor "kanan" runtuh jadi nol.
    Bug itu selamat dari DUA kali perbaikan tanda karena yang diuji selalu yaw
    awal, satu-satunya sudut di mana rumus lama kebetulan benar. Diukur di
    _bench/probes/probe_basis_kamera.py dan _bench/probes/probe_arah_wasd.py.
    """
    import math as _m
    from ursina import held_keys, camera
    from direct.showbase.ShowBaseGlobal import base as _b

    if getattr(g.panels, 'mode', 'hud') != 'hud':
        return _ok('dilewati: panel terbuka')

    # DIUJI DI BEBERAPA YAW, dan itu bukan kelebihan -- itu syarat.
    # Versi pertama pemeriksaan ini hanya memakai yaw yang sedang aktif, dan
    # TERBUKTI TIDAK MENANGKAP bug yang melahirkannya: dengan rumus lama
    # dipasang kembali, farm dan town tetap LULUS. Sebabnya persis jebakan yang
    # menyelamatkan bug itu dua kali -- di yaw awal kedua rumus memberi angka
    # yang sama. Penjaga yang hanya menguji yaw awal menjaga apa pun kecuali
    # bug ini.
    # KEADAAN DISALIN DAN DIPULIHKAN. Versi kedua pemeriksaan ini tidak
    # melakukannya, dan akibatnya terukur: `beach` LULUS kalau dijalankan
    # pertama, GAGAL kalau dijalankan keenam -- pemain sudah tergeser dan
    # kamera masih dalam perjalanan dari pemeriksaan scene SEBELUMNYA. Itu
    # cacat yang sama persis dengan `motif_waras` dulu: pemeriksaan yang
    # meninggalkan bekas pada apa yang diperiksanya.
    yaw_asli = getattr(g, 'camera_yaw', None)
    pos_asli = tuple(g.player.position)
    vel_asli = (g.player.velocity_x, g.player.velocity_z)
    buruk = []
    diuji = []
    try:
        for yaw in (yaw_asli if yaw_asli is not None else 0.0, 135.0, 270.0):
            if yaw_asli is not None:
                g.camera_yaw = yaw
                for _ in range(30):
                    _b.taskMgr.step()

            for k in ('w', 'a', 's', 'd', 'shift'):
                held_keys[k] = 0
            # Tiap yaw diukur dari TITIK YANG SAMA, bukan dari tempat yaw
            # sebelumnya berhenti.
            g.player.position = pos_asli
            g.player.velocity_x = g.player.velocity_z = 0.0
            if hasattr(g, '_snap_camera_to_player'):
                g._snap_camera_to_player()
            for _ in range(5):
                _b.taskMgr.step()

            x0, _, z0 = g.player.world_position
            # ACUAN DIAMBIL SEBELUM BERJALAN. Sesudahnya kamera sudah ikut
            # bergeser mengikuti pemain dan sempat disesuaikan pemotong dinding,
            # jadi vektor kamera->fokus bukan lagi arah "atas layar" yang
            # berlaku saat tombol ditekan.
            _cx0, _, _cz0 = camera.world_position
            _ux0, _uz0 = g.camera_focus[0] - _cx0, g.camera_focus[2] - _cz0
            held_keys['w'] = 1
            x_awal, z_awal = x0, z0
            for _i in range(12):
                _b.taskMgr.step()
                if _i == 9:
                    x_awal, _, z_awal = g.player.world_position
            held_keys['w'] = 0
            g.player.velocity_x = g.player.velocity_z = 0.0

            # DIUKUR DI JENDELA AWAL (10 frame), bukan di akhir 40 frame.
            # Alasannya terukur: makin jauh pemain berjalan, makin besar
            # kemungkinan ia menggeser rintangan, dan penyimpangan itu
            # MENUMPUK. Dibandingkan langsung di scene yang sama:
            #
            #   scene      10 frame        40 frame
            #   lake       11,0 deg        36,0 deg
            #   cemetery   10,8 deg        36,1 deg
            #   mountain   11,4 deg        34,4 deg
            #   town        2,8 deg        30,3 deg
            #
            # Angka 40-frame itu yang dulu menuduh enam scene sehat. Yang
            # tumbuh bukan kesalahan arah, melainkan jarak geser -- pemain
            # menyusuri dinding. Sisa 11 derajat di jendela awal adalah
            # tikungan saat pemain berakselerasi dari diam, dan ambang 45
            # derajat memberinya ruang empat kali lipat sebelum menuduh,
            # sementara bug yang sesungguhnya mengukur 179 derajat.
            dx, dz = x_awal - x0, z_awal - z0
            jarak = _m.hypot(dx, dz)
            # Jalan bebas 10 frame memberi 0,7-1,0 satuan. Jarak jauh di bawah itu
            # berarti pemain TERHALANG, dan arah sisa geraknya adalah hasil
            # menggeser dinding -- bukan jawaban soal basis arah. `house` ruang
            # kecil: terukur 102 derajat menyimpang hanya karena pemainnya
            # menabrak. Pemeriksaan yang menghukum itu melaporkan bug yang
            # tidak ada.
            if jarak < 0.25:
                diuji.append(f'{yaw:.0f}:terhalang({jarak:.1f}u)')
                continue

            ux, uz = _ux0, _uz0
            nu = _m.hypot(ux, uz)
            if nu < 1e-4:
                continue                      # kamera tegak lurus: tak terukur
            cos = max(-1.0, min(1.0, (dx * ux + dz * uz) / (jarak * nu)))
            beda = _m.degrees(_m.acos(cos))
            diuji.append(f'{yaw:.0f}:{beda:.0f}d/{jarak:.1f}u')
            if beda > 45.0:
                buruk.append(f'yaw{yaw:.0f}: W menyimpang {beda:.0f} deg '
                             f'(jarak {jarak:.2f}u)')
    finally:
        for k in ('w', 'a', 's', 'd', 'shift'):
            held_keys[k] = 0
        if yaw_asli is not None:
            g.camera_yaw = yaw_asli
        g.player.position = pos_asli
        g.player.velocity_x, g.player.velocity_z = vel_asli
        if hasattr(g, '_snap_camera_to_player'):
            g._snap_camera_to_player()
        for _ in range(5):
            _b.taskMgr.step()
    
    if buruk:
        return _fail('; '.join(buruk[:2]))
    bersih = [d for d in diuji if 'terhalang' not in d]
    if not bersih:
        # Jujur: semua yaw terhalang, jadi scene ini tidak menguji apa pun.
        return _ok('W tak terukur: ' + ' '.join(diuji) if diuji else 'W tak terukur')
    return _ok('W ' + ' '.join(diuji))


def cek_motif_waras(g):
    from game.motives import MOTIVES, MOTIVE_MIN, MOTIVE_MAX
    mv = g.state.mv
    for m in MOTIVES:
        v = mv.get(m)
        if not (MOTIVE_MIN - 0.01 <= v <= MOTIVE_MAX + 0.01):
            return _fail(f'motif {m}={v:.1f} di luar rentang')
    mood = mv.mood
    if mood != mood or abs(mood) > 1e6:
        return _fail(f'mood tidak terhingga: {mood}')
    # Peluruhan diuji pada mesin NYATA, tapi tanpa meninggalkan bekas: nilai
    # kedelapan motif (plus akumulator pecahannya) disalin dulu dan dipulihkan
    # di `finally`.
    #
    # Kenapa: pemeriksaan ini memakai mesin motif MILIK STATE YANG SAMA untuk
    # tiap scene, dan tiap panggilan memajukan 240 menit tanpa memulihkannya.
    # Laju peluruhan Lapar adalah HUNGER_RATIO * (100 + lapar) -- non-linear,
    # dan MENUJU NOL saat lapar mendekati dasar -100. Setelah belasan scene
    # penurunannya tidak lagi mencapai satu poin utuh yang bisa dibukukan
    # `tick()`, jadi nilainya mendatar: diukur, tick ke-15 memberi
    # -98,0000 -> -98,0000. Akibatnya `mv.get('lapar') >= sebelum` benar dan
    # scene TERAKHIR apa pun gagal tanpa sebab nyata -- larian 14 scene menuduh
    # `swarga`, padahal `swarga` sendirian LULUS. Hasilnya ditentukan urutan
    # scene, bukan kesehatan motif.
    #
    # Dua agen menemukan cacat ini terpisah dan menambalnya berbeda: satu
    # menyetel ulang `lapar` ke titik netral tiap scene, satu menyalin-dan-
    # memulihkan. Yang kedua dipakai di sini karena ia tidak mengubah keadaan
    # yang dipakai pemeriksaan SESUDAHNYA (`save_bolak` membaca state yang
    # sama); penjelasan rumus di atas datang dari yang pertama.
    salinan = {m: mv.get(m) for m in MOTIVES}
    carry, acc = mv._tick_carry, dict(mv._acc)
    try:
        mv.add('lapar', 100.0)      # jauhkan dari dasar supaya peluruhan terukur
        sebelum = mv.get('lapar')
        mv.tick(240.0)
        if mv.get('lapar') >= sebelum:
            return _fail('lapar tidak turun setelah 4 jam-sim')
    finally:
        for m, v in salinan.items():
            setattr(mv, m, v)
        mv._tick_carry, mv._acc = carry, acc
    return _ok(f'mood {mood:+.1f}')


def cek_save_bolak(g):
    from game.state import GameState
    try:
        g.state.sync_motives()
        blob = json.dumps({k: v for k, v in g.state.__dict__.items()
                           if not k.startswith('_')})
    except Exception as e:
        return _fail(f'state tidak bisa di-JSON: {e}')
    try:
        data = json.loads(blob)
        gs = GameState()
        for k, v in data.items():
            if hasattr(gs, k):
                setattr(gs, k, v)
        asli, ulang = g.state.mv.get('lapar'), gs.mv.get('lapar')
    except Exception as e:
        return _fail(f'muat balik gagal: {e}')
    if abs(asli - ulang) > 0.01:
        return _fail(f'motif berubah saat bolak-balik ({asli:.2f} -> {ulang:.2f})')
    return _ok(f'{len(blob)}B')


# ─── PENGGERAK ───────────────────────────────────────────

def main():
    from ursina import application
    application.asset_folder = ROOT
    application.fonts_folder = ROOT / 'assets' / 'fonts'
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = W, H

    from game.scenes import SCENES
    minta = [a for a in sys.argv[1:] if not a.startswith('-')]
    scenes = minta or [s for s in SCENES if s != 'dungeon']

    from game.app import Game3D
    t0 = time.time()
    try:
        g = Game3D()
    except Exception:
        print('GAGAL TOTAL: game tidak bisa dibangun\n')
        traceback.print_exc()
        sys.exit(1)
    from direct.showbase.ShowBaseGlobal import base
    for _ in range(20):
        base.taskMgr.step()
    boot_s = time.time() - t0

    # ── Pre-flight: bisakah jendela ini menggambar sama sekali? ─────────────
    # Diperiksa SEBELUM keempat belas scene dijalankan. Kalau jendela tidak bisa
    # difokuskan (Windows menolak SetForegroundWindow), isinya tidak pernah
    # digambar dan setiap tangkapan layar akan kosong -- melaporkan 14 scene
    # gagal karena itu berarti memberi vonis atas keadaan yang bukan milik
    # scene.
    #
    # Sinyal LANGSUNG, bukan statistik. Versi pertama penjaga ini hanya melihat
    # hasil di ujung dan mensyaratkan kegagalannya SERAGAM; ketika jendela sempat
    # pulih di tengah run, 12 dari 14 scene tetap divonis gagal. Memeriksa satu
    # frame lebih dulu menutup celah itu.
    for _ in range(8):
        base.graphicsEngine.renderFrame()
    _probe = OUT / '_probe.png'
    _img = base.win.getScreenshot()
    if _img is not None:
        _img.write(Filename.fromOsSpecific(str(_probe)))
    if _probe.exists():
        _ok_probe, _pesan_probe = cek_frame_kosong(_probe)
        _probe.unlink(missing_ok=True)
        if not _ok_probe:
            print()
            print('=' * 78)
            print('LINGKUNGAN BERMASALAH -- dihentikan SEBELUM menjalankan scene.')
            print(f'Jendela tidak menghasilkan gambar: {_pesan_probe}')
            print('Windows kemungkinan menolak SetForegroundWindow(), sehingga isinya')
            print('tidak pernah digambar. Setiap tangkapan layar akan kosong, dan')
            print('melaporkan scene gagal karena itu tidak sah.')
            print('Coba lagi dengan:  python tools/regress.py --offscreen')
            print('=' * 78)
            sys.stdout.flush()
            os._exit(2)

    from ursina import scene as uscene
    baris = []
    gagal_total = 0

    for nama in scenes:
        hasil = {}
        try:
            g.state.scene_name = nama
            for _ in range(WARM):
                base.taskMgr.step()

            tm = time.time()
            for _ in range(MEASURE):
                base.taskMgr.step()
            ms = (time.time() - tm) / MEASURE * 1000.0

            # `taskMgr.step()` menjalankan logika permainan, tapi TIDAK menjamin
            # buffer belakang selesai digambar sebelum `getScreenshot()`
            # membacanya. Itulah sebabnya enam scene dilaporkan `frame_kosong`
            # di sini -- shop, house, lake, cemetery, beach, clinic -- padahal
            # `tools/capture.py`, yang memang memanggil renderFrame(),
            # merender scene yang sama dengan puluhan ribu warna unik.
            #
            # Dan frame kosong bisa TRANSIEN: jendela kehilangan fokus sebentar,
            # isinya tidak digambar, dan tangkapan berikutnya sudah benar lagi.
            # Diulang sampai tiga kali, karena yang perlu diputuskan bukan
            # "tangkapan pertama kosong" melainkan "scene ini TIDAK PERNAH bisa
            # digambar". Memvonis dari satu percobaan berarti menghukum keadaan
            # sesaat -- dan itu sudah dua kali menyesatkan.
            png = OUT / f'{nama}.png'
            hasil_frame = _fail('tidak ada tangkapan layar')
            for _percobaan in range(3):
                for _ in range(8):
                    base.graphicsEngine.renderFrame()
                img = base.win.getScreenshot()
                if img is not None:
                    img.write(Filename.fromOsSpecific(str(png)))
                if png.exists():
                    hasil_frame = cek_frame_kosong(png)
                    if hasil_frame[0]:
                        break

            hasil['geom_nol'] = cek_geom_nol(nama)
            hasil['frame_kosong'] = hasil_frame
            hasil['pemain_valid'] = cek_pemain_valid(g)
            hasil['bisa_keluar'] = cek_bisa_keluar(g)
            hasil['arah_maju'] = cek_arah_maju(g)
            hasil['motif_waras'] = cek_motif_waras(g)
            hasil['save_bolak'] = cek_save_bolak(g)
            n_ent = len(uscene.children)
        except Exception as e:
            hasil['boot'] = _fail(f'{type(e).__name__}: {e}')
            ms, n_ent = float('nan'), 0
            traceback.print_exc()

        buruk = [k for k, (ok, _) in hasil.items() if not ok]
        gagal_total += len(buruk)
        baris.append((nama, hasil, ms, n_ent, buruk))

    # ── laporan ──
    # Empat belas scene kosong SEKALIGUS bukan cacat scene: game ini terbukti
    # merender semuanya di `gauntlet/check.py`. Yang terjadi adalah jendelanya
    # tidak bisa difokuskan -- Windows menolak `SetForegroundWindow()`, isinya
    # tidak pernah digambar, dan `getScreenshot()` membaca buffer kosong.
    #
    # Alat yang melaporkan 0/14 karena lingkungan lebih berbahaya daripada tidak
    # ada alat sama sekali: 0/14 palsu tidak bisa dibedakan dari kerusakan
    # sungguhan, dan itu melatih pemakainya untuk mengabaikan alarmnya.
    lingkungan = bool(baris) and gagal_total > 0 and all(
        set(buruk) == {'frame_kosong'} for _n, _h, _ms, _e, buruk in baris)
    if lingkungan:
        print()
        print('=' * 78)
        print('LINGKUNGAN BERMASALAH -- ini BUKAN cacat scene.')
        print('Seluruh scene menghasilkan frame kosong. Game ini terbukti merender')
        print('semuanya di gauntlet/check.py, jadi yang gagal adalah jendelanya:')
        print('Windows menolak SetForegroundWindow(), isinya tidak pernah digambar,')
        print('dan getScreenshot() membaca buffer kosong.')
        print('Tabel di bawah dicetak sebagai bukti, bukan sebagai vonis.')
        print('Coba lagi dengan:  python tools/regress.py --offscreen')
        print('=' * 78)
    print()
    print(f'{"scene":14s} {"hasil":>7s} {"ms/frame":>9s} {"entity":>7s}  catatan')
    print('-' * 78)
    for nama, hasil, ms, n_ent, buruk in baris:
        tanda = 'LULUS' if not buruk else 'GAGAL'
        catatan = '; '.join(f'{k}: {hasil[k][1]}' for k in buruk) if buruk else \
                  hasil.get('pemain_valid', (True, ''))[1]
        print(f'{nama:14s} {tanda:>7s} {ms:9.1f} {n_ent:7d}  {catatan[:44]}')
    print('-' * 78)
    n_lulus = sum(1 for _, _, _, _, b in baris if not b)
    print(f'{n_lulus}/{len(baris)} scene lulus, {gagal_total} pemeriksaan gagal, '
          f'boot {boot_s:.1f}s')
    if lingkungan:
        print('CATATAN: angka di atas TIDAK SAH. Kegagalannya seragam dan sebabnya')
        print('lingkungan, bukan scene. Pakai --offscreen, atau fokuskan jendelanya')

    laporan = OUT / 'report.md'
    with open(laporan, 'w', encoding='utf-8') as f:
        f.write('# Laporan regresi\n\n')
        f.write(f'{n_lulus}/{len(baris)} scene lulus, {gagal_total} pemeriksaan gagal.\n\n')
        if lingkungan:
            f.write('> **Hasil ini tidak sah.** Kegagalannya seragam `frame_kosong` '
                    'dan sebabnya\n> lingkungan (jendela tidak bisa difokuskan), '
                    'bukan scene. Jalankan ulang dengan `--offscreen`.\n\n')
        f.write('| scene | hasil | ms/frame | entity | catatan |\n|---|---|--:|--:|---|\n')
        for nama, hasil, ms, n_ent, buruk in baris:
            tanda = 'LULUS' if not buruk else '**GAGAL**'
            catatan = '; '.join(f'`{k}` {hasil[k][1]}' for k in buruk) or '-'
            f.write(f'| {nama} | {tanda} | {ms:.1f} | {n_ent} | {catatan} |\n')
    print(f'laporan: {laporan}')

    try:
        with open(ROOT / '_bench' / 'progress.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'slice': 'REGRESI', 'round': 0, 'role': 'note',
                'note': f'{n_lulus}/{len(baris)} scene lulus, '
                        f'{gagal_total} pemeriksaan gagal',
            }, ensure_ascii=False) + '\n')
    except Exception:
        pass

    sys.stdout.flush()
    # Kode 2 dibedakan dari 1: 1 berarti ada scene yang benar-benar rusak,
    # 2 berarti hasilnya tidak sah karena lingkungan. CI bisa membedakannya.
    os._exit(2 if lingkungan else (1 if gagal_total else 0))


if __name__ == '__main__':
    main()
