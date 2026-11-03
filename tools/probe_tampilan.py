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

import math
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
                # Tekstur kosong = None ATAU objek Texture tanpa nama (quad
                # Ursina polos mencetak tekstur '' -- versi pertama probe ini
                # hanya memeriksa None dan meloloskan mutasi kotak polos).
                tex = e.texture
                if getattr(e, 'billboard', False) and (tex is None or not str(tex).strip()):
                    polos.append(tuple(round(v, 1) for v in e.world_position))
            except Exception:
                continue
        cek(f'tidak ada kotak polos melayang di {nama}', not polos,
            f'{len(polos)} quad: {polos[:3]}')
    s.time_minutes = jam_asli
    s.scene_name = 'farm'
    langkah(40)


PANEL = (('i', 'inventory'), ('j', 'quest'), ('m', 'map'), ('h', 'relations'),
         ('p', 'wishes'), ('n', 'catatan'), ('f1', 'help'), ('f6', 'papan'),
         ('f4', 'ekosistem'))
DIGAMBAR = ('quest', 'map', 'relations', 'help', 'wishes', 'papan', 'ekosistem',
            'shop', 'olahan', 'crafting')


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
    beda = sum(abs(hp[i] - en[i]) for i in range(3))
    cek('HUD: bilah HP dan energi berbeda warna', beda > 0.3, f'selisih {beda:.2f}')
    asli = s.weather
    t0 = p._weather_ikon.texture
    s.weather = 'Hujan' if asli != 'Hujan' else 'Cerah'
    langkah(3)
    cek('HUD: ikon cuaca ikut cuaca', p._weather_ikon.texture is not t0
        and p._weather_ikon.texture is not None, s.weather)
    s.weather = asli
    langkah(2)


def _buka_di(g, scene, tombol, nama):
    s, p = g.state, g.panels
    s.scene_name = scene
    langkah(30)
    tekan(g, tombol, 4)
    return p.mode == 'panel' and p._panel_name == nama


def uji_panel_berbaris(g):
    """Warung, Dapur, Bengkel lewat tombol aslinya di tempatnya, dan angka
    di baris yang tergambar menjalankan baris yang sama."""
    p, s = g.panels, g.state
    s.gold = 5000
    s.inventory.update({'kayu': 40, 'besi': 10, 'lobak': 8})
    for scene, tombol, nama in (('shop', 'k', 'shop'), ('house', 'o', 'olahan'),
                                ('smith', 'u', 'crafting')):
        if not _buka_di(g, scene, tombol, nama):
            cek(f'[{tombol}] di {scene} membuka {nama}', False, f'mode={p.mode} {p._panel_name}')
            continue
        hidup = [e for e in p._kanvas.ents if getattr(e, 'enabled', True)]
        cek(f'{nama} digambar berbaris, bukan tabel teks',
            len(hidup) >= 20 and not str(p._panel_body.text).strip(),
            f'{len(hidup)} entity')
        if nama == 'shop':
            n0 = s.inventory.get('lobak_seed', 0)
            tekan(g, '1', 3)
            cek('Warung: [1] membeli baris pertama yang tergambar (Benih Lobak)',
                s.inventory.get('lobak_seed', 0) == n0 + 1, f'{n0} -> {s.inventory.get("lobak_seed", 0)}')
        if nama == 'crafting':
            tekan(g, 'e', 2)
            tekan(g, 'e', 2)
            cek('Bengkel: [E][E] pindah ke tab Perkakas', getattr(p, '_craft_tab', 0) == 2,
                getattr(p, '_craft_tab', None))
            n0 = s.inventory.get('perahu', 0)
            tekan(g, '1', 3)
            cek('Bengkel: Perahu Kayu bisa dibuat (dulu nomor [10], tak terjangkau)',
                s.inventory.get('perahu', 0) == n0 + 1, f'{n0} -> {s.inventory.get("perahu", 0)}')
        tekan(g, 'escape', 3)
    s.scene_name = 'farm'
    langkah(30)


