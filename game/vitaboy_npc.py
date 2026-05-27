"""
vitaboy_npc.py — Helper untuk membuat NPC pakai Vitaboy avatar lengkap
(body + head + hair + textures) yang dirakit dari `.apr` appearance refs.

Phase 9 final: pakai VitaboyAvatar yang sudah resolve .apr → .bnd → mesh + tex.

API:
    npc_root._va  # VitaboyAvatar — panggil .update(dt) tiap frame

Per-NPC outfit pilihan (deterministic dari npc_id).
"""
from __future__ import annotations
import logging
from typing import Optional, List
from ursina import Entity, color

from .vitaboy import VitaboyAvatar, asset_registry


# ─── OUTFIT PILIHAN PER NPC ──────────────────────────────────────────────────
# (body+clothes.apr, head.apr, hair.apr)
NPC_OUTFIT = {
    # Wanita
    'sari':       ('fabd000_sl__defaultpjs.apr', 'fahd001_alt.apr', 'fahl003_longhair02.apr'),
    'maya':       ('fabd000_sl__defaultpjs.apr', 'fahd001_alt.apr', 'fahl902_spikeyhair.apr'),
    'cici':       ('fabd000_sl__defaultpjs.apr', 'fahd001_alt.apr', 'fahl003_longhair02.apr'),
    'ningsih':    ('fabd000_sl__defaultpjs.apr', 'fahd001_alt.apr', 'fahl902_spikeyhair.apr'),
    'mbok_jum':   ('fabd000_sl__defaultpjs.apr', 'fahd001_alt.apr', 'fahl003_longhair02.apr'),
    # Pria
    'arya':       ('mabd000_leathers.apr', 'mahd000_proxy.apr', None),
    'budi':       ('mabd000_leathers.apr', 'mahd000_proxy.apr', None),
    'raka':       ('mabd000_leathers.apr', 'mahd000_proxy.apr', None),
    'joko':       ('mabd000_leathers.apr', 'mahd000_proxy.apr', None),
    'bowo':       ('mabd000_leathers.apr', 'mahd000_proxy.apr', None),
    'pak_guru':   ('mabd000_leathers.apr', 'mahd000_proxy.apr', None),
    'jaka_ronda': ('mabd000_leathers.apr', 'mahd000_proxy.apr', None),
}

DEFAULT_OUTFIT = ('mabd000_leathers.apr', 'mahd000_proxy.apr', None)

DEFAULT_IDLE_ANIM = 'a2a-talk-idle-loop'


def _resolve_outfit_apr_list(npc_id: str) -> List[str]:
    outfit = NPC_OUTFIT.get(npc_id, DEFAULT_OUTFIT)
    return [x for x in outfit if x]


def build_vitaboy_human_npc(parent: Entity, npc_id: str,
                            tint=color.white, scale: float = 0.30) -> Optional[VitaboyAvatar]:
    """Bangun NPC manusia pakai VitaboyAvatar lengkap. Return avatar atau None."""
    apr_list = _resolve_outfit_apr_list(npc_id)
    try:
        avatar = VitaboyAvatar(parent, apr_list, scale=scale, tint=tint)
    except Exception as e:
        logging.warning(f"Vitaboy NPC '{npc_id}' build gagal: {e}")
        return None

    # Default idle
    try:
        avatar.set_animation(DEFAULT_IDLE_ANIM)
    except Exception:
        pass
    return avatar
