"""
Ursina 3D Scene & Level Editor
Main application entry point.

Run this script to launch the visual editor:
    python main.py
    or
    python -m ursina_editor.main
"""
import sys
import os
import time
from pathlib import Path

# Ensure package and current directory are on sys.path for versatile execution
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Berkas kerja editor. Dulu ketiganya relatif CWD, jadi menjalankan
# `python -m ursina_editor.main` dari akar repo menulis `scene.json` dan
# `exported_scene.py` ke akar repo -- mengotori pohon kerja dengan berkas yang
# bukan bagian dari game. Sekarang ditulis di sebelah paketnya sendiri, sama
# seperti `main.py` menambatkan folder asetnya ke `__file__`.
_DIR_EDITOR = Path(__file__).resolve().parent
BERKAS_SCENE = str(_DIR_EDITOR / 'scene.json')
BERKAS_EKSPOR = str(_DIR_EDITOR / 'exported_scene.py')

from ursina import (
    Ursina, window, camera, color, mouse, held_keys,
    Entity, Button, Text, Grid, Sky, DirectionalLight, AmbientLight,
    EditorCamera, Vec2, Vec3, Color, destroy, scene, InputField
)

try:
    from ursina_editor.scene_manager import SceneManager
    from ursina_editor.gizmo import TransformGizmo
    from ursina_editor.hierarchy import HierarchyPanel
    from ursina_editor.inspector import InspectorPanel
    from ursina_editor.play_mode import PlayModeManager
    from ursina_editor.karsa_panel import PanelKarsa
except ImportError:
    from scene_manager import SceneManager
    from gizmo import TransformGizmo
    from hierarchy import HierarchyPanel
    from inspector import InspectorPanel
    from play_mode import PlayModeManager
    from karsa_panel import PanelKarsa