def uji_penunjuk(g):
    """Penunjuk tujuan tutorial (game/penunjuk.py) lewat jalur asli."""
    from ursina import Entity, camera, destroy
    from game.config import TILE_SIZE as TS, MB, BD
    from game.penunjuk import _tile_pertama
    s, P = g.state, g.penunjuk
    jam = s.time_minutes
    s.scene_name = 'farm'
    langkah(30)
    s.mail_read = False
    tunggu_detik(0.4)
    mb = _tile_pertama('farm', MB)
    cek('penunjuk: langkah surat menunjuk kotak pos',
        P.titik is not None and tuple(P.titik[1:3]) == mb and
        (P.ketupat.enabled or P.panah.enabled), f'titik={P.titik} kotak pos={mb}')
    tekan(g, 'i', 3)
    cek('penunjuk: sembunyi saat panel terbuka',
        not P.ketupat.enabled and not P.panah.enabled, f'mode={g.panels.mode}')
    tekan(g, 'escape', 3)

    # Arah layar benar di empat sudut kamera: titik di kanan kamera harus
    # jatuh di kanan layar. Versi pertama membaca sumbu kedalaman yang salah
    # (Panda di Ursina memakai yup-left: depan = +z) dan menunjuk terbalik.
    salah = []
    px, py = g.player.get_tile_pos()
    for yaw in (0, 90, 180, 270):
        g.camera_yaw = yaw
        langkah(2)
        g._snap_camera_to_player()
        langkah(2)
        r = camera.right
        e = Entity(position=(px * TS + r.x * 6, 1.0, py * TS + r.z * 6))
        sp = P._layar(e)
        destroy(e)
        if sp is None or sp[0] <= 0.05:
            salah.append(f'yaw {yaw}: {sp}')
    cek('penunjuk: titik di kanan kamera jatuh di kanan layar', not salah, '; '.join(salah))

    # Tidur: dari kebun menunjuk portal rumah, di dalam rumah menunjuk kasur.
    s.mail_read = True
    s.stats.update({'tilled': 3, 'lobak_planted': 3, 'watered': 3})
    tunggu_detik(0.4)
    from game.penunjuk import _portal_menuju
    pintu = _portal_menuju('farm', 'house')
    cek('penunjuk: langkah tidur dari kebun menunjuk pintu rumah',
        P.titik is not None and tuple(P.titik[1:3]) == tuple(pintu), f'{P.titik} pintu={pintu}')
    s.scene_name = 'house'
    langkah(30)
    tunggu_detik(0.3)
    kasur = _tile_pertama('house', BD)
    cek('penunjuk: di dalam rumah menunjuk kasur',
        P.titik is not None and tuple(P.titik[1:3]) == kasur, f'{P.titik} kasur={kasur}')
    s.day = 3
    s.stats.update({'lobak_harvested': 1, 'earned': 10})
    tunggu_detik(0.3)
    # Sejak 3 Nov 2026 penunjuk tidak padam saat tutorial tamat: ia
    # meneruskan ke tugas utama (uji_penunjuk_quest). Yang dijaga di sini:
    # langkah tutorial tidak lagi ditunjuk -- bukan kasur lagi.
    cek('penunjuk: sesudah tutorial tamat tidak lagi menunjuk langkah tutorial',
        P.titik is None or P.titik[3] != 'Kasur', str(P.titik))
    s.scene_name = 'farm'
    s.time_minutes = jam
    langkah(30)


def _pindah(g, nama, tx=None, ty=None):
    s = g.state
    s.scene_name = nama
    langkah(40)
    if tx is not None:
        g.player.set_tile_pos(tx, ty)
    g.player._portal_cd = 3.0
    langkah(4)


