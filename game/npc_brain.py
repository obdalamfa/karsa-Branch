"""npc_brain.py — Lapisan AI tambahan untuk NPC Lembah Karsa 3D.

Menggabungkan:
  - BehaviorVM (motif + antrian aksi, adaptasi SimAntics FreeSO)
  - PathGrid   (A* tile-based, adaptasi VMRectRouter FreeSO)

Tidak menggantikan sistem pergerakan NPC berbasis schedule yang sudah ada
di EntitiesManager. Lapisan ini menambah motif (hunger, energy, social, ...)
yang berubah seiring waktu, dan mem-publish animasi hint yang bisa dibaca
oleh sistem visual jika diperlukan.

Pemakaian dari EntitiesManager:
    from .npc_brain import NPCBrains
    self.brains = NPCBrains(self.state)
    # tiap frame:
    self.brains.tick(dt)
"""
from __future__ import annotations
from typing import Dict, Optional

import random

from .behavior_vm import BehaviorVM, BehaviorEntity
from .pathfinder import PathGrid
from .data import HUMAN_NPCS, all_npcs
from .motives import Advert, Interaction, Motives, choose_action
from .objects import autonomy_candidates, object_name
from .scenes import SCENES
from .config import INGAME_MINUTES_PER_REAL_SECOND, WALKABLE


# Interaksi cadangan untuk NPC yang tidak punya perabot apa pun di dekatnya.
#
# Dibentuk sebagai `Interaction` sungguhan, bukan cabang kode terpisah, supaya
# jalur cadangan melewati durasi dan pembayaran yang SAMA dengan jalur dunia.
# Versi pertama menyambungkan otonomi tanpa ini, dan akibatnya terukur: NPC
# yang jauh dari perabot meluruh sampai -100 di setiap motif dan tidak punya
# jalan apa pun untuk pulih, karena daftar mati lama cuma menyentuh dict lima
# motif milik VM dan tidak pernah menyentuh mesin motif yang dipakai menilai.
#
# Dinilai dengan mesin yang SAMA seperti perabot sungguhan, bukan lewat daftar
# ambang. Daftar ambang lama memeriksa berurutan — lapar, lalu energi, lalu
# sosial — jadi begitu motif pertama di bawah ambangnya, dua sisanya tidak
# pernah sempat dipertimbangkan. Terukur: keempat warga di farm terkunci di
# energi -100 karena "makan" selalu menang lebih dulu, padahal "Istirahat"
# tersedia dan iklannya lolos gerbang. Sebagai kandidat berjarak nol, yang
# paling mendesak yang menang — tanpa satu pun aturan prioritas.
_CADANGAN = (
    ('makan',  Interaction('Makan Bekal', [Advert('lapar', 35, minimum=40)],
                           duration=45, attenuation=0.0)),
    ('tidur',  Interaction('Istirahat', [Advert('energi', 45, minimum=35),
                                         Advert('nyaman', 15)],
                           duration=180, attenuation=0.0)),
    ('bicara', Interaction('Mengobrol', [Advert('sosial', 30, minimum=45),
                                         Advert('senang', 10)],
                           duration=40, attenuation=0.0)),
)


class _PetaScene:
    """Pembaca tile scene aktif, cukup untuk `autonomy_candidates`.

    Fungsi itu hanya butuh `get_tile(x, y)`, dan EntitiesManager tidak memegang
    World3D. Daripada menarik World3D melewati tiga lapis hanya demi satu
    metode, dibaca langsung dari definisi scene — sumber yang sama dengan yang
    dipakai `_can_walk`, jadi tidak ada dua kebenaran soal apa yang ada di
    ubin mana.
    """

    __slots__ = ('scene_name', 'dungeon_tiles')

    def __init__(self, scene_name, dungeon_tiles=None):
        self.scene_name = scene_name
        self.dungeon_tiles = dungeon_tiles

    def get_tile(self, tx: int, ty: int) -> int:
        if self.scene_name == 'dungeon' and self.dungeon_tiles:
            grid = self.dungeon_tiles
        else:
            sc = SCENES.get(self.scene_name)
            grid = getattr(sc, 'tiles', None) if sc else None
        if not grid:
            return -1
        if ty < 0 or ty >= len(grid):
            return -1
        baris = grid[ty]
        if tx < 0 or tx >= len(baris):
            return -1
        return baris[tx]


