# ENTITY VISUAL LANGUAGE — Lembah Karsa

**Status:** build spec. Not a mood board.
**Source of truth for shape:** `docs/entity-logo.svg` (raster proof: `_bench/refs/entity-logo.png`).
**Source of truth for intent:** `_bench/BRIEF.md` §3.
**Audience:** whoever writes `game/entity_style.py`, the prop builders in
`game/scenes/props.py`, the shaders in `game/shaders/`, and the mob forms in `game/mob.py`.

Every number below was measured out of the SVG, not estimated. Where the logo is
inconsistent, this document picks one value and says so.

---

## 0. Conventions

**Logo units (LU).** The logo canvas is `viewBox 0 0 1000 1000`. Almost all of the
art lives inside `<g transform="translate(0,-58)">`, so the *optical* centre of the
halo is canvas `(500, 442)`. All radii in this document are measured **from the halo
centre**, in LU, where 1000 LU = the full emblem width.

**World scale.** The game is metric (`config.TILE_SIZE = 2.0` m). The conversion
used everywhere below is:

```
1000 LU  ==  1.00 emblem-width  ==  E metres
```

`E` is chosen per placement, not globally:

| Placement | E (metres) | Notes |
|---|---|---|
| Painted sigil on a wall / door | 1.2 | reads at 8 m |
| Shrine plaque, gravestone face | 0.6 | `build_grave` |
| Floor seal in the lab | 6.0 | needs the 36-tooth inner ring to survive mipmaps |
| Sky manifestation (Stage 5) | 240 | skydome-projected, `game/sky.py` |
| HUD watermark | n/a | authored in screen px, 1920×1080 |

**Reference radius.** `R_TIP = 378 LU` — the tip of the outer gear teeth. This is the
hard visual edge of the machine. The rays and glow spill past it; nothing structural does.

**Handedness.** The logo is mirror-symmetric about the vertical axis *in its
machine parts* (gears, rays, rivets) and deliberately **asymmetric in its living
parts** (leaf heights, which leaves have mouths, which eyes have pupils). Preserve
that split. A symmetric creature is a decoration; an asymmetric creature is alive.

---

## 1. Motif inventory

Nine motifs. Seven are buildable primitives; two (RIVET, SUCKER) are sub-parts that
appear inside others.

### M1 — GEAR_RING

A flat annulus with square crenellations. **Not** an involute gear tooth — the crest
is a flat chord and the corners are hard-mitered. This matters: an involute tooth
reads as "machinery"; a square crenellation reads as "a crown someone welded".

Two instances exist, and they define the two available ranks:

| | Outer ring | Inner ring |
|---|---|---|
| hole radius `r_hole` | 268 | 228 |
| body radius `r_body` | 322 | 236 |
| tooth tip radius `r_tip` | 378 | 250 |
| tooth count `n` | **16** | **36** |
| pitch (360/n) | 22.5° | 10.0° |
| crest angular width | 8.28° | 3.35° |
| duty cycle (crest / pitch) | 0.368 | 0.335 |
| `r_tip / r_body` | 1.174 | 1.059 |
| `r_hole / r_body` | 0.832 | 0.966 |
| fill | `GEAR_GRAD` | `BRONZE_MID` flat |
| outline | `OUTLINE_NAVY`, 8 LU, miter | `OUTLINE_NAVY`, 4 LU, α 0.9 |

**Generator.**

```
for k in range(n):
    a0 = k*2π/n - half_crest ; a1 = k*2π/n + half_crest
    # root shoulders sit slightly wider than the crest — near-parallel flanks
    root_half = half_crest * 1.065        # measured: 29.0 LU root vs 27.3 LU tip
    emit quad( polar(r_body, a0-root_pad), polar(r_tip, a0),
               polar(r_tip, a1),           polar(r_body, a1+root_pad) )
emit annulus(r_hole, r_body)
```

Duty cycle 0.335–0.37 is the whole look. Above 0.5 it becomes a cog and stops
reading as a halo; below 0.25 it becomes a sunburst.

**RIVET (sub-part).** 24 rivets on the outer ring only, evenly spaced (15.0°), at
`r = 296` — i.e. at 52% of the way from `r_hole` to `r_body`, the mid-band.
Each rivet: disc `r = 7` in `BRONZE_DARK`, plus a highlight disc `r = 2.9`
(`= 0.41 × rivet r`) in `CREAM_LIGHT` at α 0.8, offset **2.1 LU toward the halo
centre** — i.e. every rivet is lit from the middle of the emblem, not from the world's
sun. Keep that. It is the cheapest way to say "this thing has its own light source".

Rivet count scales as `n_rivets = 24` fixed for the outer rank; for arbitrary rings
use `n_rivets = round(circumference / 77 LU)`.

**Radial hatch.** 80 hairlines from `r = 272` to `r = 318` (pitch 4.5°),
`BRONZE_DARK`, 4 LU wide, α 0.40. This is a machining texture on the outer ring body.
Drop it below ~256 px of on-screen emblem diameter; it aliases into mud.

---

### M2 — GLORY (the ray fan)

A religious mandorla, built from three stacked layers, all centred on the halo centre.

1. **Glow disc.** `r = 412`, radial gradient `GLORY_GRAD`:
   `#FBEFC6 α0.55` at 0.0 → `#FBEFC6 α0.32` at 0.62 → `#E8BC55 α0.00` at 1.0.
