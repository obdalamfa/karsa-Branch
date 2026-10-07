"""
anim_state.py — Animation State Machine untuk Lembah Karsa 3D.

Mengelola transisi antara state animasi dan memetakan state ke animasi TSO
(Vitaboy) atau ke animasi prosedural Ursina untuk model fallback voxel.

State priority (tinggi = tidak bisa di-interrupt):
  100 DEATH      — tidak bisa di-interrupt sama sekali
   90 HIT        — interrupt semua kecuali DEATH
   80 ATTACK_*   — interrupt idle/walk
   70 FISH_REEL  — interrupt idle/walk
   60 FISH_CAST  — interrupt idle
   50 GIVE_GIFT, RECEIVE_GIFT, PLANT, HARVEST, GREET, WIN — satu tembak
   30 WALK, RUN  — interrupt idle
   10 IDLE       — prioritas terendah, selalu bisa diganti

Pemakaian:
    from game.anim_state import AnimStateMachine, AnimState

    asm = AnimStateMachine(vitaboy_avatar=player._va,
                           voxel_pivots=player._pivots)
    # Tiap frame:
    asm.update(dt)
    # Saat aksi:
    asm.request(AnimState.ATTACK_SWORD)
    asm.request(AnimState.WALK)
    asm.request(AnimState.SLEEP)
"""
from __future__ import annotations
import math
from enum import Enum, auto
from typing import Optional, Dict, Any, Callable


# ---------------------------------------------------------------------------
# Enum semua state
# ---------------------------------------------------------------------------
class AnimState(Enum):
    IDLE          = auto()
    WALK          = auto()
    RUN           = auto()
    ATTACK_SWORD  = auto()
    ATTACK_HOE    = auto()   # cangkul / palu
    ATTACK_PUNCH  = auto()
    FISH_CAST     = auto()
    FISH_WAIT     = auto()
    FISH_REEL     = auto()
    GIVE_GIFT     = auto()
    RECEIVE_GIFT  = auto()
    PLANT         = auto()
    HARVEST       = auto()
    SLEEP         = auto()
    HIT           = auto()
    DEATH         = auto()
    WIN           = auto()
    GREET         = auto()
    SIT           = auto()
    CHEER         = auto()
    DANCE         = auto()


# ---------------------------------------------------------------------------
# Konfigurasi per-state
# ---------------------------------------------------------------------------
_STATE_CFG: Dict[AnimState, Dict[str, Any]] = {
    #                          TSO anim name                      loop   dur(s)  priority
    AnimState.IDLE:          {'tso': 'a2a-talk-idle-loop',        'loop': True,  'dur': 0,    'pri': 10},
    AnimState.WALK:          {'tso': 'a2a-talk-idle-loop',        'loop': True,  'dur': 0,    'pri': 30},  # TSO walk belum tersedia, pakai idle
    AnimState.RUN:           {'tso': 'a2a-talk-idle-loop',        'loop': True,  'dur': 0,    'pri': 35},
    AnimState.ATTACK_SWORD:  {'tso': 'a2a-attack-loop-slam',      'loop': False, 'dur': 0.55, 'pri': 80},
    AnimState.ATTACK_HOE:    {'tso': 'a2o-hammer-swing-strike',   'loop': False, 'dur': 0.60, 'pri': 80},
    AnimState.ATTACK_PUNCH:  {'tso': 'a2a-attack-loop-punch',     'loop': False, 'dur': 0.45, 'pri': 80},
    AnimState.FISH_CAST:     {'tso': 'a2o-pond-boat-steer1',      'loop': False, 'dur': 0.80, 'pri': 60},
    AnimState.FISH_WAIT:     {'tso': 'a2o-pond-boat-steer2',      'loop': True,  'dur': 0,    'pri': 50},
    AnimState.FISH_REEL:     {'tso': 'a2o-pond-boat-get',         'loop': False, 'dur': 1.20, 'pri': 70},
    AnimState.GIVE_GIFT:     {'tso': 'a2a-gift-appreciater',      'loop': False, 'dur': 1.50, 'pri': 50},
    AnimState.RECEIVE_GIFT:  {'tso': 'a2a-gift-appreciatee',      'loop': False, 'dur': 1.50, 'pri': 50},
    AnimState.PLANT:         {'tso': 'a2o-garden-kneel-look-plant','loop': False,'dur': 1.00, 'pri': 50},
    AnimState.HARVEST:       {'tso': 'a2o-garden-kneel-harvest',  'loop': False, 'dur': 1.00, 'pri': 50},
    AnimState.SLEEP:         {'tso': 'a2o-chaiselounge-sleep-loop','loop': True, 'dur': 0,    'pri': 50},
    AnimState.HIT:           {'tso': 'a2o-trap-reaction-arrow',   'loop': False, 'dur': 0.40, 'pri': 90},
    AnimState.DEATH:         {'tso': 'a2a-attack-lose-start',     'loop': False, 'dur': 2.00, 'pri': 100},
    AnimState.WIN:           {'tso': 'a2a-attack-win-start',      'loop': False, 'dur': 1.50, 'pri': 50},
    AnimState.GREET:         {'tso': 'a2o-greet01',               'loop': False, 'dur': 1.20, 'pri': 50},
    AnimState.SIT:           {'tso': 'a2a-sit',                   'loop': True,  'dur': 0,    'pri': 50},
    AnimState.CHEER:         {'tso': 'a2a-cheerer-loop',          'loop': True,  'dur': 0,    'pri': 50},
    AnimState.DANCE:         {'tso': 'a2a-dancee-loop-basic',     'loop': True,  'dur': 0,    'pri': 50},
}


