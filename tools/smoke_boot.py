"""smoke_boot.py — Boot penuh game offscreen + simulasi alur menu M1.

Memverifikasi tanpa membuka jendela:
  boot → layar judul tampil → navigasi menu → Mulai Baru → intro → tutup intro
  → 30 frame gameplay (tracker tutorial + context prompt jalan).
Exit code 0 = sehat. Pakai: python tools/smoke_boot.py
"""
import sys, os, logging
sys.stdout.reconfigure(line_buffering=True)   # print langsung flush (os._exit di akhir)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from panda3d.core import loadPrcFileData
loadPrcFileData('', 'window-type offscreen')
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'audio-library-name null')

logging.basicConfig(level=logging.WARNING)

# Script ini ada di tools/ — arahkan asset_folder Ursina ke repo root supaya
# font & aset ditemukan persis seperti saat run dari main.py.
from pathlib import Path
from ursina import application
_ROOT = Path(__file__).resolve().parent.parent
application.asset_folder = _ROOT
os.chdir(_ROOT)

from game.app import Game3D

game = Game3D()
app = game.app

def step(n=1):
    for _ in range(n):
        app.taskMgr.step()

# ── Boot: layar judul harus aktif ──
step(5)
assert game.panels.mode == 'menu', f"mode boot = {game.panels.mode!r}, harusnya 'menu'"
print("[OK] Boot -> layar judul tampil")

# ── Navigasi menu: turun, naik, buka kontrol, kembali ──
game.input('s'); step(1)
game.input('w'); step(1)
game.input('3'); step(2)            # halaman kontrol
game.input('escape'); step(1)       # kembali ke menu
assert game.panels.mode == 'menu', "gagal kembali dari halaman kontrol"
print("[OK] Navigasi menu + halaman kontrol")

# ── Mulai Baru → layar buat karakter (chargen) ──
game.input('1'); step(3)
assert game.panels.mode == 'chargen', f"mode = {game.panels.mode!r}, harusnya 'chargen'"
print("[OK] Mulai Baru -> layar buat karakter")

# ── Chargen: pindah ke opsi, ganti nilai, konfirmasi ──
game.input('down arrow'); step(1)
game.input('d'); step(1)            # ganti warna kulit
game.input('enter'); step(3)
assert game.panels.mode == 'intro', f"mode = {game.panels.mode!r}, harusnya 'intro'"
print("[OK] Chargen dikonfirmasi -> kartu intro")

# ── Tutup intro → gameplay ──
game.input('space'); step(3)
assert game.panels.mode not in ('menu', 'intro'), "intro tidak tertutup"
print("[OK] Intro ditutup -> gameplay")

# ── 30 frame gameplay: tracker + context prompt tidak melempar error ──
step(30)
from game.tutorial import tracker_lines
title, stepline, hint = tracker_lines(game.state)
assert title and stepline, "tracker kosong"
print(f"[OK] Tracker: {title} | {stepline}")
prompt = game.state.action_prompt if hasattr(game.state, 'action_prompt') else ''
print(f"[OK] Context prompt: {prompt!r}")

# ── Buka beberapa panel sekali jalan (regresi cepat) ──
for k in ('i', 'j', 'escape'):
    game.input(k); step(2)
print("[OK] Panel inventory/quest buka-tutup")

# ── Majelis Batin (4 suara + skill-check, port dari prototipe three.js) ──
assert game.panels.batin is not None, "panels.batin tidak terpasang"
n0 = len(game.batin.lines)
game.panels.say_batin('akar', 'uji suara batin'); step(1)
assert len(game.batin.lines) > n0, "say_batin tidak menambah log"
print("[OK] say_batin menambah log:", game.batin.lines[-1])

game.input('tab'); step(2)
assert game.panels._batin_open, "panel batin tidak terbuka dgn TAB"
assert game.panels._batin_log.text.strip(), "log batin kosong"
game.input('tab'); step(1)
assert not game.panels._batin_open, "panel batin tidak tertutup"
print("[OK] Toggle Majelis Batin (TAB)")

from game.batin import roll as _roll
r = _roll(game.state, 'akar', 'sepele')
assert 'ok' in r and 'txt' in r, "roll tidak valid"
print("[OK] Skill-check 2d6:", r['txt'])

before = dict(game.state.batin)
game.panels.open_batin_check('UJI', 'Pilih jalanmu.', [
    {'voice': 'sukma', 'label': 'opsi A', 'fn': lambda: None},
    {'voice': 'bara', 'label': 'opsi B', 'fn': lambda: None},
]); step(1)
assert game.panels.mode == 'batin', "mode bukan 'batin' saat check terbuka"
game.input('1'); step(2)
assert game.panels.mode == 'hud', "check tidak menutup setelah memilih"
assert game.state.batin['sukma'] == before['sukma'] + 1, "stat suara tidak naik"
print("[OK] Skill-check modal: pilih -> SUKMA", before['sukma'], '->', game.state.batin['sukma'])

# ── Menu Jeda (pause, M3) ──
game.input('escape'); step(2)
assert game.panels.mode == 'pause', "Esc tidak membuka menu Jeda"
game.input('s'); step(1)
game.input('escape'); step(2)
assert game.panels.mode == 'hud', "menu Jeda tidak menutup dgn Esc"
print("[OK] Menu Jeda (Esc buka/tutup)")

# ── Peti Kirim / shipping bin (Stardew, M4) ──
from game.config import SHIP_BIN_TILE as _BIN
game.state.scene_name = 'farm'
game.state.inventory['lobak'] = 5
game.player.set_tile_pos(_BIN[0], _BIN[1]); step(1)
ok = game.player.interaction_controller._try_shipping_bin(game.panels)
assert ok and game.state.ship_bin.get('lobak', 0) == 5 and game.state.inventory.get('lobak', 0) == 0, "setor ke Peti gagal"
_g0 = game.state.gold
game.player.time_controller.advance_day(game.player); step(2)
assert game.state.gold > _g0 and not game.state.ship_bin, "penjualan Peti saat fajar gagal"
print(f"[OK] Peti Kirim: 5 lobak -> jual saat fajar (+{game.state.gold - _g0}G)")

# ── Tani-mendalam Sakuna (jadwal air, nutrisi, gulma → mutu ★) ──
sc = game.state.scene_name
game.state.soil['90,90,' + sc] = {'tilled': True, 'crop': 'lobak', 'age': 0,
                                  'quality': 3.0, 'nutrients': 3, 'weeds': 0, 'watered': True}
game.state.soil['91,91,' + sc] = {'tilled': True, 'crop': 'lobak', 'age': 0,
                                  'quality': 3.0, 'nutrients': 0, 'weeds': 3, 'watered': False}
for _ in range(3):
    game.state.soil['90,90,' + sc]['watered'] = True     # petani rajin menyiram
    game.player.time_controller.advance_day(game.player); step(2)