# Decay motif per detik (kasar — 100 → 0 dalam ~16 menit real-time)
_MOTIVE_DECAY = {
    "hunger":  0.10,
    "energy":  0.06,
    "social":  0.08,
    "fun":     0.05,
    "hygiene": 0.04,
}


class NPCBrains:
    """Manajer otak NPC: satu BehaviorEntity per NPC manusia."""

    def __init__(self, state, grid_w: int = 32, grid_h: int = 32):
        self.state = state
        self.vm = BehaviorVM()
        self.grid = PathGrid(grid_w, grid_h, tile_size=1.0)
        self._brains: Dict[str, BehaviorEntity] = {}
        self._anim_hint: Dict[str, str] = {}
        self._grid_scene: Optional[str] = None

        # Mesin motif delapan-motif yang sama dengan milik pemain, satu per
        # NPC. BehaviorEntity punya dict lima-motif sendiri untuk VM-nya; yang
        # ini dipakai untuk MEMILIH, karena hanya bentuk ini yang dimengerti
        # `choose_action` dan katalog iklan di objects.py.
        self._motif: Dict[str, Motives] = {}
        self._rng = random.Random(20260828)   # deterministik: lihat _auto_queue
        self._pilihan: Dict[str, tuple] = {}  # npc_id -> (obj, interaksi)
        self._sisa: Dict[str, float] = {}     # npc_id -> menit-sim tersisa
        self.jml_selesai = 0                  # interaksi yang benar-benar tuntas
        self.peta = None                      # diisi rebuild_grid()
        self.jml_pilihan_dunia = 0            # dihitung untuk regresi

        for npc_id in HUMAN_NPCS.keys():
            ent = BehaviorEntity(npc_id, motives={
                "hunger":  80.0, "energy": 80.0, "social": 70.0,
                "fun":     60.0, "hygiene": 75.0,
            })
            ent.on_animation_change(lambda anim, _id=npc_id: self._on_anim(_id, anim))
            self.vm.add_entity(ent)
            self._brains[npc_id] = ent
            self._motif[npc_id] = Motives()

    def _on_anim(self, npc_id: str, anim_name: str):
        self._anim_hint[npc_id] = anim_name

    # ─── PUBLIC ──────────────────────────────────────────
    def _di_scene_aktif(self, npc_id: str) -> bool:
        """NPC ini sedang berada di scene yang dirender?

        Hanya satu scene hidup pada satu waktu. Meluruhkan motif NPC yang
        sedang berada di scene lain berarti ia meluruh tanpa pernah punya
        kesempatan pulih — perabot yang bisa menolongnya ada di scene yang
        tidak sedang disimulasikan. Terukur sebelum penjagaan ini: NPC yang
        jadwalnya menaruhnya di `town` jatuh ke -100 pada SEMUA motif sambil
        `house` dirender, dengan nol interaksi seumur hidupnya.
        """
        aktif = getattr(self.state, 'scene_name', None)
        pos = getattr(self.state, 'npc_positions', {}).get(npc_id)
        if aktif is None or not pos:
            return True     # tidak tahu = jangan diam-diam membekukan
        return pos.get('scene', aktif) == aktif

    def tick(self, dt: float):
        # Decay motif
        for npc_id, ent in self._brains.items():
            if not self._di_scene_aktif(npc_id):
                continue
            for key, rate in _MOTIVE_DECAY.items():
                ent.change_motive(key, -rate * dt)
            mv = self._motif.get(npc_id)
            # Mesin motif dan durasi interaksi dihitung dalam MENIT-SIM, dan
            # dt datang dalam DETIK-REAL. Konversinya bukan 1:1 — satu hari
            # dalam game = 900 detik real, jadi satu detik real = 1,6 menit
            # sim. Memakai dt mentah membuat motif NPC berjalan 1,6x lebih
            # lambat daripada jam yang mereka tinggali, dan "Tidur 420 menit"
            # sebenarnya berlangsung 420 detik real, bukan 7 jam dalam game.
            menit = dt * INGAME_MINUTES_PER_REAL_SECOND
            if mv is not None:
                mv.tick(menit)
            self._maju_interaksi(npc_id, menit)
            # Auto-queue aksi paling urgent kalau idle DAN tidak sedang
            # menjalani interaksi. Tanpa syarat kedua, sim memilih ulang tiap
            # frame dan tidak pernah menyelesaikan apa pun.
            if npc_id not in self._sisa and not ent.thread.queue and not ent.thread.stack:
                self._auto_queue(ent)
        self.vm.tick(dt)

    # ─── OTONOMI ─────────────────────────────────────────
    def _posisi_ubin(self, npc_id: str):
        pos = getattr(self.state, 'npc_positions', {}).get(npc_id)
        if not pos:
            return None
        try:
            return int(round(pos['x'])), int(round(pos['y']))
        except Exception:
            return None

    def _pilih_dari_dunia(self, npc_id: str):
        """Pilih satu (objek, interaksi) dari yang benar-benar ada di sekitar.

        Ini yang membuat perabot berarti. Sebelum ini NPC memilih dari daftar
        mati tiga baris — lapar<35 makan, energi<25 tidur, sosial<30 bicara —
        dan tidak pernah melihat sekelilingnya sama sekali. Kasur, kompor,
        kursi, televisi, rak buku, cermin, tungku, dermaga: seluruh katalog
        iklan di objects.py tidak pernah dibaca satu kali pun oleh siapa pun.

        Sekarang skornya datang dari jarak nyata ke benda nyata, dan gerbang
        `minimum` tiap iklan yang memutuskan apakah sim boleh tergoda —
        itulah yang mencegah tidur saat segar tanpa satu pun aturan khusus.
        """
        if self.peta is None:
            return None
        mv = self._motif.get(npc_id)
        ubin = self._posisi_ubin(npc_id)
        if mv is None or ubin is None:
            return None
        try:
            kandidat = autonomy_candidates(self.peta, ubin[0], ubin[1])
        except Exception:
            return None
        if not kandidat:
            return None
        return choose_action(mv, kandidat, self._rng)

    def _auto_queue(self, ent: BehaviorEntity):
        # Dunia dulu: kalau ada perabot di sekitar yang iklannya lolos gerbang,
        # itu yang dipakai. Daftar mati di bawah cuma jaring pengaman untuk
        # scene tanpa perabot sama sekali — supaya perilaku tidak pernah jadi
        # lebih buruk daripada sebelum otonomi disambungkan.
        pilih = self._pilih_dari_dunia(ent.name)
        if pilih is not None:
            obj, inter = pilih
            self._pilihan[ent.name] = (obj, inter)
            self.jml_pilihan_dunia += 1
            # Iklannya BELUM dibayar di sini. Membayarnya saat memilih berarti
            # sim mendapat manfaatnya tanpa melakukan apa pun — motif kenyang
            # seketika, lalu ia langsung memilih hal lain, dan desanya terlihat
            # kedutan alih-alih hidup. Dibayar di _maju_interaksi() setelah
            # durasinya benar-benar berlalu.
            self._sisa[ent.name] = max(1.0, float(getattr(inter, 'duration', 60.0)))
            self._anim_hint[ent.name] = inter.name.lower().replace(' ', '_')
            ent.queue_action('idle', priority=1)
            return

        mv = self._motif.get(ent.name)
        if mv is not None:
            kandidat = [((None, None, -1), inter, 0.0) for _, inter in _CADANGAN]
            pilih = choose_action(mv, kandidat, self._rng)
            if pilih is not None:
                obj, inter = pilih
                nama_vm = next((a for a, i in _CADANGAN if i is inter), 'idle')
                ent.queue_action(nama_vm, priority=10)
                self._pilihan[ent.name] = (obj, inter)
                self._sisa[ent.name] = inter.duration
                return
        ent.queue_action("idle", priority=1)

    def _maju_interaksi(self, npc_id: str, dt: float):
        """Jalankan waktu interaksi yang sedang berlangsung; bayar saat tuntas.

        Durasi diambil dari `Interaction.duration` (menit-sim) — Tidur 420,
        Makan 45, Duduk 60. Itu yang membuat komitmen: sim yang sedang tidur
        tidak ikut memilih ulang, dan desanya punya ritme alih-alih semua orang
        berganti kegiatan tiap frame.
        """
        sisa = self._sisa.get(npc_id)
        if sisa is None:
            return
        sisa -= dt
        if sisa > 0.0:
            self._sisa[npc_id] = sisa
            return
        del self._sisa[npc_id]
        pilih = self._pilihan.get(npc_id)
        if pilih is not None:
            self._terapkan_iklan(npc_id, pilih[1])
            self.jml_selesai += 1

    def _terapkan_iklan(self, npc_id: str, inter):
        """Bayar janji interaksinya ke motif NPC.

        Iklan adalah JANJI, dan janji yang tidak pernah ditepati membuat sim
        memilih hal yang sama berulang-ulang selamanya: motifnya tidak pernah
        naik, jadi skornya tidak pernah turun. Menepatinya di sini yang membuat
        sim pindah ke kebutuhan berikutnya — dan itu yang terlihat sebagai
        desa yang hidup, bukan desa yang macet.

        Dipanggil SETELAH durasi interaksinya berlalu, bukan saat memilihnya.
        """
        mv = self._motif.get(npc_id)
        if mv is None:
            return
        for ad in getattr(inter, 'adverts', ()) or ():
            if ad.minimum is not None and mv.get(ad.motive) > ad.minimum:
                continue
            mv.add(ad.motive, ad.delta)

    def pilihan_terakhir(self, npc_id: str):
        """(objek, interaksi) yang terakhir dipilih NPC ini, atau None."""
        return self._pilihan.get(npc_id)

    def ringkas_pilihan(self) -> dict:
        """npc_id -> 'Nama Interaksi pada Nama Objek'. Dipakai regresi."""
        out = {}
        for npc_id, (obj, inter) in self._pilihan.items():
            try:
                if obj is None or obj[2] < 0:
                    out[npc_id] = f'{inter.name} (cadangan)'
                else:
                    out[npc_id] = f'{inter.name} pada {object_name(obj[2])}'
            except Exception:
                continue
        return out

    def get_motives(self, npc_id: str) -> Optional[dict]:
        ent = self._brains.get(npc_id)
        return dict(ent.motives) if ent else None

    def get_anim_hint(self, npc_id: str) -> Optional[str]:
        return self._anim_hint.get(npc_id)

    def queue(self, npc_id: str, action_name: str, priority: int = 5):
        ent = self._brains.get(npc_id)
        if ent:
            ent.queue_action(action_name, priority=priority)

    # ─── PATHFINDING ─────────────────────────────────────
    def rebuild_grid(self, scene_name: str, dungeon_tiles=None):
        """Bangun ulang PathGrid dari tile WALKABLE pada scene aktif.

        Sekaligus mengarahkan ulang pembaca peta otonomi. Kalau ini terlewat,
        NPC memilih perabot scene LAMA di scene baru — dan itu tidak melempar
        error apa pun, cuma membuat mereka berjalan ke arah yang tidak masuk
        akal. Dijaga `otonomi_hidup` di regress.py.
        """
        self.peta = _PetaScene(scene_name, dungeon_tiles)
        self._pilihan.clear()
        self._sisa.clear()
        if scene_name == "dungeon" and dungeon_tiles:
            tiles = dungeon_tiles
            h, w = len(tiles), len(tiles[0]) if tiles else 0
        else:
            sc = SCENES.get(scene_name)
            if sc is None:
                return
            tiles = sc.tiles
            h, w = sc.h, sc.w
        self.grid = PathGrid(w, h, tile_size=1.0)
        for r in range(h):
            for c in range(w):
                if tiles[r][c] not in WALKABLE:
                    self.grid.set_obstacle(c, r)
        self._grid_scene = scene_name

    def plan_path(self, sx: float, sy: float, tx: float, ty: float):
        """Return list waypoint [(cx, cy), ...] atau None."""
        start = (int(round(sx)), int(round(sy)))
        goal  = (int(round(tx)), int(round(ty)))
        path = self.grid.find_path(start, goal)
        if not path:
            return None
        smooth = self.grid.smooth_path(path)
        # Buang titik start (NPC sudah di sana)
        return [(float(c), float(r)) for (c, r) in smooth[1:]] or None
