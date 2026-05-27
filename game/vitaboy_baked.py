"""
vitaboy_baked.py — Loader untuk Vitaboy GLB hasil bake (tools/bake_vitaboy.py).

Tujuan: ganti Python skinning runtime yang lambat dengan GLB native Panda3D Actor.
Animasi jalan di GPU via Panda3D built-in skinning — zero Python overhead.

Pemakaian:
    from game.vitaboy_baked import load_baked_actor
    actor = load_baked_actor('assets/vitaboy/sari_idle.glb', play='a2a-talk-idle-loop')
    actor.reparent_to(npc_root)   # tempel ke NPC root entity
    actor.set_scale(0.32)         # adjust ukuran ke skala dunia
    # Actor.loop() sudah dipanggil — animasi jalan otomatis

GLB harus dibake dulu:
    blender --background --python tools/bake_vitaboy.py -- \\
        --mesh au-blue --anim a2a-talk-idle-loop --out assets/vitaboy/sari_idle.glb
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

from panda3d.core import Filename, NodePath
from direct.actor.Actor import Actor


# Direktori GLB baked Vitaboy avatar
_VITABOY_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'models'


def load_baked_actor(path: str, play: Optional[str] = None,
                     loop: bool = True) -> Optional[Actor]:
    """Load .glb bake, optional auto-play animasi.

    Args:
        path: absolute atau relative ke 3d/ root.
        play: nama animasi (mis. 'a2a-talk-idle-loop'). Kalau None, tidak play.
        loop: True (default) = loop terus, False = play sekali.

    Return: Actor instance, atau None kalau gagal load.
    """
    p = Path(path)
    if not p.is_absolute():
        p = _VITABOY_DIR.parent.parent / path
    if not p.exists():
        logging.warning(f"Vitaboy baked GLB tidak ada: {p}")
        return None

    try:
        actor = Actor(Filename.fromOsSpecific(str(p)))
    except Exception as e:
        logging.warning(f"Actor load failed: {e}")
        return None

    if play:
        anim_names = actor.getAnimNames()
        if play in anim_names:
            if loop:
                actor.loop(play)
            else:
                actor.play(play)
        else:
            logging.warning(f"Anim '{play}' tidak ditemukan. Tersedia: {anim_names}")
            # Fallback: play first available
            if anim_names:
                if loop:
                    actor.loop(anim_names[0])
                else:
                    actor.play(anim_names[0])

    return actor


def list_baked() -> list[Path]:
    """List semua .glb di assets/vitaboy/."""
    if not _VITABOY_DIR.exists():
        return []
    return sorted(_VITABOY_DIR.glob('*.glb'))


def bake_status() -> dict:
    """Diagnostik: berapa GLB tersedia, ukuran total, nama-nama."""
    baked = list_baked()
    return {
        'count': len(baked),
        'total_kb': sum(b.stat().st_size for b in baked) // 1024,
        'names': [b.stem for b in baked],
    }


# ─── Two-state actor: idle + walk ────────────────────────────────────────────
class BakedNPCActor:
    """Wrapper untuk NPC dengan 2 GLB files (idle + walk), swap saat moving.

    Karena tiap GLB hanya bawa 1 anim track, kita instansiasi 2 Actor: idle + walk.
    Hanya 1 aktif (parented ke npc_root) pada waktu tertentu — yang lain disembunyikan.

    Usage:
        actor = BakedNPCActor('au-red', parent=npc_root, scale=0.32)
        actor.set_idle()
        actor.set_walk()
    """

    def __init__(self, color: str, parent=None, scale: float = 0.32):
        self.color = color
        idle_path = _VITABOY_DIR / f'au-{color}_idle.glb'
        walk_path = _VITABOY_DIR / f'au-{color}_walk.glb'

        self.idle_actor = None
        self.walk_actor = None
        if idle_path.exists():
            try:
                self.idle_actor = Actor(Filename.fromOsSpecific(str(idle_path)))
            except Exception as e:
                logging.warning(f"BakedNPCActor idle load fail ({color}): {e}")
        if walk_path.exists():
            try:
                self.walk_actor = Actor(Filename.fromOsSpecific(str(walk_path)))
            except Exception as e:
                logging.warning(f"BakedNPCActor walk load fail ({color}): {e}")

        # Setup both
        for a in (self.idle_actor, self.walk_actor):
            if a:
                a.set_scale(scale)
                if parent is not None:
                    try:
                        a.reparent_to(parent)
                    except Exception:
                        pass

        self._state = None
        if self.idle_actor:
            self.set_idle()
        elif self.walk_actor:
            self.set_walk()

    def set_idle(self):
        if self._state == 'idle':
            return
        if self.walk_actor: self.walk_actor.hide()
        if self.idle_actor:
            self.idle_actor.show()
            names = self.idle_actor.getAnimNames()
            if names:
                self.idle_actor.loop(names[0])
        self._state = 'idle'

    def set_walk(self):
        if self._state == 'walk':
            return
        if self.idle_actor: self.idle_actor.hide()
        if self.walk_actor:
            self.walk_actor.show()
            names = self.walk_actor.getAnimNames()
            if names:
                self.walk_actor.loop(names[0])
        self._state = 'walk'

    def cleanup(self):
        for a in (self.idle_actor, self.walk_actor):
            if a:
                try:
                    a.cleanup()
                    a.remove_node()
                except Exception:
                    pass