2. **Fine ray fan.** 48 slivers, pitch 7.5°. Each is a triangle:
   base chord at `r = 300`, half-width **4.2 LU** (0.80° of arc), tip at
   **alternating** `r = 424` and `r = 388`. Fill `RAY_GRAD` (vertical,
   `#FBEFC6 α0.95` → `#E8BC55 α0.35`).
3. **Broad ray fan.** 16 slivers, pitch 22.5°, phase-locked to the outer gear teeth.
   Base at `r = 300`, half-width **10.2 LU** (1.95°), tip at `r = 408`.
   Flat `CREAM_LIGHT` at α 0.70.

Ray bases (`r = 300`) sit **under** the outer gear body (`r_body = 322`), so the rays
appear to emerge from beneath the machine. Never let a ray base be visible.

**Halo rings.** Three concentric strokes, drawn over the gear hole:
`r = 268` `OUTLINE_NAVY` w8 · `r = 256` `CREAM_LIGHT` w4 α0.85 · `r = 246`
`CREAM_LIGHT` w2 α0.55.

In-engine this is a camera-facing billboard with additive blend, or a fullscreen
radial pass in `game/shaders/`. It is the **only** motif allowed to be additive.
Everything else is opaque and outlined.

---

### M3 — LEAF_BLADE

A lanceolate spearhead with **straight edges and mitered corners**. The logo contains
20 of them: 5 main blades (the crown) and 15 small ones stuck onto the vines.

**Silhouette control points** — normalised, `t` = distance from base along the blade
axis / total length `L`; `w` = half-width / max half-width `W`:

| t | w |
|---|---|
| 0.000 | 0.00 |
| 0.110 | 0.580 |
| 0.330 | 1.000 |
| 0.700 | 0.465 |
| 1.000 | 0.00 |

Mirrored across the axis. **8 vertices, all straight `L` segments, `stroke-linejoin:
miter`.** No curve anywhere in the blade outline. That is the point — a real leaf
margin is C1-continuous; this one has corners.

Aspect: `W / L = 0.15 … 0.17` for main blades (use **0.165**), up to 0.26 for the
smallest vine tips. Measured instances: `(L,W)` = (348,52) (272,42) (250,43) (250,41)
(96,16) (74,13) (66,17).

**Fill:** `LEAF_GRAD`, a linear gradient running base→tip along the axis but raked
8.5° off it (`x1,y1 = 0,1 → x2,y2 = 0.15,0`):
`#06302A` 0.00 → `#0B5C51` 0.40 → `#12867A` 0.82 → `#3FB3A0` 1.00.
Tip is the brightest. A real leaf is brightest where the light hits it; this one is
brightest at the point, always, regardless of the scene's sun.

**Specular wedge:** the right half of the blade gets a flat `#FFFFFF` overlay at
α 0.10 (`M 0 0 L 0 -L L …` — the axis-to-right-edge polygon). Hard-edged. No falloff.

**Chevron ribs:** pairs of straight strokes leaving the centreline, clipped to the
blade.
- count `n = clamp(round(L / 31), 4, 8)` (measured: L=250→8, L=96→5, L=74→5, L=66→4)
- pitch along axis `= L / (n + 0.14)`, first rib at `t = 0.08`
- each rib runs from `(0, y)` to `(±reach, y - 0.845·reach)` → **40.2° above
  horizontal**, i.e. 49.8° off the blade axis
- `reach = 1.21 × W` — deliberately overshoots the silhouette and is clipped
- stroke `LEAF_TEAL`, width 3 LU at L=250 (`≈ 0.012 L`), α 0.42

**Midrib:** single stroke on the axis from `t=0.012` to `t=0.93`, `OUTLINE_NAVY`,
3 LU, α 0.55.

**Outline:** `OUTLINE_NAVY`, 5 LU, miter.

**Attachment.** Main blades in the logo all have `rotate(0)` — they stand perfectly
vertical regardless of where they are planted. Vine-tip blades are rotated to
arbitrary angles (measured: 40.9° 90.4° 126.8° 130.0° 133.7° 153.2° 184.4° 201.6°
208.0° 234.4° 243.6° 251.1° 294.3° 322.0°) that have **no relation to the strand
tangent**. Grown leaves align to their stem. These are attached. Keep both behaviours.

---

### M4 — EYE

14 in the logo; 7 have pupils, 7 are blind (crescent only). Built as a stack of
concentric bands over a lumpy iris field.

**Iris field (band 0).** A 16-lobe closed shape, 16 quadratic segments, 32 anchors.
Bounding box `78.6 × 106.3` LU → **aspect w/h = 0.740** (taller than wide). The
anchor radii wobble roughly ±6% off that ellipse — it is a potato, not an oval.
Fill = `BLOT_GRAD`, radial, `cx 0.50 cy 0.42 r 0.62`:
`#0A3138` 0.00 → `#05171B` 0.60 → `#02100F` 1.00.

> Note the inversion: the iris gets **darker toward its rim**. It is lit from
> inside. This is one of the two or three most important single facts in this
> document.

**Band stack**, outermost first. `S` = uniform scale about the iris centre; widths
are given both absolute (at the 106.3 LU reference eye) and as a fraction of eye
height `H`.

