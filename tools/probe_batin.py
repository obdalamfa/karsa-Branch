"""probe_batin.py — Majelis Batin dimainkan dari game baru, lewat jalur asli.

Majelis Batin (suara batin gaya Disco Elysium) hilang sebagian di merge
5683e79: `game/batin.py` tetap ada, enam pemanggil `say_batin_once` tetap ada,
tapi `Batin` tidak pernah dibuat, modal PAGI PERTAMA tidak bisa terbuka, dan
panelnya tidak punya tombol. Tidak ada alat yang menyadarinya, karena tidak ada
yang memainkannya.

Probe ini memainkannya. Tiga aturan, semuanya lahir dari probe lama yang salah:

1. Tombol ditekan lewat dispatcher Ursina `g.app.input`, bukan
   `Game3D.input`. Jalur Ursina membagikan tombol ke SEMUA entity, termasuk
   HotReloader dan window_input -- probe yang melewatinya tidak bisa melihat
   tabrakan tombol (lihat obsidian/40-Bug/F5 dan F9 dibajak HotReloader).
2. HUD dicapai dengan SPACE sampai sinema benar-benar selesai
   (`not g.sinema.aktif`), bukan ESC. ESC meninggalkan sisa sinema di layar.
3. Game3D hanya bisa dibuat sekali per proses, dan PAGI PERTAMA hanya
   terpicu sekali per pemain. Jadi tiap fase subproses sendiri:

     A  pilih opsi di modal, suara yang hilang, panel, TAB, tata letak
     B  ESC pada modal, subtitle memudar selama modal terbuka
     C  persistensi: C1 menjawab + F5, C2 boot dari save itu, C3 save lama
     D  F9 di tengah sesi: bendera sekali-ucap ikut save yang dimuat

Save ditulis ke direktori sementara (game.state.SAVE_FILE ditambal), jadi
probe tidak pernah menyentuh save pemain dan tidak perlu dilewati kalau ada.

    python tools/probe_batin.py           # semua fase, keluar 1 kalau gagal
    python tools/probe_batin.py --fase A  # satu fase (dipakai orkestrator)

Cek yang prasyaratnya tidak terpenuhi (mis. modal tidak pernah terbuka)
dinilai GAGAL dengan alasan itu, bukan lulus kosong.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Tombol panel Majelis Batin. F7 bebas hanya karena development_mode Ursina
# dimatikan (game/app.py); tanpa itu HotReloader.reload_models menangkapnya.
TOMBOL_PANEL = 'f7'

hasil: list[tuple[str, bool, str]] = []


def cek(nama, ok, ket=''):
    hasil.append((nama, bool(ok), str(ket)))


def prasyarat(nama, ok, ket=''):
    """Langkah persiapan: lulus pada kode rusak maupun benar, jadi tidak
    dihitung sebagai bukti. Hanya muncul di laporan kalau GAGAL."""
    if not ok:
        cek('prasyarat: ' + nama, False, ket)


# ─── alat jalur asli ────────────────────────────────────────────────────────
def langkah(n=1):
    from direct.showbase.ShowBaseGlobal import base
    for _ in range(n):
        base.taskMgr.step()


def tekan(g, key, n=3):
    """Tekan lewat dispatcher Ursina. Huruf/angka lewat jalur 'raw' seperti
    keyboard sungguhan; tombol lain lewat buttonDown."""
    from ursina.main import keyboard_keys
    g.app.input(key, key in keyboard_keys)
    langkah(n)


def tunggu_detik(detik):
    """taskMgr.step memakai dt nyata, jadi waktu dimajukan dengan jam dinding."""
    t0 = time.time()
    while time.time() - t0 < detik:
        langkah(1)


def ke_hud(g):
    """Chargen -> Enter -> sinema dengan SPACE sampai selesai."""
    if g.panels.mode == 'chargen':
        tekan(g, 'enter', 5)
    t0 = time.time()
    while time.time() - t0 < 120:
        langkah(1)
        if g.sinema.aktif:
            if g.sinema._menunggu:
                tekan(g, 'space', 1)
            continue
        if g.panels.mode == 'hud':
            _vinyet_sudah(g)
            return True
    return False


def _vinyet_sudah(g):
    """Adegan interaksi pertama (surat, cangkul, tiba di desa, ...) ditandai
    sudah ditonton. Probe ini menguji Majelis Batin, bukan sinema; adegan itu
    menelan tombol yang ditekan probe (CI 23 Okt 2026: 2/28) dan diuji
    sendiri oleh tools/probe_sinema.py. Adegan pembuka dan belokan quest
    (`tahap`) tetap ditonton lewat SPACE seperti sebelumnya."""
    from game.cutscene import NASKAH
    sudah = g.state.sinema_selesai
    for nama, sk in NASKAH.items():
        if sk.get('syarat') and nama not in sudah:
            sudah.append(nama)


def ui_sinema_hidup(g):
    return [e for e in getattr(g.sinema, '_ui', []) if e and getattr(e, 'enabled', False)]


def jalan(g, x, y, hadap='up'):
    s = g.state
    if s.scene_name != 'farm':
        s.scene_name = 'farm'
        langkah(30)
    g.player.set_tile_pos(x, y)
    g.player.facing = hadap
    langkah(3)


def baca_surat(g):
    from game.config import MB
    from game.scenes import SCENES
    mb = next((x, y) for y, r in enumerate(SCENES['farm'].tiles)
              for x, v in enumerate(r) if v == MB)
    jalan(g, mb[0], mb[1] - 1, 'up')
    tekan(g, 'f', 6)
    if g.panels.mode != 'hud':
        tekan(g, 'escape', 4)
    return g.state.mail_read


def cangkul(g, x, y):
    """Petak (x, y) dicangkul dengan [1] + [SPACE] dari petak di bawahnya."""
    tekan(g, '1', 2)
    jalan(g, x, y - 1, 'up')
    tekan(g, 'space', 2)


def bukan_suara(teks):
    """Flash tidak boleh berisi suara batin. Isi tepatnya tidak dicek: pesan
    sambutan chargen ikut menulis flash dengan jeda waktu (invoke 4/8,5/13
    dtk), jadi isi persisnya bergantung pada kecepatan mesin."""
    from game.batin import VOICES
    t = (teks or '').strip()
    return not any(t.startswith(v['name'] + ' ') for v in VOICES.values())


def batin_lines(g):
    b = getattr(g, 'batin', None)
    return list(getattr(b, 'lines', []) or [])


def bc_hidup(p):
    return [e for e in getattr(p, '_bc_ents', []) or [] if e and getattr(e, 'enabled', False)]


def modal_terbuka(p):
    return p.mode == 'batin' and bool(bc_hidup(p))


# ─── tata letak ─────────────────────────────────────────────────────────────
TEPI_CHROME = 0.10   # bingkai chrome yang dipangkas: ~10,4% tiap sisi


def kotak(e):
    """(x0, y0, x1, y1) entity di ruang camera.ui, dari geometri yang digambar."""
    from ursina import camera
    try:
        b = e.get_tight_bounds(camera.ui)
    except Exception:
        b = None
    if b:
        lo, hi = b
        return (lo.x, lo.y, hi.x, hi.y)
    return (e.x - e.scale_x / 2, e.y - e.scale_y / 2,
            e.x + e.scale_x / 2, e.y + e.scale_y / 2)


def _irisan(a, b, sela=0.004):
    return (min(a[2], b[2]) - max(a[0], b[0]) > sela
            and min(a[3], b[3]) - max(a[1], b[1]) > sela)


def _nama(p, e):
    for k, v in vars(p).items():
        if v is e:
            return k
    return type(e).__name__ + ':' + (getattr(e, 'text', '') or '')[:12]


def di_luar_latar(latar, teks):
    """Teks yang keluar dari bagian latar yang TAMPAK (di dalam bingkai)."""
    x0, y0, x1, y1 = kotak(latar)
    tx, ty = (x1 - x0) * TEPI_CHROME, (y1 - y0) * TEPI_CHROME
    dalam = (x0 + tx, y0 + ty, x1 - tx, y1 - ty)
    keluar = []
    # Kotak quad belum tentu latar yang TAMPAK: panel_chrome.png hanya opak
    # di 49% tengahnya. Tepat di dalam bingkai (12% dari tepi) teksturnya
    # harus opak, kalau tidak teks yang 'di dalam quad' melayang di atas dunia.
    try:
        from panda3d.core import PNMImage
        img = PNMImage()
        if latar.texture is not None and latar.texture._texture.store(img):
            for fx, fy in ((0.12, 0.5), (0.88, 0.5), (0.5, 0.12), (0.5, 0.88)):
                a = img.get_alpha(int(img.get_x_size() * fx), int(img.get_y_size() * fy))
                if a < 0.5:
                    keluar.append(f'latar transparan di ({fx},{fy}) alfa={a:.2f}')
                    break
    except Exception as ex:
        keluar.append(f'alfa latar tak terbaca: {ex}')
    for e in teks:
        if not (getattr(e, 'text', '') or '').strip():
            continue
        k = kotak(e)
        if (k[0] < dalam[0] - 0.003 or k[2] > dalam[2] + 0.003
                or k[1] < dalam[1] - 0.003 or k[3] > dalam[3] + 0.003):
            keluar.append(f"'{e.text[:14]}' keluar latar {tuple(round(v, 3) for v in k)}")
    return keluar


def tumpang(milik, lain, label):
    hasil_ = []
    for e in lain:
        if e is None or not getattr(e, 'enabled', False) or e.has_disabled_ancestor():
            continue
        if hasattr(e, 'text') and not (e.text or '').strip():
            continue
        kb = kotak(e)
        for m in milik:
            if _irisan(kotak(m), kb):
                hasil_.append(f'{label} menimpa {getattr(e, "text", "")[:16] or type(e).__name__}'
                              f' {tuple(round(v, 3) for v in kb)}')
                break
    return hasil_


def hud_lain(p):
    """Blok HUD yang tampak di samping panel: pelacak tutorial, roda alat,
    jam, motif, petunjuk tombol, flash, subtitle."""
    nama = ('_obj_bg', '_obj_title', '_obj_step', '_obj_hint', '_obj_janji',
            '_scrim_kiri', '_scrim_kanan', '_scrim_bawah', '_motive_panel_bg',
            '_control_hint', '_time_txt', '_date_txt', '_gold_txt', '_scene_txt',
            '_flash_ent', '_voice_sub')
    return [getattr(p, n) for n in nama if getattr(p, n, None) is not None]


def subtitle_vs_dialog(p):
    """Subtitle tidak boleh jatuh di kotak dialog (termasuk papan nama)."""
    sub = getattr(p, '_voice_sub', None)
    if sub is None:
        return ['subtitle tidak ada']
    ks = kotak(sub)
    dlg = [kotak(getattr(p, n)) for n in ('_dlg_border', '_dlg_papan')
           if getattr(p, n, None) is not None]
    return [f'subtitle {tuple(round(v, 3) for v in ks)} di dalam kotak dialog'
            for d in dlg if _irisan(ks, d)]


# ─── boot ───────────────────────────────────────────────────────────────────
def boot(save_path: Path):
    os.chdir(ROOT)
    from panda3d.core import loadPrcFileData
    loadPrcFileData('', 'audio-library-name null')
    loadPrcFileData('', 'sync-video false')
    import logging
    logging.basicConfig(level=logging.ERROR)
    from ursina import application
    application.asset_folder = ROOT
    application.fonts_folder = ROOT / 'assets' / 'fonts'
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))
    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = 640, 360
    import game.state as gs
    gs.SAVE_FILE = str(save_path)          # save probe, bukan save pemain
    from game.app import Game3D
    return Game3D()


# ─── fase A ─────────────────────────────────────────────────────────────────
def fase_a(g):
    from ursina import application, window
    p, s = g.panels, g.state

    sampai = ke_hud(g)
    prasyarat('A sampai HUD lewat SPACE, sinema selesai',
        sampai and not g.sinema.aktif and not ui_sinema_hidup(g),
        f'mode={p.mode} sinema.aktif={g.sinema.aktif} ui_sinema={len(ui_sinema_hidup(g))}')

    from game.batin import Batin
    cek('A Batin dibuat dan dipegang panels',
        isinstance(getattr(g, 'batin', None), Batin) and p.batin is getattr(g, 'batin', None),
        f'game.batin={getattr(g, "batin", None)!r} panels.batin={p.batin!r}')

    prasyarat('A surat dibaca dengan [F]', baca_surat(g), f'mail_read={s.mail_read}')

    t0 = s.stats.get('tilled', 0)
    cangkul(g, 10, 12)
    prasyarat('A cangkul pertama mencangkul', s.stats.get('tilled', 0) == t0 + 1,
        f"tilled {t0}->{s.stats.get('tilled', 0)}")
    opsi = getattr(p, '_batin_opts', None) or []
    cek('A cangkul pertama membuka modal PAGI PERTAMA (3 opsi)',
        modal_terbuka(p) and len(opsi) == 3,
        f'mode={p.mode} opsi={len(opsi)} ents={len(bc_hidup(p))}')
    terbuka = modal_terbuka(p)
    flash = p._flash_ent.text if p._flash_ent else ''
    sub = getattr(p, '_voice_sub', None)
    cek('A suara cangkul di subtitle, flash tidak ditimpa',
        bukan_suara(flash) and sub is not None and sub.enabled
        and 'AKAR' in (sub.text or ''),
        f'flash={flash!r} subtitle={getattr(sub, "text", None)!r} '
        f'nyala={getattr(sub, "enabled", None)}')

    # Tata letak modal: dibaca dari kotak entity yang benar-benar digambar.
    if terbuka:
        ents = bc_hidup(p)
        masalah = di_luar_latar(ents[0], ents[1:])
        masalah += tumpang(ents, [p._flash_ent, sub], 'modal')
        masalah += subtitle_vs_dialog(p)
        cek('A tata letak modal: teks di dalam latar, tidak menimpa flash/subtitle',
            not masalah, '; '.join(masalah[:3]) or 'bersih')
    else:
        cek('A tata letak modal: teks di dalam latar, tidak menimpa flash/subtitle',
            False, 'modal tidak terbuka')

    langkah(2)
    cek("A mode 'batin' bertahan 2 frame (tidak dipulihkan yatim)",
        terbuka and modal_terbuka(p), f'mode={p.mode}' if terbuka else 'modal tidak terbuka')

    sukma0 = s.batin.get('sukma', 1)
    alat0 = s.tool_index
    n0 = len(batin_lines(g))
    tekan(g, '2', 3)
    cek('A [2] memilih opsi SUKMA (+1), alat tidak berganti',
        s.batin.get('sukma', 1) == sukma0 + 1 and s.tool_index == alat0,
        f"sukma {sukma0}->{s.batin.get('sukma')} tool_index {alat0}->{s.tool_index}")
    cek('A modal tertutup bersih setelah memilih',
        terbuka and p.mode == 'hud' and not bc_hidup(p),
        f'mode={p.mode} ents={len(bc_hidup(p))}' if terbuka else 'modal tidak terbuka')
    cek('A log Batin mencatat cangkul + pilihan', terbuka and len(batin_lines(g)) >= 2,
        f'lines {n0}->{len(batin_lines(g))}')

    # Suara yang hilang di merge: siram, panen, kirim_hint.
    tekan(g, '2', 2)
    jalan(g, 10, 11, 'up')
    tekan(g, 'space', 3)
    siram = [t for v, t in batin_lines(g) if 'Air itu jadwal' in t]
    cek("A siram pertama: suara AKAR 'siram', flash tetap",
        siram and bukan_suara(p._flash_ent.text),
        f'siram={len(siram)} flash={p._flash_ent.text!r}')
    # Tanaman matang dipasang sebagai fixture keadaan; aksinya tetap tombol.
    s.soil['11,12,farm'] = {'tilled': True, 'crop': 'lobak', 'age': 99,
                           'quality': 3.0, 'nutrients': 3, 'weeds': 0}
    tekan(g, '4', 2)
    jalan(g, 11, 11, 'up')
    h0 = s.stats.get('lobak_harvested', 0)
    tekan(g, 'space', 3)
    teks = [t for v, t in batin_lines(g)]
    cek("A panen pertama: suara 'panen' + 'kirim_hint', flash nilai tetap",
        s.stats.get('lobak_harvested', 0) == h0 + 1
        and any('Panen pertama' in t for t in teks)
        and any('Peti Kirim' in t for t in teks)
        and bukan_suara(p._flash_ent.text),
        f"panen {h0}->{s.stats.get('lobak_harvested', 0)} flash={p._flash_ent.text!r}")

    # Panel majelis: tombol tidak boleh disentuh mesin.
    hr = getattr(application, 'hot_reloader', None)
    kena = []
    if hr is not None:
        for k in list(hr.hotkeys):
            hr.hotkeys[k] = (lambda kk: (lambda *a, **kw: kena.append(kk)))(k)
    rm0 = window.render_mode
    ed0 = getattr(getattr(window, 'editor_ui', None), 'enabled', None)
    tekan(g, TOMBOL_PANEL, 3)
    log = getattr(getattr(p, '_batin_log', None), 'text', '') or ''
    panel_buka = bool(getattr(p, '_batin_open', False) and log.strip() and p.mode == 'hud')
    cek(f'A [{TOMBOL_PANEL.upper()}] membuka panel majelis berisi log', panel_buka,
        f"open={getattr(p, '_batin_open', None)} log={log[:40]!r} mode={p.mode}")
    # Dua cek berikut hanya bermakna kalau panelnya memang terbuka; pada kode
    # tanpa panel keduanya akan lulus kosong.
    cek(f'A [{TOMBOL_PANEL.upper()}] tidak ditangkap mesin Ursina',
        panel_buka and not kena and window.render_mode == rm0
        and getattr(getattr(window, 'editor_ui', None), 'enabled', None) == ed0,
        f'hotkeys={kena} render_mode {rm0}->{window.render_mode}'
        if panel_buka else 'panel tidak terbuka')
    if panel_buka:
        latar = p._batin_ents[0]
        masalah = di_luar_latar(latar, [e for e in p._batin_ents[1:] if e.enabled])
        masalah += tumpang([latar], hud_lain(p), 'panel')
        cek('A tata letak panel majelis: teks di dalam latar, tidak menimpa HUD',
            not masalah, '; '.join(masalah[:3]) or 'bersih')
    else:
        cek('A tata letak panel majelis: teks di dalam latar, tidak menimpa HUD',
            False, 'panel tidak terbuka')
    tekan(g, TOMBOL_PANEL, 3)
    cek(f'A [{TOMBOL_PANEL.upper()}] lagi menutup panel',
        panel_buka and not getattr(p, '_batin_open', True),
        f"open={getattr(p, '_batin_open', None)}" if panel_buka else 'panel tidak terbuka')

    m0 = getattr(p, '_motif_tampil', None)
    tekan(g, 'tab', 3)
    cek('A TAB tetap milik ringkasan motif (majelis punya tombol sendiri)',
        panel_buka and getattr(p, '_motif_tampil', None) is (not m0)
        and not getattr(p, '_batin_open', False),
        f"_motif_tampil {m0}->{getattr(p, '_motif_tampil', None)} "
        f"_batin_open={getattr(p, '_batin_open', None)}")
    tekan(g, 'tab', 3)

    # Panel majelis menutup sendiri begitu mode meninggalkan HUD. Tanpa itu ia
    # tetap tergambar di kolom kanan, di atas panel inventaris, kotak dialog
    # dan modal pilihan (UIManager.update). Prasyaratnya panel benar-benar
    # terbuka dulu; kalau tidak, 'tertutup' lulus kosong.
    tekan(g, TOMBOL_PANEL, 3)
    buka_lagi = bool(getattr(p, '_batin_open', False))
    tekan(g, 'i', 4)
    hidup = [e for e in getattr(p, '_batin_ents', []) or [] if e and e.enabled]
    cek('A [I] dengan panel majelis terbuka: majelis tertutup sendiri',
        buka_lagi and p.mode != 'hud' and not getattr(p, '_batin_open', True) and not hidup,
        (f"mode={p.mode} open={getattr(p, '_batin_open', None)} hidup={len(hidup)}")
        if buka_lagi else 'panel tidak terbuka sebelum [I]')
    tekan(g, 'escape', 3)


# ─── fase B ─────────────────────────────────────────────────────────────────
def fase_b(g):
    p, s = g.panels, g.state
    sampai = ke_hud(g)
    prasyarat('B sampai HUD lewat SPACE', sampai and not g.sinema.aktif, f'mode={p.mode}')
    baca_surat(g)
    cangkul(g, 10, 12)
    terbuka = modal_terbuka(p)
    sub = getattr(p, '_voice_sub', None)
    sub_nyala = bool(sub is not None and sub.enabled)
    cek('B modal terbuka, subtitle cangkul menyala', terbuka and sub_nyala,
        f'mode={p.mode} subtitle={sub_nyala}')

    # Subtitle memudar walau modal masih terbuka (pemudar di luar gerbang hud).
    tunggu_detik(5.2)
    cek('B subtitle padam setelah 5 dtk selama modal terbuka',
        terbuka and sub_nyala and modal_terbuka(p) and not sub.enabled,
        (f'subtitle={sub.enabled} mode={p.mode}') if terbuka else 'modal tidak terbuka')

    tekan(g, 'escape', 3)
    cek('B ESC menutup modal: mode hud, nol entity modal tersisa',
        terbuka and p.mode == 'hud' and not bc_hidup(p)
        and not getattr(p, '_bc_ents', None),
        (f'mode={p.mode} hidup={len(bc_hidup(p))} '
         f"sisa={len(getattr(p, '_bc_ents', []) or [])}") if terbuka else 'modal tidak terbuka')

    cangkul(g, 11, 12)
    cek('B cangkul berikutnya tidak membuka modal lagi',
        terbuka and p.mode == 'hud' and not bc_hidup(p),
        f'mode={p.mode}' if terbuka else 'modal tidak terbuka')


# ─── fase C ─────────────────────────────────────────────────────────────────
def fase_c1(g, save: Path):
    p, s = g.panels, g.state
    ke_hud(g)
    baca_surat(g)
    cangkul(g, 10, 12)
    terbuka = modal_terbuka(p)
    tekan(g, '1', 3)
    tekan(g, 'f5', 3)
    isi = json.loads(save.read_text(encoding='utf-8')) if save.exists() else {}
    sekali = isi.get('batin_sekali')
    cek('C1 modal dijawab lalu F5 menyimpan bendera sekali-ucap',
        terbuka and isinstance(sekali, list) and 'pagi_pertama' in sekali,
        f'modal={terbuka} save={save.exists()} batin_sekali={sekali}')


def fase_c2(g):
    p, s = g.panels, g.state
    sampai = ke_hud(g)
    prasyarat('C2 boot dari save C1 sampai HUD tanpa chargen',
        sampai and s.char_name, f'mode={p.mode} nama={s.char_name!r}')
    cangkul(g, 12, 12)
    langkah(2)
    ulang = [t for v, t in batin_lines(g) if 'mata bajak' in t]
    ada = getattr(g, 'batin', None) is not None
    cek('C2 sesi baru: cangkul tidak membuka PAGI PERTAMA lagi',
        ada and p.mode == 'hud' and not bc_hidup(p) and not ulang,
        f'mode={p.mode} suara_cangkul_ulang={len(ulang)}' if ada
        else 'Batin tidak dibuat (cek ini akan lulus kosong)')


def fase_c3(g):
    p, s = g.panels, g.state
    ke_hud(g)
    cek('C3 save lama tanpa batin_sekali dimuat apa adanya',
        getattr(g, '_load_status', None) == 'ok' and s.char_name
        and getattr(s, 'batin_sekali', None) == [],
        f"status={getattr(g, '_load_status', None)} "
        f"batin_sekali={getattr(s, 'batin_sekali', None)!r}")


# ─── fase D ─────────────────────────────────────────────────────────────────
def fase_d(g, save: Path):
    """F9 mengganti isi state; bendera sekali-ucap harus ikut save yang dimuat.
    Batin yang menyimpan rujukan list lama (cache) akan tetap mengira
    PAGI PERTAMA sudah dijawab, padahal save yang dimuat belum."""
    p, s = g.panels, g.state
    ke_hud(g)
    baca_surat(g)
    tekan(g, 'f5', 3)
    awal = json.loads(save.read_text(encoding='utf-8')) if save.exists() else None
    prasyarat('D F5 awal menyimpan save tanpa pagi_pertama',
        awal is not None and 'pagi_pertama' not in (awal.get('batin_sekali') or []),
        f'save={save.exists()}')
    cangkul(g, 10, 12)
    jawab1 = modal_terbuka(p)
    tekan(g, '1', 3)
    prasyarat('D modal pertama dijawab, bendera masuk state',
        jawab1 and 'pagi_pertama' in (getattr(s, 'batin_sekali', None) or []),
        f'modal={jawab1} batin_sekali={getattr(s, "batin_sekali", None)}')
    tekan(g, 'f9', 10)
    s = g.state
    cek('D F9 mengembalikan batin_sekali ke isi save',
        jawab1 and 'pagi_pertama' not in (getattr(s, 'batin_sekali', None) or ['?']),
        f'batin_sekali={getattr(s, "batin_sekali", None)}')
    cangkul(g, 12, 12)
    lagi = modal_terbuka(p)
    cek('D setelah F9 cangkul membuka PAGI PERTAMA lagi (save belum menjawab)',
        jawab1 and lagi, f'mode={p.mode}')
    tekan(g, '1', 3)
    tekan(g, 'f5', 3)
    akhir = json.loads(save.read_text(encoding='utf-8')) if save.exists() else {}
    cek('D F5 setelah F9 menyimpan pagi_pertama',
        jawab1 and lagi and 'pagi_pertama' in (akhir.get('batin_sekali') or []),
        f"batin_sekali={akhir.get('batin_sekali')}")


# ─── orkestrasi ─────────────────────────────────────────────────────────────
def jalankan_fase(fase: str, save: Path):
    g = boot(save)
    try:
        if fase == 'A':
            fase_a(g)
        elif fase == 'B':
            fase_b(g)
        elif fase == 'C1':
            fase_c1(g, save)
        elif fase == 'C2':
            fase_c2(g)
        elif fase == 'C3':
            fase_c3(g)
        elif fase == 'D':
            fase_d(g, save)
    except Exception as ex:
        traceback.print_exc()
        cek(f'{fase} probe meledak', False, f'{type(ex).__name__}: {ex}')
    for nama, ok, ket in hasil:
        print('CEK ' + json.dumps([nama, ok, ket], ensure_ascii=False))
    sys.stdout.flush()
    os._exit(0)


def _sub(fase, save: Path, log, ulang=1):
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                        '--fase', fase, '--save', str(save)],
                       cwd=ROOT, capture_output=True, text=True, timeout=600)
    log.write(f'===== {fase} (kode {r.returncode})\n{r.stdout}\n{r.stderr}\n')
    baris = [json.loads(b[4:]) for b in r.stdout.splitlines() if b.startswith('CEK ')]
    if not baris and ulang and 'Could not open window' in r.stderr:
        # Lingkungan, bukan game: Xvfb di mesin bersama sesekali menolak
        # membuka jendela GL. Diulang SEKALI dan dicatat di log.
        log.write(f'===== {fase}: jendela gagal dibuka, diulang sekali\n')
        return _sub(fase, save, log, ulang - 1)
    if not baris:
        baris = [[f'{fase} subproses tanpa hasil', False,
                  (r.stderr.strip().splitlines() or ['?'])[-1][:120]]]
    return baris


def main():
    args = sys.argv[1:]
    if '--fase' in args:
        fase = args[args.index('--fase') + 1]
        save = Path(args[args.index('--save') + 1])
        jalankan_fase(fase, save)
        return

    kerja = Path(tempfile.mkdtemp(prefix='probe_batin_'))
    semua = []
    with open(kerja / 'log.txt', 'w', encoding='utf-8') as log:
        semua += _sub('A', kerja / 'a.json', log)
        semua += _sub('B', kerja / 'b.json', log)
        save_c = kerja / 'c.json'
        semua += _sub('C1', save_c, log)
        lama = kerja / 'lama.json'
        if save_c.exists():
            d = json.loads(save_c.read_text(encoding='utf-8'))
            d.pop('batin_sekali', None)
            lama.write_text(json.dumps(d), encoding='utf-8')
        semua += _sub('C2', save_c, log)
        if lama.exists():
            semua += _sub('C3', lama, log)
        else:
            semua.append(['C3 save lama tanpa batin_sekali dimuat apa adanya', False,
                          'C1 tidak menghasilkan save'])
        semua += _sub('D', kerja / 'd.json', log)

    print('\nMAJELIS BATIN — dimainkan lewat app.input dari game baru')
    print('=' * 78)
    lebar = max(len(n) for n, _, _ in semua)
    for nama, ok, ket in semua:
        print(f"{'LULUS' if ok else 'GAGAL':>5s}  {nama:<{lebar}s}  {ket[:90]}")
    gagal = [n for n, ok, _ in semua if not ok]
    print('-' * 78)
    print(f'{len(semua) - len(gagal)}/{len(semua)} lulus  (log: {kerja / "log.txt"})')
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