gq = game.state.soil['90,90,' + sc]['quality']
bq = game.state.soil['91,91,' + sc]['quality']
ga = game.state.soil['90,90,' + sc]['age']
assert gq > bq, f"mutu petak rawatan ({gq}) harus > telantar ({bq})"
assert ga > 0, "tanaman rawatan tidak tumbuh"
print(f"[OK] Sakuna: mutu rawat {gq:.1f}* vs telantar {bq:.1f}* | umur {ga}")

# ── Ternak produktif (M4): hasil harian → peti → jual, reset tiap fajar ──
_ic = game.player.interaction_controller
game.state.scene_name = 'farm'
game.state.animals_collected = []
game.state.inventory['susu'] = 0
got = _ic._try_collect_animal('sapi_betsy', game.panels)
assert got and game.state.inventory.get('susu', 0) == 1 and 'sapi_betsy' in game.state.animals_collected, "ambil susu gagal"
assert _ic._try_collect_animal('sapi_betsy', game.panels) is False, "harusnya tak bisa ambil 2x/hari"
game.player.set_tile_pos(_BIN[0], _BIN[1]); step(1)
_ic._try_shipping_bin(game.panels)
assert game.state.ship_bin.get('susu', 0) == 1, "susu tak masuk Peti"
_g1 = game.state.gold
game.player.time_controller.advance_day(game.player); step(2)
assert game.state.gold > _g1, "susu tak terjual saat fajar"
assert game.state.animals_collected == [], "ternak tak reset saat fajar"
print(f"[OK] Ternak: susu -> peti -> jual fajar (+{game.state.gold - _g1}G), reset harian OK")

# ── Audit quest 11-stage end-to-end (M4) ──
_qc = game.player.quest_controller
_st = game.state
_st.quest_stage = 0
_st.mail_read = True
_st.stats.update({'lobak_planted': 3, 'watered': 3, 'lobak_harvested': 3,
                  'mobs_killed': 5, 'deepest_level': 10})
_st.gold = 200
_st.pickaxe_tier = 2
_st.sword_id = 'sword_besi'
_st.inventory.update({'tembaga': 5, 'besi': 3})
_st.captured_supernatural = 1
_st.naga_defeated = True
_qc.check_quest_progress()
assert _st.quest_stage == 11, f"quest MACET di tahap {_st.quest_stage}"
assert _st.post_game, "post_game tak diset saat tamat"
print("[OK] Quest 0->11 tamat tanpa macet (audit)")
# Gating: tanpa syarat tahap 0, tak boleh lompat walau sinyal akhir ada
_st.quest_stage = 0
_st.mail_read = False
_qc.check_quest_progress()
assert _st.quest_stage == 0, "tahap 0 lolos tanpa baca surat (gating bocor)"
print("[OK] Quest gating: tahap 0 menahan tanpa syarat")

# ── Jadwal NPC per-jam (M5) — NPC pindah lokasi sesuai waktu ──
_em = game.entities
game.state.time_minutes = 6 * 60          # 06:00
_em._update_npc_schedules()
_sari_pagi = dict(game.state.npc_positions.get('sari', {}))
game.state.time_minutes = 19 * 60         # 19:00
_em._update_npc_schedules()
_sari_malam = game.state.npc_positions.get('sari', {})
assert (_sari_pagi.get('scene'), _sari_pagi.get('sched_x')) != \
       (_sari_malam.get('scene'), _sari_malam.get('sched_x')), "jadwal sari tak berubah by jam"
print(f"[OK] Jadwal NPC by-jam: sari pagi={_sari_pagi.get('scene')} -> malam={_sari_malam.get('scene')}")

# ── Telegraph serangan mob (M5) — wind-up dulu, baru pukulan mendarat ──
from game.mob import Monster
_spec = {'kind': 'tikus_gua', 'hp': 20, 'damage': 5, 'x': 5.0, 'y': 5.0, 'max_hp': 20}
_mob = Monster(game.state, 'uji_mob', _spec)
game.state.invuln_timer_ms = 0
game.state.hp = 100
_hp0 = game.state.hp
_cw = lambda a, b: True
_mob.update_ai(0.016, 5.0, 5.0, _cw)               # pemain dalam jangkauan
assert _mob.windup_ms > 0 and game.state.hp == _hp0, "telegraph tak mulai / kena instan"
for _ in range(80):                                # habiskan wind-up
    _mob.update_ai(0.016, 5.0, 5.0, _cw)
    if game.state.hp < _hp0:
        break
assert game.state.hp < _hp0, "pukulan tak mendarat setelah wind-up"
print(f"[OK] Telegraph mob: wind-up dulu lalu kena (-{_hp0 - game.state.hp} HP)")
# Mengelak saat telegraph: keluar jangkauan sebelum pukulan -> tak kena
game.state.hp = 100; game.state.invuln_timer_ms = 0
_mob2 = Monster(game.state, 'uji_mob2', dict(_spec))
_mob2.update_ai(0.016, 5.0, 5.0, _cw)              # mulai wind-up
for _ in range(80):
    _mob2.update_ai(0.016, 99.0, 99.0, _cw)        # pemain lari jauh
assert game.state.hp == 100, "mengelak saat telegraph tetap kena (telegraph tak adil)"
print("[OK] Telegraph mob: mengelak saat wind-up menghindari pukulan")
try: _mob.disable(); _mob2.disable()
except Exception: pass

# ── Save/Load slot + Pengaturan (M3) ──
from game.state import GameState as _GS
game.state.gold = 777
game.state.char_name = 'UjiSlot'
assert game.state.save(2), "simpan ke slot gagal"
_info = _GS.slot_info(2)
assert _info and _info['gold'] == 777 and _info['name'] == 'UjiSlot', f"slot_info salah: {_info}"
print(f"[OK] Save slot: Slot 2 = {_info['name']} / {_info['gold']}G")
# Navigasi menu Jeda → Simpan → pilih slot lewat input
game.input('escape'); step(1)                  # buka Jeda (root)
assert game.panels.mode == 'pause' and game.panels._pause_view == 'root'
game.input('2'); step(1)                        # masuk view Simpan
assert game.panels._pause_view == 'save', "tak masuk view Simpan"
game.input('1'); step(1)                        # simpan ke Slot 1
assert _GS.slot_info(1) and _GS.slot_info(1)['gold'] == 777, "Slot 1 tak tersimpan via UI"
print("[OK] UI Jeda->Simpan->Slot 1 menulis save")
# Pengaturan: ubah volume master
game.input('escape'); step(1)                   # kembali ke root
game.input('4'); step(1)                        # masuk Pengaturan
assert game.panels._pause_view == 'settings', "tak masuk Pengaturan"
from game.sound import get_master as _gm
_v0 = _gm()
game.input('a'); step(1)                         # volume turun
assert _gm() < _v0 + 1e-6 and _gm() <= _v0, "volume tak turun"
print(f"[OK] Pengaturan: volume {_v0:.1f} -> {_gm():.1f}")
game.input('escape'); step(1); game.input('escape'); step(1)  # tutup
# Muat slot 1 (gold 777) setelah mengubah state
game.state.gold = 5
game._load_slot(1); step(2)
assert game.state.gold == 777, "muat slot tak mengembalikan state"
print(f"[OK] Muat Slot 1 -> gold kembali {game.state.gold}")
# Bersihkan file slot uji
for _s in (1, 2):
    try: os.remove(_GS.slot_path(_s))
    except Exception: pass

