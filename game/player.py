"""
player.py — 3D Player controller untuk Ursina Engine.

Model: humanoid blocky (Rune Factory style):
  Badan, kepala, topi, lengan kiri/kanan, kaki kiri/kanan.
  Semua bagian adalah Entity child dari root Player3D.

Movement: WASD/Arrow di bidang XZ. Kamera tetap.
Tool system: SPACE untuk alat aktif di tile depan player.
Combat: Z untuk serang, radius PLAYER_ATTACK_RANGE world-units.
"""
import math
from pathlib import Path
from PIL import Image
from ursina import Entity, Vec3, Vec4, color, held_keys, time, invoke, destroy, lerp, Texture

from .config import (TILE_SIZE, GROUND_H, PLAYER_SPEED, PLAYER_RUN_MULTIPLIER,
                     PLAYER_ATTACK_RANGE, PLAYER_ATTACK_COOLDOWN_MS, TOOL_DAMAGE,
                     SPRINT_ENERGY_DRAIN,
                     INVULN_AFTER_HIT_MS, WALKABLE, TILLABLE, MINEABLE, TOOLS,
                     G, D, P, W, FL, DR, GT, CV_F, STR_T, DCK, LLY, MINED,
                     STAIRS_DOWN, STAIRS_UP, ORE_TBG, ORE_BSI, ORE_EMS,
                     ORE_KRS, ORE_MTH, CV_W, CRYS,
                     NEED_MAX, QUEUE_USER_DRIVEN)
from .data import CROPS, SWORD_RECIPES, QUEST_STAGES
from .sound import play as sound_play, get_step_sound
from .config import TILE_NAMES
from .pathfinder import PathGrid, PathMover
from .controllers.time_controller import TimeController
from .controllers.quest_controller import QuestController
from .controllers.interaction_controller import InteractionController

TS = TILE_SIZE
_GH = GROUND_H

# Proporsi dewasa bergaya FreeSO/Sims 1 — 6 kepala tinggi, total ~2.75 unit
_ANKLE_Y     = GROUND_H + 0.16
_KNEE_Y      = GROUND_H + 0.74
_HIP_Y       = GROUND_H + 1.40
_WAIST_Y     = GROUND_H + 1.58
_CHEST_Y     = GROUND_H + 1.78
_SHOULDER_Y  = GROUND_H + 1.96
_NECK_Y      = GROUND_H + 2.12
_HEAD_Y      = GROUND_H + 2.42

_THIGH_LEN      = _HIP_Y      - _KNEE_Y       # 0.66
_SHIN_LEN       = _KNEE_Y     - _ANKLE_Y      # 0.58
_UPPER_ARM_LEN  = 0.46
_FOREARM_LEN    = 0.38
_TORSO_Y        = (_HIP_Y + _SHOULDER_Y) * 0.5

# Palet hangat ala FreeSO — earth tones
SKIN_COLOR   = color.rgb(230, 190, 148)
BODY_COLOR   = color.rgb(175, 135,  95)   # default sebelum chargen
PANTS_COLOR  = color.rgb(105,  85,  62)
HAT_COLOR    = color.rgb(195, 152,  82)
SHOE_COLOR   = color.rgb( 90,  68,  45)

# Impor preset dari chargen agar apply_appearance bisa baca palette
from .chargen import (SKIN_PRESETS, HAIR_PRESETS, SHIRT_PRESETS,
                      PANTS_PRESETS, HAT_PRESETS)

_ASSET_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'textures'
_TEX_CACHE: dict = {}

def _tex(name: str):
    if not name:
        return None
    if name in _TEX_CACHE:
        return _TEX_CACHE[name]
    p = _ASSET_DIR / f'{name}.png'
    if p.exists():
        try:
            img = Image.open(p)
            t = Texture(img)
            t.filtering = False  # Bikin pixel-art tajam & warnanya keluar
            _TEX_CACHE[name] = t
            return t
        except Exception:
            pass
    return None

def _part_box(pos, scale, tint, parent):
    """Helper kecil: cube tanpa texture, sharp (no soft mesh, no shader bloat).
    Sesuai port dari three.js Sim character — semua part = box murni."""
    e = Entity(model='cube', position=pos, scale=scale, color=tint, parent=parent)
    from .smooth_shader import apply_smooth
    apply_smooth(e, has_texture=False)
    return e


def _part(model, pos, scale, tex_name, tint=color.white, parent=None):
    # HYBRID: cube/cylinder TETAP primitif Ursina (sharp Crossy Road style).
    # Token custom 'chibi_head' / 'chibi_torso' → mesh kepala/torso berdetil dengan bevel halus.
    # Cube/cylinder: jangan swap — biarkan primitif Ursina (sharp Crossy Road silhouette)
    if model == 'chibi_head':
        from .meshes import chibi_head_mesh
        model = chibi_head_mesh()
    elif model == 'chibi_torso':
        from .meshes import chibi_torso_mesh
        model = chibi_torso_mesh()
    t = _tex(tex_name)
    # Transparent hanya untuk warna dengan alpha < 255 (blush, dll.) — selain itu solid.
    has_alpha = hasattr(tint, 'w') and tint.w < 0.99
    kw = dict(model=model, position=pos, scale=scale, transparent=has_alpha)
    if t:
        kw['texture'] = t
        kw['color']   = tint
    else:
        kw['color'] = tint
    if parent:
        kw['parent'] = parent
    e = Entity(**kw)
    from .smooth_shader import apply_smooth
    apply_smooth(e, has_texture=bool(t))
    return e


