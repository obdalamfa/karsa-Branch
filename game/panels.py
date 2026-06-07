"""
panels.py — 2D UI overlay untuk Ursina Engine.
Semua elemen UI menggunakan camera.ui sebagai parent (screen-space).

Layout layar (Ursina screen coords: -0.5 ke 0.5):
  ┌──────────────────────────────────┐
  │ [Tool] [Seed]    [Scene] [Cuaca] │  ← baris atas kiri / kanan
  │ HP ████░░░░░░                    │
  │ EN ████████░░                    │
  │ 💰 Gold: 100G      [Waktu/Hari]  │
  └──────────────────────────────────┘

Dialog box: muncul di bawah tengah.
Panel (inventori, quest, dll.): overlay penuh semi-transparan.
"""
from pathlib import Path as _Path
from PIL import Image as _PILImg
from ursina import (Entity, Text, Texture, color, camera, destroy,
                    Vec2, Vec4, invoke)

from .config import SEASON_NAMES, NEED_LOW, NEED_CRITICAL, NEED_MAX

# Thermometer sprite textures (FreeSO up_thermo_slice pattern)
_THERMO_BG_TEX   = None   # up_thermo_slice      (inactive bar)
_THERMO_FILL_TEX = None   # up_thermo_slice_active (filled bar)

def _init_thermo_tex():
    global _THERMO_BG_TEX, _THERMO_FILL_TEX
    _a = _Path(__file__).resolve().parent.parent / 'assets' / 'ui'
    def _lt(name):
        p = _a / f'{name}.png'
        if p.exists():
            try:
                return Texture(_PILImg.open(p))
            except Exception:
                pass
        return None
    _THERMO_BG_TEX   = _lt('up_thermo_slice')
    _THERMO_FILL_TEX = _lt('up_thermo_slice_active')
from .data import CROPS
from .data import (HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS,
                   QUEST_STAGES, SWORD_RECIPES, PICKAXE_RECIPES, SHOP_ITEMS)

_ALL_NPCS = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}


def _ui(model='quad', **kw):
    # Tidak pakai shader agar color property bekerja di camera.ui space.
    # transparent=True wajib agar alpha channel diterapkan oleh renderer.
    kw.setdefault('transparent', True)
    return Entity(parent=camera.ui, model=model, **kw)


_FONT_NAME = 'Montserrat-Bold.ttf'  # Ursina cari via glob(**) di asset_folder

def _txt(text='', pos=(0, 0), scale=1.0, col=color.white, **kw):
    kw.setdefault('font', _FONT_NAME)
    return Text(text, parent=camera.ui, position=pos,
                scale=scale * 1.2, color=col, **kw)


