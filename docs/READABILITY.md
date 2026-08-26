# READABILITY.md — What lets a player understand a Lembah Karsa scene at a glance

**Status:** build spec. Every number here is either measured out of this repo or
derived from the projection math in §1, and the derivation is shown.
**Audience:** whoever touches `game/app.py` (camera), `game/world.py` (tiles,
walls, decoration), `game/panels.py` (feedback), `game/entities.py` (actors),
`game/smooth_shader.py` (outline), `game/scenes/props.py` (props).
**Sibling docs:** `docs/CODE_MAP.md` (the honest audit), `docs/ENTITY_VISUAL_LANGUAGE.md`
(what the entity is allowed to look like), `docs/BAR_STRANGERVILLE.md` (mystery structure).

---

## 0. The premise this document is built on

The owner's redirection is the whole brief: **playable, decent-looking, clear.**
Readability is the part of "decent-looking" that is actually **function**. A life
sim is a game of *noticing*: you notice a need is falling, you notice the stove is
free, you notice the neighbour walked in, you notice the crop is ripe. Every one of
those is a perception task the screen either supports or sabotages.

So the test for every rule below is not "is it pretty" but:

> **Can a player who has never seen this screen name, within two seconds, (a) where
> they are, (b) what can be used, and (c) what the game is currently doing?**

A screenshot that passes that test and looks plain beats a screenshot that looks
lush and fails it. Our current build fails all three: the camera is near-eye-level
so you cannot see the lot, walls are solid so you cannot see inside, and 30% of
grass tiles carry a neon magenta cylinder so you cannot tell decoration from a
thing you can use.

---

# 1. Camera

## 1.1 Why isometric/dimetric, stated as function not taste

A lot-based life sim asks the player to hold a **spatial plan** in their head — this
room connects to that room, the stove is there, the bed is there, the neighbour is
walking from the door toward the sofa. Three properties decide whether the camera
supports that:

**(a) Constant scale.** Under perspective, an object's screen size depends on its
distance, so the same chair is 40 px near the camera and 12 px at the back of the
lot. The player cannot use size as a cue for anything else — not importance, not
category, not "is it near me". Under orthographic projection one world unit is a
fixed pixel count everywhere on screen:

```
px_per_world_unit = SCREEN_H / camera.fov        # ortho only
```

That single equation is worth more than every shader in this repo. It means you can
*specify UI in pixels* — name labels, progress bars, selection rings, thought
balloons — and they will be that size at every position on the lot. It also directly
kills the giant-billboard-name problem (`game/entities.py:242-245`, `scale=5`
billboard `Text`): the reason those labels are absurd is that they were tuned at one
distance under perspective.

**(b) A stable ground grid.** A near-horizontal camera (our starting pitch was 12°,
now 34° — `game/app.py:190`) compresses the ground plane into a thin band. Depth
along the view axis costs almost no vertical pixels, so two tiles 6 apart in depth
land 20 px apart on screen and the player cannot count tiles, cannot judge "is that
chair in this room or the next", and cannot aim a click. A dimetric camera spends a
fixed, generous number of pixels per tile of depth (§1.2 gives the number: 73 px at
the default zoom) — the grid becomes countable, and countable is the same thing as
plannable.

**(c) Four discrete rotations instead of free-look.** Free mouse-look
(`game/app.py:299-311`) is a continuous variable the player must *manage*. Every
frame they are half-thinking about the camera instead of the game. Four fixed
90°-apart steps make the camera a **fact** rather than a task: the player learns
"north-east view" once, the lot has four canonical readings, and — critically — you
can precompute per-wall occlusion state for exactly four cases (§2.4) instead of
recomputing every frame.

The counter-argument for a follow cam is immersion in the character. That is the
Rune-Factory game this repo currently is, and it is not the game being built. A life
sim's protagonist is the *household*, not the body.

**Bottom line:** dimetric orthographic is chosen because it makes scale constant,
depth countable, and occlusion precomputable. Those are three engineering
properties, not an art style.

## 1.2 The exact geometry: why pitch is 30°, not 34, not 45

Put the camera at yaw 45° (looking down a diagonal of the tile grid) and pitch θ
below horizontal, orthographic. A tile edge of world length `s` projects onto the
image plane as:

```
screen-horizontal extent = s · cos(45°)              = 0.7071 s
screen-vertical   extent = s · sin(45°) · sin(θ)     = 0.7071 s · sin(θ)
```

A tile therefore draws as a diamond of

```
width  = 2 · s · cos 45°           = 1.41421 s
height = 2 · s · sin 45° · sin θ   = 1.41421 s · sin θ
```

so `width / height = 1 / sin θ`. Setting that to **2:1** gives `sin θ = 0.5`, i.e.

```
DIMETRIC_PITCH = 30.0°      # exactly arcsin(0.5)
```

For reference, other pitches and the diamond they produce:

| pitch | width:height | reads as |
|---:|---:|---|
| 26.57° (atan 0.5) | 2.24 : 1 | flatter, more "map" |
| **30.00°** | **2.00 : 1** | **The Sims 1 / SimCity 2000 dimetric — our target** |
| 35.264° (atan 1/√2) | 1.73 : 1 | true isometric, all three axes equally foreshortened |
| 45° | 1.41 : 1 | almost top-down; walls and character faces vanish |

With `TILE_SIZE = 2.0` (`game/config.py:10`), one tile diamond is **2.828 × 1.414
world units** on the image plane, and a vertical world segment of height `h`
projects to `h · cos 30° = 0.866 h` image-plane units.

### Zoom steps, in numbers you can check against a screenshot

`camera.fov` under orthographic is **the vertical film size in world units** —
Ursina calls `orthographic_lens.set_film_size(fov * aspect, fov)`
(`ursina/camera.py:110`). So:

| step | `fov` | px/unit @1080p | tiles visible (W×H) | tile diamond on screen | 1.8 m character |
|---|---:|---:|---:|---:|---:|
| 0 "room" | 14 | 77.1 | 8.8 × 9.9 | 218 × 109 px | 120 px tall |
| 1 "house" (default) | 21 | 51.4 | 13.2 × 14.8 | 146 × 73 px | 80 px tall |
| 2 "lot" | 32 | 33.8 | 20.1 × 22.6 | 95 × 48 px | 52 px tall |

Sanity checks these numbers buy you:

- `farm` is 25 × 18 tiles. Step 2 shows essentially the whole lot; step 1 shows
  about half. That is the right split — the Sims 1 zoom ladder is exactly
  "room / house / lot".