def uji_penunjuk_quest(g):
    """Sesudah tutorial: penunjuk mengikuti tugas utama (QuestController)."""
    from game.config import STAIRS_DOWN, STAIRS_UP
    s, P = g.state, g.penunjuk
    # Adegan tiba di tempat baru (lereng, desa, dungeon) menelan mode HUD;
    # adegan diuji probe_sinema, bukan di sini.
    from game.cutscene import NASKAH
    sinema_lama = list(s.sinema_selesai)
    s.sinema_selesai = list(NASKAH)
    simpan = (s.quest_stage, s.pickaxe_tier, s.sword_id, s.day, dict(s.stats),
              s.mail_read, s.time_minutes)
    s.mail_read = True
    s.day = 3
    s.stats.update({'tilled': 3, 'lobak_planted': 3, 'watered': 3,
                    'lobak_harvested': 3, 'earned': 10})
    emas = s.gold
    s.gold = max(s.gold, 200)            # tahap 3 (150G) terpenuhi
    try:
        s.quest_stage, s.pickaxe_tier, s.sword_id = 4, 0, None
        _pindah(g, 'farm', 20, 10)
        cek('quest Alat Lebih Baik: dari kebun menunjuk ke Bengkel',
            P.titik is not None and P.titik[0] == 'farm' and 'Bengkel' in P.titik[3],
            str(P.titik))
        _pindah(g, 'smith', 4, 5)
        budi = (s.npc_positions.get('budi') or {}).get('scene')
        cek('quest Alat Lebih Baik: di dalam Bengkel menunjuk Pak Budi (atau padam)',
            (P.titik is not None and 'Budi' in P.titik[3]) if budi == 'smith'
            else P.titik is None, f'{P.titik} budi di {budi}')

        s.quest_stage, s.pickaxe_tier = 5, 1
        _pindah(g, 'mountain', 15, 12)
        cek('quest Eksplorasi Gua (punya pickaxe): lereng menunjuk Gua Sang Hyang',
            P.titik is not None and 'Gua Sang Hyang' in P.titik[3], str(P.titik))

        s.quest_stage = 8
        _pindah(g, 'town', 15, 14)
        # Kuburan Tua tidak punya makhluk yang bisa ditangkap; yang ditunjuk
        # harus makhluk liar sungguhan (di sini, atau pintu ke scene yang punya).
        # Sejak 3 Nov 2026 Kuburan Tua punya makhluk halus (kemamang, tuyul):
        # dari desa, penunjuk harus mengarah ke sana.
        cek('quest Misteri Kuburan: dari desa menunjuk ke Kuburan Tua',
            P.titik is not None and 'Kuburan' in P.titik[3], str(P.titik))

        # Penambang Pemula di dungeon: bijih tembaga terdekat.
        from game.config import ORE_TBG
        s.quest_stage, s.pickaxe_tier, s.sword_id = 6, 1, None
        s.stats['deepest_level'] = 2
        s.inventory['tembaga'] = 0
        s.dungeon_level = 3
        s.scene_name = 'dungeon'
        g.player._generate_and_enter_dungeon()
        g.player._portal_cd = 3.0
        langkah(40)
        bijih = {(x, y) for y, r in enumerate(s.dungeon_tiles)
                 for x, v in enumerate(r) if v == ORE_TBG}
        cek('quest Penambang: di dungeon menunjuk bijih tembaga',
            (P.titik is not None and tuple(P.titik[1:3]) in bijih) if bijih
            else (P.titik is not None and 'Tangga' in P.titik[3]),
            f'{P.titik} bijih={len(bijih)}')
        # Pendekar Karsa: mob terdekat.
        s.quest_stage, s.sword_id = 7, 'sword_besi'
        s.inventory.update({'tembaga': 5, 'besi': 3})
        langkah(3)
        # Mob bergerak di antara frame penunjuk menghitung dan probe membaca:
        # cocok kalau dalam 1,5 petak dari mob hidup mana pun (ditemukan saat
        # mutasi -- versi 'sama persis' sempat GAGAL tanpa sebab).
        mob = [(m['x'], m['y']) for m in s.mobs if m.get('hp', 0) > 0]
        dekat = P.titik is not None and any(
            math.hypot(P.titik[1] - mx, P.titik[2] - my) <= 1.5 for mx, my in mob)
        cek('quest Pendekar: di dungeon menunjuk lawan',
            dekat if mob else (P.titik is not None and 'Tangga' in P.titik[3]),
            f'{P.titik} mob={len(mob)}')
        # Boss: bos hidup di lantai ini ditunjuk.
        s.stats['mobs_killed'] = 5
        s.captured_supernatural = 1
        s.stats['deepest_level'] = 10
        s.mobs.append({'kind': 'bhutakala', 'x': 5.0, 'y': 5.0, 'hp': 99, 'max_hp': 99,
                       'is_boss': True})
        langkah(3)
        cek('quest Boss: bos hidup di lantai ini ditunjuk',
            P.titik is not None and tuple(P.titik[1:3]) == (5, 5), str(P.titik))
        s.mobs.pop()
        s.captured_supernatural = 0
        s.quest_stage = 9
        s.stats['deepest_level'] = 2
        s.dungeon_level = 2
        s.scene_name = 'dungeon'             # urutan sama dengan probe_gua
        g.player._generate_and_enter_dungeon()
        g.player._portal_cd = 3.0
        langkah(40)
        bawah = next(((x, y) for y, r in enumerate(s.dungeon_tiles)
                      for x, v in enumerate(r) if v == STAIRS_DOWN), None)
        cek('quest Kedalaman: di dungeon menunjuk tangga turun lantai itu',
            P.titik is not None and bawah is not None and tuple(P.titik[1:3]) == bawah,
            f'{P.titik} tangga={bawah}')
        # Alat Lebih Baik lagi: tanpa pickaxe/pedang tahap 4 belum terpenuhi,
        # jadi tujuannya Bengkel -- di luar dungeon.
        s.quest_stage, s.pickaxe_tier, s.sword_id = 4, 0, None
        langkah(3)
        naik = next(((x, y) for y, r in enumerate(s.dungeon_tiles)
                     for x, v in enumerate(r) if v == STAIRS_UP), None)
        cek('dari dungeon ke tempat di luar: menunjuk tangga naik',
            P.titik is not None and naik is not None and tuple(P.titik[1:3]) == naik,
            f'{P.titik} naik={naik}')
    finally:
        (s.quest_stage, s.pickaxe_tier, s.sword_id, s.day, st, s.mail_read,
         s.time_minutes) = simpan
        s.stats.clear(); s.stats.update(st)
        s.gold = emas
        _pindah(g, 'farm', 20, 10)
        s.sinema_selesai = sinema_lama


