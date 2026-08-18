from ..config import (
    FORCE_SLEEP_HOUR, INGAME_MINUTES_PER_REAL_SECOND,
    NEED_DECAY_LAPAR, NEED_DECAY_SOSIAL, NEED_DECAY_SENANG,
    NEED_DECAY_KANDUNG, NEED_DECAY_BERSIH, NEED_MAX
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

        # Needs / Motives decay (5 motif Sims)
        ingame_dt = dt * INGAME_MINUTES_PER_REAL_SECOND
        s.lapar   = max(0.0, s.lapar   - NEED_DECAY_LAPAR   * ingame_dt)
        s.sosial  = max(0.0, s.sosial  - NEED_DECAY_SOSIAL  * ingame_dt)
        try:                              # tahap hidup (S10)
            from ..sims_lifestage import traits as _lt
            _fun_m = _lt(s)['fun_decay']; _en_m = _lt(s)['energy_decay']
        except Exception:
            _fun_m = _en_m = 1.0
        s.senang  = max(0.0, s.senang  - NEED_DECAY_SENANG * _fun_m * ingame_dt)
        if _en_m > 1.0:                   # lansia: tenaga terkuras lebih cepat
            s.energy = max(0.0, s.energy - 0.010 * (_en_m - 1.0) * ingame_dt)
        s.kandung = max(0.0, s.kandung - NEED_DECAY_KANDUNG * ingame_dt)
        s.bersih  = max(0.0, s.bersih  - NEED_DECAY_BERSIH  * ingame_dt)

        # Starvation: HP berkurang jika kelaparan mencapai 0.0
        if s.lapar <= 0.0:
            STARVE_HP_DRAIN = 0.15  # 0.15 HP per menit in-game
            s.hp = max(0.0, s.hp - STARVE_HP_DRAIN * ingame_dt)

        # "Kecelakaan" klasik Sims: kandung kemih penuh (0) → mengompol —
        # kandung lega tapi kebersihan anjlok, malu (senang turun).
        if s.kandung <= 0.0:
            s.kandung = 60.0
            s.bersih  = min(s.bersih, 15.0)
            s.senang  = max(0.0, s.senang - 15.0)
            return "Ups... kecelakaan! Kamu perlu mandi."

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
        s.lapar   = min(NEED_MAX, s.lapar  + 25)
        s.senang  = min(NEED_MAX, s.senang + 20)
        s.kandung = min(NEED_MAX, s.kandung + 60)   # sempat ke belakang semalam
        s.bersih  = max(0.0, s.bersih - 8)          # bangun agak lusuh → mandi pagi
        s.naga_fountain_used_today = False
        # Shift kerja baru tersedia tiap hari (S6)
        try:
            from ..sims_career import reset_daily
            reset_daily(s)
        except Exception:
            pass
        # Menua (S10) + keinginan harian baru & cek aspirasi (S9)
        self._last_stage_up = None
        self._last_wants = []
        self._last_aspir = None
        try:
            from ..sims_lifestage import age_one_day
            self._last_stage_up = age_one_day(s)
            if self._last_stage_up and hasattr(player, 'apply_life_stage'):
                player.apply_life_stage()      # efek langsung terasa
        except Exception:
            pass
        try:
            from ..sims_aspiration import check_wants, roll_wants, check_aspiration
            self._last_wants = check_wants(s)
            self._last_aspir = check_aspiration(s)
            roll_wants(s)
        except Exception:
            pass
        # Rumah tangga: setoran anggota + tagihan berkala (S8)
        self._last_household = None
        try:
            from ..sims_household import tick_day as _hh_tick
            self._last_household = _hh_tick(s)
        except Exception:
            pass
        # Relasi meluntur bila diabaikan (S5) — pertemanan perlu dirawat
        try:
            from ..sims_relationship import decay_relationships
            decay_relationships(s)
        except Exception:
            pass
        s.buffs.clear()
        s.animals_collected = []          # ternak siap diperah/diambil lagi

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
            from ..data import SHIP_PRICES
            earned, items = 0, 0
            for item, n in list(bin_.items()):
                earned += SHIP_PRICES.get(item, 0) * n
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
            from ursina import invoke as _inv0
            if getattr(self, '_last_stage_up', None):
                from ..sims_lifestage import stage_label
                _inv0(panels.flash_msg,
                      f"Kamu memasuki tahap hidup baru: {stage_label(self.state)}!", 3.4, delay=0.6)
            for _lbl, _g in (getattr(self, '_last_wants', None) or []):
                _inv0(panels.flash_msg, f"Keinginan tercapai: {_lbl} (+{_g}G)", 2.6, delay=1.0)
            if getattr(self, '_last_aspir', None):
                _al, _ag, _at = self._last_aspir
                _inv0(panels.flash_msg,
                      f"ASPIRASI TUNTAS: {_al}! +{_ag}G, gelar '{_at}'", 4.0, delay=1.6)
            hh = getattr(self, '_last_household', None)
            if hh:
                from ursina import invoke as _inv
                if hh.get('bill'):
                    _txt = (f"Tagihan {hh['bill']}G dibayar."
                            if not hh.get('unpaid') else
                            f"Tagihan {hh['bill']}G TAK TERBAYAR — jadi utang!")
                    _inv(panels.flash_msg, _txt, 3.0, delay=1.2)
                if hh.get('contrib'):
                    _inv(panels.flash_msg,
                         f"Anggota rumah menyetor +{hh['contrib']}G.", 2.4, delay=2.6)
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