- Wall height `WALL_H = 2.8` (`game/config.py:12`) → `2.8 · 0.866 = 2.42` units →
  **125 px** at the default zoom. That is a wall you can read as a wall.
- Cutaway stub `CUTAWAY_STUB = 0.42` (`game/world.py:344`) → **19 px**, which is
  24% of the character's 80 px. That is the correct proportion: high enough to
  draw the room's floorplan, low enough that it never hides a body. **Keep 0.42.**
- Below ~45 px of character height a Vitaboy avatar stops being legible as a
  person. That sets zoom step 2 as the far limit; do not add a step 3.

## 1.3 The exact setup code

Two files. First a new `game/camera_rig.py` — one place that owns the projection,
so `CAM_HEIGHT` / `CAM_BACK` (`game/config.py:24-25`, dead constants nothing reads)
can finally be deleted rather than left to rot:

```python
"""camera_rig.py — Kamera dimetrik 2:1 ortografis ala life-sim.

Satu-satunya sumber kebenaran untuk proyeksi. Ganti nilai di sini, jangan di
app.py. Empat langkah rotasi + tiga langkah zoom, tanpa free-look.

Turunan sudut ada di docs/READABILITY.md §1.2:
    lebar:tinggi belah ketupat tile = 1 / sin(pitch)
    2:1  ->  sin(pitch) = 0.5  ->  pitch = 30 derajat tepat.
"""
import math
from ursina import camera, Vec3

from .config import TILE_SIZE

# ── Konstanta proyeksi ────────────────────────────────────────────
DIMETRIC_PITCH = 30.0                          # arcsin(0.5); jangan diubah tanpa
                                               # menghitung ulang tabel di §1.2
YAW_STEPS      = (45.0, 135.0, 225.0, 315.0)   # empat pandangan kanonik
ZOOM_STEPS     = (14.0, 21.0, 32.0)            # film height (world unit): room/house/lot
DEFAULT_ZOOM   = 1

# Jarak kamera dari fokus. Di ortografis ini TIDAK mempengaruhi skala sama
# sekali (zoom = camera.fov). Ia hanya menentukan urutan clip, dan dengan near
# plane negatif di bawah pun itu tidak lagi penting. Ambil nilai besar supaya
# tidak ada geometri lot yang jatuh di belakang bidang kamera.
CAM_DIST       = 60.0

# Near/far dipasang LANGSUNG ke orthographic_lens, bukan lewat
# camera.clip_plane_near — lihat §1.4 gotcha (2).
ORTHO_NEAR     = -500.0                        # negatif = tidak ada near-clipping
ORTHO_FAR      =  2000.0

# Ukuran belah ketupat satu tile di bidang gambar (world unit).
TILE_DIAMOND_H = 2.0 * TILE_SIZE * math.sin(math.radians(45.0)) \
                     * math.sin(math.radians(DIMETRIC_PITCH))
TILE_DIAMOND_W = 2.0 * TILE_SIZE * math.cos(math.radians(45.0))


def px_per_world_unit(screen_h: int) -> float:
    """Berapa piksel satu world unit. Konstan di seluruh layar — hanya benar
    di proyeksi ortografis, dan inilah alasan utama kita memakainya."""
    return screen_h / camera.fov


def fov_for_tiles(n_tiles_vertical: float) -> float:
    """Kebalikan tabel zoom: berapa fov supaya n tile muat vertikal."""
    return n_tiles_vertical * TILE_DIAMOND_H


class CameraRig:
    """Pemilik proyeksi + langkah yaw/zoom + follow ber-deadzone."""

    def __init__(self, focus: Vec3):
        self.yaw_step  = 0
        self.zoom_step = DEFAULT_ZOOM
        self.focus     = Vec3(focus)
        self._yaw_shown = YAW_STEPS[0]      # yaw yang sedang tampil (di-tween)
        self.apply_projection()
        self.snap()

    # ── Proyeksi ──────────────────────────────────────────────────
    def apply_projection(self):
        camera.orthographic = True
        camera.fov = ZOOM_STEPS[self.zoom_step]
        # WAJIB: camera.clip_plane_* menulis ke lensa perspektif, bukan ortho.
        camera.orthographic_lens.set_near_far(ORTHO_NEAR, ORTHO_FAR)

    def on_window_resize(self):
        """Film size ortho hanya dihitung ulang di fov_setter, jadi setelah
        window resize aspect ratio berubah tapi film size tidak ikut. Set ulang
        fov ke nilainya sendiri untuk memaksa perhitungan ulang."""
        camera.fov = camera.fov
        camera.orthographic_lens.set_near_far(ORTHO_NEAR, ORTHO_FAR)

    # ── Langkah rotasi & zoom ─────────────────────────────────────
    def rotate(self, direction: int) -> int:
        self.yaw_step = (self.yaw_step + direction) % 4
        return self.yaw_step                 # pemanggil pakai ini untuk cutaway

    def zoom(self, direction: int) -> int:
        self.zoom_step = max(0, min(len(ZOOM_STEPS) - 1, self.zoom_step + direction))
        camera.fov = ZOOM_STEPS[self.zoom_step]
        camera.orthographic_lens.set_near_far(ORTHO_NEAR, ORTHO_FAR)
        return self.zoom_step

    @property
    def yaw(self) -> float:
        return YAW_STEPS[self.yaw_step]

    # ── Penempatan ────────────────────────────────────────────────
    def offset(self, yaw_deg: float) -> Vec3:
        """Konvensi sama persis dengan Game3D._camera_offset lama (app.py:634)
        supaya basis gerak pemain di player.py:433-437 tidak perlu diubah."""
        cy = math.radians(yaw_deg)
        cp = math.radians(DIMETRIC_PITCH)
        return Vec3(math.sin(cy) * math.cos(cp),
                    math.sin(cp),
                    -math.cos(cy) * math.cos(cp)) * CAM_DIST

    def _place(self):
        camera.position = self.focus + self.offset(self._yaw_shown)
        camera.look_at(self.focus)
        camera.rotation_z = 0

    def snap(self):
        """Tanpa tween — dipakai saat ganti scene dan oleh tools/capture.py."""
        self._yaw_shown = self.yaw
        self._place()

    def update(self, dt: float, target: Vec3,
               deadzone_tiles: float = 2.5, follow_speed: float = 6.0):
        """Follow ber-deadzone: fokus hanya bergerak kalau target keluar dari
        kotak di tengah layar. Kamera yang diam adalah kamera yang terbaca —
        follow-lerp lama (app.py:315-326) membuat seluruh lot bergoyang setiap
        kali pemain melangkah, dan itulah yang bikin ruangan sulit dibaca."""
        dz = deadzone_tiles * TILE_SIZE
        dx, dz_ = target.x - self.focus.x, target.z - self.focus.z
        dist = math.hypot(dx, dz_)
        if dist > dz:
            pull = (dist - dz) / dist
            k = min(1.0, follow_speed * dt)
            self.focus.x += dx  * pull * k
            self.focus.z += dz_ * pull * k
        self.focus.y = target.y

        # Tween yaw 90 derajat supaya pemain tidak kehilangan orientasi.
        d = (self.yaw - self._yaw_shown + 540.0) % 360.0 - 180.0
        if abs(d) > 0.05:
            self._yaw_shown += d * min(1.0, 9.0 * dt)
        else:
            self._yaw_shown = self.yaw
        self._place()
```