def uji_penunjuk_dua_desa(g):
    """Penunjuk kedua (biru-hijau) untuk Cerita Dua Desa."""
    from game.config import PPN
    from game.penunjuk import _tile_pertama
    from game.cutscene import NASKAH
    s, D = g.state, g.penunjuk_dd
    simpan = (s.dua_desa_stage, s.mail_read, s.day, dict(s.stats), list(s.sinema_selesai),
              getattr(s, 'gotong_royong_hari', 0))
    s.sinema_selesai = list(NASKAH)
    try:
        s.mail_read = False
        _pindah(g, 'farm', 20, 10)
        cek('Dua Desa: penunjuk kedua diam selama tutorial', D.titik is None, str(D.titik))
        s.mail_read, s.day = True, 3
        s.stats.update({'tilled': 3, 'lobak_planted': 3, 'watered': 3,
                        'lobak_harvested': 3, 'earned': 10})
        s.dua_desa_stage = 0
        _pindah(g, 'farm', 20, 10)
        cek('Dua Desa tahap 0: dari kebun menunjuk ke arah Kades Hardjo',
            D.titik is not None and D.ketupat.texture is not g.penunjuk.ketupat.texture
            and ('Desa' in D.titik[3] or 'Hardjo' in D.titik[3]), str(D.titik))
        s.dua_desa_stage = 3
        s.stats['titipan_karsa'] = 0
        _pindah(g, 'town', 15, 14)
        ppn = _tile_pertama('town', PPN)
        cek('Dua Desa Juru Titip: di desa menunjuk papan titipan Balai Desa',
            D.titik is not None and tuple(D.titik[1:3]) == ppn, f'{D.titik} papan={ppn}')
        s.dua_desa_stage = 6
        s.gotong_royong_hari = s.day
        _pindah(g, 'lawang', 12, 12)
        from game.scenes.lawang import JALAN_LONGSOR
        cek('Dua Desa Gotong Royong: di Lawang menunjuk longsor',
            D.titik is not None and tuple(D.titik[1:3]) == tuple(JALAN_LONGSOR[0]), str(D.titik))
    finally:
        (s.dua_desa_stage, s.mail_read, s.day, st, sn, s.gotong_royong_hari) = simpan
        s.stats.clear(); s.stats.update(st)
        _pindah(g, 'farm', 20, 10)
        s.sinema_selesai = sn


