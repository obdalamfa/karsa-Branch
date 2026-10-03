"""
Play Mode Manager for Ursina Editor
Switches seamlessly between 3D Edit Mode (EditorCamera) and Live Play Mode (FirstPersonController).
"""
from ursina import Entity, Text, color, mouse, camera, destroy, Vec2, Vec3
from ursina.prefabs.first_person_controller import FirstPersonController

class PlayModeManager:
    """Manages switching between Edit Mode and First-Person Play Mode."""

    def __init__(self, scene_manager, editor_camera, editor_ui_elements=None, grid_entity=None, gizmo=None):
        self.scene_manager = scene_manager
        self.editor_camera = editor_camera
        self.editor_ui_elements = editor_ui_elements or []
        self.grid_entity = grid_entity
        self.gizmo = gizmo

        self.is_playing = False
        self.player = None
        self.hud_elements = []

        self.saved_camera_pos = Vec3(0, 0, 0)
        self.saved_camera_rot = Vec3(0, 0, 0)

    def toggle(self):
        """Toggle between edit and play modes."""
        if self.is_playing:
            self.stop()
        else:
            self.start()

    def start(self):
        """Enter Play Mode."""
        if self.is_playing:
            return

        self.is_playing = True
        self.scene_manager.deselect()

        if self.gizmo:
            self.gizmo.enabled = False
            if hasattr(self.gizmo, 'selection_box'):
                self.gizmo.selection_box.enabled = False

        for elem in self.editor_ui_elements:
            if elem:
                elem.enabled = False

        spawn_pos = Vec3(0, 2, 0)
        for e in self.scene_manager.entities:
            if getattr(e, 'editor_model', None) == 'player_spawn' or getattr(e, 'editor_tag', None) == 'spawn':
                spawn_pos = e.position + Vec3(0, 1.5, 0)
                break

        if self.editor_camera:
            self.saved_camera_pos = Vec3(camera.position)
            self.saved_camera_rot = Vec3(camera.rotation)
            self.editor_camera.enabled = False

        self.player = FirstPersonController(
            position=spawn_pos,
            speed=8,
            jump_height=1.5,
            mouse_sensitivity=Vec2(40, 40)
        )
        mouse.locked = True

        banner = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.8, 0.045),
            position=(0, 0.46),
            color=color.rgba(20, 24, 30, 220)
        )
        banner_text = Text(
            parent=banner,
            text='PLAY MODE: [WASD] Move  [SPACE] Jump  [ESC] Return to Editor',
            origin=(0, 0),
            position=(0, 0),
            scale=0.75,
            color=color.lime
        )
        crosshair = Text(
            parent=camera.ui,
            text='+',
            origin=(0, 0),
            position=(0, 0),
            scale=1.2,
            color=color.rgba(255, 255, 255, 180)
        )

        self.hud_elements = [banner, banner_text, crosshair]

    def stop(self):
        """Exit Play Mode and return to Editor."""
        if not self.is_playing:
            return

        self.is_playing = False

        if self.player:
            destroy(self.player)
            self.player = None

        for elem in self.hud_elements:
            destroy(elem)
        self.hud_elements.clear()

        mouse.locked = False
        mouse.visible = True

        if self.editor_camera:
            self.editor_camera.enabled = True
            camera.position = self.saved_camera_pos
            camera.rotation = self.saved_camera_rot

        for elem in self.editor_ui_elements:
            if elem:
                elem.enabled = True

        if self.grid_entity:
            self.grid_entity.enabled = True

    def handle_input(self, key):
        """Capture hotkey to exit play mode."""
        if self.is_playing and key == 'escape':
            self.stop()
            return True
        return False