Then in `game/app.py`, replace lines 187-191:

```python
        # ── LAMA (app.py:187-191) ──
        # camera.orthographic = False
        # camera.fov          = 60
        # self.camera_yaw     = 0.0
        # self.camera_pitch   = 34.0
        # self.camera_dist    = 19.0

        # ── BARU ──
        from .camera_rig import CameraRig, DIMETRIC_PITCH
        self.cam_rig = CameraRig(self.player.position + Vec3(0, CAM_TARGET_LIFT, 0))
        # Shim supaya kode lama yang membaca camera_yaw (app.py:557,
        # player.py:433) tidak perlu diubah sekaligus:
        self.camera_yaw   = self.cam_rig.yaw
        self.camera_pitch = DIMETRIC_PITCH
```

and in `update()`, replace the free-look block (`app.py:299-311`), the pitch clamp
(`app.py:313`) and the follow-lerp (`app.py:315-327`) with:

```python
            self.cam_rig.update(dt, self.player.position + Vec3(0, CAM_TARGET_LIFT, 0))
            self.camera_yaw = self.cam_rig._yaw_shown
            self.world.set_camera_yaw_step(self.cam_rig.yaw_step)   # §2.4
```

Bind rotation and zoom in `input()` next to the existing hotkeys (`app.py:492-517`):

```python
            elif key == 'q':            self.world.set_camera_yaw_step(self.cam_rig.rotate(-1))
            elif key == 'e':            self.world.set_camera_yaw_step(self.cam_rig.rotate(+1))
            elif key == 'scroll up':    self.cam_rig.zoom(-1)
            elif key == 'scroll down':  self.cam_rig.zoom(+1)
```

`_snap_camera_to_player()` (`app.py:642-652`) becomes
`self.cam_rig.focus = ...; self.cam_rig.snap()`.

## 1.4 What breaks when you change it — precisely

**(1) Player controls become screen-relative — and this one is already fine.**
`game/player.py:433-437` derives the movement basis from
`camera.world_rotation_y` every frame, so W is always "up the screen" no matter
what yaw the rig is at. BRIEF §8.4 already records that movement was never broken.
**What does break** is the *facing* derived from it: `player.py:515-520` buckets
`rotation_y` into four cardinals (`up/down/left/right`), and
`_set_initial_rotation()` (`player.py:201-202`) maps them back with
`{'up': 0, 'down': 180, 'left': -90, 'right': 90}`. At yaw 45 those buckets land on
the diagonals, so "the tile in front of you" — which is what every tool acts on via
the `dmap` at `player.py:999` — points diagonally relative to the screen and the
player cannot predict where the hoe will land. **Fix:** stop deriving the tool
target from `facing`. Take it from the hover reticle (§5.2), which is where the
player is already looking. Keep `facing` only for choosing the sprite/animation.

**(2) `camera.clip_plane_near/far` silently writes to the wrong lens.**
`ursina/camera.py:94-98` (`orthographic_setter`) swaps `application.base.cam`'s lens
and `self.lens_node`, but leaves `self.lens` pointing at the perspective lens.
`clip_plane_near_setter` (`ursina/camera.py:113-121`) does `self.lens.set_near(...)`.
So after `camera.orthographic = True`, setting `camera.clip_plane_near` edits a lens
that is no longer in use, with no error. Always call
`camera.orthographic_lens.set_near_far(...)`. Panda3D's `OrthographicLens` defaults
to `near=1.0, far=100000.0`; a **negative** near is legal for an ortho lens
(verified in this environment) and is the standard isometric trick — it removes
near-clipping of tall geometry between the camera and the lot entirely.

**(3) Window resize stretches the projection.** The ortho film size is only computed
inside `fov_setter` (`ursina/camera.py:110`) using `self.aspect_ratio`, which is read
from the *perspective* lens. Resize the window and the aspect changes but the film
size does not. Re-assign `camera.fov = camera.fov` on resize
(`CameraRig.on_window_resize`).

**(4) Walls occlude — but the cutaway machinery already exists and mostly survives.**
`World3D.update_wall_cutaway()` (`game/world.py:346-384`) projects each wall onto the
horizontal view axis and stubs anything nearer than the focus. Under a fixed camera
this becomes *better*, not worse: the view axis only takes four values, so the whole
computation collapses to a precomputed bitmask (§2.4). Two things do break: the
`f_proj` threshold is measured against the **focus point**, which now sits in a
deadzone rather than on the player, so as the player walks the far wall of the room
will pop up and down; and the early-out `if state == self._cutaway_state`
(`world.py:367-370`) never fires under a smooth-following focus. Replace both with
the per-room, per-yaw-step rule in §2.

**(5) Billboards need re-facing and re-scaling.** `billboard=True` still faces the
camera correctly. What changes is size: under ortho, a world-space billboard has a
**fixed pixel size**, so the giant NPC name boards (`game/entities.py:242-245`,
`scale=5`) that were tuned at one distance are now uniformly wrong everywhere — but
also uniformly *fixable*. Target ~14 px cap height at the default zoom, i.e. ~0.27
world units (`14 / 51.4`). While you are in there: nameplates should not be on by
default at all (§4).

**(6) The rim/outline term drifts across the frame.** `game/smooth_shader.py:92-98`
computes `V = normalize(cam_pos - v_world_pos)` from `p3d_ViewMatrixInverse[3].xyz`.
Under perspective that is correct. Under ortho the true view direction is *constant*,
and using a point 60 units away makes the rim width vary by ~17° of incidence across
a 37-unit-wide frame — outlines get visibly fatter at the screen edges. Fix: add an
`sm_view_dir` uniform, set once per rotation step from `camera.forward`, and use it
instead of the per-pixel `V` when ortho. Two lines of GLSL, and it makes the outline
the reliable separator §3.3 needs it to be.