class UIManager:
    """Mengelola semua HUD dan panel."""

    def __init__(self, state):
        self.state       = state
        self.mode        = 'hud'    # 'hud' | 'dialog' | 'panel'
        self._panel_name = None
        self._dialog_lines: list = []
        self._dialog_idx  = 0
        self._dialog_npc  = None
        self._dlg_choices = []
        self._dlg_choice_idx = 0
        self._dlg_choices_active = False

        self._flash_ent = None
        self._flash_t   = 0.0

        _init_thermo_tex()
        self._build_hud()
        self._build_dialog_box()
        self._build_panel_bg()
        self._build_inventory_grid()
        self._build_pie_menu()

        # Previous motives cache for Arrow indicators
        self._prev_hunger = None
        self._prev_social = None
        self._prev_fun = None
        self._prev_energy = None

    # ─── PUBLIC: UPDATE ──────────────────────────────────
    def update(self, state, dt: float = 0):
        self.state = state
        if self.mode == 'hud':
            self._refresh_hud()

        # Flash message timer
        if self._flash_t > 0:
            self._flash_t -= dt
            if self._flash_t <= 0 and self._flash_ent:
                self._flash_ent.enabled = False
                if hasattr(self, '_flash_bg'):
                    self._flash_bg.enabled = False

    _TOOL_NAMES = ['Cangkul','Siram','Tanam','Panen','Kapak','Hadiah','Pickaxe','Pedang']
    # (simbol, warna_bg, warna_teks) per tool index
    _TOOL_ICON_DATA = [
        ('CGK', color.rgb(120, 88,  50),  color.rgb(255, 220, 120)),  # Cangkul
        (' ~ ', color.rgb(30,  90, 160),  color.rgb(120, 200, 255)),  # Siram
        (' * ', color.rgb(30, 100,  40),  color.rgb(140, 255, 120)),  # Tanam
        (' H ', color.rgb(80, 110,  30),  color.rgb(200, 255,  80)),  # Panen
        ('KPK', color.rgb(140,  70,  20), color.rgb(255, 170,  60)),  # Kapak
        (' + ', color.rgb(130,  30,  70), color.rgb(255, 120, 160)),  # Hadiah
        ('PKX', color.rgb(60,   60, 100), color.rgb(180, 180, 255)),  # Pickaxe
        ('PDG', color.rgb(130,  20,  20), color.rgb(255, 100, 100)),  # Pedang
    ]

    # ─── PUBLIC: HUD ─────────────────────────────────────
    def _build_hud(self):
        """HUD bawah gaya DOOM — status bar rapi di bawah layar (wajah di tengah)."""
        GOLD_C = color.rgb(255, 215, 60)
        WHITE  = color.rgb(238, 236, 226)
        BAR_TOP = -0.405
        BAR_BOT = -0.455

        # ── Panel bar penuh di bawah ──
        self._hud_bar    = _ui(scale=(1.95, 0.17), position=(0, -0.435),
                               color=color.rgb(26, 22, 20, 240), z=1.0)
        self._hud_border = _ui(scale=(1.95, 0.010), position=(0, -0.352),
                               color=color.rgb(128, 100, 72), z=0.95)

        # ── Item aktif (tengah) — menggantikan wajah ──
        sym0, bg0, fg0 = self._TOOL_ICON_DATA[0]
        self._item_frame = _ui(scale=(0.115, 0.150), position=(0.0, -0.422), color=color.rgb(48, 38, 28), z=0.6)
        self._item_bg    = _ui(scale=(0.095, 0.128), position=(0.0, -0.422), color=bg0, z=0.5)
        self._item_sym   = _txt(sym0, pos=(0.0, -0.418), scale=1.25, col=fg0, origin=(0, 0))
        self._item_lbl   = _txt(self._TOOL_NAMES[0], pos=(0.0, -0.454), scale=0.58,
                                col=color.rgb(210, 195, 165), origin=(0, 0))

        # ── Kiri jauh: Alat aktif ──
        X_TOOL = -0.82
        self._tool_icon = _ui(scale=(0.055, 0.075), position=(X_TOOL, BAR_TOP), color=color.rgb(205, 180, 90), z=0.5)
        self._tool_name = _txt('Cangkul', pos=(X_TOOL + 0.04, BAR_TOP + 0.012), scale=0.85, col=color.rgb(255, 240, 120))
        self._seed_txt  = _txt('',        pos=(X_TOOL + 0.04, BAR_BOT + 0.005), scale=0.68, col=color.rgb(160, 255, 160))

        # ── Kiri-tengah: HP & EN bar (track + fill) ──
        self._BAR_W      = 0.24
        self._BAR_X_LEFT = -0.55
        self._hp_track = _ui(scale=(self._BAR_W, 0.024), position=(self._BAR_X_LEFT + self._BAR_W/2, BAR_TOP), color=color.rgb(46, 36, 33), z=0.4)
        self._hp_bar   = _ui(scale=(self._BAR_W, 0.024), position=(self._BAR_X_LEFT + self._BAR_W/2, BAR_TOP), color=color.rgb(210, 55, 50), z=0.3)
        self._hp_val   = _txt('HP', pos=(self._BAR_X_LEFT - 0.045, BAR_TOP + 0.012), scale=0.68, col=WHITE)
        self._en_track = _ui(scale=(self._BAR_W, 0.024), position=(self._BAR_X_LEFT + self._BAR_W/2, BAR_BOT), color=color.rgb(46, 36, 33), z=0.4)
        self._en_bar   = _ui(scale=(self._BAR_W, 0.024), position=(self._BAR_X_LEFT + self._BAR_W/2, BAR_BOT), color=color.rgb(70, 180, 80), z=0.3)
        self._en_val   = _txt('EN', pos=(self._BAR_X_LEFT - 0.045, BAR_BOT + 0.010), scale=0.68, col=WHITE)

        self._buff_txt  = _txt('', pos=(-0.26, BAR_TOP + 0.012), scale=0.65, col=color.rgb(120, 255, 180))
        self._queue_txt = _txt('', pos=(-0.26, BAR_BOT + 0.005), scale=0.65, col=color.rgb(255, 210, 80))

        # ── Kanan-tengah: Emas ──
        self._gold_txt = _txt('§ 0G', pos=(0.16, BAR_TOP + 0.006), scale=1.05, col=GOLD_C)

        # ── Kanan jauh: Waktu / tanggal / cuaca / scene ──
        X_R = 0.50
        self._time_txt    = _txt('06:00',  pos=(X_R, BAR_TOP + 0.010), scale=1.15, col=WHITE)
        self._date_txt    = _txt('Hari 1',  pos=(X_R, BAR_BOT + 0.005), scale=0.66, col=color.rgb(170, 200, 255))
        self._weather_txt = _txt('^ Cerah', pos=(X_R + 0.26, BAR_TOP + 0.012), scale=0.66, col=color.rgb(255, 240, 130))
        self._scene_txt   = _txt('> Kebun', pos=(X_R + 0.26, BAR_BOT + 0.005), scale=0.66, col=color.rgb(140, 255, 160))

        self._need_lbl_ents  = []
        self._need_bg_ents   = []
        self._need_fill_ents = []
        self._NBAR_W = 0
        self._NBAR_X = 0

        # ── Flash message tengah ──
        self._flash_ent = _txt('', pos=(0, 0.15), scale=1.1,
                               col=color.rgb(255, 245, 80), origin=(0, 0))
        self._flash_ent.enabled = False

        # ── Hint kontrol (tepat di atas bar) ──
        self._control_hint = _txt(
            '', pos=(0, -0.335), scale=0.68,
            col=color.rgb(205, 222, 245), origin=(0, 0)
        )

    def _refresh_hud(self):
        s = self.state
        BAR_W = self._BAR_W
        BAR_X_LEFT = self._BAR_X_LEFT

        def _shrink_bar(bar, x_left, full_w, ratio):
            """Bar fill: anchored di sisi kiri, lebar berubah sesuai ratio."""
            w = max(0.001, full_w * ratio)
            bar.scale_x = w
            bar.x = x_left + w / 2

        # HP bar
        hp_r = max(0.001, s.hp / max(s.max_hp, 1))
        _shrink_bar(self._hp_bar, BAR_X_LEFT, BAR_W, hp_r)
        if hp_r > 0.6:
            self._hp_bar.color = color.rgb(55, 210, 80)
        elif hp_r > 0.3:
            self._hp_bar.color = color.rgb(255, 170, 30)
        else:
            self._hp_bar.color = color.rgb(220, 55, 55)
        self._hp_val.text = f'{int(s.hp)}/{s.max_hp}'

        # EN bar
        en_r = max(0.001, s.energy / max(s.max_energy, 1))
        _shrink_bar(self._en_bar, BAR_X_LEFT, BAR_W, en_r)
        self._en_bar.color = color.rgb(220, 80, 55) if en_r <= 0.3 else color.rgb(55, 205, 75)
        self._en_val.text = f'{int(s.energy)}/{s.max_energy}'

        # Gold + buff (§ simbol web-style)
        self._gold_txt.text = f'§ {s.gold}G'
        self._buff_txt.text = '+'.join(b.upper() for b in s.buffs) if s.buffs else ''

        # Active tool name + center icon
        ti = min(s.tool_index, len(self._TOOL_NAMES) - 1)
        self._tool_name.text = self._TOOL_NAMES[ti]
        sym, bg, fg = self._TOOL_ICON_DATA[ti]
        self._item_bg.color  = bg
        self._item_sym.text  = sym
        self._item_sym.color = fg
        self._item_lbl.text  = self._TOOL_NAMES[ti]

        # Seed hint (shown when Tanam/Panen active)
        if s.tool_index in (2, 3):
            seed_name = CROPS.get(s.seed_key, {}).get('name', s.seed_key)
            seed_qty  = s.inventory.get(s.seed_key + '_seed', 0)
            self._seed_txt.text = f'O/P: {seed_name} x{seed_qty}'
        else:
            self._seed_txt.text = '[1-8] pilih alat'

        # Time / weather
        self._time_txt.text = s.get_time_str()
        w_icons = {'Cerah': '^', 'Hujan': '~', 'Badai': '!', 'Mendung': '-', 'Berangin': '='}
        self._weather_txt.text = f"{w_icons.get(s.weather, '?')} {s.weather}"

        # Date / scene
        season_n = SEASON_NAMES[s.season_index]
        self._date_txt.text = f'Hari {s.day_in_season} | {season_n} Thn {s.year}'
        from .scenes import SCENES
        sc_display = SCENES.get(s.scene_name,
                     type('o', (object,), {'display': s.scene_name})()).display
        self._scene_txt.text = f'> {sc_display}'
        
        # Action prompt dynamic
        if hasattr(s, 'action_prompt'):
            self._control_hint.text = s.action_prompt
        else:
            self._control_hint.text = '[WASD] Jalan  ·  [Q/E] Putar Kamera  ·  [SPACE] Pakai  ·  [R] Aksi  ·  [F1] Panduan  ·  [I] Inv'

    # ─── PUBLIC: FLASH MESSAGE ───────────────────────────
    def flash_msg(self, text: str, duration: float = 1.2):
        if self._flash_ent:
            self._flash_ent.text    = text
            self._flash_ent.enabled = True
            if hasattr(self, '_flash_bg'):
                self._flash_bg.enabled = True
            self._flash_t           = duration

    def show_message(self, text: str, duration: float = 2.0):
        self.flash_msg(text, duration)

    # ─── PUBLIC: DIALOG ──────────────────────────────────
    def _build_dialog_box(self):
        # Background kotak dialog diperkecil
        self._dlg_bg = _ui(scale=(0.70, 0.18), position=(0, -0.38),
                            color=color.rgb(15, 8, 30, 220))
        self._dlg_border = _ui(scale=(0.71, 0.19), position=(0, -0.38),
                                color=color.rgb(100, 70, 160, 180))
        self._dlg_name = _txt('', pos=(-0.33, -0.31), scale=0.90,
                               col=color.rgb(220, 190, 255))
        self._dlg_text = _txt('', pos=(-0.33, -0.36), scale=0.85,
                               col=color.rgb(230, 220, 255))
        self._dlg_cont = _txt('[E / SPACE: lanjut]', pos=(0.15, -0.44),
                               scale=0.70, col=color.rgb(150, 130, 200))
        self._dlg_choice_ents = [
            _txt('', pos=(-0.33, -0.34 - i * 0.035), scale=0.80, col=color.rgb(200, 185, 230))
            for i in range(3)
        ]
        self._set_dialog_visible(False)

    def _set_dialog_visible(self, v: bool):
        for e in (self._dlg_bg, self._dlg_border,
                  self._dlg_name, self._dlg_text, self._dlg_cont):
            e.enabled = v
        for e in self._dlg_choice_ents:
            e.enabled = v if (self._dlg_choices_active and v) else False

    def start_dialog(self, npc_id: str, state, node_key: str = None):
        self.state      = state
        self._dialog_npc = npc_id
        self._dialog_idx = 0
        self._dlg_choices_active = False
        self._dlg_choices = []

        if node_key is not None:
            from .data import BRANCHING_DIALOGUES
            node = BRANCHING_DIALOGUES.get(node_key)
            if node:
                self._dialog_lines = [node]
            else:
                self._dialog_lines = ["..."]
        elif npc_id == 'mailbox':
            self._dialog_lines = [
                ["Surat dari Paman Arsa:"],
                ["Selamat datang di Lembah Karsa, keponakanku."],
                ["Rawat kebun ini baik-baik. Tanah di sini istimewa."],
                ["Kenali penduduk desa \u2014 mereka akan membantumu."],
                ["Jangan abaikan lembah ini. Suatu hari kau akan mengerti"],
                ["kenapa aku pergi. Bukan kabur \u2014 tapi mencari jawaban."],
                ["Ada perjanjian kuno yang harus dijaga."],
                ["Aku tidak cukup kuat untuk memenuhinya."],
                ["Tapi kau... kau bisa. Aku percaya padamu."],
                ["Salam hangat, Pamanmu Arsa."],
            ]
        else:
            npc_data = _ALL_NPCS.get(npc_id, {})
            dial_idx = state.npc_dialog_index.get(npc_id, 0)
            talks_raw = npc_data.get('talks', [["..."]])

            # Support new dict-based cascaded dialog format
            if isinstance(talks_raw, dict):
                hearts = state.npc_hearts.get(npc_id, 0)
                qs = state.quest_stage
                chosen = None
                # Priority: quest_11 > quest_10 > quest_5 > hearts_10 > hearts_7 > hearts_5 > hearts_3 > default
                if qs >= 11 and 'quest_11' in talks_raw:
                    chosen = talks_raw['quest_11']
                elif qs >= 10 and 'quest_10' in talks_raw:
                    chosen = talks_raw['quest_10']
                elif qs >= 5 and 'quest_5' in talks_raw:
                    chosen = talks_raw['quest_5']
                if chosen is None:
                    for h in (10, 7, 5, 3):
                        key = f'hearts_{h}'
                        if hearts >= h and key in talks_raw:
                            chosen = talks_raw[key]
                            break
                if chosen is None:
                    chosen = talks_raw.get('default', [["..."]])
                self._dialog_lines = [chosen[dial_idx % len(chosen)]]
            else:
                # Legacy list format fallback
                self._dialog_lines = [talks_raw[dial_idx % len(talks_raw)]]

        self._show_dialog_line()
        self.mode = 'dialog'

    def _show_dialog_line(self):
        if self._dialog_idx >= len(self._dialog_lines):
            self._end_dialog()
            return
        npc_data = _ALL_NPCS.get(self._dialog_npc, {})
        name     = npc_data.get('name', self._dialog_npc) if self._dialog_npc != 'mailbox' else 'Kotak Pos'
        line     = self._dialog_lines[self._dialog_idx]

        if isinstance(line, dict):
            # Branching node dictionary
            text = line.get('text', '')
            self._dlg_name.text = name
            self._dlg_text.text = text

            # Filter valid choices by condition
            choices = line.get('choices', [])
            valid_choices = []
            for c in choices:
                cond = c.get('condition')
                show = True
                if cond:
                    if 'min_hearts' in cond:
                        for nid, val in cond['min_hearts'].items():
                            if self.state.npc_hearts.get(nid, 0) < val:
                                show = False
                    if 'has_item' in cond:
                        item_req = cond['has_item']
                        if self.state.inventory.get(item_req, 0) <= 0:
                            show = False
                    if 'side_quest_active' in cond:
                        qkey = cond['side_quest_active']
                        if self.state.side_quests.get(qkey) != 'active':
                            show = False
                if show:
                    valid_choices.append(c)

            if valid_choices:
                self._dlg_choices = valid_choices
                self._dlg_choice_idx = 0
                self._dlg_choices_active = True

                # Expand dialog UI size for choices
                self._dlg_bg.scale_y = 0.26
                self._dlg_bg.y = -0.34
                self._dlg_border.scale_y = 0.27
                self._dlg_border.y = -0.34
                self._dlg_cont.text = '[Tekan 1-3 atau Arrow+Space]'
                self._dlg_text.y = -0.27

                self._refresh_dialog_choices_ui()
            else:
                self._dlg_choices_active = False
                self._dlg_choices = []
                self._dlg_bg.scale_y = 0.18
                self._dlg_bg.y = -0.38
                self._dlg_border.scale_y = 0.19
                self._dlg_border.y = -0.38
                self._dlg_cont.text = '[E / SPACE: lanjut]'
                self._dlg_text.y = -0.36
                for ent in self._dlg_choice_ents:
                    ent.enabled = False

            self._set_dialog_visible(True)
        else:
            # Legacy simple text line
            self._dlg_choices_active = False
            self._dlg_choices = []
            self._dlg_bg.scale_y = 0.18
            self._dlg_bg.y = -0.38
            self._dlg_border.scale_y = 0.19
            self._dlg_border.y = -0.38
            self._dlg_cont.text = '[E / SPACE: lanjut]'
            self._dlg_text.y = -0.36
            for ent in self._dlg_choice_ents:
                ent.enabled = False

            text = ' '.join(line) if isinstance(line, list) else line
            self._dlg_name.text = name
            self._dlg_text.text = text
            self._set_dialog_visible(True)

    def advance_dialog(self) -> bool:
        """Maju ke baris berikutnya. Return True jika dialog selesai."""
        if self._dlg_choices_active:
            # Cannot advance linearly while choices are active
            return False
        self._dialog_idx += 1
        if self._dialog_idx >= len(self._dialog_lines):
            self._end_dialog()
            return True
        self._show_dialog_line()
        return False

    def _end_dialog(self):
        # Majukan dialog index NPC
        if self._dialog_npc and self._dialog_npc != 'mailbox':
            s   = self.state
            npc = _ALL_NPCS.get(self._dialog_npc, {})
            idx = s.npc_dialog_index.get(self._dialog_npc, 0)
            s.npc_dialog_index[self._dialog_npc] = idx + 1
            s.npc_hearts[self._dialog_npc] = min(10, s.npc_hearts.get(self._dialog_npc, 0) + 0.1)
        self._set_dialog_visible(False)
        self.mode = 'hud'
        if hasattr(self, 'player') and self.player:
            if hasattr(self.player, '_check_quest_progress'):
                self.player._check_quest_progress(self)
            elif getattr(self.player, 'quest_controller', None):
                self.player.quest_controller.check_quest_progress(self)

    def _refresh_dialog_choices_ui(self):
        for i, ent in enumerate(self._dlg_choice_ents):
            if i < len(self._dlg_choices):
                c = self._dlg_choices[i]
                prefix = '> ' if i == self._dlg_choice_idx else '  '
                ent.text = f"{prefix}[{i+1}] {c['text']}"
                if i == self._dlg_choice_idx:
                    ent.color = color.rgb(245, 215, 80)
                else:
                    ent.color = color.rgb(200, 185, 230)
                ent.enabled = True
            else:
                ent.text = ''
                ent.enabled = False

    def is_choice_active(self) -> bool:
        return self._dlg_choices_active

    def navigate_dialog_choices(self, delta: int):
        if not self._dlg_choices:
            return
        self._dlg_choice_idx = (self._dlg_choice_idx + delta) % len(self._dlg_choices)
        self._refresh_dialog_choices_ui()

    def confirm_dialog_choice(self):
        if not self._dlg_choices:
            return
        c = self._dlg_choices[self._dlg_choice_idx]
        self._execute_choice(c)

    def select_dialog_choice(self, idx: int):
        if 1 <= idx <= len(self._dlg_choices):
            self._dlg_choice_idx = idx - 1
            self.confirm_dialog_choice()

    def _execute_choice(self, c):
        s = self.state
        effect = c.get('effect')

        if effect:
            if 'hearts' in effect:
                for nid, val in effect['hearts'].items():
                    s.npc_hearts[nid] = min(10, s.npc_hearts.get(nid, 0) + val)
            if 'gold' in effect:
                s.gold = max(0, s.gold + effect['gold'])
            if 'energy' in effect:
                s.energy = max(0, min(s.max_energy, s.energy + effect['energy']))
            if 'sosial' in effect:
                s.sosial = max(0, min(NEED_MAX, s.sosial + effect['sosial']))
            if 'give_item' in effect:
                item = effect['give_item']
                s.inventory[item] = s.inventory.get(item, 0) + 1
            if 'take_item' in effect:
                item = effect['take_item']
                s.inventory[item] = max(0, s.inventory.get(item, 0) - 1)
            if 'start_side_quest' in effect:
                qkey = effect['start_side_quest']
                s.side_quests[qkey] = 'active'
                self.flash_msg(f"Quest baru: {qkey.replace('_', ' ').title()}", 3.0)
            if 'complete_side_quest' in effect:
                qkey = effect['complete_side_quest']
                s.side_quests[qkey] = 'completed'
                self.flash_msg(f"Quest selesai: {qkey.replace('_', ' ').title()}!", 3.0)
                s.stats['gifts'] = s.stats.get('gifts', 0) + 1
            if 'naga_defeated' in effect:
                s.naga_defeated = effect['naga_defeated']

        nxt = c.get('next')
        if nxt:
            self.start_dialog(self._dialog_npc, s, node_key=nxt)
        else:
            self._end_dialog()

    # ─── PUBLIC: PANEL ───────────────────────────────────
    def _build_panel_bg(self):
        self._panel_bg = _ui(scale=(1.5, 1.2), position=(0, 0),
                              color=color.rgb(10, 5, 20, 210))
        self._panel_title = _txt('', pos=(-0.45, 0.44), scale=1.2,
                                  col=color.rgb(220, 190, 255))
        self._panel_body  = _txt('', pos=(-0.45, 0.36), scale=0.80,
                                  col=color.rgb(210, 210, 230))
        self._panel_hint  = _txt('[ESC: tutup]', pos=(-0.45, -0.44), scale=0.75,
                                  col=color.rgb(140, 130, 180))
        self._set_panel_visible(False)

    def _set_panel_visible(self, v: bool):
        for e in (self._panel_bg, self._panel_title,
                  self._panel_body, self._panel_hint):
            e.enabled = v
        if not v:
            self._hide_inventory_grid()

    # ─── INVENTORY GRID (gaya Harvest Moon) ──────────────────
    _INV_COLS = 7
    _INV_ROWS = 5
    _INV_CATS = ['Semua', 'Benih', 'Panen', 'Bahan', 'Alat']

    def _build_inventory_grid(self):
        """Grid slot inventory: kategori tab + border + bg + ikon + jumlah + kursor."""
        self._inv_slots   = []
        self._inv_cursor  = 0   # index slot terpilih
        self._inv_cat_idx = 0   # index kategori aktif
        x0, y0 = -0.46, 0.28
        dx, dy = 0.155, 0.150

        # ── Kategori tab di atas grid ──
        self._inv_cat_tabs = []
        cat_x0 = -0.48
        for i, cat in enumerate(self._INV_CATS):
            tab = _txt(cat, pos=(cat_x0 + i * 0.24, y0 + 0.075), scale=0.68,
                       col=color.rgb(255, 220, 100) if i == 0 else color.rgb(150, 140, 120),
                       origin=(0, 0))
            tab.enabled = False
            self._inv_cat_tabs.append(tab)

        # ── Detail item (bawah grid) ──
        self._inv_detail = _txt('', pos=(x0, y0 - self._INV_ROWS * dy - 0.01),
                                scale=0.60, col=color.rgb(200, 190, 165), origin=(0, 0))
        self._inv_detail.enabled = False

        for r in range(self._INV_ROWS):
            for c in range(self._INV_COLS):
                px = x0 + c * dx
                py = y0 - r * dy
                border  = _ui(scale=(0.135, 0.135), position=(px, py), color=color.rgb(95, 74, 52), z=-0.06)
                bg      = _ui(scale=(0.122, 0.122), position=(px, py), color=color.rgb(38, 32, 28, 240), z=-0.08)
                icon    = _ui(scale=(0.088, 0.088), position=(px, py + 0.010), color=color.rgb(120, 120, 120), z=-0.12)
                qty     = _txt('', pos=(px + 0.028, py - 0.052), scale=0.62, col=color.rgb(255, 255, 230), z=-0.16)
                nm      = _txt('', pos=(px, py - 0.062), scale=0.40, col=color.rgb(205, 205, 215), origin=(0, 0), z=-0.16)
                cursor  = _ui(scale=(0.140, 0.140), position=(px, py), color=color.rgb(255, 215, 60, 180), z=-0.04)
                cursor.enabled = False
                for e in (border, bg, icon, qty, nm):
                    e.enabled = False
                self._inv_slots.append({'border': border, 'bg': bg, 'icon': icon,
                                        'qty': qty, 'nm': nm, 'cursor': cursor})

    def _hide_inventory_grid(self):
        for slot in getattr(self, '_inv_slots', []):
            for e in slot.values():
                e.enabled = False
        for tab in getattr(self, '_inv_cat_tabs', []):
            tab.enabled = False
        if hasattr(self, '_inv_detail'):
            self._inv_detail.enabled = False

    @staticmethod
    def _item_icon_color(item_id: str):
        """Warna kategori untuk fallback ikon (Harvest Moon vibe)."""
        if item_id.endswith('_seed'):            return color.rgb(110, 180, 90)   # benih hijau
        if item_id in CROPS:                     return color.rgb(225, 150, 70)   # hasil panen oranye
        if item_id in ('kayu', 'batu'):          return color.rgb(140, 105, 65)   # bahan coklat
        if 'besi' in item_id or 'tembaga' in item_id or 'emas' in item_id or 'ore' in item_id or 'kristal' in item_id or 'mithril' in item_id:
            return color.rgb(165, 170, 190)      # logam abu
        if 'wild' in item_id or 'herb' in item_id or 'berry' in item_id or 'jamur' in item_id or 'mandrake' in item_id:
            return color.rgb(90, 175, 150)       # liar teal
        if item_id in ('susu', 'telur', 'wol'):  return color.rgb(235, 225, 200)  # produk hewan
        return color.rgb(190, 165, 120)          # default

    def _item_icon_tex(self, item_id: str):
        """Coba muat tekstur ikon (crop) dari assets/textures, else None."""
        cache = getattr(self, '_inv_tex_cache', None)
        if cache is None:
            cache = self._inv_tex_cache = {}
        if item_id in cache:
            return cache[item_id]
        base = item_id[:-5] if item_id.endswith('_seed') else item_id
        tex = None
        for cand in (f'crop_{base}', base, item_id):
            p = _Path(__file__).resolve().parent.parent / 'assets' / 'textures' / f'{cand}.png'
            if p.exists():
                try:
                    tex = Texture(_PILImg.open(p)); break
                except Exception:
                    pass
        cache[item_id] = tex
        return tex

    def _inv_filter_items(self):
        """Kembalikan list (item_id, qty) sesuai kategori aktif."""
        s   = self.state
        cat = self._INV_CATS[getattr(self, '_inv_cat_idx', 0)]
        all_items = [(k, v) for k, v in sorted(s.inventory.items()) if v > 0]
        if cat == 'Semua':
            return all_items
        if cat == 'Benih':
            return [(k, v) for k, v in all_items if k.endswith('_seed')]
        if cat == 'Panen':
            return [(k, v) for k, v in all_items if k in CROPS]
        if cat == 'Bahan':
            return [(k, v) for k, v in all_items
                    if k in ('kayu', 'batu') or any(x in k for x in
                       ('besi', 'tembaga', 'emas', 'ore', 'kristal', 'mithril', 'wild', 'herb', 'berry', 'mandrake'))]
        if cat == 'Alat':
            return [(k, v) for k, v in all_items if k in ('susu', 'telur', 'wol') or
                    not (k.endswith('_seed') or k in CROPS or
                         k in ('kayu', 'batu') or
                         any(x in k for x in ('besi', 'tembaga', 'emas', 'ore', 'kristal', 'mithril',
                                               'wild', 'herb', 'berry', 'mandrake')))]
        return all_items

    def _render_inventory_grid(self):
        """Isi slot dari state.inventory (filter kategori, tampilkan kursor)."""
        items   = self._inv_filter_items()
        cursor  = getattr(self, '_inv_cursor', 0)
        cursor  = min(cursor, max(0, len(items) - 1))
        self._inv_cursor = cursor

        # Update tab warna
        for i, tab in enumerate(getattr(self, '_inv_cat_tabs', [])):
            tab.color = color.rgb(255, 215, 60) if i == getattr(self, '_inv_cat_idx', 0) else color.rgb(150, 140, 120)
            tab.enabled = True

        for i, slot in enumerate(self._inv_slots):
            is_cursor = (i == cursor)
            if i < len(items):
                item_id, qty = items[i]
                slot['border'].enabled = True
                slot['bg'].enabled = True
                slot['cursor'].enabled = is_cursor
                ic = slot['icon']
                tex = self._item_icon_tex(item_id)
                if tex is not None:
                    ic.texture = tex
                    ic.color   = color.white
                else:
                    ic.texture = None
                    ic.color   = self._item_icon_color(item_id)
                ic.enabled = True
                slot['qty'].text    = str(qty) if qty > 1 else ''
                slot['qty'].enabled = True
                disp = CROPS.get(item_id, {}).get('name') or item_id.replace('_seed', '~').replace('_', ' ')
                slot['nm'].text    = disp[:9]
                slot['nm'].enabled = True
            else:
                for k, e in slot.items():
                    e.enabled = False

        # Detail item terpilih
        if hasattr(self, '_inv_detail'):
            if items and cursor < len(items):
                item_id, qty = items[cursor]
                disp = CROPS.get(item_id, {}).get('name') or item_id.replace('_seed', '~').replace('_', ' ')
                self._inv_detail.text    = f'{disp}  x{qty}'
                self._inv_detail.enabled = True
            else:
                self._inv_detail.text    = 'Inventori kosong'
                self._inv_detail.enabled = True

    def open_panel(self, name: str):
        self._panel_name = name
        self._render_panel(name)
        self._set_panel_visible(True)
        self.mode = 'panel'

    def _render_panel(self, name: str):
        s = self.state
        titles = {
            'inventory': 'Inventori',
            'quest':     'Catatan Quest',
            'map':       'Peta Dunia',
            'relations': 'Hubungan NPC',
            'shop':      'Toko Bu Sari',
            'crafting':  'Bengkel Pak Budi',
            'help':      'Panduan Kontrol',
            'catatan':   'Catatan Lembah',
        }
        self._panel_title.text = titles.get(name, name.capitalize())
        # Grid inventory hanya muncul di panel inventory
        if name != 'inventory':
            self._hide_inventory_grid()
        # Update hint sesuai panel
        if name == 'shop':
            self._panel_hint.text = '[1-9: Beli]   [ESC: Tutup]'
        elif name == 'crafting':
            self._panel_hint.text = '[1-5: Pickaxe]   [6-9: Pedang]   [ESC: Tutup]'
        else:
            self._panel_hint.text = '[ESC: tutup]'

        if name == 'inventory':
            # Header ringkas di atas, grid slot bergambar di bawah (Harvest Moon)
            self._panel_body.text = (
                f"Emas: {s.gold}G    Pickaxe: Tier {s.pickaxe_tier}    "
                f"Pedang: {s.sword_id or '-'}"
            )
            self._panel_hint.text = '[↑↓←→] Pilih  ·  [Q/E] Kategori  ·  [I/ESC] Tutup'
            self._render_inventory_grid()

        elif name == 'quest':
            qs   = s.quest_stage
            lines= ["── TUGAS UTAMA ──", ""]
            for q in QUEST_STAGES:
                mark = '[v]' if q['s'] < qs else ('[>]' if q['s'] == qs else '[ ]')
                lines.append(f"  {mark} [{q['s']}] {q['t']}: {q['d']}")

            lines.append("")
            lines.append("── QUEST SAMPINGAN ──")
            lines.append("")

            has_side = False
            from .data import SIDE_QUESTS
            s_quests = getattr(s, 'side_quests', {})
            for qkey, status in s_quests.items():
                qdata = SIDE_QUESTS.get(qkey)
                if qdata:
                    mark = '[v]' if status == 'completed' else '[>]'
                    lines.append(f"  {mark} {qdata['name']}: {qdata['desc']}")
                    has_side = True

            if not has_side:
                lines.append("  (Tidak ada quest sampingan aktif)")
            self._panel_body.text = '\n'.join(lines[:28])

        elif name == 'map':
            cur = s.scene_name
            def _loc(key, label):
                return f'[{label}]' if cur != key else f'>>>{label}<<<'
            lines = [
                '',
                f"  {_loc('mountain','LERENG GUNUNG')}",
                '          |',
                f"  {_loc('farm','KEBUN')}---{_loc('town','DESA')}---{_loc('lake','DANAU')}",
                '              |',
                f"         {_loc('cemetery','KUBURAN')}",
                '              |',
                f"         {_loc('naga_cave','GUA HYANG')}",
                '              |',
                f"         {_loc('dungeon', 'DUNGEON Lv.' + str(s.dungeon_level))}",
                '',
                '  Indoor: [rumah] [warung] [klinik]',
                '          [studio] [bengkel]',
                '',
                f"  Lokasi : {s.scene_name}",
                f"  Hari   : {s.day_in_season} | {self._season_name(s)}  Thn {s.year}",
                f"  Cuaca  : {s.weather}",
            ]
            self._panel_body.text = '\n'.join(lines)

        elif name == 'relations':
            lines = []
            for npc_id in list(_ALL_NPCS.keys()):
                hearts = s.npc_hearts.get(npc_id, 0)
                bar    = '*' * int(hearts) + '-' * (10 - int(hearts))
                name_  = _ALL_NPCS[npc_id].get('name', npc_id)
                lines.append(f"  {name_:15s} {bar[:10]}")
            self._panel_body.text = '\n'.join(lines[:25])

        elif name == 'shop':
            lines = [f"Emas: {s.gold}G   Musim: {self._season_name(s)}", '']
            for i, it in enumerate(SHOP_ITEMS):
                num = i + 1
                lines.append(f"  [{num}] {it['name']:18s}  {it['price']:>4}G   ({it['season']})")
            lines.append('')
            lines.append("Tekan angka untuk beli (kurangi gold).")
            self._panel_body.text = '\n'.join(lines)

        elif name == 'crafting':
            inv = s.inventory
            lines = [
                f"Emas: {s.gold}G   Pickaxe: Tier {s.pickaxe_tier}   "
                f"Pedang: {s.sword_id or '-'}", '',
                "── PICKAXE ──",
            ]
            for i, r in enumerate(PICKAXE_RECIPES):
                need = ', '.join(f"{k}×{v}" for k, v in r['needs'].items())
                got_gold = s.gold >= r['cost_gold']
                got_mat  = all(inv.get(k, 0) >= v for k, v in r['needs'].items())
                already  = s.pickaxe_tier >= r['tier']
                mark = '[v]' if already else ('[o]' if (got_gold and got_mat) else '[ ]')
                lines.append(f"  [{i+1}] {mark} {r['name']:18s}  {r['cost_gold']:>4}G + {need}")
            lines.append('')
            lines.append("── PEDANG ──")
            for i, r in enumerate(SWORD_RECIPES):
                num = i + 6
                need = ', '.join(f"{k}×{v}" for k, v in r['needs'].items())
                got_gold = s.gold >= r['cost_gold']
                got_mat  = all(inv.get(k, 0) >= v for k, v in r['needs'].items())
                already  = s.sword_id == r['id']
                mark = '[v]' if already else ('[o]' if (got_gold and got_mat) else '[ ]')
                lines.append(f"  [{num}] {mark} {r['name']:18s}  {r['cost_gold']:>4}G + {need} (DMG {r['damage']})")
            lines.append('')
            lines.append("[ ]=kurang bahan  [o]=siap  [v]=sudah punya")
            self._panel_body.text = '\n'.join(lines)

        elif name == 'help':
            self._panel_body.text = (
                "── GERAK ──\n"
                "  WASD / Arrow  : Jalan\n"
                "  Shift+WASD    : Lari (pakai energi)\n\n"
                "── KAMERA ──\n"
                "  Q / E  : Putar kamera kiri/kanan\n"
                "  Klik kanan + geser : Putar bebas\n\n"
                "── AKSI ──\n"
                "  SPACE  : Pakai alat aktif\n"
                "  R      : Interaksi NPC / objek\n"
                "  Z      : Serang (butuh pedang)\n"
                "  X      : Tambah/hapus tile ke Antrian\n"
                "  C      : Jalankan semua Antrian Aksi\n"
                "  F      : Tangkap makhluk liar\n"
                "  G      : Beri hadiah ke NPC\n"
                "  V      : Makan item (pulihkan HP/EN)\n"
                "  B      : Terbang (Sapoe Terbang)\n"
                "  Y      : Meluncur / Dash Stunt (-15 EN)\n"
                "  T      : Tidur (hanya di Rumah)\n\n"
                "── ALAT (angka 1-8) ──\n"
                "  1-CNG  2-SRM  3-TNM  4-PNS\n"
                "  5-KPK  6-HDH  7-PCK  8-PDG\n"
                "  O/P    : Ganti bibit\n\n"
                "── MENU ──\n"
                "  I: Inventori   M: Peta\n"
                "  J: Quest       H: Relasi NPC\n"
                "  N: Catatan Lembah (lore)\n"
                "  K: Toko (di Warung)  U: Kerajinan (di Bengkel)\n"
                "  F2: Ubah penampilan karakter\n"
                "  F5: Simpan     F9: Muat\n"
                "  ESC: Tutup panel"
            )

        elif name == 'catatan':
            from .data import LORE_ITEMS
            lines = ['Fragmen cerita dan catatan yang kau temukan:', '']
            s_lore = getattr(s, 'lore_collected', [])
            if not s_lore:
                lines.append('  (Belum ada catatan. Jelajahi lembah lebih dalam.)')
            else:
                for lore_id in s_lore:
                    item = LORE_ITEMS.get(lore_id, {})
                    name_ = item.get('name', lore_id)
                    text_ = item.get('text', '')
                    lines.append(f'  [{name_}]')
                    # Word wrap the text to fit panel
                    words = text_.split()
                    line = '    '
                    for w in words:
                        if len(line) + len(w) + 1 > 60:
                            lines.append(line)
                            line = '    ' + w
                        else:
                            line += (' ' if len(line) > 4 else '') + w
                    if line.strip():
                        lines.append(line)
                    lines.append('')
            self._panel_body.text = '\n'.join(lines[:28])

    @staticmethod
    def _season_name(s):
        try:
            from .config import SEASON_NAMES
            return SEASON_NAMES[s.season_index]
        except Exception:
            return '-'

    # ─── PANEL ACTIONS (shop/craft) ──────────────────────
    def panel_action(self, idx: int) -> str:
        """Dipanggil dari app.input() saat user tekan angka di panel.
        idx 1-based. Return pesan untuk flash_msg."""
        if self._panel_name == 'shop':
            return self._buy_shop_item(idx)
        elif self._panel_name == 'crafting':
            return self._craft_item(idx)
        return ''

    def _buy_shop_item(self, idx: int) -> str:
        s = self.state
        if not (1 <= idx <= len(SHOP_ITEMS)):
            return ''
        it = SHOP_ITEMS[idx - 1]
        if s.gold < it['price']:
            return f"Gold kurang ({it['price']}G)."
        s.gold -= it['price']
        s.inventory[it['id']] = s.inventory.get(it['id'], 0) + 1
        if not s.shop_unlocked:
            s.shop_unlocked = True
        self._render_panel('shop')   # refresh tampilan
        return f"Beli {it['name']} -{it['price']}G"

    def _craft_item(self, idx: int) -> str:
        s = self.state
        # 1-5 = pickaxe, 6-9 = sword
        if 1 <= idx <= len(PICKAXE_RECIPES):
            r = PICKAXE_RECIPES[idx - 1]
            if s.pickaxe_tier >= r['tier']:
                return "Sudah punya tier ini atau lebih."
            return self._do_craft(r, set_pickaxe=r['tier'])
        si = idx - len(PICKAXE_RECIPES) - 1   # 6→0, 7→1, …
        if 0 <= si < len(SWORD_RECIPES):
            r = SWORD_RECIPES[si]
            if s.sword_id == r['id']:
                return "Sudah punya pedang ini."
            return self._do_craft(r, set_sword=r['id'])
        return ''

    def _do_craft(self, r: dict, set_pickaxe: int = None, set_sword: str = None) -> str:
        s = self.state
        if s.gold < r['cost_gold']:
            return f"Gold kurang ({r['cost_gold']}G)."
        for k, v in r['needs'].items():
            if s.inventory.get(k, 0) < v:
                return f"Bahan kurang: butuh {k}×{v}."
        # Konsumsi
        s.gold -= r['cost_gold']
        for k, v in r['needs'].items():
            s.inventory[k] -= v
        if set_pickaxe is not None:
            s.pickaxe_tier = set_pickaxe
        if set_sword is not None:
            s.sword_id = set_sword
        self._render_panel('crafting')
        return f"Berhasil membuat {r['name']}!"

    def close_all(self):
        self._set_dialog_visible(False)
        self._set_panel_visible(False)
        self.close_pie()
        self._panel_name = None
        self.mode = 'hud'

    # ─── ACTION QUEUE INDICATOR ─────────────────────────────
    def set_queue_count(self, n: int):
        self._queue_txt.text = f'[ANT:{n}] C=jalan' if n > 0 else ''

    # ─── PIE MENU (FreeSO VMThread.ActionStrings + MotiveAdChanges) ─
    def _build_pie_menu(self):
        BG = color.rgb(12, 6, 28, 235)
        BD = color.rgb(140, 80, 200, 220)
        self._pie_bg     = _ui(scale=(0.45, 0.32), position=(-0.60, -0.10), color=BG)
        self._pie_border = _ui(scale=(0.452, 0.322), position=(-0.60, -0.10), color=BD)
        self._pie_title  = _txt('', pos=(-0.80, 0.040), scale=0.90,
                                col=color.rgb(245, 215, 80))
        self._pie_items  = [
            _txt('', pos=(-0.80, 0.010 - i * 0.030), scale=0.80, col=color.white)
            for i in range(6)
        ]
        self._pie_fx     = _txt('', pos=(-0.80, -0.200), scale=0.72,
                                col=color.rgb(127, 220, 255))
        self._pie_hint   = _txt('[</> ] Pilih  [SPACE] OK  [ESC] Batal',
                                pos=(-0.60, -0.240), scale=0.65,
                                col=color.rgb(160, 140, 200))
        self._pie_hint.origin = (0, 0)
        self._set_pie_visible(False)

        self._pie_options:  list = []
        self._pie_selected: int  = 0
        self._pie_npc_id:   str  = ''
        self._pie_callback       = None

    def _set_pie_visible(self, v: bool):
        for e in [self._pie_bg, self._pie_border, self._pie_title,
                  self._pie_fx, self._pie_hint] + self._pie_items:
            e.enabled = v

    def open_pie_menu(self, npc_id: str, options: list, callback):
        """Open pie menu. options = [(action, label, available, effects_str), ...]"""
        self._pie_npc_id   = npc_id
        self._pie_options  = options
        self._pie_selected = 0
        self._pie_callback = callback
        self.mode = 'pie'
        self._set_pie_visible(True)
        self._refresh_pie_ui()

    def navigate_pie(self, delta: int):
        if not self._pie_options:
            return
        self._pie_selected = (self._pie_selected + delta) % len(self._pie_options)
        self._refresh_pie_ui()

    def confirm_pie(self):
        if not self._pie_options:
            return
        action, _, available, _ = self._pie_options[self._pie_selected]
        if available and self._pie_callback:
            cb  = self._pie_callback
            nid = self._pie_npc_id
            self.close_pie()
            cb(nid, action)

    def close_pie(self):
        self._set_pie_visible(False)
        self._pie_options  = []
        self._pie_callback = None
        if self.mode == 'pie':
            self.mode = 'hud'

    # ─── INVENTORY NAVIGATION ────────────────────────────────
    def navigate_inventory(self, dr: int, dc: int):
        """Gerakkan kursor inventory. dr=baris, dc=kolom."""
        if getattr(self, '_panel_name', '') != 'inventory':
            return
        items  = self._inv_filter_items()
        if not items:
            return
        cur    = getattr(self, '_inv_cursor', 0)
        cols   = self._INV_COLS
        r, c   = divmod(cur, cols)
        c      = max(0, min(cols - 1, c + dc))
        r      = max(0, min(self._INV_ROWS - 1, r + dr))
        new    = r * cols + c
        self._inv_cursor = min(new, len(items) - 1)
        self._render_inventory_grid()

    def navigate_inventory_cat(self, delta: int):
        """Ganti tab kategori inventory."""
        if getattr(self, '_panel_name', '') != 'inventory':
            return
        n = len(self._INV_CATS)
        self._inv_cat_idx = (getattr(self, '_inv_cat_idx', 0) + delta) % n
        self._inv_cursor  = 0
        self._render_inventory_grid()

    def _refresh_pie_ui(self):
        from .data import HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS
        all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
        npc   = all_d.get(self._pie_npc_id, {})
        self._pie_title.text = f">> {npc.get('name', self._pie_npc_id)}"

        for i, item_ent in enumerate(self._pie_items):
            if i < len(self._pie_options):
                _, label, available, effects = self._pie_options[i]
                prefix  = '>' if i == self._pie_selected else ' '
                avail_s = '' if available else ' [terkunci]'
                item_ent.text  = f'{prefix} [{i+1}] {label}{avail_s}'
                if not available:
                    item_ent.color = color.rgb(100, 80, 120)
                elif i == self._pie_selected:
                    item_ent.color = color.rgb(245, 215, 80)
                else:
                    item_ent.color = color.rgb(200, 185, 230)
            else:
                item_ent.text = ''

        # Effects preview for selected option (FreeSO MotiveAdChanges)
        if self._pie_options:
            _, _, _, effects = self._pie_options[self._pie_selected]
            self._pie_fx.text = f'Efek: {effects}' if effects else ''
