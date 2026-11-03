"""penunjuk.py — penunjuk tujuan tutorial: penanda di dunia + panah di tepi layar.

Kenapa ini ada. Tutorial "Lima Menit Pertama" (game/tutorial.py) hanya
memberi kalimat: "Kotak pos ada di depan rumah - dekati lalu tekan [F]",
"Masuk rumah lalu tekan [T]". Pemain baru harus menerjemahkan kalimat itu
menjadi arah di peta 28x20 yang belum pernah ia lihat, dan rumah, kotak pos,
serta Peti Kirim tidak menonjol dari kejauhan.

Penunjuk ini menjawab "ke mana" untuk tiap langkah tutorial:

  surat    kotak pos (tile MB di kebun)
  cangkul  petak tanah terdekat yang belum dicangkul
  tanam    petak tercangkul terdekat yang masih kosong
  siram    tanaman terdekat yang belum disiram
  tidur    pintu rumah; di dalam rumah, kasur
  panen    tanaman matang terdekat
  kirim    Peti Kirim (hanya kalau tas berisi hasil panen)

Target di scene lain ditunjuk lewat portal di scene sekarang yang menuju ke
sana (dicari lewat graf portal, bukan dipatok). Target dipilih sekali lalu
"lengket" sampai tidak berlaku lagi -- penanda yang meloncat ke petak lain
setiap pemain melangkah terbaca sebagai gangguan, bukan petunjuk.

Rupa: belah ketupat emas melayang naik-turun di atas target, cincin
berdenyut di tanah, dan -- kalau target di luar layar -- panah emas di tepi
layar dengan nama tujuannya.
"""
from __future__ import annotations

import math
from collections import deque

from ursina import Entity, Text, Texture, camera, color

from . import panel_kartu as PK

_TEX: dict = {}


# Warna per jalur: emas = tutorial/tugas utama, biru-hijau = Cerita Dua Desa.
WARNA_JALUR = {
    'utama':    (PK.EMAS, (255, 236, 180), (120, 82, 30)),
    'dua_desa': ((112, 214, 200), (200, 246, 238), (30, 96, 88)),
}