**(7) Mouse picking survives, verified.** `ursina/mouse.py:227` raycasts with
`scene.camera.lens_node`, and `orthographic_setter` swaps exactly that node. So
`mouse.world_point` — which `app.py:470-473` uses to turn a click into a tile —
keeps working, and the invisible ground collider (`game/world.py:423-429`) is still
the only collider you need. Do **not** add per-entity colliders for hover; §5.2.

**(8) `camera_dist` stops meaning anything.** Under ortho, distance does not scale.
`tools/capture.py:34-36` exposes `--pitch` / `--yaw` / `--dist` as camera knobs;
`--dist` becomes a no-op and `--pitch` becomes a way to silently break the 2:1 grid.
Replace them with `--zoom {0,1,2}` and `--yaw-step {0,1,2,3}`, wired to `CameraRig`.
A camera a critic cannot photograph at a known setting does not exist (BRIEF §4).

**(9) The white 1000×1000 horizon quad and the VHS post-process now dominate.**
`game/world.py:436-438` builds a 1000-unit white quad whenever `has_horizon` is
truthy — which, per CODE_MAP §6 bug 3, is *always*, including indoors. Under a lot
camera that quad is most of the frame. And `camera.shader = vhs_bloom_shader`
(`app.py:202-208`) applies barrel warp + chromatic aberration + scanlines to a
projection whose entire value proposition is that straight lines stay straight.
Both must go before any camera screenshot is taken seriously.

**(10) The sky dome is fine.** `game/sky.py:159` is a radius-500 inverted sphere; it
sits comfortably inside `ORTHO_FAR = 2000`, and the half of it behind the camera
plane is clipped, which is what you want.

---

# 2. Occlusion — the wall cutaway problem

## 2.1 The problem, stated exactly

A lot camera looks at a building from outside. The near walls of every roofed room
stand directly between the camera and the thing the player came to watch. If you draw
them, the interior — the entire game — is invisible. If you do not draw them, the
building has no volume and the player cannot tell a room from a courtyard.

## 2.2 The three wall states

Every wall segment is in exactly one of three states. Name them in code; do not use
booleans.

| State | Geometry | Reads as | When |
|---|---|---|---|
| **UP** | full `WALL_H = 2.8` (125 px) | a wall you cannot see past | the wall's interior side faces the camera |
| **CUT** | stub `CUTAWAY_STUB = 0.42` (19 px) | a floorplan line — the room still has an edge, but you see over it | the wall stands between the camera and its room's interior |
| **DOWN** | not drawn at all | floor plan only | global "walls down" view mode, and any wall of a room whose roof is hidden |

The stub is not a compromise, it is the point: at 19 px it draws the room's outline —
so the player still reads "this is a room, it has four sides, the door is there" —
while occluding nothing taller than a doormat. That is why `CUTAWAY_STUB = 0.42` is
right and must not be raised "so walls look more solid".

Add a fourth *global* state as a player-facing toggle, exactly as Sims 1 does:
`WALLS_UP` (everything UP, for admiring the exterior), `WALLS_CUTAWAY` (the per-wall
rule below — the default), `WALLS_DOWN` (everything DOWN, for build/buy). One key.

## 2.3 How to pick per wall

Do **not** pick by "is this wall between the camera and the player". That is what
`world.py:346-384` does, and it produces the near wall of the *next* room popping,
because the test is a distance comparison against a moving focus point. Pick by
**geometry that never moves**:

1. At scene build time each wall segment already knows its tile `(tx, ty)` — it is
   stored in `self._wall_ents` as `[entity, height, y, tx, ty]` (`world.py:631`).
   Also record its **orientation** (does it run along X or along Z) and which side is
   interior — the interior side is simply the neighbouring tile that is floor (`FL`)
   rather than outdoors.
2. For each of the four yaw steps, a wall is **CUT** if its interior side faces
   *away* from the camera, i.e.
   `dot(interior_normal, camera_forward_horizontal) > 0`. Because there are only four
   yaws, this is four boolean evaluations per wall, done once, at build.
3. Store the four booleans as a **4-bit mask** on the wall record.

That gives a rule with no per-frame geometry, no dependence on the player's position,
and — crucially — **no popping**: the same wall is in the same state for as long as
the camera yaw does not change. Popping is the single worst readability failure a
cutaway can have, because it makes the player distrust what they see.

Two refinements worth the lines:

- **Roofs follow walls, not the player.** `game/scenes/props.py:118-135` already
  flood-scans multi-tile houses to merge them, so the footprint exists. Store it. A
  roof is hidden whenever any wall of its footprint is CUT — which under this rule
  means "whenever we are looking into this building". Never hide a roof based on
  "player is inside", because then the roof pops as the player crosses the doorway.
- **Doorways stay open.** `DR` tiles are built at full `WALL_H` (`world.py:594`). A
  door inside an UP wall is invisible, so the player cannot see how to get in. Doors
  get their own state: always drawn at the stub height, in a distinct colour, in
  every state except WALLS_UP.

## 2.4 The cheap way to do it for hundreds of segments in Ursina

The naive version writes `e.scale_y` and `e.y` for every wall every time anything
changes — two `NodePath` transform writes each, plus a bounding-volume dirty flag.
For a lot with a few hundred segments that is fine at rotation time and wasteful per
frame. Three levels of cheap; pick the one that matches how far along you are:

**Level 1 — minimum change to what exists (do this first).** Keep one entity per
wall. Precompute the 4-bit mask (§2.3). Replace `update_wall_cutaway` with a
`set_camera_yaw_step(step)` that early-outs unless `step` changed, then walks
`_wall_ents` once and touches only walls whose bit differs between the old and new
step — at most half of them, and only on a keypress:

```python
    def set_camera_yaw_step(self, step: int):
        """Terapkan state cutaway untuk satu dari empat sudut kanonik.
        Hanya berjalan saat sudut berubah — bukan tiap frame."""
        if step == self._yaw_step:
            return
        old, self._yaw_step = self._yaw_step, step
        stub = self.CUTAWAY_STUB
        for rec in self._wall_ents:
            e, full_h, full_y, mask = rec[0], rec[1], rec[2], rec[5]
            if not e or ((mask >> old) & 1) == ((mask >> step) & 1):
                continue
            if (mask >> step) & 1:
                e.scale_y, e.y = stub, stub / 2 + GROUND_H
            else:
                e.scale_y, e.y = full_h, full_y
```

