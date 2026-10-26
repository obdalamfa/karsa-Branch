"""probe_tampilan.py — panel menu, menu jeda, HUD, dan dunia tanpa kotak polos.

Dijaga sejak 26 Okt 2026, perombakan tampilan atas keluhan pemilik ("HUD
masih sangat jelek, menu-menu dan tutorial"):

  dunia    tidak ada quad billboard putih tanpa tekstur di scene luar
           (dulu makhluk liar di kebun/desa/danau; lihat obsidian/40-Bug/
           Makhluk liar tampil sebagai kotak putih.md)
  panel    [I] [J] [M] [H] [P] [N] [F1] membuka kartu: bingkai tampil, kaki
           punya kepingan tombol, semua teks di dalam kartu; panel yang
           digambar (J, M, H, F1) punya isi gambar sungguhan
  peta     jalur peta = portal scene (Kuburan<->Lereng, bukan Kuburan<->Desa)
  inventori grid tampil, WASD menggeser kursor, Q/E mengganti kategori
  jeda     ESC di HUD membuka jeda, dunia beku, 'Simpan' menulis save,
           ESC melanjutkan
  HUD      bilah HP dan energi berbeda warna, ikon cuaca ikut cuaca

Semua tombol lewat g.app.input (aturan #2), dari game baru; save ditulis ke
direktori sementara.

    python tools/probe_tampilan.py
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

from probe_batin import boot, ke_hud, langkah, tekan, tunggu_detik  # noqa: E402

hasil: list[tuple[str, bool, str]] = []


def cek(nama, ok, ket=''):
    hasil.append((nama, bool(ok), str(ket)))


def _kotak(e):
    from ursina import camera
    try:
        tb = e.getTightBounds(camera.ui)
    except Exception:
        return None
    if tb is None:
        return None
    lo, hi = tb
    return (lo.x, hi.x, lo.y, hi.y)


def uji_dunia(g):
    """Quad billboard putih tanpa tekstur di dunia = kotak polos melayang."""
    from ursina import scene, camera
    s = g.state
    jam_asli = s.time_minutes
    # Malam: kunang-kunang (night_only) baru dibangun saat scene dimuat malam.
    s.time_minutes = 20 * 60 + 30
    for nama in ('farm', 'town', 'lake'):
        s.scene_name = nama
        langkah(40)
        polos = []
        for e in scene.entities:
            try:
                if not e.enabled or e.has_ancestor(camera.ui):
                    continue
                m = getattr(e, 'model', None)
                if m is None or 'quad' not in str(getattr(m, 'name', '')):
                    continue
                if getattr(e, 'billboard', False) and e.texture is None:
                    polos.append(tuple(round(v, 1) for v in e.world_position))
            except Exception:
                continue
        cek(f'tidak ada kotak polos melayang di {nama}', not polos,
            f'{len(polos)} quad: {polos[:3]}')
    s.time_minutes = jam_asli
    s.scene_name = 'farm'
    langkah(40)


PANEL = (('i', 'inventory'), ('j', 'quest'), ('m', 'map'), ('h', 'relations'),
         ('p', 'wishes'), ('n', 'catatan'), ('f1', 'help'))
DIGAMBAR = ('quest', 'map', 'relations', 'help')


def uji_panel(g):
    from game import panel_kartu as PK
    p = g.panels
    for tombol, nama in PANEL:
        tekan(g, tombol, 4)
        if p.mode != 'panel' or p._panel_name != nama:
            cek(f'[{tombol}] membuka panel {nama}', False, f'mode={p.mode} nama={p._panel_name}')
            tekan(g, 'escape', 3)
            continue
        kartu = _kotak(p._panel_frame)
        tampil = p._panel_frame.enabled and p._panel_frame.texture is not None
        hidup = [e for e in p._kanvas.ents if getattr(e, 'enabled', True)]
        teks = [e for e in hidup if type(e).__name__ == 'Text'] + [p._panel_title, p._panel_body]
        kaki = [e for e in hidup if getattr(e, 'texture', None) is not None
                and abs(e.y - PK.Y_KAKI) < 0.02]
        luar = []
        if kartu:
            x0, x1, y0, y1 = kartu
            for t in teks:
                k = _kotak(t)
                if not k or not str(getattr(t, 'text', '')).strip():
                    continue
                lewat = max(x0 - k[0], k[1] - x1, y0 - k[2], k[3] - y1)
                if lewat > 0.004:
                    luar.append(f'{str(t.text)[:18]!r} {lewat:+.3f}')
        cek(f'[{tombol}] {nama}: kartu tampil, kaki berkeping, teks di dalam kartu',
            tampil and kaki and not luar,
            f'kartu={tampil} keping={len(kaki)} luar={luar[:2]}')
        if nama in DIGAMBAR:
            cek(f'[{tombol}] {nama} digambar, bukan dump teks',
                len(hidup) >= 12 and not str(p._panel_body.text).strip(),
                f'{len(hidup)} entity, body={len(str(p._panel_body.text))} huruf')
        tekan(g, 'escape', 3)
        cek(f'ESC menutup {nama} tanpa sisa kanvas',
            p.mode == 'hud' and not p._kanvas.ents, f'mode={p.mode} sisa={len(p._kanvas.ents)}')


def uji_peta():
    from game.panel_kartu import sambungan_peta
    j = set(sambungan_peta())
    cek('peta: Kuburan tersambung ke Lereng, bukan ke Desa',
        ('cemetery', 'mountain') in j and ('cemetery', 'town') not in j, sorted(j))
    cek('peta: Pantai tersambung ke Desa', ('beach', 'town') in j, sorted(j))


def uji_inventori(g):
    p, s = g.panels, g.state
    s.inventory.update({'lobak': 4, 'kayu': 7, 'batu': 3})
    tekan(g, 'i', 4)
    tampil = [sl for sl in p._inv_slots if sl['icon'].enabled]
    cek('inventori: grid menampilkan petak berikon',
        len(tampil) >= 3, f'{len(tampil)} petak berikon')
    c0 = p._inv_cursor
    tekan(g, 'd', 2)
    cek('inventori: [D] menggeser kursor', p._inv_cursor == c0 + 1,
        f'{c0} -> {p._inv_cursor}')
    k0 = p._inv_cat_idx
    tekan(g, 'e', 2)
    cek('inventori: [E] mengganti kategori', p._inv_cat_idx == (k0 + 1) % len(p._INV_CATS),
        f'{k0} -> {p._inv_cat_idx}')
    tekan(g, 'escape', 3)
    cek('inventori: ESC menyembunyikan grid',
        not any(e.enabled for sl in p._inv_slots for e in sl.values()), '')


def uji_jeda(g):
    import game.state as gs
    p, s = g.panels, g.state
    tekan(g, 'escape', 3)
    cek('ESC di HUD membuka menu jeda', p.mode == 'jeda' and p._pause_ents[1].enabled,
        f'mode={p.mode}')
    m0 = s.time_minutes if hasattr(s, 'time_minutes') else None
    tunggu_detik(1.5)
    m1 = s.time_minutes if hasattr(s, 'time_minutes') else None
    cek('dunia beku selama jeda', m0 == m1, f'{m0} -> {m1}')
    try:
        os.remove(gs.SAVE_FILE)
    except OSError:
        pass
    tekan(g, 's', 2)                       # 'Simpan Permainan'
    tekan(g, 'enter', 3)
    cek("jeda 'Simpan' menulis save dan kembali ke HUD",
        os.path.exists(gs.SAVE_FILE) and p.mode == 'hud',
        f'ada={os.path.exists(gs.SAVE_FILE)} mode={p.mode}')
    tekan(g, 'escape', 3)
    tekan(g, 'escape', 3)
    cek('ESC di jeda melanjutkan permainan', p.mode == 'hud'
        and not any(e.enabled for e in p._pause_ents), f'mode={p.mode}')


def uji_hud(g):
    p, s = g.panels, g.state
    langkah(3)
    hp, en = p._hp_bar.color, p._en_bar.color
    beda = sum(abs(a - b) for a, b in zip(hp[:3], en[:3]))
    cek('HUD: bilah HP dan energi berbeda warna', beda > 0.3, f'selisih {beda:.2f}')
    asli = s.weather
    t0 = p._weather_ikon.texture
    s.weather = 'Hujan' if asli != 'Hujan' else 'Cerah'
    langkah(3)
    cek('HUD: ikon cuaca ikut cuaca', p._weather_ikon.texture is not t0
        and p._weather_ikon.texture is not None, s.weather)
    s.weather = asli
    langkah(2)


def main():
    kerja = Path(tempfile.mkdtemp(prefix='probe_tampilan_'))
    try:
        g = boot(kerja / 'save.json')
        if not ke_hud(g):
            cek('mencapai HUD', False, 'sinema/chargen tidak selesai')
        else:
            uji_dunia(g)
            uji_hud(g)
            uji_panel(g)
            uji_peta()
            uji_inventori(g)
            uji_jeda(g)
    except Exception:
        traceback.print_exc()
        cek('probe berjalan tanpa pengecualian', False, 'lihat traceback')
    gagal = [h for h in hasil if not h[1]]
    for nama, ok, ket in hasil:
        print(f'  {"LULUS" if ok else "GAGAL"}  {nama:62s} {ket}')
    print(f'{len(hasil) - len(gagal)}/{len(hasil)} lulus')
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
