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
  kanal_jenuh    rumput siang terbaca neon: albedo (148,205,105) sampai ke
                 layar sebagai (230,255,90) dengan kanal hijau MENTOK, jadi
                 gradasinya hilang. Dicatat sebagai angka, bukan lulus/gagal.
  hud_layar      HUD terpotong tepi layar. Jam, tanggal, cuaca, nama scene dan
                 baris bantuan semuanya lari keluar tepi kanan karena dipatok
                 ke angka tetap (x=0,70) padahal tepi UI mengikuti rasio layar.
  arah_wasd      arah WASD terbalik. Kegagalan yang PALING sering kembali di
                 proyek ini — tiga kali, dan tiap kali "diperbaiki" dengan
                 membalik tanda sampai terasa benar. Diukur sekali di akhir
                 lewat tools/probe_arah.py, alat ukur yang sama dengan probe
                 manual, supaya tidak ada dua kebenaran.
  rawat_ternak   husbandry.py kini sumber kebenaran ternak dan peluruhan
                 hariannya hidup lagi. Kombinasi itu pernah merusak: peluruhan
                 tanpa perawatan yang terjangkau membuat kedelapan ternak sakit
                 permanen di hari 4. Diperiksa dari DUA sisi -- yang dirawat
                 selamat dan benar-benar panen, yang ditelantarkan menanggung.
  bentuk_gua     cutaway dinding ala Sims 1 benar untuk rumah, tapi di gua
                 dinding BUKAN pembatas ruangan — dinding ADALAH ruangannya.
                 Aturan lama memangkas 53-72% seluruh dinding gua sekaligus,
                 menyisakan lapangan datar bertabur tunggul. Diperiksa dua
                 angka sekaligus: gua tetap berbentuk DAN pemain tidak
                 tertutup batu; memperbaiki satu saja menukar cacat.
  panel_wishes   mesin Keinginan (Tahap 4) benar tapi tak terjangkau adalah
                 kegagalan yang TIDAK terlihat sebagai error — persis yang
                 terjadi pada husbandry.py. Diperiksa lewat jalur tombol
                 sungguhan: [l] membuka, [1] berjanji, [6] melupakan,
                 [a] membeli hadiah, ESC menutup.
  rumput_hidup   uniform `grs_time` sekarang didorong SEKALI ke `scene`, bukan
                 ke tiap entity rumput (147x lebih murah). Yang membuatnya aman
                 cuma satu syarat: tidak boleh ada input per-entity yang
                 menindihnya. Kalau ada, rumputnya membeku TANPA error — jadi
                 diukur, lewat tools/probe_rumput.py, dengan menghitung piksel
                 yang bergerak.

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