**Level 2 — group by mask (do this when a lot gets furnished).** There are only 16
possible masks. At build time create 16 parent `Entity`s and reparent each wall into
`groups[mask]`, in two variants: a full-height copy and a stub copy. Rotation then
costs **32 `enabled` writes total**, independent of wall count:

```python
        for m in range(16):
            cut = bool((m >> step) & 1)
            self._wall_full[m].enabled = not cut
            self._wall_stub[m].enabled = cut
```

`Entity.enabled` stashes/unstashes the whole subtree in one `NodePath` operation.
This is also the only version that scales to a build mode where the player adds
walls at runtime.

**Level 3 — combine into one mesh per group.** Once walls stop changing at runtime,
merge each group's boxes into a single `Mesh` and you are down to 32 draw calls for
every wall on the lot. This is the same fix CODE_MAP §6 asks for against the
1,227-entity census, and walls are the easiest place to prove it works. (Mind the
shared-mesh trap recorded in BRIEF §8.1 — go through `_instance()` in
`game/meshes.py`, never hand one `Mesh` NodePath to two Entities.)

**What not to do:** do not alpha-fade the near walls. Alpha in this renderer is a
minefield — the road-tile episode (BRIEF §8.6) needed `transparent=True` **and**
`smooth=False` **and** a geometry change before a texture with real alpha rendered
correctly, and translucent walls additionally need back-to-front sorting that Ursina
will not do for you. A stub is opaque, sorts trivially, and reads better anyway.

---

# 3. Silhouette and colour

The player must separate four classes at a glance, in this priority order:

1. **Characters** — the player, NPCs, animals. The things with intent.
2. **Interactables** — anything a click produces a menu for: stove, bed, chair,
   crops, ore, the mailbox.
3. **Scenery** — walls, floors, roofs, fences, trees. Structure you navigate but do
   not use.
4. **Ground** — grass, dirt, road, water. The surface.

Any rule below that separates one class from another is doing work. Any rule that
does not is decoration.

## 3.1 Value separation (the one that matters most)

Value — not hue — is what a human eye uses to segment a scene. Colour-blind players
and small screenshots both fall back to value alone.

**The rule:** measure luminance as `L = 0.299 R + 0.587 G + 0.114 B` on a 0–100 scale
and give each class a band, with a **≥ 25-point gap** between any object and the
surface it sits on:

| Class | L band | Chroma (HSV S) |
|---|---:|---:|
| Ground (grass, dirt, road) | 28 – 42 | 12 – 30 |
| Scenery (walls, floors, roofs, trees) | 40 – 62 | 15 – 35 |
| Interactables | 62 – 85 | 35 – 65 |
| Characters | free — must contain the frame's darkest dark **and** brightest light | 30 – 70 |

This is already half-applied and it worked: BRIEF §8.5 records that the indoor
palette was separated **by value** — dark teak floor, pale plaster walls — because
previously floor and wall were near-identical. `world.py:612-618` caps the plaster at
`_c(170,164,150)` specifically to stop the cel shader clipping it to flat white. That
is the correct instinct, applied to one room. Apply it to all four classes.

The cel shader has three tiers (`smooth_shader.py:85-91`: `1.0 / 0.6 / 0.3`), so a
lit surface reads at its base value and a shadowed one at 30% of it. That means an
object's *shadowed* value must still clear the ground's *lit* value where they meet,
or the object dissolves into the ground in shade. Practically: interactables need
base L ≥ 62 so their shadow side (≈ 0.6 × 62 = 37) still sits at the top of the
ground band.

## 3.2 Saturation budget

Under a cel shader with a saturation lift (`smooth_shader.py:107`), high chroma is
the loudest signal available. Treat it as a **budget, not a style**:

- **No more than ~8% of screen pixels above S = 60.** Everything above that line must
  be interactive, a character, or the entity.
- The entity's palette (`docs/ENTITY_VISUAL_LANGUAGE.md`: leaf teal `#3FB3A0`, bronze
  `#C79B45`, cream `#FBEFC6`, flesh pink `#E77E9A`) is **reserved**. When those hues
  appear on something the entity has not touched, the game's single most important
  narrative signal is destroyed. This is the strongest argument against the neon
  magenta/cyan pass in §4 — not that it is ugly, but that it burns the channel the
  horror needs.
- Ground and scenery live at S ≤ 35 so they can absorb 60% of the frame without
  competing.

## 3.3 Outline / rim

The cel shader darkens every edge uniformly by up to 55% (`smooth_shader.py:97-98`).
That is a *style*, not a *separator*: if everything has an outline, the outline
distinguishes nothing.

**The rule:** outlines are class-coded, via one new per-entity uniform.

| Class | Rim |
|---|---|
| Ground | none |
| Scenery | dark rim, current behaviour, strength ≤ 0.35 |
| Interactables | dark rim 0.55 — the current default, i.e. the strongest passive edge |
| Characters | **light** rim: cream `#FBEFC6` at 0.35, added not subtracted |
| Entity-touched | teal `#3FB3A0` rim, and it is the only thing that pulses |

A light rim on characters is the single cheapest way to keep a Vitaboy avatar from
sinking into a dark interior, and it costs one `mix()` in the existing fragment
shader. Combine with the `sm_view_dir` fix from §1.4(6) so the rim has constant
width.

While you are in the shader: `player.py:722-724` re-sets `self.body.color` with a
hardcoded alpha 0.4 every frame, which is why the player is see-through (CODE_MAP
§1.4). A translucent protagonist fails item 6 of the checklist by construction.

## 3.4 Size hierarchy — the reserved band

Under a fixed camera you can legislate heights, and this is the highest-value rule
in this whole document:

> **The 0.6 m – 1.2 m height band is reserved for interactable objects.**
> Nothing else may occupy it.

- Ground clutter (tufts, pebbles, fallen leaves): **≤ 0.35 m.** Reads as texture.
- Interactables: **0.6 – 1.2 m** (`OBJ_H = 1.2`, `config.py:15`, is already exactly
  the top of this band — good). Footprint ≥ 1 tile so it is clickable.
- Characters: **1.6 – 1.9 m.** Taller than every interactable, shorter than every
  wall. At the default zoom a 1.8 m character is 80 px; the tallest interactable is
  `1.2 × 0.866 × 51.4 = 53 px`. That 27 px difference is what lets you find a person
  in a furnished room instantly.
- Scenery/architecture: **≥ 2.5 m** (`WALL_H = 2.8`, `TREE_H = 3.6`, `HOUSE_H = 3.2`).

`SMALL_OBJ_H = 0.7` (`config.py:16`) currently puts ore and rocks inside the reserved
band — which is *correct*, because they are minable. The law is already almost
respected; only the decoration pass violates it. See §4.