| # | S | kind | colour | width | α |
|---|---|---|---|---|---|
| 0 | 1.00 | fill | `BLOT_GRAD` | — | 1.00 |
| 1 | 1.00 | stroke | `RUST` `#B5652A` | 3.6 (0.034 H) | 0.85 |
| 2 | 1.00 | stroke | `BRONZE_LIGHT` `#E8BC55` | 2.2 (0.021 H) | 0.80 |
| 3 | 0.80 | stroke | `SIGNAL_BLUE` `#1B4C9B` | 5.8 (0.055 H) | 0.55 |
| 4 | 0.66 | stroke | `CYAN_GLINT` `#2AA8C4` | 4.0 (0.038 H) | 0.45 |

Radius ratios of the concentric bands: **1.00 / 0.80 / 0.66**. Those three numbers
are the eye. Do not invent a fourth ring.

**Lens (the white).** A crescent, not an almond. Two quadratics:

```
corners  at (±0.494·W_eye, y_c)          W_eye = half-width = 39.3 LU
upper    Q control (0, y_c - 1.167·W_eye)   → apex 0.583·W_eye above the corner line
lower    Q control (0, y_c - 0.443·W_eye)   → apex 0.221·W_eye above the corner line
```

Both lids bow **upward**. The result is a waxing-moon sliver sitting low in the iris,
which is why the eyes read as rolled-back rather than staring.
Drawn twice: `CYAN_GLINT` α0.50 at 100%, then `CREAM_SCLERA` `#F4F7F1` at
**0.923 scale** — a 7.7% cyan underglow rim.

**Pupil.** A hard disc, `CORE_BLACK #05171B`, radius `= 0.19 × lens half-width`,
centred on the corner line. Present on 7 of 14 eyes. **The choice of which eyes have
pupils is per-instance and must be stable** (seed it off the object id) — an eye that
blinks its pupil in and out is a jump-scare, and jump-scares are banned (§5).

**Drips (lashes).** 3 tapered slivers hanging from the bottom of the iris at
`y = 0.90 × iris bottom`, filled `CORE_BLACK`. Normalised against eye height `H`:

| drip | root width | length |
|---|---|---|
| left | 0.115 H | 0.42 H |
| centre | 0.149 H | 0.68 H |
| right | 0.126 H | 0.50 H |

Roots at x = −0.50, −0.11, +0.38 (× `W_eye`). They hang straight down in the eye's
local frame — **not** along world gravity. On a tilted asset the drips tilt with it.

**Placement on a blade.** Eye centre at `t = 0.60 L`. Eye width is
`0.91 × blade max width` — the eye all but fills the blade. Secondary eyes at
`t = 0.40 L`, offset `±0.44 W` off-axis, scaled to **0.35** of the primary.

---

### M5 — MOUTH

3 in the logo (on the left-outer, left-inner, and centre blades — never on the right
pair; the asymmetry is deliberate).

Let `W` = mouth half-width. Corners at `(±W, 0)` in mouth-local space, `+y` down.

```
lower lip:  Q control (0, +1.028·W)   → belly at +0.514·W
upper lip:  Q control (0, +0.349·W)   → belly at +0.175·W
gap at centre = 0.339·W
```

- **Fill** `CORE_BLACK #05171B`; **outline** `OUTLINE_NAVY` 0.089 W wide, α 0.80.
- **Teeth:** exactly **6**, `CREAM_TOOTH #FBF7E8`. Each is a triangle with a
  top edge of length `W/3` lying on the upper lip curve, apex at the **midpoint** of
  that edge, dropped `0.473·W`.
  Since `0.473 W > 0.339 W`, **the teeth are longer than the mouth is open — they
  break the lower-lip silhouette.** That overshoot is what makes them read as fangs
  and drool at once. Do not clip them.
- **Tongue:** a lens of half-width `0.301·W`, hanging from `y = +0.487·W`,
  apex `+0.744·W`. Fill `FLESH_PINK #E77E9A`.
- **Gum blush:** two ellipses at `x = ±0.914·W`, `y = +0.171·W`,
  `rx = 0.325·W`, `ry = 0.161·W`, `FLESH_PINK` at α 0.45. Corners only.

**Placement on a blade:** corner line at `t = 0.28 L`; `W_mouth ≈ 0.68 × blade max
half-width`.

---

### M6 — VINE

6 strands in the logo. Each is a **polyline of 47 sampled points**, drawn twice:

1. shadow pass — `VINE_SHADOW #08462F`, width `1.36 × core width`, α 0.55, round caps
2. core pass — `VINE_GREEN #0E6B4F`, round caps

Measured strands (width, arc length, total turning, min curvature radius):

| strand | core w | arc len | total turn | min bend radius |
|---|---|---|---|---|
| left halo | 11 | 694 | 145° | 136 |
| right halo | 11 | 694 | −145° | 136 |
| bottom sweep | 8 | 473 | −52° | 41 |
| left upper | 9 | 238 | 31° | 63 |
| right upper | 9 | 238 | −31° | 63 |
| base swag | 10 | 573 | −61° | 113 |

**Curvature rule.** `min_bend_radius ≥ 4 × core_width` and
`≥ 0.04 × emblem_width`. Total turning per strand between 30° and 150°. A vine that
turns more than 180° becomes a spiral and reads as decorative wrought iron — wrong
register. A vine that turns less than 25° reads as a cable — also wrong, though it
is the correct read for Stage 5 conduit, which is a different motif.

Strands hug the halo: radial extent stays inside `r ∈ [298, 422]`, i.e. they wrap
the machine rather than crossing it.

