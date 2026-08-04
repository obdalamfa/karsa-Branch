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

print("SMOKE BOOT PASS")
os._exit(0)