# ── Ikon item inventory (M3) — PNG prosedural termuat sbg tekstur ──
_icon_set = ('lobak', 'wortel', 'jamur', 'susu', 'telur', 'wol', 'kayu', 'besi', 'kristal',
             'sword_besi', 'jala', 'obor', 'mithril', 'ikan_legendaris', 'mandrake',
             'firefly', 'buku_paman_arsa', 'surat_paman_arsa_2')
_icon_hits = sum(1 for _it in _icon_set if game.panels._item_icon_tex(_it) is not None)
assert _icon_hits >= len(_icon_set) - 1, f"ikon item tak termuat ({_icon_hits}/{len(_icon_set)})"
print(f"[OK] Ikon item: {_icon_hits}/{len(_icon_set)} PNG termuat sebagai tekstur inventory")

# ── Dressing props obj scene baru (M2): mountain/lake/cemetery ──
# scatter_obj_props menempatkan model di tile lantai kosong jauh dari portal.
from game.scenes import props as _props
import game.entities as _ent
_orig_lmf = _ent.load_model_file
_ent.load_model_file = lambda n: 'cube'          # stub: model selalu "ada"
_props_default = _props.default_prop_builder
_props.default_prop_builder = lambda world, scene: None  # isolasi scatter
class _StubW:
    def __init__(self, scn): self._obj_ents = []; self.scene_obj = scn
    def _create_entity(self, *a, **k): return object()
from game.scenes.mountain import mountain_builder, build_mountain
from game.scenes.lake import lake_builder, build_lake
from game.scenes.cemetery import cemetery_builder, build_cemetery
for _nm, _bld, _build in (('mountain', mountain_builder, build_mountain),
                          ('lake', lake_builder, build_lake),
                          ('cemetery', cemetery_builder, build_cemetery)):
    _w = _StubW(_build())
    _bld(_w)
    assert len(_w._obj_ents) >= 8, f"dressing {_nm} terlalu sedikit ({len(_w._obj_ents)})"
    print(f"[OK] Dressing {_nm}: scatter menempatkan {len(_w._obj_ents)} props")
_ent.load_model_file = _orig_lmf
_props.default_prop_builder = _props_default

# ── S1 Motif Sims: 5 motif + peluruhan + kecelakaan kandung + HUD 5 bar ──
_s = game.state
assert hasattr(_s, 'kandung') and hasattr(_s, 'bersih'), "motif kandung/bersih tak ada"
assert len(game.panels._need_fills) == 5, f"HUD motif = {len(game.panels._need_fills)} bar, harusnya 5"
_s.lapar = _s.sosial = _s.senang = _s.kandung = _s.bersih = 80.0
_s.time_minutes = 8 * 60                            # jauh dari FORCE_SLEEP
game.player.time_controller.tick(10.0, game.player) # 10 dtk real = banyak menit game
assert _s.kandung < 80.0 and _s.bersih < 80.0, "motif baru tak meluruh"
assert _s.kandung < _s.bersih, "kandung harusnya meluruh tercepat"
print(f"[OK] S1 peluruhan: kandung {_s.kandung:.1f} < bersih {_s.bersih:.1f} < 80")
# Kecelakaan: kandung 0 → lega tapi kotor & malu
_s.kandung = 0.001; _s.bersih = 70.0; _s.senang = 50.0
_msg = game.player.time_controller.tick(1.0, game.player)
assert _s.kandung > 30.0 and _s.bersih <= 15.0 and _s.senang < 50.0, "kecelakaan tak berefek benar"
assert _msg and 'mandi' in _msg, f"pesan kecelakaan aneh: {_msg!r}"
print(f"[OK] S1 kecelakaan: kandung->%.0f bersih->%.0f, pesan tampil" % (_s.kandung, _s.bersih))
# Mood kini rata-rata 5 motif
_s.lapar = _s.sosial = _s.senang = 100.0; _s.kandung = 0.0; _s.bersih = 0.0
assert abs(_s.get_mood() - 60.0) < 0.01, f"mood 5-motif salah: {_s.get_mood()}"
print("[OK] S1 mood = rata-rata 5 motif")
# HUD: tiap bar motif mengikuti nilainya + merah saat kritis
game.panels.mode = 'hud'
_s.lapar, _s.sosial, _s.senang, _s.kandung, _s.bersih = 90, 70, 50, 30, 10
game.panels.update(_s, 0.016); step(1)
for _k, _want in (('lapar',90),('sosial',70),('senang',50),('kandung',30),('bersih',10)):
    _fill, _nx, _nw, _ncol = game.panels._need_fills[_k]
    _pct = _fill.scale_x / _nw * 100
    assert abs(_pct - _want) < 1.5, f"bar {_k}: {_pct:.1f}% != {_want}%"
_bfill = game.panels._need_fills['bersih'][0]
assert round(_bfill.color[0]*255) > 150 and round(_bfill.color[1]*255) < 100, "bar kritis tak memerah"
print("[OK] S1 HUD: 5 bar motif sinkron + merah saat kritis")

# ── S2 Objek-beraksi: katalog + iklan + jalan-ke-objek + isi motif bertahap ──
from game.sims_objects import (SIMS_OBJECTS, advertise_score, best_motive,
                               objects_in_scene, find_best_object)