**SUCKER (sub-part).** Exactly **3 per strand** in the logo, at roughly `t = 0.25,
0.50, 0.75` of the visible run. Each is:
- outer disc `r = 0.58 × core width`, fill `VOID_RIM #0A3138`, stroke `OUTLINE_NAVY`
  `0.19 × core width`
- core disc `r = 0.42 × outer r`, `FLESH_PINK`, α 0.80

For procedural strands use fixed arc spacing of `6–8 × core width`, capped at 5 per
strand. The pink core is the only warm colour in the entire vine and it is 4 px wide —
that scarcity is the effect.

**Tips.** Each strand ends in one or more `LEAF_BLADE` at `L = 0.19–0.28 ×` the main
blade length, rotated arbitrarily (see M3).

---

### M7 — CIRCUIT_TREE

The thesis. A "plant" whose entire topology is a PCB trace.

Geometry in the logo (local coordinates, `+y` down, all lengths LU, all strokes
`VINE_GREEN`):

```
trunk        (500,792) → (500,566)          w15   len 226   round cap
root flare   (500,780) C (470,794)(448,800)(428,792)   w8   [MIRRORED]
crossbar     (372,730) → (628,730)          w11   len 256   round cap
corner stubs (372,730) → (372,704)          w8    len  26   [MIRRORED]
             (372,730) → (336,704)          w8    len  44 @ 35.8°  [MIRRORED]
branch L     (500,636) → (424,636) → (424,600)   w8   miter, 90.0°
branch R     (500,676) → (576,676) → (576,640)   w8   miter, 90.0°
pads         (307,704)→(365,704) w6 · (635,704)→(693,704) w6
             (395,600)→(453,600) w6 · (548,640)→(604,640) w6
             (465,566)→(535,566) w6
```

**Rules extracted:**

1. **Width ladder.** `15 → 11 → 8 → 6`. Ratio `0.735 ± 0.02` per rank.
   Maximum **4 ranks**. A fifth rank disappears at game distances.
2. **Length quantisation.** Every segment's length is 3–16× its own stroke width.
   Measured: trunk 15.1w, crossbar half 11.6w, branch run 9.5w, pad 9.7w,
   vertical stub 4.5w, corner stub 3.25w.
3. **Right-angle branching.** A branch leaves its parent by running **perpendicular**
   for a run of 9–10× its width, then turning **exactly 90°** toward the tip.
   `stroke-linejoin: miter`. Fillet radius **zero**.
4. **Two sanctioned exceptions**, and only these:
   - the **root flare** at the very bottom is a cubic Bézier — the only curve in
     the tree. It is where the machine pretends to be planted.
   - the **corner stubs** take off at 35.8°, not 90°. Two of them, at the outer ends
     of the crossbar, mirrored.
   Everything else is orthogonal. If a builder adds a third exception the motif dies.
5. **Terminal pad.** Every growth point ends in a bar perpendicular to the last
   segment, length `9.7 × own width`, width `0.75 ×` the branch that feeds it. The
   `LEAF_BLADE` is then planted at the pad's midpoint. Component on a solder pad.
6. **Node dots.** Where a right-angle turn is not terminated by a pad, place a
   `SUCKER` (M6 sub-part) at the corner: `r = 0.58 × width`, `FLESH_PINK` core.
   The logo puts 3 of these on the base swag.

**Layout of the 5 crown blades on the tree** (this exact asymmetry is canon):

| pad | blade L | tip height above pad |
|---|---|---|
| left outer (336,704) | 250 | 250 |
| left inner (424,600) | 272 | 272 |
| centre (500,566) | 348 | 348 |
| right inner (576,640) | 250 | 250 |
| right outer (664,704) | 250 | 250 |

Pad *heights* are staggered (704 / 600 / 566 / 640 / 704) which produces the
splayed-hand read; blade lengths are near-uniform except the centre spike. Mouths on
left-outer, left-inner and centre only.

---

### M8 — VOID (the blot)

Not a shape, a fill: `BLOT_GRAD` (see M4). Used for the iris field, the mouth
interior, the eye drips, and — at Stage 4+ — for any hole the entity opens in a
surface. It has one property worth stating separately: **it never has a specular
highlight and never receives the scene's ambient.** In `game/app.py` terms it is
drawn with `unlit=True` and a colour that ignores `self.ambient`. A black that
responds to lighting reads as paint; a black that does not respond reads as absence.

---

## 2. Palette

Named constants, exactly as they appear in `game/entity_style.py`. Ordered by
frequency in the SVG.

