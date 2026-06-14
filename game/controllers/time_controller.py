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

        # Needs / Motives decay
        ingame_dt = dt * INGAME_MINUTES_PER_REAL_SECOND
        s.lapar  = max(0.0, s.lapar  - NEED_DECAY_LAPAR  * ingame_dt)
        s.sosial = max(0.0, s.sosial - NEED_DECAY_SOSIAL * ingame_dt)
        s.senang = max(0.0, s.senang - NEED_DECAY_SENANG * ingame_dt)

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

        # Tumbuh tanaman semalam — Sakuna: jadwal air, nutrisi, gulma → mutu (★)
        cur_season = s.get_season()
        akar = (getattr(s, 'batin', {}) or {}).get('akar', 1)
        for soil in s.soil.values():
            crop = soil.get('crop')
            if not crop:
                if soil.get('tilled') and _rng.random() < 0.18:      # gulma di petak kosong
                    soil['weeds'] = min(3, soil.get('weeds', 0) + 1)
                continue
            cdata   = CROPS.get(crop, {})
            days    = cdata.get('days', 4)
            age     = soil.get('age', 0)
            q       = soil.get('quality', 3.0)
            nut     = soil.get('nutrients', 3)
            weeds   = soil.get('weeds', 0)
            watered = soil.get('watered', False) or s.weather in ('Hujan', 'Badai')
            ripening = age >= max(1, days * 0.6)                     # fase menua → ingin kering
            in_season = cur_season in cdata.get('seasons', [])
            grow = 0
            # Jadwal air: muda ingin BASAH, menua ingin KERING (inti Sakuna)
            if not ripening:
                if watered:
                    grow = 2 if in_season else 1; q += 0.15
                else:
                    q -= 0.5                                          # kekeringan saat muda
            else:
                grow = 1
                q += 0.2 if not watered else -0.55                   # tergenang saat menua = buruk
            # Nutrisi tanah
            if nut > 0:
                q += 0.2 + akar * 0.05; nut -= 1
            else:
                q -= 0.35
            # Gulma menekan
            if weeds >= 2:
                q -= 0.4; grow = max(0, grow - 1)
            if _rng.random() < 0.32:
                weeds = min(3, weeds + 1)
            soil['age']       = age + grow
            soil['quality']   = max(1.0, min(5.0, q))
            soil['nutrients'] = nut
            soil['weeds']     = weeds
            soil['watered']   = False

        if s.day_in_season > DAYS_PER_SEASON:
            s.day_in_season = 1
            old_season      = s.season_index
            s.season_index  = (old_season + 1) % 4
            if s.season_index == 0 and old_season == 3:
                s.year += 1

        _weathers = ['Cerah','Cerah','Cerah','Mendung','Hujan','Berangin','Badai']
        _weights  = [38, 22, 14, 12, 8, 4, 2]
        s.weather = _rng.choices(_weathers, weights=_weights)[0]

        # Jual isi Peti Kirim (shipping bin) — emas masuk saat fajar
        self._last_ship_sale = (0, 0)
        bin_ = getattr(s, 'ship_bin', None)
        if bin_:
            earned, items = 0, 0
            for item, n in list(bin_.items()):
                earned += CROPS.get(item, {}).get('sell', 0) * n
                items += n
            if earned > 0:
                s.gold += earned
                s.stats['earned'] = s.stats.get('earned', 0) + earned
                self._last_ship_sale = (items, earned)
            bin_.clear()

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
            # Ringkasan penjualan Peti Kirim (Stardew)
            items, earned = getattr(self, '_last_ship_sale', (0, 0))
            if earned > 0:
                invoke(panels.flash_msg,
                       f"Peti Kirim: {items} hasil panen terjual — +{earned}G", 3.0, delay=2.3)
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
