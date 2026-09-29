"""
Scene Manager for Ursina Editor
Handles scene entities, lifecycle, selection, serialization, and Python code generation.
"""
import json
import os
import time
from ursina import Entity, Vec2, Vec3, Vec4, Color, color, Cylinder, Cone, destroy

class SceneManager:
    """Manages scene objects, selection, persistence, and export."""

    def __init__(self):
        self.entities = []
        self.selected_entity = None
        self._id_counter = 1
        self.current_filepath = None

        # Undo / Redo History
        self._undo_stack = []
        self._redo_stack = []
        self._is_history_action = False
        self._batch_loading = False

        # Callbacks
        self.on_selection_changed = None
        self.on_entity_added = None
        self.on_entity_removed = None
        self.on_scene_modified = None

    def snapshot(self):
        """Record scene state for Undo."""
        if self._is_history_action:
            return
        state = self.to_dict()
        self._undo_stack.append(state)
        if len(self._undo_stack) > 30:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self):
        """Undo last scene change."""
        if not self._undo_stack:
            return False
        self._is_history_action = True
        try:
            current = self.to_dict()
            self._redo_stack.append(current)
            prev = self._undo_stack.pop()
            self.from_dict(prev)
            return True
        finally:
            self._is_history_action = False

    def redo(self):
        """Redo previously undone change."""
        if not self._redo_stack:
            return False
        self._is_history_action = True
        try:
            current = self.to_dict()
            self._undo_stack.append(current)
            nxt = self._redo_stack.pop()
            self.from_dict(nxt)
            return True
        finally:
            self._is_history_action = False

    def reset_transform(self, entity=None, pos=True, rot=True, scale=True):
        """Reset entity transform to defaults."""
        target = entity or self.selected_entity
        if not target:
            return
        self.snapshot()
        if pos:
            default_y = target.scale_y / 2.0 if getattr(target, 'editor_model', '') not in ('plane', 'quad') else 0.0
            target.position = Vec3(0, default_y, 0)
        if rot:
            target.rotation = Vec3(0, 0, 0)
        if scale:
            target.scale = Vec3(1, 1, 1)
        if self.on_scene_modified:
            self.on_scene_modified()

    def snap_to_ground(self, entity=None):
        """Align object bottom directly to Y=0 ground plane."""
        target = entity or self.selected_entity
        if not target:
            return
        self.snapshot()
        target.y = target.scale_y / 2.0 if getattr(target, 'editor_model', '') not in ('plane', 'quad') else 0.0
        if self.on_scene_modified:
            self.on_scene_modified()

    def toggle_visibility(self, entity=None):
        """Toggle entity visibility."""
        target = entity or self.selected_entity
        if not target:
            return
        self.snapshot()
        target.visible = not target.visible
        if self.on_scene_modified:
            self.on_scene_modified()

    def add_entity(self, model='cube', name=None, position=Vec3(0, 0.5, 0),
                   rotation=Vec3(0, 0, 0), scale=Vec3(1, 1, 1),
                   col=color.white, texture=None, collider='box', tag='default',
                   unlit=False, double_sided=False):
        """Add a new editable entity to the scene."""
        if not self._is_history_action and not self._batch_loading:
            self.snapshot()

        if name is None:
            name = f"{model.capitalize()}_{self._id_counter}"
            self._id_counter += 1

        # Adjust position if tuple or list passed
        if not isinstance(position, Vec3):
            position = Vec3(*position)
        if not isinstance(rotation, Vec3):
            rotation = Vec3(*rotation)
        if not isinstance(scale, Vec3):
            scale = Vec3(*scale)

        # Convert color if necessary
        if not isinstance(col, Color):
            if isinstance(col, (tuple, list)):
                col = Color(*col)
            else:
                col = color.white

        # Model resolution
        if model == 'cylinder':
            actual_model = Cylinder(resolution=16)
        elif model == 'cone':
            actual_model = Cone(resolution=16)
        elif model == 'player_spawn':
            actual_model = 'sphere'
        else:
            actual_model = model

        actual_color = color.cyan if model == 'player_spawn' else col
        actual_collider = None if model == 'player_spawn' else collider

        entity = Entity(
            name=name,
            model=actual_model,
            position=position,
            rotation=rotation,
            scale=scale,
            color=actual_color,
            collider=actual_collider,
            unlit=unlit,
            double_sided=double_sided
        )

        if texture:
            entity.texture = texture

        # Attach editor metadata
        entity.is_scene_object = True
        entity.editor_name = name
        entity.editor_model = model
        entity.editor_texture = texture
        entity.editor_collider = collider
        entity.editor_tag = tag if model != 'player_spawn' else 'spawn'
        entity.editor_unlit = unlit
        entity.editor_double_sided = double_sided

        # If spawn point, add direction arrow child
        if model == 'player_spawn':
            arrow = Entity(
                parent=entity,
                model=Cone(resolution=12),
                scale=(0.3, 0.6, 0.3),
                rotation_x=90,
                position=(0, 0, 0.6),
                color=color.yellow,
                unlit=True
            )
            entity.spawn_arrow = arrow

        self.entities.append(entity)
        self.select(entity)

        if self.on_entity_added:
            self.on_entity_added(entity)
        if self.on_scene_modified:
            self.on_scene_modified()

        return entity

    def select(self, entity):
        """Select an entity in the scene."""
        if self.selected_entity == entity:
            return
        self.selected_entity = entity
        if self.on_selection_changed:
            self.on_selection_changed(self.selected_entity)

    def deselect(self):
        """Deselect the currently selected entity."""
        if self.selected_entity is not None:
            self.selected_entity = None
            if self.on_selection_changed:
                self.on_selection_changed(None)

    def remove_entity(self, entity):
        """Remove an entity from the scene."""
        if entity not in self.entities:
            return

        if not self._is_history_action and not self._batch_loading:
            self.snapshot()

        is_selected = (self.selected_entity == entity)
        self.entities.remove(entity)

        if is_selected:
            self.deselect()

        destroy(entity)

        if self.on_entity_removed:
            self.on_entity_removed(entity)
        if self.on_scene_modified:
            self.on_scene_modified()

    def remove_selected(self):
        """Remove the currently selected entity."""
        if self.selected_entity:
            self.remove_entity(self.selected_entity)

    def duplicate_entity(self, entity):
        """Duplicate an existing entity with an offset."""
        if not entity or entity not in self.entities:
            return None

        new_name = f"{entity.editor_name}_copy"
        new_pos = entity.position + Vec3(1, 0, 1)

        new_entity = self.add_entity(
            model=entity.editor_model,
            name=new_name,
            position=new_pos,
            rotation=entity.rotation,
            scale=entity.scale,
            col=entity.color,
            texture=entity.editor_texture,
            collider=entity.editor_collider,
            tag=entity.editor_tag,
            unlit=entity.editor_unlit,
            double_sided=entity.editor_double_sided
        )
        return new_entity

    def duplicate_selected(self):
        """Duplicate the currently selected entity."""
        if self.selected_entity:
            return self.duplicate_entity(self.selected_entity)
        return None

    def clear_scene(self):
        """Clear all user entities from the scene."""
        if not self._is_history_action and not self._batch_loading:
            self.snapshot()

        self.deselect()
        for e in list(self.entities):
            destroy(e)
        self.entities.clear()
        self._id_counter = 1
        if self.on_scene_modified:
            self.on_scene_modified()

    def to_dict(self):
        """Serialize scene to dictionary."""
        data = {
            "version": "1.0",
            "generator": "Ursina Scene Editor",
            "entities": []
        }

        for e in self.entities:
            c = e.color
            item = {
                "name": getattr(e, 'editor_name', e.name),
                "model": getattr(e, 'editor_model', 'cube'),
                "position": [round(float(e.x), 3), round(float(e.y), 3), round(float(e.z), 3)],
                "rotation": [round(float(e.rotation_x), 3), round(float(e.rotation_y), 3), round(float(e.rotation_z), 3)],
                "scale": [round(float(e.scale_x), 3), round(float(e.scale_y), 3), round(float(e.scale_z), 3)],
                "color": [round(float(c[0]), 3), round(float(c[1]), 3), round(float(c[2]), 3), round(float(c[3]), 3)],
                "texture": getattr(e, 'editor_texture', None),
                "collider": getattr(e, 'editor_collider', 'box'),
                "tag": getattr(e, 'editor_tag', 'default'),
                "unlit": bool(getattr(e, 'editor_unlit', False)),
                "double_sided": bool(getattr(e, 'editor_double_sided', False)),
                "visible": bool(e.visible)
            }
            data["entities"].append(item)

        return data

    def from_dict(self, data):
        """Reconstruct scene from dictionary."""
        self._batch_loading = True
        try:
            self.clear_scene()

            entity_list = data.get("entities", [])
            for item in entity_list:
                col_data = item.get("color", [1, 1, 1, 1])
                col = Color(*col_data)

                e = self.add_entity(
                    model=item.get("model", "cube"),
                    name=item.get("name"),
                    position=Vec3(*item.get("position", [0, 0, 0])),
                    rotation=Vec3(*item.get("rotation", [0, 0, 0])),
                    scale=Vec3(*item.get("scale", [1, 1, 1])),
                    col=col,
                    texture=item.get("texture"),
                    collider=item.get("collider", "box"),
                    tag=item.get("tag", "default"),
                    unlit=item.get("unlit", False),
                    double_sided=item.get("double_sided", False)
                )
                e.visible = item.get("visible", True)

            self.deselect()
            if self.on_scene_modified:
                self.on_scene_modified()
        finally:
            self._batch_loading = False

    def save_to_json(self, filepath="scene.json"):
        """Save scene data to a JSON file."""
        data = self.to_dict()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.current_filepath = filepath
        return True

    def load_from_json(self, filepath="scene.json"):
        """Load scene data from a JSON file."""
        if not os.path.exists(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.from_dict(data)
        self.current_filepath = filepath
        return True

    def export_to_python(self, filepath="exported_scene.py", include_player=True):
        """Export the entire scene into a standalone, runnable Ursina script."""
        lines = [
            '"""',
            'Standalone Ursina Game / Scene',
            'Exported from Ursina Project Editor',
            f'Generated on: {time.strftime("%Y-%m-%d %H:%M:%S")}',
            'Run this file directly with: python ' + os.path.basename(filepath),
            '"""',
            'from ursina import *',
        ]

        # Check if we need player controller
        has_spawn = False
        spawn_pos = Vec3(0, 2, 0)
        for e in self.entities:
            if getattr(e, 'editor_model', None) == 'player_spawn' or getattr(e, 'editor_tag', None) == 'spawn':
                has_spawn = True
                spawn_pos = e.position + Vec3(0, 1.5, 0)
                break

        if include_player:
            lines.append('from ursina.prefabs.first_person_controller import FirstPersonController')

        lines.extend([
            '',
            '# Initialize Application',
            'app = Ursina()',
            'window.title = "Exported Ursina Level"',
            'window.borderless = False',
            'window.vsync = True',
            '',
            '# Environment & Lighting',
            'Sky(color=color.light_gray)',
            'sun = DirectionalLight()',
            'sun.look_at(Vec3(1, -2, 1))',
            'AmbientLight(color=color.rgba(140, 140, 140, 255))',
            '',
            '# Scene Entities'
        ])

        for i, e in enumerate(self.entities):
            model = getattr(e, 'editor_model', 'cube')
            # If spawn marker, don't render as geometry in exported game
            if model == 'player_spawn':
                continue

            var_name = f"obj_{i+1}"
            c = e.color
            tex_str = f"'{e.editor_texture}'" if getattr(e, 'editor_texture', None) else "None"
            col_str = f"'{e.editor_collider}'" if getattr(e, 'editor_collider', None) else "None"

            if model == 'cylinder':
                model_repr = 'Cylinder(resolution=16)'
            elif model == 'cone':
                model_repr = 'Cone(resolution=16)'
            else:
                model_repr = f"'{model}'"

            lines.append(f"# Entity: {e.editor_name}")
            lines.append(f"{var_name} = Entity(")
            lines.append(f"    name='{e.editor_name}',")
            lines.append(f"    model={model_repr},")
            lines.append(f"    position=Vec3({e.x:.3f}, {e.y:.3f}, {e.z:.3f}),")
            lines.append(f"    rotation=Vec3({e.rotation_x:.3f}, {e.rotation_y:.3f}, {e.rotation_z:.3f}),")
            lines.append(f"    scale=Vec3({e.scale_x:.3f}, {e.scale_y:.3f}, {e.scale_z:.3f}),")
            lines.append(f"    color=Color({c[0]:.3f}, {c[1]:.3f}, {c[2]:.3f}, {c[3]:.3f}),")
            if e.editor_texture:
                lines.append(f"    texture={tex_str},")
            if e.editor_collider:
                lines.append(f"    collider={col_str},")
            if getattr(e, 'editor_unlit', False):
                lines.append("    unlit=True,")
            if getattr(e, 'editor_double_sided', False):
                lines.append("    double_sided=True,")
            if not e.visible:
                lines.append("    visible=False,")
            lines.append(")")
            lines.append("")

        if include_player:
            lines.extend([
                '# Player Controller',
                f'player = FirstPersonController(position=Vec3({spawn_pos.x:.3f}, {spawn_pos.y:.3f}, {spawn_pos.z:.3f}))',
                '',
                'def input(key):',
                "    if key == 'escape':",
                '        mouse.locked = not mouse.locked',
                '',
            ])
        else:
            lines.extend([
                '# Camera Setup',
                'EditorCamera()',
                '',
            ])

        lines.extend([
            'if __name__ == "__main__":',
            '    app.run()',
            ''
        ])

        content = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return True
