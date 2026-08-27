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
  hud_muat       HUD terpotong di tepi kanan: jam, tanggal, nama scene, dan
                 baris kontrol tumbuh melewati tepi layar karena dijangkar di
                 KIRI pada koordinat mati 0.70/0.60, sementara camera.ui
                 sebenarnya membentang -aspect/2..+aspect/2. Bertahan lama
                 justru karena cuma bisa dilihat: tiap screenshot dinilai
                 dengan mata, dan mata memaafkan. Sekarang jadi angka.
  hud_terbaca    panel motif terbaca mati sejak awal. Termometernya selalu
                 ada; yang salah urutan gambarnya — latar panel menang di bin
                 transparan Panda dan menutupi barnya. Diukur dari PIKSEL
                 tangkapan layar, bukan dari properti color, supaya "ada di
                 memori" tidak lagi dianggap sama dengan "terlihat".
  rumput_catur   rumput luar ruang terbaca sebagai papan catur. Tint ubin
                 dipilih (tx+ty) % 2 — periode DUA, pola paling teratur yang
                 bisa dibuat, dan mata mengunci grid-nya sebelum sempat
                 membacanya sebagai tanah. Diukur sebagai korelasi antara
                 terang ubin dan paritasnya, jadi "sudah tidak catur" jadi
                 angka, bukan pendapat.
  avatar_warna   di mesin tanpa instalasi TSO avatar Vitaboy gagal dimuat dan
                 warga desa jatuh ke humanoid.obj — mesh yang benar, tapi tanpa
                 warna sama sekali, jadi semua orang sampai ke layar sebagai
                 gumpalan PUTIH POLOS. Diperiksa dua-duanya: warnanya benar ADA
                 di vertex data, DAN shader yang membacanya benar terpasang.
                 Yang kedua bukan tambahan: shader hasil setShaderAuto() Panda
                 mengabaikan kolom warna vertex, jadi mesh yang sudah diwarnai
                 tetap keluar putih tanpa smooth_shader.
  rumput_lambai  uniform rumput dipindah dari per-entity ke induknya (976
                 panggilan set_shader_input per frame jadi 2). Kalau nilainya
                 berhenti sampai ke shader, rumputnya BEKU — dan beku itu
                 tidak melempar error, tidak menulis log, dan tidak terlihat
                 di frame diam. Diukur sebagai piksel yang berubah antara dua
                 nilai grs_time yang jauh.
  arah_wasd      arah WASD terbalik. Kegagalan yang PALING sering kembali di
                 proyek ini — tiga kali, dan tiap kali "diperbaiki" dengan
                 membalik tanda sampai terasa benar. Diukur sekali di akhir
                 lewat tools/probe_arah.py, alat ukur yang sama dengan probe
                 manual, supaya tidak ada dua kebenaran.

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
    # Versi sebelumnya men-tick state hidup, dan pemeriksaan ini jalan sekali
    # per scene: di scene keempat belas motifnya sudah diluruhkan 14 x 4 jam
    # tanpa pernah makan. Peluruhannya asimtotik (lajunya sebanding dengan
    # jarak ke lantai), jadi di sekitar -98 satu tick tidak lagi memindahkan
    # satu poin penuh dan pemeriksaannya melaporkan GAGAL — padahal mesinnya
    # sehat: yang salah alat ukurnya, yang merusak barang yang diukurnya
    # sendiri lalu terkejut melihatnya rusak. Scene terakhir dihukum karena
    # kebetulan berdiri paling belakang di antrean.
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


_HUD_TUNGGAL = (
    '_time_txt', '_date_txt', '_weather_txt', '_scene_txt', '_gold_txt',
    '_tool_name', '_seed_txt', '_hp_bar', '_hp_val', '_en_bar', '_en_val',
    '_buff_txt', '_queue_txt', '_control_hint',
    '_motive_panel_bg', '_mood_lbl', '_mood_bg', '_mood_fill',
)
_HUD_DERET = ('_need_lbl_ents', '_need_bg_ents', '_need_fill_ents')


