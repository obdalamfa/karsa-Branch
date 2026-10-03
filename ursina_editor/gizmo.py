"""
3D Transform Gizmo and Visual Selection Highlight
Provides 3-axis interactive translation handles, rotation/scale modes, and snapping.
"""
from ursina import Entity, Vec2, Vec3, color, mouse, camera, distance, Cylinder, Cone, destroy

class TransformGizmo(Entity):
    """3D Interactive Translation and Transform Gizmo."""

    def __init__(self, scene_manager, **kwargs):
        super().__init__(always_on_top=True, **kwargs)
        self.scene_manager = scene_manager
        self.snap_grid = 0.5  # 0.0 = off, 0.5 = 0.5 units, 1.0 = 1.0 units
        self.mode = 'translate'  # 'translate', 'rotate', 'scale'

        self.active_axis = None
        self.is_dragging = False
        self.drag_start_mouse = Vec2(0, 0)
        self.drag_start_pos = Vec3(0, 0, 0)
        self.drag_start_rot = Vec3(0, 0, 0)
        self.drag_start_scale = Vec3(1, 1, 1)

        # Build Visual Selection Highlight
        self.selection_box = Entity(
            model='wireframe_cube',
            color=color.cyan,
            unlit=True,
            enabled=False,
            always_on_top=True
        )

        # Build Gizmo Handles
        self._build_handles()
        self.enabled = False

        # Callback on transform change
        self.on_transform_changed = None

    def _build_handles(self):
        """Construct the 3-axis handles."""
        # Center Ball
        self.center_handle = Entity(
            parent=self,
            model='sphere',
            color=color.yellow,
            scale=0.22,
            collider='box',
            unlit=True
        )
        self.center_handle.axis_name = 'ALL'

        # X Axis (Red)
        self.x_shaft = Entity(
            parent=self,
            model=Cylinder(resolution=10),
            color=color.red,
            scale=(0.04, 1.0, 0.04),
            rotation_z=-90,
            position=(0.5, 0, 0),
            unlit=True
        )
        self.x_cone = Entity(
            parent=self,
            model=Cone(resolution=12),
            color=color.red,
            scale=(0.16, 0.35, 0.16),
            rotation_z=-90,
            position=(1.05, 0, 0),
            collider='box',
            unlit=True
        )
        self.x_cone.axis_name = 'X'

        # Y Axis (Green)
        self.y_shaft = Entity(
            parent=self,
            model=Cylinder(resolution=10),
            color=color.green,
            scale=(0.04, 1.0, 0.04),
            position=(0, 0.5, 0),
            unlit=True
        )
        self.y_cone = Entity(
            parent=self,
            model=Cone(resolution=12),
            color=color.green,
            scale=(0.16, 0.35, 0.16),
            position=(0, 1.05, 0),
            collider='box',
            unlit=True
        )
        self.y_cone.axis_name = 'Y'

        # Z Axis (Blue)
        self.z_shaft = Entity(
            parent=self,
            model=Cylinder(resolution=10),
            color=color.azure,
            scale=(0.04, 1.0, 0.04),
            rotation_x=90,
            position=(0, 0, 0.5),
            unlit=True
        )
        self.z_cone = Entity(
            parent=self,
            model=Cone(resolution=12),
            color=color.azure,
            scale=(0.16, 0.35, 0.16),
            rotation_x=90,
            position=(0, 0, 1.05),
            collider='box',
            unlit=True
        )
        self.z_cone.axis_name = 'Z'

        self.handles = [self.center_handle, self.x_cone, self.y_cone, self.z_cone]

    def update(self):
        target = self.scene_manager.selected_entity
        if not target or not target.enabled:
            self.enabled = False
            self.selection_box.enabled = False
            self.is_dragging = False
            return

        self.enabled = True
        self.selection_box.enabled = True

        # Sync position with selected entity
        self.world_position = target.world_position
        self.selection_box.world_position = target.world_position
        self.selection_box.world_rotation = target.world_rotation
        self.selection_box.world_scale = target.world_scale * 1.05

        # Scale gizmo to keep size constant relative to camera view
        cam_dist = distance(self.world_position, camera.world_position)
        size_factor = max(0.2, cam_dist * 0.12)
        self.scale = Vec3(size_factor, size_factor, size_factor)

        # Handle mouse dragging
        if self.is_dragging and self.active_axis:
            mouse_delta = mouse.position - self.drag_start_mouse
            sensitivity = max(1.0, cam_dist * 0.8)

            new_pos = Vec3(self.drag_start_pos)

            if self.active_axis == 'X':
                dx = mouse_delta.x * sensitivity * 12
                new_pos.x = self.drag_start_pos.x + dx
            elif self.active_axis == 'Y':
                dy = mouse_delta.y * sensitivity * 12
                new_pos.y = self.drag_start_pos.y + dy
            elif self.active_axis == 'Z':
                dz = (-mouse_delta.y + mouse_delta.x * 0.5) * sensitivity * 12
                new_pos.z = self.drag_start_pos.z + dz
            elif self.active_axis == 'ALL':
                cam_right = camera.right
                cam_up = camera.up
                move_vec = (cam_right * mouse_delta.x + cam_up * mouse_delta.y) * sensitivity * 12
                new_pos = self.drag_start_pos + move_vec

            # Apply Snapping
            if self.snap_grid > 0:
                new_pos.x = round(new_pos.x / self.snap_grid) * self.snap_grid
                new_pos.y = round(new_pos.y / self.snap_grid) * self.snap_grid
                new_pos.z = round(new_pos.z / self.snap_grid) * self.snap_grid

            target.position = new_pos
            self.world_position = target.world_position

            if self.on_transform_changed:
                self.on_transform_changed(target)

    def handle_input(self, key):
        """Handle mouse clicks on gizmo handles or transform hotkeys."""
        target = self.scene_manager.selected_entity
        if not target:
            return False

        if key == 'left mouse down':
            hovered = mouse.hovered_entity
            if hovered in self.handles:
                self.scene_manager.snapshot()
                self.active_axis = getattr(hovered, 'axis_name', None)
                self.is_dragging = True
                self.drag_start_mouse = Vec2(mouse.x, mouse.y)
                self.drag_start_pos = Vec3(target.position)
                self.drag_start_rot = Vec3(target.rotation)
                self.drag_start_scale = Vec3(target.scale)
                return True

        elif key == 'left mouse up':
            if self.is_dragging:
                self.is_dragging = False
                self.active_axis = None
                return True

        elif key == 'g' or key == 't' or key == 'w':
            self.scene_manager.snapshot()
            self.active_axis = 'ALL'
            self.is_dragging = True
            self.drag_start_mouse = Vec2(mouse.x, mouse.y)
            self.drag_start_pos = Vec3(target.position)
            return True

        elif key == 'r' or key == 'e':
            self.scene_manager.snapshot()
            target.rotation_y = (target.rotation_y + 45) % 360
            if self.on_transform_changed:
                self.on_transform_changed(target)
            return True

        elif key == 'shift+r' or key == 'shift+e':
            self.scene_manager.snapshot()
            target.rotation_y = (target.rotation_y - 45) % 360
            if self.on_transform_changed:
                self.on_transform_changed(target)
            return True

        elif key == 'escape':
            if self.is_dragging:
                target.position = self.drag_start_pos
                self.is_dragging = False
                self.active_axis = None
                if self.on_transform_changed:
                    self.on_transform_changed(target)
                return True

        return False
