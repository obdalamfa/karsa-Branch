from ..data import QUEST_STAGES
from ..sound import play as sound_play
from ursina import invoke

class QuestController:
    """Manages quest progression, checks, and lore."""
    
    def __init__(self, state):
        self.state = state

    def check_quest_progress(self, panels=None):
        s = self.state
        # Rantai: satu aksi bisa melompati beberapa tahap sekaligus (cegah macet).
        while s.quest_stage < 11 and self._stage_done(s.quest_stage):
            s.quest_stage += 1
            if s.quest_stage >= 11:
                s.post_game = True
            self._notify_quest_up(panels)

    def _stage_done(self, st):
        """Syarat tiap tahap — DICOCOKKAN dgn deskripsi QUEST_STAGES, pakai sinyal
        yang benar-benar terjadi di gameplay (audit M4)."""
        s = self.state
        inv = s.inventory
        stt = s.stats
        if st == 0:  return bool(s.mail_read)                                       # cek kotak pos
        if st == 1:  return stt.get('lobak_planted', 0) >= 3 and stt.get('watered', 0) >= 3
        if st == 2:  return stt.get('lobak_harvested', 0) >= 3                       # panen 3 lobak
        if st == 3:  return s.gold >= 150                                           # kumpulkan 150G
        if st == 4:  return s.pickaxe_tier >= 1 or bool(s.sword_id)                 # alat lebih baik
        if st == 5:  return s.pickaxe_tier >= 1 and stt.get('deepest_level', 0) >= 1 # crafting + masuk gua
        if st == 6:  return inv.get('tembaga', 0) >= 5 and inv.get('besi', 0) >= 3   # 5 tembaga + 3 besi
        # Pedang besi ATAU lebih tinggi (kalau pemain sudah upgrade ke emas/mithril,
        # '== sword_besi' bikin quest MACET PERMANEN — pemblokir tamat game).
        if st == 7:  return s.sword_id in ('sword_besi', 'sword_emas', 'sword_mithril') and stt.get('mobs_killed', 0) >= 5
        if st == 8:  return s.captured_supernatural >= 1                            # tangkap makhluk halus
        if st == 9:  return stt.get('deepest_level', 0) >= 10                       # gua level 10
        if st == 10: return bool(s.naga_defeated)                                   # kalahkan Naga
        return False

    def _notify_quest_up(self, panels):
        s = self.state
        sound_play('magic', 0.8)
        # QUEST_STAGES adalah list of {'s','t','d'} (bukan dict) — cari berdasarkan stage.
        stage_title = next((q['t'] for q in QUEST_STAGES if q['s'] == s.quest_stage), 'Rahasia baru terungkap')
        msg = f"Quest Update: Tahap {s.quest_stage} - {stage_title}"
        if panels:
            panels.flash_msg(msg, 3.5)
        else:
            print("[Quest]", msg)

    def check_dungeon_lore(self, dungeon_level, player, panels=None):
        """Berikan setiap catatan LORE_ITEMS ber-found_at 'dungeon_<lantai>'.

        `found_at` satu-satunya sumber kebenaran. Dulu kedalamannya ditulis dua
        kali dan keduanya bocor: tabel fragmen di sini menaruh fragmen III di
        lantai 14 yang tidak pernah dibuat, dan tiga pesan kedalaman dicatat
        dengan id yang tidak punya entri LORE_ITEMS, jadi panel Catatan
        menampilkan "[dungeon_3]" tanpa isi.
        """
        from ..data import LORE_ITEMS
        s = self.state
        koleksi = getattr(s, 'lore_collected', [])
        tempat = f'dungeon_{dungeon_level}'
        baru = [lid for lid, item in LORE_ITEMS.items()
                if item.get('found_at') == tempat and lid not in koleksi]
        if not baru:
            return
        koleksi.extend(baru)
        s.lore_collected = koleksi
        pesan = self._pesan_lore_gua(baru)
        if panels:
            # Jeda 1 detik: lantai baru dimuat pada frame yang sama, dan frame
            # muat yang panjang menghabiskan waktu tampil flash.
            invoke(panels.flash_msg, pesan, 5.0, delay=1.0)
        else:
            player._pending_lore_msg = pesan

    @staticmethod
    def _pesan_lore_gua(lore_ids):
        """Judul catatan lalu isinya, dibungkus per 48 huruf: flash tidak
        membungkus sendiri, dan pesan lama 80-100 huruf dalam satu baris
        membentang hampir selebar layar."""
        import textwrap
        from ..data import LORE_ITEMS
        baris = ['[N] Catatan baru: ' + ', '.join(LORE_ITEMS[i]['name'] for i in lore_ids)]
        for i in lore_ids:
            baris += textwrap.wrap(LORE_ITEMS[i]['text'], 48)
        return '\n'.join(baris)

    def add_lore(self, lore_id, player, panels=None):
        """Add a lore item to the player's collection if not already found."""
        s = self.state
        lore_list = getattr(s, 'lore_collected', [])
        if lore_id not in lore_list:
            lore_list.append(lore_id)
            s.lore_collected = lore_list
            from ..data import LORE_ITEMS
            item = LORE_ITEMS.get(lore_id, {})
            name = item.get('name', lore_id)
            if panels:
                panels.flash_msg(f"[N] Catatan baru: {name}", 3.5)
            else:
                # Delayed flash via stored pending
                player._pending_lore_msg = f"[N] Catatan baru: {name}"

    # ─── Cerita Dua Desa (docs/CERITA_DUA_DESA.md) ───────────────────────
    # Jalur kedua yang berjalan sejajar quest_stage. Dimajukan oleh efek
    # pilihan dialog ('dua_desa' dan 'mitra' di BRANCHING_DIALOGUES), BUKAN oleh
    # check_quest_progress() di atas: pengecek itu belum tersambung ke mana pun
    # dan syarat tahapnya tidak cocok dengan QUEST_STAGES.

    @staticmethod
    def tahap_babak(babak=1):
        """Entri QUEST_STAGES milik satu babak Dua Desa, urut 's'."""
        return sorted((q for q in QUEST_STAGES
                       if q.get('alur') == 'dua_desa' and q.get('babak') == babak),
                      key=lambda q: q['s'])

    @staticmethod
    def tahap_dua_desa():
        """Semua entri jalur Dua Desa dari babak mana pun, urut 's'."""
        return sorted((q for q in QUEST_STAGES if q.get('alur') == 'dua_desa'),
                      key=lambda q: q['s'])

    @classmethod
    def babak_aktif(cls, tahap):
        """Babak yang sedang berjalan pada dua_desa_stage `tahap`. Sesudah
        tahap terakhir, babak terakhir yang sudah ditulis (panel J tetap
        menampilkannya, semua tercentang, sampai babak berikutnya dibuat)."""
        semua = cls.tahap_dua_desa()
        return next((q['babak'] for q in semua if q['s'] == tahap),
                    semua[-1]['babak'] if semua else 1)

    def maju_dua_desa(self, ke_tahap, panels=None):
        """Majukan jalur Dua Desa ke `ke_tahap`. Tidak pernah mundur, jadi
        mengulang percakapan yang sama tidak memutar balik cerita."""
        s = self.state
        if ke_tahap <= s.dua_desa_stage:
            return False
        babak_lama = self.babak_aktif(s.dua_desa_stage)
        s.dua_desa_stage = ke_tahap
        sound_play('magic', 0.8)
        berikut = [q for q in self.tahap_dua_desa() if q['s'] == ke_tahap]
        # Pesan flash dibatasi ~60 huruf: teks tengah layar berskala 1,32 dan
        # tidak membungkus baris, jadi rincian tahap cukup ada di panel J.
        if panels:
            if berikut:
                panels.flash_msg(f"Cerita Dua Desa: {berikut[0]['t']}. Lihat quest (J).", 4.0)
            else:
                panels.flash_msg(f"Cerita Dua Desa: babak {babak_lama} selesai.", 3.5)
        return True

    def bonus_mitra(self, desa):
        """Barang bonus awal untuk desa mitra, {item_id: jumlah}.

        Karsa memberi bibit dua tanaman termahal MUSIM INI, supaya bonusnya
        langsung bisa ditanam kapan pun pemain memilih. Hanya tanaman yang
        dijual Warung yang dihitung: crops.py ikut mendaftarkan tanaman baru ke
        CROPS, dan benih yang tidak ada di toko belum punya nama tampilan pasti.
        """
        from ..data import MITRA_DESA, CROPS, SHOP_ITEMS
        info = MITRA_DESA.get(desa)
        if not info:
            return {}
        if 'barang' in info:
            return dict(info['barang'])
        musim = self.state.get_season()
        cocok = [it['crop'] for it in SHOP_ITEMS
                 if it.get('crop') and musim in CROPS.get(it['crop'], {}).get('seasons', [])]
        cocok.sort(key=lambda c: -CROPS[c]['sell'])
        n = info.get('bibit_per_jenis', 5)
        return {f'{c}_seed': n for c in cocok[:2]}

    def pilih_mitra(self, desa, panels=None):
        """Tetapkan desa mitra, beri bonus awalnya, dan tutup babak 1.
        Pilihan ini sekali seumur permainan; panggilan kedua diabaikan."""
        from ..data import MITRA_DESA
        from ..economy import item_name
        s = self.state
        if s.mitra_desa or desa not in MITRA_DESA:
            return False
        bonus = self.bonus_mitra(desa)
        for item, n in bonus.items():
            s.inventory[item] = s.inventory.get(item, 0) + n
        s.mitra_desa = desa
        # Langsung ke tahap "selesai" tanpa lewat maju_dua_desa(): satu pesan
        # gabungan, karena flash kedua akan menimpa pesan bonus.
        s.dua_desa_stage = max(s.dua_desa_stage, len(self.tahap_babak()))
        sound_play('magic', 0.8)
        isi = ', '.join(f"+{n} {item_name(i)}" for i, n in bonus.items())
        if panels:
            panels.flash_msg(f"Babak 1 selesai: kini kau mitra {MITRA_DESA[desa]['nama']}!\n{isi}", 4.5)
        return True

    # ─── Babak 2 "Menjembatani" ──────────────────────────────────────────
    # Perhitungan murninya (titipan harian, nilai lomba, jadwal) ada di
    # game/dua_desa.py; di sini hanya yang mengubah state dan memberi kabar.

    def tambah_kerukunan(self, n):
        """Tambah kerukunan Karsa-Lawang, dijepit 0..KERUKUNAN_MAKS.
        Mengembalikan kenaikan yang SUNGGUH terjadi (0 kalau sudah penuh)."""
        from ..data import KERUKUNAN_MAKS
        s = self.state
        lama = s.kerukunan
        s.kerukunan = max(0, min(KERUKUNAN_MAKS, lama + n))
        return s.kerukunan - lama

    def serahkan_titipan(self, papan, idx, panels=None):
        """Antar titipan nomor `idx` (1-based) dari papan `papan` hari ini.

        Mengembalikan pesan untuk flash ('' = tombol itu tidak berarti apa-apa).
        Pesan maju tahap DIGABUNG ke pesan ini, tidak di-flash sendiri: panel
        mem-flash kembalian ini sesudahnya, jadi flash kedua akan menimpanya.
        """
        from .. import dua_desa as dd
        from ..data import TITIPAN_KERUKUNAN, TITIPAN_HATI
        from ..economy import item_name
        s = self.state
        if s.dua_desa_stage < dd.TAHAP_BABAK2:
            return ''
        daftar = dd.titipan_hari_ini(s, papan)
        if not (1 <= idx <= len(daftar)):
            return ''
        t = daftar[idx - 1]
        sudah = dd.selesai_hari_ini(s)
        if t['id'] in sudah:
            return "Titipan itu sudah kau antar hari ini."
        punya = s.inventory.get(t['item'], 0)
        if punya < t['n']:
            return f"Barang kurang: butuh {item_name(t['item'])} x{t['n']} (punya {punya})."
        s.inventory[t['item']] = punya - t['n']
        if s.inventory[t['item']] <= 0:
            del s.inventory[t['item']]
        emas = dd.imbalan(t)
        s.gold += emas
        s.stats['earned'] = s.stats.get('earned', 0) + emas
        if t.get('npc'):
            s.npc_hearts[t['npc']] = min(10, s.npc_hearts.get(t['npc'], 0) + TITIPAN_HATI)
        naik = self.tambah_kerukunan(TITIPAN_KERUKUNAN)
        s.titipan = {'hari': dd.kunci_hari(s), 'selesai': sudah + [t['id']]}
        s.stats[f'titipan_{papan}'] = s.stats.get(f'titipan_{papan}', 0) + 1
        sound_play('gift', 0.8)
        pesan = f"{dd.nama_peminta(t)}: Terima kasih! +{emas}G, Kerukunan +{naik}"
        # Juru Titip selesai begitu KEDUA papan pernah dilayani.
        if (s.dua_desa_stage == dd.TAHAP_BABAK2 and s.stats.get('titipan_karsa', 0) >= 1
                and s.stats.get('titipan_lawang', 0) >= 1 and self.maju_dua_desa(dd.TAHAP_BABAK2 + 1)):
            berikut = [q for q in self.tahap_dua_desa() if q['s'] == s.dua_desa_stage]
            pesan += f"\nCerita Dua Desa: {berikut[0]['t']}. Lihat quest (J)."
        return pesan

    def ikut_lomba(self, kategori, idx, panels=None):
        """Serahkan calon nomor `idx` (1-based, urutan dua_desa.pilihan_lomba)
        untuk kategori 'masak' atau 'panen' Lomba Antar-Desa. Sekali per
        kategori per tahun. Mengembalikan pesan hasil untuk flash."""
        from .. import dua_desa as dd
        from ..data import LOMBA_ANTAR_DESA
        from ..economy import item_name
        s = self.state
        if not dd.lomba_berlangsung(s) or not s.mitra_desa:
            return ''
        k = LOMBA_ANTAR_DESA['kategori'][kategori]
        catatan = dict(dd.catatan_lomba(s))
        if kategori in catatan:
            return f"Kau sudah ikut {k['nama']} tahun ini."
        calon = dd.pilihan_lomba(s, kategori)
        if not (1 <= idx <= len(calon)):
            return ''
        item, n, nilai = calon[idx - 1]
        s.inventory[item] -= n
        if s.inventory[item] <= 0:
            del s.inventory[item]
        lawan = dd.nilai_lawan(s, kategori)
        menang = nilai > lawan
        naik = self.tambah_kerukunan(LOMBA_ANTAR_DESA['kerukunan_ikut']
                                     + (LOMBA_ANTAR_DESA['kerukunan_menang'] if menang else 0))
        if menang:
            s.gold += k['hadiah']
            for juri in LOMBA_ANTAR_DESA['juri']:
                s.npc_hearts[juri] = min(10, s.npc_hearts.get(juri, 0)
                                         + LOMBA_ANTAR_DESA['hati_juri_menang'])
        catatan['tahun'] = s.year
        catatan[kategori] = {'item': item, 'n': n, 'nilai': nilai, 'lawan': lawan, 'menang': menang}
        s.lomba = catatan
        sound_play('magic' if menang else 'menu_select', 0.8)
        nama = item_name(item) + (f" x{n}" if n > 1 else '')
        hasil = f"MENANG! +{k['hadiah']}G" if menang else "Kalah tipis."
        return f"{k['nama']}: {nama} {nilai} vs {lawan}. {hasil}\nKerukunan +{naik}"

    def jadwalkan_gotong_royong(self, panels=None):
        """Kades setuju: penggalian longsor dimulai esok pagi (dua_desa.jadwal_npc
        memindahkan kedua sesepuh ke longsor mulai hari itu)."""
        s = self.state
        if s.jalan_lama_terbuka:
            return False
        s.gotong_royong_hari = s.day + 1
        return True

    def buka_jalan_lama(self, panels=None, world=None):
        """Gotong royong selesai: jalan lama terbuka dan babak 2 tamat."""
        from ..data import KERUKUNAN_GOTONG
        s = self.state
        if s.jalan_lama_terbuka:
            return False
        s.jalan_lama_terbuka = True
        s.gotong_royong_hari = 0
        naik = self.tambah_kerukunan(KERUKUNAN_GOTONG)
        s.dua_desa_stage = max(s.dua_desa_stage, max(q['s'] for q in self.tahap_babak(2)) + 1)
        sound_play('magic', 0.8)
        if panels:
            panels.flash_msg(f"Babak 2 selesai: jalan lama ke Gua Sang Hyang\n"
                             f"terbuka! Kerukunan +{naik}", 4.5)
        # Ubin longsor dan portal baru hanya berlaku sesudah scene dimuat ulang
        # (Scene.sesuaikan). Mengosongkan nama scene membuat app.update()
        # menjalankan transisi scene biasa ke scene yang SAMA begitu dialog
        # selesai — jalur yang sama dengan melewati portal, lengkap dengan
        # pendaratan aman dan NPC yang dimuat ulang.
        if world is not None:
            world.scene_name = None
        return True

    def check_npc_lore_gift(self, npc_id, player, panels):
        """Check if an NPC should gift a lore item based on hearts."""
        s = self.state
        hearts = s.npc_hearts.get(npc_id, 0)
        lore_gifts = {
            'sari': (6, 'buku_paman_arsa'),
            'maya': (7, 'peta_mimpi_maya'),
        }
        if npc_id in lore_gifts:
            req_hearts, lore_id = lore_gifts[npc_id]
            if hearts >= req_hearts:
                self.add_lore(lore_id, player, panels)