class Player3D(Entity):
    """Player sebagai Ursina Entity. Root di y=0, semua bagian sebagai child."""

    def __init__(self, state, world):
        super().__init__()
        self.state = state
        self.world = world

        self.speed             = PLAYER_SPEED
        self.facing            = state.facing
        self._attack_cd        = 0.0    # ms
        self._invuln           = 0.0    # ms
        self._anim_t           = 0.0
        self._attack_anim      = 0.0
        self._anim_mode        = 'swing' # swing|down|water|bend
        self.target_rotation_y = 0.0
        self.velocity_x        = 0.0
        self.velocity_y        = 0.0
        self.velocity_z        = 0.0
        self.is_jumping        = False

        self.action_queue: list = []  # [(tx, ty, tool_idx, priority), ...]
        self._shirt_col = BODY_COLOR

        # Story system: pending messages delivered after scene transition
        self._pending_seasonal_event = None
        self._pending_lore_msg = None

        self.path_grid = None
        self.mover = None

        self._is_flying = False
        self._broom_ent = None
        self._slide_cooldown_ms = 0.0
        self._slide_active_ms = 0.0
        self._portal_cd = 0.0

        self.time_controller = TimeController(state)
        self.quest_controller = QuestController(state)
        self.interaction_controller = InteractionController(self, world)

        self._build_model()
        self.set_tile_pos(state.player_x, state.player_y)
        self.rebuild_pathgrid()
        self._set_initial_rotation()

    def rebuild_pathgrid(self):
        sc = self.world.scene_obj
        is_dungeon = (self.world.scene_name == 'dungeon' and self.state.dungeon_tiles)
        tiles = self.state.dungeon_tiles if is_dungeon else sc.tiles
        
        h = len(tiles)
        w = len(tiles[0]) if h > 0 else 0
        
        self.path_grid = PathGrid(width=w, height=h, tile_size=TS, allow_diagonal=True)
        for ty in range(h):
            for tx in range(w):
                tid = tiles[ty][tx]
                if tid not in WALKABLE:
                    self.path_grid.set_obstacle(tx, ty, False)
        
        self.mover = PathMover(self, self.path_grid, speed=self.speed)
        
        # Callback saat pindah tile untuk suara langkah
        def on_step(idx):
            tx_i, ty_i = self.get_tile_pos()
            if getattr(self, '_last_tile', None) != (tx_i, ty_i):
                self._last_tile = (tx_i, ty_i)
                tid = self.world.get_tile(tx_i, ty_i)
                sound_play(get_step_sound(TILE_NAMES.get(tid, 'grass')), 0.4)
                
        self.mover.on_step(on_step)

    def move_to_world(self, wx, wz):
        """Pindahkan player ke titik world (hasil klik mouse)."""
        if self.mover:
            # Gunakan speed lari jika shift ditahan
            run = held_keys['shift'] and self.state.energy > 0
            self.mover.speed = self.speed * (PLAYER_RUN_MULTIPLIER if run else 1.0)
            self.mover.move_to((wx, wz))

    def _set_initial_rotation(self):
        rot_map = {'up': 0, 'down': 180, 'left': -90, 'right': 90}
        self.rotation_y = rot_map.get(self.state.facing, 180)
        self.target_rotation_y = self.rotation_y

    # ─── MODEL BUILDING ──────────────────────────────────
    def _build_model(self):
        p = self

        # ── Drop shadow di tanah (flat quad gelap) ─────────────────────────────
        self._shadow = Entity(parent=p, model='quad',
                              position=Vec3(0, 0.02, 0),
                              rotation=(90, 0, 0),
                              scale=(0.95, 0.95, 1),
                              color=color.rgba(0, 0, 0, 120),
                              shader=None)

        self._is_vitaboy = True
        self._va = None

        # Dummy pivots for compatibility with existing item attachment logic
        PEL_Y, SHOULDER_Y = _GH + 0.96, _GH + 1.55
        self._pivot_hip_l = Entity(parent=p)
        self._pivot_hip_r = Entity(parent=p)
        self._pivot_knee_l = Entity(parent=p)
        self._pivot_knee_r = Entity(parent=p)
        self._pivot_shoulder_l = Entity(parent=p, position=Vec3(-0.30, SHOULDER_Y, 0))
        self._pivot_shoulder_r = Entity(parent=p, position=Vec3(0.30, SHOULDER_Y, 0))
        self.body = Entity(parent=p)
        self._pivot_neck = Entity(parent=p)

        try:
            from .vitaboy import VitaboyAvatar
            apr_list = [x for x in ['mabd000_leathers.apr', 'mahd000_proxy.apr', None] if x]
            self._va = VitaboyAvatar(self, apr_list, scale=0.32)
            self._va.set_animation("a2a-talk-idle-loop")
        except Exception as e:
            import logging
            logging.error(f"Failed to load Vitaboy for Player: {e}")
            self._is_vitaboy = False

            # Build full gorgeous voxel character fallback
            pants = PANTS_COLOR
            shoe  = SHOE_COLOR
            skin  = SKIN_COLOR
            cloth = self._shirt_col

            PEL_Y, WST_Y, CHEST_Y = _GH + 0.96, _GH + 1.16, _GH + 1.42
            NECK_Y, HEAD_Y        = _GH + 1.62, _GH + 1.89
            SHOULDER_Y, HIP_Y     = _GH + 1.55, _GH + 0.88

            # Destroy the default dummy body, and recreate body properly
            if hasattr(self, 'body') and self.body:
                destroy(self.body)

            # Build body boxes
            self.belt = _part_box(Vec3(0, PEL_Y, 0), (0.42, 0.18, 0.28), pants, parent=p)
            self.waist = _part_box(Vec3(0, WST_Y, 0), (0.40, 0.22, 0.26), cloth, parent=p)
            self.body = _part_box(Vec3(0, CHEST_Y, 0), (0.52, 0.30, 0.30), cloth, parent=p)

            # Neck & Head
            _part_box(Vec3(0, NECK_Y, 0), (0.14, 0.10, 0.14), skin, parent=p)
            if hasattr(self, '_pivot_neck') and self._pivot_neck:
                destroy(self._pivot_neck)
            self._pivot_neck = Entity(parent=p, position=Vec3(0, HEAD_Y, 0))
            self.head = _part_box(Vec3(0, 0, 0), (0.35, 0.45, 0.35), skin, parent=self._pivot_neck)

            # Surreal floating geometric halo
            self._halo_ring = Entity(model='cylinder', position=Vec3(0, 0.45, 0), scale=(0.5, 0.05, 0.5), color=color.rgb(255, 0, 255), parent=self._pivot_neck)
            self._halo_cube = Entity(model='cube', position=Vec3(0, 0.7, 0), scale=(0.15, 0.15, 0.15), color=color.rgb(0, 255, 255), parent=self._pivot_neck, rotation=(45, 45, 45))
            from .smooth_shader import apply_smooth
            apply_smooth(self._halo_ring, has_texture=False)
            apply_smooth(self._halo_cube, has_texture=False)

            # Destroy and recreate pivot shoulders & hips to have proper positions
            if hasattr(self, '_pivot_shoulder_l') and self._pivot_shoulder_l: destroy(self._pivot_shoulder_l)
            if hasattr(self, '_pivot_shoulder_r') and self._pivot_shoulder_r: destroy(self._pivot_shoulder_r)
            if hasattr(self, '_pivot_hip_l') and self._pivot_hip_l: destroy(self._pivot_hip_l)
            if hasattr(self, '_pivot_hip_r') and self._pivot_hip_r: destroy(self._pivot_hip_r)
            if hasattr(self, '_pivot_knee_l') and self._pivot_knee_l: destroy(self._pivot_knee_l)
            if hasattr(self, '_pivot_knee_r') and self._pivot_knee_r: destroy(self._pivot_knee_r)

            # Arms
            for side, sx in (('l', -1), ('r', 1)):
                piv_sh = Entity(parent=p, position=Vec3(sx * 0.30, SHOULDER_Y, 0))
                setattr(self, f'_pivot_shoulder_{side}', piv_sh)

                ua = _part_box(Vec3(0, -0.16, 0), (0.14, 0.32, 0.16), cloth, parent=piv_sh)
                setattr(self, f'upper_arm_{side}', ua)

                piv_el = Entity(parent=piv_sh, position=Vec3(0, -0.32, 0))
                setattr(self, f'_pivot_elbow_{side}', piv_el)

                fa = _part_box(Vec3(0, -0.15, 0), (0.13, 0.30, 0.14), skin, parent=piv_el)
                setattr(self, f'forearm_{side}', fa)

                hd = _part_box(Vec3(0, -0.36, 0), (0.14, 0.12, 0.14), skin, parent=piv_el)
                setattr(self, f'hand_{side}', hd)
                setattr(self, f'_arm_{side}', ua)

            # Legs
            for side, sx in (('l', -1), ('r', 1)):
                piv_hip = Entity(parent=p, position=Vec3(sx * 0.12, HIP_Y, 0))
                setattr(self, f'_pivot_hip_{side}', piv_hip)

                th = _part_box(Vec3(0, -0.21, 0), (0.18, 0.42, 0.22), pants, parent=piv_hip)
                setattr(self, f'thigh_{side}', th)

                piv_kn = Entity(parent=piv_hip, position=Vec3(0, -0.42, 0))
                setattr(self, f'_pivot_knee_{side}', piv_kn)

                sh_e = _part_box(Vec3(0, -0.20, 0), (0.17, 0.40, 0.20), pants, parent=piv_kn)
                setattr(self, f'shin_{side}', sh_e)

                foot = _part_box(Vec3(0, -0.45, 0.06), (0.20, 0.10, 0.32), shoe, parent=piv_kn)
                setattr(self, f'shoe_{side}', foot)
                setattr(self, f'_leg_{side}', th)

            self._walk_t = 0.0

    # ─── APPEARANCE (chargen) ────────────────────────────
    def apply_appearance(self, state):
        """Terapkan pilihan karakter dari chargen ke model yang sudah dibangun."""
        sk = getattr(state, 'char_skin',  0)
        hr = getattr(state, 'char_hair',  0)
        sh = getattr(state, 'char_shirt', 0)
        pn = getattr(state, 'char_pants', 0)
        ht = getattr(state, 'char_hat',   0)

        self._shirt_col = color.rgb(*SHIRT_PRESETS[sh][1]) if sh < len(SHIRT_PRESETS) else color.white

        if getattr(self, '_is_vitaboy', False) and hasattr(self, '_va') and self._va:
            body_apr = 'mabd000_leathers.apr' if sh == 0 else 'fabd000_sl__defaultpjs.apr'
            head_apr = 'mahd000_proxy.apr' if sh == 0 else 'fahd001_alt.apr'
            hair_apr = 'fahl003_longhair02.apr' if hr > 0 else None
            try:
                from .vitaboy import VitaboyAvatar
                if hasattr(self._va, 'root_entity') and self._va.root_entity:
                    destroy(self._va.root_entity)
                apr_list = [x for x in [body_apr, head_apr, hair_apr] if x]
                self._va = VitaboyAvatar(self, apr_list, scale=0.32)
                anim = "a2o-walking-loop" if getattr(self, '_was_moving', False) else "a2a-talk-idle-loop"
                self._va.set_animation(anim)
            except Exception:
                pass
        elif not getattr(self, '_is_vitaboy', True):
            # Update voxel colors dynamically
            cloth = self._shirt_col
            skin  = color.rgb(*SKIN_PRESETS[sk][1]) if sk < len(SKIN_PRESETS) else SKIN_COLOR
            pants = color.rgb(*PANTS_PRESETS[pn][1]) if pn < len(PANTS_PRESETS) else PANTS_COLOR
            
            if hasattr(self, 'waist') and self.waist: self.waist.color = cloth
            if hasattr(self, 'body') and self.body: self.body.color = cloth
            if hasattr(self, 'belt') and self.belt: self.belt.color = pants
            
            for side in ('l', 'r'):
                if hasattr(self, f'upper_arm_{side}') and getattr(self, f'upper_arm_{side}'):
                    getattr(self, f'upper_arm_{side}').color = cloth
                if hasattr(self, f'forearm_{side}') and getattr(self, f'forearm_{side}'):
                    getattr(self, f'forearm_{side}').color = skin
                if hasattr(self, f'hand_{side}') and getattr(self, f'hand_{side}'):
                    getattr(self, f'hand_{side}').color = skin
                if hasattr(self, f'thigh_{side}') and getattr(self, f'thigh_{side}'):
                    getattr(self, f'thigh_{side}').color = pants
                if hasattr(self, f'shin_{side}') and getattr(self, f'shin_{side}'):
                    getattr(self, f'shin_{side}').color = pants
            if hasattr(self, 'head') and self.head:
                self.head.color = skin

    # ─── POSITION HELPERS ────────────────────────────────
    def set_tile_pos(self, tx: float, ty: float):
        self.x = tx * TS
        self.y = 0
        self.z = ty * TS
        self._last_tile = (int(round(tx)), int(round(ty)))

    def get_tile_pos(self):
        return int(round(self.x / TS)), int(round(self.z / TS))

    def get_float_tile(self):
        return self.x / TS, self.z / TS

    # ─── TICK (dipanggil manual dari app.py saat mode='hud') ──
    def tick(self, dt: float = None, panels=None):
        if dt is None:
            dt = time.dt
        s = self.state
        if self._invuln > 0:
            self._invuln = max(0, self._invuln - dt * 1000)
        self._attack_anim= max(0.0, self._attack_anim- dt * 1000)
        s.invuln_timer_ms = self._invuln
        if self._portal_cd > 0.0:
            self._portal_cd = max(0.0, self._portal_cd - dt)

        # Slide/Dash Active Tick
        if hasattr(self, '_slide_active_ms') and self._slide_active_ms > 0:
            self._slide_active_ms = max(0.0, self._slide_active_ms - dt * 1000)
            # Spawn slide dust trail (beige particles)
            self._fx_burst(self.x, self.y + 0.1, self.z, color.rgb(230, 220, 200), n=2, spread=0.3)
            
        # Slide Cooldown Tick
        if hasattr(self, '_slide_cooldown_ms') and self._slide_cooldown_ms > 0:
            self._slide_cooldown_ms = max(0.0, self._slide_cooldown_ms - dt * 1000)

        # ── WASD MOVEMENT (kamera-relative isometric) ──────────────────────
        dx_in, dz_in = 0.0, 0.0
        if held_keys['w'] or held_keys['up arrow']:    dz_in += 1
        if held_keys['s'] or held_keys['down arrow']:  dz_in -= 1
        if held_keys['a'] or held_keys['left arrow']:  dx_in -= 1
        if held_keys['d'] or held_keys['right arrow']: dx_in += 1

        is_moving_wasd = False
        run = held_keys['shift'] and s.energy > 0
        
        # Sapoe Terbang flying speed boost!
        fly_boost = 2.2 if getattr(self, '_is_flying', False) else 1.0
        spd_factor = (PLAYER_RUN_MULTIPLIER if run else 1.0) * fly_boost
        max_speed = self.speed * spd_factor
        if getattr(self, '_slide_active_ms', 0) > 0:
            max_speed = max(max_speed, 38.0)
        
        ACCEL = 85.0 * spd_factor
        FRICTION = 6.0
        
        if dx_in or dz_in:
            # Normalisasi vector input
            mag = math.sqrt(dx_in * dx_in + dz_in * dz_in)
            dx_in /= mag; dz_in /= mag

            # Gerakan relatif terhadap arah kamera saat ini
            from ursina import camera
            cam_yaw = math.radians(camera.world_rotation_y)
            fwd_x   = math.sin(cam_yaw);  fwd_z   = math.cos(cam_yaw)
            right_x = math.cos(cam_yaw);  right_z = -math.sin(cam_yaw)
            mx = dz_in * fwd_x + dx_in * right_x
            mz = dz_in * fwd_z + dx_in * right_z

            self.velocity_x += mx * ACCEL * dt
            self.velocity_z += mz * ACCEL * dt
            is_moving_wasd = True

            # Hadapkan ke arah gerak (Ursina forward = +Z)
            self.rotation_y = math.degrees(math.atan2(self.velocity_x, self.velocity_z))

            # Energy drain saat lari
            if run:
                s.energy = max(0, s.energy - SPRINT_ENERGY_DRAIN * dt)

        # Apply friction
        self.velocity_x = lerp(self.velocity_x, 0, FRICTION * dt)
        self.velocity_z = lerp(self.velocity_z, 0, FRICTION * dt)

        # Clamp max speed
        v_mag = math.sqrt(self.velocity_x**2 + self.velocity_z**2)
        if v_mag > max_speed:
            self.velocity_x = (self.velocity_x / v_mag) * max_speed
            self.velocity_z = (self.velocity_z / v_mag) * max_speed

        if v_mag > 0.01:
            # Coba per-axis collision (sliding dengan padding/radius)
            radius = 0.26 * TS
            new_x = self.x + self.velocity_x * dt
            new_z = self.z + self.velocity_z * dt
            tx_new = int(round((new_x + math.copysign(radius, self.velocity_x)) / TS))
            tz_new = int(round((new_z + math.copysign(radius, self.velocity_z)) / TS))
            tx_cur, tz_cur = self.get_tile_pos()

            # Diagonal check: prevent clipping inside diagonal corner obstacles
            if self.world.is_walkable(tx_new, tz_cur) and self.world.is_walkable(tx_cur, tz_new):
                if self.world.is_walkable(tx_new, tz_new):
                    self.x = new_x
                    self.z = new_z
                else:
                    if abs(self.velocity_x) > abs(self.velocity_z):
                        self.x = new_x
                        self.velocity_z = 0.0
                    else:
                        self.z = new_z
                        self.velocity_x = 0.0
            else:
                if self.world.is_walkable(tx_new, tz_cur):
                    self.x = new_x
                else:
                    self.velocity_x = 0.0

                if self.world.is_walkable(tx_cur, tz_new):
                    self.z = new_z
                else:
                    self.velocity_z = 0.0

            # Suara langkah
            if is_moving_wasd:
                tx_i, tz_i = self.get_tile_pos()
                if getattr(self, '_last_tile', None) != (tx_i, tz_i):
                    self._last_tile = (tx_i, tz_i)
                    tid = self.world.get_tile(tx_i, tz_i)
                    sound_play(get_step_sound(TILE_NAMES.get(tid, 'grass')), 0.4)

        # PathMover hanya update kalau WASD tidak dipakai (fallback misal autopath)
        if self.mover and not is_moving_wasd:
            if self.mover.is_moving and self.mover.speed > self.speed:
                s.energy = max(0, s.energy - SPRINT_ENERGY_DRAIN * dt)
            self.mover.update(dt)
        elif self.mover and is_moving_wasd and self.mover.is_moving:
            # Batalkan pathfinding kalau player mulai WASD
            self.mover.stop()

        # Gabungkan moving state: WASD atau PathMover
        moving_now = is_moving_wasd or (self.mover and self.mover.is_moving)
        if moving_now:
            run = (is_moving_wasd and held_keys['shift'] and s.energy > 0) or \
                  (self.mover and self.mover.is_moving and self.mover.speed > self.speed)

            # Tentukan facing dari rotation_y (di-set oleh WASD atau PathMover)
            rot = self.rotation_y % 360
            if rot > 315 or rot <= 45:
                self.facing = 'up'
            elif rot > 45 and rot <= 135:
                self.facing = 'right'
            elif rot > 135 and rot <= 225:
                self.facing = 'down'
            else:
                self.facing = 'left'

        # Animation Handling
        if getattr(self, '_is_vitaboy', False) and hasattr(self, '_va') and self._va:
            if getattr(self, '_slide_active_ms', 0) > 0:
                self._va.set_animation('a2o-slide-normal')
                self._was_moving = False
                self._va.speed = 1.0
            elif getattr(self, '_is_flying', False):
                self._va.set_animation('a2o-broom-fly-leftside')
                self._was_moving = False
                self._va.speed = 1.0
            else:
                if moving_now:
                    if not getattr(self, '_was_moving', False):
                        self._va.set_animation('a2o-walking-loop')
                        self._was_moving = True
                    # Scale walk cycle speed to match velocity magnitude dynamically
                    self._va.speed = (v_mag / max(0.1, self.speed)) * 1.05
                else:
                    if getattr(self, '_was_moving', False):
                        self._va.set_animation('a2a-talk-idle-loop')
                        self._was_moving = False
                    self._va.speed = 1.0
            self._va.update(dt)
        elif not getattr(self, '_is_vitaboy', True):
            # Procedural Voxel Mannequin animations (Walk cycle & Idle & Halo)
            if not hasattr(self, '_walk_t'):
                self._walk_t = 0.0

            # Floating halo ring and cube rotation & bobbing
            if hasattr(self, '_halo_ring') and self._halo_ring:
                self._halo_ring.rotation_y += dt * 50
                self._halo_cube.rotation_x += dt * 70
                self._halo_cube.rotation_y += dt * 90
                self._halo_ring.y = 0.45 + math.sin(self._walk_t * 2.0) * 0.02
                self._halo_cube.y = 0.70 + math.cos(self._walk_t * 2.0) * 0.03

            if getattr(self, '_slide_active_ms', 0) > 0:
                # Slide pose for Voxel chibi
                self.body.rotation_x = lerp(self.body.rotation_x, -35, dt * 15)
                self.body.y = lerp(self.body.y, _GH + 0.8, dt * 15)
                if hasattr(self, '_pivot_hip_l') and self._pivot_hip_l:
                    self._pivot_hip_l.rotation_x = lerp(self._pivot_hip_l.rotation_x, 90, dt * 15)
                    self._pivot_hip_r.rotation_x = lerp(self._pivot_hip_r.rotation_x, 90, dt * 15)
                    self._pivot_knee_l.rotation_x = lerp(self._pivot_knee_l.rotation_x, 90, dt * 15)
                    self._pivot_knee_r.rotation_x = lerp(self._pivot_knee_r.rotation_x, 90, dt * 15)
                    self._pivot_shoulder_l.rotation_x = lerp(self._pivot_shoulder_l.rotation_x, -25, dt * 15)
                    self._pivot_shoulder_r.rotation_x = lerp(self._pivot_shoulder_r.rotation_x, -25, dt * 15)
            elif getattr(self, '_is_flying', False):
                # Flying pose for Voxel chibi
                self._walk_t += dt * 3.0
                t = self._walk_t
                
                # Bobbing body
                bob = math.sin(t) * 0.05
                self.body.y = (_GH + 1.42) + bob
                self._pivot_neck.y = _GH + 1.89 + bob
                self._pivot_shoulder_l.y = _GH + 1.55 + bob
                self._pivot_shoulder_r.y = _GH + 1.55 + bob
                
                # sitting-flying pose
                if hasattr(self, '_pivot_hip_l') and self._pivot_hip_l:
                    self._pivot_hip_l.rotation_x = lerp(self._pivot_hip_l.rotation_x, 65, dt * 8)
                    self._pivot_hip_r.rotation_x = lerp(self._pivot_hip_r.rotation_x, 65, dt * 8)
                    self._pivot_knee_l.rotation_x = lerp(self._pivot_knee_l.rotation_x, 40, dt * 8)
                    self._pivot_knee_r.rotation_x = lerp(self._pivot_knee_r.rotation_x, 40, dt * 8)
                    self._pivot_shoulder_l.rotation_x = lerp(self._pivot_shoulder_l.rotation_x, -40, dt * 8)
                    self._pivot_shoulder_r.rotation_x = lerp(self._pivot_shoulder_r.rotation_x, -40, dt * 8)
                    
                    if hasattr(self, '_pivot_elbow_l') and self._pivot_elbow_l:
                        self._pivot_elbow_l.rotation_x = lerp(self._pivot_elbow_l.rotation_x, -25, dt * 8)
                        self._pivot_elbow_r.rotation_x = lerp(self._pivot_elbow_r.rotation_x, -25, dt * 8)
                
                self.body.rotation_x = lerp(self.body.rotation_x, 15, dt * 8)
                self.body.rotation_z = math.sin(t) * 3  # gentle sway
            elif moving_now:
                # Scale walk animation frequency based on actual velocity
                speed_ratio = v_mag / max(0.1, self.speed)
                self._walk_t += dt * (7.0 + speed_ratio * 9.0)
                t = self._walk_t
                swing = math.sin(t) * 45

                if hasattr(self, '_pivot_hip_l') and self._pivot_hip_l:
                    # Shoulders & Hips (Opposite swing)
                    self._pivot_shoulder_l.rotation_x = -swing
                    self._pivot_shoulder_r.rotation_x = swing
                    self._pivot_hip_l.rotation_x = swing
                    self._pivot_hip_r.rotation_x = -swing

                    # Elbows (Bend slightly when swinging forward)
                    if hasattr(self, '_pivot_elbow_l') and self._pivot_elbow_l:
                        self._pivot_elbow_l.rotation_x = -max(0, math.sin(t)) * 30
                        self._pivot_elbow_r.rotation_x = -max(0, -math.sin(t)) * 30

                    # Knees (Bend backwards primarily when lifting the leg to step forward)
                    if hasattr(self, '_pivot_knee_l') and self._pivot_knee_l:
                        self._pivot_knee_l.rotation_x = max(0, math.sin(t)) * 50
                        self._pivot_knee_r.rotation_x = max(0, -math.sin(t)) * 50

                    # Body Lean and Bob
                    lean = 5.0 + speed_ratio * 15.0  # Dynamic lean based on speed (lean forward more when running)
                    self.body.rotation_x = lean
                    bob = abs(math.sin(t)) * (0.08 + speed_ratio * 0.08)  # Dynamic bobbing based on speed
                    self.body.y = (_GH + 1.42) + bob
                    self._pivot_neck.y = _GH + 1.89 + bob
                    self._pivot_shoulder_l.y = _GH + 1.55 + bob
                    self._pivot_shoulder_r.y = _GH + 1.55 + bob
            else:
                # Idle bobbing
                self._walk_t += dt * 1.8
                t = self._walk_t
                if hasattr(self, '_pivot_hip_l') and self._pivot_hip_l:
                    self._pivot_hip_l.rotation_x = lerp(self._pivot_hip_l.rotation_x, 0, dt * 10)
                    self._pivot_hip_r.rotation_x = lerp(self._pivot_hip_r.rotation_x, 0, dt * 10)
                    self._pivot_shoulder_l.rotation_x = lerp(self._pivot_shoulder_l.rotation_x, 0, dt * 10)
                    self._pivot_shoulder_r.rotation_x = lerp(self._pivot_shoulder_r.rotation_x, 0, dt * 10)

                    if hasattr(self, '_pivot_elbow_l') and self._pivot_elbow_l:
                        self._pivot_elbow_l.rotation_x = lerp(self._pivot_elbow_l.rotation_x, 0, dt * 10)
                        self._pivot_elbow_r.rotation_x = lerp(self._pivot_elbow_r.rotation_x, 0, dt * 10)
                    if hasattr(self, '_pivot_knee_l') and self._pivot_knee_l:
                        self._pivot_knee_l.rotation_x = lerp(self._pivot_knee_l.rotation_x, 0, dt * 10)
                        self._pivot_knee_r.rotation_x = lerp(self._pivot_knee_r.rotation_x, 0, dt * 10)

                    self.body.rotation_x = lerp(self.body.rotation_x, 0, dt * 10)
                    breathe = math.sin(t) * 0.015
                    self.body.y = (_GH + 1.42) + breathe
                    self._pivot_neck.y = _GH + 1.89 + breathe
                    self._pivot_shoulder_l.y = _GH + 1.55 + breathe
                    self._pivot_shoulder_r.y = _GH + 1.55 + breathe

        # Animasi alat/serangan — per mode
        if self._attack_anim > 0:
            t  = self._attack_anim / 350.0
            # Gaya voxel: ayunan kaku linier (segitiga 0 -> 1 -> 0), bukan gelombang sinus halus
            st = 1.0 - abs(t * 2.0 - 1.0)
            m  = self._anim_mode
            
            # Tubuh dipertahankan kaku tegak (kecuali saat menambang keras)
            if m != 'mine':
                self.body.rotation_x = 0
            
            va_root = None
            if getattr(self, '_is_vitaboy', False) and hasattr(self, '_va') and self._va:
                va_root = self._va.root_entity
            
            if m == 'swing':
                self._pivot_shoulder_r.rotation_x = -100 * st
                self._pivot_shoulder_r.rotation_z = 0
                if va_root: va_root.rotation_x = -45 * st
            elif m == 'mine':
                # Swing right arm back far and strike down aggressively
                self._pivot_shoulder_r.rotation_x = -160 * st
                self._pivot_shoulder_r.rotation_z = -15 * st
                # Bend right elbow slightly at the peak of the strike
                if hasattr(self, '_pivot_elbow_r') and self._pivot_elbow_r:
                    self._pivot_elbow_r.rotation_x = -st * 35
                # Lean torso forward at impact peak to show weight and power!
                self.body.rotation_x = st * 18
                if va_root: va_root.rotation_x = -80 * st
            elif m == 'down':
                self._pivot_shoulder_r.rotation_x = -135 * st
                self._pivot_shoulder_l.rotation_x = 0
                if va_root: va_root.rotation_x = -70 * st
            elif m == 'water':
                self._pivot_shoulder_r.rotation_x = -70 * t
                self._pivot_shoulder_l.rotation_x = 0
                if va_root: va_root.rotation_x = -35 * st
            elif m == 'bend':
                self._pivot_shoulder_r.rotation_x = -85 * st
                self._pivot_shoulder_l.rotation_x = -85 * st
                if va_root: va_root.rotation_x = -45 * st
        else:
            self._pivot_shoulder_r.rotation_z = 0
            if moving_now and not getattr(self, '_is_vitaboy', True):
                pass # let walk cycle govern rotation_x
            else:
                self._pivot_shoulder_r.rotation_x = lerp(self._pivot_shoulder_r.rotation_x, 0, dt * 10)
                self._pivot_shoulder_l.rotation_x = lerp(self._pivot_shoulder_l.rotation_x, 0, dt * 10)
            self.body.rotation_x = lerp(self.body.rotation_x, 0, dt * 10)
            if getattr(self, '_is_vitaboy', False) and hasattr(self, '_va') and self._va:
                self._va.root_entity.rotation_x = 0

        # ── python-2d-game health_and_mana.py pattern: passive HP regen ──
        if s.hp < s.max_hp:
            regen = s.hp_regen_rate
            if s.buffs.get('regen', 0) > 0:
                regen *= 3.5   # wild_herb buff: regen 3.5×
            s.hp = min(s.max_hp, s.hp + regen * dt)

        # ── Buff tick (python-2d-game AbstractBuffEffect.apply_middle_effect) ──
        for buff_name in list(s.buffs.keys()):
            s.buffs[buff_name] = max(0, s.buffs[buff_name] - dt * 1000)
            if s.buffs[buff_name] <= 0:
                del s.buffs[buff_name]

        # Invuln: kedip merah
        if self._invuln > 0:
            blink = int(self._invuln / 80) % 2 == 0
            self.body.color = color.rgb(255, 80, 80, 102) if blink else Vec4(self._shirt_col[0], self._shirt_col[1], self._shirt_col[2], 0.4)
        else:
            self.body.color = Vec4(self._shirt_col[0], self._shirt_col[1], self._shirt_col[2], 0.4)

        # Sync state
        s.player_x = self.x / TS
        s.player_y = self.z / TS
        s.facing   = self.facing

        # Terrain following & Gravity
        tx_i, ty_i = int(round(self.x / TS)), int(round(self.z / TS))
        target_y = self.world.get_surface_height(tx_i, ty_i)
        
        if getattr(self, '_is_flying', False):
            # Float at 1.25 units smoothly above surface with sin bobbing
            if not hasattr(self, '_fly_time'):
                self._fly_time = 0.0
            self._fly_time += dt * 4.0
            ideal_fly_y = target_y + 1.25 + math.sin(self._fly_time) * 0.15
            self.y = lerp(self.y, ideal_fly_y, min(1.0, dt * 6.0))
            self.velocity_y = 0.0
            self.is_jumping = False
        elif self.is_jumping:
            GRAVITY = -30.0
            self.velocity_y += GRAVITY * dt
            self.y += self.velocity_y * dt
            if self.y <= target_y:
                self.y = target_y
                self.velocity_y = 0.0
                self.is_jumping = False
        else:
            self.y = lerp(self.y, target_y, min(1.0, dt * 14))
            
        # Broom Flying neon trailing particle sparks when moving
        if getattr(self, '_is_flying', False) and v_mag > 0.5:
            import random as _rng_mod
            rad_angle = math.radians(self.rotation_y)
            tail_x = self.x - math.sin(rad_angle) * 1.2
            tail_z = self.z - math.cos(rad_angle) * 1.2
            tail_y = self.y + 0.4
            # Neon sparks: cyan, magenta, or yellow
            spark_col = _rng_mod.choice([color.rgb(0, 255, 255), color.rgb(255, 0, 255), color.rgb(255, 255, 0)])
            self._fx_burst(tail_x, tail_y, tail_z, spark_col, n=1, spread=0.1)

        # Check portals every tick unconditionally so cooldowns don't block standing players
        self._check_portals(tx_i, ty_i)

    def _reset_anim(self):
        for piv in (self._pivot_hip_l, self._pivot_hip_r,
                    self._pivot_knee_l, self._pivot_knee_r,
                    self._pivot_shoulder_l, self._pivot_shoulder_r):
            if abs(piv.rotation_x) > 0.5:
                piv.rotation_x *= 0.75
            else:
                piv.rotation_x = 0

    # ─── INPUT ACTIONS ───────────────────────────────────
    def handle_input(self, key, entities_mgr, panels):
        """Dipanggil dari app.py saat mode='play'.
        Return True jika input dikonsumsi."""
        s = self.state

        if key == 'left alt':
            if not self.is_jumping and not getattr(self, '_is_flying', False):
                self.is_jumping = True
                self.velocity_y = 12.0
            return True

        if key == 'b':
            self.toggle_broom_flying(panels)
            return True

        if key == 'y':
            self.trigger_slide_stunt(panels)
            return True

        if key == 'space':
            self.interaction_controller.use_tool(entities_mgr, panels)
            return True

        if key == 'e':
            self.interaction_controller.interact(entities_mgr, panels)
            return True

        if key == 'z':
            self.interaction_controller.attack(entities_mgr, panels)
            return True

        if key == 'f':
            self.interaction_controller.capture(entities_mgr, panels)
            return True

        if key == 't':
            self._try_sleep(panels)
            return True

        if key == 'v':
            self.interaction_controller.consume_item(panels)
            return True

        if key == 'g':
            self.give_gift(entities_mgr, panels)
            return True

        if key == 'x':
            self.queue_toggle(panels)
            return True

        if key == 'c':
            self.queue_execute(entities_mgr, panels)
            return True

        if key.isdigit():
            n = int(key)
            if 1 <= n <= len(TOOLS):
                s.tool_index = n - 1
                sound_play('menu_move', 0.6)
                return True

        if key == 'q':
            keys = list(CROPS.keys())
            idx  = keys.index(s.seed_key) if s.seed_key in keys else 0
            s.seed_key = keys[(idx - 1) % len(keys)]
            sound_play('menu_move', 0.6)
            return True

        if key == 'r':
            keys = list(CROPS.keys())
            idx  = keys.index(s.seed_key) if s.seed_key in keys else 0
            s.seed_key = keys[(idx + 1) % len(keys)]
            sound_play('menu_move', 0.6)
            return True

        return False

    # ─── PRIVATE: PORTAL & DUNGEON ───────────────────────
    def _check_portals(self, tx_i, ty_i) -> bool:
        import logging
        s = self.state
        sc = self.world.scene_obj
        # Cooldown setelah transition supaya WASD held tidak ulang-ulang
        if getattr(self, '_portal_cd', 0.0) > 0.0:
            return False

        # 1. Cek Portal Normal
        if sc and hasattr(sc, 'portals'):
            for (px, py, t_scene, tx, ty) in sc.portals:
                if tx_i == px and ty_i == py:
                    logging.info(f"[PORTAL] dari {s.scene_name}({tx_i},{ty_i}) → {t_scene}({tx},{ty})")
                    s.scene_name = t_scene
                    s.player_x = float(tx)
                    s.player_y = float(ty)
                    self.x = float(tx) * TS
                    self.z = float(ty) * TS
                    sound_play('step_floor', 0.8)
                    self._portal_cd = 0.8  # 0.8 detik cooldown
                    return True

        # 2. Cek Tangga Dungeon
        if s.scene_name == 'dungeon':
            tid = self.world.get_tile(tx_i, ty_i)
            if tid == STAIRS_DOWN:
                s.dungeon_level += 1
                if s.dungeon_level > s.stats.get('deepest_level', 0):
                    s.stats['deepest_level'] = s.dungeon_level
                self._generate_and_enter_dungeon()
                self.x = float(s.player_x) * TS
                self.z = float(s.player_y) * TS
                self._portal_cd = 0.8
                return True
            elif tid == STAIRS_UP:
                s.dungeon_level -= 1
                if s.dungeon_level <= 0:
                    s.scene_name = 'naga_cave'
                    s.player_x = 12.0
                    s.player_y = 10.0
                    self.x = 12.0 * TS
                    self.z = 10.0 * TS
                    sound_play('step_floor', 0.8)
                else:
                    self._generate_and_enter_dungeon()
                    self.x = float(s.player_x) * TS
                    self.z = float(s.player_y) * TS
                self._portal_cd = 0.8
                return True
        # Masuk dungeon dari Gua Naga
        elif s.scene_name == 'naga_cave':
            tid = self.world.get_tile(tx_i, ty_i)
            if tid == STAIRS_DOWN:
                s.scene_name = 'dungeon'
                s.dungeon_level = 1
                self._generate_and_enter_dungeon()
                self.x = float(s.player_x) * TS
                self.z = float(s.player_y) * TS
                self._portal_cd = 0.8
                return True
                
        return False

    def _generate_and_enter_dungeon(self):
        s = self.state
        from .dungeon import generate_dungeon_level
        grid, px, py, mobs = generate_dungeon_level(s.dungeon_level)
        s.dungeon_tiles = grid
        s.player_x = float(px)
        s.player_y = float(py)
        s.mobs = mobs
        sound_play('step_floor', 0.8)
        # ── Lore pickup at specific dungeon levels ──
        self.quest_controller.check_dungeon_lore(s.dungeon_level, self)

    def _play_tool_anim(self, mode='swing'):
        self._attack_anim = 350
        self._anim_mode   = mode

    def _fx_burst(self, wx, wy, wz, col, n=5, spread=0.45, dur=0.38):
        """Partikel ledakan singkat di posisi world — efek visual alat/serangan."""
        import random as _r
        for _ in range(n):
            ox = _r.uniform(-spread, spread)
            oy = _r.uniform(0.05, spread)
            oz = _r.uniform(-spread, spread)
            e = Entity(model='sphere',
                       position=(wx + ox, wy + oy, wz + oz),
                       scale=_r.uniform(0.08, 0.18), color=col)
            invoke(destroy, e, delay=dur)

    def _animate_falling_tree(self, wx, wz, tid):
        """Spawns a temporary visual tree replica that falls over and sinks into the ground."""
        from ursina import Entity, destroy, Vec3, color
        from .config import TREE_H, TR, DT
        
        # Create a falling tree pivot entity at ground level
        falling_root = Entity(position=(wx, 0, wz))
        
        # Build matching visual replica components
        if tid == TR:
            # Trunk
            Entity(model='cylinder', parent=falling_root, position=(0, TREE_H * 0.40, 0),
                   scale=(TS * 0.35, TREE_H * 0.80, TS * 0.35), color=color.rgb(100, 70, 40))
            # Foliage
            Entity(model='sphere', parent=falling_root, position=(0, TREE_H * 1.0, 0),
                   scale=(TS * 1.8, TS * 1.5, TS * 1.8), color=color.rgb(95, 200, 65))
            Entity(model='sphere', parent=falling_root, position=(TS*0.2, TREE_H * 1.4, -TS*0.2),
                   scale=(TS * 1.4, TS * 1.2, TS * 1.4), color=color.rgb(105, 220, 75))
            Entity(model='sphere', parent=falling_root, position=(-TS*0.2, TREE_H * 1.3, TS*0.2),
                   scale=(TS * 1.2, TS * 1.1, TS * 1.2), color=color.rgb(115, 240, 85))
        elif tid == DT:
            # Trunk only for dead tree
            Entity(model='cylinder', parent=falling_root, position=(0, TREE_H * 0.40, 0),
                   scale=(TS * 0.22, TREE_H * 0.80, TS * 0.22), color=color.rgb(68, 50, 30))

        # Calculate fall target rotation away from player based on facing direction
        rot_target = Vec3(0, 0, 0)
        if self.facing == 'up':
            rot_target = Vec3(75, 0, 0)
        elif self.facing == 'down':
            rot_target = Vec3(-75, 0, 0)
        elif self.facing == 'left':
            rot_target = Vec3(0, 0, -75)
        elif self.facing == 'right':
            rot_target = Vec3(0, 0, 75)
        
        # Smooth ease-in-out rotation tilt
        falling_root.animate_rotation(rot_target, duration=0.8, curve='ease_in_out')
        # Sinks slowly into the ground after hitting the floor
        falling_root.animate_y(-2.5, duration=1.2, delay=0.6, curve='ease_in')
        
        # Destroy visual dummy once animation completes
        invoke(destroy, falling_root, delay=1.8)

    # ─── PRIVATE: TOOL ───────────────────────────────────
    def _facing_tile(self):
        tx, ty = self.get_tile_pos()
        # Camera-relative: standard cardinal axes for straight behind camera follow
        dmap = {'up': (0, 1), 'down': (0, -1), 'left': (-1, 0), 'right': (1, 0)}
        dx, dz = dmap.get(self.facing, (1, 1))
        return tx + dx, ty + dz

    def _spend_energy(self, n: int):
        actual = max(1, round(n * self.state.mood_energy_multiplier()))
        self.state.energy = max(0, self.state.energy - actual)

    def _try_sleep(self, panels):
        self.time_controller.try_sleep(panels, self)

    def give_gift(self, entities_mgr, panels):
        self.interaction_controller.give_gift(entities_mgr, panels)

    def complete_gift_gifting(self, npc_id, panels):
        self.interaction_controller.complete_gift_gifting(npc_id, panels)

    def _build_pie_options(self, npc_id: str) -> list:
        return self.interaction_controller.build_pie_options(npc_id)

    def execute_pie_action(self, npc_id: str, action: str, entities_mgr, panels):
        self.interaction_controller.execute_pie_action(npc_id, action, entities_mgr, panels)

    def queue_toggle(self, panels):
        self.interaction_controller.queue_toggle(panels)

    def queue_execute(self, entities_mgr, panels):
        self.interaction_controller.queue_execute(entities_mgr, panels)

    def _add_lore(self, lore_id, panels=None):
        self.quest_controller.add_lore(lore_id, self, panels)

    def check_npc_lore_gift(self, npc_id, panels):
        self.quest_controller.check_npc_lore_gift(npc_id, self, panels)

    def toggle_broom_flying(self, panels=None):
        self.interaction_controller.toggle_broom_flying(panels)

    def trigger_slide_stunt(self, panels=None):
        self.interaction_controller.trigger_slide_stunt(panels)
