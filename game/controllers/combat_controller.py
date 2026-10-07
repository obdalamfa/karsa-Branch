"""
combat_controller.py — Sistem Bertarung Dungeon Lembah Karsa 3D.

Fitur:
  - Serangan pedang dengan cooldown, range, dan damage tier
  - Combo 3-hit (tap cepat berturut dalam window 0.7 detik)
  - Dodge roll (Q / double-tap arah) — iframe 0.35 detik
  - Block/tangkis (E tahan) — kurangi damage 60%, ada stamina cost
  - Critical hit 15% chance → 1.8× damage + efek khusus
  - Setiap mob punya pola serangan berbeda (fase + cooldown)
  - Damage number melayang di layar
  - Screen shake saat kena serangan
  - Loot drop saat mob mati (jatuh ke lantai, bisa dipungut)
  - Respawn player setelah mati (kembali ke entrance dungeon)
  - Progress stat: mobs_killed, deepest_level, total_damage_dealt
"""
from __future__ import annotations
import math
import random
import logging
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..player import Player3D
    from ..panels import UIManager
    from ..entities import EntitiesManager

from ..mob import Monster, MobState
from ..anim_state import AnimState
from ..config import GROUND_H, TILE_SIZE as TS
from ..sound import play as sound_play

# ── Konstanta combat ────────────────────────────────────────────────────────
PLAYER_ATTACK_RANGE      = 1.8    # tile
PLAYER_ATTACK_COOLDOWN   = 0.55   # detik (base, bisa dikurangi upgrade)
DODGE_COOLDOWN           = 1.20   # detik
DODGE_IFRAME_DUR         = 0.35   # detik invuln saat dodge
DODGE_DIST               = 2.2    # tile jauh dodge
BLOCK_STAMINA_COST       = 8      # energi per detik saat nahan block
CRIT_CHANCE              = 0.15   # 15%
CRIT_MULT                = 1.80
COMBO_WINDOW             = 0.70   # detik jendela combo lanjutan
COMBO_DAMAGE_MULT        = (1.0, 1.3, 1.8)  # hit ke-1, 2, 3

# Damage pedang per tier (ID dari data.py SWORD_RECIPES)
SWORD_DAMAGE: Dict[str, int] = {
    'kayu':     8,
    'tembaga':  15,
    'besi':     24,
    'mithril':  40,
    'emas':     35,
    'kristal':  50,
}
BARE_DAMAGE = 4   # tanpa pedang (tinju)

# Pola serangan per jenis mob (cooldown_ms, damage_mult, special)
MOB_ATTACK_PATTERN: Dict[str, Dict] = {
    'kelelawar':   {'cd': 0.80, 'dmg_mult': 0.8,  'special': None},
    'tikus_gua':   {'cd': 0.60, 'dmg_mult': 0.7,  'special': None},
    'genderuwo':   {'cd': 1.40, 'dmg_mult': 1.5,  'special': 'knockback'},
    'banaspati':   {'cd': 0.90, 'dmg_mult': 1.0,  'special': 'burn'},
    'kuntilanak':  {'cd': 1.10, 'dmg_mult': 1.2,  'special': 'slow'},
    'leak':        {'cd': 1.00, 'dmg_mult': 1.3,  'special': 'fear'},
    'pocong':      {'cd': 2.00, 'dmg_mult': 2.0,  'special': 'stun'},
}

# Status efek durasi (detik)
STATUS_DURATION = {'burn': 3.0, 'slow': 4.0, 'fear': 2.5, 'stun': 1.5}