| Constant | Hex | RGB | Used by |
|---|---|---|---|
| `LEAF_TEAL` | `#3FB3A0` | 63,179,160 | M3 gradient tip, M3 chevron ribs |
| `LEAF_MID` | `#12867A` | 18,134,122 | M3 gradient 0.82 |
| `LEAF_DEEP` | `#0B5C51` | 11,92,81 | M3 gradient 0.40 |
| `LEAF_ROOT` | `#06302A` | 6,48,42 | M3 gradient 0.00 |
| `OUTLINE_NAVY` | `#0E2033` | 14,32,51 | **every** silhouette outline — M1 gears, M3 blades + midrib, M5 mouth, M6 sucker rings. Never M4: the eye is rimmed in `RUST`/`BRONZE_LIGHT` instead, which is why it sits *on* the leaf rather than *in* it. |
| `CORE_BLACK` | `#05171B` | 5,23,27 | M4 iris mid, M4 pupil, M4 drips, M5 interior |
| `VOID_DEEP` | `#02100F` | 2,16,15 | M4 iris rim (outermost stop) |
| `VOID_RIM` | `#0A3138` | 10,49,56 | M4 iris centre, M6 sucker outer disc |
| `CREAM_LIGHT` | `#FBEFC6` | 251,239,198 | M2 glory + rays, M1 rivet highlight, halo rings |
| `CREAM_TOOTH` | `#FBF7E8` | 251,247,232 | M5 teeth **only** |
| `CREAM_SCLERA` | `#F4F7F1` | 244,247,241 | M4 lens white **only** |
| `BRONZE_DARK` | `#8A6428` | 138,100,40 | M1 gear gradient bottom, M1 rivet body, M1 hatch |
| `BRONZE_MID` | `#C79B45` | 199,155,69 | M1 inner ring flat fill, M1 gradient mid |
| `BRONZE_LIGHT` | `#E8BC55` | 232,188,85 | M1 gradient, M2 ray gradient bottom, M4 band 2 |
| `BRONZE_PALE` | `#EBD08A` | 235,208,138 | M1 gradient top stop |
| `VINE_GREEN` | `#0E6B4F` | 14,107,79 | M6 core, **all of M7** |
| `VINE_SHADOW` | `#08462F` | 8,70,47 | M6 shadow pass |
| `FLESH_PINK` | `#E77E9A` | 231,126,154 | M5 tongue, M5 gum blush, M6 sucker core, M7 node dots |
| `CYAN_GLINT` | `#2AA8C4` | 42,168,196 | M4 band 4, M4 lens underglow |
| `SIGNAL_BLUE` | `#1B4C9B` | 27,76,155 | M4 band 3 **only** |
| `RUST` | `#B5652A` | 181,101,42 | M4 band 1 **only** |

### Gradients

| Name | Kind | Stops |
|---|---|---|
| `LEAF_GRAD` | linear, base→tip, raked 8.5° | `LEAF_ROOT` 0.00 · `LEAF_DEEP` 0.40 · `LEAF_MID` 0.82 · `LEAF_TEAL` 1.00 |
| `BLOT_GRAD` | radial, `c=(0.50,0.42) r=0.62` | `VOID_RIM` 0.00 · `CORE_BLACK` 0.60 · `VOID_DEEP` 1.00 |
| `GEAR_GRAD` | linear, `(0.1,0)→(0.9,1)` | `BRONZE_PALE` 0.00 · `BRONZE_MID` 0.50 · `BRONZE_DARK` 1.00 |
| `GLORY_GRAD` | radial | `CREAM_LIGHT` α0.55 · `CREAM_LIGHT` α0.32 @0.62 · `BRONZE_LIGHT` α0.00 |
| `RAY_GRAD` | linear, vertical | `CREAM_LIGHT` α0.95 · `BRONZE_LIGHT` α0.35 |

### Colour discipline

- **Bronze and teal never blend.** They meet along a navy outline. Any pixel that is
  a bronze-teal mix is a bug.
- **`FLESH_PINK` is rationed.** Across a 1000×1000 emblem it covers under 0.4% of the
  pixels. In-engine, cap it: no more than **three pink elements visible in one
  frame** before Stage 4.
- **Blue appears exactly once**, as eye band 3. It is not a theme colour. Resist the
  urge to use it for UI.
- The village's own palette is the muted Disco/Zomboid set already in
  `game/world.py OBJ_COLORS`. Entity colours are *more saturated* than the village.
  That contrast is the whole StrangerVille lesson (`_bench/BRIEF.md` §2): the
  ordinary must stay ordinary and slightly drab, so the intrusion is the only
  saturated thing on screen.

---

## 3. Escalation ladder

Five stages. The village is supposed to look ordinary; these stages are the schedule
on which it stops. Each stage names (a) the in-engine change, (b) the file it lands
in, (c) the density budget, (d) the capture command that photographs it.

To make the ladder photographable, `tools/capture.py` gains one flag:

```
--taint N        # 0..5, forces game.state.entity_stage before the warmup frames
```

Without that flag a critic cannot see stage 2 and, per `_bench/BRIEF.md` §4, a
feature a critic cannot photograph does not exist.

`game/state.py` gains `entity_stage: int = 0`, driven by quest progress in
`game/controllers/quest_controller.py`.

---

### Stage 1 — SALAH SUDUT · "the wrong angle"

**Nobody notices. That is the requirement.** A player who screenshots this frame and
a clean frame side by side should have to hunt.

| | |
|---|---|
| **Budget** | ≤ 3 tainted elements in the whole scene; none within 4 m of the player spawn; total tainted screen area < 0.15% |
| **Colour** | none of the entity palette is *introduced*; only geometry changes |

Concrete changes:

1. **`game/scenes/props.py` → `build_tree`, `build_palm`.** Add
   `taint_joint(seed)`: on 3 designated prop instances, exactly **one** branch leaves
   the trunk at 90.0° about a world axis instead of the usual 35–60° about the
   branch's own frame, with the fillet removed. Branch length snaps to
   `0.25 m × k`. Nothing else about the tree changes.
2. **Puddle glint.** In `game/scenes/farm.py` and `town.py`, one water plane gets its
   specular tint shifted from the sky colour to `BRONZE_LIGHT` at 12% —
   a single warm sparkle that is the wrong colour for the sky above it. Reads as a
   coin at the bottom of the puddle. It is not a coin.