def cek_hud_muat(g):
    """Tiap elemen HUD harus muat di layar, dan isi panel harus di dalam panel.

    Dua kegagalan nyata sekaligus. (1) camera.ui membentang
    -aspect/2..+aspect/2 mendatar, bukan -0.5..0.5; teks kanan dijangkar di
    KIRI pada x=0.70 lalu tumbuh melewati tepi 0.889, jadi jam, tanggal, nama
    scene, dan ekor baris kontrol terpotong. (2) tinggi panel SUASANA HATI
    dihitung dengan rumus tebakan sehingga tepi atasnya jatuh DI BAWAH judul
    dan judulnya menyembul keluar.

    Diukur lewat getTightBounds di ruang camera.ui — bukan lewat rumus yang
    sama dengan yang dipakai membangunnya, supaya alat ukurnya tidak ikut
    salah bersama barang yang diukurnya.
    """
    from ursina import camera, window
    ui = camera.ui
    ex = window.aspect_ratio / 2
    EPS = 0.004

    pan = getattr(g, 'panels', None)
    if pan is None:
        return _fail('tidak ada UIManager untuk diperiksa')
    if getattr(pan, 'mode', 'hud') != 'hud':
        return _ok('mode bukan hud, dilewati')

    def kotak(e):
        if e is None:
            return None
        try:
            if e.is_hidden():
                return None
            tb = e.getTightBounds(ui)
        except Exception:
            return None
        if tb is None:
            return None
        lo, hi = tb
        return (lo.x, hi.x, lo.y, hi.y)

    def elemen():
        for nama in _HUD_TUNGGAL:
            yield nama, getattr(pan, nama, None)
        for nama in _HUD_DERET:
            for i, e in enumerate(getattr(pan, nama, []) or []):
                yield f'{nama}[{i}]', e

    luber = []
    for nama, e in elemen():
        k = kotak(e)
        if k is None:
            continue
        x0, x1, y0, y1 = k
        lewat = max(-ex - x0, x1 - ex, -0.5 - y0, y1 - 0.5)
        if lewat > EPS:
            luber.append(f'{nama} lewat tepi {lewat:+.3f}')

    # Isi panel motif harus benar-benar di dalam kotak panelnya.
    pk = kotak(getattr(pan, '_motive_panel_bg', None))
    if pk:
        px0, px1, py0, py1 = pk
        for nama, e in elemen():
            if nama == '_motive_panel_bg' or not nama.startswith(
                    ('_mood', '_need')):
                continue
            k = kotak(e)
            if k is None:
                continue
            x0, x1, y0, y1 = k
            lewat = max(px0 - x0, x1 - px1, py0 - y0, y1 - py1)
            if lewat > EPS:
                luber.append(f'{nama} keluar panel {lewat:+.3f}')

    if luber:
        return _fail(f'{len(luber)} elemen terpotong ({"; ".join(luber[:3])})')
    return _ok(f'tepi ±{ex:.3f}')


def cek_hud_terbaca(g, png):
    """Bar termometer harus TERLIHAT, bukan cuma ada di memori.

    Warna fill dibaca dari piksel tangkapan layar lalu dibandingkan dengan
    warna yang diminta entity-nya. Sebelum ini fill hijau rgb(120,200,130)
    sampai ke layar sebagai rgb(19,33,31) — semua elemen camera.ui duduk di
    z=0, Panda menyortir bin transparannya sesukanya, dan latar panel 93% opak
    yang menang. Memeriksa `entity.color` tidak akan pernah menangkap itu:
    properti warnanya benar sepanjang waktu.
    """
    from ursina import camera, window
    pan = getattr(g, 'panels', None)
    if pan is None or getattr(pan, 'mode', 'hud') != 'hud':
        return _ok('mode bukan hud, dilewati')
    fills = list(getattr(pan, '_need_fill_ents', None) or [])
    mf = getattr(pan, '_mood_fill', None)
    if mf is not None:
        fills.append(mf)
    if not fills:
        return _ok('tidak ada termometer')
    try:
        from PIL import Image
        im = Image.open(png).convert('RGB')
    except Exception as e:
        return _fail(f'gagal baca png: {e}')

    w_px, h_px = im.size
    ex = window.aspect_ratio / 2
    ui = camera.ui
    buruk = []
    diperiksa = 0
    for i, e in enumerate(fills):
        try:
            if e.is_hidden():
                continue
            tb = e.getTightBounds(ui)
        except Exception:
            continue
        if tb is None:
            continue
        lo, hi = tb
        if (hi.x - lo.x) < 0.05:        # bar nyaris kosong: tidak ada yang bisa dibaca
            continue
        cx = lo.x + (hi.x - lo.x) * 0.35
        cy = (lo.y + hi.y) / 2
        px = min(w_px - 1, max(0, int(round((cx + ex) / (2 * ex) * w_px))))
        py = min(h_px - 1, max(0, int(round((0.5 - cy) * h_px))))
        dapat = im.getpixel((px, py))
        minta = tuple(int(round(c * 255)) for c in tuple(e.color)[:3])
        beda = sum(abs(a - b) for a, b in zip(dapat, minta))
        diperiksa += 1
        if beda > 90:
            buruk.append(f'bar{i} layar{dapat} bukan {minta}')
    if buruk:
        return _fail(f'{len(buruk)} bar tertimbun ({buruk[0]})')
    if not diperiksa:
        return _ok('semua bar kosong')
    return _ok(f'{diperiksa} bar terbaca')


