"""karsa_panel.py — Menyunting peta game dari dalam editor.

## Kenapa logikanya dipisah dari tombolnya

`SesiKarsa` memegang seluruh logika menyunting -- buka scene, pilih jenis ubin,
klik ubin, simpan -- dan TIDAK menyentuh satu pun widget. `PanelKarsa` baru
membungkusnya dengan tombol.

Alasannya bisa diuji: yang perlu dibuktikan bukan bahwa tombolnya enak dipakai
(itu perlu mata), melainkan bahwa membuka scene, mengubah ubin, lalu menyimpan
menghasilkan berkas yang benar. Pemisahan itu membuat bagian yang penting bisa
diperiksa offscreen oleh `gauntlet/check.py`, sementara bagian yang hanya bisa
dinilai mata tetap kecil dan jelas.

## Batas yang jujur

Editor ini memakai gizmo transform untuk memindahkan, memutar, dan menskalakan
entity bebas. Itu TIDAK berlaku untuk ubin: ubin menempati sel grid, jadi
"memindahkan" sebuah ubin berarti menulis ulang dua sel, bukan menggeser posisi.
Karena itu penyuntingan ubin di sini memakai **klik-untuk-mengecat**, bukan
gizmo. Objek bebas yang bisa digeser dengan gizmo adalah Fase 5.
"""
import sys
from pathlib import Path

_DIR_EDITOR = Path(__file__).resolve().parent
_ROOT_REPO = _DIR_EDITOR.parent
if str(_ROOT_REPO) not in sys.path:
    sys.path.insert(0, str(_ROOT_REPO))

from ursina import Button, Entity, Text, camera, color, destroy, mouse, window  # noqa: E402

from . import karsa_scene as ks      # noqa: E402
from . import karsa_tiles as kt      # noqa: E402