# ---------------------------------------------------------------------------
# Prosedural animasi voxel via Ursina lerp/animate
# ---------------------------------------------------------------------------

def _voxel_attack_sword(pivots: Dict[str, Any], t: float):
    """Animasi prosedural pedang — ayun lengan kanan ke depan."""
    try:
        from ursina import Vec3
        piv = pivots.get('shoulder_r')
        if piv:
            # Fase 0-0.15s: angkat ke belakang; 0.15-0.4s: ayun ke depan; 0.4-0.55s: reset
            if t < 0.15:
                angle = t / 0.15 * (-55)
            elif t < 0.40:
                angle = -55 + (t - 0.15) / 0.25 * 120
            else:
                angle = 65 - (t - 0.40) / 0.15 * 65
            piv.rotation_x = angle
    except Exception:
        pass


def _voxel_attack_hoe(pivots: Dict[str, Any], t: float):
    """Animasi cangkul — kedua lengan ayun ke bawah."""
    try:
        for side in ('shoulder_l', 'shoulder_r'):
            piv = pivots.get(side)
            if piv:
                if t < 0.20:
                    angle = t / 0.20 * (-80)
                elif t < 0.45:
                    angle = -80 + (t - 0.20) / 0.25 * 120
                else:
                    angle = 40 - (t - 0.45) / 0.15 * 40
                piv.rotation_x = angle
    except Exception:
        pass


def _voxel_walk(pivots: Dict[str, Any], t: float, speed: float = 2.5):
    """Walk cycle — kaki & lengan berayun bergantian."""
    try:
        cycle = (t * speed) % 1.0
        angle = math.sin(cycle * 2 * math.pi) * 30
        for side, mult in (('hip_l', 1), ('hip_r', -1)):
            piv = pivots.get(side)
            if piv:
                piv.rotation_x = angle * mult
        for side, mult in (('shoulder_l', -1), ('shoulder_r', 1)):
            piv = pivots.get(side)
            if piv:
                piv.rotation_x = angle * mult * 0.5
    except Exception:
        pass


def _voxel_idle(pivots: Dict[str, Any], t: float):
    """Napas halus saat idle."""
    try:
        bob = math.sin(t * 1.2) * 0.008
        neck = pivots.get('neck')
        if neck:
            neck.position.y = neck._base_y + bob if hasattr(neck, '_base_y') else neck.position.y
    except Exception:
        pass


def _voxel_hit(pivots: Dict[str, Any], t: float):
    """Reaksi kena serangan — tilt ke belakang."""
    try:
        neck = pivots.get('neck')
        if neck and t < 0.20:
            neck.rotation_x = (t / 0.20) * -25
        elif neck:
            neck.rotation_x = -25 + ((t - 0.20) / 0.20) * 25
    except Exception:
        pass


def _voxel_sleep(pivots: Dict[str, Any], t: float):
    """Tidur — rebah ke samping."""
    try:
        neck = pivots.get('neck')
        if neck:
            neck.rotation_z = -80  # kepala rebah
    except Exception:
        pass


def _voxel_fish_cast(pivots: Dict[str, Any], t: float):
    """Cast pancing — ayun lengan kanan ke belakang lalu lempar ke depan."""
    try:
        piv = pivots.get('shoulder_r')
        if piv:
            if t < 0.30:
                angle = t / 0.30 * (-90)
            elif t < 0.60:
                angle = -90 + (t - 0.30) / 0.30 * 120
            else:
                angle = 30 - (t - 0.60) / 0.20 * 30
            piv.rotation_x = angle
    except Exception:
        pass


def _voxel_fish_wait(pivots: Dict[str, Any], t: float):
    """Menunggu umpan — pose tenang sedikit membungkuk."""
    try:
        piv = pivots.get('shoulder_r')
        if piv:
            piv.rotation_x = 30 + math.sin(t * 0.8) * 3
    except Exception:
        pass


def _voxel_give_gift(pivots: Dict[str, Any], t: float):
    """Ngasih kado — angkat kedua tangan."""
    try:
        for side in ('shoulder_l', 'shoulder_r'):
            piv = pivots.get(side)
            if piv:
                if t < 0.40:
                    angle = t / 0.40 * (-70)
                elif t < 1.10:
                    angle = -70
                else:
                    angle = -70 + (t - 1.10) / 0.40 * 70
                piv.rotation_x = angle
    except Exception:
        pass


