"""
🌾 Lembah Karsa 3D - Dedicated Level & Scene Editor (Modern Premium UI)
Visual 3D/Isometric Tilemap Editor with modern glassmorphism aesthetic and intuitive controls.

Run from terminal:
    python karsa_level_editor.py
"""
import sys
import os
import json
import time

repo_root = os.path.dirname(os.path.abspath(__file__))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from ursina import (
    Ursina, window, camera, color, mouse, held_keys,
    Entity, Button, Text, Grid, Sky, DirectionalLight, AmbientLight,
    EditorCamera, Vec2, Vec3, Color, destroy
)

from game.config import (
    TILE_SIZE, GROUND_H, WALL_H, TREE_H, HOUSE_H, OBJ_H,
    G, D, P, W, FL, WL, TR, H, MB, DR, FN, GT, BD, ST, TB, BS,
    MR, FP, CL, PP, CH, CT, SH, GR, LN, DT, CV_W, CV_F, PEN, STR_T,
    DCK, BOT, LLY, CRYS, ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH,
    STAIRS_DOWN, STAIRS_UP, MINED, SD, LGH_B, LGH_F, CLOUD, GOLD_W, PALM, TV, CHR, CAL,
    TILE_NAMES
)
from game.scenes import SCENES
from game.scenes.scene_base import Scene
from game.state import GameState
from game.world import World3D
from game.player import Player3D

# Theme Color Tokens (Sleek Modern Dark Palette)
COLOR_BG_DARK       = color.rgba(14, 17, 24, 255)
COLOR_SURFACE       = color.rgba(24, 29, 42, 235)
COLOR_SURFACE_LIGHT = color.rgba(36, 43, 60, 240)
COLOR_PRIMARY       = color.rgba(40, 150, 230, 240)
COLOR_PRIMARY_HOVER = color.rgba(60, 170, 250, 255)
COLOR_ACCENT        = color.rgba(245, 180, 50, 255)
COLOR_SUCCESS       = color.rgba(40, 170, 80, 240)
COLOR_SUCCESS_HOVER = color.rgba(55, 200, 95, 255)
COLOR_DANGER        = color.rgba(210, 55, 65, 240)
COLOR_TEXT_LIGHT    = color.rgba(240, 244, 250, 255)
COLOR_TEXT_MUTED    = color.rgba(160, 175, 195, 255)

# Visual Color Swatches for Palette Icons
TILE_SWATCH_COLORS = {
    G: color.rgb(125, 182, 85),
    D: color.rgb(176, 150, 112),
    P: color.rgb(180, 180, 180),
    W: color.rgb(88, 210, 218),
    SD: color.rgb(230, 210, 160),
    CLOUD: color.rgb(240, 248, 255),
    FL: color.rgb(150, 112, 74),
    CV_F: color.rgb(132, 118, 152),
    STR_T: color.rgb(220, 200, 120),
    DCK: color.rgb(160, 110, 60),

    WL: color.rgb(118, 105, 138),
    CV_W: color.rgb(88, 75, 108),
    GOLD_W: color.rgb(255, 223, 0),
    H: color.rgb(248, 235, 200),
    DR: color.rgb(168, 112, 62),
    GT: color.rgb(168, 130, 72),
    FN: color.rgb(178, 148, 95),
    PEN: color.rgb(155, 115, 65),
    STAIRS_UP: color.rgb(200, 170, 130),
    STAIRS_DOWN: color.rgb(160, 130, 100),

    TR: color.rgb(95, 200, 65),
    DT: color.rgb(112, 85, 55),
    PALM: color.rgb(40, 180, 100),
    PP: color.rgb(88, 215, 88),
    LLY: color.rgb(70, 190, 140),

    BD: color.rgb(196, 92, 88),
    ST: color.rgb(198, 200, 204),
    TB: color.rgb(96, 130, 122),
    CHR: color.rgb(180, 120, 70),
    BS: color.rgb(72, 96, 140),
    MR: color.rgb(165, 225, 255),
    FP: color.rgb(255, 148, 55),
    CL: color.rgb(105, 85, 68),
    CH: color.rgb(120, 92, 158),
    CT: color.rgb(206, 208, 212),
    SH: color.rgb(86, 112, 96),
    MB: color.rgb(88, 128, 228),
    LN: color.rgb(255, 248, 120),
    TV: color.rgb(50, 50, 60),
    CAL: color.rgb(220, 70, 70),
    GR: color.rgb(148, 132, 165),
    BOT: color.rgb(215, 165, 102),

    CRYS: color.rgb(208, 168, 255),
    ORE_TBG: color.rgb(215, 138, 72),
    ORE_BSI: color.rgb(165, 168, 195),
    ORE_EMS: color.rgb(255, 238, 95),
    ORE_KRS: color.rgb(198, 158, 255),
    ORE_MTH: color.rgb(165, 245, 255),
}

