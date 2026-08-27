"""
vitaboy_npc.py — Pabrik tunggal avatar manusia, plus tabel outfit per-orang.

KENAPA SEMUA LEWAT SINI
=======================
Sebelumnya `entities.py` dan `player.py` masing-masing memanggil
`VitaboyAvatar(...)` langsung, dengan try/except sendiri-sendiri dan tabel
outfit sendiri-sendiri. Akibatnya: dua tabel outfit yang tumpang tindih dan
tidak pernah diadu, dan tidak ada satu tempat pun untuk mengganti backend
skinning. Sekarang satu pintu: `build_vitaboy_avatar()`.

DUA BACKEND, URUTANNYA DITENTUKAN OLEH PENGUKURAN
=================================================
1. `vitaboy_baked.NativeAvatar` — Character Panda3D, skinning + interpolasi
   keyframe di C++.
2. `vitaboy.VitaboyAvatar` — skinning di Python, menulis ulang vertex buffer
   tiap frame.

Diukur di `_bench/probes/probe_native_wire.py` (8 avatar, 800x450, pandagl):

    frame kosong (tanpa avatar)      9,34 ms
    8 NativeAvatar                  11,64 ms  ->  0,288 ms per avatar
    8 VitaboyAvatar                 60,43 ms  ->  6,387 ms per avatar

**22x lebih murah per frame.** Dan setelah AnimBundle-nya panas, membangunnya
juga lebih cepat (`_bench/probes/probe_native_build.py`): 15-25 ms per avatar
lawan 76-90 ms. Satu-satunya ongkos tambahan adalah bake AnimBundle sekali per
proses, ~2,6 detik, yang jatuh di `load_scene` pertama yang berisi manusia.

Jalur Python TIDAK dibuang. Ia tetap jadi jaring: kalau `Character` Panda3D
gagal dibangun di suatu mesin, avatar tetap muncul, cuma lebih mahal.

GAGAL-LUNAK
===========
Tanpa install TSO, kedua jalur mengembalikan None dan pemanggil turun ke mesh
prosedural. Game harus tetap bisa dibuka dan berjalan penuh kecepatan di mesin
tanpa aset TSO — itu syarat dari BRIEF bagian 11, dan diuji oleh
`_bench/probes/probe_no_tso.py`.

API:
    from .vitaboy_npc import build_vitaboy_human_npc, build_vitaboy_avatar
    av = build_vitaboy_human_npc(actor_entity, 'sari', scale=0.32)
    av = build_vitaboy_avatar(player_entity, apr_list, scale=0.32)
    av.set_animation('a2o-walking-loop'); av.update(dt)
"""
from __future__ import annotations

import logging
from typing import List, Optional

from ursina import Entity, color

# ─── OUTFIT PER-ORANG ────────────────────────────────────────────────────────
# Gabungan dua tabel yang dulu terpisah: `NPC_APPEARANCES` di entities.py (10
# orang, yang benar-benar dipakai) dan `NPC_OUTFIT` di sini (12 orang, sebagian
# besar seragam). Yang dari entities.py menang kalau bentrok — outfitnya lebih
# beragam dan sudah terbukti tampil. Sisanya menambah orang yang tadinya jatuh
# ke mesh 'humanoid' generik.
#
# Ke-24 nama .apr di bawah sudah diverifikasi resolve ke registry TSO
# (`_bench/probes/probe_apr_valid.py`: 24 OK, 0 GAGAL). Nama yang salah gagal
# DIAM-DIAM — NPC-nya jatuh ke mesh generik tanpa pesan — jadi jangan tambah
# baris di sini tanpa menjalankan probe itu lagi.
NPC_OUTFIT = {
    # ── dari entities.py: beragam, sudah terpakai ──
    'arya':       ['mabd000_sw__default.apr', 'mahd001_romeo.apr'],
    'sari':       ['fabd002_mom01.apr', 'fahd001_sharon.apr', 'fahl001_sharon.apr'],
    'raka':       ['mabd000_sl__teepjs.apr', 'mahd001_ross.apr'],
    'maya':       ['fabd001_slacker.apr', 'fahd001_shannon01.apr', 'fahl001_shannon01.apr'],
    'mbok_jum':   ['fabd002_gma1.apr', 'fahd001_alt.apr', 'fahl001_alt.apr'],
    'budi':       ['mabd000_leathers.apr', 'mahd000_proxy.apr'],
    'jaka_ronda': ['mabd000_robin.apr', 'mahd001_robin.apr'],
    'kapten_kuro': ['mabd000_leathers3.apr', 'mahd002_asian.apr'],
    'cici':       ['fabd001_summer01.apr'],
    'bowo':       ['mabd000_sl__teepjs2.apr'],
    # ── tambahan: orang yang tadinya tidak punya wajah sendiri ──
    'ningsih':    ['fabd000_sl__defaultpjs.apr', 'fahd001_alt.apr', 'fahl902_spikeyhair.apr'],
    'joko':       ['mabd000_sl__teepjs.apr', 'mahd000_proxy.apr'],
    'pak_guru':   ['mabd000_leathers3.apr', 'mahd001_ross.apr'],
}

