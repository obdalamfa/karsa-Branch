"""npc_brain.py — Lapisan AI tambahan untuk NPC Lembah Karsa 3D.

Menggabungkan:
  - BehaviorVM (motif + antrian aksi, adaptasi SimAntics FreeSO)
  - PathGrid   (A* tile-based, adaptasi VMRectRouter FreeSO)

Tidak menggantikan sistem pergerakan NPC berbasis schedule yang sudah ada
di EntitiesManager. Lapisan ini menambah motif (hunger, energy, social, ...)
yang berubah seiring waktu, dan mem-publish animasi hint yang bisa dibaca
oleh sistem visual jika diperlukan.

Pemakaian dari EntitiesManager:
    from .npc_brain import NPCBrains
    self.brains = NPCBrains(self.state)
    # tiap frame:
    self.brains.tick(dt)
"""
from __future__ import annotations
import random
from typing import Dict, Optional

from .behavior_vm import BehaviorVM, BehaviorEntity
from .pathfinder import PathGrid
from .data import HUMAN_NPCS, all_npcs
from .scenes import SCENES
from .config import WALKABLE
from .motives import Motives, choose_action
from .objects import autonomy_candidates


# Decay motif per detik (kasar — 100 → 0 dalam ~16 menit real-time)
_MOTIVE_DECAY = {
    "hunger":  0.10,
    "energy":  0.06,
    "social":  0.08,
    "fun":     0.05,
    "hygiene": 0.04,
}


# ─── JEMBATAN DUA MODEL MOTIF ──────────────────────────────────────────────
# Otak NPC (BehaviorEntity.motives) memakai lima kunci INGGRIS berskala 0..100;
# mesin pemain (Motives) memakai delapan motif INDONESIA berskala -100..100.
# Iklan perabot di objects.py ditulis untuk mesin pemain, jadi `choose_action`
# tidak bisa diberi dict otak mentah-mentah -- itulah sebabnya dua fungsi ini
# selama ini tidak punya pemanggil.
#
# Lima motif ini punya padanan satu-satu (arah sama: makin rendah makin butuh).
# Nyaman/kandung/ruang TIDAK dimodelkan otak NPC, dan dibiarkan pada default
# netral Motives -- memalsukan angkanya akan membuat NPC mengejar kursi dan
# kamar mandi yang sebenarnya tidak ia rasakan.
_MOTIVE_BRIDGE = {
    "hunger":  "lapar",
    "energy":  "energi",
    "social":  "sosial",
    "fun":     "senang",
    "hygiene": "higiene",
}

# Ambang "mendesak" untuk otonomi. Satu-satunya sumber kebenaran untuk "kapan
# NPC dianggap butuh" -- dipakai `motive_urgent` di pemilihan perabot.
URGENT_THRESHOLD = {
    "hunger":  35.0,
    "energy":  25.0,
    "social":  30.0,
}

# Kebalikan _MOTIVE_BRIDGE: nama motif mesin pemain → kunci otak NPC. Dipakai
# `selesaikan_otonom` untuk menerapkan janji iklan kembali ke otak.
_MOTIVE_BRIDGE_REVERSE = {v: k for k, v in _MOTIVE_BRIDGE.items()}


def _motif_dari_otak(ent: BehaviorEntity) -> Motives:
    """Bangun `Motives` (mesin pemain) dari `BehaviorEntity.motives` (otak NPC)."""
    mv = Motives()
    for key_otak, nama in _MOTIVE_BRIDGE.items():
        setattr(mv, nama, float(ent.get_motive(key_otak)))
    return mv