from game.config import WC, SWR, KLK, BD
assert WC in SIMS_OBJECTS and SWR in SIMS_OBJECTS and KLK in SIMS_OBJECTS, "objek Sims baru tak ada di katalog"
# Iklan: objek makin menarik saat motif makin kurang (inti Sims)
_s.kandung = 95.0; _hi = advertise_score(WC, _s)
_s.kandung = 5.0;  _lo = advertise_score(WC, _s)
assert _lo > _hi * 3, f"skor iklan tak naik saat motif kurang ({_hi:.1f} -> {_lo:.1f})"
print(f"[OK] S2 iklan objek: toilet {_hi:.1f} (kandung 95) -> {_lo:.1f} (kandung 5)")
# Motif terendah dipilih benar
_s.lapar = _s.sosial = _s.senang = _s.bersih = 90.0; _s.kandung = 8.0; _s.energy = _s.max_energy
assert best_motive(_s) == 'kandung', f"motif terendah salah: {best_motive(_s)}"
print("[OK] S2 best_motive -> kandung (paling mendesak)")
# Objek terpasang di scene rumah & bisa ditemukan
game.state.scene_name = 'house'
game.world.load_scene('house'); game.entities.load_scene('house'); step(1)
_objs = objects_in_scene(game.world)
_ids = {t for t, _, _ in _objs}
assert WC in _ids and SWR in _ids and KLK in _ids, f"objek baru tak ada di rumah: {_ids}"
print(f"[OK] S2 scan rumah: {len(_objs)} objek Sims (termasuk toilet/pancuran/kulkas)")
_best = find_best_object(game.world, _s, motive='kandung', from_tile=(3, 3))
assert _best and _best[0] == WC, f"find_best_object utk kandung salah: {_best}"
print(f"[OK] S2 find_best_object(kandung) -> toilet di tile ({_best[1]},{_best[2]})")
# Jalankan aksi: isi motif BERTAHAP, selesai tepat di akhir durasi
_ctl = game.player.sims_action
_s.kandung = 10.0
game.player.set_tile_pos(4, 5)          # tepat di samping toilet (4,6)
assert _ctl.start(WC, 4, 6, game.panels), "gagal memulai aksi toilet"
_ctl.tick(0.1, game.panels)             # dekat → langsung fase 'do'
assert _ctl.current and _ctl.current['phase'] == 'do', "tak masuk fase melakukan"
_mid = None
for _ in range(40):
    _ctl.tick(0.1, game.panels)
    if _mid is None and _s.kandung > 30.0:
        _mid = _s.kandung               # bukti pengisian bertahap
    if not _ctl.busy:
        break
assert _mid is not None and _mid < 100.0, "motif tak terisi bertahap (langsung penuh?)"
assert _s.kandung > 90.0, f"kandung tak terisi penuh: {_s.kandung}"
assert not _ctl.busy, "aksi tak selesai setelah durasi"
print(f"[OK] S2 aksi toilet: kandung 10 -> {_s.kandung:.0f} (bertahap, selesai)")
# Batal di tengah tetap memberi sebagian manfaat
_s.bersih = 10.0
game.player.set_tile_pos(5, 5)
_ctl.start(SWR, 5, 6, game.panels); _ctl.tick(0.1, game.panels)
for _ in range(8): _ctl.tick(0.1, game.panels)
_partial = _s.bersih
_ctl.cancel(game.panels)
assert 10.0 < _partial < 95.0, f"pembatalan tak memberi sebagian manfaat: {_partial}"
assert not _ctl.busy, "cancel tak menghentikan aksi"
print(f"[OK] S2 batal di tengah: bersih 10 -> {_partial:.0f} (sebagian, adil)")

# ── S3 Autonomi / free-will: Sim urus motif terendah sendiri ──
# Sim harus BENAR-BENAR senggang: hentikan sisa jalan dari uji S2 di atas
# (autonomi memang sengaja tak membajak Sim yang sedang berjalan).
if getattr(game.player, 'mover', None):
    game.player.mover.stop()
_ctl.cancel(None); _ctl._auto_cd = 0.0
_s.free_will = True
_s.lapar = _s.sosial = _s.senang = _s.bersih = 90.0
_s.energy = _s.max_energy
_s.kandung = 12.0                      # di bawah ambang → harus ditangani
game.player.set_tile_pos(8, 3)
_ctl.tick(0.1, game.panels)
assert _ctl.busy, "autonomi tak memulai aksi walau motif kritis"
assert _ctl.current['auto'] is True, "aksi tak ditandai autonom"
assert _ctl.current['tid'] == WC, f"autonomi pilih objek salah: {_ctl.current['tid']}"
print(f"[OK] S3 autonomi: kandung 12 -> otomatis menuju {_ctl.current['obj']['label']}")
# Motif cukup → Sim TIDAK sibuk sendiri
_ctl.cancel(None); _ctl._auto_cd = 0.0
_s.kandung = 95.0
_ctl.tick(0.1, game.panels)
assert not _ctl.busy, "autonomi jalan padahal semua motif cukup"
print("[OK] S3 autonomi diam saat semua motif cukup")
# Free will OFF → Sim tak berinisiatif
_ctl.cancel(None); _ctl._auto_cd = 0.0
_s.free_will = False; _s.kandung = 8.0
_ctl.tick(0.1, game.panels)
assert not _ctl.busy, "free_will OFF tapi Sim tetap berinisiatif"
print("[OK] S3 free_will OFF menghentikan autonomi")
# Toggle di menu Pengaturan mengubah & tersimpan di state
game.panels._toggle_free_will()
assert _s.free_will is True, "toggle free will tak bekerja"
game.panels._pause_view = 'settings'
assert any('Free Will' in r for r in game.panels._pause_rows()), "baris Free Will tak ada di Pengaturan"
game.panels._pause_view = 'root'
print("[OK] S3 toggle Free Will ada di menu Pengaturan & mengubah state")
# Aksi autonom terbawa ke save (free_will) — kompatibel save lama
assert 'free_will' in game.state.__dict__, "free_will tak ikut ter-serialize"
print("[OK] S3 free_will tersimpan di state (ikut save)")

# ── S4 Mood: motif → emosi → pengaruh kecepatan aksi & sosial ──
from game.sims_mood import (current_mood, mood_label, mood_speed_multiplier,
                            mood_social_bonus)
_ctl.cancel(None)
def _set_motifs(lapar=90, sosial=90, senang=90, kandung=90, bersih=90, en=None):
    _s.lapar, _s.sosial, _s.senang = lapar, sosial, senang
    _s.kandung, _s.bersih = kandung, bersih
    _s.energy = _s.max_energy if en is None else en
# Semua motif tinggi → Gembira
_set_motifs()
assert current_mood(_s) == 'gembira', f"mood salah: {current_mood(_s)}"
assert mood_speed_multiplier(_s) < 1.0 and mood_social_bonus(_s) > 0
print(f"[OK] S4 mood semua tinggi -> {mood_label(_s)} (cepat, sosial +{mood_social_bonus(_s)})")
# Satu motif kritis MENDOMINASI walau rata-rata tinggi
_set_motifs(kandung=5)
assert current_mood(_s) == 'kebelet', f"motif kritis tak mendominasi: {current_mood(_s)}"
print(f"[OK] S4 kandung kritis mendominasi -> {mood_label(_s)}")
_set_motifs(lapar=8)
assert current_mood(_s) == 'lapar', f"lapar kritis tak mendominasi: {current_mood(_s)}"
# Semua sedang-rendah → muram
_set_motifs(20+1, 21, 21, 21, 21)
assert current_mood(_s) in ('muram', 'lesu'), f"mood rendah salah: {current_mood(_s)}"
print(f"[OK] S4 semua motif rendah -> {mood_label(_s)}")
# Mood mengubah DURASI aksi objek (gembira lebih cepat dari loyo)
_set_motifs()                                   # gembira
_ctl.start(WC, 4, 6, None); _dur_baik = _ctl.current['dur']; _ctl.cancel(None)
_set_motifs(21, 21, 21, 21, 21)                 # muram
_ctl.start(WC, 4, 6, None); _dur_muram = _ctl.current['dur']; _ctl.cancel(None)
assert _dur_muram > _dur_baik, f"mood tak memengaruhi durasi ({_dur_baik} vs {_dur_muram})"
print(f"[OK] S4 durasi aksi ikut mood: gembira {_dur_baik:.1f}s < muram {_dur_muram:.1f}s")
# Mood mengubah HASIL interaksi sosial
_ic = game.player.interaction_controller
_set_motifs(); _s.sosial = 50.0
_gain_baik = _ic._social(_s, 10)
_set_motifs(lapar=8); _s.sosial = 50.0
_gain_buruk = _ic._social(_s, 10)
assert _gain_baik > _gain_buruk, f"mood tak memengaruhi sosial ({_gain_baik} vs {_gain_buruk})"
print(f"[OK] S4 hasil sosial ikut mood: gembira +{_gain_baik:.1f} > kelaparan +{_gain_buruk:.1f}")
# Chip mood tampil di HUD
game.panels.mode = 'hud'; _set_motifs(); game.panels.update(_s, 0.016); step(1)
assert 'Gembira' in game.panels._mood_txt.text, f"chip mood HUD: {game.panels._mood_txt.text!r}"
print(f"[OK] S4 chip mood di HUD: {game.panels._mood_txt.text!r}")