TILE_CATEGORIES = {
    "🌾 Tanah": [
        (G, "Rumput"), (D, "Tanah"), (P, "Jalan Batu"), (W, "Air"),
        (SD, "Pasir"), (CLOUD, "Awan/Salju"), (FL, "Lantai Kayu"),
        (CV_F, "Lantai Gua"), (STR_T, "Jerami"), (DCK, "Dermaga"),
    ],
    "🏰 Bangunan": [
        (WL, "Dinding"), (CV_W, "Dinding Gua"), (GOLD_W, "Dinding Emas"),
        (H, "Rumah Block"), (DR, "Pintu"), (GT, "Gerbang"), (FN, "Pagar Bambu"),
        (PEN, "Pagar Kandang"), (STAIRS_UP, "Tangga Naik"), (STAIRS_DOWN, "Tangga Turun"),
    ],
    "🌲 Tanaman": [
        (TR, "Pohon Rimba"), (DT, "Pohon Mati"), (PALM, "Kelapa"),
        (PP, "Pot Bunga"), (LLY, "Teratai"),
    ],
    "🪑 Perabot": [
        (BD, "Kasur"), (ST, "Kompor"), (TB, "Meja"), (CHR, "Kursi"),
        (BS, "Rak Buku"), (MR, "Cermin"), (FP, "Perapian"), (CL, "Jam Dinding"),
        (CH, "Peti Sembunyi"), (CT, "Meja Kasir"), (SH, "Rak Toko"),
        (MB, "Kotak Surat"), (LN, "Lentera"), (TV, "Televisi"),
        (CAL, "Kalender"), (GR, "Nisan"), (BOT, "Perahu"),
    ],
    "💎 Mineral": [
        (CRYS, "Kristal Murni"), (ORE_TBG, "Ore Tembaga"), (ORE_BSI, "Ore Besi"),
        (ORE_EMS, "Ore Emas"), (ORE_KRS, "Ore Kristal"), (ORE_MTH, "Ore Mithril"),
    ]
}

