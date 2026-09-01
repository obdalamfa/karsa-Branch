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
                    Vec2, Vec4, invoke, window)

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
            self._update_motive_panel()
            self._update_action_readout()

        # Flash message timer
        if self._flash_t > 0:
            self._flash_t -= dt
            if self._flash_t <= 0 and self._flash_ent:
                self._flash_ent.enabled = False
                if hasattr(self, '_flash_bg'):
                    self._flash_bg.enabled = False

    _TOOL_NAMES = ['Cangkul','Siram','Tanam','Panen','Kapak','Hadiah','Pickaxe','Pedang']

    # ─── PUBLIC: HUD ─────────────────────────────────────
    def _build_hud(self):
        """HUD tipis yang MENEMPEL di tepi layar (patokan: AWL).

        Bentuk lama memakan seperempat layar dengan empat panel pejal: kotak
        alat 390x280 di kiri-atas, kotak waktu 660x280 di kanan-atas, panel
        SUASANA HATI 285x400 yang mengambang jauh dari tepi, dan pita tombol
        SELEBAR LAYAR di bawah. Diukur dari tangkapan layar 1920x1080: ~27%
        layar tertutup HUD.

        Patokannya justru kebalikannya — bilah stamina TIPIS menempel di
        kiri-atas, tanggal/musim/jam kecil di kanan-atas, petunjuk tombol
        kecil di kanan-bawah, dan latar panel nyaris tidak ada: teks duduk
        langsung di atas dunia dengan alas gelap setipis mungkin.

        Tiga aturan tata letak, dan tidak ada yang keempat:

        1. Semua dijangkar ke SUDUT lewat satu margin yang sama (`M`), jadi
           tidak ada blok yang "hampir" di tepi.
        2. Satu baris menampung sebanyak mungkin. Waktu/tanggal/cuaca dulu
           empat baris bertumpuk; sekarang satu baris rata kanan yang
           lebarnya dihitung dari teksnya sendiri (`_tata_kanan_atas`).
        3. Alas gelap dipas ke isinya tiap kali teksnya berubah, bukan
           dipatok ke kotak tetap. Pita bawah selebar layar mati karena
           alasan ini: ia dibuat selebar layar supaya prompt sepanjang apa
           pun tetap berlatar — padahal yang perlu melar cuma alasnya.

        Informasi tidak dibuang, cuma dikecilkan dan dipindahkan. Delapan
        motif tetap tampil lengkap dengan namanya di sudut kiri-bawah, dan
        TAB menyembunyikan/menampilkannya kalau pemain mau layar bersih.
        """
        TIME_C   = color.rgb(255, 255, 255)
        GOLD_C   = color.rgb(255, 215,  60)

        # ── Tepi layar yang sebenarnya ──
        # camera.ui membentang -aspect/2..+aspect/2 mendatar, BUKAN -0.5..0.5.
        # Angka mati 0.70 lahir dari menebak layar 16:9 lalu menjangkar teks di
        # KIRI-nya; tiap teks lalu tumbuh ke kanan sampai lewat tepi 0.889.
        # Itu sebabnya jam, tanggal, dan nama scene terpotong di screenshot.
        # Yang duduk di kanan dijangkar di KANAN (origin x = +0.5) supaya
        # tumbuhnya ke dalam layar, berapa pun panjang teksnya.
        self._edge_x = window.aspect_ratio / 2
        M = 0.013                       # jarak ke tepi: 14 px di layar 1080
        self._M   = M
        self._X_L = X_L = -self._edge_x + M
        self._X_R = X_R =  self._edge_x - M
        self._Y_T = Y_T =  0.5 - M
        self._Y_B = Y_B = -0.5 + M
        self._GAP = 0.014               # jarak antar potongan dalam satu baris
        self._RA  = (0.5, 0.0)          # rata kanan, jangkar tengah menegak

        # Tinggi satu baris teks di ruang camera.ui = Text.size * skala entity.
        # Dipakai untuk menumpuk baris tanpa menebak; skala di sini adalah
        # argumen `_txt`, yang dikalikan 1.2 di dalamnya.
        def _tinggi(s):
            return 0.025 * s * 1.2

        S_JAM   = 0.92                  # jam: satu-satunya teks yang boleh besar
        S_KECIL = 0.66
        h_jam   = _tinggi(S_JAM)
        h_kecil = _tinggi(S_KECIL)

        # ── Kanan Atas: satu baris jam/cuaca/tanggal + satu baris tipis ──
        # Empat baris jadi dua. Posisi mendatar dihitung ulang dari lebar
        # teksnya di `_tata_kanan_atas`, jadi teks sepanjang apa pun tetap
        # rata kanan dan tidak pernah menabrak yang di sebelahnya.
        r1 = Y_T - h_jam / 2
        r2 = r1 - h_jam / 2 - 0.004 - h_kecil / 2
        self._ROW1_Y, self._ROW2_Y = r1, r2
        self._time_txt    = _txt('06:00',         pos=(X_R, r1), scale=S_JAM,   col=TIME_C, origin=self._RA)
        self._weather_txt = _txt('^ Cerah',       pos=(X_R, r1), scale=S_KECIL, col=color.rgb(255, 240, 130), origin=self._RA)
        self._date_txt    = _txt('Hari 1 | Semi', pos=(X_R, r1), scale=S_KECIL, col=color.rgb(180, 205, 255), origin=self._RA)
        self._gold_txt    = _txt('§ 0G',          pos=(X_R, r2), scale=S_KECIL, col=GOLD_C, origin=self._RA)
        self._scene_txt   = _txt('> Kebun',       pos=(X_R, r2), scale=S_KECIL, col=color.rgb(150, 250, 170), origin=self._RA)

        # ── Kiri Atas: nama alat + dua bilah stamina TIPIS ──
        # Patokan menaruh satu bilah setebal 16 px menempel di sudut. Dua
        # bilah kita 14 px, bertumpuk, dengan angkanya di ujung kanan bilah —
        # bukan di ATAS bilah, tempat angka "100/100" dulu tertimpa dan
        # terbaca separuh.
        S_ALAT   = 0.74
        S_ANGKA  = 0.52
        h_alat   = _tinggi(S_ALAT)
        LA       = (-0.5, 0.0)          # rata kiri, jangkar tengah menegak
        self._LA = LA

        y_alat = Y_T - h_alat / 2
        self._tool_name = _txt('Cangkul', pos=(X_L, y_alat), scale=S_ALAT,
                               col=color.rgb(255, 240, 100), origin=LA)
        self._seed_txt  = _txt('', pos=(X_L, y_alat), scale=S_ANGKA + 0.06,
                               col=color.rgb(155, 255, 155), origin=LA)

        self._BAR_W      = 0.235
        self._BAR_H      = 0.013
        self._BAR_X_LEFT = X_L
        BH = self._BAR_H

        hy = y_alat - h_alat / 2 - 0.005 - BH / 2
        ey = hy - BH - 0.005
        self._hy, self._ey = hy, ey

        # Alas bilah: tanpa ini bilah yang menyusut jadi tidak terbaca sebagai
        # "sisa dari sekian", cuma sebagai garis pendek yang berubah panjang.
        trek = color.rgb(18, 26, 30, 200)
        self._hp_trek = _ui(scale=(self._BAR_W, BH), z=0.06,
                            position=(X_L + self._BAR_W / 2, hy), color=trek)
        self._en_trek = _ui(scale=(self._BAR_W, BH), z=0.06,
                            position=(X_L + self._BAR_W / 2, ey), color=trek)
        self._hp_bar = _ui(scale=(self._BAR_W, BH), z=0.03,
                           position=(X_L + self._BAR_W / 2, hy),
                           color=color.rgb(55, 210, 80))
        self._en_bar = _ui(scale=(self._BAR_W, BH), z=0.03,
                           position=(X_L + self._BAR_W / 2, ey),
                           color=color.rgb(55, 205, 75))
        self._hp_val = _txt('HP', pos=(X_L + self._BAR_W + 0.010, hy),
                            scale=S_ANGKA, col=color.rgb(230, 240, 245), origin=LA)
        self._en_val = _txt('EN', pos=(X_L + self._BAR_W + 0.010, ey),
                            scale=S_ANGKA, col=color.rgb(230, 240, 245), origin=LA)

        # Buff dan antrian aksi: dua baris yang HAMPIR SELALU kosong, jadi
        # ongkos layarnya nol kecuali saat memang ada yang perlu dibaca.
        self._buff_txt  = _txt('', pos=(X_L, ey - BH / 2 - 0.005 - h_kecil / 2),
                               scale=S_KECIL, col=color.rgb(120, 255, 180), origin=LA)
        self._queue_txt = _txt('', pos=(X_L, ey - BH / 2 - 0.007 - h_kecil * 1.5),
                               scale=S_KECIL, col=color.rgb(255, 210, 80), origin=LA)

        # ── Kiri Bawah: ringkasan motif, menempel di SUDUT ──
        # Delapan motif ditumpuk vertikal dengan Suasana di puncaknya. Tanpa
        # ini seluruh mesin motif tidak terlihat oleh pemain, dan need yang
        # tak terlihat sama saja dengan tidak ada.
        #
        # Yang berubah cuma ukuran dan jangkarnya: lebar bilah 0.20 -> 0.10,
        # jarak baris 0.038 -> 0.0195, judul satu baris sendiri dilebur jadi
        # label kolom, dan blok yang tadinya mengambang 60 px dari tepi kiri
        # dan berhenti 100 px di atas dasar sekarang duduk di sudut. Tinggi
        # blok 400 px -> 195 px.
        from .motives import MOTIVES, LABELS
        self._motive_keys = MOTIVES
        S_MOTIF        = 0.50
        self._NBAR_W   = 0.100
        self._NBAR_H   = 0.013
        self._NROW     = 0.0195
        NBH            = self._NBAR_H

        n = len(self._motive_keys)
        y_need0 = Y_B + NBH / 2 + 0.002          # motif terakhir, paling bawah
        y_mood  = y_need0 + (n - 1) * self._NROW + 0.026
        MOOD_H  = 0.016

        # Label dibuat DULU, lalu kolomnya diukur dari label terpanjang.
        # Lebar kolom yang ditebak (0.098) membuat 'Kamar Kecil' menabrak
        # bilahnya sendiri di tangkapan pertama; angka tebakan tidak tahu
        # font apa yang benar-benar dimuat, `getTightBounds` tahu.
        self._mood_lbl = _txt('Suasana', pos=(X_L, y_mood), scale=S_MOTIF,
                              col=color.rgb(240, 224, 176), origin=LA, z=-0.02)
        self._need_lbl_ents = [
            _txt(LABELS[key], pos=(X_L, y_need0 + (n - 1 - i) * self._NROW),
                 scale=S_MOTIF, col=color.rgb(214, 224, 230), origin=LA, z=-0.02)
            for i, key in enumerate(self._motive_keys)]
        w_lbl = max([self._lebar(e)
                     for e in [self._mood_lbl] + self._need_lbl_ents] + [0.06])
        self._NLBL_W = min(w_lbl, 0.16) + 0.010
        self._NBAR_X = X_L + self._NLBL_W

        # Alas panel: tipis, bukan kotak 93% opak lagi. Tugasnya cuma menjamin
        # label putih tetap terbaca di atas lantai terang; selebihnya biar
        # dunia yang kelihatan.
        PAD       = 0.007
        panel_top = y_mood + MOOD_H / 2 + PAD
        panel_bot = y_need0 - NBH / 2 - PAD
        panel_w   = self._NLBL_W + self._NBAR_W + PAD * 2
        # z eksplisit, dan ini bukan hiasan.
        #
        # Semua elemen camera.ui duduk di z=0, jadi Panda menyortir bin
        # transparannya tanpa urutan yang bisa diandalkan — dan yang menang
        # ternyata latar panelnya. Termometernya SELALU ada, cuma dilihat
        # menembus kotak gelap 93% opak: fill hijau rgb(120,200,130) terukur
        # jadi rgb(19,33,31) di layar, persis 0.926*latar + 0.074*fill. Itu
        # sebabnya panel motif terbaca mati sejak awal. Yang di belakang diberi
        # z lebih besar, yang di depan lebih kecil.
        self._motive_panel_bg = _ui(
            scale=(panel_w, panel_top - panel_bot),
            position=(X_L - PAD + panel_w / 2, (panel_top + panel_bot) / 2),
            z=0.10,
            color=color.rgb(12, 20, 24, 128))

        self._mood_bg = _ui(scale=(self._NBAR_W, MOOD_H), z=0.06,
                            position=(self._NBAR_X + self._NBAR_W / 2, y_mood),
                            color=color.rgb(28, 34, 40, 210))
        self._mood_fill = _ui(scale=(self._NBAR_W, MOOD_H), z=0.03,
                              position=(self._NBAR_X + self._NBAR_W / 2, y_mood),
                              color=color.rgb(120, 210, 140))

        self._need_bg_ents   = []
        self._need_fill_ents = []
        for i, key in enumerate(self._motive_keys):
            y = y_need0 + (n - 1 - i) * self._NROW
            self._need_bg_ents.append(
                _ui(scale=(self._NBAR_W, NBH), z=0.06,
                    position=(self._NBAR_X + self._NBAR_W / 2, y),
                    color=color.rgb(28, 34, 40, 200)))
            self._need_fill_ents.append(
                _ui(scale=(self._NBAR_W, NBH), z=0.03,
                    position=(self._NBAR_X + self._NBAR_W / 2, y),
                    color=color.rgb(120, 200, 130)))
        self._motif_tampil = True

        # ── Flash message tengah ───────────────────────────────
        self._flash_ent = _txt('', pos=(0, 0.108), scale=1.1,
                               col=color.rgb(255, 245, 80), origin=(0, 0))
        self._flash_ent.enabled = False

        # ── Scrim: jaminan kontras untuk teks HUD ──────────────
        #
        # Teks HUD putih tanpa apa pun di belakangnya menghilang total di atas
        # latar terang. Terukur di scene farm jam 10: kotak jam berisi 2.528
        # piksel dan 95% di antaranya nyaris putih — teksnya ADA, warnanya
        # benar, dan tidak satu pun huruf bisa dibaca karena bangunan di
        # belakangnya sama putihnya.
        #
        # Bukan diperbaiki dengan mengganti warna teks: latar dunia berubah
        # sepanjang hari dan antar-scene, jadi warna teks apa pun akan kalah di
        # suatu tempat. Yang dijamin harus latarnya sendiri.
        #
        # Yang berubah sekarang: ukurannya tidak lagi dipatok. Scrim kiri dulu
        # 0.30 x 0.27 dan scrim bawah SELEBAR LAYAR, keduanya dipilih supaya
        # muat untuk teks terpanjang yang mungkin. Sekarang ketiganya dipas
        # ulang ke isinya di `_pas_scrim`, jadi alasnya persis sebesar yang
        # dibutuhkan dan tidak sepiksel pun lebih.
        #
        # z lebih besar = di belakang. Pelajaran yang sudah dibayar sekali di
        # panel motif: semua elemen camera.ui duduk di z=0 dan Panda menyortir
        # bin transparannya tanpa urutan yang bisa diandalkan.
        SCRIM_C = color.rgb(10, 16, 20, 112)
        self._scrim_kanan = _ui(scale=(0.001, 0.001), z=0.20,
                                position=(X_R, r1), color=SCRIM_C)
        self._scrim_kiri  = _ui(scale=(0.001, 0.001), z=0.20,
                                position=(X_L, y_alat), color=SCRIM_C)
        self._scrim_bawah = _ui(scale=(0.001, 0.001), z=0.20,
                                position=(X_R, Y_B), color=SCRIM_C)

        # ── Bawah Kanan: petunjuk tombol ──────────────────────
        # Dipusatkan di 0.60 berarti separuh barisnya tumbuh melewati tepi
        # 0.889 dan "[I] Inv" hilang. Dijangkar di sudut kanan-bawah
        # (origin 0.5, -0.5), jadi seberapa pun panjang prompt aksinya,
        # ekornya tetap di dalam layar dan alasnya ikut mengecil.
        self._control_hint = _txt(
            '', pos=(X_R, Y_B), scale=0.60,
            col=color.rgb(225, 238, 255), origin=(0.5, -0.5)
        )

        # Kotak yang dijangkar ke tepi KIRI, disimpan bersama JARAKNYA ke
        # tepi — bukan cuma daftar entity yang nanti digeser `+= dx`.
        #
        # Alasannya terukur: `position=` di konstruktor Entity meleset
        # setengah dari perubahan aspek yang terjadi SESUDAHNYA (0.0088 satuan
        # ui saat aspek pindah 1.81 -> 1.778), dan menggeser relatif dari
        # angka yang sudah meleset cuma menambah melesetnya — nama alat
        # berakhir 17 px dari tempatnya sementara bilah di bawahnya benar,
        # karena bilah memang ditulis ulang dari `_BAR_X_LEFT` tiap frame.
        # Menyimpan jaraknya membuat tiap penataan ulang mutlak, bukan
        # bertumpuk.
        bar_off = self._BAR_W / 2
        need_off = self._NLBL_W + self._NBAR_W / 2
        self._geser_kotak = [
            (self._hp_trek, bar_off), (self._en_trek, bar_off),
            (self._motive_panel_bg, -PAD + panel_w / 2),
            (self._mood_bg, need_off),
        ] + [(e, need_off) for e in self._need_bg_ents]

        # Teks tidak dijangkar lewat angka sama sekali; letaknya diukur dari
        # TINTA-nya di `_tata_ulang_hud`.
        self._teks_kiri = [
            self._tool_name, self._hp_val, self._en_val,
            self._buff_txt, self._queue_txt, self._mood_lbl,
        ] + self._need_lbl_ents

    # ── Tata letak yang dihitung ulang saat teksnya berubah ──────────
    #
    # Dihitung ulang HANYA saat teks berubah, bukan tiap frame: `Text.width`
    # membuat TextNode baru dan mengukur ulang fontnya tiap kali dipanggil,
    # dan ada tujuh teks yang perlu diukur. Frame rate di proyek ini sudah
    # 18-64 ms/frame; mengukur font 420 kali sedetik untuk hasil yang sama
    # persis adalah ongkos yang tidak dibayar siapa pun.

    @staticmethod
    def _lebar(e):
        """Lebar teks yang BENAR-BENAR tergambar, di ruang camera.ui.

        Bukan `Text.width * scale_x`. Rumus itu mengukur ulang fontnya lewat
        TextNode sementara dan hasilnya meleset ~10% ke bawah dari yang
        tergambar — terlihat langsung di tangkapan pertama sebagai
        'Cangkul[1-8] pilih alat' yang menempel tanpa jarak, padahal jaraknya
        diberi 15 px. `getTightBounds` membaca simpul yang sama dengan yang
        dirender, jadi tidak bisa meleset dari apa yang dilihat pemain.
        """
        try:
            if not str(e.text).strip():
                return 0.0
        except Exception:
            pass
        try:
            tb = e.getTightBounds(camera.ui)
            if tb is not None:
                return float(tb[1].x - tb[0].x)
        except Exception:
            pass
        try:
            return e.width * e.scale_x
        except Exception:
            return 0.0

    def _pas_scrim(self, scrim, kiri, kanan, atas, bawah, pad=0.008):
        if kanan <= kiri or atas <= bawah:
            scrim.enabled = False
            return
        scrim.enabled = True
        w = (kanan - kiri) + pad * 2
        h = (atas - bawah) + pad * 2
        scrim.scale = (w, h)
        scrim.position = ((kiri + kanan) / 2, (atas + bawah) / 2)

    def _pasang_tepi(self):
        """Ikuti tepi layar yang SEKARANG, bukan yang saat HUD dibangun.

        `window.aspect_ratio` masih berubah SESUDAH UIManager dibangun —
        tools/capture.py mencatatnya sendiri: 'changed aspect ratio: 1.81 ->
        1.778'. HUD yang dijangkar ke angka lama meleset 0.016 satuan ui,
        dan itu 17 px: jam kanan-atas terpotong di sisi kanan sementara nama
        alat menggantung 3 px di luar sisi kiri. Terlihat di tangkapan
        pertama sesudah perubahan ini, bukan diduga-duga.

        Mengembalikan True kalau tepinya bergeser, supaya pemanggilnya tahu
        harus menata ulang.
        """
        ex = window.aspect_ratio / 2
        if abs(ex - self._edge_x) < 1e-6:
            return False
        x_l = -ex + self._M
        dx = x_l - self._X_L
        self._edge_x = ex
        self._X_L = x_l
        self._X_R = ex - self._M
        self._BAR_X_LEFT = x_l
        self._NBAR_X = x_l + self._NLBL_W
        for e in getattr(self, '_jangkar_kiri', ()):
            try:
                e.x += dx
            except Exception:
                pass
        self._control_hint.x = self._X_R
        return True

    def _tata_ulang_hud(self):
        """Susun ulang baris kanan-atas, kiri-atas, dan alas gelapnya."""
        X_L, X_R = self._X_L, self._X_R
        Y_T, Y_B = self._Y_T, self._Y_B
        G = self._GAP

        # Kanan atas, baris 1: jam paling kanan, lalu cuaca, lalu tanggal.
        x = X_R
        for e in (self._time_txt, self._weather_txt, self._date_txt):
            e.x = x
            if str(e.text).strip():
                x -= self._lebar(e) + G
        kiri1 = x + G if x < X_R else X_R

        # Kanan atas, baris 2: emas paling kanan, lalu nama scene.
        x = X_R
        for e in (self._gold_txt, self._scene_txt):
            e.x = x
            if str(e.text).strip():
                x -= self._lebar(e) + G
        kiri2 = x + G if x < X_R else X_R

        h1 = self._time_txt.height * self._time_txt.scale_y
        h2 = self._gold_txt.height * self._gold_txt.scale_y
        self._pas_scrim(self._scrim_kanan, min(kiri1, kiri2), X_R,
                        Y_T, self._ROW2_Y - h2 / 2, pad=0.008)

        # Kiri atas: hint benih menempel di kanan nama alat.
        w_alat = self._lebar(self._tool_name)
        self._seed_txt.x = X_L + w_alat + G
        kanan = max(
            X_L + w_alat,
            self._seed_txt.x + self._lebar(self._seed_txt),
            self._BAR_X_LEFT + self._BAR_W + 0.010 + self._lebar(self._hp_val),
            self._BAR_X_LEFT + self._BAR_W + 0.010 + self._lebar(self._en_val),
        )
        bawah = self._ey - self._BAR_H / 2
        for e in (self._buff_txt, self._queue_txt):
            if str(e.text).strip():
                kanan = max(kanan, X_L + self._lebar(e))
                bawah = min(bawah, e.y - (e.height * e.scale_y) / 2)
        self._pas_scrim(self._scrim_kiri, X_L, kanan, Y_T, bawah, pad=0.008)

        # Kanan bawah: alas dipas ke petunjuk tombol, bukan selebar layar.
        ch = self._control_hint
        if str(ch.text).strip():
            self._pas_scrim(self._scrim_bawah,
                            X_R - self._lebar(ch), X_R,
                            Y_B + ch.height * ch.scale_y, Y_B, pad=0.007)
        else:
            self._scrim_bawah.enabled = False

    def toggle_motive_panel(self):
        """TAB: sembunyikan/tampilkan ringkasan motif di sudut kiri-bawah.

        Delapan motif adalah informasi yang berguna, tapi ia juga satu-satunya
        blok HUD yang tetap memakan tempat walau pemain sudah hafal isinya.
        Disembunyikan, bukan dibuang.
        """
        self._motif_tampil = not getattr(self, '_motif_tampil', True)
        v = self._motif_tampil
        for e in (self._motive_panel_bg, self._mood_lbl,
                  self._mood_bg, self._mood_fill):
            if e is not None:
                e.enabled = v
        for nama in self._DAFTAR_HUD:
            for e in getattr(self, nama, None) or []:
                e.enabled = v
        return v

    # Warna termometer: hijau aman, kuning waspada, merah mendesak. Pemain harus
    # bisa membaca "yang mana yang gawat" tanpa membaca satu kata pun.
    _MOTIVE_OK   = (108, 196, 128)
    _MOTIVE_WARN = (226, 178,  70)
    _MOTIVE_CRIT = (214,  86,  92)

    @staticmethod
    def _motive_color(v: float):
        """v dalam skala motif -100..+100."""
        if v <= -40:
            return color.rgb(*UIManager._MOTIVE_CRIT)
        if v <= 10:
            return color.rgb(*UIManager._MOTIVE_WARN)
        return color.rgb(*UIManager._MOTIVE_OK)

    def _update_action_readout(self):
        """Tampilkan aksi yang sedang dijalankan + sisa antrian.

        Tanpa ini pemain menekan E lalu tidak melihat apa pun terjadi selama
        beberapa puluh detik-sim, dan menyimpulkan tombolnya rusak.
        """
        txt = getattr(self, '_queue_txt', None)
        if txt is None:
            return
        q = getattr(getattr(self, 'player', None), 'queue', None)
        if q is None or not q.busy:
            txt.text = ''
            return
        cur = q.current
        bar_n = 10
        filled = int(round(cur.progress * bar_n))
        bar = '#' * filled + '.' * (bar_n - filled)
        sisa = len(q.items) - 1
        ekor = f'  (+{sisa} antri)' if sisa > 0 else ''
        txt.text = f'{cur.name}  [{bar}] {int(cur.progress*100)}%{ekor}'

    def _update_motive_panel(self):
        """Isi termometer dari mesin motif. Bar diisi dari kiri; skala -100..+100
        dipetakan ke 0..1 sehingga bar setengah berarti motif netral."""
        if not self._need_fill_ents:
            return
        eng = self.state.mv
        for i, key in enumerate(self._motive_keys):
            v = eng.get(key)
            frac = max(0.0, min(1.0, (v + 100.0) / 200.0))
            fill = self._need_fill_ents[i]
            fill.scale_x = max(0.001, self._NBAR_W * frac)
            fill.x = self._NBAR_X + fill.scale_x / 2
            fill.color = self._motive_color(v)
        m = eng.mood
        frac = max(0.0, min(1.0, (m + 100.0) / 200.0))
        self._mood_fill.scale_x = max(0.001, self._NBAR_W * frac)
        self._mood_fill.x = self._NBAR_X + self._mood_fill.scale_x / 2
        self._mood_fill.color = self._motive_color(m)

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

        # Active tool name
        self._tool_name.text = self._TOOL_NAMES[min(s.tool_index, len(self._TOOL_NAMES) - 1)]

        # Seed hint (shown when Tanam/Panen active)
        if s.tool_index in (2, 3):
            seed_name = CROPS.get(s.seed_key, {}).get('name', s.seed_key)
            seed_qty  = s.inventory.get(s.seed_key + '_seed', 0)
            self._seed_txt.text = f'Q/R: {seed_name} x{seed_qty}'
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
        
        # Petunjuk tombol: dua baris pendek di sudut kanan-bawah, bukan satu
        # baris sepanjang layar. Origin (0.5, -0.5) membuat TIAP baris rata
        # kanan sendiri-sendiri, jadi dua baris yang panjangnya beda tetap
        # rapi menempel di tepi.
        if hasattr(s, 'action_prompt'):
            self._control_hint.text = s.action_prompt
        else:
            self._control_hint.text = (
                '[WASD] Jalan  ·  [SPACE] Pakai  ·  [E] Aksi\n'
                '[I] Tas  ·  [J] Jurnal  ·  [TAB] Motif  ·  [F1] Panduan')

        # Susun ulang hanya kalau ada teks yang benar-benar berubah.
        tanda = (self._time_txt.text, self._date_txt.text,
                 self._weather_txt.text, self._scene_txt.text,
                 self._gold_txt.text, self._tool_name.text,
                 self._seed_txt.text, self._hp_val.text, self._en_val.text,
                 self._buff_txt.text, self._queue_txt.text,
                 self._control_hint.text)
        geser = self._pasang_tepi()
        if geser or tanda != getattr(self, '_tanda_hud', None):
            self._tanda_hud = tanda
            self._tata_ulang_hud()

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
            self.player._check_quest_progress(self)

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

    # Entity yang membentuk HUD permainan. Didaftar sekali di sini supaya
    # menyembunyikannya tidak perlu menebak-nebak isi camera.ui — dan supaya
    # menambah elemen HUD baru cuma butuh satu nama di daftar ini.
    _NAMA_HUD = (
        '_tool_name', '_seed_txt', '_hp_bar', '_hp_val', '_en_bar', '_en_val',
        '_hp_trek', '_en_trek',
        '_time_txt', '_date_txt', '_weather_txt', '_scene_txt', '_gold_txt',
        '_buff_txt', '_queue_txt', '_mood_bg', '_mood_fill', '_mood_lbl',
        '_motive_panel_bg',
    )
    _DAFTAR_HUD = ('_need_bg_ents', '_need_fill_ents', '_need_lbl_ents')

    def set_hud_visible(self, v: bool):
        """Sembunyikan/tampilkan seluruh HUD permainan.

        Dibuat untuk sinema: adegan bercerita yang masih menampilkan bar
        energi dan panel suasana hati tidak terbaca sebagai adegan, ia
        terbaca sebagai permainan yang macet dengan pita hitam di atasnya.
        Terlihat jelas di tangkapan pertama — panel SUASANA HATI menabrak
        baris narasinya sendiri.
        """
        for nama in self._NAMA_HUD:
            e = getattr(self, nama, None)
            if e is not None:
                try:
                    e.enabled = v
                except Exception:
                    pass
        for nama in self._DAFTAR_HUD:
            for e in getattr(self, nama, None) or []:
                try:
                    e.enabled = v
                except Exception:
                    pass
        # Scrim kontras ikut: tanpa ini pita hitamnya bertumpuk dengan
        # gradien gelap HUD dan tepinya terlihat sebagai dua lapis abu.
        for nama in ('_scrim_kanan', '_scrim_kiri', '_scrim_bawah'):
            e = getattr(self, nama, None)
            if e is not None:
                try:
                    e.enabled = v
                except Exception:
                    pass
        # Pilihan pemain menang atas "tampilkan lagi": kalau ringkasan motif
        # sengaja disembunyikan lewat TAB, keluar dari sinema tidak boleh
        # diam-diam menyalakannya kembali.
        if v and not getattr(self, '_motif_tampil', True):
            self._motif_tampil = True       # toggle akan membalikkannya
            self.toggle_motive_panel()

    def _set_panel_visible(self, v: bool):
        for e in (self._panel_bg, self._panel_title,
                  self._panel_body, self._panel_hint):
            e.enabled = v

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
            'shop':      'Warung Bu Sari',
            'olahan':    'Dapur - Olah Hasil Panen',
            'crafting':  'Bengkel Pak Budi',
            'help':      'Panduan Kontrol',
            'catatan':   'Catatan Lembah',
        }
        self._panel_title.text = titles.get(name, name.capitalize())
        # Update hint sesuai panel
        if name == 'shop':
            self._panel_hint.text = ('[TAB atau 0: ganti BELI/JUAL]   [1-9: pilih baris]'
                                     '   [Q/R: halaman]   [ESC: Tutup]')
        elif name == 'olahan':
            self._panel_hint.text = '[1-9: Olah]   [Q/R: halaman]   [ESC: Tutup]'
        elif name == 'crafting':
            self._panel_hint.text = '[1-5: Pickaxe]   [6-9: Pedang]   [ESC: Tutup]'
        else:
            self._panel_hint.text = '[ESC: tutup]'

        if name == 'inventory':
            # Tas dulu mencetak kunci dict mentah tanpa harga ('lobak_seed: 3').
            # Angka yang tidak bisa ditemukan pemain tidak mengajarkan apa-apa,
            # jadi tiap baris kini membawa nama layak baca, harga satuan, nilai
            # total, dan - hanya kalau mengolahnya memang lebih untung - ke mana
            # barang itu sebaiknya pergi.
            from .economy import (item_name, sell_price, best_process_hint,
                                  inventory_value)
            lines = [f"Emas: {s.gold}G   HP: {s.hp}/{s.max_hp}   Energi: {s.energy}/{s.max_energy}",
                     f"Pickaxe: Tier {s.pickaxe_tier}   Pedang: {s.sword_id or 'Tidak punya'}", '']
            rows = [(k, q) for k, q in s.inventory.items() if q > 0]
            if rows:
                # Paling berharga di atas: itu yang sedang dipikirkan pemain.
                rows.sort(key=lambda r: (-sell_price(r[0]) * r[1], r[0]))
                lines.append(f"  {'BARANG':<18}{'JML':>4}{'@':>7}{'TOTAL':>8}   SARAN")
                for item, qty in rows[:19]:
                    harga = sell_price(item)
                    hrg_s = f"{harga}G" if harga else "-"
                    tot_s = f"{harga * qty}G" if harga else "-"
                    lines.append(f"  {item_name(item)[:18]:<18}{qty:>4}{hrg_s:>7}"
                                 f"{tot_s:>8}   {best_process_hint(item)}")
                lines.append('')
                lines.append("  Nilai seluruh tas bila dijual di Warung: "
                             f"{inventory_value(s.inventory)}G")
                lines.append("  Peti Kirim di kebun membayar 85% tanpa perlu jalan.")
            else:
                lines.append("  (Kosong)")
            self._panel_body.text = '\n'.join(lines[:28])

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
            # Warung sekarang punya dua sisi. Sebelumnya hanya BELI ada, jadi
            # setiap barang yang dikumpulkan pemain tidak punya jalan keluar
            # dan harganya tidak pernah terlihat di mana pun.
            lines = self._render_market(s)
            self._set_body(lines)

        elif name == 'olahan':
            lines = self._render_olahan(s)
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
                "── AKSI ──\n"
                "  SPACE  : Pakai alat aktif\n"
                "  E      : Pie Menu interaksi NPC\n"
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
                "  Q/R    : Ganti bibit\n\n"
                "── MENU ──\n"
                "  I: Inventori   M: Peta\n"
                "  J: Quest       H: Relasi NPC\n"
                "  N: Catatan Lembah (lore)\n"
                "  K: Warung, beli & JUAL (di Warung)\n"
                "  O: Dapur, olah hasil panen (di Rumah)\n"
                "  Peti Kirim di kebun: jual cepat 85% harga\n"
                "  U: Kerajinan (di Bengkel)\n"
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

    def _set_body(self, lines):
        self._panel_body.text = chr(10).join(lines)

    @staticmethod
    def _season_name(s):
        try:
            from .config import SEASON_NAMES
            return SEASON_NAMES[s.season_index]
        except Exception:
            return '-'

    # ─── PASAR: BELI / JUAL ──────────────────────────────
    # Sembilan baris per halaman karena input panel hanya menerima angka 1-9.
    ROWS_PER_PAGE = 9

    def _market_state(self):
        """(mode, halaman). Hidup di UIManager, bukan di save — ini keadaan
        layar, bukan keadaan dunia."""
        if not hasattr(self, '_market_mode'):
            self._market_mode = 'beli'
            self._market_page = 0
        return self._market_mode, self._market_page

    def cycle_market_mode(self):
        mode, _ = self._market_state()
        self._market_mode = 'jual' if mode == 'beli' else 'beli'
        self._market_page = 0
        self._render_panel(self._panel_name or 'shop')

    def market_page(self, delta: int):
        self._market_state()
        self._market_page = max(0, self._market_page + delta)
        self._render_panel(self._panel_name or 'shop')

    def _page_slice(self, rows):
        self._market_state()
        n_pages = max(1, -(-len(rows) // self.ROWS_PER_PAGE))
        self._market_page = min(self._market_page, n_pages - 1)
        start = self._market_page * self.ROWS_PER_PAGE
        return rows[start:start + self.ROWS_PER_PAGE], self._market_page, n_pages

    def _render_market(self, s) -> list:
        from .economy import (margin_hint, sellable_items, sell_price,
                              item_name, inventory_value)
        mode, _ = self._market_state()
        tab = ('>> BELI <<      jual' if mode == 'beli'
               else '   beli      >> JUAL <<')
        lines = [f"Emas: {s.gold}G   Musim: {self._season_name(s)}   "
                 f"Nilai tas: {inventory_value(s.inventory)}G",
                 tab, '']

        if mode == 'beli':
            rows, page, n_pages = self._page_slice(list(SHOP_ITEMS))
            lines.append(f"  {'BARANG':<20}{'HARGA':>6}  {'MUSIM':<11} HASILNYA NANTI")
            for i, it in enumerate(rows):
                mampu = '' if s.gold >= it['price'] else '  (gold kurang)'
                # Ternak yang sudah dibeli tetap terdaftar tapi ditandai, bukan
                # dihilangkan: daftar yang barisnya berpindah-pindah tiap kali
                # membeli membuat nomor pilihannya tidak bisa dihafal.
                if it.get('animal') in getattr(s, 'owned_animals', []):
                    mampu = '  (sudah di kandang)'
                lines.append(f"  [{i+1}] {it['name'][:16]:<16}{it['price']:>5}G  "
                             f"{it['season']:<11} {margin_hint(it)}{mampu}")
            lines.append('')
            lines.append("  Angka = beli 1. Kolom kanan memberi tahu berapa hasil")
            lines.append("  panennya nanti, jadi untung-ruginya terlihat sebelum bayar.")
        else:
            all_rows = sellable_items(s.inventory)
            if not all_rows:
                lines.append("  Tidak ada yang bisa dijual. Panen dulu, atau ambil")
                lines.append("  hasil ternak di kandang.")
                return lines
            rows, page, n_pages = self._page_slice(all_rows)
            lines.append(f"  {'BARANG':<20}{'JML':>4}{'@':>7}{'SEMUA':>8}")
            for i, (item, qty, total) in enumerate(rows):
                lines.append(f"  [{i+1}] {item_name(item)[:16]:<16}{qty:>4}"
                             f"{sell_price(item):>6}G{total:>7}G")
            lines.append('')
            lines.append("  Angka = jual SEMUA barang di baris itu, harga penuh.")
            lines.append("  Peti Kirim di kebun lebih cepat tapi hanya membayar 85%.")

        if n_pages > 1:
            lines.append(f"  -- halaman {page+1}/{n_pages}  [Q/R] --")
        return lines

    def _render_olahan(self, s) -> list:
        from .economy import (PROCESS_RECIPES, recipe_input_value,
                              recipe_output_value, recipe_uplift, item_name)
        lines = [f"Emas: {s.gold}G   Energi: {s.energy}/{s.max_energy}", '',
                 "Mengolah menambah sekitar 40% nilai, dibayar dengan energi.",
                 '']
        rows, page, n_pages = self._page_slice(list(PROCESS_RECIPES))
        lines.append(f"  {'HASIL':<20}{'DARI':<22}{'NILAI':>14}  EN")
        for i, r in enumerate(rows):
            bahan = ', '.join(f"{item_name(k)} x{v}" for k, v in r['needs'].items())
            punya = all(s.inventory.get(k, 0) >= v for k, v in r['needs'].items())
            cukup = s.energy >= r['en']
            mark  = '[o]' if (punya and cukup) else '[ ]'
            masuk = recipe_input_value(r)
            keluar = recipe_output_value(r)
            naik  = int(round((recipe_uplift(r) - 1) * 100))
            out_n = f"{item_name(r['out'])} x{r['n']}" if r['n'] > 1 else item_name(r['out'])
            lines.append(f"  [{i+1}]{mark} {out_n[:15]:<15}{bahan[:22]:<22}"
                         f"{masuk:>4}G > {keluar:>4}G +{naik}%{r['en']:>3}")
        lines.append('')
        lines.append("  [o] = bahan & energi cukup.  [ ] = belum bisa.")
        lines.append("  Pakan Ternak dinilai dari jerami yang tidak jadi dibeli")
        lines.append("  (18G/hari-pakan) — menjualnya rugi, memakainya untung.")
        if n_pages > 1:
            lines.append(f"  -- halaman {page+1}/{n_pages}  [Q/R] --")
        return lines

    # ─── PANEL ACTIONS (shop/craft) ──────────────────────
    def panel_action(self, idx: int) -> str:
        """Dipanggil dari app.input() saat user tekan angka di panel.
        idx 1-based. Return pesan untuk flash_msg."""
        if self._panel_name == 'shop':
            mode, _ = self._market_state()
            return (self._buy_shop_item(idx) if mode == 'beli'
                    else self._sell_stack(idx))
        elif self._panel_name == 'olahan':
            return self._process_item(idx)
        elif self._panel_name == 'crafting':
            return self._craft_item(idx)
        return ''

    def _buy_shop_item(self, idx: int) -> str:
        s = self.state
        rows, _page, _n = self._page_slice(list(SHOP_ITEMS))
        if not (1 <= idx <= len(rows)):
            return ''
        it = rows[idx - 1]
        if s.gold < it['price']:
            return f"Gold kurang ({it['price']}G)."

        # Ternak tidak masuk tas. Ia pindah ke kandang, dan itu satu-satunya
        # baris toko yang mengubah dunia alih-alih inventori.
        aid = it.get('animal')
        if aid:
            punya = getattr(s, 'owned_animals', None)
            if punya is None:
                punya = s.owned_animals = []
            if aid in punya:
                return f"{it['name']} sudah ada di kandangmu."
            s.gold -= it['price']
            punya.append(aid)
            if not s.shop_unlocked:
                s.shop_unlocked = True
            self._render_panel('shop')
            return (f"{it['name']} dibeli -{it['price']}G. "
                    f"Ia menunggu di kandang — beri makan hari ini.")

        s.gold -= it['price']
        s.inventory[it['id']] = s.inventory.get(it['id'], 0) + 1
        if not s.shop_unlocked:
            s.shop_unlocked = True
        self._render_panel('shop')   # refresh tampilan
        return f"Beli {it['name']} -{it['price']}G"

    def _sell_stack(self, idx: int) -> str:
        """Jual seluruh tumpukan di satu baris, harga penuh Warung.

        Per-tumpukan, bukan per-butir: pemain dengan 40 lobak tidak boleh harus
        menekan tombol 40 kali. Peti Kirim tetap ada untuk yang ingin menjual
        semuanya sekaligus dengan potongan.
        """
        from .economy import sellable_items, item_name
        s = self.state
        rows, _page, _n = self._page_slice(sellable_items(s.inventory))
        if not (1 <= idx <= len(rows)):
            return ''
        item, qty, total = rows[idx - 1]
        del s.inventory[item]
        s.gold += total
        s.stats['earned'] = s.stats.get('earned', 0) + total
        self._render_panel('shop')
        return f"Jual {item_name(item)} x{qty} +{total}G"

    def _process_item(self, idx: int) -> str:
        """Olah bahan mentah jadi barang lebih mahal, bayar dengan energi."""
        from .economy import (PROCESS_RECIPES, item_name, recipe_output_value,
                              recipe_input_value)
        s = self.state
        rows, _page, _n = self._page_slice(list(PROCESS_RECIPES))
        if not (1 <= idx <= len(rows)):
            return ''
        r = rows[idx - 1]
        for k, v in r['needs'].items():
            if s.inventory.get(k, 0) < v:
                return f"Bahan kurang: butuh {item_name(k)} x{v}."
        if s.energy < r['en']:
            return f"Energi kurang (butuh {r['en']})."
        for k, v in r['needs'].items():
            s.inventory[k] -= v
            if s.inventory[k] <= 0:
                del s.inventory[k]
        s.energy -= r['en']
        s.inventory[r['out']] = s.inventory.get(r['out'], 0) + r['n']
        s.stats['processed'] = s.stats.get('processed', 0) + 1
        self._render_panel('olahan')
        untung = recipe_output_value(r) - recipe_input_value(r)
        return (f"+{r['n']} {item_name(r['out'])} "
                f"(nilai naik {untung}G, -{r['en']} EN)")

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
        self._pie_bg     = _ui(scale=(0.45, 0.32), position=(-0.14, -0.10), color=BG)
        self._pie_border = _ui(scale=(0.452, 0.322), position=(-0.14, -0.10), color=BD)
        self._pie_title  = _txt('', pos=(-0.34, 0.040), scale=0.90,
                                col=color.rgb(245, 215, 80))
        self._pie_items  = [
            _txt('', pos=(-0.34, 0.010 - i * 0.030), scale=0.80, col=color.white)
            for i in range(6)
        ]
        self._pie_fx     = _txt('', pos=(-0.34, -0.200), scale=0.72,
                                col=color.rgb(127, 220, 255))
        self._pie_hint   = _txt('[</> ] Pilih  [SPACE] OK  [ESC] Batal',
                                pos=(-0.34, -0.240), scale=0.65,
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

    def _refresh_pie_ui(self):
        from .data import HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS
        all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
        # Menu perabot mengirim id 'obj:<Nama>' — pakai nama itu apa adanya,
        # jangan cari di daftar NPC (dulu judulnya tampil sebagai 'obj:12').
        if self._pie_npc_id.startswith('obj:'):
            self._pie_title.text = f">> {self._pie_npc_id[4:]}"
        else:
            npc = all_d.get(self._pie_npc_id, {})
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