# ── S5 Relasi dua-meter: persahabatan + asmara, gate & peluruhan ──
from game.sims_relationship import (friendship, romance, friend_label,
                                    romance_label, add_friendship, add_romance,
                                    can_romance, decay_relationships, summary,
                                    ROMANCE_MIN_FRIENDSHIP)
_npc = 'sari'
_set_motifs()                                   # mood gembira (bonus sosial)
_s.npc_hearts[_npc] = 0.0; _s.npc_romance = {}; _s.npc_last_social = {}
# Persahabatan naik & berlabel
add_friendship(_s, _npc, 1.5)
assert friendship(_s, _npc) > 1.0, "persahabatan tak naik"
print(f"[OK] S5 persahabatan: {friendship(_s,_npc):.1f} ({friend_label(_s,_npc)})")
# Asmara DITOLAK saat belum akrab, dan bikin canggung (persahabatan turun)
_before = friendship(_s, _npc)
_ok, _d, _msg = add_romance(_s, _npc, 1.0)
assert _ok is False and romance(_s, _npc) == 0.0, "rayuan lolos padahal belum akrab"
assert friendship(_s, _npc) < _before, "rayuan prematur tak ada konsekuensi"
print(f"[OK] S5 rayuan prematur ditolak & canggung: {_before:.1f} -> {friendship(_s,_npc):.1f} hati")
# Cukup akrab → rayuan berhasil
_s.npc_hearts[_npc] = 5.0
assert can_romance(_s, _npc), "harusnya boleh merayu di 5 hati"
_ok, _d, _ = add_romance(_s, _npc, 1.0)
assert _ok and romance(_s, _npc) > 0, "rayuan gagal padahal sudah akrab"
print(f"[OK] S5 rayuan berhasil: {romance(_s,_npc):.1f} asmara ({romance_label(_s,_npc)})")
# Mood memengaruhi pertumbuhan relasi
_s.npc_hearts['budi'] = 0.0
_set_motifs(); _g_baik = add_friendship(_s, 'budi', 1.0)
_s.npc_hearts['budi'] = 0.0
_set_motifs(lapar=8); _g_buruk = add_friendship(_s, 'budi', 1.0)
assert _g_baik > _g_buruk, f"mood tak memengaruhi relasi ({_g_baik} vs {_g_buruk})"
print(f"[OK] S5 relasi ikut mood: gembira +{_g_baik:.2f} > kelaparan +{_g_buruk:.2f}")
# Peluruhan: diabaikan berhari-hari → luntur; baru berinteraksi → aman
_s.npc_hearts[_npc] = 6.0; _s.npc_romance[_npc] = 4.0
_s.npc_last_social[_npc] = 1; _s.day = 10          # lama tak bertemu
_f0, _r0 = friendship(_s, _npc), romance(_s, _npc)
decay_relationships(_s)
assert friendship(_s, _npc) < _f0 and romance(_s, _npc) < _r0, "relasi tak luntur"
assert romance(_s,_npc) - (_r0 - 0.25) < 0.01, "laju luntur asmara salah"
print(f"[OK] S5 luntur diabaikan: hati {_f0:.1f}->{friendship(_s,_npc):.2f}, asmara {_r0:.1f}->{romance(_s,_npc):.2f}")
_s.npc_last_social[_npc] = 10                      # baru saja berinteraksi
_f1 = friendship(_s, _npc); decay_relationships(_s)
assert friendship(_s, _npc) == _f1, "relasi luntur padahal baru berinteraksi"
print("[OK] S5 masa tenggang: baru berinteraksi -> tak luntur")
# Aksi pie 'gombal' & 'puji' tersedia dgn gate yang benar
_s.npc_hearts[_npc] = 1.0
_pie = {a[0]: a[2] for a in _ic.build_pie_options(_npc)}
assert 'gombal' in _pie and 'puji' in _pie, f"aksi asmara tak ada di pie: {list(_pie)}"
assert _pie['gombal'] is False, "gombal aktif padahal baru 1 hati"
_s.npc_hearts[_npc] = 5.0
_pie = {a[0]: a[2] for a in _ic.build_pie_options(_npc)}
assert _pie['gombal'] is True, "gombal tak aktif padahal 5 hati"
print("[OK] S5 pie menu: gombal terkunci di 1 hati, terbuka di 5 hati")
# Relasi ikut save
assert 'npc_romance' in game.state.__dict__ and 'npc_last_social' in game.state.__dict__
print("[OK] S5 npc_romance & npc_last_social ikut ter-serialize")