3. **One fence post** in `build_house_block` has its top cut as a `GEAR_RING` crest —
   a 22.5° square crenellation — instead of a bevel. One post. Not the row.

**Capture:** `python tools/capture.py --out _bench/shots/taint1_farm.png --scene farm --taint 1 --hour 9 --frames 90 --width 1920 --height 1080`

---

### Stage 2 — POLA · "the pattern"

The player can now find it if they look. It is still deniable — everything visible
could be a coincidence, a mould, a manufacturing mark.

| | |
|---|---|
| **Budget** | ≤ 12 tainted elements; ≤ 1 `EYE` in the frame and it must be `< 24 px` tall; tainted screen area < 1.5% |
| **Colour** | `VINE_GREEN`, `BRONZE_DARK` and `LEAF_ROOT` may appear. No `FLESH_PINK`, no `CYAN_GLINT`, no `CREAM_LIGHT`. |

Concrete changes:

1. **`CIRCUIT_TREE` in the undergrowth.** A new prop builder
   `build_circuit_shrub(world, wx, wz)` in `props.py`: 2 ranks of the width ladder
   (8 → 6), 4 pads, no blades — just bare right-angled `VINE_GREEN` trace lying flat
   in the grass, ~0.6 m across. Read at a distance: a dead branch. Read up close: a
   PCB.
2. **`GEAR_RING` weathering.** `OBJ_COLORS` entries for `WL` (wall) and `GT` (gate)
   gain a decal pass: the 36-tooth inner-ring profile stamped at 0.25 m, `BRONZE_DARK`
   at α 0.35, on the north face of three buildings. Reads as rust bloom.
3. **One blind eye.** A single `EYE` at `S = 0.35`, **pupil absent** (crescent only,
   no `SIGNAL_BLUE` band — bands 0, 1, 2 only), inside a `build_ore` crystal or under
   the lantern glass in `build_lantern`. Under 24 px on screen it reads as a
   reflection.
4. **NPC posture.** In `game/npc_brain.py`, one villager's idle animation gains a
   4-frame hold where the head yaw snaps to an **exact 90°** off their body axis and
   holds for 1.2 s before easing back. No sound, no music cue. Sims 1 idles do not
   snap; this one does.

**Capture:** `--scene town --taint 2 --hour 14`

---

### Stage 3 — TUMBUH · "it is growing"

The village is still running normally around it — shops open, NPCs queue for the
well — and that is what makes it land. Do not stop the simulation.

| | |
|---|---|
| **Budget** | ≤ 40 tainted elements; up to 4 `EYE`, one of which may be pupilled; ≤ 3 `FLESH_PINK` elements; tainted area < 8% |
| **Colour** | full palette unlocked except `CREAM_LIGHT`/`GLORY` — the entity has no halo yet |

Concrete changes:

1. **Infected crops.** `game/scenes/farm.py` and `greenhouse.py`: a `taint_level`
   per crop tile. At level ≥ 1 the crop's mesh is swapped (via the existing
   mesh-swap path in `game/base_actor.py`) for `leaf_blade()` at `L = 0.4 m`, with
   `LEAF_GRAD` and the chevron ribs. At level ≥ 2 it grows a secondary `EYE` at
   `t = 0.40 L`. Crops still harvest; they still give yield; the yield item icon is
   unchanged. **The economy must keep working.**
2. **`VINE` on architecture.** `build_house_block` gains an optional vine pass: 1–2
   strands, `min_bend_radius = 4 × width`, 3 suckers each, climbing the wall and
   ending in 2 arbitrary-rotation blade tips. The suckers are the first pink in the
   game.
3. **Infected villagers.** In `game/mob.py` / `game/npc.py`: eyes swap to the
   `EYE` band stack at `S = 0.18` scaled to the head, **blind variant**, plus the
   shared vacant posture. They still walk their schedules, still greet the player,
   still queue. Their dialogue in `game/data.py` is unchanged Indonesian small talk.
   The horror is that nothing about them has changed except the eyes.
4. **HUD.** `game/panels.py`: the motive thermometers gain a 1-px `VINE_GREEN`
   right-angle tick at the top of one bar. Never animated. Never explained.

**Capture:** `--scene farm --taint 3 --hour 11` and `--scene town --taint 3 --hour 18`

---

### Stage 4 — MESIN · "the machine under the field"

The lab / `naga_cave` / `dungeon` register. The entity's own architecture, seen from
inside. This is where `GEAR_RING` and `CIRCUIT_TREE` become the *building*, not
decoration.

| | |
|---|---|
| **Budget** | unbounded inside the entity's own spaces; **hard cap of Stage 3 budgets in any outdoor village scene** |
| **Colour** | full palette. `GLORY` allowed but only as a floor seal, never in the sky. |

Concrete changes:

1. **Floor seal.** `game/scenes/naga_cave.py`: the full emblem projected at
   `E = 6.0 m` on the chamber floor — outer `GEAR_RING` (16 teeth, 24 rivets), inner
   ring (36 teeth), the 48+16 ray fan baked into the diffuse, `CIRCUIT_TREE` in
   `VINE_GREEN` emissive at 0.4. The five crown blades are *absent* — they are
   standing up elsewhere in the room as 3 m props.
2. **Conduit.** `VINE` degenerates into its Stage-4 form: total turning drops below
   25°, so the strands read as cable, and they run in `CIRCUIT_TREE` orthogonal
   bundles along the ceiling. Same colours, opposite curvature rule. That reversal is
   the reveal: the vines were always wiring.
