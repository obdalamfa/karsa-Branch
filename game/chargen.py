"""
chargen.py — Layar pembuatan karakter (Character Creation).

Terinspirasi FreeSO avatar creation:
  - 12 warna baju dari palette au-* (au-red, au-blue, au-green, …)
  - Hat accessory: plain, wizard, jerami, tanpa
  - Skin tones, hair colors, pants colors

Kontrol:
  Up/Down   : pindah opsi
  Left/Right: ganti nilai opsi
  Huruf/BS  : ketik nama (saat di baris Nama)
  Enter     : konfirmasi & mulai game
  ESC       : reset ke default
"""
from ursina import Entity, Text, color, camera, destroy, held_keys

# ── Palettes ──────────────────────────────────────────────────────────────────
# Warna kulit: dari terang ke gelap
SKIN_PRESETS = [
    ('Cerah',  (255, 225, 180)),
    ('Hangat', (240, 195, 150)),
    ('Sawo',   (205, 155, 110)),
    ('Coklat', (168, 112,  72)),
    ('Gelap',  (130,  85,  52)),
    ('Pucat',  (248, 238, 225)),
]

# Warna rambut
HAIR_PRESETS = [
    ('Coklat', ( 58,  38,  18)),
    ('Hitam',  ( 28,  22,  12)),
    ('Pirang', (210, 178,  98)),
    ('Merah',  (188,  62,  42)),
    ('Abu',    (155, 148, 145)),
    ('Putih',  (228, 222, 215)),
]

# Warna baju — FreeSO au-* 8 warna pilihan
SHIRT_PRESETS = [
    ('Hijau',  ( 50, 185,  75)),   # au-green
    ('Merah',  (195,  50,  50)),   # au-red
    ('Biru',   ( 55,  80, 195)),   # au-blue
    ('Kuning', (235, 218,  52)),   # au-yellow
    ('Ungu',   (122,  55, 198)),   # au-purple
    ('Oranye', (218, 130,  45)),   # au-orange
    ('Pink',   (235, 115, 175)),   # au-pink
    ('Cyan',   ( 48, 205, 195)),   # au-cyan
]

# Warna celana
PANTS_PRESETS = [
    ('Navy',   ( 88, 128, 195)),
    ('Coklat', (115,  82,  48)),
    ('Hitam',  ( 45,  40,  55)),
    ('Abu',    (128, 122, 135)),
]

# Topi: (nama, tint_rgb | None, tex_name, scale_xz, scale_y, y_offset)
HAT_PRESETS = [
    ('Coklat', (215, 170, 100), 'hat_brown',    0.78, 0.26, 0.00),
    ('Wizard', (118,  65, 205), 'hat_wizard',   0.65, 0.52, 0.10),
    ('Jerami', (228, 198,  95), 'hat_mushroom', 1.12, 0.16,-0.04),
    ('Cap',    ( 78, 128, 225), 'hat_cap',      0.82, 0.22, 0.00),
    ('Tanpa',  None,            '',             0.00, 0.00, 0.00),
]

# Nama-nama opsi dalam urutan layar
_OPT_KEYS    = ['name',  'skin',       'hair',        'shirt',       'pants',       'hat']
_OPT_LABELS  = ['Nama',  'Kulit',      'Rambut',      'Baju',        'Celana',      'Topi']
_OPT_PRESETS = [None,    SKIN_PRESETS, HAIR_PRESETS,  SHIRT_PRESETS, PANTS_PRESETS, HAT_PRESETS]
_OPT_COUNT   = [None,
                len(SKIN_PRESETS), len(HAIR_PRESETS),
                len(SHIRT_PRESETS), len(PANTS_PRESETS), len(HAT_PRESETS)]

_FONT = 'Montserrat-Bold.ttf'


def _ui(model='quad', **kw):
    kw.setdefault('transparent', True)
    return Entity(parent=camera.ui, model=model, **kw)


def _txt(text='', pos=(0, 0), scale=1.0, col=color.white, **kw):
    kw.setdefault('font', _FONT)
    return Text(text, parent=camera.ui, position=pos,
                scale=scale * 1.8, color=col, **kw)


