"""
Hierarchy / Outliner Panel for Ursina Editor
Displays active scene entities with search filtering, visibility toggles, focus shortcuts, and quick primitive addition.
"""
from ursina import Entity, Button, Text, InputField, color, camera, window, destroy, Vec2, Vec3

class HierarchyPanel(Entity):
    """Left sidebar panel listing scene entities with search, selection, and management controls."""

    def __init__(self, scene_manager, on_focus=None, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)
        self.scene_manager = scene_manager
        self.on_focus = on_focus
        self.is_ui = True

        self.panel_width = 0.28
        self.panel_height = 0.86
        self.origin = (-0.5, 0.5)
        self.position = (-window.aspect_ratio / 2 + 0.015, 0.43)

        # Background Panel
        self.bg = Entity(
            parent=self,
            model='quad',
            scale=(self.panel_width, self.panel_height),
            origin=(-0.5, 0.5),
            color=color.rgba(20, 24, 32, 245),
            collider='box'
        )
        self.bg.is_ui = True

        # Header Title
        self.title = Text(
            parent=self,
            text='SCENE HIERARCHY',
            position=(0.015, -0.022),
            scale=0.85,
            color=color.azure
        )

        # Add Object Button
        self.add_btn = Button(
            parent=self,
            text='+ Add Object',
            scale=(self.panel_width - 0.03, 0.036),
            position=(0.015, -0.055),
            origin=(-0.5, 0.5),
            color=color.rgba(35, 115, 215, 240),
            highlight_color=color.rgba(55, 140, 240, 255),
            on_click=self.toggle_add_menu
        )
        self.add_btn.is_ui = True

        # Add Menu Popup
        self._build_add_menu()

        # Search Bar
        search_w = self.panel_width - 0.075
        self.search_field = InputField(
            parent=self,
            default_value='',
            scale=(search_w, 0.032),
            position=(0.015, -0.098),
            origin=(-0.5, 0.5),
            color=color.rgba(30, 36, 48, 240)
        )
        self.search_field.is_ui = True
        self.search_field.on_value_changed = self._on_search_changed

        self.search_clear_btn = Button(
            parent=self,
            text='X',
            scale=(0.035, 0.032),
            position=(0.02 + search_w, -0.098),
            origin=(-0.5, 0.5),
            color=color.rgba(50, 56, 70, 220),
            highlight_color=color.rgba(180, 50, 50, 240),
            on_click=self._clear_search
        )
        self.search_clear_btn.is_ui = True

        # Entity Item Rows Container
        self.page = 0
        self.page_size = 9
        self.row_entities = []

        # Pagination controls
        self.page_info = Text(
            parent=self,
            text='Page 1/1 (0 objs)',
            position=(0.015, -self.panel_height + 0.082),
            scale=0.68,
            color=color.gray
        )
        self.prev_btn = Button(
            parent=self,
            text='Prev',
            scale=(0.048, 0.028),
            position=(self.panel_width - 0.112, -self.panel_height + 0.082),
            origin=(-0.5, 0.5),
            color=color.rgba(40, 46, 60, 230),
            on_click=self.prev_page
        )
        self.prev_btn.is_ui = True
        self.prev_btn.text_entity.scale = 0.65

        self.next_btn = Button(
            parent=self,
            text='Next',
            scale=(0.048, 0.028),
            position=(self.panel_width - 0.058, -self.panel_height + 0.082),
            origin=(-0.5, 0.5),
            color=color.rgba(40, 46, 60, 230),
            on_click=self.next_page
        )
        self.next_btn.is_ui = True
        self.next_btn.text_entity.scale = 0.65

        # Bottom Quick Action Buttons
        btn_w3 = (self.panel_width - 0.04) / 3
        self.desel_btn = Button(
            parent=self,
            text='Deselect',
            scale=(btn_w3, 0.034),
            position=(0.015, -self.panel_height + 0.04),
            origin=(-0.5, 0.5),
            color=color.rgba(45, 52, 65, 230),
            highlight_color=color.rgba(65, 75, 95, 255),
            on_click=self._on_deselect
        )
        self.desel_btn.is_ui = True

        self.dup_btn = Button(
            parent=self,
            text='Duplicate',
            scale=(btn_w3, 0.034),
            position=(0.015 + btn_w3 + 0.005, -self.panel_height + 0.04),
            origin=(-0.5, 0.5),
            color=color.rgba(45, 80, 120, 230),
            highlight_color=color.rgba(60, 110, 160, 255),
            on_click=self._on_duplicate
        )
        self.dup_btn.is_ui = True

        self.del_btn = Button(
            parent=self,
            text='Delete',
            scale=(btn_w3, 0.034),
            position=(0.015 + (btn_w3 + 0.005) * 2, -self.panel_height + 0.04),
            origin=(-0.5, 0.5),
            color=color.rgba(140, 45, 45, 230),
            highlight_color=color.rgba(180, 55, 55, 255),
            on_click=self._on_delete
        )
        self.del_btn.is_ui = True

        # Register callbacks with scene manager
        self.scene_manager.on_entity_added = lambda e: self.refresh()
        self.scene_manager.on_entity_removed = lambda e: self.refresh()
        self.scene_manager.on_selection_changed = lambda e: self.refresh_selection()
        self.scene_manager.on_scene_modified = lambda: self.refresh()

        self.refresh()

    def _build_add_menu(self):
        """Construct the popup menu for adding primitives and special objects."""
        self.add_menu = Entity(
            parent=self,
            model='quad',
            scale=(self.panel_width - 0.02, 0.29),
            position=(0.01, -0.095),
            origin=(-0.5, 0.5),
            color=color.rgba(26, 32, 42, 252),
            collider='box',
            enabled=False,
            always_on_top=True
        )
        self.add_menu.is_ui = True

        primitives = [
            ('+ Cube', 'cube'),
            ('+ Sphere', 'sphere'),
            ('+ Cylinder', 'cylinder'),
            ('+ Plane / Floor', 'plane'),
            ('+ Cone', 'cone'),
            ('+ Player Spawn', 'player_spawn')
        ]

        y_offset = -0.012
        for label, model_type in primitives:
            btn = Button(
                parent=self.add_menu,
                text=label,
                scale=(self.panel_width - 0.04, 0.038),
                position=(0.01, y_offset),
                origin=(-0.5, 0.5),
                color=color.rgba(40, 48, 64, 245),
                highlight_color=color.rgba(50, 110, 200, 255),
                on_click=lambda m=model_type: self._create_object(m)
            )
            btn.is_ui = True
            y_offset -= 0.044

    def toggle_add_menu(self):
        """Show or hide the object creation menu."""
        self.add_menu.enabled = not self.add_menu.enabled

    def _create_object(self, model_type):
        """Add object and close menu."""
        self.add_menu.enabled = False
        spawn_y = 0.5 if model_type not in ('plane', 'quad') else 0.0
        self.scene_manager.add_entity(model=model_type, position=Vec3(0, spawn_y, 0))

    def _on_search_changed(self):
        self.page = 0
        self.refresh()

    def _clear_search(self):
        self.search_field.text = ''
        self.page = 0
        self.refresh()

    def _on_deselect(self):
        self.scene_manager.deselect()

    def _on_duplicate(self):
        self.scene_manager.duplicate_selected()

    def _on_delete(self):
        self.scene_manager.remove_selected()

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.refresh()

    def next_page(self):
        matched = self._get_matched_entities()
        max_page = max(0, (len(matched) - 1) // self.page_size)
        if self.page < max_page:
            self.page += 1
            self.refresh()

    def _get_matched_entities(self):
        query = self.search_field.text.strip().lower() if hasattr(self, 'search_field') else ""
        if not query:
            return self.scene_manager.entities
        return [
            e for e in self.scene_manager.entities
            if query in getattr(e, 'editor_name', e.name).lower()
            or query in getattr(e, 'editor_model', '').lower()
            or query in getattr(e, 'editor_tag', '').lower()
        ]

    def _get_badge_info(self, model_name):
        model_name = (model_name or '').lower()
        if 'cube' in model_name:
            return 'CUB', color.rgba(180, 120, 30, 240)
        elif 'sphere' in model_name:
            return 'SPH', color.rgba(30, 140, 170, 240)
        elif 'cyl' in model_name:
            return 'CYL', color.rgba(140, 70, 170, 240)
        elif 'plane' in model_name or 'quad' in model_name:
            return 'PLN', color.rgba(50, 140, 70, 240)
        elif 'cone' in model_name:
            return 'CON', color.rgba(190, 85, 30, 240)
        elif 'spawn' in model_name:
            return 'SPW', color.rgba(200, 160, 20, 240)
        return 'OBJ', color.rgba(60, 70, 90, 240)

    def refresh(self):
        """Rebuild the list of visible entities."""
        for elem in self.row_entities:
            destroy(elem)
        self.row_entities.clear()

        matched = self._get_matched_entities()
        total_matched = len(matched)
        total_all = len(self.scene_manager.entities)

        max_page = max(0, (total_matched - 1) // self.page_size) if total_matched > 0 else 0
        if self.page > max_page:
            self.page = max_page

        query = self.search_field.text.strip() if hasattr(self, 'search_field') else ""
        if query:
            self.page_info.text = f"P{self.page + 1}/{max_page + 1} ({total_matched}/{total_all})"
        else:
            self.page_info.text = f"P{self.page + 1}/{max_page + 1} ({total_all} objs)"

        start_idx = self.page * self.page_size
        end_idx = min(start_idx + self.page_size, total_matched)

        y_pos = -0.142
        row_h = 0.038
        row_gap = 0.042

        for i in range(start_idx, end_idx):
            ent = matched[i]
            is_selected = (self.scene_manager.selected_entity == ent)
            model_tag = getattr(ent, 'editor_model', 'obj')
            badge_text, badge_col = self._get_badge_info(model_tag)

            # 1. Type Badge Button
            badge_btn = Button(
                parent=self,
                text=badge_text,
                scale=(0.042, row_h),
                position=(0.015, y_pos),
                origin=(-0.5, 0.5),
                color=badge_col,
                on_click=lambda e=ent: self.scene_manager.select(e)
            )
            badge_btn.is_ui = True
            badge_btn.text_entity.scale = 0.65
            self.row_entities.append(badge_btn)

            # 2. Main Name Button
            name_w = self.panel_width - 0.132
            name_text = getattr(ent, 'editor_name', ent.name)
            if len(name_text) > 13:
                name_text = name_text[:11] + '..'

            name_col = color.rgba(40, 100, 170, 245) if is_selected else color.rgba(32, 38, 50, 230)
            name_btn = Button(
                parent=self,
                text=name_text,
                scale=(name_w, row_h),
                position=(0.061, y_pos),
                origin=(-0.5, 0.5),
                color=name_col,
                highlight_color=color.rgba(50, 120, 200, 255),
                on_click=lambda e=ent: self.scene_manager.select(e)
            )
            name_btn.is_ui = True
            name_btn.target_entity = ent
            name_btn.text_entity.scale = 0.72
            self.row_entities.append(name_btn)

            # 3. Visibility Toggle Button (Vis / Hide)
            vis_col = color.rgba(35, 120, 60, 230) if ent.visible else color.rgba(90, 40, 40, 230)
            vis_text = 'V' if ent.visible else '-'
            vis_btn = Button(
                parent=self,
                text=vis_text,
                scale=(0.032, row_h),
                position=(0.065 + name_w, y_pos),
                origin=(-0.5, 0.5),
                color=vis_col,
                highlight_color=color.rgba(70, 150, 80, 255),
                on_click=lambda e=ent: self._toggle_vis(e)
            )
            vis_btn.is_ui = True
            vis_btn.text_entity.scale = 0.75
            self.row_entities.append(vis_btn)

            # 4. Focus Camera Button (F)
            foc_btn = Button(
                parent=self,
                text='F',
                scale=(0.032, row_h),
                position=(0.101 + name_w, y_pos),
                origin=(-0.5, 0.5),
                color=color.rgba(48, 56, 72, 230),
                highlight_color=color.rgba(60, 130, 220, 255),
                on_click=lambda e=ent: self._focus_on(e)
            )
            foc_btn.is_ui = True
            foc_btn.text_entity.scale = 0.75
            self.row_entities.append(foc_btn)

            y_pos -= row_gap

    def _toggle_vis(self, entity):
        entity.visible = not entity.visible
        if self.scene_manager.on_scene_modified:
            self.scene_manager.on_scene_modified()
        self.refresh()

    def _focus_on(self, entity):
        self.scene_manager.select(entity)
        if self.on_focus:
            self.on_focus(entity)

    def refresh_selection(self):
        """Update button highlight styles when selection changes."""
        selected = self.scene_manager.selected_entity
        for elem in self.row_entities:
            if hasattr(elem, 'target_entity'):
                if elem.target_entity == selected:
                    elem.color = color.rgba(40, 100, 170, 245)
                else:
                    elem.color = color.rgba(32, 38, 50, 230)