def uji_kuburan(g):
    """Makhluk halus Kuburan Tua bisa ditemukan, ditunjuk, dan ditangkap."""
    from ursina import held_keys
    from game.cutscene import NASKAH
    from game.controllers.quest_controller import QuestController
    s, P = g.state, g.penunjuk
    sn = list(s.sinema_selesai)
    s.sinema_selesai = list(NASKAH)
    jenis = {w['kind'] for w in s.wild_entities if w.get('scene') == 'cemetery'}
    cek('game baru: Kuburan Tua punya kemamang dan tuyul',
        {'kemamang', 'tuyul'} <= jenis, sorted(jenis))
    simpan = (s.quest_stage, s.mail_read, s.day, dict(s.stats), s.time_minutes,
              s.captured_supernatural, s.gold, s.pickaxe_tier, s.sword_id)
    try:
        s.mail_read, s.day, s.time_minutes = True, 3, 10 * 60
        s.stats.update({'tilled': 3, 'lobak_planted': 3, 'watered': 3, 'lobak_harvested': 3,
                        'earned': 10, 'deepest_level': 1, 'mobs_killed': 5})
        s.gold, s.pickaxe_tier, s.sword_id = 200, 1, 'sword_besi'
        s.inventory.update({'tembaga': 5, 'besi': 3})
        s.quest_stage, s.captured_supernatural = 8, 0
        _pindah(g, 'cemetery', 10, 10)
        tuyul = [w for w in s.wild_entities if w['scene'] == 'cemetery' and w['kind'] == 'tuyul']
        model_ok = bool(g.entities.wild_ents) and all(
            getattr(e, 'model', None) is None or 'quad' not in str(getattr(e.model, 'name', ''))
            for e in g.entities.wild_ents.values())
        cek('di kuburan siang: tuyul tampil sebagai model (bukan kotak polos)',
            tuyul and model_ok, f'{len(tuyul)} tuyul, {len(g.entities.wild_ents)} entity liar')
        cek('di kuburan: penunjuk menunjuk makhluk halus',
            P.titik is not None and 'Makhluk halus' in P.titik[3], str(P.titik))
        n0 = s.captured_supernatural
        for _ in range(25):
            hidup = [w for w in s.wild_entities if w['scene'] == 'cemetery'
                     and w['kind'] == 'tuyul']
            if not hidup or s.captured_supernatural > n0:
                break
            w = hidup[0]
            g.player.set_tile_pos(int(round(w['x'])), int(round(w['y'])))
            langkah(1)
            held_keys['shift'] = 1
            tekan(g, 'f', 2)
            held_keys['shift'] = 0
            if g.panels.mode != 'hud':
                tekan(g, 'escape', 2)
        cek('[Shift]+[F] menangkap makhluk halus kuburan, syarat Misteri Kuburan terpenuhi',
            s.captured_supernatural > n0 and QuestController(s)._stage_done(8),
            f'tertangkap {s.captured_supernatural - n0}')
    finally:
        held_keys['shift'] = 0
        (s.quest_stage, s.mail_read, s.day, st, s.time_minutes, s.captured_supernatural,
         s.gold, s.pickaxe_tier, s.sword_id) = simpan
        s.stats.clear(); s.stats.update(st)
        _pindah(g, 'farm', 20, 10)
        s.sinema_selesai = sn


def uji_saklar_penunjuk(g):
    """[F8] memutar empat mode penunjuk."""
    s = g.state
    simpan = (s.mail_read, s.day, dict(s.stats), s.dua_desa_stage, s.gold,
              s.pickaxe_tier, s.sword_id, s.quest_stage)
    try:
        # Tahap Alat Lebih Baik: penunjuk emas pasti punya tujuan (Bengkel).
        s.gold, s.pickaxe_tier, s.sword_id, s.quest_stage = 200, 0, None, 4
        s.mail_read, s.day = True, 3
        s.stats.update({'tilled': 3, 'lobak_planted': 3, 'watered': 3, 'lobak_harvested': 3,
                        'earned': 10})
        s.dua_desa_stage = 0
        s.penunjuk_mode = 0
        _pindah(g, 'farm', 20, 10)
        hasil_mode = []
        for _ in range(4):
            tekan(g, 'f8', 3)
            hasil_mode.append((s.penunjuk_mode, g.penunjuk.titik is not None,
                               g.penunjuk_dd.titik is not None))
        harap = [(1, True, False), (2, False, True), (3, False, False), (0, True, True)]
        cek('[F8] memutar mode penunjuk: utama saja, Dua Desa saja, mati, keduanya',
            hasil_mode == harap, f'{hasil_mode}')
    finally:
        s.penunjuk_mode = 0
        (s.mail_read, s.day, st, s.dua_desa_stage, s.gold, s.pickaxe_tier, s.sword_id,
         s.quest_stage) = simpan
        s.stats.clear(); s.stats.update(st)