class UrsinaEditorApp:
    """Complete visual 3D scene and level editor application."""

    def __init__(self, headless=False):
        self.app = Ursina(
            title="Ursina 3D Scene & Level Editor",
            borderless=False,
            vsync=True,
            headless=headless
        )

        window.color = color.rgba(16, 18, 24, 255)
        window.fps_counter.enabled = True

        # Environment & 3D Setup
        self._setup_environment()

        # Scene Manager
        self.scene_manager = SceneManager()

        # 3D Transform Gizmo
        self.gizmo = TransformGizmo(self.scene_manager)

        # Editor UI Components
        self.hierarchy_panel = HierarchyPanel(self.scene_manager, on_focus=self.focus_entity)
        self.inspector_panel = InspectorPanel(self.scene_manager, self.gizmo)

        # Top Bar & Bottom Bar
        self._build_top_bar()
        self._build_bottom_bar()

        # Notification Banner
        self._build_notification()

        # Interactive Help & Shortcuts Modal
        self._build_help_modal()

        # Play Mode Manager
        all_ui = [
            self.top_bar,
            self.bottom_bar,
            self.hierarchy_panel,
            self.inspector_panel,
            self.notification_banner,
            self.help_modal
        ]
        self.play_mode_manager = PlayModeManager(
            scene_manager=self.scene_manager,
            editor_camera=self.editor_cam,
            editor_ui_elements=all_ui,
            grid_entity=self.grid,
            gizmo=self.gizmo
        )

        # Panel peta Lembah Karsa. Panel ini mengurus GRID UBIN milik game,
        # sedangkan seluruh panel di atas mengurus entity bebas -- dua model
        # yang berbeda, jadi ia berdiri sendiri dan tidak menumpang toolbar.
        # Tersembunyi sampai dinyalakan dengan `K`.
        self.karsa_panel = PanelKarsa(
            on_pesan=self.show_notification,
            # Gizmo mengikuti `scene_manager.selected_entity`, jadi mengklik
            # objek peta cukup menyeleksinya lewat jalur yang sudah ada.
            on_pilih=self.scene_manager.select,
        )
        # Gizmo menggeser entity; kalau yang digeser adalah objek peta Karsa,
        # posisinya ditulis BALIK ke `scene.objects`. Tanpa ini gizmo hanya
        # memindahkan gambarnya, dan perubahannya hilang begitu scene disimpan.
        self.gizmo.on_transform_changed = self.karsa_panel.sesi.sinkron_objek

        # Populate Starter Scene
        self._setup_starter_scene()

        # Bind Global Ursina update and input hooks
        self.app.update = self.update
        self.app.input = self.input

    def _setup_environment(self):
        """Create lighting, sky, ground grid, and editor camera."""
        Sky(color=color.rgba(36, 44, 58, 255))

        self.sun = DirectionalLight()
        self.sun.look_at(Vec3(1, -2, 1))

        self.ambient = AmbientLight(color=color.rgba(140, 145, 160, 255))

        # Ground Grid
        self.grid = Entity(
            model=Grid(40, 40),
            scale=40,
            rotation_x=90,
            color=color.rgba(70, 90, 120, 85),
            y=0,
            collider=None
        )

        # Free 3D Editor Camera
        self.editor_cam = EditorCamera(
            rotation=(30, -35, 0),
            position=(0, 2, -10)
        )

    def _build_top_bar(self):
        """Construct the top navigation and action toolbar."""
        bar_height = 0.052
        self.top_bar = Entity(
            parent=camera.ui,
            model='quad',
            scale=(window.aspect_ratio, bar_height),
            position=(0, 0.5 - bar_height / 2),
            color=color.rgba(18, 22, 30, 248),
            collider='box'
        )
        self.top_bar.is_ui = True

        # App Title Badge
        self.title_text = Text(
            parent=self.top_bar,
            text='URSINA 3D',
            origin=(-0.5, 0),
            position=(-0.49, 0),
            scale=0.88,
            color=color.azure
        )

        btn_y = 0
        btn_h = 0.034

        # File actions: New, Open, Save, Export
        self.btn_new = Button(
            parent=self.top_bar,
            text='New',
            scale=(0.046, btn_h),
            position=(-0.38, btn_y),
            color=color.rgba(38, 44, 56, 240),
            highlight_color=color.rgba(50, 60, 78, 255),
            on_click=self.on_new_scene
        )
        self.btn_new.is_ui = True
        self.btn_new.text_entity.scale = 0.72

        self.btn_load = Button(
            parent=self.top_bar,
            text='Open',
            scale=(0.046, btn_h),
            position=(-0.33, btn_y),
            color=color.rgba(38, 44, 56, 240),
            highlight_color=color.rgba(50, 60, 78, 255),
            on_click=self.on_load_scene
        )
        self.btn_load.is_ui = True
        self.btn_load.text_entity.scale = 0.72

        self.btn_save = Button(
            parent=self.top_bar,
            text='Save',
            scale=(0.046, btn_h),
            position=(-0.28, btn_y),
            color=color.rgba(38, 44, 56, 240),
            highlight_color=color.rgba(50, 60, 78, 255),
            on_click=self.on_save_scene
        )
        self.btn_save.is_ui = True
        self.btn_save.text_entity.scale = 0.72

        self.btn_export = Button(
            parent=self.top_bar,
            text='Export Code',
            scale=(0.075, btn_h),
            position=(-0.215, btn_y),
            color=color.rgba(30, 95, 170, 240),
            highlight_color=color.rgba(45, 125, 210, 255),
            on_click=self.on_export_python
        )
        self.btn_export.is_ui = True
        self.btn_export.text_entity.scale = 0.70

        # History: Undo / Redo
        self.btn_undo = Button(
            parent=self.top_bar,
            text='Undo',
            scale=(0.046, btn_h),
            position=(-0.148, btn_y),
            color=color.rgba(40, 48, 62, 240),
            highlight_color=color.rgba(55, 68, 88, 255),
            on_click=self.on_undo
        )
        self.btn_undo.is_ui = True
        self.btn_undo.text_entity.scale = 0.72

        self.btn_redo = Button(
            parent=self.top_bar,
            text='Redo',
            scale=(0.046, btn_h),
            position=(-0.098, btn_y),
            color=color.rgba(40, 48, 62, 240),
            highlight_color=color.rgba(55, 68, 88, 255),
            on_click=self.on_redo
        )
        self.btn_redo.is_ui = True
        self.btn_redo.text_entity.scale = 0.72

        # Viewport toggles: Grid & Snapping
        self.btn_grid = Button(
            parent=self.top_bar,
            text='Grid: ON',
            scale=(0.058, btn_h),
            position=(-0.042, btn_y),
            color=color.rgba(44, 52, 68, 240),
            highlight_color=color.rgba(60, 72, 95, 255),
            on_click=self.toggle_grid
        )
        self.btn_grid.is_ui = True
        self.btn_grid.text_entity.scale = 0.68

        self.snap_levels = [0.5, 1.0, 2.0, 0.25, 0.0]
        self.snap_idx = 0
        self.btn_snap = Button(
            parent=self.top_bar,
            text='Snap: 0.5',
            scale=(0.065, btn_h),
            position=(0.024, btn_y),
            color=color.rgba(44, 52, 68, 240),
            highlight_color=color.rgba(60, 72, 95, 255),
            on_click=self.cycle_snap
        )
        self.btn_snap.is_ui = True
        self.btn_snap.text_entity.scale = 0.68

        # Camera view cycle button
        self.cam_views = ['iso', 'top', 'front', 'side', 'reset']
        self.cam_view_idx = 0
        self.btn_cam = Button(
            parent=self.top_bar,
            text='Cam: Iso',
            scale=(0.062, btn_h),
            position=(0.092, btn_y),
            color=color.rgba(50, 60, 80, 240),
            highlight_color=color.rgba(70, 85, 115, 255),
            on_click=self.cycle_camera_view
        )
        self.btn_cam.is_ui = True
        self.btn_cam.text_entity.scale = 0.68

        # Focus button
        self.btn_focus = Button(
            parent=self.top_bar,
            text='Focus [F]',
            scale=(0.058, btn_h),
            position=(0.156, btn_y),
            color=color.rgba(45, 75, 105, 240),
            highlight_color=color.rgba(60, 105, 150, 255),
            on_click=self.focus_selection
        )
        self.btn_focus.is_ui = True
        self.btn_focus.text_entity.scale = 0.68

        # Play Mode Button (Prominent Green)
        self.btn_play = Button(
            parent=self.top_bar,
            text='Play Mode [P]',
            scale=(0.095, btn_h),
            position=(0.240, btn_y),
            color=color.rgba(30, 130, 60, 245),
            highlight_color=color.rgba(45, 165, 80, 255),
            on_click=self.toggle_play_mode
        )
        self.btn_play.is_ui = True
        self.btn_play.text_entity.scale = 0.70

        # Help / Shortcuts Button
        self.btn_help = Button(
            parent=self.top_bar,
            text='? Help [H]',
            scale=(0.060, btn_h),
            position=(0.324, btn_y),
            color=color.rgba(40, 100, 140, 240),
            highlight_color=color.rgba(55, 135, 185, 255),
            on_click=self.toggle_help
        )
        self.btn_help.is_ui = True
        self.btn_help.text_entity.scale = 0.68

    def _build_bottom_bar(self):
        """Construct the bottom status bar and shortcut hint strip."""
        bar_height = 0.038
        self.bottom_bar = Entity(
            parent=camera.ui,
            model='quad',
            scale=(window.aspect_ratio, bar_height),
            position=(0, -0.5 + bar_height / 2),
            color=color.rgba(14, 17, 24, 250),
            collider='box'
        )
        self.bottom_bar.is_ui = True

        # Left status: Selection transform info
        self.selection_info_text = Text(
            parent=self.bottom_bar,
            text='No Selection',
            origin=(-0.5, 0),
            position=(-0.49, 0),
            scale=0.68,
            color=color.azure
        )

        # Center hints: Common hotkeys
        self.hints_text = Text(
            parent=self.bottom_bar,
            text='[W] Move  [E/R] Rot  [F] Focus  [Ctrl+D] Dup  [Del] Del  [Ctrl+Z] Undo  [P] Play  [H] Help',
            origin=(0, 0),
            position=(0.04, 0),
            scale=0.65,
            color=color.gray
        )

        # Right status: Scene info
        self.status_text = Text(
            parent=self.bottom_bar,
            text='Objs: 0',
            origin=(0.5, 0),
            position=(0.49, 0),
            scale=0.68,
            color=color.light_gray
        )

    def _build_notification(self):
        """Construct floating toast banner for saving, exporting, or alert messages."""
        self.notification_banner = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.56, 0.042),
            position=(0, 0.42),
            color=color.rgba(25, 75, 135, 240),
            enabled=False,
            always_on_top=True
        )
        self.notification_banner.is_ui = True
        self.notification_text = Text(
            parent=self.notification_banner,
            text='',
            origin=(0, 0),
            position=(0, 0),
            scale=0.78,
            color=color.white
        )
        self.notification_time = 0.0

    def _build_help_modal(self):
        """Construct interactive overlay modal with complete shortcuts guide."""
        self.help_modal = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.82, 0.76),
            position=(0, 0),
            color=color.rgba(14, 18, 26, 252),
            collider='box',
            enabled=False,
            always_on_top=True
        )
        self.help_modal.is_ui = True

        # Header
        Text(
            parent=self.help_modal,
            text='URSINA 3D EDITOR - KEYBOARD SHORTCUTS & GUIDE',
            origin=(0, 0.5),
            position=(0, 0.45),
            scale=0.95,
            color=color.azure
        )

        # Section 1: Navigation
        nav_text = (
            "CAMERA NAVIGATION\n"
            "- Right Mouse + Drag: Orbit camera view\n"
            "- Middle Mouse / Shift+RMB: Pan camera\n"
            "- Scroll Wheel: Zoom camera in / out\n"
            "- [F] Key: Focus camera on selected object\n"
            "- [1, 3, 7] Keys: Front, Side, Top view presets\n"
            "- [0] Key: Reset camera to default perspective"
        )
        Text(
            parent=self.help_modal,
            text=nav_text,
            origin=(-0.5, 0.5),
            position=(-0.46, 0.36),
            scale=0.74,
            color=color.light_gray
        )

        # Section 2: Editing
        edit_text = (
            "TRANSFORM & OBJECT EDITING\n"
            "- [W / G / T]: Translate (Move) Gizmo\n"
            "- [E / R]: Quick Rotate 45 deg (Shift+R for -45 deg)\n"
            "- [Delete / Backspace]: Delete selected object\n"
            "- [Ctrl + D]: Duplicate selected object\n"
            "- [Ctrl + Z]: Undo last change\n"
            "- [Ctrl + Y]: Redo undone change\n"
            "- [Ctrl + S]: Quick save scene to scene.json"
        )
        Text(
            parent=self.help_modal,
            text=edit_text,
            origin=(-0.5, 0.5),
            position=(0.02, 0.36),
            scale=0.74,
            color=color.light_gray
        )

        # Section 3: Play Mode
        play_text = (
            "PLAYTESTING & EXPORT\n"
            "- [P] Key: Enter / Exit First-Person Play Mode\n"
            "- [W, A, S, D]: Walk in Play Mode\n"
            "- [Space]: Jump\n"
            "- [Esc]: Exit Play Mode and return to Editor\n"
            "- [Export Code Button]: Creates standalone runnable Python script"
        )
        Text(
            parent=self.help_modal,
            text=play_text,
            origin=(-0.5, 0.5),
            position=(-0.46, -0.14),
            scale=0.74,
            color=color.lime
        )

        # Close button
        close_btn = Button(
            parent=self.help_modal,
            text='Close Help [Esc / H]',
            scale=(0.28, 0.045),
            position=(0, -0.40),
            origin=(0, 0),
            color=color.rgba(35, 110, 190, 240),
            highlight_color=color.rgba(50, 135, 220, 255),
            on_click=self.toggle_help
        )
        close_btn.is_ui = True

    def toggle_help(self):
        """Toggle the help and shortcuts modal."""
        self.help_modal.enabled = not self.help_modal.enabled

    def show_notification(self, msg, duration=3.0, bg_color=None):
        """Display a floating toast notification."""
        self.notification_text.text = msg
        if bg_color:
            self.notification_banner.color = bg_color
        else:
            self.notification_banner.color = color.rgba(25, 75, 135, 240)
        self.notification_banner.enabled = True
        self.notification_time = time.time() + duration

    def _setup_starter_scene(self):
        """Add starter entities so the user has an immediate playground."""
        # Ground Platform
        self.scene_manager.add_entity(
            name="Ground_Platform",
            model="cube",
            position=Vec3(0, -0.5, 0),
            scale=Vec3(24, 1, 24),
            col=Color(0.28, 0.45, 0.28, 1.0),
            texture="grass",
            collider="box",
            tag="ground"
        )

        # Starter Pillars
        self.scene_manager.add_entity(
            name="Pillar_Left",
            model="cylinder",
            position=Vec3(-5, 2, 4),
            scale=Vec3(1.2, 4, 1.2),
            col=Color(0.85, 0.85, 0.85, 1.0),
            texture="brick",
            collider="box",
            tag="obstacle"
        )

        self.scene_manager.add_entity(
            name="Pillar_Right",
            model="cylinder",
            position=Vec3(5, 2, 4),
            scale=Vec3(1.2, 4, 1.2),
            col=Color(0.85, 0.85, 0.85, 1.0),
            texture="brick",
            collider="box",
            tag="obstacle"
        )

        self.scene_manager.add_entity(
            name="Step_Platform",
            model="cube",
            position=Vec3(0, 1, 6),
            scale=Vec3(4, 2, 3),
            col=Color(0.7, 0.6, 0.4, 1.0),
            texture="brick",
            collider="box",
            tag="obstacle"
        )

        # Player Spawn Marker
        self.scene_manager.add_entity(
            name="Player_Spawn",
            model="player_spawn",
            position=Vec3(0, 0.5, -4),
            scale=Vec3(0.8, 0.8, 0.8),
            tag="spawn"
        )

        if self.scene_manager.entities:
            self.scene_manager.select(self.scene_manager.entities[0])

    def on_new_scene(self):
        """Reset scene."""
        self.scene_manager.clear_scene()
        self.show_notification("Scene cleared. Add objects from the hierarchy panel!")

    def on_save_scene(self):
        """Save scene to JSON."""
        save_path = BERKAS_SCENE
        success = self.scene_manager.save_to_json(save_path)
        if success:
            self.show_notification(f"Saved {len(self.scene_manager.entities)} objects to {os.path.basename(save_path)}!")

    def on_load_scene(self):
        """Load scene from JSON."""
        load_path = BERKAS_SCENE
        if not os.path.exists(load_path):
            self.show_notification(f"{os.path.basename(load_path)} not found! Save a scene first.", bg_color=color.rgba(140, 45, 45, 230))
            return
        success = self.scene_manager.load_from_json(load_path)
        if success:
            self.show_notification(f"Loaded {len(self.scene_manager.entities)} objects from {os.path.basename(load_path)}!")

    def on_export_python(self):
        """Export standalone runnable Ursina python file."""
        export_path = BERKAS_EKSPOR
        self.scene_manager.export_to_python(export_path, include_player=True)
        self.show_notification(f"Exported to {os.path.basename(export_path)}! Run: python {export_path}")

    def on_undo(self):
        """Revert last scene action."""
        success = self.scene_manager.undo()
        if success:
            self.show_notification("Undo successful!")
        else:
            self.show_notification("Nothing to undo.", duration=1.5)

    def on_redo(self):
        """Reapply undone action."""
        success = self.scene_manager.redo()
        if success:
            self.show_notification("Redo successful!")
        else:
            self.show_notification("Nothing to redo.", duration=1.5)

    def cycle_snap(self):
        """Cycle grid snap values."""
        self.snap_idx = (self.snap_idx + 1) % len(self.snap_levels)
        val = self.snap_levels[self.snap_idx]
        self.gizmo.snap_grid = val
        self.btn_snap.text = f"Snap: {val}" if val > 0 else "Snap: OFF"
        self.show_notification(f"Grid snapping: {val if val > 0 else 'OFF'}", duration=1.5)

    def toggle_grid(self):
        """Toggle ground grid visibility."""
        self.grid.enabled = not self.grid.enabled
        self.btn_grid.text = "Grid: ON" if self.grid.enabled else "Grid: OFF"

    def cycle_camera_view(self):
        """Cycle through camera view presets."""
        self.cam_view_idx = (self.cam_view_idx + 1) % len(self.cam_views)
        view = self.cam_views[self.cam_view_idx]
        self.set_camera_view(view)

    def set_camera_view(self, view_name):
        """Position camera according to standard view presets."""
        sel = self.scene_manager.selected_entity
        target_pos = sel.position if sel else Vec3(0, 0, 0)

        if view_name == 'top':
            self.editor_cam.rotation = (90, 0, 0)
            self.editor_cam.position = target_pos + Vec3(0, 18, 0)
            self.editor_cam.look_at(target_pos)
            self.btn_cam.text = "Cam: Top"
        elif view_name == 'front':
            self.editor_cam.rotation = (0, 0, 0)
            self.editor_cam.position = target_pos + Vec3(0, 2, -18)
            self.editor_cam.look_at(target_pos)
            self.btn_cam.text = "Cam: Front"
        elif view_name == 'side':
            self.editor_cam.rotation = (0, -90, 0)
            self.editor_cam.position = target_pos + Vec3(18, 2, 0)
            self.editor_cam.look_at(target_pos)
            self.btn_cam.text = "Cam: Side"
        elif view_name == 'iso':
            self.editor_cam.rotation = (30, -35, 0)
            self.editor_cam.position = target_pos + Vec3(9, 8, -9)
            self.editor_cam.look_at(target_pos)
            self.btn_cam.text = "Cam: Iso"
        elif view_name == 'reset':
            self.editor_cam.rotation = (30, -35, 0)
            self.editor_cam.position = (0, 2, -10)
            self.btn_cam.text = "Cam: Reset"

        self.show_notification(f"Camera view: {view_name.capitalize()}", duration=1.5)

    def toggle_play_mode(self):
        """Toggle play testing mode."""
        if self.help_modal.enabled:
            self.help_modal.enabled = False
        self.play_mode_manager.toggle()

    def focus_selection(self):
        """Focus editor camera on selected object."""
        target = self.scene_manager.selected_entity
        if target:
            self.focus_entity(target)
        else:
            self.show_notification("No object selected to focus on.", duration=1.5)

    def focus_entity(self, entity):
        """Smoothly position camera to frame entity."""
        if entity:
            self.editor_cam.position = entity.position + Vec3(0, 2, -6)
            self.editor_cam.look_at(entity.position)
            self.show_notification(f"Focused on: {getattr(entity, 'editor_name', entity.name)}", duration=1.5)

    def is_ui_entity(self, entity):
        """Check if an entity belongs to camera.ui."""
        curr = entity
        while curr:
            if getattr(curr, 'is_ui', False) or curr == camera.ui:
                return True
            curr = curr.parent
        return False

    def is_typing(self):
        """Check if any input field currently has keyboard focus."""
        for e in scene.entities:
            if isinstance(e, InputField) and getattr(e, 'active', False):
                return True
        return False

    def update(self):
        """Frame update loop."""
        if self.notification_banner.enabled and time.time() > self.notification_time:
            self.notification_banner.enabled = False

        if not self.play_mode_manager.is_playing:
            total_objs = len(self.scene_manager.entities)
            sel = self.scene_manager.selected_entity
            if sel:
                self.selection_info_text.text = f"Selected: {getattr(sel, 'editor_name', sel.name)} | Pos: ({sel.x:.1f}, {sel.y:.1f}, {sel.z:.1f}) | Rot: {sel.rotation_y:.0f}°"
            else:
                self.selection_info_text.text = "No Selection (Click in 3D or Outliner)"

            undo_count = len(self.scene_manager._undo_stack)
            self.status_text.text = f"Objs: {total_objs} | Undo: {undo_count}"

    def input(self, key):
        """Global keyboard and mouse input handler."""
        if self.play_mode_manager.is_playing:
            self.play_mode_manager.handle_input(key)
            return

        # If user is typing in a search bar or name field, protect keys from triggering hotkeys
        if self.is_typing():
            if key == 'escape':
                for e in scene.entities:
                    if isinstance(e, InputField):
                        e.active = False
            return

        # Help modal toggle
        if key == 'h' or key == 'f1':
            self.toggle_help()
            return
        elif key == 'escape' and self.help_modal.enabled:
            self.help_modal.enabled = False
            return

        # Panel peta Karsa. Diperiksa SEBELUM gizmo: mengklik ubin untuk
        # mengecat tidak boleh sekaligus memindahkan gizmo ke sana.
        if key == 'k':
            nyala = self.karsa_panel.toggle()
            self.show_notification(
                "Panel peta Karsa aktif -- pilih scene, pilih ubin, klik ubin untuk mengecat."
                if nyala else "Panel peta Karsa disembunyikan.")
            return
        if key == 'left mouse down' and self.karsa_panel.klik_viewport():
            return

        # Gizmo hotkeys & clicks
        if self.gizmo.handle_input(key):
            return

        # Undo / Redo
        if held_keys['control'] and key == 'z':
            self.on_undo()
            return
        elif held_keys['control'] and key == 'y':
            self.on_redo()
            return

        # Play mode toggle
        if key == 'p':
            self.toggle_play_mode()
            return

        # Focus selection
        elif key == 'f':
            self.focus_selection()
            return

        # Camera view shortcuts
        elif key == '1':
            self.set_camera_view('front')
            return
        elif key == '3':
            self.set_camera_view('side')
            return
        elif key == '7':
            self.set_camera_view('top')
            return
        elif key == '0':
            self.set_camera_view('reset')
            return

        # Delete selection. Objek peta Karsa diperiksa lebih dulu: kalau yang
        # sedang diseleksi gizmo adalah objek terpasang, hapus dari
        # `scene.objects`; kalau bukan, jatuh ke penghapusan entity bebas.
        elif key == 'delete' or key == 'backspace':
            if self.karsa_panel.hapus_terpilih(self.scene_manager.selected_entity):
                return
            self.scene_manager.remove_selected()
            return

        # Duplicate selection
        elif held_keys['control'] and key == 'd':
            self.scene_manager.duplicate_selected()
            return

        # Quick save
        elif held_keys['control'] and key == 's':
            self.on_save_scene()
            return

        # 3D Viewport Mouse Selection
        elif key == 'left mouse down':
            hovered = mouse.hovered_entity
            if hovered:
                if self.is_ui_entity(hovered):
                    return
                if hovered in self.gizmo.handles:
                    return
                if getattr(hovered, 'is_scene_object', False):
                    self.scene_manager.select(hovered)
                    return
                if hovered.parent and getattr(hovered.parent, 'is_scene_object', False):
                    self.scene_manager.select(hovered.parent)
                    return

            if not self.is_ui_entity(mouse.hovered_entity):
                self.scene_manager.deselect()

    def run(self):
        """Launch the Ursina main loop."""
        self.app.run()


if __name__ == '__main__':
    editor = UrsinaEditorApp()
    editor.run()