class KarsaLevelEditor:
    """Beautiful, intuitive Visual 3D Level & Scene Editor for Lembah Karsa 3D."""

    def __init__(self, headless=False):
        self.app = Ursina(
            title="Lembah Karsa 3D - Level & Scene Editor",
            borderless=False,
            vsync=True,
            headless=headless
        )

        window.color = COLOR_BG_DARK
        window.fps_counter.enabled = True

        # Game State & 3D World Renderer
        self.game_state = GameState()
        self.world = World3D(self.game_state)

        # Editor Variables
        self.current_scene_name = 'farm'
        self.active_tile_id = G
        self.active_tool = 'brush'  # 'brush', 'rect', 'erase', 'picker'
        self.active_category = "🌾 Tanah"
        self.show_grid_overlay = True

        self.rect_start = None
        self.hovered_tile = (0, 0)

        self.camera_mode = 'orbit'
        self.is_playing = False
        self.test_player = None

        # Setup Environment & Initial Scene
        self._setup_editor_camera()
        self.world.load_scene(self.current_scene_name)

        # Build UI Systems
        self._build_top_bar()
        self._build_sidebar()
        self._build_active_brush_card()
        self._build_bottom_bar()
        self._build_cursor_indicator()
        self._build_3d_grid_lines()
        self._build_notification()

        # Input & Update Hooks
        self.app.update = self.update
        self.app.input = self.input

    def _setup_editor_camera(self):
        self.editor_cam = EditorCamera(
            rotation=(35, -45, 0),
            position=(28, 15, -10)
        )
        self._focus_on_map()

    def _focus_on_map(self):
        sc = self.world.scene_obj
        if sc:
            cx = (sc.w * TILE_SIZE) / 2.0
            cz = (sc.h * TILE_SIZE) / 2.0
            self.editor_cam.position = Vec3(cx, 12, cz - 12)

    def _build_3d_grid_lines(self):
        """Construct visual grid lines on the 3D ground for tile alignment."""
        if hasattr(self, 'grid_mesh_entity') and self.grid_mesh_entity:
            destroy(self.grid_mesh_entity)

        sc = self.world.scene_obj
        if not sc:
            return

        w, h = sc.w, sc.h
        self.grid_mesh_entity = Entity(
            model=Grid(w, h),
            scale=(w * TILE_SIZE, h * TILE_SIZE),
            rotation_x=90,
            position=(w * TILE_SIZE / 2.0 - TILE_SIZE / 2.0, GROUND_H + 0.05, h * TILE_SIZE / 2.0 - TILE_SIZE / 2.0),
            color=color.rgba(255, 255, 255, 60),
            enabled=self.show_grid_overlay
        )

    def _build_top_bar(self):
        """Construct sleek top header toolbar."""
        bar_h = 0.06
        self.top_bar = Entity(
            parent=camera.ui,
            model='quad',
            scale=(window.aspect_ratio, bar_h),
            position=(0, 0.5 - bar_h / 2),
            color=COLOR_SURFACE,
            collider='box'
        )
        self.top_bar.is_ui = True

        # Header Title with Icon
        Text(
            parent=self.top_bar,
            text='🌾 LEMBAH KARSA 3D',
            origin=(-0.5, 0),
            position=(-0.48, 0),
            scale=0.9,
            color=COLOR_ACCENT
        )

        # Scene Dropdown Button
        self.btn_scene = Button(
            parent=self.top_bar,
            text=f"🗺️ Scene: {self.current_scene_name}",
            scale=(0.16, 0.042),
            position=(-0.21, 0),
            color=COLOR_PRIMARY,
            highlight_color=COLOR_PRIMARY_HOVER,
            on_click=self.toggle_scene_menu
        )
        self.btn_scene.is_ui = True

        self._build_scene_popup()

        # Tool Action Buttons
        tools = [
            ('🖌️ Lukis', 'brush'),
            ('📦 Isi Kotak', 'rect'),
            ('🧹 Hapus', 'erase'),
            ('🧪 Eyedropper', 'picker')
        ]
        t_w = 0.088
        for idx, (t_label, t_mode) in enumerate(tools):
            is_active = (self.active_tool == t_mode)
            btn = Button(
                parent=self.top_bar,
                text=t_label,
                scale=(t_w - 0.006, 0.042),
                position=(-0.04 + idx * t_w, 0),
                color=COLOR_PRIMARY if is_active else COLOR_SURFACE_LIGHT,
                highlight_color=COLOR_PRIMARY_HOVER,
                on_click=lambda m=t_mode: self.set_tool(m)
            )
            btn.is_ui = True

        # Grid Lines Toggle
        self.btn_grid_toggle = Button(
            parent=self.top_bar,
            text='🌐 Grid: ON' if self.show_grid_overlay else '🌐 Grid: OFF',
            scale=(0.095, 0.042),
            position=(0.30, 0),
            color=COLOR_SURFACE_LIGHT,
            on_click=self.toggle_grid_lines
        )
        self.btn_grid_toggle.is_ui = True

        # Play / Test Mode Button
        self.btn_play = Button(
            parent=self.top_bar,
            text='🎮 PLAY TEST [P]',
            scale=(0.13, 0.042),
            position=(0.425, 0),
            color=COLOR_SUCCESS,
            highlight_color=COLOR_SUCCESS_HOVER,
            on_click=self.toggle_play_mode
        )
        self.btn_play.is_ui = True

    def _build_scene_popup(self):
        """Construct popup list for switching scenes."""
        self.scene_menu = Entity(
            parent=self.top_bar,
            model='quad',
            scale=(0.20, 0.52),
            position=(-0.21, -0.29),
            color=color.rgba(20, 24, 34, 250),
            collider='box',
            enabled=False,
            always_on_top=True
        )
        self.scene_menu.is_ui = True

        scene_names = list(SCENES.keys())
        y_pos = 0.46
        for name in scene_names:
            sc_obj = SCENES[name]
            disp = getattr(sc_obj, 'display', name)
            btn = Button(
                parent=self.scene_menu,
                text=f"{name} ({disp})",
                scale=(0.92, 0.055),
                position=(0, y_pos),
                color=COLOR_SURFACE_LIGHT,
                highlight_color=COLOR_PRIMARY_HOVER,
                on_click=lambda n=name: self.switch_scene(n)
            )
            btn.is_ui = True
            y_pos -= 0.062

    def toggle_scene_menu(self):
        self.scene_menu.enabled = not self.scene_menu.enabled

    def switch_scene(self, scene_name):
        self.scene_menu.enabled = False
        if scene_name not in SCENES:
            return
        self.current_scene_name = scene_name
        self.btn_scene.text = f"🗺️ Scene: {scene_name}"
        self.world.load_scene(scene_name)
        self._build_3d_grid_lines()
        self._focus_on_map()
        self.show_notification(f"Scene dimuat: {scene_name}")

    def set_tool(self, mode):
        self.active_tool = mode
        self.show_notification(f"Alat Aktif: {mode.upper()}")
        self._build_top_bar()

    def toggle_grid_lines(self):
        self.show_grid_overlay = not self.show_grid_overlay
        self.btn_grid_toggle.text = '🌐 Grid: ON' if self.show_grid_overlay else '🌐 Grid: OFF'
        if hasattr(self, 'grid_mesh_entity') and self.grid_mesh_entity:
            self.grid_mesh_entity.enabled = self.show_grid_overlay

    def _build_sidebar(self):
        """Construct sidebar visual tile palette."""
        panel_w = 0.32
        self.sidebar = Entity(
            parent=camera.ui,
            model='quad',
            scale=(panel_w, 0.86),
            position=(-window.aspect_ratio / 2 + panel_w / 2 + 0.01, -0.015),
            color=COLOR_SURFACE,
            collider='box'
        )
        self.sidebar.is_ui = True

        Text(parent=self.sidebar, text='🎨 KATALOG UBIN', position=(-0.45, 0.46), scale=0.85, color=COLOR_ACCENT)

        # Category Tabs
        cats = list(TILE_CATEGORIES.keys())
        cols = 3
        c_w = 0.92 / cols
        for idx, cat in enumerate(cats):
            r = idx // cols
            c = idx % cols
            is_active = (self.active_category == cat)
            btn = Button(
                parent=self.sidebar,
                text=cat,
                scale=(c_w - 0.01, 0.038),
                position=(-0.46 + c * c_w + c_w / 2, 0.40 - r * 0.042),
                color=COLOR_PRIMARY if is_active else COLOR_SURFACE_LIGHT,
                highlight_color=COLOR_PRIMARY_HOVER,
                on_click=lambda name=cat: self.set_category(name)
            )
            btn.is_ui = True

        # Tile Items Container
        self.palette_container = Entity(parent=self.sidebar)
        self._refresh_palette()

        # Export Button
        self.btn_save_py = Button(
            parent=self.sidebar,
            text='💾 SIMPAN / EKSPOR KODE PYTHON',
            scale=(0.92, 0.046),
            position=(0, -0.42),
            color=COLOR_PRIMARY,
            highlight_color=COLOR_PRIMARY_HOVER,
            on_click=self.export_scene_python
        )
        self.btn_save_py.is_ui = True

    def set_category(self, cat_name):
        self.active_category = cat_name
        self._build_sidebar()

    def _refresh_palette(self):
        """Rebuild palette swatches grid."""
        for c in list(self.palette_container.children):
            destroy(c)

        items = TILE_CATEGORIES.get(self.active_category, [])
        y_start = 0.28
        for i, (tid, label) in enumerate(items):
            is_active = (self.active_tile_id == tid)
            swatch_col = TILE_SWATCH_COLORS.get(tid, color.gray)

            # Row item container
            btn = Button(
                parent=self.palette_container,
                text=f"  [{tid}] {label}",
                scale=(0.92, 0.038),
                position=(0, y_start - i * 0.044),
                color=COLOR_PRIMARY if is_active else COLOR_SURFACE_LIGHT,
                highlight_color=COLOR_PRIMARY_HOVER,
                on_click=lambda t=tid: self.select_tile(t)
            )
            btn.is_ui = True

            # Color Indicator Badge on Left
            icon_badge = Entity(
                parent=btn,
                model='quad',
                scale=(0.04, 0.7),
                position=(-0.44, 0),
                color=swatch_col
            )
            icon_badge.is_ui = True

    def select_tile(self, tid):
        self.active_tile_id = tid
        self.active_tool = 'brush'
        self._refresh_palette()
        self._update_active_card()
        name = TILE_NAMES.get(tid, f"Tile_{tid}")
        self.show_notification(f"Ubin Dipilih: [{tid}] {name}")

    def _build_active_brush_card(self):
        """Construct top-right preview card of currently selected tile."""
        card_w = 0.20
        self.active_card = Entity(
            parent=camera.ui,
            model='quad',
            scale=(card_w, 0.08),
            position=(window.aspect_ratio / 2 - card_w / 2 - 0.01, 0.43),
            color=COLOR_SURFACE,
            collider='box'
        )
        self.active_card.is_ui = True

        Text(parent=self.active_card, text='KUAS AKTIF', position=(-0.45, 0.32), scale=0.65, color=COLOR_TEXT_MUTED)

        self.card_swatch = Entity(
            parent=self.active_card,
            model='quad',
            scale=(0.14, 0.50),
            position=(-0.35, -0.15),
            color=color.gray
        )
        self.card_swatch.is_ui = True

        self.card_title = Text(
            parent=self.active_card,
            text='Rumput (G)',
            position=(-0.24, -0.15),
            scale=0.75,
            color=COLOR_TEXT_LIGHT
        )

        self._update_active_card()

    def _update_active_card(self):
        tid = self.active_tile_id
        swatch_col = TILE_SWATCH_COLORS.get(tid, color.gray)
        name = TILE_NAMES.get(tid, f"Tile_{tid}")

        self.card_swatch.color = swatch_col
        self.card_title.text = f"[{tid}] {name}"

    def _build_bottom_bar(self):
        """Construct bottom helper toolbar."""
        bar_h = 0.04
        self.bottom_bar = Entity(
            parent=camera.ui,
            model='quad',
            scale=(window.aspect_ratio, bar_h),
            position=(0, -0.5 + bar_h / 2),
            color=color.rgba(16, 19, 24, 245),
            collider='box'
        )
        self.bottom_bar.is_ui = True

        Text(
            parent=self.bottom_bar,
            text='🖱️ [LMB] Lukis Ubin   |   🖱️ [RMB + Drag] Putar Kamera 3D   |   🎮 [P] Uji Coba Game   |   Esc Keluar Uji',
            origin=(-0.5, 0),
            position=(-0.48, 0),
            scale=0.7,
            color=COLOR_TEXT_MUTED
        )

        self.status_text = Text(
            parent=self.bottom_bar,
            text='Tile: (0, 0)',
            origin=(0.5, 0),
            position=(0.48, 0),
            scale=0.7,
            color=COLOR_TEXT_LIGHT
        )

    def _build_cursor_indicator(self):
        """Construct glowing 3D selector boundary box."""
        self.cursor_box = Entity(
            model='wireframe_cube',
            scale=(TILE_SIZE * 1.02, 0.35, TILE_SIZE * 1.02),
            color=COLOR_ACCENT,
            unlit=True,
            always_on_top=True
        )

    def _build_notification(self):
        """Construct floating toast banner."""
        self.notification_banner = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.55, 0.045),
            position=(0, 0.40),
            color=color.rgba(30, 90, 160, 235),
            enabled=False,
            always_on_top=True
        )
        self.notification_banner.is_ui = True
        self.notification_text = Text(
            parent=self.notification_banner,
            text='',
            origin=(0, 0),
            position=(0, 0),
            scale=0.8,
            color=color.white
        )
        self.notification_time = 0.0

    def show_notification(self, msg, duration=3.0, bg_color=None):
        self.notification_text.text = msg
        self.notification_banner.color = bg_color if bg_color else color.rgba(30, 90, 160, 235)
        self.notification_banner.enabled = True
        self.notification_time = time.time() + duration

    def is_ui_hovered(self):
        hovered = mouse.hovered_entity
        curr = hovered
        while curr:
            if getattr(curr, 'is_ui', False) or curr == camera.ui:
                return True
            curr = curr.parent
        return False

    def paint_tile_at(self, tx, ty, tid):
        sc = self.world.scene_obj
        if not sc or not (0 <= tx < sc.w and 0 <= ty < sc.h):
            return

        if sc.tiles[ty][tx] != tid:
            sc.tiles[ty][tx] = tid
            self.world.load_scene(self.current_scene_name)
            self._build_3d_grid_lines()

    def export_scene_python(self):
        sc = self.world.scene_obj
        if not sc:
            return

        out_path = f"custom_{self.current_scene_name}.py"
        lines = [
            '"""',
            f'Custom Scene Layout: {sc.name} ({sc.display})',
            'Exported from Lembah Karsa 3D Level Editor',
            '"""',
            'from game.config import *',
            'from game.scenes.scene_base import Scene',
            'from game.scenes.layout import blank, put, rect, border',
            '',
            f'def build_custom_{sc.name}():',
            f'    w, h = {sc.w}, {sc.h}',
            '    m = blank(w, h, G)',
            ''
        ]

        for y in range(sc.h):
            for x in range(sc.w):
                tid = sc.tiles[y][x]
                if tid != G:
                    tile_name = TILE_NAMES.get(tid, str(tid)).upper()
                    lines.append(f'    put(m, {x}, {y}, {tile_name})')

        lines.extend([
            '',
            f"    return Scene('{sc.name}', '{sc.display}', m, indoor={sc.indoor})",
            ''
        ])

        content = "\n".join(lines)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.show_notification(f"Berhasil Diekspor ke Kode Python: {out_path}!", bg_color=COLOR_SUCCESS)

    def toggle_play_mode(self):
        if self.is_playing:
            self.stop_play_mode()
        else:
            self.start_play_mode()

    def start_play_mode(self):
        if self.is_playing:
            return

        self.is_playing = True
        self.sidebar.enabled = False
        self.top_bar.enabled = False
        self.active_card.enabled = False
        self.bottom_bar.enabled = False
        self.cursor_box.enabled = False
        self.editor_cam.enabled = False

        if hasattr(self, 'grid_mesh_entity') and self.grid_mesh_entity:
            self.grid_mesh_entity.enabled = False

        # Spawn Player
        self.game_state.scene_name = self.current_scene_name
        self.game_state.player_x = 8.0
        self.game_state.player_y = 8.0

        self.test_player = Player3D(self.game_state, self.world)
        mouse.locked = True
        self.show_notification("MODE UJI COBA: [WASD] Bergerak  |  [SPACE] Pakai Alat  |  [ESC] Kembali ke Editor", duration=5.0, bg_color=COLOR_SUCCESS)

    def stop_play_mode(self):
        if not self.is_playing:
            return

        self.is_playing = False
        if self.test_player:
            destroy(self.test_player)
            self.test_player = None

        mouse.locked = False
        mouse.visible = True

        self.sidebar.enabled = True
        self.top_bar.enabled = True
        self.active_card.enabled = True
        self.bottom_bar.enabled = True
        self.cursor_box.enabled = True
        self.editor_cam.enabled = True

        if hasattr(self, 'grid_mesh_entity') and self.grid_mesh_entity:
            self.grid_mesh_entity.enabled = self.show_grid_overlay

        self.show_notification("Kembali ke Mode Editor Level")

    def update(self):
        if self.notification_banner.enabled and time.time() > self.notification_time:
            self.notification_banner.enabled = False

        if self.is_playing:
            if self.test_player:
                self.test_player.update(time.dt)
            return

        if mouse.world_point:
            wx, wz = mouse.world_point.x, mouse.world_point.z
            tx = int(round(wx / TILE_SIZE))
            ty = int(round(wz / TILE_SIZE))

            sc = self.world.scene_obj
            if sc and 0 <= tx < sc.w and 0 <= ty < sc.h:
                self.hovered_tile = (tx, ty)
                self.cursor_box.enabled = True
                self.cursor_box.position = Vec3(tx * TILE_SIZE, GROUND_H + 0.18, ty * TILE_SIZE)

                tile_id = sc.tiles[ty][tx]
                tile_str = TILE_NAMES.get(tile_id, f"Tile_{tile_id}")
                self.status_text.text = f"Posisi: ({tx}, {ty})  |  Ubin: [{tile_id}] {tile_str}  |  Alat: {self.active_tool.upper()}"

                if mouse.left and not self.is_ui_hovered():
                    if self.active_tool == 'brush':
                        self.paint_tile_at(tx, ty, self.active_tile_id)
                    elif self.active_tool == 'erase':
                        default_t = FL if sc.indoor else G
                        self.paint_tile_at(tx, ty, default_t)

    def input(self, key):
        if self.is_playing:
            if key == 'escape':
                self.stop_play_mode()
            elif self.test_player:
                self.test_player.input(key)
            return

        if key == 'p':
            self.toggle_play_mode()
            return

        if self.is_ui_hovered():
            return

        tx, ty = self.hovered_tile

        if key == 'left mouse down':
            if self.active_tool == 'brush':
                self.paint_tile_at(tx, ty, self.active_tile_id)

            elif self.active_tool == 'erase':
                sc = self.world.scene_obj
                default_t = FL if (sc and sc.indoor) else G
                self.paint_tile_at(tx, ty, default_t)

            elif self.active_tool == 'picker':
                sc = self.world.scene_obj
                if sc and 0 <= tx < sc.w and 0 <= ty < sc.h:
                    picked = sc.tiles[ty][tx]
                    self.select_tile(picked)

            elif self.active_tool == 'rect':
                if self.rect_start is None:
                    self.rect_start = (tx, ty)
                    self.show_notification(f"Awal Isi Kotak: ({tx}, {ty}). Klik sudut seberang!")
                else:
                    x0, y0 = self.rect_start
                    x1, y1 = tx, ty
                    min_x, max_x = min(x0, x1), max(x0, x1)
                    min_y, max_y = min(y0, y1), max(y0, y1)

                    for cy in range(min_y, max_y + 1):
                        for cx in range(min_x, max_x + 1):
                            self.paint_tile_at(cx, cy, self.active_tile_id)

                    self.show_notification(f"Selesai Mengisi Kotak ({min_x},{min_y}) ke ({max_x},{max_y})!", bg_color=COLOR_SUCCESS)
                    self.rect_start = None

if __name__ == '__main__':
    editor = KarsaLevelEditor()
    editor.app.run()