class ChargenScreen:
    """Layar pembuatan karakter — keyboard-driven overlay.

    Dipanggil dari app.py pada first run. Memanggil on_confirm(state)
    setelah pemain tekan Enter.
    """

    _NAME_MAX = 18

    def __init__(self, state, on_confirm, player=None):
        self.state      = state
        self.on_confirm = on_confirm
        self.player     = player

        # Nilai saat ini per opsi
        self._cursor = 0
        self._name_buf = (state.char_name or 'Petani Muda')[:self._NAME_MAX]
        self._vals = [
            None,              # name
            state.char_skin,
            state.char_hair,
            state.char_shirt,
            state.char_pants,
            state.char_hat,
        ]
        self._ents: list = []
        self._row_lbl: list = []    # Text per baris (label)
        self._row_val: list = []    # Text per baris (value)
        self._row_sw:  list = []    # Entity swatch per baris (warna)
        self._row_hi:  list = []    # Entity highlight per baris
        self._cursor_bar = None

        self._build()
        self._refresh()

    # ─── BUILD UI ──────────────────────────────────────────────────────────
    def _build(self):
        # Layer gelap di belakang
        bg = _ui(scale=(1.10, 1.02), position=(0, 0),
                 color=color.rgb(8, 5, 22, 232))
        border = _ui(scale=(0.84, 0.92), position=(0, 0),
                     color=color.rgb(90, 60, 160, 190))
        inner = _ui(scale=(0.82, 0.90), position=(0, 0),
                    color=color.rgb(12, 8, 28, 230))
        self._ents += [bg, border, inner]

        # Judul
        title = _txt('BUAT KARAKTER', pos=(-0.33, 0.415), scale=1.30,
                      col=color.rgb(240, 210, 80), origin=(0, 0))
        sub = _txt('Lembah Karsa', pos=(-0.33, 0.375), scale=0.75,
                    col=color.rgb(160, 140, 200), origin=(0, 0))
        self._ents += [title, sub]

        # Garis pemisah
        sep = _ui(scale=(0.80, 0.003), position=(0, 0.355),
                   color=color.rgb(130, 90, 200, 180))
        self._ents.append(sep)

        # Baris opsi
        ROW_START_Y = 0.270
        ROW_STEP    = 0.098
        for i in range(len(_OPT_KEYS)):
            y = ROW_START_Y - i * ROW_STEP

            # Highlight baris (awalnya tidak terlihat)
            hi = _ui(scale=(0.80, 0.082), position=(0, y + 0.005),
                      color=color.rgb(80, 50, 140, 90))
            hi.enabled = False
            self._row_hi.append(hi)
            self._ents.append(hi)

            # Label
            lbl = _txt(_OPT_LABELS[i], pos=(-0.38, y + 0.016), scale=0.82,
                        col=color.rgb(165, 148, 195))
            self._row_lbl.append(lbl)
            self._ents.append(lbl)

            # Swatch warna (hanya untuk non-name; hat juga punya warna)
            sw = _ui(model='quad', scale=(0.042, 0.052),
                      position=(-0.13, y + 0.005),
                      color=color.rgb(60, 50, 80))
            self._row_sw.append(sw)
            self._ents.append(sw)

            # Nilai
            val = _txt('', pos=(-0.08, y + 0.016), scale=0.84,
                        col=color.white)
            self._row_val.append(val)
            self._ents.append(val)

        # Garis bawah + hint
        sep2 = _ui(scale=(0.80, 0.003), position=(0, -0.372),
                    color=color.rgb(130, 90, 200, 180))
        hint = _txt('[Up/Down] Pindah   [</> Arah] Ubah   [Enter] Mulai',
                     pos=(-0.40, -0.400), scale=0.66,
                     col=color.rgb(140, 125, 180), origin=(0, 0))
        hint2 = _txt('[ESC] Reset ke default',
                      pos=(-0.40, -0.428), scale=0.62,
                      col=color.rgb(120, 108, 155), origin=(0, 0))
        self._ents += [sep2, hint, hint2]

    def _refresh(self):
        """Update semua teks & swatch sesuai nilai saat ini."""
        for i in range(len(_OPT_KEYS)):
            hi = self._row_hi[i]
            hi.enabled = (i == self._cursor)
            if i == self._cursor:
                hi.color = color.rgb(95, 58, 175, 115)

            if i == 0:
                # Nama — tampilkan dengan kursor berkedip
                cursor_char = '_' if self._cursor == 0 else ''
                self._row_val[i].text = self._name_buf + cursor_char
                self._row_sw[i].color  = color.rgb(60, 50, 80)
                self._row_lbl[i].color = (color.rgb(255, 240, 120)
                                           if i == self._cursor
                                           else color.rgb(165, 148, 195))
                continue

            presets = _OPT_PRESETS[i]
            v       = self._vals[i]
            entry   = presets[v]

            if i == len(_OPT_KEYS) - 1:   # Hat: (name, tint, tex, ...)
                name, tint_rgb = entry[0], entry[1]
                val_text = f'[A] {name}  {v+1}/{len(presets)} [D]'
                swatch_col = (color.rgb(*tint_rgb) if tint_rgb
                               else color.rgb(40, 35, 52))
            else:                          # color preset: (name, rgb)
                name, rgb = entry
                val_text = f'[A] {name}  {v+1}/{len(presets)} [D]'
                swatch_col = color.rgb(*rgb)

            self._row_val[i].text = val_text
            self._row_sw[i].color  = swatch_col
            self._row_lbl[i].color = (color.rgb(255, 240, 120)
                                       if i == self._cursor
                                       else color.rgb(165, 148, 195))

        # Update preview karakter jika ada
        if self.player:
            try:
                self.player.apply_appearance(self._to_state())
            except Exception:
                pass

    def _to_state(self):
        """Buat objek proxy state dengan nilai chargen saat ini."""
        class _S:
            pass
        s = _S()
        s.char_name  = self._name_buf
        s.char_skin  = self._vals[1]
        s.char_hair  = self._vals[2]
        s.char_shirt = self._vals[3]
        s.char_pants = self._vals[4]
        s.char_hat   = self._vals[5]
        return s

    # ─── INPUT ─────────────────────────────────────────────────────────────
    def handle_input(self, key) -> bool:
        """Return True jika input dikonsumsi."""
        if key == 'escape':
            self._reset_defaults()
            return True

        if key in ('up arrow', 'w'):
            self._cursor = max(0, self._cursor - 1)
            self._refresh()
            return True

        if key in ('down arrow', 's'):
            self._cursor = min(len(_OPT_KEYS) - 1, self._cursor + 1)
            self._refresh()
            return True

        if key in ('enter', ):
            self._confirm()
            return True

        if self._cursor == 0:
            # Mode ketik nama
            if key == 'backspace':
                self._name_buf = self._name_buf[:-1]
                self._refresh()
                return True
            if key == 'space':
                if len(self._name_buf) < self._NAME_MAX:
                    self._name_buf += ' '
                self._refresh()
                return True
            if len(key) == 1 and (key.isalpha() or key.isdigit()):
                if len(self._name_buf) < self._NAME_MAX:
                    c = key.upper() if held_keys.get('shift') else key
                    self._name_buf += c
                self._refresh()
                return True
        else:
            # Mode pilih nilai
            if key in ('left arrow', 'a', 'q'):
                n = _OPT_COUNT[self._cursor]
                self._vals[self._cursor] = (self._vals[self._cursor] - 1) % n
                self._refresh()
                return True
            if key in ('right arrow', 'd', 'r'):
                n = _OPT_COUNT[self._cursor]
                self._vals[self._cursor] = (self._vals[self._cursor] + 1) % n
                self._refresh()
                return True

        return False

    # ─── HELPERS ───────────────────────────────────────────────────────────
    def _reset_defaults(self):
        self._name_buf  = 'Petani Muda'
        self._vals[1:]  = [0, 0, 0, 0, 0]
        self._cursor    = 0
        self._refresh()

    def _confirm(self):
        s = self.state
        s.char_name  = self._name_buf.strip() or 'Petani Muda'
        s.char_skin  = self._vals[1]
        s.char_hair  = self._vals[2]
        s.char_shirt = self._vals[3]
        s.char_pants = self._vals[4]
        s.char_hat   = self._vals[5]
        self.destroy_all()
        self.on_confirm(s)

    def destroy_all(self):
        for e in self._ents:
            try:
                destroy(e)
            except Exception:
                pass
        self._ents.clear()
        self._row_lbl.clear()
        self._row_val.clear()
        self._row_sw.clear()
        self._row_hi.clear()