class CombatController:
    """
    Mengelola semua mekanik combat untuk player di dungeon.

    Dipanggil dari Player3D.tick() setiap frame.
    Juga di-hook ke interaction_controller.attack() untuk override.
    """

    def __init__(self, player: 'Player3D'):
        self.player = player
        self.state  = player.state

        # Cooldown & timer
        self._attack_cd    = 0.0
        self._dodge_cd     = 0.0
        self._dodge_iframe = 0.0    # sisa iframe dari dodge
        self._block_held   = False

        # Combo system
        self._combo_count  = 0      # 0, 1, 2
        self._combo_timer  = 0.0    # countdown window

        # Status efek pada player
        self._status: Dict[str, float] = {}   # name → sisa durasi

        # Loot entities di lantai (list of (item_name, Entity, timer))
        self._floor_loot: List[Tuple[str, object, float]] = []

        # Damage number pool (list of active DamageNumber)
        self._dmg_numbers: List[_DamageNumber] = []

        # Screen shake
        self._shake_t = 0.0

    # ── TICK ────────────────────────────────────────────────────────────────

    def tick(self, dt: float, entities_mgr: Optional['EntitiesManager'],
             panels: Optional['UIManager']):
        """Panggil tiap frame dari Player3D.tick()."""
        self._advance_timers(dt)
        self._tick_status(dt, panels)
        self._tick_floor_loot(dt)
        self._tick_dmg_numbers(dt)

    # ── ATTACK ──────────────────────────────────────────────────────────────

    def attack(self, entities_mgr: 'EntitiesManager',
               panels: 'UIManager') -> bool:
        """
        Serangan pemain. Return True jika menyerang (bukan blocked cooldown).
        Mendukung combo 3-hit.
        """
        if self._attack_cd > 0:
            return False
        if self._dodge_iframe > 0:
            return False

        p = self.player
        s = self.state

        # Hitung damage dasar
        base_dmg = self._calc_sword_damage(s)

        # Combo multiplier
        if self._combo_timer > 0 and self._combo_count < 3:
            self._combo_count += 1
        else:
            self._combo_count = 1
        self._combo_timer = COMBO_WINDOW

        combo_mult = COMBO_DAMAGE_MULT[min(self._combo_count - 1, 2)]
        dmg = int(base_dmg * combo_mult)

        # Critical hit
        is_crit = random.random() < CRIT_CHANCE
        if is_crit:
            dmg = int(dmg * CRIT_MULT)

        # Hit mobs dalam range
        tx, ty = p.get_tile_pos()
        hit_count = 0
        killed = 0
        for actor_id, actor in list(entities_mgr.actors.items()):
            if not isinstance(actor, Monster):
                continue
            if actor.hp <= 0:
                continue
            dist = math.hypot(actor.logical_x - tx, actor.logical_y - ty)
            if dist > PLAYER_ATTACK_RANGE:
                continue

            # Terapkan damage
            prev_hp = actor.hp
            actor.hp = max(0, actor.hp - dmg)
            actor.dmg_flash_ms = 300
            hit_count += 1

            # Update total damage dealt
            s.stats['total_damage'] = s.stats.get('total_damage', 0) + (prev_hp - actor.hp)

            # Damage number
            wx = actor.logical_x * TS
            wz = actor.logical_y * TS
            self._spawn_dmg_number(dmg, wx, GROUND_H + 2.2, wz,
                                   color_key='crit' if is_crit else 'normal')

            if actor.hp <= 0:
                killed += 1
                self._on_mob_killed(actor, entities_mgr, panels)

        # Update stats & UI
        if hit_count > 0:
            sound_play('sword', 0.9 if not is_crit else 1.0)
            if is_crit:
                sound_play('crit', 0.7)
                panels.flash_msg(f"CRITICAL! {dmg} damage!", 0.8)
            if killed:
                s.stats['mobs_killed'] = s.stats.get('mobs_killed', 0) + killed
                panels.flash_msg(f"{killed} musuh dikalahkan!", 1.2)
                self._check_quests(panels)
        else:
            sound_play('sword_miss', 0.4)

        # Animasi pedang
        if hasattr(p, '_anim') and p._anim:
            p._anim.request(AnimState.ATTACK_SWORD)
        elif hasattr(p, '_play_tool_anim'):
            p._play_tool_anim('swing')

        # Cooldown (combo hit 3 lebih lambat)
        cd_mult = 1.0 if self._combo_count < 3 else 1.4
        self._attack_cd = PLAYER_ATTACK_COOLDOWN * cd_mult

        return True

    # ── DODGE ───────────────────────────────────────────────────────────────

    def dodge(self, dir_x: float, dir_z: float,
              panels: 'UIManager') -> bool:
        """
        Dodge roll ke arah (dir_x, dir_z) — tile space.
        Memberikan iframe DODGE_IFRAME_DUR detik.
        """
        if self._dodge_cd > 0:
            return False
        if 'stun' in self._status:
            panels.flash_msg("Terstun! Tidak bisa dodge.", 0.6)
            return False

        p = self.player
        # Normalise
        length = math.hypot(dir_x, dir_z)
        if length < 0.01:
            # Dodge ke arah menghadap
            angle = math.radians(p.rotation_y)
            dir_x = -math.sin(angle)
            dir_z = -math.cos(angle)
        else:
            dir_x /= length
            dir_z /= length

        # Cek tile tujuan (walkable)
        cur_tx, cur_ty = p.get_tile_pos()
        dest_tx = cur_tx + round(dir_x * DODGE_DIST)
        dest_ty = cur_ty + round(dir_z * DODGE_DIST)

        if p.world.is_walkable(int(dest_tx), int(dest_ty)):
            target_x = dest_tx * TS
            target_z = dest_ty * TS
            # Geser player (langsung setpos karena ini dash cepat)
            try:
                from ursina import invoke
                invoke(p.set_position,
                       (target_x, GROUND_H, target_z), delay=0.15)
            except Exception:
                p.x = target_x
                p.z = target_z

        self._dodge_iframe = DODGE_IFRAME_DUR
        self._dodge_cd     = DODGE_COOLDOWN
        self.state.invuln_timer_ms = int(DODGE_IFRAME_DUR * 1000)

        sound_play('dodge', 0.7)
        return True

    # ── BLOCK ───────────────────────────────────────────────────────────────

    def start_block(self):
        self._block_held = True

    def stop_block(self):
        self._block_held = False

    def is_blocking(self) -> bool:
        return self._block_held

    # ── DAMAGE TERIMA ────────────────────────────────────────────────────────

    def receive_damage(self, raw_dmg: int, source_kind: str,
                       panels: 'UIManager') -> int:
        """
        Proses damage yang masuk ke player.
        Return damage aktual setelah modifikasi block/dodge.
        """
        s = self.state

        # Immune jika iframe aktif
        if self._dodge_iframe > 0 or s.invuln_timer_ms > 0:
            return 0

        dmg = raw_dmg

        # Block: kurangi 60%
        if self._block_held:
            dmg = max(1, int(dmg * 0.40))
            s.energy = max(0, s.energy - BLOCK_STAMINA_COST)
            sound_play('block', 0.8)

        # Status efek slow tidak mempengaruhi damage

        # Terapkan
        s.hp = max(0, s.hp - dmg)
        s.invuln_timer_ms = 600

        # Animasi
        p = self.player
        if hasattr(p, '_anim') and p._anim:
            p._anim.request(AnimState.HIT)
        self._shake_t = 0.3

        # UI
        self._spawn_dmg_number(dmg, p.x, GROUND_H + 2.5, p.z, color_key='player')
        sound_play('hit', 0.8)

        if s.hp <= 0:
            self._on_player_death(panels)

        return dmg

    # ── SPECIAL EFFECTS ──────────────────────────────────────────────────────

    def apply_status(self, effect: str, panels: 'UIManager'):
        dur = STATUS_DURATION.get(effect, 2.0)
        self._status[effect] = dur
        msgs = {
            'burn':  "Terbakar! HP terus berkurang.",
            'slow':  "Melambat! Kecepatan berkurang.",
            'fear':  "Ketakutan! Kendali berkurang.",
            'stun':  "Terstun! Tidak bisa bergerak.",
        }
        if panels and effect in msgs:
            panels.flash_msg(msgs[effect], 1.5)

    # ── INTERNAL ────────────────────────────────────────────────────────────

    def _advance_timers(self, dt: float):
        self._attack_cd    = max(0.0, self._attack_cd    - dt)
        self._dodge_cd     = max(0.0, self._dodge_cd     - dt)
        self._dodge_iframe = max(0.0, self._dodge_iframe - dt)
        self._shake_t      = max(0.0, self._shake_t      - dt)
        if self._combo_timer > 0:
            self._combo_timer = max(0.0, self._combo_timer - dt)
            if self._combo_timer <= 0:
                self._combo_count = 0

    def _tick_status(self, dt: float, panels: Optional['UIManager']):
        for effect in list(self._status):
            self._status[effect] -= dt
            if self._status[effect] <= 0:
                del self._status[effect]
                if panels:
                    panels.flash_msg(f"Efek {effect} hilang.", 0.6)
                continue

            # Efek aktif tiap tick
            if effect == 'burn':
                burn_dmg = max(1, int(3 * dt))
                self.state.hp = max(0, self.state.hp - burn_dmg)
            elif effect == 'slow':
                # Speed modifier diterapkan di player.py saat movement
                pass

    def _tick_floor_loot(self, dt: float):
        """Hapus loot lantai setelah 30 detik."""
        alive = []
        for item_name, ent, timer in self._floor_loot:
            timer -= dt
            if timer <= 0:
                try:
                    from ursina import destroy
                    destroy(ent)
                except Exception:
                    pass
            else:
                alive.append((item_name, ent, timer))
        self._floor_loot = alive

    def _tick_dmg_numbers(self, dt: float):
        alive = []
        for dn in self._dmg_numbers:
            dn.tick(dt)
            if dn.alive:
                alive.append(dn)
        self._dmg_numbers = alive



    def _calc_sword_damage(self, s) -> int:
        if not s.sword_id:
            return BARE_DAMAGE
        # Cari dari SWORD_DAMAGE dict (id = tier material)
        for mat, dmg in SWORD_DAMAGE.items():
            if mat in (s.sword_id or ''):
                return dmg
        # Fallback ke SWORD_RECIPES
        try:
            from ..data import SWORD_RECIPES
            for r in SWORD_RECIPES:
                if r.get('id') == s.sword_id:
                    return r.get('damage', 10)
        except Exception:
            pass
        return 10

    def _on_mob_killed(self, mob: Monster, entities_mgr: 'EntitiesManager',
                       panels: 'UIManager'):
        """Animasi mati mob + drop loot ke lantai."""
        mob.ai_state = MobState.DEAD

        # Animasi death vitaboy mob (jika ada)
        if hasattr(mob, '_va') and mob._va:
            try:
                mob._va.set_animation('a2a-attack-lose-start')
            except Exception:
                pass

        # Drop loot
        for item_name, qty in mob.mob_spec.get('drops', {}).items():
            for _ in range(qty):
                self._spawn_floor_loot(
                    item_name,
                    mob.logical_x * TS + random.uniform(-0.3, 0.3),
                    mob.logical_y * TS + random.uniform(-0.3, 0.3),
                    entities_mgr
                )

        # XP / gold
        xp = mob.mob_spec.get('xp', 0)
        self.state.stats['xp'] = self.state.stats.get('xp', 0) + xp

        # Sound
        sound_play('mob_die', 0.8)

    def _spawn_floor_loot(self, item_name: str, wx: float, wz: float,
                          entities_mgr: Optional['EntitiesManager']):
        """Buat entity loot di lantai."""
        try:
            from ursina import Entity, color as ucolor
            LOOT_COLOR = {
                'tembaga': ucolor.rgb(184, 115, 51),
                'besi':    ucolor.rgb(140, 140, 148),
                'emas':    ucolor.rgb(255, 200, 0),
                'kristal': ucolor.rgb(160, 200, 255),
                'kayu':    ucolor.rgb(139, 90, 43),
                'mithril': ucolor.rgb(170, 220, 255),
            }
            col = LOOT_COLOR.get(item_name, ucolor.white)
            ent = Entity(model='sphere',
                         position=(wx, GROUND_H + 0.18, wz),
                         scale=0.22,
                         color=col)
            self._floor_loot.append((item_name, ent, 30.0))

            # Pungut otomatis jika pemain melewati (check di pickup_nearby)
        except Exception as e:
            logging.warning(f"Floor loot spawn error: {e}")

    def pickup_nearby(self, tx: int, ty: int, panels: 'UIManager'):
        """
        Cek dan pungut loot lantai dekat player.
        Panggil dari interaction_controller atau Player3D.tick().
        """
        radius = 1.2
        picked = []
        remaining = []
        for item_name, ent, timer in self._floor_loot:
            try:
                ex, ez = ent.x / TS, ent.z / TS
            except Exception:
                remaining.append((item_name, ent, timer))
                continue
            if math.hypot(ex - tx, ez - ty) <= radius:
                # Tambah ke inventory
                self.state.inventory[item_name] = \
                    self.state.inventory.get(item_name, 0) + 1
                picked.append(item_name)
                try:
                    from ursina import destroy
                    destroy(ent)
                except Exception:
                    pass
            else:
                remaining.append((item_name, ent, timer))

        self._floor_loot = remaining
        if picked and panels:
            summary = ', '.join(
                f"{v}×{k}" for k, v in
                {i: picked.count(i) for i in set(picked)}.items()
            )
            panels.flash_msg(f"Memungut: {summary}", 1.5)
            sound_play('pickup', 0.6)

    def _on_player_death(self, panels: 'UIManager'):
        """Tangani kematian player — animasi, pause, respawn dialog."""
        p = self.player
        if hasattr(p, '_anim') and p._anim:
            p._anim.force(AnimState.DEATH)
        elif hasattr(p, 'set_pose'):
            # AnimStateMachine tak pernah diinstansiasi (dead code), jadi dulu
            # animasi tumbang TAK PERNAH jalan. Pakai sistem pose bertahan.
            p.set_pose('death')

        sound_play('player_die', 1.0)

        if panels:
            panels.flash_msg(
                "💀 Kau gugur di kedalaman gua...\n"
                "[Tekan Enter untuk respawn di pintu masuk]",
                5.0
            )

        # Respawn: kembalikan HP minimal, teleport ke tile awal dungeon
        try:
            from ursina import invoke
            invoke(self._respawn, panels, delay=3.0)
        except Exception:
            self._respawn(panels)

    def _respawn(self, panels: 'UIManager'):
        s = self.state
        # Lepas pose tumbang — kalau tidak, pemain hidup lagi tapi tetap rebah.
        if hasattr(self.player, 'set_pose'):
            self.player.set_pose(None)
        s.hp = max(1, s.max_hp // 4)     # HP 25%
        s.energy = max(1, s.max_energy // 3)
        s.dungeon_level = 1              # kembali ke lantai 1

        # Hapus semua status efek
        self._status.clear()

        # Kembali ke entrance (tile 1,1 di dungeon)
        p = self.player
        try:
            p.set_tile_pos(2, 2)
        except Exception:
            pass

        if hasattr(p, '_anim') and p._anim:
            p._anim.force(AnimState.IDLE)

        if panels:
            panels.flash_msg("Kamu terbangun di pintu masuk gua.", 2.0)

        sound_play('respawn', 0.7)

    def _spawn_dmg_number(self, dmg: int, wx: float, wy: float, wz: float,
                          color_key: str = 'normal'):
        dn = _DamageNumber(dmg, wx, wy, wz, color_key)
        self._dmg_numbers.append(dn)

    def _check_quests(self, panels: 'UIManager'):
        """Panggil quest controller setelah kill."""
        p = self.player
        if hasattr(p, 'quest_controller') and p.quest_controller:
            p.quest_controller.check_quest_progress(panels)

    # ── Status queries ───────────────────────────────────────────────────────

    @property
    def is_slowed(self) -> bool:
        return 'slow' in self._status

    @property
    def is_stunned(self) -> bool:
        return 'stun' in self._status

    @property
    def speed_multiplier(self) -> float:
        if 'slow' in self._status:
            return 0.45
        return 1.0

    @property
    def combo_count(self) -> int:
        return self._combo_count

    @property
    def attack_ready(self) -> bool:
        return self._attack_cd <= 0

    @property
    def dodge_ready(self) -> bool:
        return self._dodge_cd <= 0


# ---------------------------------------------------------------------------
# Floating damage number (text entity Ursina sederhana)
# ---------------------------------------------------------------------------
class _DamageNumber:
    """Angka damage yang mengambang ke atas dan menghilang."""

    def __init__(self, value: int, wx: float, wy: float, wz: float,
                 color_key: str = 'normal'):
        self.alive = True
        self._t = 0.0
        self._ent = None

        COLOR_MAP = {
            'normal': (255, 60, 60),
            'crit':   (255, 200, 0),
            'player': (220, 80, 255),
        }
        r, g, b = COLOR_MAP.get(color_key, (255, 60, 60))

        try:
            from ursina import Text, color as ucolor
            txt = f"{'CRIT! ' if color_key == 'crit' else ''}{value}"
            scale = 1.8 if color_key == 'crit' else 1.2
            self._ent = Text(
                text=txt,
                position=(wx, wy, wz),
                scale=scale,
                color=ucolor.rgb(r, g, b),
                billboard=True,
                always_on_top=True,
            )
        except Exception:
            pass

    def tick(self, dt: float):
        self._t += dt
        if self._t > 1.2:
            self.alive = False
            try:
                from ursina import destroy
                destroy(self._ent)
            except Exception:
                pass
            return
        # Gerak ke atas + fade
        if self._ent:
            try:
                self._ent.y += dt * 0.9
                alpha = max(0, 1.0 - self._t / 1.2)
                self._ent.color = self._ent.color.tint(1, 1, 1, alpha)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Fungsi helper untuk dipakai entitas Monster (di entities.py)
# ---------------------------------------------------------------------------

def process_mob_attack(mob: Monster, player, dt: float,
                       combat_ctrl: CombatController,
                       panels: Optional['UIManager']):
    """
    Proses serangan mob ke player.
    Panggil dari EntitiesManager.update() gantikan logika lama di mob.update_ai().
    """
    if mob.hp <= 0 or mob.ai_state == MobState.DEAD:
        return

    s = player.state
    tx, ty = player.get_tile_pos()
    dist = math.hypot(mob.logical_x - tx, mob.logical_y - ty)

    if dist > mob.atk_r:
        return
    if mob.attack_cooldown_ms > 0:
        return

    # Pola serangan per mob
    pattern = MOB_ATTACK_PATTERN.get(mob.kind, {'cd': 1.0, 'dmg_mult': 1.0, 'special': None})
    raw_dmg = int(mob.damage * pattern['dmg_mult'])

    actual = combat_ctrl.receive_damage(raw_dmg, mob.kind, panels)

    if actual > 0 and pattern['special']:
        combat_ctrl.apply_status(pattern['special'], panels)

    # Animasi serangan mob (jika punya va)
    if actual > 0 and hasattr(mob, '_va') and mob._va:
        try:
            mob._va.set_animation('a2a-attack-loop-punch')
        except Exception:
            pass

    mob.attack_cooldown_ms = int(pattern['cd'] * 1000)
    mob.ai_state = MobState.ATTACK
