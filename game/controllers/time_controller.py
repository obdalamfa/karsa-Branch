from ..config import (
    FORCE_SLEEP_HOUR, INGAME_MINUTES_PER_REAL_SECOND, 
    NEED_DECAY_LAPAR, NEED_DECAY_SOSIAL, NEED_DECAY_SENANG, NEED_MAX
)
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
        s.time_minutes   = 360.0
        s.energy         = s.max_energy
        s.hp             = s.max_hp
        s.lapar  = min(NEED_MAX, s.lapar  + 25)
        s.senang = min(NEED_MAX, s.senang + 20)
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

        # Ternak maju semalam persis seperti tanaman: yang kenyang mendekat
        # satu hari ke hasilnya, yang lapar diam di tempat. Diletakkan tepat
        # di bawah pertumbuhan tanaman supaya kedua siklus hidup di satu tempat
        # dan tidak bisa lagi menyimpang satu sama lain.
        from ..economy import tick_animals_daily
        tick_animals_daily(s)

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
            panels.flash_msg("Tidur... Hari baru dimulai!", 2.0)
            self.advance_day(player)
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
