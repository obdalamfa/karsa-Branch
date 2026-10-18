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
            return True
    return False


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
    tekan(g, 'e', 6)
    if g.panels.mode != 'hud':
        tekan(g, 'escape', 4)
    return g.state.mail_read


def cangkul(g, x, y):
    """Petak (x, y) dicangkul dengan [1] + [SPACE] dari petak di bawahnya."""
    tekan(g, '1', 2)
    jalan(g, x, y - 1, 'up')
    tekan(g, 'space', 2)


def batin_lines(g):
    b = getattr(g, 'batin', None)
    return list(getattr(b, 'lines', []) or [])


def bc_hidup(p):
    return [e for e in getattr(p, '_bc_ents', []) or [] if e and getattr(e, 'enabled', False)]


def modal_terbuka(p):
    return p.mode == 'batin' and bool(bc_hidup(p))


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

    prasyarat('A surat dibaca dengan [E]', baca_surat(g), f'mail_read={s.mail_read}')

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
    cek("A flash 'Tanah dicangkul!' tidak ditimpa suara batin",
        flash == 'Tanah dicangkul!' and sub is not None and sub.enabled
        and 'AKAR' in (sub.text or ''),
        f'flash={flash!r} subtitle={getattr(sub, "text", None)!r} '
        f'nyala={getattr(sub, "enabled", None)}')

    # Tata letak modal: dibaca dari entity yang benar-benar dibangun.
    if terbuka:
        ents = bc_hidup(p)
        teks = [e for e in ents if hasattr(e, 'text')]
        prompt = next((e for e in teks if 'lumpur' in (e.text or '')), None)
        tekan_e = next((e for e in teks if (e.text or '').startswith('Tekan 1')), None)
        bentrok = []
        if prompt is not None and abs(prompt.y - p._flash_ent.y) < 0.04:
            bentrok.append(f'prompt y={prompt.y:.3f} = flash y={p._flash_ent.y:.3f}')
        if tekan_e is not None and sub is not None and abs(tekan_e.y - sub.y) < 0.04:
            bentrok.append(f"'Tekan 1-N' y={tekan_e.y:.3f} = subtitle y={sub.y:.3f}")
        dlg_atas = p._DLG_Y + p._DLG_H / 2
        dlg_bawah = p._DLG_Y - p._DLG_H / 2
        if sub is not None and dlg_bawah - 0.02 < sub.y < dlg_atas + 0.02:
            bentrok.append(f'subtitle y={sub.y:.3f} di dalam kotak dialog')
        bg = ents[0]
        if sub is not None and abs(sub.y - bg.y) < bg.scale_y / 2:
            bentrok.append(f'subtitle y={sub.y:.3f} di dalam modal')
        cek('A tata letak modal: prompt/Tekan/subtitle tidak bertumpuk',
            prompt is not None and tekan_e is not None and not bentrok,
            '; '.join(bentrok) or f'prompt y={prompt.y if prompt else None}')
    else:
        cek('A tata letak modal: prompt/Tekan/subtitle tidak bertumpuk', False,
            'modal tidak terbuka')

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
        siram and p._flash_ent.text == 'Tanaman disiram!',
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
        and (p._flash_ent.text or '').startswith('+1 '),
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
    except Exception as ex:
        traceback.print_exc()
        cek(f'{fase} probe meledak', False, f'{type(ex).__name__}: {ex}')
    for nama, ok, ket in hasil:
        print('CEK ' + json.dumps([nama, ok, ket], ensure_ascii=False))
    sys.stdout.flush()
    os._exit(0)


def _sub(fase, save: Path, log):
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                        '--fase', fase, '--save', str(save)],
                       cwd=ROOT, capture_output=True, text=True, timeout=600)
    log.write(f'===== {fase} (kode {r.returncode})\n{r.stdout}\n{r.stderr}\n')
    baris = [json.loads(b[4:]) for b in r.stdout.splitlines() if b.startswith('CEK ')]
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
