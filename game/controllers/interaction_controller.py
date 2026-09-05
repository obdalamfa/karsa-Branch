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

    def use_tool(self, entities_mgr, panels):
        tx, ty = self.player._facing_tile()
        self.use_tool_at(self.player.state.tool_index, tx, ty, entities_mgr, panels)

    def use_tool_at(self, tool_idx, tx, ty, entities_mgr, panels):
        from .. import care_anim
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
                self.player._spend_energy(2)
                self.world.refresh_tile(tx, ty, soil_key)
                care_anim.mulai(self.player, 'cangkul')
                self.player._fx_burst(fx, fy, fz, color.rgb(120, 82, 42))
                sound_play('hoe', 0.8)
                panels.flash_msg("Tanah dicangkul!", 0.8)
            else:
                sound_play('blocked', 0.6)

        elif tool == 'Siram':
            soil = s.soil.get(soil_key)
            if soil and soil.get('tilled') and s.energy >= 1:
                soil['watered'] = True
                self.player._spend_energy(1)
                s.stats['watered'] = s.stats.get('watered', 0) + 1
                self.world.refresh_tile(tx, ty, soil_key)
                care_anim.mulai(self.player, 'siram')
                self.player._fx_burst(fx, fy + 0.2, fz, color.rgb(60, 150, 255, 200), n=6)
                sound_play('water', 0.8)
                panels.flash_msg("Tanaman disiram!", 0.8)
                self.check_quests()
            else:
                sound_play('blocked', 0.6)

        elif tool == 'Tanam':
            soil = s.soil.get(soil_key, {})
            seed_key = s.seed_key + '_seed'
            if soil.get('tilled') and not soil.get('crop') and s.inventory.get(seed_key, 0) > 0:
                soil = s.soil.setdefault(soil_key, {})
                soil.update({'crop': s.seed_key, 'age': 0, 'tilled': True})
                s.inventory[seed_key] -= 1
                self.player._spend_energy(2)
                self.world.refresh_tile(tx, ty, soil_key)
                care_anim.mulai(self.player, 'tanam')
                self.player._fx_burst(fx, fy, fz, color.rgb(70, 200, 70), n=4)
                sound_play('plant', 0.8)
                if s.seed_key == 'lobak':
                    s.stats['lobak_planted'] = s.stats.get('lobak_planted', 0) + 1
                panels.flash_msg(f"{CROPS[s.seed_key]['name']} ditanam!", 0.8)
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
                    care_anim.mulai(self.player, 'petik')
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
                care_anim.mulai(self.player, 'tebang')
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
                care_anim.mulai(self.player, 'tambang')
                self.player._fx_burst(fx, fy + 0.3, fz, spark_col, n=8)
                sound_play('axe', 0.8)
                self.check_quests(panels)
            else:
                sound_play('blocked', 0.6)

        elif tool == 'Pedang':
            self.attack(entities_mgr, panels)

        elif tool == 'Pancing':
            self.try_fishing(panels)

    def interact(self, entities_mgr, panels):
        s = self.player.state
        tx, ty = self.player.get_tile_pos()

        if s.scene_name == 'beach' and self.try_repair_lighthouse(panels):
            return
        if s.scene_name == 'lake' and self.try_fishing(panels):
            return
        if s.scene_name == 'dungeon' and getattr(self.world, 'dungeon_level', 0) == 13 and self.try_fishing(panels):
            return
        if s.scene_name == 'clinic' and self.try_healing(panels):
            return

        # Perabot di sekitar: sumber utama pengisian motif. Dicek SEBELUM
        # perilaku tile lama supaya kasur/kompor/kursi memberi menu aksi ala
        # The Sims, bukan satu pesan tetap.
        if self.open_object_menu(panels):
            return

        npc_info = entities_mgr.get_nearest_npc(tx, ty, max_dist_tiles=3.0)
        if npc_info:
            npc_id  = npc_info['id']
            options = self.build_pie_options(npc_id)
            panels.open_pie_menu(
                npc_id, options,
                lambda nid, act: self.execute_pie_action(nid, act, entities_mgr, panels)
            )
        else:
            ftx, fty = self.player._facing_tile()
            my_tx, my_ty = self.player.get_tile_pos()
            
            from ..config import MB, ST, CL, CAL, TV, CHR, BD
            my_tid = self.world.get_tile(my_tx, my_ty)
            tid = self.world.get_tile(ftx, fty)
            
            if my_tid == CHR:
                panels.flash_msg("Kamu sedang duduk bersantai di kursi.", 1.5)
                self.player.state.energy = min(100, self.player.state.energy + 5)
                sound_play('menu_select', 0.5)
                return
            elif my_tid == BD:
                self.player._try_sleep(panels)
                return

            if tid == MB and not self.player.state.mail_read:
                self.player.state.mail_read = True
                if self.player.state.quest_stage == 0:
                    self.player.state.quest_stage = 1
                sound_play('menu_select', 0.8)
                panels.start_dialog('mailbox', self.player.state)
            elif tid == ST:
                panels.flash_msg("Kamu memasak makanan yang lezat. (+20 Energi)", 1.5)
                self.player.state.energy = min(100, self.player.state.energy + 20)
                sound_play('menu_select', 0.8)
            elif tid == CL:
                h, m = self.player.state.time_hm()
                panels.flash_msg(f"Jam menunjukkan pukul {h:02d}:{m:02d}.", 1.5)
                sound_play('menu_select', 0.8)
            elif tid == CAL:
                panels.flash_msg(f"Hari ini adalah Hari ke-{self.player.state.day} Musim {self.player.state.season_name()}.", 1.5)
                sound_play('menu_select', 0.8)
            elif tid == TV:
                panels.flash_msg("Kamu menonton acara televisi yang menarik. (+10 Senang)", 1.5)
                self.player.state.senang = min(100, getattr(self.player.state, 'senang', 100) + 10)
                sound_play('menu_select', 0.8)
            elif tid == CHR:
                panels.flash_msg("Ini kursi yang nyaman. Coba berdiri di atasnya untuk duduk.", 1.5)

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
        
        if _rng.random() < 0.55:
            if is_legendary_lake and _rng.random() < 0.25:
                s.inventory['ikan_legendaris'] = s.inventory.get('ikan_legendaris', 0) + 1
                sound_play('harvest', 0.8)
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
            panels.flash_msg("Tidak ada yang menggigit... coba lagi.", 1.0)
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
        from ..economy import shippable_items, SHIPPING_RATE
        s_ = self.player.state
        if tid == CH:
            rows  = shippable_items(s_.inventory)
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
        from ..economy import shippable_items, shipping_price, item_name
        s = self.player.state
        rows = shippable_items(s.inventory)
        if not rows:
            sound_play('blocked', 0.5)
            panels.flash_msg("Peti kosong — belum ada hasil untuk dijual.", 1.4)
            return
        total = 0
        for item, qty, _ in rows:
            total += shipping_price(item) * qty
            del s.inventory[item]
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
            from ..economy import (animal_status, pick_feed, item_name,
                                   produce_for, care_rec, EN_FEED, EN_COLLECT,
                                   EN_WATER, EN_BRUSH, FEED_DAY_VALUE, sell_price)
            from ..husbandry import (ISI_PAKAN, MIN_AIR_PRODUKSI,
                                    MIN_BERSIH_PRODUKSI)
            species = npc.get('type', '')
            siap, alasan = animal_status(s, npc_id, species)
            rec  = care_rec(s, npc_id)
            feed = pick_feed(s.inventory)
            if feed:
                boros = '' if feed in ('pakan', 'jerami') else ' (boros!)'
                feed_lbl = f'Beri Makan ({item_name(feed)}){boros}'
                feed_fx  = f'-{EN_FEED} EN, kenyang +{ISI_PAKAN}%'
            else:
                feed_lbl = 'Beri Makan (tak ada pakan)'
                feed_fx  = f'Beli Jerami {FEED_DAY_VALUE}G di Warung'

            # Label minum MENGATAKAN isi palungnya. Aturan yang tidak bisa
            # dilihat pemain bukan aturan — prinsip yang sudah dipegang
            # husbandry.py, dan angka persennya yang membuat "kenapa sapiku
            # berhenti kasih susu" bisa dijawab tanpa menebak.
            # Palung hanya ada di kandang, dan hanya hewan kandang berbagi
            # palung. Kucing dan kelinci diurus tapi tidak dikandangkan;
            # rubah liar tidak diurus sama sekali. Menawarkan "Beri Minum"
            # kepada mereka berarti menawarkan aksi terhadap benda yang tidak
            # ada — dan labelnya terpaksa mengarang keadaan palung yang tidak
            # pernah dibangun.
            from ..husbandry import is_penned
            ada_palung = getattr(self.world, 'trough', None) is not None
            tawarkan_minum = is_penned(npc_id) and ada_palung

            air = self._trough_level() if tawarkan_minum else 0
            penuh = air >= 95
            jarak = self._jarak_palung()
            jauh = jarak is not None and jarak > self.JANGKAU_PALUNG
            if penuh:
                minum_lbl = 'Beri Minum - palung masih penuh'
                minum_fx  = f'Air {air}%'
            elif jauh:
                # Ember diisi DI palung, bukan dari seberang kandang. Tanpa
                # syarat ini pemain menuang ke arah sesuatu yang berjarak lima
                # meter dan airnya melintas seperti garis lurus di udara —
                # aturan yang benar, gambar yang bohong.
                minum_lbl = f'Beri Minum - terlalu jauh dari palung ({jarak:.0f} tile)'
                minum_fx  = 'Dekati palung di kandang'
            elif air <= 0:
                minum_lbl = 'Beri Minum - palung KERING'
                minum_fx  = f'-{EN_WATER} EN, air {air}% -> 100%'
            else:
                kurang = ' (produksi terhenti)' if air < MIN_AIR_PRODUKSI else ''
                minum_lbl = f'Beri Minum - air {air}%{kurang}'
                minum_fx  = f'-{EN_WATER} EN, air {air}% -> 100%'

            prod = produce_for(species)
            ambil_fx = (f'-{EN_COLLECT} EN, +{sell_price(prod["item"])}G nilai'
                        if prod else 'Hewan ini tidak menghasilkan')
            # Label gosok menyebut kebersihan SEKARANG. Angka yang menghentikan
            # produksi harus terbaca di tempat pemain memutuskan, bukan di
            # panel terpisah yang harus dicari dulu.
            bersih = int(rec.get('bersih', 0))
            sudah_bersih = bersih >= 95
            if sudah_bersih:
                gosok_lbl = 'Gosok - bulunya masih bersih'
                gosok_fx  = f'Bersih {bersih}%'
            else:
                mampet = ' (produksi terhenti)' if bersih < MIN_BERSIH_PRODUKSI else ''
                gosok_lbl = f'Gosok - bersih {bersih}%{mampet}'
                gosok_fx  = f'-{EN_BRUSH} EN, bersih -> 100%, +1 hati'

            opsi = [
                ('belai',       'Belai',                    True,          '+8 Senang'),
                ('gosok',       gosok_lbl,          not sudah_bersih,      gosok_fx),
                ('ambil_hasil', f'Ambil Hasil - {alasan}',  siap,          ambil_fx),
                ('beri_makan',  feed_lbl,                   bool(feed),    feed_fx),
            ]
            if tawarkan_minum:
                opsi.append(
                    ('beri_minum', minum_lbl, not penuh and not jauh, minum_fx))
            return opsi

    def execute_pie_action(self, npc_id: str, action: str, entities_mgr, panels):
        from ..data import HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS
        all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
        npc   = all_d.get(npc_id, {})
        s     = self.player.state
        from ..config import NEED_MAX

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
            self.give_gift(entities_mgr, panels)
            s.sosial = min(NEED_MAX, s.sosial + 20)
        elif action == 'tanya_kabar':
            s.sosial = min(NEED_MAX, s.sosial + 8)
            s.npc_hearts[npc_id] = min(10, s.npc_hearts.get(npc_id, 0) + 1)
            pos = s.npc_positions.get(npc_id, {})
            act = pos.get('activity', 'tidak ada info')
            sound_play('menu_select', 0.7)
            panels.flash_msg(f"{npc.get('name', npc_id)}: Sekarang lagi {act}.", 2.0)
        elif action == 'amati':
            s.senang = min(NEED_MAX, s.senang + 5)
            sound_play('menu_select', 0.6)
            panels.flash_msg(f"{npc.get('name', npc_id)} tampak misterius...", 1.5)
        elif action == 'sapa_halus':
            s.sosial = min(NEED_MAX, s.sosial + 10)
            s.npc_hearts[npc_id] = min(10, s.npc_hearts.get(npc_id, 0) + 1)
            panels.start_dialog(npc_id, s)
        elif action == 'naga_riddle':
            panels.start_dialog(npc_id, s, node_key='naga_riddle_start')
        elif action == 'tawarkan':
            self.give_gift(entities_mgr, panels)
            s.senang = min(NEED_MAX, s.senang + 15)
        elif action == 'belai':
            self._belai(npc_id, npc, entities_mgr, panels)
        elif action == 'ambil_hasil':
            from ..economy import (produce_for, animal_record, animal_status,
                                   item_name, sell_price, best_process_hint,
                                   EN_COLLECT)
            species = npc.get('type', '')
            prod    = produce_for(species)
            siap, alasan = animal_status(s, npc_id, species)
            if not prod:
                panels.flash_msg(f"{npc.get('name', npc_id)} tidak menghasilkan apa-apa.", 1.2)
            elif not siap:
                sound_play('blocked', 0.5)
                panels.flash_msg(alasan, 1.4)
            elif s.energy < EN_COLLECT:
                sound_play('blocked', 0.5)
                panels.flash_msg("Terlalu lelah untuk mengurus kandang.", 1.2)
            else:
                self._panen(npc_id, npc, prod, entities_mgr, panels)
        elif action == 'gosok':
            self._gosok(npc_id, npc, entities_mgr, panels)
        elif action == 'beri_minum':
            self._beri_minum(npc_id, npc, entities_mgr, panels)
        elif action == 'beri_makan':
            # Memberi makan mengisi 'kenyang'. Hewan yang kenyang maju satu
            # langkah menuju hasil tiap pagi; yang lapar berhenti. Itu seluruh
            # aturannya — cukup untuk mengajarkan sebab-akibat, tidak cukup
            # untuk jadi simulasi peternakan.
            from ..economy import (pick_feed, animal_record, item_name,
                                   produce_for, EN_FEED, FEED_DAYS)
            feed = pick_feed(s.inventory)
            if not feed:
                sound_play('blocked', 0.5)
                panels.flash_msg("Tidak punya pakan. Beli Jerami di Warung (18G).", 1.6)
            elif s.energy < EN_FEED:
                sound_play('blocked', 0.5)
                panels.flash_msg("Terlalu lelah untuk mengurus kandang.", 1.2)
            else:
                s.inventory[feed] -= 1
                if s.inventory[feed] <= 0:
                    del s.inventory[feed]
                self.player._spend_energy(EN_FEED)
                # Kenyang ditulis ke husbandry — satu-satunya pemilik takaran
                # perawatan sejak buku ganda dibereskan. economy hanya memegang
                # siklus hasil.
                from ..husbandry import ISI_PAKAN
                from ..economy import care_rec
                crec = care_rec(s, npc_id)
                crec['kenyang'] = min(100, crec.get('kenyang', 0) + ISI_PAKAN)
                crec['hari_makan'] = s.day
                rec = animal_record(s, npc_id)
                s.npc_hearts[npc_id] = min(10, s.npc_hearts.get(npc_id, 0) + 1)
                sound_play('gift', 0.7)
                prod = produce_for(npc.get('type', ''))
                janji = (f" {item_name(prod['item'])} besok pagi."
                         if prod and rec.get('siap', 0) + 1 >= prod['cycle'] else '')
                panels.flash_msg(
                    f"{npc.get('name', npc_id)} diberi {item_name(feed)}. "
                    f"Kenyang {crec['kenyang']}%.{janji}", 1.6)





    # ─── PANEN HASIL TERNAK ─────────────────────────────────────────────────
    # Cara mengambil hasil ditentukan PRODUKNYA, bukan spesiesnya: apa pun yang
    # menghasilkan susu diperah, apa pun yang bertelur dirogoh sarangnya. Kalau
    # nanti ada spesies baru, ia otomatis memakai postur yang benar.
    CARA_PANEN = {
        'susu':        ('perah', 'Memerah'),
        'susu_kambing': ('perah', 'Memerah'),
        'telur':       ('telur', 'Mengambil telur'),
        'telur_bebek': ('telur', 'Mengambil telur'),
        'wol':         ('cukur', 'Mencukur'),
    }
    # Kapan hasilnya berpindah ke tangan, per resep. Angkanya jatuh di fase
    # ANGKAT, bukan di awal: barang yang masuk tas sebelum tangannya bergerak
    # membuat animasinya jadi hiasan yang bisa diabaikan.
    SAAT_HASIL = {'perah': 1900.0, 'telur': 1620.0, 'cukur': 2180.0}

    def _panen(self, npc_id, npc, prod, entities_mgr, panels):
        from ..economy import (animal_record, item_name, sell_price,
                               best_process_hint, EN_COLLECT)
        from .. import care_anim

        s = self.player.state
        item = prod['item']
        jenis, kata = self.CARA_PANEN.get(item, ('telur', 'Mengambil hasil'))


        pos = s.npc_positions.get(npc_id) or {}
        hx, hy = pos.get('x'), pos.get('y')
        dari, maju_ke, turun, skala = self._tempat_kerja(
            npc_id, npc, entities_mgr, jenis)

        # Tahan hewannya selama aksi. Tanpa ini domba berjalan pergi di tengah
        # pencukuran — terukur, jaraknya ke gunting naik dari 0,00 m ke median
        # 2,06 m dalam satu aksi yang sama.
        aktor = entities_mgr.actors.get(npc_id)
        if aktor is not None and hasattr(aktor, 'tahan_diam'):
            aktor.tahan_diam(3.2)

        def _frame(aksi, dt):
            self._maju(self.player, dari, maju_ke, aksi.t, 520.0)

        def _ambil(aksi):
            # Energinya ikut di sini: aksi yang dibatalkan sebelum titik ini
            # tidak menghasilkan apa-apa, jadi ia juga tidak boleh menagih apa-apa.
            self.player._spend_energy(EN_COLLECT)
            s.inventory[item] = s.inventory.get(item, 0) + 1
            animal_record(s, npc_id)['siap'] = 0
            s.stats['produce_collected'] = s.stats.get('produce_collected', 0) + 1
            care_anim.pasang_hasil(self.player)
            sound_play('harvest', 0.8)
            hint = best_process_hint(item)
            ekor = f" | {hint}" if hint else ""
            panels.flash_msg(
                f"+1 {item_name(item)} (nilai {sell_price(item)}G){ekor}", 1.6)

        aksi = care_anim.mulai(
            self.player, jenis,
            pemicu=[(self.SAAT_HASIL.get(jenis, 1800.0), _ambil)],
            saat_frame=_frame, turun=turun, skala=skala,
        )
        if aksi is None:
            # Resep hilang: jangan menelan hasilnya. Lebih baik tanpa animasi
            # daripada pemain kehilangan energi tanpa mendapat apa pun.
            _ambil(None)
            return
        panels.flash_msg(f"{kata} {npc.get('name', npc_id)}...", 1.0)


    # Tinggi punggung sapi adalah patokan resep aslinya: semua resep perawatan
    # ditulis untuk tangan yang bekerja di ketinggian itu. Hewan yang lebih
    # pendek butuh pemainnya menunduk selisihnya.
    TINGGI_PATOKAN = 1.37
    # Jangkauan dari sisi badan hewan ke ujung yang bekerja. Sikat menambah
    # panjang; telapak telanjang tidak. Memakai satu angka untuk keduanya
    # membuat aksi bertangan kosong berhenti sependek selisih itu — terukur,
    # telapak saat membelai ayam berhenti 0,11 m dari badannya, persis
    # selisih 0,62 dan 0,48.
    JANGKAU_TANGAN = 0.62      # tangan memegang alat (sikat, ember, gunting)
    JANGKAU_TELAPAK = 0.48     # tangan telanjang

    def _tempat_kerja(self, npc_id, npc, entities_mgr, jenis: str):
        """(dari, tujuan, turun, skala) — titik berdiri di rusuk hewan.

        Urutannya tidak boleh ditukar: titik rusuk dihitung dulu, pemain
        DIHADAPKAN dari titik itu, baru langkahnya dihitung. `_geser_tangan()`
        membaca pergeseran bahu kanan pada rotasi yang sedang berlaku, jadi
        menghadapkan pemain sesudah melangkah akan menggeser tangannya ke arah
        yang salah.
        """
        import math as _m
        s = self.player.state
        pos = s.npc_positions.get(npc_id) or {}
        hx, hy = pos.get('x'), pos.get('y')
        diam = (self.player.x, self.player.z)
        if hx is None:
            return diam, None, 0.0, 1.0
        geo = self._geometri_hewan(npc_id, npc, self._jangkau(jenis),
                                   self._hadap(entities_mgr, npc_id))
        if geo is None:
            self.player.rotation_y = _m.degrees(
                _m.atan2(hx - self.player.x / TS, hy - self.player.z / TS))
            self.player.target_rotation_y = self.player.rotation_y
            return diam, None, 0.0, 1.0
        tx, tz, turun, skala = geo
        self.player.rotation_y = _m.degrees(
            _m.atan2(hx - tx / TS, hy - tz / TS))
        self.player.target_rotation_y = self.player.rotation_y
        dari, tujuan = self._langkah_masuk(tx, tz)
        return dari, tujuan, turun, skala

    @staticmethod
    def _hadap(entities_mgr, npc_id: str) -> float:
        """Arah hadap hewan sekarang, dalam derajat. 0 kalau aktornya tidak ada."""
        aktor = entities_mgr.actors.get(npc_id) if entities_mgr else None
        return float(getattr(aktor, 'rotation_y', 0.0) or 0.0)

    def _jangkau(self, jenis: str) -> float:
        """Jangkauan yang benar untuk resep `jenis`, dibaca dari resepnya.

        Dulu tiap pemanggil memilih angkanya sendiri, dan satu di antaranya
        salah: mengambil telur dikerjakan bertangan kosong tapi memakai
        jangkauan bertangkai, jadi pemainnya berhenti 14 cm terlalu jauh.
        Membaca `alat` dari RESEP berarti resep baru ikut benar tanpa ada
        yang perlu ingat memperbaruinya di sini.
        """
        from .. import care_anim
        resep = care_anim.RESEP.get(jenis) or {}
        return self.JANGKAU_TANGAN if resep.get('alat') else self.JANGKAU_TELAPAK

    def _geometri_hewan(self, npc_id: str, npc: dict, jangkau: float,
                        rotasi: float = 0.0):
        """(x_rusuk, z_rusuk, kedalaman_jongkok, skala_ayunan) untuk hewan ini.

        Dua angka pertama adalah TITIK BERDIRI di rusuk hewan, bukan sekadar
        jarak. Sebelumnya fungsi ini mengembalikan pusat hewan plus sebuah
        jarak, dan pemanggilnya berdiri di sinar dari pusat itu ke tempat
        pemain kebetulan lewat — jadi sisi mana yang dipakai ditentukan oleh
        kebetulan. Diukur, sudut sisinya tersebar rata 0-180 derajat dan
        seperempat pemerahan terjadi dalam 45 derajat dari moncong sapi.
        """
        from ..animal_models import ukuran, titik_rusuk
        s = self.player.state
        pos = s.npc_positions.get(npc_id) or {}
        hx, hy = pos.get('x'), pos.get('y')
        if hx is None:
            return None
        cx, cz = hx * TS, hy * TS
        spesies = npc.get('type', '')
        _hw, _hl, tinggi = ukuran(spesies)
        # Batas 0,70 m, bukan 0,52: selisih tinggi punggung ayam (0,44 m) ke
        # sapi menuntut 0,67 m, dan batas lama memotongnya tepat di situ —
        # terukur, sapuan sikat pada ayam masih melayang di median 0,42 m
        # sementara sapi dan kambing sudah 0,05-0,12 m. Jongkok 0,70 m pada
        # karakter 1,76 m memang jongkok penuh; itu memang yang dilakukan
        # orang saat mengurus ayam.
        turun = max(0.0, min(0.70, (self.TINGGI_PATOKAN - tinggi) * 0.72))
        # Jongkok mentok di 0,70 m, jadi hewan yang jauh lebih pendek dari sapi
        # tidak bisa diselesaikan dengan menunduk saja: ayunannya juga harus
        # mengecil. Batas bawah 0,50 supaya rentang sendi tetap lewat ambang
        # 25 derajat — menggosok 73 derajat jadi 40, membelai 53 jadi 29.
        skala = max(0.50, min(1.0, tinggi / self.TINGGI_PATOKAN))
        # Jangkauan ikut mengecil bersama ayunannya. Lengan yang berayun lebih
        # pendek juga MENJULUR lebih pendek: terukur, memperkecil ayunan saja
        # menurunkan sikat ke ketinggian punggung ayam tapi menariknya 0,07-0,27 m
        # ke belakang, jadi ia lewat di atas ayam alih-alih menyentuhnya.
        tx, tz = titik_rusuk(cx, cz, spesies, rotasi,
                             self.player.x, self.player.z, jangkau * skala)
        return tx, tz, turun, skala

    def _langkah_masuk(self, tx: float, tz: float):
        """Hitung langkah pendek dari posisi sekarang ke titik berdiri (tx,tz).

        Ubin bersebelahan berjarak 2 m. Aksi perawatan yang dimulai dari ubin
        sebelah selalu terlihat seperti menyentuh udara: sikat berhenti satu
        setengah meter dari badan hewan, ember menuang ke rumput. Satu langkah
        kecil di fase pembuka menutup jarak itu — pola yang sama dipakai game
        bertani lain saat interaksi dimulai. Return (dari, tujuan); tujuan
        None kalau tidak ada yang perlu didekati.
        """
        dari = (self.player.x, self.player.z)
        if abs(tx - dari[0]) < 1e-3 and abs(tz - dari[1]) < 1e-3:
            return dari, None
        # Yang harus lurus dengan hewan adalah TANGAN YANG BEKERJA, bukan
        # pusar pemain. Semua alat perawatan menggantung di lengan kanan, jadi
        # ujung kerjanya selalu sekitar 0,30 m ke samping. Pada sapi selisih
        # itu ditelan badan yang panjangnya 2 m; pada ayam selebar 0,44 m ia
        # adalah SELURUH celahnya — terukur, tangan berhenti 0,08 m dari kotak
        # badan ayam sepanjang aksi, persis 0,30 dikurangi setengah-panjang
        # ayam 0,22. Berdirinya digeser sebanyak itu ke kiri.
        gx, gz = self._geser_tangan()
        return dari, (tx - gx, tz - gz)

    def _geser_tangan(self) -> tuple:
        """Pergeseran (dx,dz) dunia dari pusat pemain ke bahu kanannya.

        Dibaca dari rig, bukan ditulis sebagai angka tetap: kalau bahunya
        digeser suatu saat, penyelarasan ini ikut benar tanpa ada yang perlu
        ingat memperbaruinya. Pemain sudah diputar menghadap hewan sebelum ini
        dipanggil, jadi arahnya sudah benar tanpa perlu dihitung ulang.
        """
        bahu = getattr(self.player, '_pivot_shoulder_r', None)
        if bahu is None:
            return 0.0, 0.0
        try:
            w = bahu.world_position
        except Exception:
            return 0.0, 0.0
        return float(w[0]) - float(self.player.x), float(w[2]) - float(self.player.z)

    @staticmethod
    def _maju(player, dari, tujuan, t_detik: float, panjang_ms: float) -> None:
        """Terapkan langkah masuk untuk frame ini (ease-out kubik)."""
        if tujuan is None:
            return
        u = min(1.0, t_detik * 1000.0 / panjang_ms)
        e = 1.0 - (1.0 - u) ** 3
        player.x = dari[0] + (tujuan[0] - dari[0]) * e
        player.z = dari[1] + (tujuan[1] - dari[1]) * e


    # ─── BELAI ──────────────────────────────────────────────────────────────
    def _belai(self, npc_id, npc, entities_mgr, panels):
        """Sapaan pendek dua usapan. Gratis, tidak membersihkan apa pun.

        Aksi inilah yang dipakai sebagai titik nol sepanjang pekerjaan ini —
        diukur, ia dulu menghasilkan "TIDAK ADA SENDI YANG BERGERAK". Sekarang
        ia bergerak, tapi sengaja dengan bobot yang jauh lebih ringan daripada
        Gosok: separuh rentang, separuh durasi, satu tangan, tanpa alat. Kalau
        keduanya dianimasikan sama beratnya, salah satunya jadi mubazir.
        """
        from ..config import NEED_MAX
        from .. import care_anim

        s = self.player.state
        s.senang = min(NEED_MAX, s.senang + 8)
        sound_play('menu_select', 0.6)

        pos = s.npc_positions.get(npc_id) or {}
        hx, hy = pos.get('x'), pos.get('y')
        dari, maju_ke, turun, skala = self._tempat_kerja(
            npc_id, npc, entities_mgr, 'belai')

        actor = entities_mgr.actors.get(npc_id)
        if actor is not None and hasattr(actor, 'tahan_diam'):
            actor.tahan_diam(2.0)

        def _frame(aksi, dt):
            self._maju(self.player, dari, maju_ke, aksi.t, 300.0)

        def _usap(aksi):
            # Hewan mencondong ke telapak, sama seperti saat disikat — tapi
            # dipicu dua kali saja, bukan enam.
            if actor is not None and hasattr(actor, 'disikat'):
                actor.disikat(self.player.x, self.player.z)

        def _usai(aksi):
            if actor is not None and hasattr(actor, 'selesai_disikat'):
                actor.selesai_disikat()

        care_anim.mulai(
            self.player, 'belai',
            pemicu=[(430, _usap), (860, _usap)],
            saat_frame=_frame, saat_usai=_usai, turun=turun, skala=skala,
        )
        panels.flash_msg(f"Kamu membelai {npc.get('name', npc_id)}.", 1.0)

    # ─── GOSOK ──────────────────────────────────────────────────────────────
    def _gosok(self, npc_id, npc, entities_mgr, panels):
        """Sikat badan hewan: lima sapuan, hewan mencondong ke arah sikat.

        Menggosok adalah aksi perawatan yang paling sering diulang, jadi ia
        yang paling cepat terasa murah kalau cuma satu kedutan lalu pesan.
        Yang membuatnya berharga bukan angkanya — angkanya cuma `bersih` naik
        — tapi hewan yang bereaksi terhadapnya.
        """
        from ..economy import EN_BRUSH, care_rec
        from ..husbandry import clean as husb_clean, is_livestock
        from .. import care_anim

        s = self.player.state
        if not is_livestock(npc_id):
            panels.flash_msg(f"{npc.get('name', npc_id)} tidak mau disikat.", 1.4)
            return
        rec = care_rec(s, npc_id)
        if rec.get('bersih', 0) >= 95:
            sound_play('blocked', 0.5)
            panels.flash_msg("Bulunya masih bersih.", 1.2)
            return
        if s.energy < EN_BRUSH:
            sound_play('blocked', 0.5)
            panels.flash_msg("Terlalu lelah untuk menyikat.", 1.2)
            return

        sebelum = int(rec.get('bersih', 0))

        # Menghadap hewannya. Menyikat sambil membelakanginya adalah hal
        # pertama yang terlihat salah di filmstrip.
        pos = s.npc_positions.get(npc_id) or {}
        hx, hy = pos.get('x'), pos.get('y')
        actor = entities_mgr.actors.get(npc_id)
        if actor is not None and hasattr(actor, 'tahan_diam'):
            actor.tahan_diam(3.4)

        # Melangkah ke RUSUK hewan supaya sikatnya benar-benar menyentuh,
        # dan menunduk sedalam selisih tinggi punggungnya terhadap sapi.
        dari, maju_ke, turun, skala = self._tempat_kerja(
            npc_id, npc, entities_mgr, 'gosok')

        def _frame(aksi, dt):
            self._maju(self.player, dari, maju_ke, aksi.t, 420.0)

        def _sapuan(aksi):
            """Satu sapuan mendarat: bunyi + hewan mencondong ke sikat."""
            sound_play('menu_select', 0.35)
            if actor is not None and hasattr(actor, 'disikat'):
                actor.disikat(self.player.x, self.player.z)

        def _terapkan(aksi):
            # Energi ditagih DI SINI, bukan di muka. `AksiRawat.update()`
            # berhenti memanggil pemicu begitu aksi dibatalkan, jadi biaya yang
            # dibayar di muka akan mendarat pada aksi yang tidak pernah terjadi:
            # terukur, menekan W setengah detik sesudah mulai menyikat memotong
            # 2 energi, menulis "Bersih 100%, +1 hati" di HUD, dan meninggalkan
            # hewannya tetap 12% kotor tanpa satu hati pun.
            self.player._spend_energy(EN_BRUSH)
            ok, pesan = husb_clean(s, npc_id)
            if ok:
                s.npc_hearts[npc_id] = min(10, s.npc_hearts.get(npc_id, 0) + 1)
                s.stats['brushed'] = s.stats.get('brushed', 0) + 1
            panels.flash_msg(
                f"Menyikat {npc.get('name', npc_id)}. "
                f"Bersih {sebelum}% -> 100%, +1 hati.", 1.8)

        def _usai(aksi):
            if actor is not None and hasattr(actor, 'selesai_disikat'):
                actor.selesai_disikat()

        care_anim.mulai(
            self.player, 'gosok',
            # Satu pemicu per sapuan, di titik TENGAH tiap sapuan — bunyi yang
            # jatuh di titik balik terdengar seperti klik, bukan seperti bulu
            # yang menyapu.
            pemicu=[(560, _sapuan), (870, _sapuan), (1190, _sapuan),
                    (1500, _sapuan), (1830, _sapuan), (2160, _sapuan),
                    (2320, _terapkan)],
            saat_frame=_frame, saat_usai=_usai, turun=turun, skala=skala,
        )
        panels.flash_msg(f"Menyikat {npc.get('name', npc_id)}...", 1.0)

    # ─── BERI MINUM ─────────────────────────────────────────────────────────
    def _pen_livestock(self) -> list:
        """Ternak yang berbagi palung yang sama: semua ternak di scene ini.

        Palung itu milik KANDANG, bukan milik satu ekor. Mengisinya untuk satu
        sapi lalu membiarkan kambing di sebelahnya kehausan bukan cuma aneh —
        itu memaksa pemain mengulang aksi yang sama lima kali untuk satu ember.
        """
        from ..data import ANIMAL_NPCS
        from ..husbandry import is_penned
        s = self.player.state
        out = []
        for aid in ANIMAL_NPCS:
            if not is_penned(aid):
                continue
            pos = s.npc_positions.get(aid) or {}
            if pos.get('scene') == s.scene_name:
                out.append(aid)
        return out

    def _trough_level(self) -> int:
        """Isi palung = takaran air TERENDAH di kandang.

        Yang terendah, bukan rata-rata: palung yang terlihat setengah penuh
        sementara satu ekor sudah 0% akan berbohong tentang hal yang justru
        harus dilihat pemain.
        """
        from ..economy import care_rec
        s = self.player.state
        kawanan = self._pen_livestock()
        if not kawanan:
            return 0
        return int(min(care_rec(s, aid).get('air', 0) for aid in kawanan))

    JANGKAU_PALUNG = 2.6      # tile

    def _jarak_palung(self) -> float | None:
        """Jarak pemain ke palung dalam tile. None kalau kandang tak berpalung."""
        t = getattr(self.world, 'trough', None)
        if not t:
            return None
        tx, ty = t['tile']
        px, py = self.player.x / TS, self.player.z / TS
        return ((tx - px) ** 2 + (ty - py) ** 2) ** 0.5

    def sync_trough(self) -> None:
        """Samakan tinggi air palung dengan keadaan sekarang."""
        try:
            from ..scenes.props import set_trough_level
            set_trough_level(self.world, self._trough_level())
        except Exception:
            pass

    def _beri_minum(self, npc_id, npc, entities_mgr, panels):
        from ..economy import EN_WATER, care_rec
        from ..husbandry import water as husb_water, is_penned
        from ..scenes.props import trough_pour_point, set_trough_level
        from .. import care_anim

        s = self.player.state
        if not is_penned(npc_id):
            panels.flash_msg(
                f"{npc.get('name', npc_id)} tidak dikandangkan — tidak minum "
                "dari palung ternak.", 1.6)
            return
        if getattr(self.world, 'trough', None) is None:
            panels.flash_msg("Tidak ada palung minum di sini.", 1.4)
            return
        if self._trough_level() >= 95:
            sound_play('blocked', 0.5)
            panels.flash_msg("Palungnya masih penuh.", 1.2)
            return
        jarak = self._jarak_palung()
        if jarak is not None and jarak > self.JANGKAU_PALUNG:
            sound_play('blocked', 0.5)
            panels.flash_msg(
                f"Terlalu jauh dari palung ({jarak:.0f} tile). Dekati dulu.", 1.6)
            return
        if s.energy < EN_WATER:
            sound_play('blocked', 0.5)
            panels.flash_msg("Terlalu lelah untuk mengangkat ember.", 1.2)
            return

        kawanan = self._pen_livestock() or [npc_id]
        sebelum = self._trough_level()

        titik = trough_pour_point(self.world)
        if titik is None:
            # Kandang tanpa palung (scene lain): tuang di depan kaki pemain,
            # supaya aksinya tetap punya sasaran yang terlihat.
            titik = (self.player.x, 0.15, self.player.z + 0.6)
        else:
            # Bidik BIBIR palung yang paling dekat, bukan titik tengahnya.
            # Membidik tengah membuat kolom airnya melintas separuh panjang
            # palung secara mendatar; membidik bibir terdekat membuatnya jatuh.
            tx, ty, tz = titik
            titik = (tx + max(-1.0, min(1.0, self.player.x - tx)),
                     ty,
                     tz + max(-0.35, min(0.35, self.player.z - tz)))
            # Pemain menghadap palung sebelum menuang. Menuang ke samping
            # sambil menghadap ke arah lain adalah hal pertama yang terlihat
            # salah di filmstrip.
            import math as _m
            self.player.rotation_y = _m.degrees(
                _m.atan2(titik[0] - self.player.x, titik[2] - self.player.z))
            self.player.target_rotation_y = self.player.rotation_y

        aliran = care_anim.AliranAir(titik)

        # Melangkah ke bibir palung. Ubin bersebelahan berjarak 2 m, jadi
        # pemain yang berdiri di ubin sebelah menuang air melintasi jarak
        # satu setengah meter — angkanya benar, gambarnya bohong. Satu langkah
        # kecil selama fase ancang-ancang menutup jarak itu; ini pola yang
        # sama dipakai game bertani lain saat interaksi dimulai.
        pal = getattr(self.world, 'trough', None)
        dari, maju_ke = (self.player.x, self.player.z), None
        if pal is not None:
            cx, _cy, cz = pal['pos']
            # Palung tidak punya arah hadap, jadi titik berdirinya masih di
            # sinar dari pemain ke palung — 1,02 m dari pusatnya.
            ddx, ddz = self.player.x - cx, self.player.z - cz
            dd = (ddx * ddx + ddz * ddz) ** 0.5 or 1.0
            dari, maju_ke = self._langkah_masuk(cx + ddx / dd * 1.02,
                                                cz + ddz / dd * 1.02)

        def _mulai_tuang(aksi):
            aliran.nyala(True)
            sound_play('water', 0.85)

        def _isi(aksi):
            """Air benar-benar masuk saat air TERLIHAT jatuh, bukan saat menu
            diklik. Akibat yang mendahului sebabnya di layar terbaca sebagai
            bug, bahkan kalau angkanya benar.

            Energi dan pesannya ikut di sini karena alasan yang sama dari sisi
            sebaliknya: aksi yang dibatalkan sebelum titik ini tidak mengisi
            palung, jadi ia juga tidak boleh menagih ember yang tidak pernah
            terangkat."""
            self.player._spend_energy(EN_WATER)
            for aid in kawanan:
                husb_water(s, aid)
            s.stats['trough_filled'] = s.stats.get('trough_filled', 0) + 1
            for aid in kawanan:
                s.npc_hearts[aid] = min(10, s.npc_hearts.get(aid, 0) + 0.5)
            ekor = '' if len(kawanan) <= 1 else f" ({len(kawanan)} ekor ikut minum)"
            panels.flash_msg(
                f"Palung diisi untuk {npc.get('name', npc_id)}. "
                f"Air {sebelum}% -> 100%.{ekor}", 1.8)

        def _selesai_tuang(aksi):
            aliran.nyala(False)

        def _frame(aksi, dt):
            # Langkah masuk diselesaikan sebelum ember mulai miring, supaya
            # yang terlihat adalah "mendekat lalu menuang", bukan "menuang
            # sambil melayang".
            self._maju(self.player, dari, maju_ke, aksi.t, 620.0)
            prop = getattr(self.player, '_care_prop', None)
            if prop is not None and aliran.aktif:
                try:
                    wp = prop.world_position
                    aliran.perbarui((wp[0], wp[1] - 0.10, wp[2]))
                except Exception:
                    pass
            # Palung terisi BERTAHAP selama fase tuang — melompat dari kering
            # ke penuh dalam satu frame membuang satu-satunya bagian yang
            # benar-benar memuaskan untuk ditonton.
            if aksi.fase in ('tuang', 'tegak'):
                mulai_ms, panjang_ms = 1030.0, 700.0
                u = min(1.0, max(0.0, (aksi.t * 1000.0 - mulai_ms) / panjang_ms))
                set_trough_level(self.world, sebelum + (100 - sebelum) * u)

        def _usai(aksi):
            aliran.hapus()
            self.sync_trough()

        care_anim.mulai(
            self.player, 'minum',
            pemicu=[(1030.0, _mulai_tuang), (1240.0, _isi), (1760.0, _selesai_tuang)],
            saat_frame=_frame, saat_usai=_usai,
        )

        # Ternak menghampiri palung dan menunduk. Diberi jeda supaya mereka
        # bergerak SESUDAH air terlihat jatuh, bukan sebelum.
        tile = getattr(self.world, 'trough', None)
        if tile:
            tx, ty = tile['tile']
            for aid in kawanan:
                actor = entities_mgr.actors.get(aid)
                if actor is not None and hasattr(actor, 'panggil_minum'):
                    actor.panggil_minum(tx, ty, tunda=1.4)

        panels.flash_msg(f"Mengisi palung untuk {npc.get('name', npc_id)}...", 1.0)

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
