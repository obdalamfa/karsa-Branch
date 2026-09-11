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
                self.player._play_tool_anim('down')
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
                self.player._play_tool_anim('water')
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
                self.player._play_tool_anim('bend')
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

            return [
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
