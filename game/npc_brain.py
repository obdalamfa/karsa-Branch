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
from typing import Dict, Optional

from .behavior_vm import BehaviorVM, BehaviorEntity
from .pathfinder import PathGrid
from .data import HUMAN_NPCS, all_npcs
from .scenes import SCENES
from .config import WALKABLE


# Decay motif per detik (kasar — 100 → 0 dalam ~16 menit real-time)
_MOTIVE_DECAY = {
    "hunger":  0.10,
    "energy":  0.06,
    "social":  0.08,
    "fun":     0.05,
    "hygiene": 0.04,
}


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
        # Decay motif
        for ent in self._brains.values():
            for key, rate in _MOTIVE_DECAY.items():
                ent.change_motive(key, -rate * dt)
            # Auto-queue aksi paling urgent kalau idle
            if not ent.thread.queue and not ent.thread.stack:
                self._auto_queue(ent)
        self.vm.tick(dt)

    def _auto_queue(self, ent: BehaviorEntity):
        # Pilih kebutuhan paling rendah & antri aksi yang menaikkannya
        thresholds = [
            ("hunger", "makan",  35.0),
            ("energy", "tidur",  25.0),
            ("social", "bicara", 30.0),
        ]
        for key, act, th in thresholds:
            if ent.get_motive(key) < th:
                ent.queue_action(act, priority=10)
                return
        ent.queue_action("idle", priority=1)

    def get_motives(self, npc_id: str) -> Optional[dict]:
        ent = self._brains.get(npc_id)
        return dict(ent.motives) if ent else None

    def get_anim_hint(self, npc_id: str) -> Optional[str]:
        return self._anim_hint.get(npc_id)

    def queue(self, npc_id: str, action_name: str, priority: int = 5):
        ent = self._brains.get(npc_id)
        if ent:
            ent.queue_action(action_name, priority=priority)

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