def uji_tebing(g):
    """Tebing lereng gunung tembus pandang saat menghalangi kamera.

    Permintaan pemilik 3 Nov 2026. Di mulut gua (18,4) tebing dulu menutup
    ~85% layar. Di tiap posisi x sudut, garis kamera -> kepala pemain tidak
    boleh menembus tebing yang masih pejal (alfa model > 0,5)."""
    from ursina import camera
    s, w = g.state, g.world
    s.scene_name = 'mountain'
    langkah(60)
    if not getattr(w, '_tembus', None):
        cek('tebing gunung terdaftar untuk tembus pandang', False, '0 tebing')
        return
    menghalangi, pudar_total = [], 0
    for (x, y) in ((18, 4), (14, 4), (20, 8)):
        for yaw in (0, 90, 180, 270):
            g.player.set_tile_pos(x, y)
            g.camera_yaw = yaw
            langkah(3)
            g._snap_camera_to_player()
            langkah(2)
            c = camera.world_position
            o = (c[0], c[1], c[2])
            p = g.player.world_position
            d = (p[0] - o[0], p[1] + 1.2 - o[1], p[2] - o[2])
            for ent, b in w._tembus:
                if not ent or not w._sinar_kena(o, d, b, 0.96):
                    continue
                a = (ent.model if ent.model is not None else ent).getColorScale()[3]
                if a > 0.5:
                    menghalangi.append(f'({x},{y}) yaw {yaw}')
                    break
                pudar_total += 1
    cek('tebing yang menghalangi kamera memudar (12 posisi x sudut)',
        not menghalangi and pudar_total > 0,
        f'pejal di {menghalangi[:3]}; {pudar_total} tebing pudar')
    s.scene_name = 'farm'
    langkah(40)


def uji_dialog_kilat(g):
    p = g.panels
    p.start_dialog('sari', g.state)
    langkah(3)
    p.tuntaskan_ketik()
    langkah(2)
    i0, m0 = p._dialog_idx, p.mode
    tekan(g, 'f', 3)
    cek('[F] melanjutkan kotak dialog (F = tombol interaksi)',
        m0 == 'dialog' and (p._dialog_idx != i0 or p.mode != 'dialog'),
        f'mode {m0}->{p.mode} idx {i0}->{p._dialog_idx}')
    cek('petunjuk dialog tidak menjanjikan [E]', '[E' not in str(p._dlg_cont.text),
        repr(str(p._dlg_cont.text)))
    for _ in range(12):
        if p.mode != 'dialog':
            break
        p.tuntaskan_ketik()
        tekan(g, 'f', 2)
    if p.mode != 'hud':
        tekan(g, 'escape', 3)
    p.flash_msg('Pesan uji yang cukup panjang untuk alasnya', 2.0)
    langkah(2)
    kb, kt = _kotak(p._flash_bg), _kotak(p._flash_ent)
    cek('pesan kilat beralas selebar teksnya',
        p._flash_bg.enabled and kb and kt and kb[0] <= kt[0] and kb[1] >= kt[1],
        f'alas={kb} teks={kt}')


def main():
    kerja = Path(tempfile.mkdtemp(prefix='probe_tampilan_'))
    try:
        g = boot(kerja / 'save.json')
        if not ke_hud(g):
            cek('mencapai HUD', False, 'sinema/chargen tidak selesai')
        else:
            uji_penunjuk(g)
            uji_tebing(g)
            uji_penunjuk_quest(g)
            uji_penunjuk_dua_desa(g)
            uji_kuburan(g)
            uji_saklar_penunjuk(g)
            uji_dunia(g)
            uji_hud(g)
            uji_panel(g)
            uji_peta()
            uji_inventori(g)
            uji_jeda(g)
            uji_dialog_kilat(g)
            uji_panel_berbaris(g)
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