3. **The wall of eyes.** A grid of `EYE` at three scales (1.00 / 0.35 / 0.12) with
   the full 5-band stack, pupils on the stable 50%, drips on all. Lit only by their
   own `BLOT_GRAD` — the room's lights do not reach them.
4. **UI corruption.** `game/panels.py`: the blue Sims-1 control panel keeps working
   perfectly, but its corner rivets become `RIVET` (bronze + centre-facing cream
   highlight) and the mood bar's fill gains the `LEAF_GRAD` ramp. The clock still
   tells the right time. **Never break a control the player needs.**

**Capture:** `--scene naga_cave --taint 4` and `--scene dungeon --taint 4`

---

### Stage 5 — WUJUD · "manifestation"

The emblem, at scale, in the sky over an unchanged village. One frame. It should be
the only frame in the game that looks like the logo.

| | |
|---|---|
| **Budget** | the emblem occupies 35–55% of frame height, centred above the horizon; the village below is rendered **exactly as at Stage 0** |
| **Colour** | everything |

Concrete changes:

1. **`game/sky.py`**: the skydome gains the emblem at `E = 240 m`, drawn in this
   order — `GLORY_GRAD` disc, 48 fine rays, 16 broad rays, outer `GEAR_RING` with
   rivets and hatch, halo rings, inner `GEAR_RING`, the six `VINE` strands, the
   `CIRCUIT_TREE`, then the five blades with their eyes and three mouths.
   The gear rings **rotate at 0.6°/s in opposite directions**. Nothing else moves.
2. **`game/app.py`**: `target_sun` shifts to `CREAM_LIGHT`, `target_amb` to a
   bronze-tinted value. The village's own materials are untouched — they are simply
   lit by the wrong sun. The shadow direction changes to point away from the emblem.
3. **The village keeps running.** NPC schedules, shop hours, the harvest timer, the
   clock in the control panel — all normal. An NPC walks past selling *pisang goreng*.
   That is the shot.
4. **Sound** (`game/sound.py`): ambient birds and market noise continue at full
   volume. The entity's own layer is a sub-30 Hz bed and the 4-note Disco motif
   already in the project. No sting. No riser.

**Capture:** `--scene town --taint 5 --hour 16 --frames 120`

---

## 4. The tell

> **Right angles where nature would curve.**

Written as a rule a builder can apply to any asset:

### RULE — ORTHOGONALITY INTRUSION

**Applies to:** anything that represents growth or flow — plants, water edges, cloth,
hair, smoke, footpaths, rust bloom, cracks, flesh, roots, flocking, queue lines.
**Does not apply to:** anything already man-made (walls, fences, tools, the HUD).
Man-made things are already orthogonal; tainting them says nothing.

**Procedure.**

1. Enumerate the asset's **joints** `J` — every point where a child leaves a parent,
   or where a silhouette changes direction by more than 15°.
2. Record each joint's natural parameters: turn angle `θ` (typically 30–60° off the
   parent axis, sampled continuously), fillet radius `f` (typically
   `≥ 0.15 × parent thickness`), child thickness ratio `ρ` (continuous, 0.5–0.8),
   child length `ℓ` (continuous).
3. Choose `k = TAINT_JOINTS[stage]` joints to replace:
   `[0, 1, 3, 8, 24, ALL]` for stages 0–5. Selection is seeded off the object id so
   it is **stable across frames** — a joint that flickers between natural and
   orthogonal is a jump-scare.
4. At each chosen joint, overwrite:
   - `θ := 90.0° ± 0.25°`, taken about a **world** axis (`±X`, `±Z`, `+Y`),
     never about the parent's local frame. This is what makes it look *imposed*
     rather than grown: a whole hedgerow of tainted joints all turn the same way,
     regardless of how each plant is rotated.
   - `f := 0` — hard miter. No fillet, no bevel, no smoothing group across the corner.
   - `ρ := 0.735` — snapped to the width ladder (§M7 rule 1), max 4 ranks.
   - `ℓ := M · round(ℓ / M)` with `M = 0.25 m`, and additionally clamped so
     `ℓ ∈ [3, 16] × child_thickness`.
   - the child terminates in a **stub + pad**: a perpendicular bar of length
     `9.7 × child_thickness`, width `0.75 × child_thickness`.
   - if the joint is *not* terminal, place a node dot: radius
     `0.58 × child_thickness`, `VOID_RIM` disc, `FLESH_PINK` core at `0.42` of that.
5. **Leave one curve.** Every tainted asset keeps exactly one Bézier — at its base,
   where it meets the ground. That is the root flare from §M7 rule 4. It is the lie
   the object tells about being alive, and without it the object is merely a machine
   and nobody is unsettled by a machine.

**Sanity checks a builder can run on any asset:**

- Does a photograph of the asset at 30 m still read as a plant? If no, you went
  past the stage budget.
- Does the asset have **two or more** curved exceptions? If yes, delete one.
- Do the tainted joints in a group of assets all turn toward the **same world
  direction**? If no, you rotated about the local frame — fix it, this is the entire
  effect.
- Is any corner filleted, bevelled, or smoothed? If yes, it reads as design.
  It must read as a mistake in the growth.

---

## 5. What it must never look like

Named failure modes. Each one is a way this document gets thrown away.

**5.1 — Jump-scare vocabulary.** Banned outright:
- anything that appears **because the camera looked at it** or disappears because the
  camera looked away