def cek_kanal_jenuh(png: Path):
    """Berapa banyak layar yang kanal warnanya mentok 255 (detailnya hilang).

    Diukur karena rumput siang terbaca neon: albedo-nya (148,205,105) tapi yang
    sampai ke layar (230,255,90) — kanal hijau MENTOK, jadi bayangan dan
    gradasi di rumput hilang sama sekali dan papan catur di bawahnya berubah
    jadi dua pita datar. app.py sendiri menulis invarian "ambient + sun x dot
    <= 100% agar warna tidak overflow putih"; nilai yang dipakai sekarang
    (amb 95, sun 255) jauh di atas plafon yang dicatat komentarnya (70/185).

    Dicatat sebagai ANGKA, bukan lulus/gagal, seperti ms/frame: yang penting
    regresinya terlihat. Gagal hanya kalau sudah terang-terangan terbakar.
    """
    try:
        from PIL import Image
        im = Image.open(png).convert('RGB').resize((160, 90))
    except Exception as e:
        return _fail(f'gagal baca png: {e}'), 0.0
    px = list(im.getdata())
    jenuh = sum(1 for p in px if max(p) >= 255) / len(px)
    if jenuh > 0.25:
        return _fail(f'{jenuh:.0%} layar terbakar (kanal mentok)'), jenuh
    return _ok(f'{jenuh:.0%}'), jenuh

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
    # Peluruhan diuji pada SALINAN, bukan pada state yang dipakai game.
    #
    # Kedua cabang memperbaiki bug yang sama — pemeriksaan ini memakai SATU
    # mesin motif untuk semua scene, tiap panggilan memajukan 240 menit, dan
    # setelah belasan scene `lapar` menempel di lantai -100 tempat laju
    # peluruhannya menjadi nol; scene terakhir lalu GAGAL semata-mata karena
    # berdiri paling belakang di antrean. Cabang dasar menyelesaikannya dengan
    # mengembalikan `lapar` ke titik netral sebelum diuji. Yang dipakai di sini
    # menguji salinannya, sehingga mencapai keterurutan yang sama TANPA
    # menyentuh state hidup yang dipakai pemeriksaan lain di scene yang sama.
    import copy
    try:
        uji = copy.deepcopy(mv)
    except Exception:
        uji = mv        # kalau tidak bisa disalin, lebih baik tetap diuji
    sebelum = uji.get('lapar')
    uji.tick(240.0)
    sesudah = uji.get('lapar')
    if sesudah >= sebelum and sesudah > MOTIVE_MIN + 5.0:
        return _fail(f'lapar tidak turun setelah 4 jam-sim ({sebelum:.1f} -> {sesudah:.1f})')
    if sesudah < MOTIVE_MIN - 0.01:
        return _fail(f'lapar tembus lantai ({sesudah:.1f} < {MOTIVE_MIN})')
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
    application.fonts_folder = ROOT / 'fonts'
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
            if png.exists():
                hasil['kanal_jenuh'], jenuh = cek_kanal_jenuh(png)
            else:
                jenuh = float('nan')
            hasil['pemain_valid'] = cek_pemain_valid(g)
            hasil['bisa_keluar'] = cek_bisa_keluar(g)
            hasil['motif_waras'] = cek_motif_waras(g)
            hasil['save_bolak'] = cek_save_bolak(g)
            n_ent = len(uscene.children)
        except Exception as e:
            hasil['boot'] = _fail(f'{type(e).__name__}: {e}')
            ms, n_ent, jenuh = float('nan'), 0, float('nan')
            traceback.print_exc()

        buruk = [k for k, (ok, _) in hasil.items() if not ok]
        gagal_total += len(buruk)
        baris.append((nama, hasil, ms, n_ent, buruk, jenuh))

    # ── arah WASD (sekali saja; mahal, dan tidak bergantung scene) ──
    arah_baris = []
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from probe_arah import uji_arah
        for key, ok, catatan, _ in uji_arah(g, base):
            arah_baris.append((key, ok, catatan))
            if not ok:
                gagal_total += 1
    except Exception as e:
        arah_baris.append(('?', False, f'probe arah gagal jalan: {e}'))
        gagal_total += 1

    # ── HUD terpotong tepi layar (sekali saja, tidak bergantung scene) ──
    hud_baris = []
    try:
        from probe_hud import uji_hud
        for nama, ok, catatan in uji_hud(g):
            if not ok:
                hud_baris.append((nama, catatan))
                gagal_total += 1
    except Exception as e:
        hud_baris.append(('?', f'probe HUD gagal jalan: {e}'))
        gagal_total += 1

    # ── animasi rumput masih hidup (sekali saja, butuh render penuh) ──
    rumput_baris = []
    try:
        from probe_rumput import uji_rumput
        ok, catatan = uji_rumput(g, 'farm')
        rumput_baris.append((ok, catatan))
        if not ok:
            gagal_total += 1
    except Exception as e:
        rumput_baris.append((False, f'probe rumput gagal jalan: {e}'))
        gagal_total += 1

    # ── panel Keinginan terjangkau pemain (Tahap 4) ──
    # Mesinnya diuji terpisah di tools/uji_wishes.py; yang diperiksa di sini
    # keterjangkauannya lewat jalur tombol sungguhan. Sistem yang benar tapi
    # tak terjangkau sudah pernah terjadi di proyek ini (husbandry.py), dan
    # kegagalannya tidak kelihatan sebagai error apa pun.
    wish_baris = []
    try:
        import probe_wishes
        probe_wishes.uji_panel_hidup(g)
        buruk_w = [(n, k) for n, ok, k in probe_wishes.hasil if not ok]
        n_w = len(probe_wishes.hasil)
        wish_baris.append((not buruk_w,
                           f'{n_w - len(buruk_w)}/{n_w} pemeriksaan panel lulus'
                           + ('; ' + '; '.join(f'{n}: {k}' for n, k in buruk_w[:2])
                              if buruk_w else '')))
        gagal_total += len(buruk_w)
    except Exception as e:
        wish_baris.append((False, f'probe keinginan gagal jalan: {e}'))
        gagal_total += 1

    # ── loop perawatan ternak (husbandry jadi sumber kebenaran) ──
    # Peluruhan harian husbandry pernah berjalan TANPA aksi perawatan yang
    # terjangkau, dan itu membuat kedelapan ternak sakit permanen di hari 4.
    # Sekarang keduanya tersambung; yang dijaga di sini pasangan itu tetap utuh
    # dari KEDUA sisi -- yang dirawat selamat, yang ditelantarkan menanggung.
    ternak_baris = []
    try:
        import probe_ternak
        probe_ternak.uji_ternak(g)
        buruk_t = [(n, k) for n, ok, k in probe_ternak.hasil if not ok]
        n_t = len(probe_ternak.hasil)
        ternak_baris.append((not buruk_t,
                             f'{n_t - len(buruk_t)}/{n_t} pemeriksaan ternak lulus'
                             + ('; ' + '; '.join(f'{n}: {k}' for n, k in buruk_t[:2])
                                if buruk_t else '')))
        gagal_total += len(buruk_t)
    except Exception as e:
        ternak_baris.append((False, f'probe ternak gagal jalan: {e}'))
        gagal_total += 1

    # ── bentuk gua vs keterlihatan pemain ──
    # Dua angka yang harus benar BERSAMAAN: gua tetap berbentuk, dan pemain
    # tidak tertutup batu. Memperbaiki satu saja menukar cacat dengan cacat.
    gua_baris = []
    try:
        import probe_gua
        probe_gua.uji_gua(g)
        buruk_g = [(n, k) for n, ok, k in probe_gua.hasil if not ok]
        n_g = len(probe_gua.hasil)
        gua_baris.append((not buruk_g,
                          f'{n_g - len(buruk_g)}/{n_g} pemeriksaan gua lulus'
                          + ('; ' + '; '.join(f'{n}: {k}' for n, k in buruk_g[:2])
                             if buruk_g else '')))
        gagal_total += len(buruk_g)
    except Exception as e:
        gua_baris.append((False, f'probe gua gagal jalan: {e}'))
        gagal_total += 1

    # ── laporan ──
    # Empat belas scene kosong SEKALIGUS bukan cacat scene: game ini terbukti
    # merender semuanya di `gauntlet/check.py`. Yang terjadi adalah jendelanya
    # tidak bisa difokuskan -- Windows menolak `SetForegroundWindow()`, isinya
    # tidak pernah digambar, dan `getScreenshot()` membaca buffer kosong.
    #
    # Alat yang melaporkan 0/14 karena lingkungan lebih berbahaya daripada tidak
    # ada alat sama sekali: 0/14 palsu tidak bisa dibedakan dari kerusakan
    # sungguhan, dan itu melatih pemakainya untuk mengabaikan alarmnya.
    # `baris` berisi tuple ENAM elemen (nama, hasil, ms, entity, buruk, jenuh);
    # baris ini dulu membongkarnya jadi lima dan meledak dengan
    # "too many values to unpack". Tidak pernah terlihat karena hanya dijalankan
    # saat `gagal_total > 0` -- jadi alat ini akan CRASH persis pada saat ia
    # paling dibutuhkan, yaitu ketika ada yang benar-benar gagal, dan menelan
    # laporan kegagalan yang sudah susah payah dikumpulkan. Dibongkar lewat
    # indeks supaya penambahan kolom berikutnya tidak mengulanginya.
    lingkungan = bool(baris) and gagal_total > 0 and all(
        set(b[4]) == {'frame_kosong'} for b in baris)
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
    print(f'{"scene":14s} {"hasil":>7s} {"ms/frame":>9s} {"entity":>7s} {"jenuh":>6s}  catatan')
    print('-' * 86)
    for nama, hasil, ms, n_ent, buruk, jenuh in baris:
        tanda = 'LULUS' if not buruk else 'GAGAL'
        catatan = '; '.join(f'{k}: {hasil[k][1]}' for k in buruk) if buruk else \
                  hasil.get('pemain_valid', (True, ''))[1]
        print(f'{nama:14s} {tanda:>7s} {ms:9.1f} {n_ent:7d} {jenuh:5.0%}  {catatan[:44]}')
    print('-' * 86)
    tanda_hud = 'LULUS' if not hud_baris else 'GAGAL'
    ring_hud = '; '.join(f'{k} {c}' for k, c in hud_baris) or 'semua di dalam layar'
    print(f'{"HUD di layar":14s} {tanda_hud:>7s} {"":>9s} {"":>7s}  {ring_hud[:44]}')
    tanda_arah = 'LULUS' if all(ok for _, ok, _ in arah_baris) else 'GAGAL'
    rangkum = ', '.join(f'{k.upper()}={c.split(" ")[0]}' for k, ok, c in arah_baris)
    print(f'{"arah WASD":14s} {tanda_arah:>7s} {"":>9s} {"":>7s}  {rangkum[:44]}')
    ok_rumput, catatan_rumput = rumput_baris[0] if rumput_baris else (True, '-')
    tanda_rumput = 'LULUS' if ok_rumput else 'GAGAL'
    print(f'{"rumput hidup":14s} {tanda_rumput:>7s} {"":>9s} {"":>7s}  {catatan_rumput[:44]}')
    ok_wish, catatan_wish = wish_baris[0] if wish_baris else (True, '-')
    print(f'{"panel wishes":14s} {"LULUS" if ok_wish else "GAGAL":>7s} '
          f'{"":>9s} {"":>7s}  {catatan_wish[:44]}')
    ok_gua, catatan_gua = gua_baris[0] if gua_baris else (True, '-')
    print(f'{"bentuk gua":14s} {"LULUS" if ok_gua else "GAGAL":>7s} '
          f'{"":>9s} {"":>7s}  {catatan_gua[:44]}')
    ok_ternak, catatan_ternak = ternak_baris[0] if ternak_baris else (True, '-')
    print(f'{"rawat ternak":14s} {"LULUS" if ok_ternak else "GAGAL":>7s} '
          f'{"":>9s} {"":>7s}  {catatan_ternak[:44]}')
    print('-' * 78)
    n_lulus = sum(1 for _, _, _, _, b, _ in baris if not b)
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
        f.write('| scene | hasil | ms/frame | entity | jenuh | catatan |\n|---|---|--:|--:|--:|---|\n')
        for nama, hasil, ms, n_ent, buruk, jenuh in baris:
            tanda = 'LULUS' if not buruk else '**GAGAL**'
            catatan = '; '.join(f'`{k}` {hasil[k][1]}' for k in buruk) or '-'
            f.write(f'| {nama} | {tanda} | {ms:.1f} | {n_ent} | {jenuh:.0%} | {catatan} |\n')
        f.write(f'\n## HUD\n\n{ring_hud}\n')
        f.write(f'\n## Animasi rumput\n\n'
                f'{"LULUS" if ok_rumput else "**GAGAL**"} — {catatan_rumput}\n')
        f.write(f'\n## Panel Keinginan\n\n'
                f'{"LULUS" if ok_wish else "**GAGAL**"} — {catatan_wish}\n')
        f.write(f'\n## Bentuk gua\n\n'
                f'{"LULUS" if ok_gua else "**GAGAL**"} — {catatan_gua}\n')
        f.write(f'\n## Perawatan ternak\n\n'
                f'{"LULUS" if ok_ternak else "**GAGAL**"} — {catatan_ternak}\n')
        f.write('\n## Arah WASD\n\n| tombol | hasil | catatan |\n|---|---|---|\n')
        for k, ok, c in arah_baris:
            f.write(f'| {k.upper()} | {"LULUS" if ok else "**GAGAL**"} | {c} |\n')
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