class SesiKarsa:
    """Logika menyunting satu scene game. Tanpa widget, tanpa ursina."""

    def __init__(self):
        self.scene = None
        self.layer = None
        self.layer_objek = None
        self.sumber = None          # 'data' atau 'kode'
        self.tid_aktif = None
        self.kind_aktif = None
        self.ubin_terakhir = None   # tempat "+ OBJEK" akan menaruh bendanya
        self.kotor = False

    # ─── Membuka & menutup ──────────────────────────────────────────────────
    def daftar(self) -> list:
        return ks.scene_tersedia()

    def buka(self, nama: str) -> dict:
        """Muat scene game ke viewport. Mengembalikan ringkasannya."""
        self.tutup()
        self.scene, self.sumber = ks.muat(nama)
        self.layer = kt.LayerUbin(self.scene)
        self.layer_objek = kt.LayerObjek(self.scene)
        self.kotor = False
        if self.tid_aktif is None:
            # Default yang berguna: ubin yang paling banyak dipakai peta ini.
            self.tid_aktif = max(
                {tid for baris in self.scene.tiles for tid in baris},
                key=lambda t: sum(b.count(t) for b in self.scene.tiles))
        if self.kind_aktif is None:
            from game.objects import OBJECT_KINDS
            self.kind_aktif = sorted(OBJECT_KINDS)[0]
        return ks.ringkas(self.scene)

    def tutup(self):
        for lapis in (self.layer, self.layer_objek):
            if lapis is not None:
                destroy(lapis.root)
        self.layer = None
        self.layer_objek = None
        self.scene = None
        self.sumber = None

    # ─── Menyunting ─────────────────────────────────────────────────────────
    def pilih_ubin(self, tid: int):
        self.tid_aktif = tid

    def pilih_kind(self, kind: str):
        self.kind_aktif = kind

    def klik(self, entity) -> bool:
        """Cat ubin yang diklik dengan ubin aktif.

        Mengembalikan False kalau yang diklik bukan ubin scene ini -- supaya
        pemanggil bisa membiarkan editor generik menangani entity bebasnya.
        """
        if self.layer is None or entity is None:
            return False
        koor = self.layer.koordinat(entity)
        if koor is None:
            return False
        # Diingat walau tidak jadi mengecat: "+ OBJEK" menaruh bendanya di
        # ubin terakhir yang disentuh, jadi pemain menunjuk tempat dulu.
        self.ubin_terakhir = koor
        if self.tid_aktif is None:
            return False
        if not self.layer.set(koor[0], koor[1], self.tid_aktif):
            return False
        self.kotor = True
        return True

    # ─── Objek terpasang ────────────────────────────────────────────────────
    def klik_objek(self, entity) -> bool:
        """True kalau entity ini objek terpasang milik scene yang terbuka.

        Tidak menyeleksi apa pun sendiri -- pemanggil yang tahu cara editor
        memilih entity (gizmo mengikuti `scene_manager.selected_entity`).
        """
        if self.layer_objek is None or entity is None:
            return False
        return self.layer_objek.index_dari(entity) is not None

    def tambah_objek(self, kind: str = None):
        """Taruh satu objek di ubin terakhir yang diklik.

        Menunjuk tempat dulu lalu menambah, bukan sebaliknya: benda yang
        muncul di tempat yang baru saja disentuh selalu bisa ditemukan, dan
        tidak perlu dialog untuk memilih koordinat.
        """
        if self.layer_objek is None:
            return None
        if self.ubin_terakhir is None:
            # Belum ada yang diklik: pakai tengah peta, bukan pojok, supaya
            # bendanya langsung terlihat kamera.
            self.ubin_terakhir = (self.scene.w // 2, self.scene.h // 2)
        ent = self.layer_objek.tambah(kind or self.kind_aktif,
                                      float(self.ubin_terakhir[0]),
                                      float(self.ubin_terakhir[1]))
        if ent is not None:
            self.kotor = True
        return ent

    def sinkron_objek(self, entity) -> bool:
        """Tulis balik posisi objek setelah gizmo menggesernya."""
        if self.layer_objek is None:
            return False
        if not self.layer_objek.sinkron(entity):
            return False
        self.kotor = True
        return True

    def hapus_objek(self, entity) -> bool:
        if self.layer_objek is None:
            return False
        if not self.layer_objek.hapus(entity):
            return False
        self.kotor = True
        return True

    def simpan(self):
        """Tulis scene kembali ke berkas data game.

        Menolak menyimpan JIKA tidak ada yang dibuka, dan mengembalikan path
        supaya pemanggil bisa memberi tahu pemakai di mana berkasnya mendarat.
        """
        if self.scene is None:
            raise RuntimeError('belum ada scene yang dibuka')
        p = ks.simpan(self.scene)
        self.kotor = False
        return p


class PanelKarsa:
    """Tombol-tombol untuk `SesiKarsa`: daftar scene, palet ubin, simpan.

    Sengaja sederhana dan berdiri sendiri di sisi kiri layar, bukan menumpang
    toolbar editor: tombol editor yang ada mengurus entity bebas, sedangkan
    panel ini mengurus grid ubin, dan mencampur keduanya di satu baris membuat
    dua model yang berbeda terlihat seperti satu.
    """

    LEBAR = 0.30

    def __init__(self, sesi: SesiKarsa = None, on_pesan=None, on_pilih=None):
        self.sesi = sesi or SesiKarsa()
        self.on_pesan = on_pesan or (lambda pesan, **kw: None)
        # Dipanggil saat sebuah objek diklik. Editor yang tahu cara memilih
        # entity (gizmo mengikuti `scene_manager.selected_entity`), bukan panel.
        self.on_pilih = on_pilih or (lambda ent: None)
        self.root = Entity(parent=camera.ui, enabled=False)
        self.tombol_scene = {}
        self.tombol_ubin = {}
        self.tombol_kind = {}
        self._bangun()

    def _bangun(self):
        self.latar = Entity(
            parent=self.root, model='quad', color=color.rgba(18, 22, 30, 235),
            scale=(self.LEBAR, 1.0), position=(-0.5 + self.LEBAR / 2, 0),
            z=0.1,
        )
        Text(parent=self.root, text='PETA KARSA', position=(-0.5 + 0.02, 0.46),
             scale=0.9, color=color.rgb(120, 210, 190), z=0.0)

        # Daftar scene game.
        y = 0.42
        for nama in self.sesi.daftar():
            b = Button(
                parent=self.root, text=nama, scale=(self.LEBAR - 0.04, 0.028),
                position=(-0.5 + self.LEBAR / 2, y), color=color.rgba(40, 48, 62, 230),
                highlight_color=color.rgba(70, 90, 110, 240),
            )
            b.on_click = (lambda n=nama: self._buka(n))
            self.tombol_scene[nama] = b
            y -= 0.030

        # Palet ubin game.
        self.label_palet = Text(
            parent=self.root, text='ubin aktif: -', position=(-0.5 + 0.02, y - 0.01),
            scale=0.8, color=color.rgb(220, 200, 140), z=0.0)
        y -= 0.035
        for kolom, (tid, nama, ada_tekstur) in enumerate(kt.palet()):
            bx = -0.5 + 0.02 + (kolom % 4) * ((self.LEBAR - 0.05) / 4)
            by = y - (kolom // 4) * 0.021
            b = Button(
                parent=self.root, text='' if ada_tekstur else '?',
                scale=((self.LEBAR - 0.06) / 4, 0.019), position=(bx, by),
                color=kt.warna_ubin(tid), highlight_color=color.white,
            )
            b.on_click = (lambda t=tid, n=nama: self._pilih(t, n))
            self.tombol_ubin[tid] = b

        # ── Objek terpasang ─────────────────────────────────────────────────
        # Palet terpisah dari palet ubin karena keduanya benda yang berbeda:
        # ubin MENEMPATI sel, objek BERDIRI di posisi bebas dan bisa digeser
        # gizmo. Mencampurnya di satu baris akan membuat perbedaan itu hilang.
        y = y - (51 // 4 + 1) * 0.021
        self.label_kind = Text(
            parent=self.root, text='objek aktif: -', position=(-0.5 + 0.02, y),
            scale=0.8, color=color.rgb(200, 170, 230), z=0.0)
        y -= 0.030
        from game.objects import OBJECT_KINDS
        for kolom, kind in enumerate(sorted(OBJECT_KINDS)):
            bx = -0.5 + 0.02 + (kolom % 5) * ((self.LEBAR - 0.05) / 5)
            by = y - (kolom // 5) * 0.021
            b = Button(
                parent=self.root, text=kind[:4],
                scale=((self.LEBAR - 0.06) / 5, 0.019), position=(bx, by),
                color=color.rgba(70, 55, 90, 235),
                highlight_color=color.rgba(110, 85, 140, 245),
            )
            b.on_click = (lambda k=kind: self._pilih_kind(k))
            self.tombol_kind[kind] = b
        y -= (len(OBJECT_KINDS) // 5 + 1) * 0.021

        self.btn_objek = Button(
            parent=self.root, text='+ OBJEK DI UBIN TERAKHIR',
            scale=(self.LEBAR - 0.04, 0.030), position=(-0.5 + self.LEBAR / 2, y),
            color=color.rgba(80, 60, 110, 235),
            highlight_color=color.rgba(120, 90, 160, 245),
        )
        self.btn_objek.on_click = self._tambah_objek
        y -= 0.036

        self.btn_simpan = Button(
            parent=self.root, text='SIMPAN PETA', scale=(self.LEBAR - 0.04, 0.032),
            position=(-0.5 + self.LEBAR / 2, y),
            color=color.rgba(45, 105, 80, 235),
            highlight_color=color.rgba(70, 150, 115, 245),
        )
        self.btn_simpan.on_click = self._simpan

    # ─── Aksi ───────────────────────────────────────────────────────────────
    def _buka(self, nama):
        try:
            ringkas = self.sesi.buka(nama)
        except Exception as e:
            self.on_pesan(f"Gagal membuka {nama}: {e}", bg_color=color.rgba(140, 45, 45, 230))
            return
        self.on_pesan(
            f"{nama}: {ringkas['ukuran'][0]}x{ringkas['ukuran'][1]}, "
            f"{ringkas['jenis_ubin']} jenis ubin, sumber {self.sesi.sumber}")

    def _pilih(self, tid, nama):
        self.sesi.pilih_ubin(tid)
        self.label_palet.text = f'ubin aktif: {nama}'

    def _pilih_kind(self, kind):
        self.sesi.pilih_kind(kind)
        self.label_kind.text = f'objek aktif: {kind}'

    def _tambah_objek(self):
        ent = self.sesi.tambah_objek()
        if ent is None:
            self.on_pesan("Buka scene dulu sebelum menambah objek.",
                          bg_color=color.rgba(140, 45, 45, 230))
            return
        # Langsung diseleksi supaya gizmo menempel padanya dan pemain bisa
        # menggesernya tanpa mencari dulu.
        self.on_pilih(ent)
        self.on_pesan(f"{self.sesi.kind_aktif} ditaruh di ubin "
                      f"{self.sesi.ubin_terakhir}. Geser dengan gizmo.")

    def _simpan(self):
        try:
            p = self.sesi.simpan()
        except Exception as e:
            self.on_pesan(f"Gagal menyimpan: {e}", bg_color=color.rgba(140, 45, 45, 230))
            return
        self.on_pesan(f"Tersimpan: {p.name}. "
                      f"Jalankan tools/scene_export.py --check untuk membandingkan dengan kode.")

    # ─── Kait ke editor ─────────────────────────────────────────────────────
    def toggle(self):
        self.root.enabled = not self.root.enabled
        return self.root.enabled

    def klik_viewport(self) -> bool:
        """Klik kiri di viewport.

        Objek terpasang diperiksa DULU: mengklik kursi harus memilihnya supaya
        gizmo menempel, bukan mengecat ubin di bawahnya. Handle gizmo bukan
        objek maupun ubin, jadi klik pada handle jatuh ke gizmo seperti biasa.
        """
        if not self.root.enabled:
            return False
        ent = getattr(mouse, 'hovered_entity', None)
        if self.sesi.klik_objek(ent):
            self.on_pilih(ent)
            return True
        return self.sesi.klik(ent)

    def hapus_terpilih(self, ent) -> bool:
        """Hapus objek terpasang yang sedang diseleksi gizmo."""
        if not self.sesi.klik_objek(ent):
            return False
        if self.sesi.hapus_objek(ent):
            self.on_pesan("Objek dihapus.")
            return True
        return False