- a face that is not present in frame N and is present in frame N+1 at the same pixel
- audio stings, risers, sub-bass hits synchronised to a visual
- eyes that open, blink, or track the player. The eyes in the logo are **rolled back
  and blind**. They are not watching you; that is worse.
- strobing, flicker, per-frame random. Everything the entity does is either static or
  on a slow constant rate (see the 0.6°/s gear rotation).
- The horror is spiritual and slow (`_bench/BRIEF.md` §1). If a change would work in
  a 15-second horror clip, it is wrong for this game.

**5.2 — Gore.** No blood, no wounds, no viscera, no body horror of the human form.
`FLESH_PINK` is a *gum and sucker* colour and it is rationed to under 0.4% of pixels.
The mouth has clean teeth and a clean tongue. There is nothing wet in this design.
The pink exists to make the machine feel like it has a mucous membrane, which is
unsettling precisely because it is so small and so tidy.

**5.3 — Generic horror kit.** None of the following exist in this project:
- red. There is no red in the palette. `RUST #B5652A` is a bronze-orange used as a
  3.6 px eye rim, nothing else.
- black voids with white text, "static", VHS scanlines, glitch-shader RGB split
- pentagrams, upside-down crosses, occult runes, Latin
- cobwebs, dripping candles, skulls, ravens, crows, fog machines
- tentacles as *threat*. The vines in the logo coil around the halo like ivy on a
  gate. They hold. They do not reach for the camera.

**5.4 — Alien/sci-fi drift.** StrangerVille is the structural reference, **not the
art reference** (`_bench/BRIEF.md` §2). Banned: purple, chartreuse, hazmat orange,
"biolab" cyan glow, UFO silhouettes, translucent slime. Our machine is **bronze** —
a colour that means old, votive, and made by hand.

**5.5 — Symmetry.** The gears are symmetric; the creature must not be. If all five
blades are the same height, all have mouths, and all eyes have pupils, it becomes a
logo again. It has to look like something that grew wrong, not something that was
designed.

**5.6 — Breaking the ordinary.** The single largest failure available. If the shop
closes, the NPCs stop walking, the clock freezes, the music drops out, or the
control panel stops working, the effect dies. **The mundane must keep running
normally around the intrusion.** At Stage 5, with the emblem filling half the sky,
an NPC is still selling fried bananas at the correct in-game hour.

**5.7 — Overuse.** The density budgets in §3 are not suggestions. The most common
way to ruin this is to put a small `CIRCUIT_TREE` on every third prop because the
helper function is fun to call. Three tainted elements at Stage 1. Three.

---

## 6. `game/entity_style.py`

Written. Constants are real and measured; the mesh helpers are declared with honest
signatures and `NotImplementedError` bodies so nothing silently returns a cube.

```python
gear_ring(r_body, *, teeth, tooth_h_ratio=1.174, hole_ratio=0.832,
          duty=0.368, rivets=0, thickness=0.02, segments_per_flank=1) -> Mesh
eye_disc(height, *, bands=EYE_BANDS, pupil=True, lobes=16,
         wobble=0.06, aspect=0.740, drips=3, seed=0) -> list[Entity]
leaf_blade(length, *, width_ratio=0.165, ribs=None, midrib=True,
           specular_wedge=True) -> Mesh
vine_curve(points, *, core_width, suckers=3, shadow=True,
           min_bend_factor=4.0) -> list[Mesh]
circuit_branch(origin, direction, *, rank=0, run_ratio=9.5, stub_ratio=4.5,
               pad=True, node_dot=False) -> list[Mesh]
```

Read the module for the full parameter documentation and the measured tables
(`LEAF_PROFILE`, `EYE_BANDS`, `MOUTH_PROFILE`, `WIDTH_LADDER`, `GEAR_OUTER`,
`GEAR_INNER`, `TAINT_JOINTS`).

---

## Appendix A — concentric radius chart

Everything in the emblem, from the halo centre outward, in LU.

| r | what |
|---|---|
| 228 | inner gear hole — edge of the cream field |
| 236 | inner gear body |
| 246 | cream ring, w2, α0.55 |
| 250 | inner gear tooth tip (36 teeth) |
| 256 | cream ring, w4, α0.85 |
| 268 | navy ring, w8 — outer gear hole |
| 272 → 318 | 80 radial hatch lines, `BRONZE_DARK` w4 α0.40 |
| 296 | rivet ring — 24 rivets, r7 |
| 298 → 422 | band the six `VINE` strands stay inside |
| 300 | ray fan base (both fans) |
| 322 | outer gear body |
| 378 | outer gear tooth tip (16 teeth) — **`R_TIP`, the machine's hard edge** |
| 388 / 424 | short / long tips of the 48 fine rays |
| 408 | tips of the 16 broad rays |
| 412 | `GLORY_GRAD` glow disc |

## Appendix B — inventory counts in the logo

| motif | count |
|---|---|
| gear rings | 2 (16 teeth, 36 teeth) |
| rivets | 24 |
| radial hatch lines | 80 |
| fine rays | 48 (alternating length) |
| broad rays | 16 |
| leaf blades | 20 (5 crown + 15 vine tips) |
| eyes | 14 (7 pupilled, 7 blind) |
| mouths | 3 (6 teeth each = 18 teeth) |
| vine strands | 6 |
| suckers / node dots | 9 |
| circuit-tree segments | 13 (incl. 5 pads, 2 curved root flares) |