# ── Pose bertahan aksi Sims (animasi): duduk/tidur/mandi/masak/baca ──
_p = game.player
_ctl.cancel(None); _p.set_pose(None)
_neutral_hip = _p._pivot_hip_l.rotation_x
# Duduk: paha & lutut menekuk, badan turun
_p.set_pose('sit'); _p._update_pose(0.1)
assert _p._pivot_hip_l.rotation_x < -40 and _p._pivot_knee_l.rotation_x > 40, "pose duduk tak menekuk"
assert _p._pose_y_off < -0.2, "pose duduk tak menurunkan badan"
print(f"[OK] Pose duduk: paha {_p._pivot_hip_l.rotation_x:.0f}, lutut {_p._pivot_knee_l.rotation_x:.0f}, turun {_p._pose_y_off:.2f}")
# Tidur: badan rebah 90 derajat
_p.set_pose('sleep'); _p._update_pose(0.1)
assert _p.rotation_x == -90, f"pose tidur tak rebah: {_p.rotation_x}"
print(f"[OK] Pose tidur: badan rebah {_p.rotation_x} derajat")
# Mandi: kedua tangan terangkat tinggi & bergoyang (beda antar frame)
_p.set_pose('shower'); _p._update_pose(0.1)
_sh1 = _p._pivot_shoulder_l.rotation_x
assert _sh1 < -100, f"pose mandi tak mengangkat tangan: {_sh1}"
_p._update_pose(0.35)
assert abs(_p._pivot_shoulder_l.rotation_x - _sh1) > 0.5, "pose mandi tak bergerak (statis)"
print(f"[OK] Pose mandi: tangan {_sh1:.0f} & bergoyang antar-frame")
# Masak: tangan mengaduk (berubah tiap frame)
_p.set_pose('cook'); _p._update_pose(0.1); _ck1 = _p._pivot_shoulder_r.rotation_x
_p._update_pose(0.25)
assert abs(_p._pivot_shoulder_r.rotation_x - _ck1) > 1.0, "pose masak tak mengaduk"
print("[OK] Pose masak: tangan mengaduk (bergerak)")
# Lepas pose -> rig kembali netral
_p.set_pose(None)
assert _p._pivot_hip_l.rotation_x == _neutral_hip and _p.rotation_x == 0 and _p._pose_y_off == 0.0, "pose tak dilepas bersih"
print("[OK] Pose dilepas -> rig netral kembali")
# Aksi objek benar-benar MEMASANG pose yang sesuai, lalu melepasnya saat selesai
game.state.scene_name = 'house'
game.world.load_scene('house'); game.entities.load_scene('house'); step(1)
if getattr(_p, 'mover', None): _p.mover.stop()
_s.kandung = 10.0
_p.set_tile_pos(4, 5)
_ctl.start(WC, 4, 6, None); _ctl.tick(0.1, None)
assert getattr(_p, '_pose', None) == 'sit', f"aksi toilet tak memasang pose duduk: {getattr(_p,'_pose',None)}"
print("[OK] Aksi Toilet memasang pose 'sit'")
for _ in range(60):
    _ctl.tick(0.1, None)
    if not _ctl.busy: break
assert getattr(_p, '_pose', None) is None, "pose tak dilepas setelah aksi selesai"
print("[OK] Pose dilepas otomatis saat aksi selesai")

# ── Animasi mati pemain (dulu TAK PERNAH jalan: AnimStateMachine dead code) ──
_p.set_pose(None)
game.player.combat_controller._on_player_death(None)
assert getattr(_p, '_pose', None) == 'death', "animasi tumbang tak terpasang saat mati"
_p._update_pose(0.1)
assert _p.rotation_x < -80, f"pose tumbang tak rebah: {_p.rotation_x}"
print(f"[OK] Anim mati: pose 'death' terpasang, badan rebah {_p.rotation_x:.0f} derajat")
game.player.combat_controller._respawn(None)
assert getattr(_p, '_pose', None) is None and _p.rotation_x == 0, "pose tumbang tak dilepas saat respawn"
print("[OK] Anim mati: pose dilepas saat respawn (tak rebah selamanya)")

# ── Pose NPC per-aktivitas (dulu cuma berdiri; tidur pun langsung ditegakkan) ──
from game.entities import NPC_ACTIVITY_POSE
_acts_sched = {e[4] for v in __import__('game.data', fromlist=['SCHEDULES']).SCHEDULES.values() for e in v}
_covered = _acts_sched & set(NPC_ACTIVITY_POSE)
assert len(_covered) >= 25, f"pose aktivitas terlalu sedikit: {len(_covered)}"
print(f"[OK] Pose NPC: {len(_covered)}/{len(_acts_sched)} aktivitas jadwal punya pose khas")
assert NPC_ACTIVITY_POSE['forging'][0] > 15, "menempa harusnya membungkuk jelas"
assert NPC_ACTIVITY_POSE['hovering'][1] > 0.3, "makhluk melayang harusnya terangkat"
assert NPC_ACTIVITY_POSE['meditating'][2] < 0.01, "meditasi harusnya nyaris diam"
print("[OK] Pose NPC khas: menempa membungkuk, hantu melayang, meditasi diam")
# NPC tidur benar-benar rebah & tetap rebah (bug lama: langsung ditegakkan)
game.state.scene_name = 'town'
game.world.load_scene('town'); game.entities.load_scene('town'); step(1)
_slp = None
for _aid, _a in game.entities.actors.items():
    if hasattr(_a, 'activity') and not getattr(_a, '_va', None):
        _a.activity = 'sleeping'
        _a.target_x, _a.target_y = _a.logical_x, _a.logical_y   # diam
        _slp = _a; break
if _slp is not None:
    game.entities.update(0.1); game.entities.update(0.1)
    assert _slp.rotation_x == -90, f"NPC tidur tak rebah: {_slp.rotation_x}"
    print(f"[OK] NPC tidur rebah & bertahan ({_slp.rotation_x} derajat)")
    _slp.activity = 'forging'
    game.entities.update(0.1)
    assert _slp.rotation_x != -90, "NPC bangun tapi masih rebah"
    print(f"[OK] NPC bangun -> pose kerja ({_slp.rotation_x:.0f} derajat, tak rebah lagi)")

# ── Walk cycle 4-frame (M5): kontak → passing → kontak → passing ──
from game.entities import _setup_pose_swap as _sps, load_model_file as _lmf
class _Dummy:  # aktor minimal utk menguji pemilihan pose
    pass
_d = _Dummy(); _sps(_d, 'npc_arya')
_names = getattr(_d, '_pose_names', ())
assert len(_names) == 5, f"pose swap bukan 4-frame: {_names}"
assert _names[1].endswith('_walk1') and _names[2].endswith('_walk3') \
   and _names[3].endswith('_walk2') and _names[4].endswith('_walk4'), f"urutan siklus salah: {_names}"
print(f"[OK] Walk 4-frame: urutan {[n.split('_')[-1] for n in _names]}")
# Aset passing benar-benar ada & beda dari kontak
assert _lmf('npc_arya_walk3') and _lmf('npc_arya_walk4'), "aset passing tak termuat"
def _vs(p):
    return [tuple(map(float, l.split()[1:4])) for l in open(p, errors='ignore') if l.startswith('v ')]
_bv = _vs('assets/models/npc_arya.obj')
_w1 = _vs('assets/models/npc_arya_walk1.obj'); _w3 = _vs('assets/models/npc_arya_walk3.obj')
_ys = [v[1] for v in _bv]; _H = max(_ys) - min(_ys); _top = min(_ys) + 0.42 * _H
_leg1 = max(abs(_w1[i][2] - _bv[i][2]) for i, v in enumerate(_bv) if v[1] < _top)
_leg3 = max(abs(_w3[i][2] - _bv[i][2]) for i, v in enumerate(_bv) if v[1] < _top)
_body3 = max(_w3[i][1] - _bv[i][1] for i, v in enumerate(_bv) if v[1] >= _top)
assert _leg3 < _leg1, "passing harusnya kaki lebih rapat dari kontak"
assert _body3 > 0.02 * _H, "passing harusnya badan terangkat"
print(f"[OK] Walk 4-frame pose: kontak kaki {_leg1:.2f} > passing {_leg3:.2f}, badan naik {_body3:.3f}")
# Siklus benar-benar berputar melewati SEMUA frame saat berjalan
_d.is_moving = True; _d._walk_t = 0.0; _d._pose_cur = -1
_seen = set()
for _k in range(40):
    _d._walk_t = _k * 0.55
    _seen.add(1 + (int(_d._walk_t * 0.5) % (len(_names) - 1)))
