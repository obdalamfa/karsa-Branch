# Ursina 3D Scene & Level Editor

A standalone, visual 3D scene and level editor built with the **Ursina Engine**. Design levels visually, manipulate objects with 3D gizmos, inspect properties in real-time, test your level in First-Person Play Mode, and export ready-to-run Python code!

---

## What's New & GUI Usability Improvements

- **Undo / Redo System (`Ctrl+Z` / `Ctrl+Y`)**:
  - Full history tracking for all scene actions (transforms, creation, deletion, duplication, load).
  - Dedicated `Undo` and `Redo` buttons on the top toolbar.
- **Enhanced Hierarchy Outliner**:
  - **Live Search & Filter**: Instant search bar to filter objects by name, model, or tag in real time.
  - **1-Click Visibility Toggle (`V` / `-`)**: Hide or show objects directly from the hierarchy row.
  - **1-Click Focus (`F`)**: Jump camera focus to any object with a single click.
  - **Color-Coded Model Badges**: Distinct visual badges (`[CUB]`, `[SPH]`, `[CYL]`, `[PLN]`, `[CON]`, `[SPW]`).
  - **Quick Add Menu**: Clean primitive shelf for Cube, Sphere, Cylinder, Plane, Cone, and Player Spawn.
  - **Deselect All**: Dedicated button to clear current selection.
- **Ergonomic Inspector Panel**:
  - **Quick Transform Tools**: 1-click buttons for `Pos 0`, `Floor` (snap bottom to Y=0 ground), `Rot 0`, and `Scale 1`.
  - **Configurable Step Multipliers**: Choose step size (`0.1`, `0.5`, `1.0`, `5.0`) with `--`, `-`, `+`, `++`, and `0` reset buttons.
  - **Fast Degree Rotation**: Quick buttons for `-90°`, `-15°`, `+15°`, `+90°`, and `0°` reset.
  - **Uniform Scale Presets**: `x0.5`, `- Step`, `+ Step`, `x2.0`, and `Reset 1.0`.
  - **1-Click Texture Selector**: Visual buttons for `None`, `Brick`, `Grass`, `Shore`, and `White Cube` (no more blind cycling!).
  - **1-Click Collider & Tag Selectors**: Clear segmented buttons for colliders (`None`, `Box`, `Sphere`, `Mesh`) and gameplay tags (`#default`, `#ground`, `#obstacle`, `#hazard`, `#pickup`, `#spawn`).
  - **16-Color Palette**: Curated palette with active preview and white reset.
- **Top Toolbar & Viewport Controls**:
  - **Camera View Presets**: Quick switch between `Iso`, `Top`, `Front`, `Side`, and `Reset` view angles (hotkeys `1`, `3`, `7`, `0`).
  - **Grid Snapping**: Granular levels (`0.25`, `0.5`, `1.0`, `2.0`, `OFF`).
  - **Grid Visibility Toggle**: Toggle ground grid on/off.
  - **In-App Help Modal (`H` / `F1`)**: Interactive shortcuts guide accessible anytime.
- **Keyboard Protection**:
  - Editor hotkeys are automatically silenced when typing inside input fields (e.g. search bar or rename).
- **Flexible Execution**:
  - Run directly via `python main.py` or from parent directory `python -m ursina_editor.main`.

---

## How to Run

Launch the editor from your terminal:

```bash
# From the repository root:
python -m ursina_editor.main

# Or from within the ursina_editor folder:
python main.py
```

The editor writes `scene.json` and `exported_scene.py` next to its own package,
**not** in the current working directory. Both are ignored by git — they are
session output, not part of the game.

---

## Menyunting peta Lembah Karsa

Tekan **`K`** untuk membuka panel peta. Panel itu berdiri sendiri karena ia
mengurus **grid ubin** milik game, sedangkan seluruh panel lain di editor ini
mengurus **entity bebas** — dua model yang berbeda, dan mencampurnya di satu
toolbar akan membuat keduanya terlihat seperti satu.

Alurnya: pilih scene dari daftar, pilih jenis ubin dari palet, lalu **klik ubin
di viewport untuk mengecat**. Tombol `SIMPAN PETA` menulis
`game/scenes/<nama>.json`.

Ubin ditampilkan memakai **tekstur asli game** dari `assets/textures/`, bukan
warna karangan, supaya peta terlihat seperti di game. Empat ubin (PALM, TV, CHR,
CAL) tidak punya tekstur di `world.py`; keempatnya memakai warna netral dan
ditandai `?` di palet.

### Yang belum bisa dilakukan di sini

Editor ini memakai gizmo transform untuk memindahkan, memutar, dan menskalakan
entity. Itu **tidak berlaku untuk ubin**: ubin menempati sel grid, jadi
"memindahkan" sebuah ubin berarti menulis ulang dua sel, bukan menggeser posisi.
Karena itu penyuntingan ubin memakai klik-untuk-mengecat.

Objek bebas yang bisa digeser dengan gizmo — furnitur, pohon, bangunan — belum
tersimpan di game. Dunia game adalah grid, bukan daftar entity. Lapisan objek
terpasang adalah pekerjaan tersendiri.

### Setelah menyimpan

Jalankan dari akar repo:

```bash
python tools/scene_export.py --check
```

Perintah itu mengadu **berkas data melawan kode**. Kalau hasil editan Anda
menyimpang dari `game/scenes/<nama>.py`, ia menyebut ubin yang berbeda beserta
koordinatnya. Itu memang tujuannya: kode dan data tidak boleh berbeda diam-diam.

```bash
python tools/scene_export.py --check farm town   # scene tertentu saja
python tools/editor_smoke.py                     # uji editor tanpa membuka jendela
```

---

## Controls & Shortcuts Reference

| Action | Shortcut / Input |
|---|---|
| **Orbit Camera** | Right Mouse Button + Drag |
| **Pan Camera** | Middle Mouse Button (or Shift + Right Mouse Button) + Drag |
| **Zoom Camera** | Mouse Scroll Wheel |
| **Select Object** | Left Click on object in 3D scene or hierarchy |
| **Deselect** | Left Click on empty space or click `Deselect` |
| **Translate Object (Move)** | Drag Gizmo Handles or press `W` / `G` / `T` |
| **Rotate Object (45°)** | Press `E` or `R` (Press `Shift + R` for -45°) |
| **Focus Camera on Selection** | Press `F` or click `Focus [F]` |
| **Camera View Presets** | `1` = Front View, `3` = Side View, `7` = Top View, `0` = Reset View |
| **Undo Action** | `Ctrl + Z` or click `Undo` |
| **Redo Action** | `Ctrl + Y` or click `Redo` |
| **Duplicate Selected Object** | `Ctrl + D` or click `Duplicate` |
| **Delete Selected Object** | `Delete` / `Backspace` or click `Delete` |
| **Quick Save Scene** | `Ctrl + S` or click `Save` |
| **Toggle Play Mode** | Press `P` or click `Play Mode [P]` |
| **Exit Play Mode** | Press `Esc` |
| **Toggle Peta Karsa** | Press `K` |
| **Cat ubin (peta Karsa)** | Klik kiri pada ubin di viewport |
| **Toggle Shortcuts & Help** | Press `H` or `F1` or click `? Help [H]` |

---

## Exporting Your Scene to Python

When you're happy with your level design:
1. Click the **Export Code** button on the top toolbar.
2. The editor generates `exported_scene.py` in your working directory.
3. Run the standalone game immediately:
   ```bash
   python exported_scene.py
   ```