## 3.5 Grounding: the blob shadow

Orthographic projection removes the perspective cues that tell you whether an object
is standing on the floor or floating above it. Without a contact shadow, a crop, a
character and a floating decoration are the same to the eye.

**Every character and every interactable gets a contact shadow**: one unlit quad,
parented to the object, `rotation_x = 90`, at `y = GROUND_H + 0.005`, radial-gradient
texture, `color = rgba(0,0,0,110)`, scale ≈ 0.8 × the object's footprint. That is one
entity, no shader, no light, no render pass — and it does more for spatial legibility
than the entire `vhs_bloom` post-process. It also gives a free surface for "is this
thing selected" (§5.1).

## 3.6 The four-class summary card

| | Value L | Chroma S | Height | Rim | Shadow | Motion |
|---|---:|---:|---:|---|---|---|
| Ground | 28–42 | 12–30 | ≤ 0.35 | none | — | grass sway only |
| Scenery | 40–62 | 15–35 | ≥ 2.5 | dark 0.35 | — | none |
| Interactable | 62–85 | 35–65 | 0.6–1.2 | dark 0.55 | yes | only when in use |
| Character | extremes | 30–70 | 1.6–1.9 | **light cream** | yes | always (idle breathe) |
| Entity-touched | any | ≥ 70 teal/bronze | any | **teal, pulsing** | yes | pulsing |

**The test:** take any screenshot, desaturate it, scale it to 25% width. If you can
still point at every character and every usable object, the scene passes.

---

# 4. Signal vs noise

## 4.1 The rule

> **The Earned-Pixel Rule.** A pixel earns its place only by answering one of four
> questions the player is actually asking:
> **(1) What can I use?** **(2) Where can I walk?** **(3) What is happening right
> now?** **(4) What time / season / weather is it?**
> Anything that answers none of them is *ground*, and ground must recede: value in
> band, chroma ≤ 35, silhouette ≤ 0.35 m, no motion, no emission.

And its enforcement clause, which is the part that actually changes code:

> **Decoration may never use a channel that gameplay needs.** The channels gameplay
> owns are: **high chroma**, **motion**, **emission/glow**, **the 0.6–1.2 m height
> band**, and **screen-space UI area**. A decorative object that is bright, moving,
> glowing, knee-to-waist high, or wearing a label is not decoration — it is a false
> positive, and false positives cost more than missing detail. A player who learns
> that "sticking up and colourful" sometimes means nothing stops scanning for it,
> and then genuinely misses the stove.

This is why "sprinkle interesting things around" is the wrong instinct for a life sim
specifically. In a walking sim, noise is atmosphere. In a game whose core loop is
*spotting the object that fixes your falling need before it bottoms out*, noise is a
tax on every second of play.

## 4.2 Applied to what is actually in this repo

**`_add_outdoor_deco()` — `game/world.py:563-582`, called at `world.py:485-488`.**
Three violations at once, on 30% of every grass tile (`if nv < 0.30`):

- a pure cyan cube `_c(0,255,255)` at `surface_y + 0.8`, rotated 45° — S = 100,
  emissive-looking, floating (no shadow), and sitting at 0.8 m: **inside the reserved
  interactable band**;
- a pure magenta cylinder `_c(255,0,255)`, 0.8 units tall — same band, same chroma;
- a `lamp_glow`-textured white sphere at 0.6 m — glow channel, same band.

The docstring is honest: *"Surreal digital deco: floating cubes, wireframe pyramids"*.
It is a different game's art direction still running. **Verdict: delete the three
branches.** Keep the function and its deterministic hash placement (that is good
code), and re-aim it:

```python
    def _add_outdoor_deco(self, wx, wz, surface_y, tx, ty, nv):
        """Dekorasi tanah: rumpun rumput / kerikil / bunga kecil.

        Aturan (docs/READABILITY.md §4): tinggi <= 0.35 (di bawah pita objek
        yang bisa dipakai), saturasi mengikuti rumput, tanpa glow, tanpa gerak
        sendiri, dan TIDAK PERNAH di tile yang bertetangga dengan objek yang
        bisa diklik — pemain butuh satu tile ruang bersih di sekitar apa pun
        yang bisa dipakai.
        """
        if self._has_interactable_neighbour(tx, ty):
            return
        ...
```

Then lower the rate: **`nv < 0.12`**, not 0.30. At 30% the eye stops treating "a
thing sticking out of the grass" as information; at ~12% it stays information. This
also removes roughly 200 entities from the `farm` census of 1,227.

**Paths.** BRIEF §8.6 records this as fixed — road tiles needed `transparent=True`
**and** `smooth=False` **and** a thin slab instead of a full cube (z-fighting), plus
an earth tint instead of the grass checkerboard. Keep the *principle* on the wall: a
path answers question (2), "where can I walk", so **a path must read as walkable from
a still frame with no other cue**. A magenta/black checker is not merely wrong, it is
the strongest negative signal a renderer can emit — every player who has seen a game
before reads it as "this is broken", and everything else on screen inherits that
judgement.

**Everything else currently spending gameplay channels on nothing:**

| Where | What | Channel stolen |
|---|---|---|
| `game/player.py:268-269` | magenta halo ring + spinning cyan cube on the player's head | chroma + motion, on the one silhouette that must never be ambiguous |
| `game/world.py:444` | `pl.color = color.rgb(255, 40, 200)` — neon magenta indoor `PointLight` | tints every interior surface, destroying §3.1's value bands |
| `game/controllers/interaction_controller.py:600-602` | pure magenta broom bristles | chroma |
| `game/player.py:763` | neon cyan/magenta/yellow flight particles | motion + chroma |
| `game/world.py:436-438` | white 1000×1000 horizon quad, drawn indoors too (CODE_MAP §6 bug 3) | value — it is the brightest thing on screen and means nothing |
| `game/entities.py:242-245` | `scale=5` billboard name `Text` on every NPC | screen-space UI area; hides the horizon and the NPCs themselves |
| `game/app.py:202-208` | `vhs_bloom` post: barrel warp, chromatic aberration, scanlines, 7×7 bloom | contrast + straight lines + fill rate, globally |

None of these is a bug. Each was a deliberate aesthetic choice for a different
target. The redirection is what makes them wrong: they cost clarity, and clarity is
now the goal.

## 4.3 The numeric budget, for a 1920×1080 frame

- ≤ 8% of pixels above S = 60.
- ≤ 5 simultaneously animated highlights (excluding grass sway and character idles).
- Exactly **1** element may blink or pulse at a time, and it is always the most
  urgent thing (a critical motive, or the entity).