def _voxel_reset(pivots: Dict[str, Any]):
    """Reset semua pivot ke pose default."""
    try:
        defaults = {
            'shoulder_l': (0, 0, 0), 'shoulder_r': (0, 0, 0),
            'hip_l': (0, 0, 0),      'hip_r': (0, 0, 0),
            'neck': (0, 0, 0),
        }
        for name, rot in defaults.items():
            piv = pivots.get(name)
            if piv:
                piv.rotation_x, piv.rotation_y, piv.rotation_z = rot
    except Exception:
        pass


# Mapping state → prosedural anim function
_VOXEL_ANIM: Dict[AnimState, Optional[Callable]] = {
    AnimState.IDLE:         _voxel_idle,
    AnimState.WALK:         _voxel_walk,
    AnimState.RUN:          _voxel_walk,
    AnimState.ATTACK_SWORD: _voxel_attack_sword,
    AnimState.ATTACK_HOE:   _voxel_attack_hoe,
    AnimState.ATTACK_PUNCH: _voxel_attack_sword,
    AnimState.FISH_CAST:    _voxel_fish_cast,
    AnimState.FISH_WAIT:    _voxel_fish_wait,
    AnimState.FISH_REEL:    _voxel_fish_cast,
    AnimState.GIVE_GIFT:    _voxel_give_gift,
    AnimState.RECEIVE_GIFT: _voxel_give_gift,
    AnimState.HIT:          _voxel_hit,
    AnimState.SLEEP:        _voxel_sleep,
    AnimState.PLANT:        _voxel_attack_hoe,
    AnimState.HARVEST:      _voxel_attack_hoe,
}


# ---------------------------------------------------------------------------
# AnimStateMachine
# ---------------------------------------------------------------------------
class AnimStateMachine:
    """
    Drives animasi Vitaboy avatar ATAU voxel fallback berdasarkan game state.

    Args:
        vitaboy_avatar: instance VitaboyAvatar (player._va), bisa None.
        voxel_pivots:   dict name→Entity pivot, bisa None.
    """

    def __init__(self,
                 vitaboy_avatar=None,
                 voxel_pivots: Optional[Dict[str, Any]] = None):
        self._va      = vitaboy_avatar
        self._pivots  = voxel_pivots or {}
        self._state   = AnimState.IDLE
        self._timer   = 0.0        # waktu di state ini
        self._on_done: Optional[Callable] = None
        self._blocking = False     # apakah state saat ini blocking
        self._walk_t   = 0.0      # akumulator untuk walk cycle

        self._enter_state(AnimState.IDLE)

    # ── Public API ──────────────────────────────────────────────────────────

    @property
    def state(self) -> AnimState:
        return self._state

    def request(self, new_state: AnimState,
                on_done: Optional[Callable] = None) -> bool:
        """
        Minta transisi ke state baru.
        Return True jika diterima, False jika ditolak (state saat ini lebih prioritas).
        """
        cfg_cur = _STATE_CFG[self._state]
        cfg_new = _STATE_CFG[new_state]

        # Cek blocking
        if self._blocking and cfg_new['pri'] < cfg_cur['pri']:
            return False

        self._on_done = on_done
        self._enter_state(new_state)
        return True

    def force(self, new_state: AnimState,
              on_done: Optional[Callable] = None):
        """Paksa transisi apapun state saat ini."""
        self._blocking = False
        self._on_done = on_done
        self._enter_state(new_state)

    def update(self, dt: float):
        """Panggil tiap frame dari player.tick()."""
        self._timer += dt
        self._walk_t += dt

        cfg = _STATE_CFG[self._state]

        # Jalankan animasi prosedural voxel
        if self._pivots:
            fn = _VOXEL_ANIM.get(self._state)
            if fn:
                fn(self._pivots, self._timer)

        # Update vitaboy
        if self._va:
            try:
                self._va.update(dt)
            except Exception:
                pass

        # Auto-return ke IDLE setelah one-shot selesai
        dur = cfg.get('dur', 0)
        if dur > 0 and self._timer >= dur:
            self._blocking = False
            cb = self._on_done
            self._on_done = None
            self._enter_state(AnimState.IDLE)
            if cb:
                try:
                    cb()
                except Exception:
                    pass

    def is_blocking(self) -> bool:
        return self._blocking

    def is_state(self, s: AnimState) -> bool:
        return self._state == s

    # ── Internal ────────────────────────────────────────────────────────────

    def _enter_state(self, new_state: AnimState):
        if self._state != new_state and self._pivots:
            _voxel_reset(self._pivots)

        self._state  = new_state
        self._timer  = 0.0
        cfg = _STATE_CFG[new_state]

        # Blocking = state dengan durasi tertentu (satu tembak)
        self._blocking = cfg.get('dur', 0) > 0

        # Set animasi Vitaboy
        if self._va:
            tso_name = cfg.get('tso', 'a2a-talk-idle-loop')
            try:
                self._va.set_animation(tso_name)
            except Exception:
                pass
