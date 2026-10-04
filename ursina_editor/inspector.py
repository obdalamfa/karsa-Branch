"""
Inspector / Property Editor Panel for Ursina Editor
Inspects and modifies transform, visual properties, colliders, and tags of the selected entity.
Designed for maximum speed, clarity, and ergonomics with direct-action buttons.
"""
from ursina import Entity, Button, Text, InputField, color, camera, window, destroy, Vec3, Color, Cylinder, Cone

class InspectorPanel(Entity):
    """Right sidebar panel for inspecting and tweaking entity properties."""

    def __init__(self, scene_manager, gizmo, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)
        self.scene_manager = scene_manager
        self.gizmo = gizmo
        self.is_ui = True

        self.panel_width = 0.35
        self.panel_height = 0.88
        self.origin = (-0.5, 0.5)
        self.position = (window.aspect_ratio / 2 - self.panel_width - 0.015, 0.44)

        # Step configuration
        self.step_options = [0.1, 0.5, 1.0, 5.0]
        self.active_step = 0.5

        # Background
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
            text='INSPECTOR & PROPERTIES',
            position=(0.015, -0.018),
            scale=0.82,
            color=color.azure
        )

        # Container for controls
        self.controls_container = Entity(parent=self)

        # Placeholder text when nothing is selected
        self.no_sel_text = Text(
            parent=self,
            text='No object selected.\n\nClick an object in the\n3D scene or hierarchy\nto inspect and edit.',
            position=(0.025, -0.2),
            scale=0.8,
            color=color.gray
        )

        # Hook into events
        self.scene_manager.on_selection_changed = self.on_selection_changed
        if self.gizmo:
            self.gizmo.on_transform_changed = lambda target: self.update_transform_display()

        self.refresh()

    def on_selection_changed(self, entity):
        self.refresh()

    def refresh(self):
        """Rebuild property controls based on current selection."""
        for c in list(self.controls_container.children):
            destroy(c)

        target = self.scene_manager.selected_entity
        if not target:
            self.no_sel_text.enabled = True
            return

        self.no_sel_text.enabled = False
        y = -0.046

        # ---------------- 1. Name Field ----------------
        Text(parent=self.controls_container, text='Name:', position=(0.015, y), scale=0.72, color=color.light_gray)
        self.name_field = InputField(
            parent=self.controls_container,
            default_value=getattr(target, 'editor_name', target.name),
            scale=(self.panel_width - 0.08, 0.030),
            position=(0.065, y + 0.005),
            origin=(-0.5, 0.5),
            color=color.rgba(30, 36, 48, 240)
        )
        self.name_field.is_ui = True
        self.name_field.on_submit = self._on_name_change

        y -= 0.038

        # ---------------- Quick Action Buttons ----------------
        qw4 = (self.panel_width - 0.036) / 4
        quick_btns_1 = [
            ('Pos 0', lambda: self.scene_manager.reset_transform(target, pos=True, rot=False, scale=False)),
            ('Floor', lambda: self.scene_manager.snap_to_ground(target)),
            ('Rot 0', lambda: self.scene_manager.reset_transform(target, pos=False, rot=True, scale=False)),
            ('Scale 1', lambda: self.scene_manager.reset_transform(target, pos=False, rot=False, scale=True)),
        ]
        for idx, (label, callback) in enumerate(quick_btns_1):
            btn = Button(
                parent=self.controls_container,
                text=label,
                scale=(qw4, 0.026),
                position=(0.015 + idx * (qw4 + 0.002), y),
                origin=(-0.5, 0.5),
                color=color.rgba(42, 52, 70, 230),
                highlight_color=color.rgba(60, 100, 160, 255),
                on_click=callback
            )
            btn.is_ui = True
            btn.text_entity.scale = 0.68

        y -= 0.030
        qw2 = (self.panel_width - 0.034) / 2
        dup_btn = Button(
            parent=self.controls_container,
            text='Duplicate (Ctrl+D)',
            scale=(qw2, 0.026),
            position=(0.015, y),
            origin=(-0.5, 0.5),
            color=color.rgba(40, 80, 130, 230),
            highlight_color=color.rgba(55, 110, 180, 255),
            on_click=lambda: self.scene_manager.duplicate_selected()
        )
        dup_btn.is_ui = True
        dup_btn.text_entity.scale = 0.68

        del_btn = Button(
            parent=self.controls_container,
            text='Delete (Del)',
            scale=(qw2, 0.026),
            position=(0.019 + qw2, y),
            origin=(-0.5, 0.5),
            color=color.rgba(130, 45, 45, 230),
            highlight_color=color.rgba(175, 55, 55, 255),
            on_click=lambda: self.scene_manager.remove_selected()
        )
        del_btn.is_ui = True
        del_btn.text_entity.scale = 0.68

        y -= 0.036

        # ---------------- 2. Transform Section ----------------
        Text(parent=self.controls_container, text='TRANSFORM', position=(0.015, y), scale=0.76, color=color.gold)

        # Step Selector
        Text(parent=self.controls_container, text='Step:', position=(0.145, y), scale=0.68, color=color.light_gray)
        step_btn_w = 0.036
        for s_idx, st in enumerate(self.step_options):
            is_cur = (self.active_step == st)
            st_btn = Button(
                parent=self.controls_container,
                text=str(st),
                scale=(step_btn_w, 0.022),
                position=(0.185 + s_idx * (step_btn_w + 0.002), y + 0.002),
                origin=(-0.5, 0.5),
                color=color.rgba(45, 120, 210, 240) if is_cur else color.rgba(36, 42, 54, 220),
                on_click=lambda val=st: self._set_step(val)
            )
            st_btn.is_ui = True
            st_btn.text_entity.scale = 0.62

        y -= 0.028

        # Position (X, Y, Z)
        axes = [
            ('X', color.red, lambda: target.x, lambda val: self._set_pos('x', val)),
            ('Y', color.green, lambda: target.y, lambda val: self._set_pos('y', val)),
            ('Z', color.azure, lambda: target.z, lambda val: self._set_pos('z', val))
        ]
        for ax, c, getter, setter in axes:
            self._build_stepper(
                label=f"Pos {ax}",
                lbl_color=c,
                y=y,
                getter=getter,
                setter=setter,
                step=self.active_step,
                mult_step=self.active_step * 5.0,
                reset_val=0.0
            )
            y -= 0.027

        y -= 0.006

        # Rotation (X, Y, Z)
        rot_axes = [
            ('X', color.red, 'rotation_x'),
            ('Y', color.green, 'rotation_y'),
            ('Z', color.azure, 'rotation_z')
        ]
        for ax, c, attr in rot_axes:
            self._build_rot_stepper(
                label=f"Rot {ax}",
                lbl_color=c,
                y=y,
                attr=attr,
                target=target
            )
            y -= 0.027

        y -= 0.006

        # Scale (X, Y, Z)
        scale_axes = [
            ('X', color.red, 'scale_x'),
            ('Y', color.green, 'scale_y'),
            ('Z', color.azure, 'scale_z')
        ]
        for ax, c, attr in scale_axes:
            self._build_scale_stepper(
                label=f"Scale {ax}",
                lbl_color=c,
                y=y,
                attr=attr,
                target=target
            )
            y -= 0.027

        # Uniform Scale Buttons
        u_btns = [
            ('x0.5', lambda: self._uniform_scale_factor(0.5)),
            ('- Step', lambda: self._uniform_scale_delta(-self.active_step)),
            ('+ Step', lambda: self._uniform_scale_delta(self.active_step)),
            ('x2.0', lambda: self._uniform_scale_factor(2.0)),
            ('Reset', lambda: self._set_uniform_scale(1.0))
        ]
        u_w = (self.panel_width - 0.038) / len(u_btns)
        for u_idx, (u_lbl, u_act) in enumerate(u_btns):
            ubtn = Button(
                parent=self.controls_container,
                text=u_lbl,
                scale=(u_w, 0.024),
                position=(0.015 + u_idx * (u_w + 0.002), y),
                origin=(-0.5, 0.5),
                color=color.rgba(42, 48, 62, 230),
                highlight_color=color.rgba(60, 90, 140, 255),
                on_click=u_act
            )
            ubtn.is_ui = True
            ubtn.text_entity.scale = 0.65

        y -= 0.034

        # ---------------- 3. Visuals & Material Section ----------------
        Text(parent=self.controls_container, text='VISUALS & MATERIAL', position=(0.015, y), scale=0.76, color=color.gold)
        y -= 0.026

        # Model Selector Buttons
        models = [('Cube', 'cube'), ('Sphere', 'sphere'), ('Cyl', 'cylinder'), ('Plane', 'plane'), ('Cone', 'cone')]
        m_w = (self.panel_width - 0.038) / len(models)
        for idx, (m_label, m_val) in enumerate(models):
            is_active = (getattr(target, 'editor_model', None) == m_val)
            m_btn = Button(
                parent=self.controls_container,
                text=m_label,
                scale=(m_w, 0.025),
                position=(0.015 + idx * (m_w + 0.002), y),
                origin=(-0.5, 0.5),
                color=color.rgba(40, 110, 190, 240) if is_active else color.rgba(36, 42, 54, 220),
                highlight_color=color.rgba(60, 130, 220, 255),
                on_click=lambda mv=m_val: self._set_model(mv)
            )
            m_btn.is_ui = True
            m_btn.text_entity.scale = 0.68

        y -= 0.029

        # Texture Selector 1-Click Buttons
        textures = [('None', None), ('Brick', 'brick'), ('Grass', 'grass'), ('Shore', 'shore'), ('White', 'white_cube')]
        t_w = (self.panel_width - 0.038) / len(textures)
        for idx, (t_label, t_val) in enumerate(textures):
            is_cur = (getattr(target, 'editor_texture', None) == t_val)
            t_btn = Button(
                parent=self.controls_container,
                text=t_label,
                scale=(t_w, 0.025),
                position=(0.015 + idx * (t_w + 0.002), y),
                origin=(-0.5, 0.5),
                color=color.rgba(35, 135, 110, 240) if is_cur else color.rgba(36, 42, 54, 220),
                highlight_color=color.rgba(50, 160, 135, 255),
                on_click=lambda tv=t_val: self._set_texture(tv)
            )
            t_btn.is_ui = True
            t_btn.text_entity.scale = 0.68

        y -= 0.029

        # Color Palette Swatches (16 curated colors in 2 rows of 8)
        palette = [
            color.white, color.light_gray, color.gray, color.dark_gray,
            color.black, color.red, color.orange, color.gold,
            color.yellow, color.lime, color.green, color.turquoise,
            color.cyan, color.azure, color.blue, color.magenta
        ]
        cols_per_row = 8
        c_size = (self.panel_width - 0.04) / cols_per_row
        for i, col in enumerate(palette):
            r = i // cols_per_row
            c_idx = i % cols_per_row
            swatch = Button(
                parent=self.controls_container,
                text='',
                scale=(c_size - 0.003, 0.018),
                position=(0.015 + c_idx * c_size, y - r * 0.022),
                origin=(-0.5, 0.5),
                color=col,
                on_click=lambda c=col: self._set_color(c)
            )
            swatch.is_ui = True

        y -= (0.022 * 2 + 0.014)

        # ---------------- 4. Physics & Gameplay Section ----------------
        Text(parent=self.controls_container, text='PHYSICS & GAMEPLAY', position=(0.015, y), scale=0.76, color=color.gold)
        y -= 0.026

        # Collider Type (4 direct buttons)
        colliders = [('None', None), ('Box', 'box'), ('Sphere', 'sphere'), ('Mesh', 'mesh')]
        col_w = (self.panel_width - 0.036) / len(colliders)
        for idx, (c_label, c_val) in enumerate(colliders):
            is_col = (getattr(target, 'editor_collider', None) == c_val)
            col_btn = Button(
                parent=self.controls_container,
                text=f"Col: {c_label}",
                scale=(col_w, 0.025),
                position=(0.015 + idx * (col_w + 0.002), y),
                origin=(-0.5, 0.5),
                color=color.rgba(140, 80, 40, 240) if is_col else color.rgba(36, 42, 54, 220),
                highlight_color=color.rgba(180, 100, 50, 255),
                on_click=lambda cv=c_val: self._set_collider(cv)
            )
            col_btn.is_ui = True
            col_btn.text_entity.scale = 0.64

        y -= 0.028

        # Gameplay Tags (6 direct buttons in 2 rows)
        tags = ['default', 'ground', 'obstacle', 'hazard', 'pickup', 'spawn']
        tag_w = (self.panel_width - 0.034) / 3
        for idx, tg in enumerate(tags):
            r = idx // 3
            c = idx % 3
            is_tg = (getattr(target, 'editor_tag', 'default') == tg)
            tag_btn = Button(
                parent=self.controls_container,
                text=f"#{tg}",
                scale=(tag_w, 0.024),
                position=(0.015 + c * (tag_w + 0.002), y - r * 0.026),
                origin=(-0.5, 0.5),
                color=color.rgba(50, 110, 160, 240) if is_tg else color.rgba(36, 42, 54, 220),
                highlight_color=color.rgba(70, 135, 190, 255),
                on_click=lambda t=tg: self._set_tag(t)
            )
            tag_btn.is_ui = True
            tag_btn.text_entity.scale = 0.65

        y -= (0.026 * 2 + 0.008)

        # Visibility & Double Sided Toggles
        vis_w = (self.panel_width - 0.034) / 2
        vis_text = "Visibility: ON" if target.visible else "Visibility: OFF"
        vis_btn = Button(
            parent=self.controls_container,
            text=vis_text,
            scale=(vis_w, 0.026),
            position=(0.015, y),
            origin=(-0.5, 0.5),
            color=color.rgba(35, 115, 60, 240) if target.visible else color.rgba(110, 40, 40, 240),
            on_click=self._toggle_visibility
        )
        vis_btn.is_ui = True
        vis_btn.text_entity.scale = 0.66

        unlit_val = getattr(target, 'editor_unlit', False)
        unlit_text = "Unlit: YES" if unlit_val else "Unlit: NO"
        unlit_btn = Button(
            parent=self.controls_container,
            text=unlit_text,
            scale=(vis_w, 0.026),
            position=(0.019 + vis_w, y),
            origin=(-0.5, 0.5),
            color=color.rgba(90, 60, 130, 240) if unlit_val else color.rgba(42, 48, 62, 230),
            on_click=self._toggle_unlit
        )
        unlit_btn.is_ui = True
        unlit_btn.text_entity.scale = 0.66

    def _set_step(self, val):
        self.active_step = val
        self.refresh()

    def _build_stepper(self, label, lbl_color, y, getter, setter, step=0.5, mult_step=2.5, reset_val=0.0):
        """Construct a property row with fast multi-step adjustments."""
        Text(parent=self.controls_container, text=label, position=(0.015, y), scale=0.68, color=lbl_color)

        val_text = Text(
            parent=self.controls_container,
            text=f"{getter():.2f}",
            position=(0.065, y),
            scale=0.68,
            color=color.white
        )

        def adjust(delta):
            setter(getter() + delta)
            val_text.text = f"{getter():.2f}"

        btn_defs = [
            ('--', -mult_step, 0.038),
            ('-', -step, 0.032),
            ('+', step, 0.032),
            ('++', mult_step, 0.038)
        ]
        btn_x = 0.145
        for b_lbl, b_delta, b_w in btn_defs:
            b = Button(
                parent=self.controls_container,
                text=b_lbl,
                scale=(b_w, 0.022),
                position=(btn_x, y + 0.002),
                origin=(-0.5, 0.5),
                color=color.rgba(42, 48, 62, 230),
                highlight_color=color.rgba(60, 80, 110, 255),
                on_click=lambda d=b_delta: adjust(d)
            )
            b.is_ui = True
            b.text_entity.scale = 0.62
            btn_x += (b_w + 0.002)

        # Zero reset button
        rst_btn = Button(
            parent=self.controls_container,
            text='0',
            scale=(0.030, 0.022),
            position=(btn_x + 0.002, y + 0.002),
            origin=(-0.5, 0.5),
            color=color.rgba(60, 48, 48, 230),
            highlight_color=color.rgba(140, 50, 50, 255),
            on_click=lambda: (setter(reset_val), setattr(val_text, 'text', f"{reset_val:.2f}"))
        )
        rst_btn.is_ui = True
        rst_btn.text_entity.scale = 0.62

    def _build_rot_stepper(self, label, lbl_color, y, attr, target):
        Text(parent=self.controls_container, text=label, position=(0.015, y), scale=0.68, color=lbl_color)

        val_text = Text(
            parent=self.controls_container,
            text=f"{getattr(target, attr):.0f}°",
            position=(0.065, y),
            scale=0.68,
            color=color.white
        )

        def adjust_rot(delta):
            new_val = (getattr(target, attr) + delta) % 360
            self._set_rot(attr, new_val)
            val_text.text = f"{new_val:.0f}°"

        rot_btns = [
            ('-90', -90, 0.038),
            ('-15', -15, 0.034),
            ('+15', 15, 0.034),
            ('+90', 90, 0.038)
        ]
        btn_x = 0.145
        for b_lbl, b_delta, b_w in rot_btns:
            b = Button(
                parent=self.controls_container,
                text=b_lbl,
                scale=(b_w, 0.022),
                position=(btn_x, y + 0.002),
                origin=(-0.5, 0.5),
                color=color.rgba(42, 48, 62, 230),
                highlight_color=color.rgba(60, 80, 110, 255),
                on_click=lambda d=b_delta: adjust_rot(d)
            )
            b.is_ui = True
            b.text_entity.scale = 0.62
            btn_x += (b_w + 0.002)

        rst_btn = Button(
            parent=self.controls_container,
            text='0°',
            scale=(0.030, 0.022),
            position=(btn_x + 0.002, y + 0.002),
            origin=(-0.5, 0.5),
            color=color.rgba(60, 48, 48, 230),
            highlight_color=color.rgba(140, 50, 50, 255),
            on_click=lambda: (self._set_rot(attr, 0), setattr(val_text, 'text', "0°"))
        )
        rst_btn.is_ui = True
        rst_btn.text_entity.scale = 0.62

    def _build_scale_stepper(self, label, lbl_color, y, attr, target):
        Text(parent=self.controls_container, text=label, position=(0.015, y), scale=0.68, color=lbl_color)

        val_text = Text(
            parent=self.controls_container,
            text=f"{getattr(target, attr):.2f}",
            position=(0.075, y),
            scale=0.68,
            color=color.white
        )

        def adjust_s(delta):
            new_val = max(0.05, getattr(target, attr) + delta)
            self._set_scale(attr, new_val)
            val_text.text = f"{new_val:.2f}"

        scale_btns = [
            ('--', -self.active_step * 2.0, 0.038),
            ('-', -self.active_step, 0.032),
            ('+', self.active_step, 0.032),
            ('++', self.active_step * 2.0, 0.038)
        ]
        btn_x = 0.145
        for b_lbl, b_delta, b_w in scale_btns:
            b = Button(
                parent=self.controls_container,
                text=b_lbl,
                scale=(b_w, 0.022),
                position=(btn_x, y + 0.002),
                origin=(-0.5, 0.5),
                color=color.rgba(42, 48, 62, 230),
                highlight_color=color.rgba(60, 80, 110, 255),
                on_click=lambda d=b_delta: adjust_s(d)
            )
            b.is_ui = True
            b.text_entity.scale = 0.62
            btn_x += (b_w + 0.002)

        rst_btn = Button(
            parent=self.controls_container,
            text='1.0',
            scale=(0.030, 0.022),
            position=(btn_x + 0.002, y + 0.002),
            origin=(-0.5, 0.5),
            color=color.rgba(48, 55, 65, 230),
            highlight_color=color.rgba(60, 100, 160, 255),
            on_click=lambda: (self._set_scale(attr, 1.0), setattr(val_text, 'text', "1.00"))
        )
        rst_btn.is_ui = True
        rst_btn.text_entity.scale = 0.60

    def update_transform_display(self):
        """Called when gizmo moves/rotates/scales the object."""
        self.refresh()

    def _on_name_change(self):
        target = self.scene_manager.selected_entity
        if target and self.name_field.text.strip():
            target.editor_name = self.name_field.text.strip()
            target.name = target.editor_name
            if self.scene_manager.on_scene_modified:
                self.scene_manager.on_scene_modified()

    def _set_pos(self, axis, val):
        target = self.scene_manager.selected_entity
        if target:
            setattr(target, axis, val)
            if self.scene_manager.on_scene_modified:
                self.scene_manager.on_scene_modified()

    def _set_rot(self, attr, val):
        target = self.scene_manager.selected_entity
        if target:
            setattr(target, attr, val % 360)
            if self.scene_manager.on_scene_modified:
                self.scene_manager.on_scene_modified()

    def _set_scale(self, attr, val):
        target = self.scene_manager.selected_entity
        if target:
            setattr(target, attr, max(0.05, val))
            if self.scene_manager.on_scene_modified:
                self.scene_manager.on_scene_modified()

    def _uniform_scale_factor(self, factor):
        target = self.scene_manager.selected_entity
        if target:
            target.scale_x = max(0.05, target.scale_x * factor)
            target.scale_y = max(0.05, target.scale_y * factor)
            target.scale_z = max(0.05, target.scale_z * factor)
            self.refresh()
            if self.scene_manager.on_scene_modified:
                self.scene_manager.on_scene_modified()

    def _uniform_scale_delta(self, delta):
        target = self.scene_manager.selected_entity
        if target:
            target.scale_x = max(0.05, target.scale_x + delta)
            target.scale_y = max(0.05, target.scale_y + delta)
            target.scale_z = max(0.05, target.scale_z + delta)
            self.refresh()
            if self.scene_manager.on_scene_modified:
                self.scene_manager.on_scene_modified()

    def _set_uniform_scale(self, val):
        target = self.scene_manager.selected_entity
        if target:
            target.scale = Vec3(val, val, val)
            self.refresh()
            if self.scene_manager.on_scene_modified:
                self.scene_manager.on_scene_modified()

    def _set_model(self, model_name):
        target = self.scene_manager.selected_entity
        if not target:
            return
        target.editor_model = model_name
        if model_name == 'cylinder':
            target.model = Cylinder(resolution=16)
        elif model_name == 'cone':
            target.model = Cone(resolution=16)
        else:
            target.model = model_name

        self.refresh()
        if self.scene_manager.on_scene_modified:
            self.scene_manager.on_scene_modified()

    def _set_color(self, col):
        target = self.scene_manager.selected_entity
        if target:
            target.color = col
            if self.scene_manager.on_scene_modified:
                self.scene_manager.on_scene_modified()

    def _set_texture(self, new_tex):
        target = self.scene_manager.selected_entity
        if not target:
            return
        target.editor_texture = new_tex
        target.texture = new_tex
        self.refresh()
        if self.scene_manager.on_scene_modified:
            self.scene_manager.on_scene_modified()

    def _set_collider(self, new_col):
        target = self.scene_manager.selected_entity
        if not target:
            return
        target.editor_collider = new_col
        target.collider = new_col
        self.refresh()
        if self.scene_manager.on_scene_modified:
            self.scene_manager.on_scene_modified()

    def _set_tag(self, new_tag):
        target = self.scene_manager.selected_entity
        if not target:
            return
        target.editor_tag = new_tag
        self.refresh()
        if self.scene_manager.on_scene_modified:
            self.scene_manager.on_scene_modified()

    def _toggle_visibility(self):
        target = self.scene_manager.selected_entity
        if not target:
            return
        target.visible = not target.visible
        self.refresh()
        if self.scene_manager.on_scene_modified:
            self.scene_manager.on_scene_modified()

    def _toggle_unlit(self):
        target = self.scene_manager.selected_entity
        if not target:
            return
        curr = getattr(target, 'editor_unlit', False)
        target.editor_unlit = not curr
        target.unlit = target.editor_unlit
        self.refresh()
        if self.scene_manager.on_scene_modified:
            self.scene_manager.on_scene_modified()