- ≤ 12% of grass tiles carry any vertical decoration.
- ≥ 1 tile of clean ground around every interactable.
- 0 nameplates by default; names appear on hover only (§5.2).

---

# 5. Feedback channels

A life sim needs six. They are not decoration and they are not "polish" — each one
answers a question the player will otherwise ask out loud, and a game where the
player asks those out loud is the game the owner described as unclear.

For each: what it must communicate, then the cheapest form in Ursina that is actually
*correct* (cheap-and-wrong is not on the menu).

All of them build on the two helpers already in `game/panels.py:47-61`:
`_ui(model='quad', **kw)` parents to `camera.ui` with `transparent=True`, and
`_txt()` parents `Text` to `camera.ui` with the Montserrat font. Use them; do not
invent a second UI idiom.

## 5.1 Selection highlight

**Must communicate:** *this is the object your next command applies to, it is still
selected while you look elsewhere, and here is its name.* Selection is **sticky** —
that is what separates it from hover.

**Cheapest correct form:** reuse the contact shadow from §3.5. Create **one**
persistent selection ring at startup, never one per click:

```python
        self._sel_ring = Entity(model='quad', texture='ui_ring', rotation_x=90,
                                unlit=True, transparent=True, enabled=False,
                                color=color.rgba(251, 239, 198, 200))   # cream #FBEFC6
```

On selection: `self._sel_ring.enabled = True`, move it to the object's tile centre at
`y = GROUND_H + 0.01`, scale it to the footprint, and drive a slow 0.8 Hz alpha
breathe in `update()`. Cream, because §3.2 reserves teal for the entity and because
cream reads on both the dark teak floor and the pale plaster.

Do **not** duplicate the object's mesh at 1.05× as an outline shell: it doubles draw
calls, needs backface culling you would have to set per model, and breaks on the
`soft_cube_mesh` superellipsoids (`game/meshes.py`).

## 5.2 Hover affordance

**Must communicate:** *if you click here, this will happen* — the verb, not just the
noun — **before** the player commits. This is the channel that makes a game feel
"clear", and this repo currently has none: `app.py:479-487` only flashes
`"Melihat: <nama tile>"` **after** a click.

**Cheapest correct form:** one reticle plus one label, both created once and moved.
No per-entity colliders — the ground collider at `world.py:423-429` plus
`mouse.world_point` (which survives the ortho switch, §1.4(7)) gives the tile
directly, exactly as `app.py:470-473` already does:

```python
    def update_hover(self):
        from ursina import mouse
        if not mouse.world_point:
            self._hover_ring.enabled = False
            self._hover_lbl.enabled  = False
            return
        tx = int(round(mouse.world_point.x / TILE_SIZE))
        ty = int(round(mouse.world_point.z / TILE_SIZE))
        if (tx, ty) == self._hover_tile:
            return                                   # hanya bergerak saat pindah tile
        self._hover_tile = (tx, ty)
        verb, name = self.world.hover_label(tx, ty)  # ('Pakai', 'Kompor') / (None, None)
        self._hover_ring.enabled = verb is not None
        self._hover_lbl.enabled  = verb is not None
        if verb:
            self._hover_ring.position = (tx * TILE_SIZE, GROUND_H + 0.012, ty * TILE_SIZE)
            self._hover_lbl.text = f'{verb} {name}'  # bukan cuma nama
```

Rules that make it work: it snaps to the **tile**, so hovering never flickers between
neighbours; it shows a **verb** in the existing Indonesian UI voice (`Pakai`, `Ambil`,
`Bicara`, `Tanam`, `Siram`) because a noun alone does not say "clickable"; and when a
tile has nothing usable the reticle disappears entirely rather than showing a dimmed
state — absence is a faster read than a variant.

## 5.3 Queue display

**Must communicate:** *what I am doing now, what comes next, in what order, and how to
cancel any of it.* Today this is the string `[ANT:n]` (`panels.py:777-778`) over a
queue that is a list of tile coordinates executed all in one frame
(`interaction_controller.py:578-588`). CODE_MAP §4 scores it at ~10% of Sims 1, and
the missing 90% is mostly this display.

**Cheapest correct form:** a fixed strip of 8 icon slots in `camera.ui`, built once:

```python
        ATLAS = 'ui_action_icons'        # atlas 4x4, 16 verba, sel 64px
        self._q_slots = [
            _ui(model='quad', texture=ATLAS, texture_scale=(0.25, 0.25),
                scale=(0.052, 0.052), position=(-0.86 + i * 0.058, -0.44))
            for i in range(8)
        ]
        self._q_fill = _ui(model='quad', scale=(0.052, 0.0), origin=(0, -0.5),
                           position=(-0.86, -0.466),
                           color=color.rgba(63, 179, 160, 200))
```

Pick an icon by setting `texture_offset` — no texture swap, no entity churn. Slot 0 is
the running action and carries the progress fill (§5.4); it gets a cream border, the
rest are dim. Clicking a slot cancels that action. Eight slots is enough: a player who
has queued more than eight things has stopped reading anyway.

The important part is not the widget, it is that **the queue must visibly drain over
time**. An action queue that empties in one frame communicates nothing; the display
only becomes information once `behavior_vm.BehaviorThread` (`game/behavior_vm.py:96-177`
— which already has the correct priority queue, RUNNING state and blocking timer) is
what drives it.

## 5.4 Progress on an action

**Must communicate:** *this is working, it will take about this long, and you may
cancel it.* Two surfaces, because they answer for two different readers:

- **In the queue strip** (`self._q_fill` above): scale `scale_y` from 0 to the slot
  height with `origin=(0,-0.5)` so it grows upward from the bottom. This is for the
  player watching the UI.
- **Over the actor's head:** a two-entity billboard — a background quad plus a fill
  quad with `origin=(-0.5, 0)`, so `fill.scale_x = 0.9 * t` grows from the left
  without moving. Parent it to the actor with `billboard=True`. Under ortho it has a
  constant pixel size everywhere (§1.1a), so pick once: 0.9 world units wide ≈ 46 px
  at the default zoom, 0.09 units tall ≈ 5 px. This is for the player watching the
  world, which is where they actually are.

Both use the same colour, and it is the same teal the pie menu already uses for its
effect preview (`panels.py:864-867`, `color.rgb(127,220,255)`) — one hue for "the game
is doing the thing you asked".

Show the bar only for actions longer than 1.2 s. A bar that flashes for 300 ms is
noise under §4.

## 5.5 Motive change

