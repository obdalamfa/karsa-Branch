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
    """Layar Buat Karakter: panel opsi di kiri, pratinjau hidup di tengah.

    Pratinjaunya adalah pemain SUNGGUHAN di dunia -- kamera didekatkan ke
    depannya selama layar terbuka -- jadi yang dilihat pemain persis yang akan
    ia mainkan. Pilihan diterapkan lewat game/rupa_pemain.py (tekstur + topi)
    dan keahlian lewat game/keahlian.py.

    Kontrol: Atas/Bawah pindah baris, Kiri/Kanan ganti nilai, ketik di baris
    Nama, Z/C putar pratinjau, Enter mulai, ESC kembali ke bawaan.
    """

    _NAME_MAX = 18
    _BARIS = ('name', 'skin', 'hair', 'shirt', 'pants', 'hat', 'perk')
    _LABEL = ('Nama', 'Kulit', 'Rambut', 'Baju', 'Celana', 'Aksesori', 'Keahlian')

    def __init__(self, state, on_confirm, player=None, app=None):
        from . import rupa_pemain as rp
        from .keahlian import KEAHLIAN
        self._daftar = {
            'skin': rp.KULIT, 'hair': rp.RAMBUT, 'shirt': rp.BAJU,
            'pants': rp.CELANA, 'hat': rp.AKSESORI,
            'perk': [(nama, None) for _k, nama, _d in KEAHLIAN],
        }
        self._keahlian = KEAHLIAN
        self.state = state
        self.on_confirm = on_confirm
        self.player = player
        self.app = app
        self._cursor = 0
        self._name_buf = (state.char_name or 'Petani Muda')[:self._NAME_MAX]
        self._vals = {
            'skin': state.char_skin, 'hair': state.char_hair, 'shirt': state.char_shirt,
            'pants': state.char_pants, 'hat': state.char_hat,
            'perk': getattr(state, 'char_perk', 0),
        }
        for k, lst in self._daftar.items():
            self._vals[k] %= len(lst)
        self._ents = []
        self._rows = []
        self._putar = 200.0
        self._simpan_kamera()
        self._build()
        self._refresh(rupa=True)

    # -- kamera pratinjau ---------------------------------------------------
    def _simpan_kamera(self):
        a = self.app
        if a is None:
            return
        self._kamera_lama = (a.camera_dist, a.camera_pitch, a.camera_yaw)
        # Cukup jauh untuk seluruh badan + topi; geser kamera sedikit ke kiri
        # (yaw negatif) supaya pemain berdiri di sebelah kanan panel opsi.
        a.camera_dist, a.camera_pitch, a.camera_yaw = 6.2, 4.0, -14.0
        try:
            a._snap_camera_to_player()
        except Exception:
            pass
        # HUD minggir: bilah HP, roda alat, dan pelacak tutorial duduk di
        # kiri-atas, persis di bawah panel ini.
        self._sembunyikan_hud(True)

    def _sembunyikan_hud(self, ya):
        a = self.app
        p = getattr(a, 'panels', None) if a is not None else None
        if p is None:
            return
        try:
            p.set_hud_visible(not ya)
        except Exception:
            pass
        for nama in ('_obj_bg', '_obj_rust', '_obj_title', '_obj_step', '_obj_hint'):
            e = getattr(p, nama, None)
            if e is not None:
                e.enabled = not ya

    def _pulihkan_kamera(self):
        a = self.app
        if a is None or not hasattr(self, '_kamera_lama'):
            return
        a.camera_dist, a.camera_pitch, a.camera_yaw = self._kamera_lama
        self._sembunyikan_hud(False)

    # -- UI -------------------------------------------------------------------
    def _build(self):
        kayu, krem = color.rgb(96, 64, 40), color.rgb(242, 230, 204)
        tinta, pudar = color.rgb(58, 40, 28), color.rgb(140, 110, 80)
        X0, W = -0.80, 0.62                  # panel kiri: -0.80 .. -0.18
        cx = X0 + W / 2
        self._ents += [
            _ui(scale=(W + 0.024, 0.90), position=(cx, 0.0), color=kayu, z=0.06),
            _ui(scale=(W, 0.876), position=(cx, 0.0), color=krem, z=0.05),
            _ui(scale=(0.30, 0.06), position=(cx, 0.452), color=color.rgb(150, 96, 60), z=0.04),
        ]
        self._ents.append(_txt('BUAT KARAKTER', pos=(cx, 0.452), scale=0.62,
                               col=color.rgb(250, 238, 214), origin=(0, 0)))
        self._ents.append(_txt('Siapa yang datang ke Lembah Karsa?', pos=(cx, 0.395),
                               scale=0.40, col=pudar, origin=(0, 0)))
        y0, dy = 0.32, 0.082
        for i, lab in enumerate(self._LABEL):
            y = y0 - i * dy
            sorot = _ui(scale=(W - 0.04, 0.07), position=(cx, y), color=color.rgb(214, 196, 160), z=0.045)
            sorot.enabled = False
            lbl = _txt(lab, pos=(X0 + 0.035, y), scale=0.46, col=pudar, origin=(-0.5, 0))
            kiri = _txt('«', pos=(X0 + 0.24, y), scale=0.5, col=pudar, origin=(0, 0))
            kanan = _txt('»', pos=(X0 + W - 0.035, y), scale=0.5, col=pudar, origin=(0, 0))
            sw = _ui(scale=(0.036, 0.036), position=(X0 + 0.285, y), color=color.gray, z=0.03)
            val = _txt(' ', pos=(X0 + 0.315, y), scale=0.46, col=tinta, origin=(-0.5, 0))
            self._rows.append((sorot, lbl, kiri, kanan, sw, val))
            self._ents += [sorot, lbl, kiri, kanan, sw, val]
        y_desk = y0 - len(self._LABEL) * dy - 0.01
        self._ents.append(_ui(scale=(W - 0.04, 0.003), position=(cx, y_desk + 0.03), color=kayu, z=0.04))
        self._desk = _txt(' ', pos=(X0 + 0.035, y_desk), scale=0.40, col=tinta, origin=(-0.5, 0.5))
        self._desk.wordwrap = 34
        self._ents.append(self._desk)
        self._ents.append(_txt('Atas/Bawah pilih  -  Kiri/Kanan ubah  -  Z/C putar',
                               pos=(cx, -0.385), scale=0.36, col=pudar, origin=(0, 0)))
        self._ents.append(_txt('[Enter] Mulai bermain', pos=(cx, -0.42), scale=0.46,
                               col=color.rgb(150, 96, 60), origin=(0, 0)))

    def _refresh(self, rupa=False):
        sorot_lbl, pudar = color.rgb(150, 96, 60), color.rgb(140, 110, 80)
        for i, key in enumerate(self._BARIS):
            sorot, lbl, kiri, kanan, sw, val = self._rows[i]
            aktif = i == self._cursor
            sorot.enabled = aktif
            lbl.color = sorot_lbl if aktif else pudar
            if key == 'name':
                val.text = (self._name_buf + ('_' if aktif else '')) or ' '
                sw.enabled = kiri.enabled = kanan.enabled = False
                continue
            nama, nilai = self._daftar[key][self._vals[key]]
            val.text = nama
            kiri.enabled = kanan.enabled = aktif
            if isinstance(nilai, tuple):
                sw.enabled = True
                sw.color = color.rgb(*nilai)
            else:
                sw.enabled = False
        _k, nama, desk = self._keahlian[self._vals['perk']]
        self._desk.text = f'{nama}: {desk}'
        if rupa and self.player is not None:
            try:
                self.player.apply_appearance(self._to_state())
            except Exception:
                pass
        if self.player is not None:
            self.player.rotation_y = self._putar

    def _to_state(self):
        class _S:
            pass
        s = _S()
        s.char_name = self._name_buf
        s.char_skin, s.char_hair = self._vals['skin'], self._vals['hair']
        s.char_shirt, s.char_pants = self._vals['shirt'], self._vals['pants']
        s.char_hat, s.char_perk = self._vals['hat'], self._vals['perk']
        return s

    # -- INPUT ----------------------------------------------------------------
    def handle_input(self, key) -> bool:
        key_baris = self._BARIS[self._cursor]
        if key == 'escape':
            self._reset_defaults()
            return True
        if key == 'up arrow' or (key == 'w' and key_baris != 'name'):
            self._cursor = (self._cursor - 1) % len(self._BARIS)
            self._refresh()
            return True
        if key == 'down arrow' or (key == 's' and key_baris != 'name'):
            self._cursor = (self._cursor + 1) % len(self._BARIS)
            self._refresh()
            return True
        if key == 'enter':
            self._confirm()
            return True
        if key_baris != 'name' and key in ('z', 'c'):
            self._putar = (self._putar + (-30 if key == 'z' else 30)) % 360
            self._refresh()
            return True
        if key_baris == 'name':
            if key == 'backspace':
                self._name_buf = self._name_buf[:-1]
            elif key == 'space' and len(self._name_buf) < self._NAME_MAX:
                self._name_buf += ' '
            elif len(key) == 1 and (key.isalpha() or key.isdigit()) and len(self._name_buf) < self._NAME_MAX:
                self._name_buf += key.upper() if held_keys.get('shift') else key
            else:
                return False
            self._refresh()
            return True
        if key in ('left arrow', 'a', 'right arrow', 'd'):
            n = len(self._daftar[key_baris])
            arah = -1 if key in ('left arrow', 'a') else 1
            self._vals[key_baris] = (self._vals[key_baris] + arah) % n
            self._refresh(rupa=key_baris != 'perk')
            return True
        return False

    def _reset_defaults(self):
        self._name_buf = 'Petani Muda'
        for k in self._vals:
            self._vals[k] = 0
        self._cursor = 0
        self._refresh(rupa=True)

    def _confirm(self):
        s = self.state
        s.char_name = self._name_buf.strip() or 'Petani Muda'
        s.char_skin, s.char_hair = self._vals['skin'], self._vals['hair']
        s.char_shirt, s.char_pants = self._vals['shirt'], self._vals['pants']
        s.char_hat, s.char_perk = self._vals['hat'], self._vals['perk']
        self._pulihkan_kamera()
        self.destroy_all()
        self.on_confirm(s)

    def destroy_all(self):
        for e in self._ents:
            try:
                destroy(e)
            except Exception:
                pass
        self._ents.clear()
        self._rows.clear()
