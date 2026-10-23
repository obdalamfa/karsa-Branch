"""probe_sinema.py — layar judul, adegan pembuka, cerita interaksi pertama, menu radial.

Dimainkan lewat dispatcher Ursina `g.app.input` dari `Game3D(layar_judul=True)`,
persis jalur `run()` di main.py. Dua fase, masing-masing subproses sendiri
(Game3D hanya bisa dibuat sekali per proses):

  BARU    tanpa save: judul -> Permainan Baru -> Buat Karakter -> adegan
          pembuka ditonton sampai habis -> surat [F] -> adegan 'surat' ->
          tiba di desa -> adegan 'kota' -> menu radial kasur dan warga
  LANJUT  dengan save: judul menawarkan Lanjutkan -> HUD; lalu proses kedua
          memilih Permainan Baru -> konfirmasi -> Buat Karakter dengan state
          baru, save lama TIDAK terhapus

Save ditulis ke direktori sementara (game.state.SAVE_FILE ditambal).

    python tools/probe_sinema.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

hasil: list[tuple[str, bool, str]] = []


def cek(nama, ok, ket=''):
    hasil.append((nama, bool(ok), str(ket)))


def langkah(n=1):
    from direct.showbase.ShowBaseGlobal import base
    for _ in range(n):
        base.taskMgr.step()


def tunggu(detik):
    t0 = time.time()
    while time.time() - t0 < detik:
        langkah(1)


def tekan(g, key, n=3):
    """Tekan LALU lepas, seperti jari. Tanpa 'up', held_keys['w'] tertahan:
    pemain terus berjalan dan menu radial menutup sendiri (versi pertama
    probe ini salah karena itu)."""
    from ursina.main import keyboard_keys
    g.app.input(key, key in keyboard_keys)
    langkah(1)
    if key in keyboard_keys:
        g.app.input(key + ' up', True)
    langkah(max(0, n - 1))


def boot(save_path: Path):
    os.chdir(ROOT)
    from panda3d.core import loadPrcFileData, getModelPath
    loadPrcFileData('', 'audio-library-name null')
    loadPrcFileData('', 'sync-video false')
    import logging
    logging.basicConfig(level=logging.ERROR)
    from ursina import application
    application.asset_folder = ROOT
    application.fonts_folder = ROOT / 'assets' / 'fonts'
    getModelPath().append_path(str(ROOT.resolve()))
    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = 640, 360
    import game.state as gs
    gs.SAVE_FILE = str(save_path)
    from game.app import Game3D
    return Game3D(layar_judul=True)


def tracker_tampil(g):
    e = getattr(g.panels, '_obj_bg', None)
    return bool(e is not None and e.enabled)


def tonton(g, nama, maks_detik=90):
    """Tonton sinema `nama` sampai habis dengan SPACE. Kembalikan daftar
    jenis beat yang benar-benar dilalui."""
    dilalui = []
    t0 = time.time()
    while g.sinema.aktif and time.time() - t0 < maks_detik:
        i = g.sinema._i
        if 0 <= i < len(g.sinema._beat):
            j = g.sinema._beat[i][0]
            if not dilalui or dilalui[-1][0] != i:
                dilalui.append((i, j, g.sinema._baris_t.text if j == 'tujuan' else ''))
        if g.sinema._menunggu:
            tekan(g, 'space', 2)
        else:
            langkah(1)
    return dilalui


def tunggu_sinema(g, detik=3.0):
    t0 = time.time()
    while time.time() - t0 < detik:
        langkah(1)
        if g.sinema.aktif:
            return g.sinema.nama
    return None


def kotak_tindih(a, b, celah=0.004):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (abs(ax - bx) < (aw + bw) / 2 - celah) and (abs(ay - by) < (ah + bh) / 2 - celah)


def cek_tata_pie(g, label):
    p = g.panels
    kotak = list(p._pie_kotak)
    n = len(p._pie_options[:p._PIE_MAKS])
    cek(f'{label}: semua pilihan tampil', len(kotak) == n == len(p._pie_options),
        f'kapsul {len(kotak)} / opsi {len(p._pie_options)}')
    tindih = [(i, j) for i in range(len(kotak)) for j in range(i + 1, len(kotak))
              if kotak_tindih(kotak[i], kotak[j])]
    cx, cy = p._PIE_PUSAT
    r = p._pie_cincin.scale_x / 2
    kena = [i for i, (x, y, w, h) in enumerate(kotak)
            if abs(x - cx) < w / 2 + r - 0.01 and abs(y - cy) < h / 2 + r - 0.01
            and ((max(abs(x - cx) - w / 2, 0)) ** 2 + (max(abs(y - cy) - h / 2, 0)) ** 2) ** 0.5 < r - 0.005]
    cek(f'{label}: kapsul tidak saling tindih dan tidak menindih cakram',
        not tindih and not kena, f'tindih={tindih} kena_cakram={kena}')


# ─── fase BARU ──────────────────────────────────────────────────────────────
def fase_baru(g):
    from game.config import MB, BD
    from game.scenes import SCENES
    p, s = g.panels, g.state
    langkah(10)
    cek('BARU boot ke layar judul', p.mode == 'judul', f'mode={p.mode}')
    opsi = [a for a, _ in g._judul._opsi] if g._judul else []
    cek('BARU tanpa save: tidak ada "Lanjutkan"', opsi[:1] == ['baru'], opsi)
    cek('BARU pelacak tutorial tersembunyi di layar judul', not tracker_tampil(g),
        f'_obj_bg.enabled={tracker_tampil(g)}')
    yaw0 = g.camera_yaw
    tunggu(1.0)
    cek('BARU kamera judul mengorbit dunia', abs(g.camera_yaw - yaw0) > 1.0,
        f'yaw {yaw0:.1f} -> {g.camera_yaw:.1f}')

    tekan(g, 's')
    pilih = g._judul._opsi[g._judul._pilih][0]
    cek('BARU [S] menggeser pilihan', pilih == 'panduan', pilih)
    tekan(g, 'enter')
    cek('BARU Panduan terbuka', g._judul._layar == 'panduan' and g._judul._p_teks.enabled,
        g._judul._layar)
    tekan(g, 'escape')
    cek('BARU ESC kembali ke menu utama (bukan keluar/menyimpan)',
        p.mode == 'judul' and g._judul._layar == 'utama', f'mode={p.mode}')
    while g._judul._opsi[g._judul._pilih][0] != 'baru':
        tekan(g, 'w')
    tekan(g, 'enter', 6)
    cek('BARU Permainan Baru membuka Buat Karakter', p.mode == 'chargen',
        f'mode={p.mode} judul={g._judul}')

    tekan(g, 'enter', 6)
    nama = tunggu_sinema(g)
    cek('BARU adegan pembuka mulai sesudah Buat Karakter', nama == 'datang', nama)
    cek('BARU adegan warga belum tercatat sebelum bicara dengan warga',
        'warga' not in s.sinema_selesai, s.sinema_selesai)
    cek('BARU pelacak tutorial tersembunyi selama sinema', not tracker_tampil(g),
        tracker_tampil(g))
    yaw_pemain = g.sinema._kam_pemain[2] if g.sinema._kam_pemain else None
    jalan = tonton(g, 'datang')
    jenis = [j for _, j, _ in jalan]
    cek('BARU pembuka memakai kartu judul, tirai, dan kamera mengorbit',
        {'kartu', 'gelap', 'kamera'} <= set(jenis), jenis)
    tujuan = [t for _, j, t in jalan if j == 'tujuan']
    cek('BARU pembuka ditutup tujuan tutorial (baca surat)',
        bool(tujuan) and 'surat' in tujuan[-1].lower(), tujuan)
    cek('BARU sesudah pembuka: HUD, tercatat ditonton',
        p.mode == 'hud' and 'datang' in s.sinema_selesai, f'mode={p.mode}')
    cek('BARU sudut kamera pemain dipulihkan (arah WASD tidak bergeser)',
        yaw_pemain is not None and abs(g.camera_yaw - yaw_pemain) < 0.01,
        f'{yaw_pemain} -> {g.camera_yaw:.2f}')
    cek('BARU pelacak tutorial kembali sesudah sinema', tracker_tampil(g), tracker_tampil(g))

    # Surat -> adegan 'surat'
    mb = next((x, y) for y, r in enumerate(SCENES['farm'].tiles)
              for x, v in enumerate(r) if v == MB)
    g.player.set_tile_pos(mb[0], mb[1] - 1)
    g.player.facing = 'up'
    langkah(3)
    tekan(g, 'f', 6)
    for _ in range(8):
        # Tutup kotak dialog surat, tapi JANGAN tekan ESC kalau adegan
        # sudah mulai -- ESC melewati adegan (versi pertama probe ini
        # melewati adegan 'surat' sendiri lalu menyimpulkan ia tidak main).
        if p.mode in ('hud', 'sinema'):
            break
        tekan(g, 'escape', 4)
    nama = tunggu_sinema(g)
    cek('BARU membaca surat memicu adegan "surat"', nama == 'surat',
        f'{nama} mail_read={s.mail_read} mode={p.mode} tile={g.player.get_tile_pos()} '
        f'mb={mb} selesai={s.sinema_selesai}')
    jalan = tonton(g, 'surat')
    tujuan = [t for _, j, t in jalan if j == 'tujuan']
    cek('BARU adegan surat ditutup tujuan berikutnya (cangkul)',
        bool(tujuan) and 'cangkul' in tujuan[-1].lower(), tujuan)
    nama2 = tunggu_sinema(g, 1.5)
    cek('BARU adegan tidak diputar dua kali', nama2 is None, nama2)

    # Tiba di desa -> 'kota'
    s.scene_name = 'town'
    nama = tunggu_sinema(g, 6.0)
    cek('BARU tiba di desa memicu adegan "kota"', nama == 'kota', nama)
    tekan(g, 'escape', 4)
    cek('BARU ESC melewati adegan, kembali ke HUD',
        p.mode == 'hud' and not g.sinema.aktif and 'kota' in s.sinema_selesai,
        f'mode={p.mode} aktif={g.sinema.aktif}')

    # Menu radial: kasur
    from game.cutscene import NASKAH
    s.sinema_selesai = list(NASKAH)            # sisa adegan bukan yang diuji di sini
    s.scene_name = 'house'
    langkah(40)
    bd = next((x, y) for y, r in enumerate(SCENES['house'].tiles)
              for x, v in enumerate(r) if v == BD)
    g.player.set_tile_pos(bd[0], bd[1] + 1)
    g.player.facing = 'up'
    langkah(4)
    tekan(g, 'f', 4)
    cek('BARU [F] di dekat kasur membuka menu radial', p.mode == 'pie',
        f'mode={p.mode} judul={p._pie_title.text!r}')
    if p.mode == 'pie':
        cek_tata_pie(g, 'BARU kasur')
        sel0 = p._pie_selected
        tekan(g, 'e')
        cek('BARU [E] di menu radial menggeser ke kanan',
            p._pie_selected == (sel0 + 1) % len(p._pie_options), p._pie_selected)
        tekan(g, 'q')
        cek('BARU [Q] di menu radial menggeser ke kiri', p._pie_selected == sel0,
            p._pie_selected)
        tekan(g, 'escape')
    cek('BARU ESC menutup menu radial', p.mode == 'hud', p.mode)

    # Menu radial: delapan pilihan berlabel panjang (tata letak terburuk)
    opsi = [(f'x{i}', f'Pilihan dengan label cukup panjang {i}', i % 2 == 0, '+Sosial')
            for i in range(8)]
    p.open_pie_menu('pak_guru', opsi, lambda *a: None)
    langkah(2)
    cek_tata_pie(g, 'BARU 8 pilihan panjang')
    p.close_pie()


# ─── fase LANJUT ────────────────────────────────────────────────────────────
def fase_lanjut(g, pilihan):
    p, s = g.panels, g.state
    langkah(10)
    opsi = [a for a, _ in g._judul._opsi] if g._judul else []
    if pilihan == 'lanjut':
        cek('LANJUT save ada: "Lanjutkan" pilihan pertama', opsi[:1] == ['lanjut'], opsi)
        nama_save = s.char_name
        tekan(g, 'enter', 6)
        # Save ini belum pernah menonton adegan pembuka (quest_stage 0), jadi
        # adegan itu diputar dulu -- seperti pemain lama yang baru memperbarui.
        if tunggu_sinema(g, 1.5):
            tonton(g, g.sinema.nama)
        cek('LANJUT Lanjutkan masuk HUD dengan save yang sama',
            p.mode == 'hud' and s.char_name == nama_save and nama_save,
            f'mode={p.mode} nama={s.char_name!r}')
        cek('LANJUT kamera kembali ke sudut main (bukan orbit judul)',
            abs(g.camera_dist - 19.0) < 0.01 and abs(g.camera_pitch - 34.0) < 0.01,
            f'dist={g.camera_dist} pitch={g.camera_pitch}')
    else:
        import game.state as gs
        save = Path(gs.SAVE_FILE)
        isi_lama = save.read_text(encoding='utf-8')
        while g._judul._opsi[g._judul._pilih][0] != 'baru':
            tekan(g, 's')
        tekan(g, 'enter')
        cek('LANJUT Permainan Baru dengan save: minta konfirmasi, Batal terpilih',
            g._judul._layar == 'konfirmasi'
            and g._judul._opsi[g._judul._pilih][0] == 'batal', g._judul._layar)
        tekan(g, 'w')
        tekan(g, 'enter', 10)
        cek('LANJUT konfirmasi: Buat Karakter dengan state baru',
            p.mode == 'chargen' and not s.char_name and s.day == 1,
            f'mode={p.mode} nama={s.char_name!r} hari={s.day}')
        cek('LANJUT save lama tidak dihapus sebelum disimpan ulang',
            save.exists() and save.read_text(encoding='utf-8') == isi_lama, save)


def jalankan_fase(fase, save):
    g = boot(save)
    try:
        if fase == 'BARU':
            fase_baru(g)
        else:
            fase_lanjut(g, 'lanjut' if fase == 'LANJUT1' else 'baru')
    except Exception as ex:
        traceback.print_exc()
        cek(f'{fase} probe meledak', False, f'{type(ex).__name__}: {ex}')
    print('HASIL_JSON ' + json.dumps(hasil, ensure_ascii=False), flush=True)
    os._exit(0)


def _sub(fase, save, log):
    r = subprocess.run([sys.executable, __file__, '--fase', fase, '--save', str(save)],
                       cwd=ROOT, capture_output=True, text=True, timeout=600)
    log.write(f'=== {fase} (kode {r.returncode})\n{r.stdout}\n{r.stderr}\n')
    for b in r.stdout.splitlines():
        if b.startswith('HASIL_JSON '):
            return json.loads(b[len('HASIL_JSON '):])
    return [[f'{fase} subproses tanpa hasil', False, f'kode {r.returncode}']]


def main():
    args = sys.argv[1:]
    if '--fase' in args:
        jalankan_fase(args[args.index('--fase') + 1], Path(args[args.index('--save') + 1]))
        return
    kerja = Path(tempfile.mkdtemp(prefix='probe_sinema_'))
    semua = []
    with open(kerja / 'log.txt', 'w', encoding='utf-8') as log:
        semua += _sub('BARU', kerja / 'baru.json', log)
        save = kerja / 'lanjut.json'
        shutil.copy(ROOT / 'tools' / 'fixtures' / 'regress_save.json', save)
        semua += _sub('LANJUT1', save, log)
        semua += _sub('LANJUT2', save, log)

    print('\nSINEMA, LAYAR JUDUL, MENU RADIAL — lewat app.input dari run()')
    print('=' * 78)
    lebar = max(len(n) for n, _, _ in semua)
    for nama, ok, ket in semua:
        print(f"{'LULUS' if ok else 'GAGAL':>5s}  {nama:<{lebar}s}  {str(ket)[:60]}")
    gagal = [n for n, ok, _ in semua if not ok]
    print('-' * 78)
    print(f'{len(semua) - len(gagal)}/{len(semua)} lulus  (log: {kerja / "log.txt"})')
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