**Must communicate:** *that action changed this need, by this much, just now.* This is
the feedback loop that makes a life sim legible at all, and it does not exist:
`_need_lbl_ents` / `_need_bg_ents` / `_need_fill_ents` are initialised as empty lists
(`panels.py:139-141`), `_NBAR_W` / `_NBAR_X` are `0` (`panels.py:142-143`), `_refresh_hud()`
(`panels.py:156-216`) never touches them, and `_THERMO_BG_TEX` is `None` because
`panels.py:29` loads from `assets/ui/`, which does not exist (the textures are in
`assets/textures/`). Runtime proof is in CODE_MAP §10.

**Cheapest correct form, three parts:**

1. **The thermometer itself.** One background quad and one fill quad per need,
   `origin=(-0.5, 0)` so the fill grows from the left, driven in `_refresh_hud()`.
   Three bars today (`lapar`, `sosial`, `senang` — `config.py:96-98`); lay out for
   eight, because that is where the design is going. Colour-code by *level*, not by
   need: green ≥ 60, amber 20–60, red < 20, using `NEED_LOW` and `NEED_CRITICAL`,
   which are already imported and never used (`panels.py:21`).
2. **The lag ghost.** Draw a second, paler fill at the *previous* value that eases
   toward the current one over ~0.6 s. The gap between the two bars is the change,
   visible without any text. `_prev_hunger` / `_prev_social` / `_prev_fun` /
   `_prev_energy` (`panels.py:86-89`) were set up for exactly this and never read —
   finish them.
3. **The floating delta.** Pool six `Text` entities; on a motive change place one at
   the actor and tween it up 40 px while fading over 0.9 s: `+15 Sosial`. It must use
   the **same words and the same colour** as the pie menu's preview
   (`panels.py:864-867`), because "the thing I was promised" and "the thing I got"
   being visibly identical is what teaches the player that the system is honest.

Critical needs pulse the bar rather than emitting text. `_check_needs_warning()`
(`app.py:591-599`) — currently the only needs feedback in the entire game, and a red
flash — should drive that pulse instead.

## 5.6 Notification

**Must communicate:** *something happened that you did not cause, here is what and
where, and it will wait for you.* The waiting is the whole point. `flash_msg()`
(`panels.py:219-225`) is centre-screen and vanishes — it interrupts, covers the scene,
and is gone before a player who was looking at the lot can read it.

**Cheapest correct form:** a corner toast stack — max 3 live, each an icon quad plus
one line of `_txt`, 4 s dwell, sliding down as older ones expire. Pre-build three
slots and recycle them. Then two things that matter more than the widget:

- **Every toast is also written to a log** the player can reopen. The `catatan` panel
  already exists (`panels.py:518-701`); append there. A notification that cannot be
  re-read is a notification that was not delivered.
- **Toasts never carry urgent state.** Urgent state lives on a persistent surface that
  stays wrong until the player fixes it — the pulsing thermometer, the red queue slot.
  A message that disappears cannot represent a problem that has not.

Keep `flash_msg` for one job only: confirming an action the player just took, where
centre-screen is right *because* their eyes are already there.

---

# 6. The 20-item readability checklist

Run this against any single screenshot of the game. Each item is **binary** and
answerable from the image alone by someone who has never played. Score out of 20;
below 16 the frame is not shippable, and the failing items are the work order.

**Camera & space**

1. **Tile grid countable.** Can you count the tiles between two objects without
   ambiguity? *(Catches: near-horizontal pitch, perspective foreshortening.)*
2. **Constant scale.** Are two objects of the same real size the same size on screen
   regardless of where they sit in the frame? *(Catches: perspective.)*
3. **Whole play area visible.** Is the entire room the player is in on screen, with
   its exits? *(Catches: zoom too close, camera glued to the body.)*
4. **Interior visible.** For every roofed building in frame, can you see its floor and
   its furniture? *(Catches: missing or failed wall cutaway, roofs left on.)*
5. **No floaters.** Does every object visibly touch the ground — a contact shadow or a
   clear base? *(Catches: missing blob shadows, decoration spawned at +0.8.)*

**Reading the classes**

6. **Character findable in 1 second.** Point at the player. Then at every NPC.
   *(Catches: value collapse, the alpha-0.4 transparent body, no light rim.)*
7. **Player distinct from NPCs.** Can you tell which character you control?
8. **Usable objects nameable without clicking.** Point at three things you believe are
   interactable and be right about all three. *(Catches: the §4 false positives.)*
9. **Scenery clearly not usable.** Point at three things you believe are *not*
   interactable and be right. *(Catches: the reserved-band violation.)*
10. **Desaturation test.** Convert to greyscale at 25% size: items 6–9 still pass.
    *(Catches: separation that relies on hue alone.)*
11. **Height law holds.** Nothing decorative sits in the 0.6–1.2 m band; nothing
    usable sits outside it.
12. **Walkable is obvious.** Can you tell, without moving, where you can and cannot
    walk? *(Catches: paths that read as error, water/floor ambiguity.)*

**Signal discipline**

13. **Saturation budget.** Under ~8% of pixels above S = 60, and every one of them is
    a character, an interactable, or the entity.
14. **Entity palette clean.** No teal `#3FB3A0` / bronze `#C79B45` / cream glory light
    on anything the entity has not touched.
15. **One pulse maximum.** At most one element in the frame is blinking or pulsing,
    and it is the most urgent thing on screen.
16. **No error signals.** Zero magenta/black checkerboards, zero pure `#FF00FF`, zero
    pure `#00FFFF`, zero untextured flat white covering ≥ 5% of the frame.

**Feedback**

17. **Motives readable.** Are the need thermometers on screen, filled, and is at least
    one of them legibly not-full? *(Catches: `panels.py:139-141` empty lists.)*
18. **Current action stated.** Does the frame say what the character is doing right
    now — queue slot, progress bar, or an animation that is unmistakable?
19. **Queue visible.** Is what happens next shown as discrete items, not a count?
20. **HUD intact at this resolution.** No text clipped by a screen edge, no element
    overlapping another, and nothing occupying the centre of the frame that is not the
    game world.

**How to run it.** Capture with the real game — `python tools/capture.py --out
_bench/shots/<name>.png --scene farm --frames 90 --width 1920 --height 1080` (BRIEF §4;
capture at 1920×1080 because the HUD is laid out for it). Then run items 1–20 against
the PNG and record the score in `_bench/progress.jsonl` alongside the shot. A frame
that scores 20/20 and is boring is a better starting point than a frame that scores 11
and is beautiful — the second one has to be un-built first.