def cek_rumput_tak_catur(g):
    """Terang ubin rumput tidak boleh terkunci ke paritas (tx+ty) % 2.

    Papan catur bukan soal selera warna, tapi soal PERIODE. Dua warna
    berselang tiap satu ubin adalah pola paling teratur yang bisa dibuat, dan
    mata menemukan grid-nya seketika. Variasi halus ala Sims 1 tetap boleh —
    yang dilarang variasi yang bisa diramalkan dari paritas ubin.

    Diukur sebagai jarak rata-rata dua kelompok paritas dibagi sebaran
    seluruh ubin. Papan catur murni memberi 2.00 (dua nilai, masing-masing
    satu paritas). Medan bising memberi mendekati 0.
    """
    import statistics
    w = getattr(g, 'world', None)
    ents = list(getattr(w, '_grass_ents', None) or [])
    tiles = list(getattr(w, '_grass_tiles', None) or [])
    if len(ents) != len(tiles):
        return _fail(f'{len(ents)} entity rumput vs {len(tiles)} koordinat')
    if len(ents) < 24:
        return _ok(f'{len(ents)} ubin rumput, tidak diukur')

    genap, ganjil = [], []
    for e, (tx, ty) in zip(ents, tiles):
        c = e.color
        lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
        (ganjil if (tx + ty) % 2 else genap).append(lum)
    if not genap or not ganjil:
        return _ok('satu paritas saja')

    sebar = statistics.pstdev(genap + ganjil)
    if sebar < 1e-6:
        return _ok('semua ubin sewarna')
    rasio = abs(statistics.fmean(genap) - statistics.fmean(ganjil)) / sebar
    if rasio > 0.5:
        return _fail(f'tint terkunci ke paritas ubin (rasio {rasio:.2f}, catur murni = 2.00)')
    return _ok(f'paritas {rasio:.2f}')


def cek_avatar_berwarna(g):
    """Warga desa yang jatuh ke humanoid.obj tidak boleh jadi gumpalan putih.

    Dua syarat, dan kegagalan salah satunya sudah pernah terjadi:

      1. vertex data punya kolom warna dengan lebih dari satu warna. Tanpa ini
         satu mesh cuma punya satu entity.color, dan warna itu memang tidak
         pernah diisi.
      2. ada shader terpasang di aktornya. Lampu scene memicu setShaderAuto()
         Panda3D, dan shader hasil generator itu MENGABAIKAN kolom warna
         vertex — diuji langsung: mesh yang sudah diwarnai tetap keluar putih
         pucat sampai smooth_shader dipasang. Memeriksa syarat 1 saja akan
         LULUS pada bug yang sebenarnya masih terlihat di layar.
    """
    from panda3d.core import GeomVertexReader
    ents = getattr(g, 'entities', None)
    aktor = getattr(ents, 'actors', None) or {}
    polos, tanpa_shader, diperiksa = [], [], 0

    for aid, a in aktor.items():
        m = getattr(a, 'model', None)
        if m is None or not hasattr(m, 'findAllMatches'):
            continue
        gns = list(m.findAllMatches('**/+GeomNode'))
        if not any(gn.getName().endswith('part_0') for gn in gns):
            continue        # bukan humanoid.obj — Vitaboy atau rig hewan
        diperiksa += 1
        unik = set()
        for gn in gns:
            node = gn.node()
            for i in range(node.getNumGeoms()):
                vd = node.getGeom(i).getVertexData()
                if not vd.hasColumn('color'):
                    continue
                r = GeomVertexReader(vd, 'color')
                while not r.isAtEnd():
                    c = r.getData4()
                    unik.add((round(c[0] * 255), round(c[1] * 255), round(c[2] * 255)))
        if len(unik) < 3:
            polos.append(f'{aid}({len(unik)} warna)')
            continue
        # Bukan cuma "ada shader": shader yang terpasang harus benar-benar
        # MEMBACA warna vertex. Versi pertama pemeriksaan ini cuma menuntut
        # shader tidak None, dan ia tetap LULUS ketika p3d_Color dicabut dari
        # smooth_shader — bug yang masih terlihat jelas di layar. Sumber
        # fragmennya dibaca langsung supaya tidak ada celah itu lagi.
        sh = getattr(a, 'shader', None)
        baca_warna = False
        if sh is not None:
            try:
                src = sh.fragment if isinstance(getattr(sh, 'fragment', None), str) else ''
                # Dicari `v_color`, BUKAN `p3d_Color`: `p3d_Color` adalah
                # substring dari `p3d_ColorScale`, yang ada di setiap versi
                # shader ini. Versi pertama pemeriksaan ini memakainya dan
                # karena itu lulus pada uji negatifnya sendiri.
                baca_warna = 'v_color' in src
            except Exception:
                baca_warna = False
        if not baca_warna:
            tanpa_shader.append(aid)

    if polos:
        return _fail(f'{len(polos)} avatar tanpa warna ({", ".join(polos[:3])})')
    if tanpa_shader:
        return _fail(f'{len(tanpa_shader)} avatar berwarna tapi tanpa shader '
                     f'pembaca warna vertex ({", ".join(tanpa_shader[:3])})')
    if not diperiksa:
        return _ok('tidak ada avatar cadangan')
    return _ok(f'{diperiksa} avatar berwarna')