class NPCBrains:
    """Manajer otak NPC: satu BehaviorEntity per NPC manusia."""

    def __init__(self, state, grid_w: int = 32, grid_h: int = 32):
        self.state = state
        self.vm = BehaviorVM()
        self.grid = PathGrid(grid_w, grid_h, tile_size=1.0)
        self._brains: Dict[str, BehaviorEntity] = {}
        self._anim_hint: Dict[str, str] = {}
        self._grid_scene: Optional[str] = None

        for npc_id in HUMAN_NPCS.keys():
            ent = BehaviorEntity(npc_id, motives={
                "hunger":  80.0, "energy": 80.0, "social": 70.0,
                "fun":     60.0, "hygiene": 75.0,
            })
            ent.on_animation_change(lambda anim, _id=npc_id: self._on_anim(_id, anim))
            self.vm.add_entity(ent)
            self._brains[npc_id] = ent

    def _on_anim(self, npc_id: str, anim_name: str):
        self._anim_hint[npc_id] = anim_name

    # ─── PUBLIC ──────────────────────────────────────────
    def tick(self, dt: float):
        """Meluruhkan motif tiap NPC.

        Pemulihan TIDAK lagi terjadi diam-diam di sini. Sebelumnya `_auto_queue`
        mengantri aksi "makan"/"tidur"/"bicara" ke VM, dan VM menaikkan motif
        dalam tick yang SAMA -- jadi NPC lapar tidak pernah benar-benar lapar
        dari sudut pandang siapa pun di luar `tick`. Sekarang pemulihan datang
        dari gerakan nyata: NPC berjalan ke perabot dan `selesaikan_otonom`
        yang menaikkan motif saat ia tiba.
        """
        for ent in self._brains.values():
            for key, rate in _MOTIVE_DECAY.items():
                ent.change_motive(key, -rate * dt)
        self.vm.tick(dt)

    def get_motives(self, npc_id: str) -> Optional[dict]:
        ent = self._brains.get(npc_id)
        return dict(ent.motives) if ent else None

    def get_anim_hint(self, npc_id: str) -> Optional[str]:
        return self._anim_hint.get(npc_id)

    def queue(self, npc_id: str, action_name: str, priority: int = 5):
        ent = self._brains.get(npc_id)
        if ent:
            ent.queue_action(action_name, priority=priority)

    # ─── OTONOMI ─────────────────────────────────────────
    def motive_urgent(self, npc_id: str) -> bool:
        """True kalau ada motif NPC di bawah ambang otonom."""
        ent = self._brains.get(npc_id)
        if ent is None:
            return False
        return any(ent.get_motive(k) < v for k, v in URGENT_THRESHOLD.items())

    def pilih_otonom(self, npc_id: str, world, tx: float, ty: float,
                     rng=None, radius: int = 8):
        """Pilih perabot untuk kebutuhan mendesak NPC: `((tx, ty), inter)` / None.

        Ini panggilan PERTAMA bagi dua fungsi yang selama ini tidak punya
        pemanggil: `objects.autonomy_candidates` dan `motives.choose_action`.
        `world` harus punya `get_tile(x, y)` dan `scene_obj` (yaitu World3D);
        kalau None, kembalikan None supaya pemanggil jatuh ke jadwal biasa.

        TIDAK mencari jalan -- itu tetap tugas PathGrid lewat `plan_path`.
        """
        ent = self._brains.get(npc_id)
        if ent is None or world is None:
            return None
        if not self.motive_urgent(npc_id):
            return None
        mv = _motif_dari_otak(ent)
        candidates = autonomy_candidates(
            world, int(round(tx)), int(round(ty)), radius)
        pick = choose_action(mv, candidates, rng if rng is not None else random)
        if pick is None:
            return None
        obj, inter = pick
        return (obj[0], obj[1]), inter

    def target_otonom(self, npc_id: str, world, tx: float, ty: float,
                      rng=None, radius: int = 8):
        """Ubin tujuan otonom (tanpa interaksinya), atau None."""
        pilih = self.pilih_otonom(npc_id, world, tx, ty, rng=rng, radius=radius)
        if pilih is None:
            return None
        (gx, gy), _inter = pilih
        return (gx, gy)

    def selesaikan_otonom(self, npc_id: str, inter) -> None:
        """Terapkan janji motif sebuah interaksi ke otak NPC (pemulihan nyata).

        Dipanggil ketika NPC sungguh tiba di perabot -- bukan lewat self-heal
        bayangan. Iklan `nyaman`/`ruang` tidak punya padanan di otak NPC dan
        dilewati; lima lainnya dipetakan balik lewat _MOTIVE_BRIDGE_REVERSE.
        """
        ent = self._brains.get(npc_id)
        if ent is None or inter is None:
            return
        for ad in getattr(inter, 'adverts', None) or []:
            key = _MOTIVE_BRIDGE_REVERSE.get(ad.motive)
            if key:
                ent.change_motive(key, ad.delta)

    # ─── PATHFINDING ─────────────────────────────────────
    def rebuild_grid(self, scene_name: str, dungeon_tiles=None):
        """Bangun ulang PathGrid dari tile WALKABLE pada scene aktif."""
        if scene_name == "dungeon" and dungeon_tiles:
            tiles = dungeon_tiles
            h, w = len(tiles), len(tiles[0]) if tiles else 0
        else:
            sc = SCENES.get(scene_name)
            if sc is None:
                return
            tiles = sc.tiles
            h, w = sc.h, sc.w
        self.grid = PathGrid(w, h, tile_size=1.0)
        for r in range(h):
            for c in range(w):
                if tiles[r][c] not in WALKABLE:
                    self.grid.set_obstacle(c, r)
        self._grid_scene = scene_name

    def plan_path(self, sx: float, sy: float, tx: float, ty: float):
        """Return list waypoint [(cx, cy), ...] atau None."""
        start = (int(round(sx)), int(round(sy)))
        goal  = (int(round(tx)), int(round(ty)))
        path = self.grid.find_path(start, goal)
        if not path:
            return None
        smooth = self.grid.smooth_path(path)
        # Buang titik start (NPC sudah di sana)
        return [(float(c), float(r)) for (c, r) in smooth[1:]] or None
