"""probe_lore_gua.py — catatan gua bertingkat, lewat tangga sungguhan.

Sampai 29 Okt 2026 tiga cacat hidup di lore gua tanpa satu error pun:

  id kosong   lantai 3/7/12 mencatat 'dungeon_3/7/12' ke koleksi, tapi id itu
              tidak punya entri LORE_ITEMS -- panel Catatan [N] menampilkan
              "[dungeon_3]" tanpa isi
  lantai 14   fragmen prasasti III menunggu di lantai 14; gua berhenti di 13
  pesan diam  tangga memanggil check_dungeon_lore tanpa panels, jadi pesannya
              baru muncul sesudah pemain tidur, dan lantai berikutnya sudah
              menimpanya lebih dulu

Probe ini turun lantai 1 -> 13 dengan BERDIRI di ubin STAIRS_DOWN (app.update
-> player.tick -> _check_portals), lalu memeriksa: tiap lantai memberi persis
catatan yang dijanjikan `found_at`, catatannya muncul sebagai flash saat tiba
dan muat di layar, kunjungan ulang tidak menggandakannya, dan panel [N]
menampilkan semua catatan utuh (berhalaman, dibuka di halaman terbaru).

    python tools/probe_lore_gua.py
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))

from probe_batin import boot, ke_hud, langkah, tekan  # noqa: E402

hasil: list[tuple[str, bool, str]] = []


def cek(nama, ok, ket=''):
    hasil.append((nama, bool(ok), str(ket)))


def _jalan(g, n=1):
    """Satu frame jalur asli. Pemain dijaga hidup: yang diuji tangga dan
    catatan, bukan pertarungan -- pingsan memulangkannya ke rumah."""
    for _ in range(n):
        langkah(1)
        g.state.hp = g.state.max_hp
        g.player._invuln = 60000


def _tunggu(g, syarat, maks=900):
    for _ in range(maks):
        _jalan(g)
        if syarat():
            return True
    return False


def _tunggu_detik(g, detik):
    """taskMgr.step memakai dt nyata, jadi waktu dimajukan dengan jam dinding."""
    t0 = time.time()
    while time.time() - t0 < detik:
        _jalan(g)


def _ubin(grid, tid):
    return [(x, y) for y, row in enumerate(grid) for x, t in enumerate(row) if t == tid]


def _injak(g, tx, ty):
    """Pemain berdiri tepat di ubin (tx, ty); tangga terpicu di tick()."""
    from game.config import TILE_SIZE as TS
    s = g.state
    s.player_x, s.player_y = float(tx), float(ty)
    g.player.x, g.player.z = tx * TS, ty * TS
    g.player.velocity_x = g.player.velocity_z = 0.0
    g.player._portal_cd = 0.0


def _tiba(g, lv):
    s = g.state
    return (s.scene_name == 'dungeon' and s.dungeon_level == lv
            and g.world.scene_name == 'dungeon'
            and getattr(g.world, 'dungeon_level', None) == lv)


def _halaman_n(g):
    """Panel [N] yang sudah terbuka: semua halamannya, mundur dengan [Q]."""
    halaman = [str(g.panels._panel_body.text)]
    for _ in range(20):
        tekan(g, 'q')
        t = str(g.panels._panel_body.text)
        if t in halaman:
            break
        halaman.append(t)
    return halaman


def uji_lore(g):
    from ursina import camera
    from game.config import STAIRS_DOWN, STAIRS_UP
    from game.data import LORE_ITEMS, DUNGEON_MAX_LEVEL
    s = g.state

    # Flash direkam (lalu diteruskan ke aslinya): peringatan lain bisa menimpa
    # teks flash sebelum sempat dibaca dari _flash_ent.
    kilat: list[str] = []
    asli = g.panels.flash_msg

    def rekam(text, duration=1.2):
        kilat.append(str(text))
        return asli(text, duration)

    g.panels.flash_msg = rekam

    janji: dict[int, list[str]] = {}
    for lid, it in LORE_ITEMS.items():
        m = re.fullmatch(r'dungeon_(\d+)', str(it.get('found_at', '')))
        if m:
            janji.setdefault(int(m.group(1)), []).append(lid)
    luar = sorted(lv for lv in janji if not 1 <= lv <= DUNGEON_MAX_LEVEL)
    cek('found_at dungeon_<n> ada di lantai yang dibuat', not luar,
        f'di luar 1..{DUNGEON_MAX_LEVEL}: {luar}' if luar else f'lantai {sorted(janji)}')

    # ── turun lewat tangga Gua Sang Hyang, lalu STAIRS_DOWN tiap lantai ──
    s.scene_name, s.player_x, s.player_y = 'naga_cave', 12.0, 10.0
    _tunggu(g, lambda: g.world.scene_name == 'naga_cave', 300)
    tangga = [(x, y) for y in range(40) for x in range(40)
              if g.world.get_tile(x, y) == STAIRS_DOWN]
    if not tangga:
        cek('naga_cave punya tangga turun', False)
        return
    _injak(g, *tangga[0])
    if not _tunggu(g, lambda: _tiba(g, 1)):
        cek('tangga naga_cave membawa ke lantai 1', False, f'scene={s.scene_name}')
        return

    salah, tanpa_flash, kelebaran, tertunda = [], [], [], []
    for lv in range(2, DUNGEON_MAX_LEVEL + 1):
        sebelum, k0 = list(s.lore_collected), len(kilat)
        turun = _ubin(s.dungeon_tiles, STAIRS_DOWN)
        if not turun:
            cek(f'lantai {lv - 1} punya tangga turun', False)
            return
        _injak(g, *turun[0])
        if not _tunggu(g, lambda: _tiba(g, lv)):
            cek(f'tangga membawa ke lantai {lv}', False,
                f'scene={s.scene_name} lv={s.dungeon_level}')
            return
        _tunggu_detik(g, 1.6)                 # flash memakai invoke(delay=1.0)
        baru = [x for x in s.lore_collected if x not in sebelum]
        if baru != janji.get(lv, []):
            salah.append(f'{lv}: {baru} != {janji.get(lv, [])}')
        if getattr(g.player, '_pending_lore_msg', None):
            tertunda.append(lv)
        if janji.get(lv):
            nama = [LORE_ITEMS[i]['name'] for i in janji[lv]]
            pesan = [t for t in kilat[k0:] if all(n in t for n in nama)]
            if not pesan:
                tanpa_flash.append(lv)
            elif str(g.panels._flash_ent.text) == pesan[-1]:
                lebar = g.panels._flash_ent.width / camera.aspect_ratio
                if not 0 < lebar <= 0.92:
                    kelebaran.append(f'{lv}: {lebar:.2f}')
    cek(f'lantai 2..{DUNGEON_MAX_LEVEL} lewat tangga tanpa pengecualian', True)
    cek('tiap lantai memberi persis catatan found_at-nya', not salah, '; '.join(salah))
    cek('catatan tampil sebagai flash saat tiba', not tanpa_flash, f'lantai {tanpa_flash}')
    cek('flash catatan muat di layar', not kelebaran, '; '.join(kelebaran))
    cek('tidak ada pesan tertunda sampai tidur', not tertunda, f'lantai {tertunda}')

    # ── naik lalu turun lagi: kunjungan ulang tidak menggandakan ──
    # Dari lantai tempat pemain SEKARANG berada, bukan dari 13: arena lantai 13
    # menaruh spawn tepat di STAIRS_UP, jadi pemain yang diam sudah terpantul
    # ke lantai 12 (cacat terpisah di dungeon.py, bukan urusan probe ini).
    lv0 = s.dungeon_level
    koleksi, k0 = list(s.lore_collected), len(kilat)
    _injak(g, *_ubin(s.dungeon_tiles, STAIRS_UP)[0])
    naik = _tunggu(g, lambda: _tiba(g, lv0 - 1))
    _tunggu_detik(g, 1.6)
    _injak(g, *_ubin(s.dungeon_tiles, STAIRS_DOWN)[0])
    turun = _tunggu(g, lambda: _tiba(g, lv0))
    _tunggu_detik(g, 1.6)
    cek(f'naik-turun ulang ({lv0}->{lv0 - 1}->{lv0}) tanpa catatan ganda',
        naik and turun and s.lore_collected == koleksi,
        f'naik={naik} turun={turun}; {koleksi} -> {s.lore_collected}')
    cek('naik-turun ulang tanpa flash ulang',
        not any('Catatan baru' in t for t in kilat[k0:]), str(kilat[k0:]))

    # ── panel [N] lewat tombol sungguhan ──
    g.panels.flash_msg('[N] Catatan baru: (probe)', 5.0)
    _jalan(g, 2)
    tekan(g, 'n')
    cek('[N] membuka panel Catatan', g.panels.mode == 'panel'
        and g.panels._panel_name == 'catatan', f'{g.panels.mode}/{g.panels._panel_name}')
    cek('[N] menyingkirkan flash yang menutupi panel', not g.panels._flash_ent.enabled)
    teks = '\n'.join(_halaman_n(g))
    kosong = [lid for lid in s.lore_collected
              if not LORE_ITEMS.get(lid, {}).get('text')
              or LORE_ITEMS[lid]['name'] not in teks
              or ' '.join(LORE_ITEMS[lid]['text'].split()[:3]) not in teks]
    cek('catatan gua tampil dengan nama dan isinya', not kosong, str(kosong))
    cek('tidak ada id mentah di panel', not re.search(r'\[dungeon_\d+\]', teks))
    tekan(g, 'escape')

    # ── koleksi lengkap: lebih panjang dari satu kartu, harus berhalaman ──
    s.lore_collected = list(LORE_ITEMS)
    tekan(g, 'n')
    hint = str(g.panels._panel_hint.text)
    terbaru = LORE_ITEMS[s.lore_collected[-1]]['name']
    cek('[N] dibuka di halaman catatan terbaru', terbaru in str(g.panels._panel_body.text),
        terbaru)
    halaman = _halaman_n(g)
    hilang = [lid for lid, it in LORE_ITEMS.items()
              if not any(it['name'] in h and it['text'].split()[-1] in h for h in halaman)]
    cek('semua catatan terbaca utuh di salah satu halaman', not hilang,
        f'{len(halaman)} halaman; hilang/terbelah: {hilang}')
    maks = max(len(h.split('\n')) for h in halaman)
    cek('tiap halaman muat di kartu (<= 28 baris)', maks <= 28, f'maks {maks} baris')
    if len(halaman) > 1:
        cek('petunjuk [Q/R] tampil', 'Q/R' in hint, hint)
    tekan(g, 'escape')
    cek('ESC menutup panel Catatan', g.panels.mode == 'hud', g.panels.mode)

    # ── pemanggil tanpa panels (probe_gua, gauntlet) tetap aman ──
    s.lore_collected = []
    g.player._pending_lore_msg = None
    g.player.quest_controller.check_dungeon_lore(3, g.player)
    cek('tanpa panels: catatan tercatat dan pesannya menunggu',
        s.lore_collected == ['dungeon_3'] and bool(g.player._pending_lore_msg),
        f'{s.lore_collected} / {g.player._pending_lore_msg!r}')


def main():
    kerja = Path(tempfile.mkdtemp(prefix='probe_lore_gua_'))
    try:
        g = boot(kerja / 'save.json')
        if not ke_hud(g):
            cek('mencapai HUD', False, 'sinema/chargen tidak selesai')
        else:
            # Semua adegan ditandai sudah ditonton, mekanisme yang sama dengan
            # regress: adegan interaksi pertama (tiba di gua) menyetel mode
            # 'sinema', yang membekukan pemain dan tangga.
            from game.cutscene import NASKAH
            g.state.sinema_selesai = list(NASKAH)
            b = list(getattr(g.state, 'batin_sekali', []) or [])
            g.state.batin_sekali = b + ['pagi_pertama']
            uji_lore(g)
    except Exception:
        traceback.print_exc()
        cek('probe berjalan tanpa pengecualian', False, 'lihat traceback')
    gagal = [h for h in hasil if not h[1]]
    for nama, ok, ket in hasil:
        print(f'  {"LULUS" if ok else "GAGAL"}  {nama:52s} {ket}')
    print(f'{len(hasil) - len(gagal)}/{len(hasil)} lulus')
    sys.stdout.flush()
    shutil.rmtree(kerja, ignore_errors=True)
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
