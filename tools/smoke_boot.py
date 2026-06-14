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

print("SMOKE BOOT PASS")
os._exit(0)