def cek_rumput_melambai(g, base, tmp: Path):
    """Angin rumput harus benar-benar sampai ke shader.

    Uniform `grs_time`/`grs_wind` dipasang SEKALI di induk, bukan per entity —
    976 panggilan per frame di mountain jadi 2. Yang dibayar untuk itu: kalau
    suatu saat ada yang memasang uniform di entity lagi, input entity MENIMPA
    input induknya dan rumput itu membeku sendirian; kalau assignment di
    induknya hilang, semuanya membeku. Dua-duanya diam: tidak melempar error,
    tidak menulis log, dan tidak terlihat sama sekali di frame diam.

    Jadi diuji dari luar: render dua kali dengan grs_time yang jauh berbeda,
    lalu hitung piksel yang berubah. Rumput yang melambai menggeser vertex;
    rumput yang beku menghasilkan dua frame yang identik.
    """
    ge = list(getattr(getattr(g, 'world', None), '_grass_ents', None) or [])
    if len(ge) < 16:
        return _ok(f'{len(ge)} rumput, tidak diukur')
    try:
        import game.grass_shader as gs
    except Exception as e:
        return _fail(f'grass_shader tidak bisa diimpor: {e}')
    if getattr(gs, '_grass_failed', False) or gs.get_grass_shader() is None:
        return _ok('grass shader tidak tersedia di pipeline ini')

    try:
        from PIL import Image
    except Exception as e:
        return _fail(f'butuh Pillow: {e}')

    def tembak(t, nama):
        gs.update_time(ge, t, 0.30)     # angin kencang supaya geserannya terukur
        for _ in range(2):
            base.taskMgr.step()
        p = tmp / nama
        img = base.win.getScreenshot()
        if img is None:
            return None
        img.write(Filename.fromOsSpecific(str(p)))
        return Image.open(p).convert('RGB')

    semula = getattr(g, '_grass_time', 0.0)
    try:
        a = tembak(0.0, '_lambai_a.png')
        b = tembak(3.7, '_lambai_b.png')
    finally:
        # Kembalikan waktu rumput seperti semula supaya pemeriksaan berikutnya
        # tidak menilai dunia yang sudah kita geser sendiri.
        try:
            gs.update_time(ge, semula, 0.06)
        except Exception:
            pass
    if a is None or b is None:
        return _fail('tidak ada tangkapan layar')
    if a.size != b.size:
        return _fail('ukuran frame berubah di tengah pengukuran')

    beda = sum(1 for pa, pb in zip(a.getdata(), b.getdata()) if pa != pb)
    total = a.size[0] * a.size[1]
    frac = beda / total
    if frac < 0.005:
        return _fail(f'rumput beku — cuma {frac:.2%} piksel berubah antara '
                     f'grs_time 0.0 dan 3.7')

    # Separuh struktural, dan ini bukan pengulangan yang di atas.
    #
    # Uji piksel menangkap rumput yang beku SELURUHNYA. Ia tidak menangkap
    # sebagian: diukur langsung, memaku separuh rumput di entity cuma
    # menurunkan angkanya 9,5% -> 3,5%, masih jauh di atas ambang mana pun
    # yang aman dari salah-vonis di scene yang rumputnya sedikit. Yang
    # menangkapnya justru pemeriksaan yang jauh lebih murah: tidak boleh ada
    # entity rumput yang menyimpan grs_time-nya sendiri, karena input entity
    # menimpa input induknya (juga diukur, bukan diasumsikan).
    try:
        from panda3d.core import ShaderAttrib, ShaderInput
        kosong = ShaderInput.get_blank()
        sendiri = []
        for e in ge:
            sa = e.getState().getAttrib(ShaderAttrib)
            if sa is None:
                continue
            if sa.get_shader_input('grs_time') != kosong:
                sendiri.append(getattr(e, 'name', '?'))
        if sendiri:
            return _fail(f'{len(sendiri)} rumput memasang grs_time sendiri — '
                         f'input entity menimpa induknya, jadi rumput itu beku')
    except Exception:
        pass        # versi Panda tanpa API ini: uji piksel di atas tetap jalan

    return _ok(f'{frac:.1%} piksel bergeser')


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

            png = OUT / f'{nama}.png'
            img = base.win.getScreenshot()
            if img is not None:
                img.write(Filename.fromOsSpecific(str(png)))

            hasil['geom_nol'] = cek_geom_nol(nama)
            hasil['frame_kosong'] = cek_frame_kosong(png) if png.exists() \
                else _fail('tidak ada tangkapan layar')
            hasil['pemain_valid'] = cek_pemain_valid(g)
            hasil['motif_waras'] = cek_motif_waras(g)
            hasil['rumput_catur'] = cek_rumput_tak_catur(g)
            hasil['avatar_warna'] = cek_avatar_berwarna(g)
            hasil['hud_muat'] = cek_hud_muat(g)
            hasil['hud_terbaca'] = cek_hud_terbaca(g, png) if png.exists() \
                else _fail('tidak ada tangkapan layar')
            hasil['save_bolak'] = cek_save_bolak(g)
            hasil['rumput_lambai'] = cek_rumput_melambai(g, base, OUT)
            n_ent = len(uscene.children)
        except Exception as e:
            hasil['boot'] = _fail(f'{type(e).__name__}: {e}')
            ms, n_ent = float('nan'), 0
            traceback.print_exc()

        buruk = [k for k, (ok, _) in hasil.items() if not ok]
        gagal_total += len(buruk)
        baris.append((nama, hasil, ms, n_ent, buruk))

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

    # ── laporan ──
    print()
    print(f'{"scene":14s} {"hasil":>7s} {"ms/frame":>9s} {"entity":>7s}  catatan')
    print('-' * 78)
    for nama, hasil, ms, n_ent, buruk in baris:
        tanda = 'LULUS' if not buruk else 'GAGAL'
        catatan = '; '.join(f'{k}: {hasil[k][1]}' for k in buruk) if buruk else \
                  hasil.get('pemain_valid', (True, ''))[1]
        print(f'{nama:14s} {tanda:>7s} {ms:9.1f} {n_ent:7d}  {catatan[:44]}')
    print('-' * 78)
    tanda_arah = 'LULUS' if all(ok for _, ok, _ in arah_baris) else 'GAGAL'
    rangkum = ', '.join(f'{k.upper()}={c.split(" ")[0]}' for k, ok, c in arah_baris)
    print(f'{"arah WASD":14s} {tanda_arah:>7s} {"":>9s} {"":>7s}  {rangkum[:44]}')
    print('-' * 78)
    n_lulus = sum(1 for _, _, _, _, b in baris if not b)
    print(f'{n_lulus}/{len(baris)} scene lulus, {gagal_total} pemeriksaan gagal, '
          f'boot {boot_s:.1f}s')

    laporan = OUT / 'report.md'
    with open(laporan, 'w', encoding='utf-8') as f:
        f.write('# Laporan regresi\n\n')
        f.write(f'{n_lulus}/{len(baris)} scene lulus, {gagal_total} pemeriksaan gagal.\n\n')
        f.write('| scene | hasil | ms/frame | entity | catatan |\n|---|---|--:|--:|---|\n')
        for nama, hasil, ms, n_ent, buruk in baris:
            tanda = 'LULUS' if not buruk else '**GAGAL**'
            catatan = '; '.join(f'`{k}` {hasil[k][1]}' for k in buruk) or '-'
            f.write(f'| {nama} | {tanda} | {ms:.1f} | {n_ent} | {catatan} |\n')
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
    os._exit(1 if gagal_total else 0)


if __name__ == '__main__':
    main()