assert _seen == {1, 2, 3, 4}, f"siklus tak melewati semua frame: {sorted(_seen)}"
print("[OK] Walk 4-frame: siklus melewati keempat frame (tak tersendat)")
# Model tanpa aset passing tetap jalan (turun ke 2-frame)
_d2 = _Dummy(); _sps(_d2, 'npc_kru_kuro')
_n2 = getattr(_d2, '_pose_names', ())
assert len(_n2) in (3, 5), f"fallback pose swap rusak: {_n2}"
print(f"[OK] Walk: model lain dapat {len(_n2)-1} frame jalan (fallback aman)")

# -- S6 Skill & Karier --
from game.sims_career import (SKILLS, CAREERS, add_skill_xp, skill_level, xp_to_next,
                              join_career, work_shift, can_work_now, promotion_status,
                              try_promote, reset_daily, skill_summary, career_info)
_s.skills = {}; _s.career = ''; _s.career_level = 0; _s.work_days = 0; _s.worked_today = False
# Skill naik dgn MELAKUKAN, kurva makin berat
_lv, _up = add_skill_xp(_s, 'bertani', xp_to_next(0))
assert _lv == 1 and _up, f"skill tak naik: lv={_lv}"
assert xp_to_next(1) > xp_to_next(0), "kurva XP tak menanjak"
print(f"[OK] S6 skill: Bertani -> lv{_lv}; XP lv0->1={xp_to_next(0):.0f} < lv3->4={xp_to_next(3):.0f}")
# Pakai alat melatih skill
_before = skill_level(_s, 'kebugaran')
for _ in range(30):
    _ic._tool_skill_xp('Pickaxe', None)
assert skill_level(_s, 'kebugaran') > _before, "alat tak melatih skill"
print(f"[OK] S6 alat melatih skill: Kebugaran lv{skill_level(_s,'kebugaran')} dari menambang")
# Lamar kerja
assert join_career(_s, 'tani'), "gagal melamar kerja"
_c, _r = career_info(_s)
assert _c and _r[0] == 'Buruh Panen', f"pangkat awal salah: {_r}"
print(f"[OK] S6 karier: diterima sbg {_r[0]} ({_c['label']}), gaji {_r[1]}G")
# Gate: salah tempat / salah jam / sudah kerja
_s.scene_name = 'town'; _s.time_minutes = 10*60
_ok, _why = can_work_now(_s); assert not _ok and 'farm' in _why, f"gate lokasi bocor: {_why}"
_s.scene_name = 'farm'; _s.time_minutes = 3*60
_ok, _why = can_work_now(_s); assert not _ok and 'Jam kerja' in _why, f"gate jam bocor: {_why}"
print("[OK] S6 gate kerja: salah lokasi & di luar jam ditolak dgn alasan jelas")
# Shift kerja: dapat gaji, lelah, skill naik, sekali sehari
_s.time_minutes = 10*60; _s.gold = 0; _s.energy = _s.max_energy
_set_motifs()   # mood gembira -> kinerja tinggi
_res = work_shift(_s)
assert _res and _s.gold == _res['pay'] and _res['pay'] > 45, f"gaji aneh: {_res}"
assert _s.energy < _s.max_energy, "kerja tak melelahkan"
print(f"[OK] S6 shift: +{_res['pay']}G sbg {_res['rank']} (kinerja {int(_res['perf']*100)}%), energi terkuras")
assert work_shift(_s) is None, "bisa kerja dua kali sehari"
print("[OK] S6 shift: hanya sekali per hari")
# Mood buruk -> gaji lebih kecil
_s.worked_today = False; _s.gold = 0; _set_motifs(lapar=8)
_res2 = work_shift(_s)
assert _res2['pay'] < _res['pay'], f"mood tak memengaruhi gaji ({_res2['pay']} vs {_res['pay']})"
print(f"[OK] S6 gaji ikut mood: gembira {_res['pay']}G > kelaparan {_res2['pay']}G")
# Promosi butuh skill DAN hari kerja
_s.skills['bertani'] = {'lv': 0, 'xp': 0.0}; _s.work_days = 99
assert try_promote(_s) is None, "naik pangkat tanpa skill cukup"
_s.skills['bertani'] = {'lv': 5, 'xp': 0.0}; _s.work_days = 0
assert try_promote(_s) is None, "naik pangkat tanpa hari kerja cukup"
_s.work_days = 5
_new = try_promote(_s)
assert _new == 'Petani Terampil', f"promosi salah: {_new}"
print(f"[OK] S6 promosi: butuh skill DAN hari kerja -> naik jadi {_new}")
# Shift harian reset saat hari baru
_s.worked_today = True; reset_daily(_s)
assert _s.worked_today is False, "shift tak reset"
print("[OK] S6 shift reset tiap hari baru")
# Ikut save
for _f in ('skills', 'career', 'career_level', 'work_days', 'worked_today'):
    assert _f in game.state.__dict__, f"{_f} tak ter-serialize"
print("[OK] S6 skill & karier ikut save")

# -- S7 Bangun/Beli --
from game.sims_build import (catalog, place, sell, can_place, apply_placed,
                             BUY_PRICES, sell_value)
from game.config import WC as _WC, FL as _FL
_s.placed_objects = {}
game.state.scene_name = 'house'
game.world.load_scene('house'); game.entities.load_scene('house'); step(1)
_cat = catalog()
assert len(_cat) >= 8 and _cat[0][3] <= _cat[-1][3], "katalog kosong/tak urut harga"
print(f"[OK] S7 katalog: {len(_cat)} objek, {_cat[0][1]} {_cat[0][3]}G .. {_cat[-1][1]} {_cat[-1][3]}G")
# Cari petak kosong yang bisa dipijak
_sc = game.world.scene_obj
_spot = None
for _ty in range(1, _sc.h-1):
    for _tx in range(1, _sc.w-1):
        ok, _ = can_place(_s, game.world, _tx, _ty)
        if ok: _spot = (_tx, _ty); break
    if _spot: break
