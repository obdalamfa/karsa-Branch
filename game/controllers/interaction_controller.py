import math
from ursina import color, invoke, destroy, Entity
from ..config import (
    TILE_SIZE, GROUND_H, TOOL_DAMAGE, NEED_MAX, 
    WALKABLE, TILLABLE, MINEABLE, TOOLS, 

    PLAYER_ATTACK_RANGE, PLAYER_ATTACK_COOLDOWN_MS,
    ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH, CRYS
)
from ..data import CROPS, SWORD_RECIPES, CONSUMABLES, WILD_ITEMS
from ..sound import play as sound_play

TS = TILE_SIZE

class InteractionController:
    """Handles player interactions with the world, tools, and combat."""
    
    def __init__(self, player, world):
        self.player = player
        self.world = world

    def _social(self, s, base: int) -> float:
        """Naikkan motif sosial dgn pengaruh MOOD (S4): mood bagus membuat
        interaksi lebih berbuah, mood buruk membuatnya hambar. Selalu >0
        supaya berinteraksi tak pernah sia-sia. Return delta yang diberikan."""
        from ..sims_mood import mood_social_bonus
        delta = max(1.0, base * (1.0 + mood_social_bonus(s) / 100.0))
        try:                              # tahap hidup (S10)
            from ..sims_lifestage import social_multiplier
            delta *= social_multiplier(s)
        except Exception:
            pass
        s.sosial = min(NEED_MAX, s.sosial + delta)
        return delta

    _TOOL_SKILL = {'Cangkul': ('bertani', 6.0), 'Siram': ('bertani', 4.0),
                   'Tanam': ('bertani', 6.0), 'Panen': ('bertani', 10.0),
                   'Kapak': ('kebugaran', 6.0), 'Pickaxe': ('kebugaran', 9.0),
                   'Pedang': ('kebugaran', 7.0)}

    def _tool_skill_xp(self, tool_name, panels=None):
        """Latih skill dari pemakaian alat (S6): skill naik dgn MELAKUKAN."""
        try:
            from ..sims_career import add_skill_xp, SKILLS
            ent = self._TOOL_SKILL.get(tool_name)
            if not ent:
                return
            lv, up = add_skill_xp(self.player.state, ent[0], ent[1])
            if up and panels:
                panels.flash_msg(f"Skill {SKILLS[ent[0]][0]} naik ke level {lv}!", 2.4)
        except Exception:
            pass

    def use_tool(self, entities_mgr, panels):
        tx, ty = self.player._facing_tile()
        self.use_tool_at(self.player.state.tool_index, tx, ty, entities_mgr, panels)

    def use_tool_at(self, tool_idx, tx, ty, entities_mgr, panels):
        s = self.player.state
        tool = TOOLS[tool_idx] if tool_idx < len(TOOLS) else 'Cangkul'
        sc_name = s.scene_name
        soil_key = f"{tx},{ty},{sc_name}"
        tid = self.world.get_tile(tx, ty)

        fx, fz = tx * TS, ty * TS
        fy = GROUND_H + 0.4

        if tool == 'Cangkul':
            if tid in TILLABLE and s.energy >= 2:
                soil = s.soil.setdefault(soil_key, {})
                soil['tilled'] = True
                soil.setdefault('nutrients', 3)     # Sakuna: kesuburan tanah
                soil['weeds'] = 0
                s.stats['tilled'] = s.stats.get('tilled', 0) + 1
                self.player._spend_energy(2)
                self.world.refresh_tile(tx, ty, soil_key)
                self.player._play_tool_anim('hoe')
                self.player._fx_burst(fx, fy, fz, color.rgb(120, 82, 42))
                sound_play('hoe', 0.8)
                panels.flash_msg("Tanah dicangkul!", 0.8)
                panels.say_batin_once('cangkul', 'akar',
                    "Bagus. Balik yang gelap ke bawah cahaya. Tiap negeri besar dimulai begini: satu mata bajak, satu larik.")
                self._batin_first_morning(panels)
            else:
                sound_play('blocked', 0.6)

        elif tool == 'Siram':
            soil = s.soil.get(soil_key)
            if soil and soil.get('tilled') and s.energy >= 1:
                soil['watered'] = True
                self.player._spend_energy(1)
                s.stats['watered'] = s.stats.get('watered', 0) + 1
                self.world.refresh_tile(tx, ty, soil_key)
                self.player._play_tool_anim('water')
                self.player._fx_burst(fx, fy + 0.2, fz, color.rgb(60, 150, 255, 200), n=6)
                sound_play('water', 0.8)
                panels.emote('~ ~', color.rgb(110, 180, 240))
                panels.flash_msg("Tanaman disiram!", 0.8)
                panels.say_batin_once('siram', 'akar',
                    "Genangi tunas muda, keringkan saat menua. Air itu jadwal, bukan suasana hati.")
                self.check_quests()
            else:
                sound_play('blocked', 0.6)

        elif tool == 'Tanam':
            soil = s.soil.get(soil_key, {})
            seed_key = s.seed_key + '_seed'
            if soil.get('tilled') and not soil.get('crop') and s.inventory.get(seed_key, 0) > 0:
                soil = s.soil.setdefault(soil_key, {})
                soil.update({'crop': s.seed_key, 'age': 0, 'tilled': True, 'quality': 3.0})
                s.inventory[seed_key] -= 1
                self.player._spend_energy(2)
                self.world.refresh_tile(tx, ty, soil_key)
                self.player._play_tool_anim('bend')
                self.player._fx_burst(fx, fy, fz, color.rgb(70, 200, 70), n=4)
                sound_play('plant', 0.8)
                if s.seed_key == 'lobak':
                    s.stats['lobak_planted'] = s.stats.get('lobak_planted', 0) + 1
                panels.emote('\\v/', color.rgb(140, 215, 110))
                panels.flash_msg(f"{CROPS[s.seed_key]['name']} ditanam!", 0.8)
                panels.say_batin_once('tanam', 'sukma',
                    "Benih adalah jurus tersegel. Sawah adalah kitab ajiannya. Baca pelan-pelan.")
            else:
                sound_play('blocked', 0.6)

        elif tool == 'Panen':
            soil = s.soil.get(soil_key)
            if soil and soil.get('crop'):
                crop_data = CROPS.get(soil['crop'], {})
                if soil.get('age', 0) >= crop_data.get('days', 4):
                    crop_name = soil['crop']
                    s.inventory[crop_name] = s.inventory.get(crop_name, 0) + 1
                    # Panen TIDAK lagi langsung mencetak emas. Dulu baris ini
                    # menambah gold DAN menaruh barangnya di tas sekaligus,
                    # jadi hasil panen tidak punya harga yang berarti dan
                    # menjual tidak pernah ada gunanya. Sekarang panen
                    # menghasilkan BARANG; emas datang dari menjualnya —
                    # di Warung (harga penuh) atau Peti Kirim kebun (85%).
                    from ..economy import sell_price, best_process_hint
                    nilai = sell_price(crop_name)
                    if crop_name == 'lobak':
                        s.stats['lobak_harvested'] = s.stats.get('lobak_harvested', 0) + 1
                    s.stats['harvested'] = s.stats.get('harvested', 0) + 1
                    del s.soil[soil_key]
                    self.player._spend_energy(2)
                    s.senang = min(NEED_MAX, s.senang + 8)
                    self.world.refresh_tile(tx, ty, soil_key)
                    self.player._play_tool_anim('bend')
                    self.player._fx_burst(fx, fy + 0.3, fz, color.rgb(255, 225, 50), n=7)
                    sound_play('harvest', 0.8)
                    hint = best_process_hint(crop_name)
                    ekor = f" | {hint}" if hint else ""
                    panels.flash_msg(
                        f"+1 {CROPS[crop_name]['name']} (nilai {nilai}G){ekor}", 1.6)
                    self.check_quests(panels)
                else:
                    sound_play('blocked', 0.6)
                    panels.flash_msg("Belum siap panen.", 0.8)

        elif tool == 'Hadiah':
            self.player.give_gift(entities_mgr, panels)

        elif tool == 'Kapak':
            from ..config import TR, DT, G, D, CV_F
            if tid in (TR, DT) and s.energy >= 2:
                s.inventory['kayu'] = s.inventory.get('kayu', 0) + 1
                panels.flash_msg("+1 Kayu", 0.8)
                try:
                    self.player._animate_falling_tree(fx, fz, tid)
                except Exception: pass
                if s.scene_name == 'dungeon':
                    s.dungeon_tiles[ty][tx] = CV_F
                else:
                    sc = self.world.scene_obj
                    sc.tiles[ty][tx] = G if tid == TR else D
                self.world.load_scene(s.scene_name)
                self.player._spend_energy(2)
                self.player._play_tool_anim('swing')
                self.player._fx_burst(fx, fy + 0.5, fz, color.rgb(185, 135, 72), n=6)
                sound_play('axe', 0.8)
                self.check_quests(panels)
            else:
                sound_play('blocked', 0.6)

        elif tool == 'Pickaxe':
            if tid in MINEABLE and s.pickaxe_tier > 0 and s.energy >= 2:
                ore_map = {
                    ORE_TBG: 'tembaga', ORE_BSI: 'besi', ORE_EMS: 'emas',
                    ORE_KRS: 'kristal', ORE_MTH: 'mithril', CRYS: 'kristal',
                }
                mineral = ore_map.get(tid)
                spark_col = {
                    'tembaga': color.rgb(200, 120, 55),
                    'besi':    color.rgb(180, 180, 200),
                    'emas':    color.rgb(255, 225, 60),
                    'kristal': color.rgb(200, 155, 255),
                    'mithril': color.rgb(148, 235, 255),
                }.get(mineral, color.rgb(140, 130, 118))
                if mineral:
                    s.inventory[mineral] = s.inventory.get(mineral, 0) + 1
                    s.stats['minerals_mined'] = s.stats.get('minerals_mined', 0) + 1
                    panels.flash_msg(f"+1 {mineral.capitalize()}", 0.8)
                if s.scene_name == 'dungeon':
                    if 0 <= ty < len(s.dungeon_tiles) and 0 <= tx < len(s.dungeon_tiles[0]):
                        s.dungeon_tiles[ty][tx] = 30 # MINED
                        self.world.load_scene(s.scene_name)
                else:
                    sc = self.world.scene_obj
                    if 0 <= tx < sc.w and 0 <= ty < sc.h:
                        sc.tiles[ty][tx] = 30 # MINED
                        self.world.load_scene(s.scene_name)
                self.player._spend_energy(2)
                self.player._play_tool_anim('mine')
                self.player._fx_burst(fx, fy + 0.3, fz, spark_col, n=8)
                sound_play('axe', 0.8)
                self.check_quests(panels)
            else:
                sound_play('blocked', 0.6)

        elif tool == 'Pedang':
            self.attack(entities_mgr, panels)

        elif tool == 'Pancing':
            self.try_fishing(panels)

        # Skill naik dgn MELAKUKAN (S6) — di AKHIR, setelah seluruh rantai alat.
        self._tool_skill_xp(tool, panels)

    def interact(self, entities_mgr, panels):
        s = self.player.state
        tx, ty = self.player.get_tile_pos()

        if s.scene_name == 'beach' and self.try_repair_lighthouse(panels):
            return
        if s.scene_name == 'beach' and self.try_sail(panels):
            return
        if s.scene_name == 'lake' and self.try_fishing(panels):
            return
        if s.scene_name == 'dungeon' and getattr(self.world, 'dungeon_level', 0) == 13 and self.try_fishing(panels):
            return
        if s.scene_name == 'clinic' and self.try_healing(panels):
            return
        if self._try_shipping_bin(panels):  # Peti Kirim: setor hasil panen
            return
        if self._try_plot_care(panels):     # Sakuna: cabut gulma / pupuk petak di kaki
            return

        # Perabot di sekitar: sumber utama pengisian motif. Dicek SEBELUM
        # perilaku tile lama supaya kasur/kompor/kursi memberi menu aksi ala
        # The Sims, bukan satu pesan tetap.
        if self.open_object_menu(panels):
            return

        npc_info = entities_mgr.get_nearest_npc(tx, ty, max_dist_tiles=3.0)
        if npc_info:
            npc_id  = npc_info['id']
            if self._try_collect_animal(npc_id, panels):   # ternak: ambil hasil harian dulu
                return
            if npc_id == 'petapa_srimana':
                self._petapa_awaken(npc_id, entities_mgr, panels)
            options = self.build_pie_options(npc_id)
            panels.open_pie_menu(
                npc_id, options,
                lambda nid, act: self.execute_pie_action(nid, act, entities_mgr, panels)
            )
        elif self._try_harvest_wild(tx, ty, entities_mgr, panels):
            return
        else:
            ftx, fty = self.player._facing_tile()
            my_tx, my_ty = self.player.get_tile_pos()
            
            from ..config import MB, ST, CL, CAL, TV, CHR, BD
            my_tid = self.world.get_tile(my_tx, my_ty)
            tid = self.world.get_tile(ftx, fty)
            
            if my_tid == CHR:
                panels.flash_msg("Kamu sedang duduk bersantai di kursi.", 1.5)
                self.player.state.energy = min(100, self.player.state.energy + 5)
                panels.emote('+5 EN', color.rgb(130, 210, 130))
                sound_play('menu_select', 0.5)
                return
            elif my_tid == BD:
                panels.emote('Zzz', color.rgb(150, 170, 235), 1.5)
                self.player._try_sleep(panels)
                return

            # ── Objek-beraksi ala Sims (S2) ──────────────────────────────
            # Menghadap objek berkatalog → antre aksi (jalan ke objek → isi
            # motif bertahap). BD dikecualikan: tidur = maju-hari (Stardew),
            # bukan aksi motif biasa. CL/CAL info-saja, tak ada di katalog.
            from ..sims_objects import SIMS_OBJECTS as _SIMS_OBJ
            sims_act = getattr(self.player, 'sims_action', None)
            if sims_act is not None and tid in _SIMS_OBJ and tid != BD:
                if sims_act.busy:
                    sims_act.cancel(panels)
                else:
                    sims_act.start(tid, ftx, fty, panels)
                return

            if tid == MB and not self.player.state.mail_read:
                self.player.state.mail_read = True
                if self.player.state.quest_stage == 0:
                    self.player.state.quest_stage = 1
                sound_play('menu_select', 0.8)
                panels.emote('!', color.rgb(255, 220, 120))
                panels.start_dialog('mailbox', self.player.state)
            elif tid == CL:
                h = self.player.state.get_hour()
                m = int(self.player.state.time_minutes % 60)
                panels.flash_msg(f"Jam menunjukkan pukul {h:02d}:{m:02d}.", 1.5)
                sound_play('menu_select', 0.8)
            elif tid == CAL:
                panels.flash_msg(f"Hari ini adalah Hari ke-{self.player.state.day} Musim {self.player.state.get_season()}.", 1.5)
                sound_play('menu_select', 0.8)
            # ST/TV/CHR kini ditangani jalur objek-beraksi Sims di atas.

    def _petapa_awaken(self, npc_id, entities_mgr, panels):
        """Arca emas Srimana yang mematung bangkit ke wujud murka
        (Iblis-Dewa Bertangan Banyak) saat pertama kali didekati pemain."""
        actor = entities_mgr.actors.get(npc_id)
        if actor is None or getattr(actor, '_petapa_form', '') == 'galak':
            return
        from ..petapa_model import petapa_transform_galak
        if petapa_transform_galak(actor):
            panels.flash_msg("Arca emas itu BERGERAK — kedelapan lengan Srimana terbuka!", 2.5)
            panels.emote('! ! !', color.rgb(255, 120, 80), 1.8)
            sound_play('menu_select', 1.0)

    def _batin_first_morning(self, panels):
        """Skill-moment pertama (gaya Disco): saat cangkul pertama, majelis batin
        memintamu memutuskan jadi siapa. Tiap pilihan menaikkan satu suara."""
        if not getattr(panels, 'batin', None):
            return
        if not panels.batin.once('pagi_pertama'):
            return
        panels.open_batin_check(
            'PAGI PERTAMA',
            'Berdiri di lumpur yang dulu kau cibir, kau memutuskan jadi siapa?',
            [
                {'voice': 'akar', 'label': 'Petani yang kebetulan berkebatinan.',
                 'fn': lambda: panels.say_batin('akar', 'Tanah mendengarnya. Ia akan ingat.')},
                {'voice': 'sukma', 'label': 'Pesilat yang memakai jurus tertua: bertani.',
                 'fn': lambda: panels.say_batin('sukma', 'Ya. Dewa pertama adalah petani yang menolak berhenti.')},
                {'voice': 'bara', 'label': 'Senjata yang butuh diberi makan.',
                 'fn': lambda: panels.say_batin('bara', 'Jujur. Aku bisa kerja sama dengan kejujuran.')},
            ])

    def _try_collect_animal(self, npc_id, panels) -> bool:
        """Ternak produktif: ambil hasil harian (susu/telur/wol) dgn [R].
        Return True jika hasil diambil; False (sudah/ bukan ternak) → lanjut pie menu."""
        from ..data import ANIMAL_NPCS, ANIMAL_PRODUCTS
        info = ANIMAL_NPCS.get(npc_id)
        if not info or not info.get('product'):
            return False
        s = self.player.state
        if getattr(s, 'animals_collected', None) is None:
            s.animals_collected = []
        if npc_id in s.animals_collected:
            return False                       # sudah diambil → biarkan pie menu (belai/ngobrol)
        product = info['product']
        s.inventory[product] = s.inventory.get(product, 0) + 1
        s.animals_collected.append(npc_id)
        s.npc_hearts[npc_id] = min(10, s.npc_hearts.get(npc_id, 0) + 1)   # merawat = hati naik
        pname = ANIMAL_PRODUCTS.get(product, {}).get('name', product)
        sound_play('harvest', 0.7)
        panels.emote('+1', color.rgb(255, 240, 180))
        panels.flash_msg(f"Dapat {pname} dari {info['name']}! Kirim ke Peti untuk dijual.", 2.0)
        panels.say_batin_once('ternak', 'lapar',
            "Hewan memberi kalau kau memberi dulu. Susu, telur, wol — bunga dari kesabaran.")
        return True

    def _try_shipping_bin(self, panels) -> bool:
        """Peti Kirim (Stardew): setor hasil panen → dijual saat tidur (emas masuk fajar)."""
        s = self.player.state
        if s.scene_name != 'farm':
            return False
        from ..config import SHIP_BIN_TILE
        tx, ty = self.player.get_tile_pos()
        if abs(tx - SHIP_BIN_TILE[0]) + abs(ty - SHIP_BIN_TILE[1]) > 1:
            return False
        if getattr(s, 'ship_bin', None) is None:
            s.ship_bin = {}
        from ..data import SHIP_PRICES
        moved = 0
        for item in list(SHIP_PRICES.keys()):     # hasil panen + hasil ternak
            n = s.inventory.get(item, 0)
            if n > 0:
                s.ship_bin[item] = s.ship_bin.get(item, 0) + n
                s.inventory[item] = 0
                moved += n
        if moved > 0:
            sound_play('menu_select', 0.8)
            panels.emote('^', color.rgb(231, 178, 61))
            panels.flash_msg(f"{moved} hasil panen masuk Peti Kirim — terjual saat tidur.", 2.2)
            panels.say_batin_once('kirim', 'lapar',
                "Beras masuk peti. Saat fajar, peti jadi emas. Logistik, sayang.")
        else:
            total = sum(s.ship_bin.values())
            if total:
                panels.flash_msg(f"Peti Kirim — {total} barang menunggu fajar.", 1.4)
            else:
                panels.flash_msg("Peti Kirim kosong. Panen dulu, lalu setor di sini [R].", 1.8)
        return True

    def _try_plot_care(self, panels) -> bool:
        """Sakuna: perawatan petak di kaki pemain via [R].
        Prioritas: cabut gulma → pupuk (isi nutrisi). Return True jika menangani."""
        s = self.player.state
        tx, ty = self.player.get_tile_pos()
        key = f"{tx},{ty},{s.scene_name}"
        soil = s.soil.get(key)
        if not soil or not soil.get('crop'):
            return False
        if soil.get('weeds', 0) > 0:
            if s.energy < 2:
                sound_play('blocked', 0.6); panels.flash_msg("Terlalu lelah mencabut gulma.", 1.0); return True
            soil['weeds'] = 0
            self.player._spend_energy(2)
            sound_play('hoe', 0.6)
            panels.flash_msg("Gulma dicabut.", 0.9)
            panels.say_batin_once('gulma', 'akar',
                "Cabut gulma sebelum senja. Gulma itu padi tanpa sopan santun tapi rajinnya luar biasa.")
            return True
        if soil.get('nutrients', 3) < 4:
            if s.energy < 3:
                sound_play('blocked', 0.6); panels.flash_msg("Terlalu lelah memupuk.", 1.0); return True
            soil['nutrients'] = 4
            self.player._spend_energy(3)
            sound_play('hoe', 0.5)
            panels.emote('+', color.rgb(180, 160, 90))
            panels.flash_msg("Tanah dipupuk (+nutrisi).", 0.9)
            panels.say_batin_once('pupuk', 'lapar',
                "Yang mati memberi makan yang hidup memberi makan kau. Lembah tak buang apa pun.")
            return True
        panels.flash_msg(f"Petak sehat — mutu kini ~{round(soil.get('quality', 3.0))}★", 1.1)
        return True

    def _try_harvest_wild(self, tx: int, ty: int, entities_mgr, panels) -> bool:
        """Panen entitas liar di tile player atau tile depan (herba, beri, jamur).
        Return True jika berhasil memanen sesuatu."""
        s = self.player.state
        HARVESTABLE = {'wild_herb', 'wild_berry', 'running_mushroom', 'mandrake'}
        ftx, fty = self.player._facing_tile()
        # Cek tile depan dulu, lalu tile player sendiri
        for chk_x, chk_y in ((ftx, fty), (tx, ty)):
            result = entities_mgr.try_capture_wild(chk_x, chk_y, s,
                                                   kinds=HARVESTABLE)
            if result:
                kind, sell = result
                item_info  = WILD_ITEMS.get(kind, {})
                item_name  = item_info.get('name', kind)
                s.inventory[kind] = s.inventory.get(kind, 0) + 1
                self.player._play_tool_anim('bend')
                self.player._fx_burst(chk_x * TS, GROUND_H + 0.5, chk_y * TS,
                                      color.rgb(150, 230, 90), n=6)
                sound_play('harvest', 0.8)
                panels.emote(f'+1 {item_name}', color.rgb(170, 225, 120), 1.3)
                panels.flash_msg(f"+1 {item_name}! (jual {sell}G)", 1.4)
                self.check_quests(panels)
                return True
        return False

    def attack(self, entities_mgr, panels):
        s = self.player.state
        if self.player._attack_cd > 0:
            return
        if not s.sword_id:
            sound_play('blocked', 0.6)
            panels.flash_msg("Tidak punya pedang!", 1.0)
            return

        sword_dmg = TOOL_DAMAGE
        for r in SWORD_RECIPES:
            if r['id'] == s.sword_id:
                sword_dmg = r['damage']
                break

        tx, ty = self.player.get_tile_pos()
        killed = entities_mgr.attack_mobs(tx, ty, PLAYER_ATTACK_RANGE, sword_dmg)
        if killed:
            s.stats['mobs_killed'] = s.stats.get('mobs_killed', 0) + killed
            panels.flash_msg(f"{killed} musuh dikalahkan!", 1.0)
            self.check_quests(panels)

        self.player._attack_cd = PLAYER_ATTACK_COOLDOWN_MS
        self.player._play_tool_anim('swing')
        sound_play('sword', 0.8)
        
        ftx, fty = self.player._facing_tile()
        self.player._fx_burst(ftx * TS, GROUND_H + 0.8, fty * TS,
                       color.rgb(255, 48, 48), n=5, spread=0.5)

    def capture(self, entities_mgr, panels):
        tx, ty = self.player.get_tile_pos()
        result = entities_mgr.try_capture_wild(tx, ty, self.player.state)
        if result:
            name, sell = result
            self.player.state.captured_supernatural += 1
            self.player.state.inventory[name] = self.player.state.inventory.get(name, 0) + 1
            self.player.state.senang = min(NEED_MAX, self.player.state.senang + 20)
            sound_play('capture', 0.8)
            self.player._play_tool_anim('bend')
            panels.emote('(o)!', color.rgb(190, 230, 150), 1.4)
            panels.flash_msg(f"{name} ditangkap! (+{sell}G jika dijual)", 1.5)
            self.check_quests(panels)
        else:
            sound_play('blocked', 0.6)
            panels.flash_msg("Tidak ada yang bisa ditangkap.", 0.8)

    def consume_item(self, panels):
        s = self.player.state
        for item_name, effect in CONSUMABLES.items():
            if s.inventory.get(item_name, 0) <= 0:
                continue
            s.inventory[item_name] -= 1

            hp_gain = effect.get('heal_hp', 0)
            en_gain = effect.get('heal_energy', 0)
            s.hp     = min(s.max_hp,     s.hp     + hp_gain)
            s.energy = min(s.max_energy, s.energy + en_gain)
            s.lapar  = min(NEED_MAX,     s.lapar  + max(hp_gain, en_gain) * 0.4)

            if 'buff' in effect:
                s.buffs[effect['buff']] = effect.get('buff_ms', 10000)

            sound_play('harvest', 0.7)
            buff_note = f" [{effect['buff'].upper()}]" if 'buff' in effect else ''
            display = (CROPS.get(item_name) or WILD_ITEMS.get(item_name) or {}).get('name', item_name)
            panels.flash_msg(f"Makan {display}: +{hp_gain}HP +{en_gain}EN{buff_note}", 1.8)
            return
        sound_play('blocked', 0.5)
        panels.flash_msg("Tidak ada makanan. (V = makan)", 1.0)

    def context_prompt(self, entities_mgr) -> str:
        """Prompt kontekstual untuk HUD: apa yang bisa dilakukan SEKARANG.
        Dipanggil tiap beberapa frame dari app.update — murah & read-only."""
        s = self.player.state
        try:
            from ..config import (TILLABLE, MB, BD, ST, W, DCK, LGH_B, CHR)
            from ..data import CROPS
            tx, ty = self.player.get_tile_pos()
            ftx, fty = self.player._facing_tile()
            tid_here = self.world.get_tile(tx, ty)
            tid_face = self.world.get_tile(ftx, fty)

            # 1) NPC terdekat — aksi sosial paling utama
            npc = entities_mgr.get_nearest_npc(tx, ty, max_dist_tiles=1.8)
            if npc:
                nama = npc.get('name') or npc['id'].replace('_', ' ').title()
                return f"[R] Bicara dengan {nama}"

            # 2) Objek dunia yang dihadap
            if tid_face == MB:
                return "[R] Baca surat" if not s.mail_read else ""
            if tid_face == LGH_B:
                return "[R] Periksa mercusuar"
            if tid_here == DCK and tid_face == W and s.inventory.get('perahu', 0) > 0:
                return "[R] Berlayar ke laut lepas"
            if tid_face == W or tid_here == DCK:
                return "[R] Memancing"
            if tid_here == BD or tid_face == BD:
                return "[R] Tidur sampai besok"
            if tid_face == ST:
                return "[R] Masak (+20 Energi)"
            if tid_here == CHR:
                return "[R] Duduk santai"

            # 3) Pertanian — tergantung alat aktif & kondisi petak yang dihadap
            soil_key = f"{ftx},{fty},{s.scene_name}"
            soil = s.soil.get(soil_key) or {}
            crop = soil.get('crop')
            if crop:
                grown = soil.get('age', 0) >= CROPS.get(crop, {}).get('days', 4)
                if grown:
                    return "[SPACE] Panen!  (alat: Panen [4])"
                if not soil.get('watered'):
                    return "[SPACE] Siram tanaman  (alat: Siram [2])"
                sisa = CROPS.get(crop, {}).get('days', 4) - soil.get('age', 0)
                return f"Tanaman tumbuh — {sisa} hari lagi"
            if soil.get('tilled'):
                return "[SPACE] Tanam benih  (alat: Tanam [3])"
            if tid_face in TILLABLE:
                return "[SPACE] Cangkul tanah  (alat: Cangkul [1])"
        except Exception:
            pass
        return ""

    def try_sail(self, panels) -> bool:
        """Berlayar dari dermaga pantai dengan perahu hasil crafting.
        Butuh: berdiri di dermaga (DCK), menghadap laut, punya 'perahu'."""
        import random as _rng
        from ..config import DCK, W
        s = self.player.state
        tx, ty = self.player.get_tile_pos()
        ftx, fty = self.player._facing_tile()
        if self.world.get_tile(tx, ty) != DCK or self.world.get_tile(ftx, fty) != W:
            return False
        if s.inventory.get('perahu', 0) < 1:
            return False          # tanpa perahu → jatuh ke aksi lain (mancing)
        if s.energy < 8:
            sound_play('blocked', 0.5)
            panels.flash_msg("Terlalu lelah untuk berlayar.", 1.2)
            return True
        s.energy = max(0, s.energy - 8)
        s.time_minutes += 45      # pelayaran memakan waktu
        self.player._play_tool_anim('water')
        panels.emote('~~>', color.rgb(120, 190, 230), 1.4)
        n_ikan = _rng.randint(2, 4)
        s.inventory['ikan_laut'] = s.inventory.get('ikan_laut', 0) + n_ikan
        loot = f"{n_ikan} Ikan Laut"
        if _rng.random() < 0.18:
            s.inventory['mutiara'] = s.inventory.get('mutiara', 0) + 1
            loot += " + MUTIARA!"
        sound_play('harvest', 0.8)
        panels.flash_msg(f"Kamu berlayar ke laut lepas... pulang membawa {loot}", 3.0)
        return True

    def try_fishing(self, panels) -> bool:
        import random as _rng
        from ..config import DCK, LLY, W
        tx, ty = self.player.get_tile_pos()
        on_dock      = self.world.get_tile(tx, ty) in (DCK, LLY)
        ftx, fty     = self.player._facing_tile()
        facing_water = self.world.get_tile(ftx, fty) == W
        if not (on_dock or facing_water):
            return False

        s = self.player.state
        if s.energy < 2:
            sound_play('blocked', 0.5)
            panels.flash_msg("Terlalu lelah untuk memancing.", 1.0)
            return True

        s.energy = max(0, s.energy - 2)
        is_legendary_lake = (s.scene_name == 'dungeon' and getattr(self.world, 'dungeon_level', 0) == 13)

        chance = 0.55 + (0.20 if s.inventory.get('jala', 0) > 0 else 0)
        if _rng.random() < chance:
            if is_legendary_lake and _rng.random() < 0.25:
                s.inventory['ikan_legendaris'] = s.inventory.get('ikan_legendaris', 0) + 1
                sound_play('harvest', 0.8)
                panels.emote('><(((*>  !!', color.rgb(255, 220, 120), 1.8)
                panels.flash_msg("Luar Biasa! Dapat Ikan Legendaris!", 2.5)
            else:
                # Dulu memancing menyetor emas langsung ke dompet. Itu satu
                # aturan berbeda dari seluruh sisa permainan; sekarang SEMUA
                # hasil kerja masuk tas dulu dan baru bernilai setelah dijual.
                from ..economy import sell_price
                s.inventory['ikan'] = s.inventory.get('ikan', 0) + 1
                sound_play('harvest', 0.8)
                panels.flash_msg(f"+1 Ikan (nilai {sell_price('ikan')}G)", 1.5)
            self.check_quests(panels)
        else:
            sound_play('blocked', 0.4)
            panels.emote('. . .', color.rgb(160, 165, 170))
            panels.flash_msg("Tidak ada yang menggigit... coba lagi.", 1.0)
        self.player._play_tool_anim('water')
        return True

    def try_healing(self, panels) -> bool:
        s = self.player.state
        pos = s.npc_positions.get('raka', {})
        if pos.get('scene') != 'clinic':
            return False
        tx, ty = self.player.get_tile_pos()
        if math.hypot(pos.get('x', -99) - tx, pos.get('y', -99) - ty) > 4.0:
            return False

        missing = s.max_hp - s.hp
        if missing <= 5:
            panels.flash_msg("HP kamu sudah penuh.", 0.8)
            return True

        cost = max(10, int(missing * 0.5))
        if s.gold < cost:
            panels.flash_msg(f"Tidak cukup Gold (Butuh {cost}G)", 1.0)
            return True

        s.gold -= cost
        s.hp = s.max_hp
        panels.emote('+HP', color.rgb(140, 220, 140), 1.4)
        sound_play('menu_select', 0.8)
        panels.flash_msg(f"Dirawat oleh Pak Raka (-{cost}G)", 1.5)
        return True

    def try_repair_lighthouse(self, panels) -> bool:
        from ..config import LGH_B, LGH_F
        ftx, fty = self.player._facing_tile()
        if self.world.get_tile(ftx, fty) != LGH_B:
            return False
            
        s = self.player.state
        kayu = s.inventory.get('kayu', 0)
        tembaga = s.inventory.get('tembaga', 0)
        besi = s.inventory.get('besi', 0)
        
        req_kayu = 100
        req_tembaga = 50
        req_besi = 20
        
        if kayu < req_kayu or tembaga < req_tembaga or besi < req_besi:
            panels.flash_msg(f"Butuh: {req_kayu} Kayu, {req_tembaga} Tembaga, {req_besi} Besi", 2.0)
            sound_play('blocked', 0.6)
            return True
            
        s.inventory['kayu'] -= req_kayu
        s.inventory['tembaga'] -= req_tembaga
        s.inventory['besi'] -= req_besi
        
        s.lighthouse_fixed = True
        self.player._play_tool_anim('swing')
        panels.emote('* ! *', color.rgb(255, 215, 110), 1.6)
        self.world.scene_obj.tiles[fty][ftx] = LGH_F
        self.world.load_scene('beach')
        sound_play('magic', 0.8)
        panels.flash_msg("Mercusuar berhasil diperbaiki! Kapal Kurofune tiba!", 3.0)
        return True

    def check_quests(self, panels=None):
        if hasattr(self.player, 'quest_manager') and self.player.quest_manager:
            self.player.quest_manager.check_quest_progress(panels)
        elif hasattr(self.player, '_check_quest_progress'):
            self.player._check_quest_progress(panels)
    def give_gift(self, entities_mgr, panels):
        s = self.player.state
        tx, ty = self.player.get_tile_pos()
        info = entities_mgr.get_nearest_npc(tx, ty, max_dist_tiles=3.0)
        if not info:
            sound_play('blocked', 0.6)
            panels.flash_msg("Tidak ada NPC di dekat (G).", 0.8)
            return
        npc_id = info['id']
        from ..data import HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS
        all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
        npc = all_d.get(npc_id, {})
        gift = npc.get('gift')
        if not gift:
            sound_play('blocked', 0.6)
            panels.flash_msg("NPC ini tidak menerima hadiah.", 1.0)
            return
        if s.inventory.get(gift, 0) <= 0:
            sound_play('blocked', 0.6)
            panels.flash_msg(f"Butuh '{gift}' untuk hadiah ke {npc.get('name', npc_id)}.", 1.5)
            return

        from ..data import BRANCHING_DIALOGUES
        gift_name = gift.replace('_', ' ').title()
        npc_name = npc.get('name', npc_id)
        BRANCHING_DIALOGUES['gift_confirm']['text'] = f"Beri 1 {gift_name} sebagai hadiah ke {npc_name}?"
        panels.start_dialog(npc_id, s, node_key='gift_confirm')

    def complete_gift_gifting(self, npc_id, panels):
        s = self.player.state
        from ..data import HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS
        all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
        npc = all_d.get(npc_id, {})
        gift = npc.get('gift')
        if not gift or s.inventory.get(gift, 0) <= 0:
            return

        s.inventory[gift] -= 1
        s.npc_hearts[npc_id] = min(10, s.npc_hearts.get(npc_id, 0) + 1.0)
        s.stats['gifts'] = s.stats.get('gifts', 0) + 1
        resp = npc.get('gift_r', 'Terima kasih!')
        sound_play('gift', 0.8)
        panels.flash_msg(f"{npc.get('name', npc_id)}: {resp}  (+*)", 2.0)
        if hasattr(self.player, 'check_npc_lore_gift'):
            self.player.check_npc_lore_gift(npc_id, panels)

    def open_object_menu(self, panels) -> bool:
        """Buka menu aksi untuk perabot terdekat. True kalau ada yang dibuka.

        Menu memakai pie menu yang sama dengan NPC — pemain memilih di antara
        beberapa janji yang ditawarkan objek, persis seperti The Sims. Setiap
        pilihan menampilkan motif yang akan diisinya, jadi pemain belajar
        sebab-akibat tanpa perlu membaca panduan.
        """
        from ..objects import find_nearby
        from ..motives import LABELS, score_interaction

        tx, ty = self.player.get_tile_pos()
        hits = find_nearby(self.world, tx, ty, radius=1)
        if not hits:
            return False

        dist, ox, oy, tid, acts = hits[0]
        mv = self.player.state.mv

        options = []

        # Dua perabot punya peran EKONOMI di samping perannya sebagai pengisi
        # motif. Keduanya disisipkan di puncak menu supaya pemain menemukannya
        # tanpa membaca panduan: peti di kebun = jual cepat, kompor = olah.
        from ..config import CH, ST
        from ..economy import SHIPPING_RATE
        from ..market import shippable_items
        s_ = self.player.state
        if tid == CH:
            rows  = shippable_items(s_, s_.inventory)
            total = sum(r[2] for r in rows)
            n     = sum(r[1] for r in rows)
            options.append((
                'econ:kirim',
                f'Jual Hasil Panen ({n} barang)',
                total > 0,
                f'+{total}G  ({int(SHIPPING_RATE*100)}% harga Warung)'))
        elif tid == ST:
            options.append((
                'econ:olah', 'Olah Hasil Panen', True,
                'Ubah bahan mentah jadi barang ~40% lebih mahal'))

        for act in acts:
            # Ringkasan efek: motif apa yang naik, supaya pilihan terbaca.
            eff = ', '.join(f'+{LABELS.get(a.motive, a.motive)}'
                            for a in act.adverts if a.delta > 0)
            # Aksi tetap boleh dipilih walau motifnya sudah penuh — pemain
            # berhak melakukan hal yang tidak optimal. Skor 0 hanya berarti
            # sim tidak akan memilihnya sendiri.
            useful = score_interaction(mv, act, dist) > 0
            label = act.name if useful else f'{act.name} (belum perlu)'
            options.append((f'obj:{act.name}', label, True, eff))

        target = (ox, oy, tid)

        def _run(_id, action):
            if action == 'econ:kirim':
                self.sell_to_shipping_bin(panels)
                return
            if action == 'econ:olah':
                panels.open_panel('olahan')
                return
            name = action.split(':', 1)[1] if ':' in action else action
            for a in acts:
                if a.name == name:
                    self.enqueue_object_action(a, target, panels)
                    return

        from ..objects import object_name
        panels.open_pie_menu(f'obj:{object_name(tid)}', options, _run)
        return True

    def sell_to_shipping_bin(self, panels) -> None:
        """Peti Kirim: jual seluruh hasil kebun & ternak seharga 85%.

        Ini jalur uang yang menggantikan panen-cetak-emas yang lama. Bedanya:
        pemain MEMILIH untuk menjual, melihat berapa yang masuk, dan boleh
        menahan barangnya untuk diolah dulu. Potongan 15% adalah harga dari
        kenyamanan tidak berjalan ke Warung.
        """
        from ..economy import item_name
        from ..market import shippable_items, shipping_price, on_sold
        s = self.player.state
        rows = shippable_items(s, s.inventory)
        if not rows:
            sound_play('blocked', 0.5)
            panels.flash_msg("Peti kosong — belum ada hasil untuk dijual.", 1.4)
            return
        total = 0
        for item, qty, _ in rows:
            total += shipping_price(s, item) * qty
            del s.inventory[item]
            # Peti Kirim menekan pasar persis seperti Warung. Kalau tidak,
            # peti jadi pintu belakang untuk membuang seratus lobak tanpa
            # harganya bergerak sedikit pun.
            on_sold(s, item, qty)
        s.gold += total
        s.stats['earned'] = s.stats.get('earned', 0) + total
        sound_play('harvest', 0.9)
        teratas = ', '.join(f'{item_name(i)} x{q}' for i, q, _ in rows[:3])
        panels.flash_msg(f"Terjual: {teratas} ... +{total}G", 2.2)
        self.check_quests(panels)

    def enqueue_object_action(self, interaction, target, panels) -> None:
        """Masukkan aksi objek ke antrian pemain."""
        from ..action_queue import PRIORITY_PLAYER
        q = self.player.queue
        # Perintah pemain membatalkan pilihan otonom sim, tapi tidak
        # membatalkan perintah pemain lain yang sudah antri.
        q.drop_autonomous()
        if q.enqueue(interaction, target, PRIORITY_PLAYER):
            panels.flash_msg(f'{interaction.name}...')
        else:
            panels.flash_msg('Antrian penuh')

    # Spesies yang boleh ditunggangi. Daftar, bukan pemeriksaan `== 'kuda'`,
    # supaya menambah tunggangan lain nanti tidak perlu menyentuh logika.
    TUNGGANGAN = ('kuda',)
    def build_pie_options(self, npc_id: str) -> list:
        from ..data import HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS
        all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
        npc    = all_d.get(npc_id, {})
        hearts = self.player.state.npc_hearts.get(npc_id, 0)
        s      = self.player.state

        if npc_id in HUMAN_NPCS:
            gift_item = npc.get('gift', '')
            opts = [
                ('sapa',        'Sapa',         True,                             '+5 Sosial'),
                ('ngobrol',     'Ngobrol',       hearts >= 1,                      '+15 Sosial +1❤'),
                ('beri_hadiah', 'Beri Hadiah',   bool(s.inventory.get(gift_item)), '+20 Sosial +2❤'),
                ('tanya_kabar', 'Tanya Kabar',   hearts >= 3,                      '+8 Sosial +1❤'),
            ]
        # Import sistem relasi (sims_relationship.py) dari feature/3d-mobs.
        # Sisi visual KOSONG di sini — tidak ada yang dibuang.
            # ── Aksi asmara (S5) — butuh modal persahabatan dulu ──
            from ..sims_relationship import (ROMANCE_MIN_FRIENDSHIP, romance as _rom,
                                             romance_label as _rlabel)
            _can_rom = hearts >= ROMANCE_MIN_FRIENDSHIP
            opts.append(('puji', 'Puji', hearts >= 2, '+Sosial +❤ +sedikit ♥'))
            # ── Karier (S6): tiap NPC pemberi kerja menawarkan pekerjaan ──
            from ..sims_career import (CAREERS as _CAR, career_id as _cid,
                                       can_work_now as _cwn, promotion_status as _pstat)
            _JOB_NPC = {'arya': 'tani', 'budi': 'pandai_besi', 'sari': 'warung'}
            _job = _JOB_NPC.get(npc_id)
            if _job:
                if _cid(s) != _job:
                    opts.append(('lamar_kerja', f"Lamar: {_CAR[_job]['label']}", True,
                                 f"jam {_CAR[_job]['start']}-{_CAR[_job]['end']}"))
                else:
                    _ok_work, _why = _cwn(s)
                    opts.append(('kerja', 'Bekerja', _ok_work, _why or 'Dapat gaji harian'))
                    _can_pro, _nn, _txt = _pstat(s)
                    opts.append(('naik_pangkat', 'Minta Naik Pangkat', _can_pro, _txt))
            # Rumah tangga (S8): ajak pindah bila sudah sangat dekat
            from ..sims_household import (can_move_in as _cmi, members as _hhm,
                                          MOVE_IN_MIN_FRIENDSHIP as _MMF)
            if npc_id in _hhm(s):
                opts.append(('usir', 'Minta Pindah Keluar', True, 'keluar dari rumah tangga'))
            else:
                _ok_mv, _why_mv = _cmi(s, npc_id)
                opts.append(('ajak_pindah', 'Ajak Tinggal Bersama', _ok_mv,
                             _why_mv or f'gabung rumah tangga (min {_MMF:.0f} hati)'))
            opts.append(('gombal', 'Gombal', _can_rom,
                         f"+♥ {_rlabel(s, npc_id)}" if _can_rom
                         else f"perlu {ROMANCE_MIN_FRIENDSHIP:.0f}❤ dulu"))
            if npc_id == 'arya':
                opts.append(('arya_tanya', 'Tanya Kebun', True, '+Misteri Kebun'))
            elif npc_id == 'sari' and hearts >= 2.0:
                opts.append(('sari_gossip', 'Minta Gosip', True, '+Gosip Paman'))
            elif npc_id == 'budi':
                opts.append(('budi_riddle', 'Tantangan Logam', True, '+Ujian Logam'))
            elif npc_id == 'maya' and s.get_season_name() == 'Semi':
                q_status = s.side_quests.get('maya_strawberry')
                if q_status == 'active':
                    opts.append(('maya_quest', 'Serahkan Stroberi', bool(s.inventory.get('stroberi')), 'Quest Sampingan'))
                elif q_status != 'completed':
                    opts.append(('maya_quest', 'Quest Lukisan', True, 'Quest Sampingan'))
            return opts
        elif npc_id in SUPERNATURAL_NPCS:
            gift_item = npc.get('gift', '')
            opts = [
                ('amati',       'Amati',         True,                             '+5 Senang'),
                ('sapa_halus',  'Sapa Halus',    hearts >= 1,                      '+10 Sosial +1❤'),
                ('tawarkan',    'Tawarkan',      bool(s.inventory.get(gift_item)), '+15 Senang +2❤'),
            ]
            if npc_id == 'naga_bijak':
                opts.append(('naga_riddle', 'Ujian Kebijakan', True, '+Ujian Naga'))
            return opts
        else:
            # Ternak. Dulu 'Ambil Hasil' digerbangi hati >= 2 dan menjalankan
            # peta hasil yang kuncinya salah, jadi tidak pernah memberi apa
            # pun. Sekarang gerbangnya adalah keadaan hewan yang sebenarnya —
            # dan labelnya MENGATAKAN keadaan itu, supaya pemain tahu apa yang
            # kurang tanpa menebak.
            # Perawatan ternak sekarang lewat husbandry.py, bukan economy.py.
            # Dua sistem paralel dulu hidup berdampingan: economy menyimpan
            # {kenyang, siap} dan husbandry menyimpan {kenyang, air, bersih,
            # lalai, sakit}, keduanya di-tick tiap malam, saling tidak tahu.
            # Yang dipakai pie menu cuma economy, jadi air dan bersih meluruh
            # tanpa satu pun cara menaikkannya — terukur: hari ke-4 seluruh
            # hewan sakit permanen, karena sembuh menuntut ketiganya >= 60.
            #
            # Labelnya menyebut ANGKA keadaannya, bukan cuma nama aksi. Itu
            # satu-satunya tempat pemain bisa melihat kenapa sapinya belum
            # menghasilkan tanpa harus menebak takaran mana yang kurang.
            from ..economy import item_name, sell_price
            from ..husbandry import (care_of, care_rules, feed_item,
                                     EN_MAKAN, EN_MINUM, EN_GOSOK, EN_AMBIL,
                                     MIN_KENYANG_PRODUKSI, MIN_AIR_PRODUKSI,
                                     MIN_BERSIH_PRODUKSI)
            r   = care_rules(npc_id)
            rec = care_of(s, npc_id)
            if not r:
                return [('belai', 'Belai', True, '+8 Senang')]

            feed = feed_item(s, npc_id)
            if feed:
                feed_lbl = f'Beri Makan ({item_name(feed)}) - kenyang {rec["kenyang"]}%'
                feed_fx  = f'-{EN_MAKAN} EN, kenyang +60'
            else:
                pakan = ', '.join(r.get('pakan', [])) or '-'
                feed_lbl = f'Beri Makan - tak ada pakan (kenyang {rec["kenyang"]}%)'
                feed_fx  = f'{r["label"]} makan: {pakan}'

            haus  = rec['air'] < 95
            kotor = rec['bersih'] < 95

            if rec['sakit']:
                ambil_lbl = 'Ambil Hasil - SEDANG SAKIT'
                ambil_fx  = f'Sembuh kalau ketiganya >= 60 selama 2 hari'
            elif not r.get('produk'):
                ambil_lbl = 'Ambil Hasil - tidak menghasilkan'
                ambil_fx  = f'{r["label"]} bukan ternak penghasil'
            elif rec['produk_siap']:
                ambil_lbl = f'Ambil Hasil - {r["produk_label"]} siap'
                ambil_fx  = f'-{EN_AMBIL} EN, +{sell_price(r["produk"])}G nilai'
            else:
                sisa = max(1, r.get('tiap', 1)) - rec['produk_t']
                ambil_lbl = f'Ambil Hasil - ~{sisa} hari lagi'
                kurang = [n for n, v, m in
                          (('kenyang', rec['kenyang'], MIN_KENYANG_PRODUKSI),
                           ('air',     rec['air'],     MIN_AIR_PRODUKSI),
                           ('bersih',  rec['bersih'],  MIN_BERSIH_PRODUKSI))
                          if v < m]
                ambil_fx = (f'berhenti: {", ".join(kurang)} terlalu rendah'
                            if kurang else 'terus maju tiap pagi')

            # Hewan tunggangan dapat dua pilihan tambahan. Digantung di jalur
            # pie yang SAMA dengan aksi perawatan lain — bukan tombol baru —
            # supaya apa yang diuji harness adalah apa yang ditempuh pemain.
            from ..husbandry import species_of
            opts_naik = []
            if species_of(npc_id) in TUNGGANGAN:
                if getattr(s, 'menunggangi', None) == npc_id:
                    opts_naik.append(('turun', 'Turun', True, 'berhenti menunggang'))
                else:
                    opts_naik.append(('naik', 'Naik', not getattr(s, 'menunggangi', None),
                                      'tunggangi, jalan jadi lebih cepat'))

            return opts_naik + [
                ('belai',       'Belai',                                True,  '+8 Senang'),
                ('beri_makan',  feed_lbl,                        bool(feed),  feed_fx),
                ('beri_minum',  f'Beri Minum - air {rec["air"]}%',      haus,
                 f'-{EN_MINUM} EN, air jadi 100'),
                ('gosok',       f'Gosok - bersih {rec["bersih"]}%',    kotor,
                 f'-{EN_GOSOK} EN, bersih jadi 100, +hati'),
                ('ambil_hasil', ambil_lbl,
                 bool(rec['produk_siap'] and not rec['sakit']),         ambil_fx),
            ]

    def execute_pie_action(self, npc_id: str, action: str, entities_mgr, panels):
        from ..data import HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS
        all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
        npc   = all_d.get(npc_id, {})
        s     = self.player.state
        from ..config import NEED_MAX

        # Setiap aksi yang isinya BERBICARA memakai pose bicara yang sama —
        # didaftar di satu tempat supaya menambah aksi percakapan baru tidak
        # bisa lupa animasinya. Sebelum ini berbicara tidak menggerakkan apa
        # pun: pemain berdiri diam sementara kotak dialog muncul sendiri.
        if action in ('sapa', 'ngobrol', 'tanya_kabar', 'sapa_halus',
                      'arya_tanya', 'sari_gossip', 'budi_riddle',
                      'naga_riddle', 'maya_quest'):
            self.player._play_tool_anim('bicara', 700)

        if action == 'naik':
            hewan = entities_mgr.actors.get(npc_id) if entities_mgr else None
            if hewan is None:
                sound_play('blocked', 0.5)
                panels.flash_msg("Hewannya tidak ada di sini.", 1.2)
                return
            s.menunggangi = npc_id
            self.player.mulai_menunggang(hewan)
            sound_play('menu_select', 0.7)
            panels.flash_msg(f"Menunggangi {npc.get('name', npc_id)}.", 1.4)
            return

        if action == 'turun':
            s.menunggangi = None
            self.player.berhenti_menunggang()
            sound_play('menu_select', 0.6)
            panels.flash_msg("Turun dari tunggangan.", 1.2)
            return

        if action == 'sapa':
            s.sosial = min(NEED_MAX, s.sosial + 5)
            sound_play('menu_select', 0.7)
            panels.flash_msg(f"{npc.get('name', npc_id)}: Halo!", 1.2)
        elif action == 'ngobrol':
            s.sosial = min(NEED_MAX, s.sosial + 15)
            s.npc_hearts[npc_id] = min(10, s.npc_hearts.get(npc_id, 0) + 1)
            panels.start_dialog(npc_id, s)
        elif action == 'arya_tanya':
            panels.start_dialog(npc_id, s, node_key='arya_history_start')
        elif action == 'sari_gossip':
            panels.start_dialog(npc_id, s, node_key='sari_gossip_start')
        elif action == 'budi_riddle':
            panels.start_dialog(npc_id, s, node_key='budi_riddle_start')
        elif action == 'maya_quest':
            q_status = s.side_quests.get('maya_strawberry')
            if q_status == 'active':
                panels.start_dialog(npc_id, s, node_key='maya_quest_delivery')
            else:
                panels.start_dialog(npc_id, s, node_key='maya_quest_start')
        elif action == 'beri_hadiah':
            # `panels.emote()` dan `_social()` keduanya SUDAH ada di pohon
            # gabungan ini (panels.py:1192, berkas ini baris 22), jadi baris
            # sisi 3d-mobs bisa dipakai apa adanya dan ia mengaitkan hadiah
            # ke sistem relasi, bukan cuma menaikkan angka sosial.
            panels.emote('<3 !', color.rgb(245, 150, 170), 1.5)
            self.give_gift(entities_mgr, panels)
            self._social(s, 20)
        elif action == 'tanya_kabar':
            self._social(s, 8)
            s.npc_hearts[npc_id] = min(10, s.npc_hearts.get(npc_id, 0) + 1)
            pos = s.npc_positions.get(npc_id, {})
            act = pos.get('activity', 'tidak ada info')
            sound_play('menu_select', 0.7)
            panels.flash_msg(f"{npc.get('name', npc_id)}: Sekarang lagi {act}.", 2.0)
            # Aksi karier (sims_career.py) dari feature/3d-mobs. Sisi visual
            # KOSONG di sini: melamar kerja belum pernah ada sama sekali.
        elif action == 'lamar_kerja':
            from ..sims_career import CAREERS as _CAR, join_career
            _JOB_NPC = {'arya': 'tani', 'budi': 'pandai_besi', 'sari': 'warung'}
            _job = _JOB_NPC.get(npc_id)
            if _job and join_career(s, _job):
                c = _CAR[_job]
                sound_play('quest', 0.9)
                panels.flash_msg(
                    f"Diterima sebagai {c['ranks'][0][0]} ({c['label']})! "
                    f"Kerja jam {c['start']}:00-{c['end']}:00 di {c['scene']}.", 3.2)
        elif action == 'kerja':
            from ..sims_career import work_shift, SKILLS
            res = work_shift(s)
            if res:
                sound_play('sell', 0.9)
                panels.emote(f"+{res['pay']}G", color.rgb(255, 220, 120), 1.6)
                panels.flash_msg(
                    f"Kerja selesai sbg {res['rank']}: +{res['pay']}G "
                    f"(mood {res['mood']}, kinerja {int(res['perf']*100)}%)", 2.8)
                if res['leveled']:
                    panels.flash_msg(
                        f"Skill {SKILLS[res['skill']][0]} naik ke level {res['skill_level']}!", 2.4)
            else:
                from ..sims_career import can_work_now
                _ok, _why = can_work_now(s)
                sound_play('blocked', 0.6)
                panels.flash_msg(_why or "Tak bisa bekerja sekarang.", 2.0)
        elif action == 'naik_pangkat':
            from ..sims_career import try_promote, promotion_status
            newr = try_promote(s)
            if newr:
                sound_play('quest', 1.0)
                panels.emote('!', color.rgb(255, 230, 140), 1.8)
                panels.flash_msg(f"Selamat! Kamu naik pangkat jadi {newr}.", 3.0)
            else:
                _c, _n, _t = promotion_status(s)
                sound_play('blocked', 0.6)
                panels.flash_msg(_t, 3.0)
        elif action == 'ajak_pindah':
            from ..sims_household import move_in, summary as _hhsum
            ok, msg = move_in(s, npc_id)
            sound_play('quest' if ok else 'blocked', 0.9)
            panels.flash_msg(msg, 2.8)
            if ok:
                panels.flash_msg(_hhsum(s), 3.0)
        elif action == 'usir':
            from ..sims_household import move_out
            ok, msg = move_out(s, npc_id)
            sound_play('menu_select' if ok else 'blocked', 0.7)
            panels.flash_msg(msg, 2.4)
        elif action == 'puji':
            # Memuji: menaikkan persahabatan + sedikit asmara (bila sudah akrab)
            from ..sims_relationship import add_friendship, add_romance, summary
            self._social(s, 8)
            _df = add_friendship(s, npc_id, 0.6)
            add_romance(s, npc_id, 0.2)          # gagal diam-diam bila belum akrab
            sound_play('menu_select', 0.8)
            panels.emote('!', color.rgb(255, 225, 150))
            panels.flash_msg(f"Kamu memuji {npc.get('name', npc_id)}. ({summary(s, npc_id)})", 2.0)
        elif action == 'gombal':
            # Merayu: hanya berhasil bila cukup akrab; gagal = canggung
            from ..sims_relationship import add_romance, summary
            ok, delta, msg = add_romance(s, npc_id, 1.0)
            if ok:
                self._social(s, 10)
                sound_play('gift', 0.8)
                panels.emote('<3', color.rgb(245, 150, 170), 1.5)
                panels.flash_msg(f"Rayuanmu mengena! ({summary(s, npc_id)})", 2.2)
            else:
                sound_play('blocked', 0.6)
                panels.emote('...', color.rgb(180, 180, 180), 1.4)
                panels.flash_msg(f"{npc.get('name', npc_id)}: {msg}", 2.2)
        elif action == 'amati':
            s.senang = min(NEED_MAX, s.senang + 5)
            sound_play('menu_select', 0.6)
            panels.flash_msg(f"{npc.get('name', npc_id)} tampak misterius...", 1.5)
        elif action == 'sapa_halus':
            self._social(s, 10)
            s.npc_hearts[npc_id] = min(10, s.npc_hearts.get(npc_id, 0) + 1)
            panels.start_dialog(npc_id, s)
        elif action == 'naga_riddle':
            panels.start_dialog(npc_id, s, node_key='naga_riddle_start')
        elif action == 'tawarkan':
            self.give_gift(entities_mgr, panels)
            s.senang = min(NEED_MAX, s.senang + 15)
        elif action == 'belai':
            s.senang = min(NEED_MAX, s.senang + 8)
            sound_play('menu_select', 0.6)
            panels.flash_msg(f"Kamu membelai {npc.get('name', npc_id)}.", 1.0)
        elif action in ('ambil_hasil', 'beri_makan', 'beri_minum', 'gosok'):
            # Satu jalur untuk keempat aksi perawatan. Sebelumnya tiap aksi
            # menulis sendiri ke catatan economy.py, dan dua di antaranya —
            # air dan bersih — tidak punya aksi sama sekali sehingga meluruh
            # tanpa bisa diisi. husbandry.py yang memegang aturannya sekarang;
            # di sini tinggal biaya energi, suara, dan pesannya.
            from ..husbandry import (feed, water, clean, collect, care_of,
                                     short_status, EN_MAKAN, EN_MINUM,
                                     EN_GOSOK, EN_AMBIL)
            biaya = {'beri_makan': EN_MAKAN, 'beri_minum': EN_MINUM,
                     'gosok': EN_GOSOK, 'ambil_hasil': EN_AMBIL}[action]
            if s.energy < biaya:
                sound_play('blocked', 0.5)
                panels.flash_msg("Terlalu lelah untuk mengurus kandang.", 1.2)
                return

            nama = npc.get('name', npc_id)
            if action == 'ambil_hasil':
                ok, pesan, item, jml = collect(s, npc_id)
            elif action == 'beri_makan':
                ok, pesan = feed(s, npc_id)
            elif action == 'beri_minum':
                ok, pesan = water(s, npc_id)
            else:
                ok, pesan = clean(s, npc_id)

            if not ok:
                # Penolakan bukan kegagalan diam: husbandry mengembalikan
                # alasannya, dan alasan itulah yang ditampilkan.
                sound_play('blocked', 0.5)
                panels.flash_msg(pesan, 1.4)
                return

            self.player._spend_energy(biaya)
            if action == 'ambil_hasil':
                s.stats['produce_collected'] = s.stats.get('produce_collected', 0) + 1
                sound_play('harvest', 0.8)
                self.player._play_tool_anim('bend')
            elif action == 'gosok':
                sound_play('menu_select', 0.6)
                self.player._play_tool_anim('gosok', 900)
            else:
                sound_play('gift', 0.7)
                self.player._play_tool_anim('bend')
            panels.flash_msg(f"{nama}: {pesan}  [{short_status(s, npc_id)}]", 1.8)

    def queue_toggle(self, panels):
        tx, ty = self.player._facing_tile()
        from ..config import QUEUE_USER_DRIVEN, TOOLS
        for i, (pos, _pri) in enumerate(self.player.action_queue):
            if pos == (tx, ty):
                self.player.action_queue.pop(i)
                panels.set_queue_count(len(self.player.action_queue))
                panels.flash_msg(f"Tile dihapus dari antrian. ({len(self.player.action_queue)})", 0.8)
                return
        self.player.action_queue.append(((tx, ty), QUEUE_USER_DRIVEN))
        panels.set_queue_count(len(self.player.action_queue))
        panels.flash_msg(f"[{TOOLS[self.player.state.tool_index]}] tile ditambah. ({len(self.player.action_queue)})", 0.8)

    def queue_execute(self, entities_mgr, panels):
        if not self.player.action_queue:
            panels.flash_msg("Antrian kosong. (X=tambah, C=jalankan)", 1.0)
            return
        queue_copy = sorted(self.player.action_queue, key=lambda x: -x[1])
        self.player.action_queue.clear()
        panels.set_queue_count(0)
        tool_idx = self.player.state.tool_index
        for (pos, _pri) in queue_copy:
            self.use_tool_at(tool_idx, pos[0], pos[1], entities_mgr, panels)
        panels.flash_msg(f"{len(queue_copy)} aksi antrian selesai!", 1.2)

    def toggle_broom_flying(self, panels=None):
        self.player._is_flying = not getattr(self.player, '_is_flying', False)
        if self.player._is_flying:
            sound_play('quest', 1.0)
            if panels:
                panels.flash_msg("Sapoe Terbang Aktif! [B]", 1.5)
            if not getattr(self.player, '_broom_ent', None):
                self.player._broom_ent = Entity(parent=self.player.body, model='cylinder', 
                                         position=(0, -0.3, 0), rotation=(90, 0, 0),
                                         scale=(0.1, 2.4, 0.1), color=color.rgb(180, 110, 60))
                Entity(parent=self.player._broom_ent, model='cube',
                       position=(0, -0.5, 0), scale=(3.5, 0.25, 3.5),
                       color=color.rgb(255, 0, 255))
        else:
            sound_play('morning', 0.8)
            if panels:
                panels.flash_msg("Turun dari Sapoe Terbang.", 1.2)
            if getattr(self.player, '_broom_ent', None):
                destroy(self.player._broom_ent)
                self.player._broom_ent = None

    def trigger_slide_stunt(self, panels=None):
        s = self.player.state
        if s.energy < 15:
            sound_play('blocked', 0.6)
            if panels:
                panels.flash_msg("Stamina terlalu rendah untuk meluncur!", 1.0)
            return
        if getattr(self.player, '_slide_cooldown_ms', 0.0) > 0:
            return
            
        s.energy = max(0, s.energy - 15)
        self.player._slide_active_ms = 400.0
        self.player._slide_cooldown_ms = 1500.0
        
        rad = math.radians(self.player.rotation_y)
        impulse = 38.0
        self.player.velocity_x = math.sin(rad) * impulse
        self.player.velocity_z = math.cos(rad) * impulse
        
        sound_play('water', 1.0)
        if panels:
            panels.flash_msg("Meluncur! (-15 Energi)", 0.8)