# Dipakai kalau npc_id tidak ada di tabel. Bukan None: lebih baik seorang warga
# memakai baju standar TSO daripada jadi balok 'humanoid'.
DEFAULT_OUTFIT = ['mabd000_leathers.apr', 'mahd000_proxy.apr']

DEFAULT_IDLE_ANIM = 'a2a-talk-idle-loop'

# Backend yang dipakai terakhir kali — untuk laporan dan probe, bukan logika.
_last_backend: Optional[str] = None


def backend_terakhir() -> Optional[str]:
    """'native' | 'python' | None. Diagnostik saja."""
    return _last_backend


def resolve_outfit(npc_id: str, default: bool = True) -> Optional[List[str]]:
    """Daftar .apr untuk satu orang. None kalau tidak dikenal dan default=False."""
    o = NPC_OUTFIT.get(npc_id)
    if o is not None:
        return list(o)
    return list(DEFAULT_OUTFIT) if default else None


def build_vitaboy_avatar(parent: Entity, apr_list: List[str],
                         scale: float = 0.30, tint=color.white,
                         idle_anim: str = DEFAULT_IDLE_ANIM):
    """Bangun satu avatar Vitaboy. Return avatar atau None.

    Coba jalur native (C++) dulu, lalu jalur Python. Keduanya punya API yang
    sama (`set_animation`, `update`, `speed`, `root_entity`, `parts`) sehingga
    pemanggil tidak perlu tahu yang mana yang dapat.
    """
    global _last_backend
    apr_list = [x for x in (apr_list or []) if x]
    if not apr_list:
        return None

    # ── 1. Native (Character Panda3D) ──
    try:
        from .vitaboy_baked import build_native_avatar, native_available
        if native_available():
            av = build_native_avatar(parent, apr_list, scale=scale, tint=tint)
            if av is not None:
                try:
                    av.set_animation(idle_anim)
                except Exception:
                    pass
                _last_backend = 'native'
                return av
    except Exception as e:
        # Jangan biarkan satu pun jalur ini menjatuhkan load_scene.
        logging.warning(f"Jalur avatar native tidak terpakai: {e}")

    # ── 2. Python (VitaboyAvatar) ──
    try:
        from .vitaboy import VitaboyAvatar
        av = VitaboyAvatar(parent, apr_list, scale=scale, tint=tint)
    except Exception as e:
        logging.warning(f"VitaboyAvatar gagal ({e}); tidak ada avatar TSO.")
        _last_backend = None
        return None
    try:
        av.set_animation(idle_anim)
    except Exception:
        pass
    _last_backend = 'python'
    return av


def build_vitaboy_human_npc(parent: Entity, npc_id: str,
                            tint=color.white, scale: float = 0.30,
                            apr_list: Optional[List[str]] = None,
                            use_default: bool = True):
    """Bangun NPC manusia dengan outfit khas orang itu. Return avatar atau None.

    `apr_list` boleh dipaksa dari luar; kalau None, diambil dari NPC_OUTFIT.
    """
    if apr_list is None:
        apr_list = resolve_outfit(npc_id, default=use_default)
    if not apr_list:
        return None
    return build_vitaboy_avatar(parent, apr_list, scale=scale, tint=tint)


# Nama lama, dipertahankan supaya kode/probe yang sudah ada tidak putus.
def _resolve_outfit_apr_list(npc_id: str) -> List[str]:
    return resolve_outfit(npc_id) or []