assert _spot, "tak ada petak kosong di rumah"
# Uang kurang -> ditolak
_s.gold = 0
_ok, _msg = place(_s, game.world, _WC, *_spot)
assert not _ok and 'kurang' in _msg.lower(), f"beli tanpa uang lolos: {_msg}"
print("[OK] S7 gate: uang kurang ditolak")
# Beli & pasang
_s.gold = 1000; _g0 = _s.gold
_ok, _msg = place(_s, game.world, _WC, *_spot)
assert _ok, f"gagal memasang: {_msg}"
assert _s.gold == _g0 - BUY_PRICES[_WC], "uang tak terpotong"
assert _sc.tiles[_spot[1]][_spot[0]] == _WC, "tile tak berubah"
print(f"[OK] S7 beli & pasang Toilet di {_spot} (-{BUY_PRICES[_WC]}G)")
# Petak terisi -> tak bisa ditimpa
_ok2, _msg2 = place(_s, game.world, _WC, *_spot)
assert not _ok2 and 'terisi' in _msg2.lower(), f"petak terisi bisa ditimpa: {_msg2}"
print("[OK] S7 gate: petak terisi tak bisa ditimpa")
# Objek yang dibeli BERFUNGSI (masuk katalog motif S2)
from game.sims_objects import objects_in_scene as _ois
assert any(t == _WC and (x, y) == _spot for t, x, y in _ois(game.world)), "objek beli tak terdeteksi sistem motif"
print("[OK] S7 objek beli langsung berfungsi utk motif")
# BERTAHAN saat scene dimuat ulang (inti: SCENES global)
_sc.tiles[_spot[1]][_spot[0]] = _FL          # simulasi template ter-reset
game.world.load_scene('house')
assert game.world.scene_obj.tiles[_spot[1]][_spot[0]] == _WC, "objek beli HILANG saat scene dimuat ulang"
print("[OK] S7 objek bertahan saat scene dimuat ulang (overlay placed_objects)")
# Jual: dapat separuh, petak kembali kosong
_g1 = _s.gold
_ok3, _msg3 = sell(_s, game.world, *_spot)
assert _ok3 and _s.gold == _g1 + sell_value(_WC), f"refund salah: {_msg3}"
assert game.world.scene_obj.tiles[_spot[1]][_spot[0]] != _WC, "petak tak kembali kosong"
print(f"[OK] S7 jual: +{sell_value(_WC)}G (separuh harga), petak kosong lagi")
# Tak bisa menjual barang bawaan scene
_ok4, _msg4 = sell(_s, game.world, 1, 1)
assert not _ok4, "barang bawaan scene bisa dijual"
print("[OK] S7 gate: barang bawaan scene tak bisa dijual")
# Mode UI: tombol L membuka, Esc menutup
game.panels.mode = 'hud'
game.input('l'); step(1)
assert game.panels.mode == 'buy', "tombol L tak membuka mode Bangun/Beli"
game.input('escape'); step(1)
assert game.panels.mode == 'hud', "Esc tak menutup mode Bangun/Beli"
print("[OK] S7 mode UI: [L] buka, [Esc] tutup")
assert 'placed_objects' in game.state.__dict__, "placed_objects tak ter-serialize"
print("[OK] S7 placed_objects ikut save")

# -- S8 Rumah tangga & Simoleon --
from game.sims_household import (members, household_size, can_move_in, move_in,
                                 move_out, bill_amount, daily_contribution,
                                 tick_day, object_count, summary as _hhsum,
                                 MOVE_IN_MIN_FRIENDSHIP, MAX_HOUSEHOLD,
                                 BILL_INTERVAL_DAYS)
_s.household = []; _s.bill_days = 0; _s.unpaid_bills = 0
_s.npc_hearts = {}; _s.placed_objects = {}
assert household_size(_s) == 1, "rumah tangga awal harusnya sendiri"
# Gate: belum cukup dekat
_s.npc_hearts['sari'] = 2.0
_ok, _why = can_move_in(_s, 'sari')
assert not _ok and 'dekat' in _why.lower(), f"gate kedekatan bocor: {_why}"
print(f"[OK] S8 gate: 2.0 hati ditolak (butuh {MOVE_IN_MIN_FRIENDSHIP:.0f})")
# Cukup dekat -> pindah
_s.npc_hearts['sari'] = 7.0
_ok, _msg = move_in(_s, 'sari')
assert _ok and household_size(_s) == 2, f"gagal pindah: {_msg}"
print(f"[OK] S8 pindah: rumah tangga {household_size(_s)} orang")
# Tagihan naik seiring anggota & objek
_b1 = bill_amount(_s)
_s.placed_objects = {'house': {'1,1': 63, '2,2': 64, '3,3': 65}}
_b2 = bill_amount(_s)
assert _b2 > _b1 and object_count(_s) == 3, f"tagihan tak ikut objek ({_b1}->{_b2})"
print(f"[OK] S8 tagihan: {_b1}G -> {_b2}G setelah beli 3 objek (rumah mewah = mahal)")
# Setoran harian anggota
_s.gold = 0; _s.bill_days = 0
_res = tick_day(_s)
assert _res and _res['contrib'] == daily_contribution(_s) and _s.gold == _res['contrib']
print(f"[OK] S8 setoran harian anggota: +{_res['contrib']}G")
# Tagihan jatuh tempo tiap N hari & benar-benar memotong
_s.gold = 5000; _s.bill_days = BILL_INTERVAL_DAYS - 1
_g0 = _s.gold
_res = tick_day(_s)
assert _res['bill'] > 0 and _s.gold == _g0 + _res['contrib'] - _res['bill'], "tagihan tak terpotong"
assert _s.bill_days == 0, "hitungan tagihan tak reset"
print(f"[OK] S8 tagihan jatuh tempo tiap {BILL_INTERVAL_DAYS} hari: -{_res['bill']}G")
# Tak mampu bayar -> jadi utang, gold tak minus
_s.gold = 10; _s.bill_days = BILL_INTERVAL_DAYS - 1; _s.unpaid_bills = 0
_res = tick_day(_s)
assert _res['unpaid'] and _s.gold == 0 and _s.unpaid_bills > 0, f"utang tak tercatat: {_res}"
print(f"[OK] S8 tak mampu bayar -> utang {_s.unpaid_bills}G, gold tak minus")
# Batas jumlah anggota
for _i, _n in enumerate(('budi', 'maya', 'raka')):
    _s.npc_hearts[_n] = 9.0; move_in(_s, _n)
assert household_size(_s) <= MAX_HOUSEHOLD, "melebihi batas anggota"
_ok, _why = can_move_in(_s, 'joko')
assert not _ok and 'penuh' in _why.lower(), f"batas rumah tak berlaku: {_why}"
print(f"[OK] S8 batas rumah tangga {MAX_HOUSEHOLD} orang ditegakkan")
# Pindah keluar
_ok, _msg = move_out(_s, 'sari')
assert _ok and 'sari' not in members(_s), "gagal pindah keluar"
print(f"[OK] S8 pindah keluar: {household_size(_s)} orang tersisa")
for _f in ('household', 'bill_days', 'unpaid_bills'):
    assert _f in game.state.__dict__, f"{_f} tak ter-serialize"
print("[OK] S8 rumah tangga ikut save")

print("SMOKE BOOT PASS")
os._exit(0)