def _tex(nama, jalur='utama'):
    kunci = (nama, jalur)
    if kunci in _TEX:
        return _TEX[kunci]
    isi, terang, gelap = WARNA_JALUR[jalur]
    tex = None
    try:
        from PIL import Image, ImageDraw, ImageFilter
        n = 128
        img = Image.new('RGBA', (n, n), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if nama == 'ketupat':
            pendar = Image.new('RGBA', (n, n), (0, 0, 0, 0))
            ImageDraw.Draw(pendar).polygon([(64, 6), (118, 64), (64, 122), (10, 64)],
                                           fill=(*isi, 150))
            img.alpha_composite(pendar.filter(ImageFilter.GaussianBlur(9)))
            d.polygon([(64, 18), (106, 64), (64, 110), (22, 64)], fill=(*isi, 255))
            d.polygon([(64, 18), (106, 64), (64, 64)], fill=(*terang, 255))
            d.polygon([(64, 18), (106, 64), (64, 110), (22, 64)], outline=(*gelap, 255),
                      width=4)
        elif nama == 'cincin':
            d.ellipse([8, 8, n - 8, n - 8], outline=(*isi, 255), width=9)
            img = img.filter(ImageFilter.GaussianBlur(1.2))
        elif nama == 'panah':
            pendar = Image.new('RGBA', (n, n), (0, 0, 0, 0))
            ImageDraw.Draw(pendar).polygon([(118, 64), (24, 16), (46, 64), (24, 112)],
                                           fill=(0, 0, 0, 160))
            img.alpha_composite(pendar.filter(ImageFilter.GaussianBlur(6)))
            d.polygon([(112, 64), (28, 22), (48, 64), (28, 106)], fill=(*isi, 255),
                      outline=(*gelap, 255))
        tex = Texture(img)
        tex.filtering = 'bilinear'
    except Exception:
        tex = None
    _TEX[kunci] = tex
    return tex


# ── mencari target ─────────────────────────────────────────────────────
def _tile_pertama(scene, tid):
    from .scenes import SCENES
    sc = SCENES.get(scene)
    if sc is None:
        return None
    for y, baris in enumerate(sc.tiles):
        for x, v in enumerate(baris):
            if v == tid:
                return (x, y)
    return None


def _portal_menuju(dari, ke):
    """Tile portal di scene `dari` yang langkah pertamanya menuju `ke`
    (BFS di graf portal). None kalau tidak tersambung."""
    from .scenes import SCENES
    if dari == ke:
        return None
    awal = {}
    antre = deque()
    for p in getattr(SCENES.get(dari), 'portals', []) or []:
        tujuan = p[2]
        if tujuan not in awal:
            awal[tujuan] = (p[0], p[1])
            antre.append(tujuan)
    asal_dari = {t: t for t in awal}
    dikunjungi = set(awal) | {dari}
    while antre:
        sc = antre.popleft()
        if sc == ke:
            return awal[asal_dari[sc]]
        for p in getattr(SCENES.get(sc), 'portals', []) or []:
            if p[2] not in dikunjungi:
                dikunjungi.add(p[2])
                asal_dari[p[2]] = asal_dari[sc]
                antre.append(p[2])
    return None


def _petak(s):
    """[(x, y, soil)] petak di kebun."""
    keluar = []
    for k, soil in (getattr(s, 'soil', {}) or {}).items():
        try:
            x, y, sc = k.split(',')
        except ValueError:
            continue
        if sc == 'farm':
            keluar.append((int(x), int(y), soil))
    return keluar


def _terdekat(s, calon):
    px, py = s.player_x, s.player_y
    return min(calon, key=lambda c: (c[0] - px) ** 2 + (c[1] - py) ** 2) if calon else None


def target_langkah(s, langkah_id):
    """(scene, tx, ty, nama) untuk langkah tutorial, atau None."""
    from .config import MB, BD, D, SHIP_BIN_TILE
    from .data import CROPS
    if langkah_id == 'surat':
        t = _tile_pertama('farm', MB)
        return ('farm', t[0], t[1], 'Kotak pos') if t else None
    if langkah_id == 'cangkul':
        from .scenes import SCENES
        tergarap = {(x, y) for x, y, so in _petak(s) if so.get('tilled')}
        calon = [(x, y) for y, r in enumerate(SCENES['farm'].tiles)
                 for x, v in enumerate(r) if v == D and (x, y) not in tergarap]
        # Berdiri di atas tanah yang bisa dicangkul = sudah sampai; penanda
        # di petak sendiri cuma menutupi kepala tokoh (tangkapan pertama).
        if s.scene_name == 'farm':
            from .scenes import SCENES as _S
            px, py = int(round(s.player_x)), int(round(s.player_y))
            try:
                if _S['farm'].tiles[py][px] == D and (px, py) not in tergarap:
                    return None
            except IndexError:
                pass
        t = _terdekat(s, calon) if s.scene_name == 'farm' else (calon[0] if calon else None)
        return ('farm', t[0], t[1], 'Tanah untuk dicangkul') if t else None
    if langkah_id == 'tanam':
        calon = [(x, y) for x, y, so in _petak(s) if so.get('tilled') and not so.get('crop')]
        t = _terdekat(s, calon)
        return ('farm', t[0], t[1], 'Petak siap tanam') if t else None
    if langkah_id == 'siram':
        calon = [(x, y) for x, y, so in _petak(s) if so.get('crop') and not so.get('watered')]
        t = _terdekat(s, calon)
        return ('farm', t[0], t[1], 'Tanaman haus') if t else None
    if langkah_id == 'tidur':
        t = _tile_pertama('house', BD)
        return ('house', t[0], t[1], 'Kasur') if t else None
    if langkah_id == 'panen':
        calon = [(x, y) for x, y, so in _petak(s) if so.get('crop')
                 and so.get('age', 0) >= CROPS.get(so['crop'], {}).get('days', 4)]
        t = _terdekat(s, calon)
        return ('farm', t[0], t[1], 'Siap panen') if t else None
    if langkah_id == 'kirim':
        inv = getattr(s, 'inventory', {}) or {}
        if any(inv.get(k, 0) > 0 for k in CROPS):
            return ('farm', SHIP_BIN_TILE[0], SHIP_BIN_TILE[1], 'Peti Kirim')
    return None


_PEDANG_BESI = ('sword_besi', 'sword_emas', 'sword_mithril')


def _tangga_gua(s):
    """Tangga turun: di dungeon, tangga lantai itu; di luar, tangga di Gua
    Sang Hyang (dungeon tidak punya portal, ia dimasuki lewat tangga)."""
    from .config import STAIRS_DOWN
    if s.scene_name == 'dungeon':
        tiles = getattr(s, 'dungeon_tiles', None) or []
        for y, r in enumerate(tiles):
            for x, v in enumerate(r):
                if v == STAIRS_DOWN:
                    return ('dungeon', x, y, 'Tangga turun')
        return None
    t = _tile_pertama('naga_cave', STAIRS_DOWN)
    return ('naga_cave', t[0], t[1], 'Tangga ke gua') if t else None


def target_quest(s):
    """(scene, tx, ty, nama) untuk tugas utama sesudah tutorial, atau None.

    Mengikuti syarat SUNGGUHAN di QuestController._stage_done, bukan judul
    tahapnya. tx/ty None = tujuannya sebuah tempat: ditunjuk lewat pintunya,
    dan penanda padam begitu pemain sudah di dalam."""
    st = getattr(s, 'quest_stage', 0)
    # Tahap pertama yang syaratnya BELUM terpenuhi, dengan pemeriksa yang sama
    # dengan QuestController. quest_stage baru maju saat ada kejadian yang
    # memanggil check_quest_progress, jadi angka mentahnya bisa tertinggal
    # satu-dua tahap dari keadaan sebenarnya.
    try:
        from .controllers.quest_controller import QuestController
        qc = QuestController(s)
        while st < 11 and qc._stage_done(st):
            st += 1
    except Exception:
        pass
    stt = getattr(s, 'stats', {}) or {}
    if st == 0:
        return target_langkah(s, 'surat')
    if st == 1:
        if stt.get('lobak_planted', 0) < 3:
            return target_langkah(s, 'tanam')
        return target_langkah(s, 'siram')
    if st == 2:
        return target_langkah(s, 'panen')
    if st == 3:
        return target_langkah(s, 'kirim')
    if st == 4:
        return _bengkel(s)
    if st == 5:
        if getattr(s, 'pickaxe_tier', 0) < 1:
            return _bengkel(s)
        return _tangga_gua(s)
    if st == 6:
        if s.scene_name != 'dungeon':
            return _tangga_gua(s)
        inv = getattr(s, 'inventory', {}) or {}
        from .config import ORE_TBG, ORE_BSI
        cari = ORE_TBG if inv.get('tembaga', 0) < 5 else ORE_BSI
        nama = 'Bijih tembaga' if cari == ORE_TBG else 'Bijih besi'
        t = _terdekat(s, _tile_dungeon(s, cari))
        return ('dungeon', t[0], t[1], nama) if t else _tangga_gua(s)
    if st == 7:
        if getattr(s, 'sword_id', None) not in _PEDANG_BESI:
            return _bengkel(s)
        if s.scene_name != 'dungeon':
            return _tangga_gua(s)
        t = _terdekat(s, [(int(round(m['x'])), int(round(m['y'])))
                          for m in getattr(s, 'mobs', []) or [] if m.get('hp', 0) > 0])
        return ('dungeon', t[0], t[1], 'Lawan') if t else _tangga_gua(s)
    if st == 8:
        return _tangkapan(s)
    if st == 9:
        return _tangga_gua(s)
    if st == 10:
        if s.scene_name == 'dungeon':
            bos = next((m for m in getattr(s, 'mobs', []) or []
                        if m.get('is_boss') and m.get('hp', 0) > 0), None)
            if bos is not None:
                return ('dungeon', int(round(bos['x'])), int(round(bos['y'])), 'Penguasa gua')
        return _tangga_gua(s)
    return None


def _tile_dungeon(s, tid):
    return [(x, y) for y, r in enumerate(getattr(s, 'dungeon_tiles', None) or [])
            for x, v in enumerate(r) if v == tid]


def _bengkel(s):
    """Bengkel Budi. Di dalamnya: Pak Budi sendiri (kalau sedang di bengkel),
    karena dialah yang terbaca sebagai 'tempat membuat alat'."""
    if s.scene_name == 'smith':
        t = _npc(s, 'budi')
        if t and t[0] == 'smith':
            return (t[0], t[1], t[2], 'Pak Budi  [U] bengkel')
        return None
    return ('smith', None, None, 'Bengkel Budi')


def _npc(s, npc_id):
    """(scene, tx, ty) warga dari npc_positions, atau None kalau tersembunyi."""
    pos = (getattr(s, 'npc_positions', {}) or {}).get(npc_id)
    if not pos or pos.get('scene') in (None, 'hidden'):
        return None
    return (pos['scene'], int(round(pos['x'])), int(round(pos['y'])))


# Scene yang punya makhluk liar (ecology.WILD_POPULASI). Kuburan Tua di depan:
# sejak 3 Nov 2026 ia punya makhluk halusnya sendiri (kemamang malam, tuyul
# kapan saja) untuk tahap "Misteri Kuburan". Scene lain cadangan, karena
# syarat tahapnya tetap tangkapan [Shift+F] makhluk liar mana pun.
_SCENE_LIAR = ('cemetery', 'farm', 'mountain', 'town', 'lake')
_HALUS = ('kemamang', 'tuyul')


def _tangkapan(s):
    """Makhluk liar terdekat yang benar-benar bisa ditangkap [Shift+F]."""
    malam = s.is_night() if hasattr(s, 'is_night') else False
    hidup = [w for w in getattr(s, 'wild_entities', []) or []
             if not w.get('night_only') or malam]
    def label(w):
        return ('Makhluk halus  [Shift+F]' if w.get('kind') in _HALUS
                else 'Tangkap  [Shift+F]')
    # Di kuburan, atau kuburan sedang berpenghuni: ke sana dulu.
    kuburan = [w for w in hidup if w.get('scene') == 'cemetery']
    if s.scene_name == 'cemetery' or kuburan:
        pilih = kuburan
    else:
        pilih = [w for w in hidup if w.get('scene') == s.scene_name]
    if pilih and pilih[0].get('scene') == s.scene_name:
        w = min(pilih, key=lambda w: (w['x'] - s.player_x) ** 2 + (w['y'] - s.player_y) ** 2)
        return (s.scene_name, int(round(w['x'])), int(round(w['y'])), label(w))
    if pilih:
        w = pilih[0]
        return (w['scene'], int(round(w['x'])), int(round(w['y'])), label(w))
    for sc in _SCENE_LIAR:
        ada = [w for w in hidup if w.get('scene') == sc]
        if ada:
            w = ada[0]
            return (sc, int(round(w['x'])), int(round(w['y'])), label(w))
    return None


def target_dua_desa(s):
    """(scene, tx, ty, nama) untuk Cerita Dua Desa (data.QUEST_STAGES ber-alur),
    atau None. Tahapnya dari state.dua_desa_stage."""
    from .config import PPN
    from . import dua_desa as dd
    from .data import KERUKUNAN_CERITA, KERUKUNAN_TIKAR
    ds = getattr(s, 'dua_desa_stage', 0)
    inv = getattr(s, 'inventory', {}) or {}
    stt = getattr(s, 'stats', {}) or {}
    kr = getattr(s, 'kerukunan', 0)

    def warga(npc_id, nama):
        t = _npc(s, npc_id)
        return (t[0], t[1], t[2], nama) if t else None

    def papan(desa):
        sc = 'town' if desa == 'karsa' else 'lawang'
        t = _tile_pertama(sc, PPN)
        nama = 'Papan Titipan ' + ('Balai Desa' if desa == 'karsa' else 'Lawang')
        return (sc, t[0], t[1], nama) if t else None

    def papan_terdekat():
        return papan('lawang' if s.scene_name == 'lawang' else 'karsa')

    if ds == 0:
        return warga('kades_hardjo', 'Kades Hardjo')
    if ds == 1:
        return warga('mbah_rukmi', 'Mbah Rukmi')
    if ds == 2:
        if inv.get('susu', 0) > 0 or inv.get('telur', 0) > 0:
            if not (inv.get('lobak', 0) > 0 or inv.get('wortel', 0) > 0):
                return warga('mbah_rukmi', 'Mbah Rukmi')
        return warga('kades_hardjo', 'Kades Hardjo')
    if ds == 3:
        if stt.get('titipan_karsa', 0) < 1:
            return papan('karsa')
        if stt.get('titipan_lawang', 0) < 1:
            return papan('lawang')
        return None
    if ds == 4:
        return papan_terdekat() if kr < KERUKUNAN_CERITA else warga('mbah_rukmi', 'Mbah Rukmi')
    if ds == 5:
        return papan_terdekat() if kr < KERUKUNAN_TIKAR else warga('kades_hardjo', 'Kades Hardjo')
    if ds == dd.TAHAP_GOTONG:
        hari = getattr(s, 'gotong_royong_hari', 0)
        if hari and getattr(s, 'day', 0) >= hari:
            from .scenes.lawang import JALAN_LONGSOR
            x, y = JALAN_LONGSOR[0]
            return ('lawang', x, y, 'Longsor: gotong royong')
    return None


def _masih_berlaku(s, langkah_id, tgt):
    """Target lengket tetap dipakai selama masih menjawab langkahnya."""
    scene, x, y, _ = tgt
    soil = (getattr(s, 'soil', {}) or {}).get(f'{x},{y},farm', {})
    if langkah_id == 'cangkul':
        return not soil.get('tilled')
    if langkah_id == 'tanam':
        return soil.get('tilled') and not soil.get('crop')
    if langkah_id == 'siram':
        return soil.get('crop') and not soil.get('watered')
    if langkah_id == 'panen':
        return bool(soil.get('crop'))
    return True


MODE_PENUNJUK = ('Penunjuk: keduanya', 'Penunjuk: tugas utama saja',
                 'Penunjuk: Cerita Dua Desa saja', 'Penunjuk: mati')


class Penunjuk:
    """Dibuat sekali oleh Game3D; `tick()` tiap frame."""

    def __init__(self, app, jalur='utama'):
        self.app = app
        self.jalur = jalur
        self._t = 0.0
        self._langkah = None
        self._target = None          # (scene, tx, ty, nama) tujuan akhir
        self.titik = None            # (scene, tx, ty, nama) yang SEDANG ditunjuk
        self.ketupat = Entity(model='quad', texture=_tex('ketupat', jalur), billboard=True,
                              scale=1.25, color=color.white, enabled=False)
        self.ketupat.setLightOff()
        self.cincin = Entity(model='quad', texture=_tex('cincin', jalur), rotation_x=90,
                             scale=1.6, color=color.white, enabled=False)
        self.cincin.setLightOff()
        self.panah = Entity(parent=camera.ui, model='quad', texture=_tex('panah', jalur),
                            scale=0.05, color=color.white, enabled=False, z=-0.2)
        self.label = Text('', parent=camera.ui, font='Montserrat-Bold.ttf', scale=0.66,
                          origin=(0, 0), color=color.rgb(*WARNA_JALUR[jalur][0]),
                          enabled=False, z=-0.2)
        # Alas kapsul: teks emas tanpa alas hilang di atas tanah terang.
        self.alas = Entity(parent=camera.ui, model='quad', enabled=False, z=-0.15,
                           color=color.rgba(14, 16, 24, 200))

    def _sembunyi(self):
        for e in (self.ketupat, self.cincin, self.panah, self.label, self.alas):
            e.enabled = False
        self.titik = None

    def tick(self, dt):
        app = self.app
        s = app.state
        self._t += dt
        if getattr(app.panels, 'mode', 'hud') != 'hud':
            self._sembunyi()
            return
        # Saklar [F8] (state.penunjuk_mode): 0 keduanya, 1 tugas utama saja,
        # 2 Cerita Dua Desa saja, 3 mati.
        mode = getattr(s, 'penunjuk_mode', 0)
        if mode == 3 or (mode == 1 and self.jalur == 'dua_desa') \
                or (mode == 2 and self.jalur == 'utama'):
            self._sembunyi()
            return
        from .tutorial import current_step
        cur = current_step(s)
        if self.jalur == 'dua_desa':
            # Jalur kedua tidak bersaing dengan tutorial: pemain baru belajar
            # satu hal dulu. Sesudah tutorial ia berjalan sejajar tugas utama.
            self._target = target_dua_desa(s) if cur is None else None
        elif cur is not None:
            lid = cur[1].get('id')
            if lid != self._langkah or self._target is None \
                    or not _masih_berlaku(s, lid, self._target):
                self._langkah = lid
                self._target = target_langkah(s, lid)
        else:
            # Tutorial tamat: tugas utama. Dihitung ulang tiap frame karena
            # targetnya bergantung pada scene (tangga lantai dungeon, pintu
            # tempat) -- murah: paling banyak satu pindaian peta.
            self._langkah = f'quest{getattr(s, "quest_stage", 0)}'
            self._target = target_quest(s)
        tgt = self._target
        if tgt is None:
            self._sembunyi()
            return
        scene, tx, ty, nama = tgt
        if scene == s.scene_name and tx is None:
            self._sembunyi()            # sudah sampai di tempatnya
            return
        if scene != s.scene_name and s.scene_name == 'dungeon':
            # Dungeon tanpa portal: jalan keluarnya tangga naik.
            from .config import STAIRS_UP
            naik = next(((x, y) for y, r in enumerate(getattr(s, 'dungeon_tiles', None) or [])
                         for x, v in enumerate(r) if v == STAIRS_UP), None)
            if naik is None:
                self._sembunyi()
                return
            tgt = ('dungeon', naik[0], naik[1], 'Tangga naik')
        elif scene != s.scene_name:
            p = _portal_menuju(s.scene_name, scene)
            if p is None:
                self._sembunyi()
                return
            from .scenes import SCENES
            nama_sc = getattr(SCENES.get(scene), 'display', scene)
            tgt = (s.scene_name, p[0], p[1], f'Ke {nama_sc}')
        self.titik = tgt
        self._gambar(tgt)

    def _gambar(self, tgt):
        from .config import TILE_SIZE as TS, GROUND_H
        _, tx, ty, nama = tgt
        t = self._t
        wx, wz = tx * TS, ty * TS
        try:
            gy = self.app.world.get_surface_height(tx, ty)
        except Exception:
            gy = GROUND_H
        self.ketupat.enabled = self.cincin.enabled = True
        # Jalur kedua melayang sedikit lebih tinggi dan berdenyut berlawanan
        # fase: dua penanda di tempat yang sama tetap terbaca dua.
        naik = 0.7 if self.jalur == 'dua_desa' else 0.0
        fase = math.pi if self.jalur == 'dua_desa' else 0.0
        self.ketupat.position = (wx, gy + 2.3 + naik + 0.18 * math.sin(t * 3.0 + fase), wz)
        self.ketupat.rotation_z = 0
        k = (t * 0.9) % 1.0
        self.cincin.position = (wx, gy + 0.06, wz)
        self.cincin.scale = 1.0 + 1.2 * k
        self.cincin.color = color.rgba(255, 255, 255, int(230 * (1.0 - k)))

        # Panah tepi layar bila penanda di luar pandangan.
        sp = self._layar(self.ketupat)
        from ursina import window
        ex = window.aspect_ratio / 2
        # "Terlihat" = di luar empat pojok HUD (alat, kartu tujuan, jam,
        # motif, petunjuk tombol). Penanda di balik pojok itu tertutup, jadi
        # diperlakukan seperti di luar layar dan ditunjuk dengan panah.
        di_layar = sp is not None and abs(sp[0]) < ex - 0.20 and abs(sp[1]) < 0.34
        if di_layar:
            self.panah.enabled = False
            # Nama tujuan kecil di atas penanda, hanya saat sudah terlihat.
            self.label.enabled = True
            self.label.text = nama
            self.label.position = (sp[0], sp[1] + 0.055)
            self._pas_alas()
            return
        if sp is None:
            # Di belakang kamera: arah dari pusat layar, dibalik.
            arah = self._arah_belakang(self.ketupat)
        else:
            arah = sp
        ax, ay = arah
        L = math.hypot(ax, ay) or 1.0
        ax, ay = ax / L, ay / L
        # Proyeksikan ke kotak tepi layar dengan margin.
        mx, my = ex - 0.06, 0.40
        sk = min(mx / abs(ax) if ax else 1e9, my / abs(ay) if ay else 1e9)
        px, py = ax * sk, ay * sk
        # Di tepi kiri/kanan, panah dijaga di pita tengah (|y| <= 0,26):
        # pojok-pojoknya milik HUD.
        if abs(px) > ex - 0.10:
            py = max(-0.26, min(0.26, py))
        if self.jalur == 'dua_desa':
            # Satu tingkat di bawah panah emas kalau keduanya di tepi yang sama.
            py -= 0.085
        denyut = 1.0 + 0.10 * math.sin(t * 6.0)
        self.panah.enabled = True
        self.panah.position = (px, py)
        self.panah.scale = 0.064 * denyut
        self.panah.rotation_z = -math.degrees(math.atan2(ay, ax))
        self.label.enabled = True
        self.label.text = nama
        self.label.position = (px - ax * 0.085, py - ay * 0.085 - 0.002)
        self._pas_alas()

    # Blok HUD yang tidak boleh ditimpa label penunjuk.
    _BLOK_HUD = ('_obj_bg', '_scrim_kiri', '_scrim_kanan', '_scrim_bawah',
                 '_motive_panel_bg')

    def _pas_alas(self):
        w = PK._lebar(self.label) + 0.026
        h = 0.034
        x, y = self.label.position[0], self.label.position[1]
        # Label yang jatuh di atas kartu tutorial/alas HUD menimpa teksnya:
        # sembunyikan labelnya, panah/penandanya tetap.
        p = getattr(self.app, 'panels', None)
        for nama in self._BLOK_HUD:
            e = getattr(p, nama, None)
            if e is None or not e.enabled:
                continue
            ex0, ex1 = e.x - e.scale_x / 2, e.x + e.scale_x / 2
            ey0, ey1 = e.y - e.scale_y / 2, e.y + e.scale_y / 2
            if x + w / 2 > ex0 and x - w / 2 < ex1 and y + h / 2 > ey0 and y - h / 2 < ey1:
                self.label.enabled = False
                self.alas.enabled = False
                return
        self.alas.enabled = True
        self.alas.position = self.label.position
        self.alas.scale = (w, h)
        self.alas.texture = PK.kotak_tex(w / h, 0.5)

    @staticmethod
    def _layar(node):
        """Posisi `node` di ruang camera.ui, atau None kalau di belakang kamera.

        Dibaca relatif ke base.cam lewat NodePath-nya sendiri, bukan dari
        `world_position`: koordinat Ursina (y ke atas) bukan koordinat
        render Panda (z ke atas), dan versi pertama yang mencampurnya
        menganggap titik di samping pemain ada di belakang kamera."""
        try:
            from direct.showbase.ShowBaseGlobal import base
            from panda3d.core import Point2
            p3 = node.getPos(base.cam)
            # Ursina memasang Panda dengan coordinate-system yup-left: depan
            # kamera = +z, bukan +y. Versi pertama memeriksa p3.y dan
            # menganggap semua titik di samping pemain ada di belakang.
            if p3.z <= 0.01:
                return None
            p2 = Point2()
            base.camLens.project(p3, p2)
            from ursina import window
            return (p2.x * window.aspect_ratio / 2, p2.y / 2)
        except Exception:
            return None

    @staticmethod
    def _arah_belakang(node):
        try:
            from direct.showbase.ShowBaseGlobal import base
            p3 = node.getPos(base.cam)
            # Di belakang: belok ke sisi tempat target berada, panah di bawah.
            return (p3.x if p3.x else 0.001, -0.6)
        except Exception:
            return (0.0, -1.0)
