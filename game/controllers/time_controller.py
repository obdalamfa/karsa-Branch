# NEED_DECAY_* dan NEED_MAX tidak diimpor lagi: setelah peluruhan pindah ke
# mesin motif dan dua tulisan mati di advance_day dihapus, tidak ada satu pun
# yang memakainya di berkas ini.
from ..config import FORCE_SLEEP_HOUR, INGAME_MINUTES_PER_REAL_SECOND
from ..data import CROPS

class TimeController:
    """Manages time, day progression, and needs decay."""
    
    def __init__(self, state):
        self.state = state

    def tick(self, dt, player):
        s = self.state
        s.time_minutes += INGAME_MINUTES_PER_REAL_SECOND * dt
        if s.time_minutes >= 1440:
            s.time_minutes -= 1440

        # Peluruhan delapan motif dengan laju asli TS1 (lihat game/motives.py).
        # Menggantikan tiga need seragam yang butuh 3,5-5,8 HARI untuk turun —
        # terlalu lambat untuk pernah terasa mendesak oleh pemain.
        ingame_dt = dt * INGAME_MINUTES_PER_REAL_SECOND
        s.mv.tick(ingame_dt)

        # Jalankan aksi terdepan di antrian. Motif diisi SELAMA aksi berjalan
        # supaya pemain melihat termometer merangkak naik dan langsung paham
        # sebab-akibatnya.
        q = getattr(player, 'queue', None)
        if q is not None:
            selesai = q.tick(ingame_dt)
            if selesai:
                self._last_action_done = selesai

        s.sync_motives()

        if s.get_hour() >= FORCE_SLEEP_HOUR:
            self.advance_day(player)
            return "Sudah larut malam — hari baru!"
        return None

    def advance_day(self, player):
        from ursina import invoke
        import random as _rng
        from ..config import DAYS_PER_SEASON
        from ..sound import play as sound_play

        s = self.state

        if getattr(player, '_is_flying', False) and hasattr(player, 'toggle_broom_flying'):
            player.toggle_broom_flying()

        s.day           += 1
        s.day_in_season += 1

        # Satu malam berlalu untuk ternak: kenyang turun, yang terlalu lama
        # dilalaikan jatuh sakit, yang terawat siap dipanen hasilnya.
        # game/husbandry.py sudah lengkap tapi tidak ada pemanggilnya sama
        # sekali — tanpa baris ini, merawat hewan tidak berakibat apa pun.
        try:
            from ..husbandry import daily_tick as _ternak_tick
            self._ternak_pagi = _ternak_tick(s)
        except Exception as e:
            import logging
            logging.warning(f"[TERNAK] daily_tick gagal: {e}")
            self._ternak_pagi = None
        # ── MALAM DISIMULASIKAN, BUKAN DILOMPATI ──────────────────────────
        # Baris lama cuma memindahkan jam ke 06:00 dan mengisi ulang stat lama.
        # Terukur: motif SEBELUM dan SESUDAH tidur identik sampai satu desimal.
        # Tidur — satu-satunya sumber pemulihan energi yang bukan interaksi —
        # tidak berakibat apa pun pada mesin yang menggerakkan mood, panel
        # SUASANA HATI, dan seluruh pilihan otonomi warga.
        #
        # Panjang malam dihitung dari jam BERAPA pemain tidur sampai 06:00,
        # jadi tidur jam 20:00 memulihkan lebih banyak daripada roboh jam 23:00
        # lewat FORCE_SLEEP_HOUR — tanpa satu pun tabel hukuman terpisah.
        menit_tidur = ((1440.0 - s.time_minutes) + 360.0
                       if s.time_minutes > 360.0 else 360.0 - s.time_minutes)
        self._tidur_menit = menit_tidur
        self._tidur_delta = s.mv.lewati_malam(menit_tidur)

        s.time_minutes   = 360.0

        # Dua sistem energi paralel disambungkan DI SINI, di satu-satunya
        # tempat yang penting. `s.energy` (stamina bertani) dan `s.mv.energi`
        # (mood dan otonomi) selama ini tidak saling tahu: yang pertama diisi
        # penuh tiap pagi apa pun yang terjadi, yang kedua tidak pernah diisi
        # sama sekali. Sekarang bangun tidur menurunkan stamina pagi dari
        # energi motif yang benar-benar didapat semalam.
        #
        # Lantai 35% disengaja, dan itu pilihan "longgar" yang diminta pemilik:
        # malam yang buruk membuat harinya berat, bukan membuat harinya mustahil.
        frac = (s.mv.energi + 100.0) / 200.0
        s.energy = max(int(s.max_energy * 0.35),
                       min(s.max_energy, int(round(s.max_energy * frac))))
        s.hp             = s.max_hp

        # `s.lapar += 25` dan `s.senang += 20` DIHAPUS, dan itu bukan
        # penghilangan fitur: keduanya tulisan mati. `update()` memanggil
        # `s.sync_motives()` tiap frame, yang menulis ulang kedua angka itu
        # dari `s.mv`. Terukur: naik ke 50,0 lalu kembali ke 25,0 dalam TIGA
        # frame. Yang menggantikannya adalah peluruhan malam yang sungguhan —
        # lapar memang turun semalaman (senang tidak, lajunya nol saat tidur),
        # jadi sarapan akhirnya punya alasan untuk ada.
        s.sync_motives()

        s.naga_fountain_used_today = False
        s.buffs.clear()

        # Rain auto-waters tilled soil
        if s.weather in ('Hujan', 'Badai'):
            for soil in s.soil.values():
                if soil.get('tilled') and not soil.get('watered'):
                    soil['watered'] = True

        # Tumbuh tanaman semalam
        cur_season = s.get_season()
        for soil in s.soil.values():
            if soil.get('watered') and soil.get('crop'):
                crop_seasons = CROPS.get(soil['crop'], {}).get('seasons', [])
                growth = 2 if cur_season in crop_seasons else 1
                soil['age'] = soil.get('age', 0) + growth
                soil['watered'] = False

        # `economy.tick_animals_daily` DIHAPUS dari sini, dan itu perbaikan
        # bukan penghilangan fitur. Dulu DUA tick ternak jalan tiap malam:
        # yang ini di atas catatan economy {kenyang, siap}, dan
        # `husbandry.daily_tick` di atas catatan {kenyang, air, bersih, lalai,
        # sakit}. Keduanya mensimulasikan hewan yang sama, di dua tempat, tanpa
        # saling tahu. Yang dibaca pie menu cuma milik economy — jadi air dan
        # bersih meluruh tanpa satu pun cara menaikkannya, dan terukur pada
        # hari ke-4 setiap hewan sakit permanen karena syarat sembuh menuntut
        # ketiganya >= 60. Sekarang husbandry satu-satunya yang memegang
        # ternak, dan aksinya sudah tersambung ke pie menu.

        if s.day_in_season > DAYS_PER_SEASON:
            s.day_in_season = 1
            old_season      = s.season_index
            s.season_index  = (old_season + 1) % 4
            if s.season_index == 0 and old_season == 3:
                s.year += 1

        _weathers = ['Cerah','Cerah','Cerah','Mendung','Hujan','Berangin','Badai']
        _weights  = [38, 22, 14, 12, 8, 4, 2]
        s.weather = _rng.choices(_weathers, weights=_weights)[0]

        sound_play('morning', 0.8)
        
        # In a real setup, wild respawn would be handled by EntityFactory/EntitiesManager
        # Using late import to prevent circular dependencies
        try:
            from ..entities import respawn_wild_at_morning
            respawn_wild_at_morning(s)
        except ImportError:
            pass
            
        # Optional: check quest progress
        if hasattr(player, 'quest_manager') and player.quest_manager:
            player.quest_manager.check_quest_progress()
        elif hasattr(player, '_check_quest_progress'):
            player._check_quest_progress()

    def try_sleep(self, panels, player):
        from ursina import invoke
        from ..sound import play as sound_play
        if self.state.scene_name == 'house':
            if getattr(player, '_is_flying', False):
                player.toggle_broom_flying(panels)
            sound_play('sleep', 0.8)
            self.advance_day(player)
            # Pesannya menyebut ANGKA, bukan cuma "hari baru". Sistem yang
            # akibatnya tidak terlihat sama saja dengan sistem yang tidak ada —
            # itu persis kenapa tidur bisa mati bertahun-tahun tanpa ada yang
            # menyadarinya. Sekarang pemain melihat lama tidurnya dan stamina
            # yang ia dapat darinya, jadi tidur jam 20:00 lawan roboh jam 23:00
            # adalah dua angka yang berbeda di layar.
            jam = getattr(self, '_tidur_menit', 0.0) / 60.0
            panels.flash_msg(
                f"Tidur {jam:.1f} jam. Bangun dengan {int(self.state.energy)}"
                f"/{self.state.max_energy} stamina.", 2.4)
            # Laporan kandang. `daily_tick` sudah mengembalikan ringkasan ini
            # sejak lama dan `advance_day` menyimpannya di `_ternak_pagi` —
            # tapi tidak ada satu pun yang menampilkannya, jadi hewan bisa
            # kelaparan sampai sakit tanpa pemain pernah diberi tahu. Ternak
            # yang sakit berhenti menghasilkan sama sekali, jadi diamnya mahal.
            lap = getattr(self, '_ternak_pagi', None)
            if lap:
                if lap.get('sakit'):
                    invoke(panels.flash_msg,
                           f"SAKIT: {', '.join(lap['sakit'])} — beri makan, "
                           f"minum, dan bersihkan kandangnya.", 4.0, delay=2.2)
                elif lap.get('lapar'):
                    invoke(panels.flash_msg,
                           f"Kelaparan: {', '.join(lap['lapar'])}", 3.0,
                           delay=2.2)
                elif lap.get('siap'):
                    invoke(panels.flash_msg,
                           f"Siap dipanen: {', '.join(lap['siap'])}", 3.0,
                           delay=2.2)
            # Deliver pending story messages after sleep
            if getattr(player, '_pending_seasonal_event', None):
                invoke(panels.flash_msg,
                       f"🎉 Hari ini: {player._pending_seasonal_event}!", 4.0,
                       delay=2.5)
                player._pending_seasonal_event = None
            if getattr(player, '_pending_lore_msg', None):
                invoke(panels.flash_msg, player._pending_lore_msg, 3.5, delay=3.0)
                player._pending_lore_msg = None
        else:
            panels.flash_msg("Tidur hanya di rumah (T).", 0.8)
