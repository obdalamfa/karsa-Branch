import logging
import math
import random
from pathlib import Path as _Path
from PIL import Image as _PILImg
from ursina import Ursina, camera, window, color, Vec3, Vec4, time, Entity, Texture, DirectionalLight, AmbientLight, lerp
from ursina.shaders import unlit_shader

# Fix: Override fungsi warna Ursina agar outputnya konsisten Vec4 (0.0 - 1.0).
# Ini mencegah layar & HUD terbakar warna putih karena kelebihan nilai.
color.rgb = lambda r, g, b, a=255: Vec4(r/255.0, g/255.0, b/255.0, a/255.0)
color.rgba = color.rgb

from .state import GameState
from .world import World3D
from .player import Player3D
from .entities import EntitiesManager
from .panels import UIManager
from .sky import SkyDome
from .chargen import ChargenScreen
from . import grass_shader as _grass
from .config import (SCREEN_W, SCREEN_H, CAM_LERP,
                     CAM_TARGET_LIFT, INGAME_MINUTES_PER_REAL_SECOND, FORCE_SLEEP_HOUR,
                     NEED_MAX, NEED_CRITICAL, NEED_DECAY_LAPAR, NEED_DECAY_SOSIAL, NEED_DECAY_SENANG)

# Ambang perubahan warna kabut sebelum di-push ulang ke shader semua entity.
# 1,5/255 — di bawah satu langkah warna 8-bit, jadi tidak pernah terlihat.
_FOG_EPS = 1.5 / 255.0

class GameHandler(Entity):
    """Menjembatani event update dan input Ursina ke class Game3D."""
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game

    def update(self):
        self.game.update(time.dt)

    def input(self, key):
        self.game.input(key)

class Game3D:
    def __init__(self):
        logging.info("Inisialisasi Game Engine 3D (Ursina)...")
        
        # Inisialisasi Ursina Engine
        self.app = Ursina(size=(SCREEN_W, SCREEN_H),
                          title='Lembah Karsa 3D — v0.10 [Cozy Edition]',
                          borderless=False)
        window.color = color.rgb(30, 20, 40)
        window.fps_counter.enabled = True
        
        # Pencahayaan — arah lebih datar agar detail karakter chibi terlihat
        self.sun = DirectionalLight(shadows=False)
        self.sun.look_at(Vec3(-1, -1.5, -0.8))
        # Ambient hangat: cream kekuningan (Animal Crossing golden hour feel)
        self.ambient = AmbientLight(color=color.rgb(95, 90, 78, 255))

        # Cek pipeline — skip shader=unlit_shader (GLSL) kalau Direct3D9
        _use_unlit_sh = self._is_opengl_pipeline_static()
        self._use_unlit_sh = _use_unlit_sh

        if not _use_unlit_sh:
            # D3D9: DirectionalLight/AmbientLight setLight() memicu setShaderAuto() Panda3D.
            # Setiap frame Panda3D mencoba compile GLSL → gagal di D3D9 → entity hitam.
            # Fix: cabut semua lampu dari render node agar auto-GLSL tidak pernah dipicu.
            try:
                from direct.showbase.ShowBaseGlobal import base as _p3d
                _p3d.render.clearLight()    # cabut lampu → tidak ada trigger auto-GLSL
                _p3d.render.clearShader()   # buang shader yang sudah terlanjur dibuat
                _p3d.render.setLightOff()   # global fallback: fixed-function no-light
            except Exception:
                pass

        # Setup Awan (Minecraft-style blocky clouds) melayang di atas peta
        self.clouds = []
        for _ in range(8):
            kw = dict(model='cube', transparent=True,
                      scale=(random.uniform(8, 16), 0.5, random.uniform(5, 12)),
                      position=(random.uniform(-10, 60), 25, random.uniform(-10, 60)))
            if _use_unlit_sh:
                kw['shader'] = unlit_shader
            cloud = Entity(**kw)
            if not _use_unlit_sh and hasattr(cloud, 'setLightOff'):
                cloud.setLightOff()
            self.clouds.append(cloud)

        # Setup Partikel Hujan (Object pool bergaya balok)
        self.rain_drops = []
        for _ in range(150):
            kw = dict(model='cube',
                      color=color.rgb(130, 185, 255, 160),
                      transparent=True,
                      scale=(0.04, 1.2, 0.04),
                      position=(random.uniform(-10, 50), random.uniform(2, 18),
                                random.uniform(-10, 50)),
                      enabled=False)
            if _use_unlit_sh:
                kw['shader'] = unlit_shader
            drop = Entity(**kw)
            if not _use_unlit_sh and hasattr(drop, 'setLightOff'):
                drop.setLightOff()
            self.rain_drops.append(drop)

        # Load snowflake texture (FreeSO snowflake.png particle)
        _sf_path = _Path(__file__).resolve().parent.parent / 'assets' / 'textures' / 'snowflake.png'
        _sf_tex  = None
        if _sf_path.exists():
            try:
                _sf_tex = Texture(_PILImg.open(_sf_path))
            except Exception:
                pass

        # Setup Partikel Salju (Musim Dingin — FreeSO snowflake.png)
        self.snow_drops = []
        for _ in range(80):
            kw = {'texture': _sf_tex} if _sf_tex else {}
            if _use_unlit_sh:
                kw['shader'] = unlit_shader
            drop = Entity(
                model='quad',
                color=color.rgb(220, 240, 255, 200),
                transparent=True,
                scale=(0.55, 0.55),
                position=(random.uniform(-10, 50), random.uniform(2, 18),
                          random.uniform(-10, 50)),
                enabled=False,
                **kw
            )
            if not _use_unlit_sh and hasattr(drop, 'setLightOff'):
                drop.setLightOff()
            self.snow_drops.append(drop)

        # Inisialisasi suara prosedural (pygame.mixer, tidak konflik dengan panda3d audio)
        from .sound import init_sound, build_sounds, _build_ambients, set_ambient_for_scene
        if init_sound():
            build_sounds()
            _build_ambients()

        logging.info("Memuat data Game State...")
        self.state = GameState.load() or GameState()

        logging.info("Membangun sistem UI, Dunia, dan Entitas...")
        self._needs_warned: set = set()

        self.panels = UIManager(self.state)
        self.world = World3D(self.state)
        self.entities = EntitiesManager(self.state)
        
        # Load map awal
        self.world.load_scene(self.state.scene_name)
        
        # Pendaratan awal memakai jalur yang sama dengan transisi scene.
        self._land_player_safely(self.state)

        self.entities.load_scene(self.state.scene_name)
        # Ambient loop sesuai scene awal
        try:
            set_ambient_for_scene(self.state.scene_name)
        except Exception:
            pass

        # SkyDome prosedural (FreeSO SkyDomeComponent pattern)
        self.sky = SkyDome()

        logging.info("Membangun Player...")
        self.player = Player3D(self.state, self.world)
        self.panels.player = self.player

        # Terapkan penampilan tersimpan (jika sudah pernah chargen)
        if self.state.char_name:
            self.player.apply_appearance(self.state)

        # Grass shader — terapkan ke entity rumput yang sudah dibangun
        _grass.apply_to_entities(self.world._grass_ents)
        self._grass_time = 0.0

        # Cache fog: dipakai untuk melewati setter Ursina yang mahal.
        # Wajib di-None-kan tiap ganti scene — entity baru belum pernah
        # menerima shader input fog_color dan akan tampil tanpa kabut.
        self._fog_color_terakhir = None
        self._fog_density_terakhir = None

        # Setup Kamera (Harvest Moon AWL / Third-person 3D)
        camera.orthographic = False
        camera.fov          = 60
        self.camera_yaw     = 0.0
        self.camera_pitch   = 34.0   # sudut baca ala life-sim isometrik
        self.camera_dist    = 19.0

        # Chargen — muncul jika first run (char_name kosong) atau tekan F2
        self._chargen: ChargenScreen = None
        if not self.state.char_name:
            self._open_chargen()

        # Inisialisasi lingkungan langsung sesuai waktu awal (bukan fade dari gelap)
        self._init_env()

        # Terapkan VHS/Bloom shader jika menggunakan OpenGL
        if self._use_unlit_sh:
            try:
                from .shaders.vhs_bloom import vhs_bloom_shader
                camera.shader = vhs_bloom_shader
                camera.set_shader_input('time', 0.0)
            except Exception as e:
                logging.error(f"Gagal memuat shader vhs_bloom: {e}")

        # Handler untuk Game Loop
        self.handler = GameHandler(self)

    def update(self, dt):
        s = self.state

        # Update shader time
        if getattr(self, '_use_unlit_sh', False) and camera.shader:
            camera.set_shader_input('time', self._grass_time if hasattr(self, '_grass_time') else 0.0)

        # Update UI HUD
        self.panels.update(s, dt)

        # ── MENJAUH MEMBATALKAN PIE MENU ───────────────────────────────
        # Pie menu objek dibuka dengan E dan sebelumnya hanya bisa ditutup
        # dengan memilih atau ESC. Karena mode non-'hud' membekukan pemain
        # sepenuhnya, pemain yang menekan WASD merasa game-nya menggantung —
        # persis laporan "jalan saja tidak bisa". Di The Sims, bergerak
        # memang membatalkan menu; itu afordans yang sudah dikenal orang.
        if self.panels.mode == 'pie':
            from ursina import held_keys as _hk
            if (_hk['w'] or _hk['a'] or _hk['s'] or _hk['d']
                    or _hk['up arrow'] or _hk['down arrow']
                    or _hk['left arrow'] or _hk['right arrow']):
                try:
                    self.panels.close_pie()
                except Exception:
                    self.panels.mode = 'hud'

        if self.panels.mode == 'hud':
            # ── Maju waktu in-game & Needs Decay (via TimeManager) ──
            msg = self.player.time_controller.tick(dt, self.player)
            if msg:
                self.panels.flash_msg(msg, 2.5)
            self._check_needs_warning()

            self.player.tick(dt, self.panels)
            # Update ambient BGM dynamic audio levels / scene check
            try:
                from .sound import update_ambient_dynamic
                update_ambient_dynamic(s, self.player, dt)
            except Exception as e:
                logging.error(f"Gagal update ambient dynamic: {e}")
            # Jika HP habis → pingsan, balik ke rumah, mulai hari baru
            if s.hp <= 0:
                s.scene_name = 'house'
                s.player_x, s.player_y = 7.0, 8.0
                self.player._advance_day()
                self.panels.flash_msg("Kamu pingsan! Terbangun di rumah...", 3.5)
            self.entities.update(dt)
            self.world.update(dt)

            # Cek transisi scene (misal keluar pintu / portal)
            current_scene = s.scene_name
            if current_scene != self.world.scene_name or (current_scene == 'dungeon' and getattr(self.world, 'dungeon_level', -1) != s.dungeon_level):
                import time as _time
                t_start = _time.time()
                logging.info(f"[SCENE_T] start: {self.world.scene_name} -> {current_scene} player_pos=({s.player_x},{s.player_y})")
                self.world.dungeon_level = s.dungeon_level
                t0 = _time.time()
                self.world.load_scene(current_scene)
                logging.info(f"[SCENE_T] world.load_scene: {_time.time()-t0:.3f}s")
                t0 = _time.time()
                self.entities.load_scene(current_scene)
                # Entity baru belum punya shader input fog_color/density.
                # Batalkan cache supaya frame berikutnya push ulang sekali.
                self._fog_color_terakhir = None
                self._fog_density_terakhir = None
                logging.info(f"[SCENE_T] entities.load_scene: {_time.time()-t0:.3f}s")
                self._land_player_safely(s)
                self.player.set_tile_pos(s.player_x, s.player_y)
                self.player._set_initial_rotation()

                # Snap kamera langsung ke posisi baru (mencegah trailing berputar/meluncur liar saat ganti scene)
                self._snap_camera_to_player()

                # Reset portal cooldown supaya tidak ada lock dari portal sebelumnya
                self.player._portal_cd = 0.5  # cukup buat hindari portal-ping-pong tapi tidak block movement
                self._init_env()
                _grass.apply_to_entities(self.world._grass_ents,
                                         self._grass_time, 0.06)
                logging.info(f"[SCENE_T] DONE total: {_time.time()-t_start:.3f}s now at {current_scene}({s.player_x},{s.player_y})")
                # Swap ambient loop sesuai scene baru
                try:
                    from .sound import set_ambient_for_scene
                    set_ambient_for_scene(current_scene)
                except Exception:
                    pass

            # Kamera mengikuti pemain (smooth lerp) — 3D Person Follow
            from ursina import held_keys, mouse
            
            if self.panels.mode == 'hud':
                if held_keys['right mouse']:
                    if not getattr(self, '_right_mouse_down', False):
                        self._right_mouse_down = True
                        mouse.locked = True
                    else:
                        # Menggunakan kontrol normal (non-inverted) untuk kenyamanan standard game 3D
                        self.camera_yaw -= mouse.velocity[0] * 200
                        self.camera_pitch += mouse.velocity[1] * 200
                else:
                    self._right_mouse_down = False
                    mouse.locked = False
            else:
                self._right_mouse_down = False
                mouse.locked = False

            # Kunci sudut kemiringan (pitch) agar tidak terbalik atau menembus tanah
            self.camera_pitch = max(5.0, min(80, self.camera_pitch))
            
            ideal_focus = self.player.position + Vec3(0, CAM_TARGET_LIFT, 0)
            if not hasattr(self, 'camera_focus'):
                self.camera_focus = ideal_focus

            # Smooth trailing focus point. Faktor lerp di-clamp ke 1.0 supaya
            # frame panjang (hitch / stepping manual) tidak membuat kamera
            # melewati target lalu berayun.
            k = min(1.0, CAM_LERP * 1.5 * dt)
            self.camera_focus = lerp(self.camera_focus, ideal_focus, k)

            target_cam = self.camera_focus + self._camera_offset()
            camera.position += (target_cam - camera.position) * min(1.0, CAM_LERP * dt)
            camera.look_at(self.camera_focus)
            camera.rotation_z = 0

            # Pangkas dinding yang menghalangi pandangan (wall cutaway ala Sims 1)
            self.world.update_wall_cutaway(camera.position, self.camera_focus)

            # ── Sky Dome + Grass Shader update ──────────────
            is_indoor = self.world.scene_obj.indoor if self.world.scene_obj else False
            hour = (s.time_minutes / 60.0) % 24.0
            self.sky.update(hour, s.weather, is_indoor)

            # FreeSO GrassShader.fx: update uniform time + wind per frame
            self._grass_time += dt
            wind_str = {'Cerah': 0.05, 'Berangin': 0.18, 'Badai': 0.28,
                        'Hujan': 0.12, 'Mendung': 0.06}.get(s.weather, 0.05)
            _grass.update_time(self.world._grass_ents, self._grass_time, wind_str)

            # Efek pencahayaan (Siang/Sore/Malam) dan Indoor/Outdoor
            # is_indoor sudah dihitung di atas
            is_raining = (self.state.weather in ('Hujan', 'Badai')) and not is_indoor

            if is_indoor:
                # Indoor: lampu hangat yang cukup terang (cave/rumah tidak gelap total)
                target_sun   = color.rgb(60, 55, 45, 255)
                target_amb   = color.rgb(190, 180, 200, 255)
                target_sky   = color.rgb(20, 15, 25)
                target_cloud = color.rgb(0, 0, 0, 0)
            else:
                # Catatan: ambient + sun×dot ≤ 100% agar warna tidak overflow putih
                # ambient max ~70, sun max ~185 (di floor dot≈0.82: 70/255+185/255×0.82 ≈ 87%)
                if 6 <= hour < 17:
                    # Siang: sinar matahari hangat keemasan (Animal Crossing golden feel)
                    target_sun = color.rgb(255, 248, 215) if not is_raining else color.rgb(145, 145, 158)
                    target_amb = color.rgb(95, 90, 78, 255) if not is_raining else color.rgb(62, 62, 72, 255)
                    target_sky = color.rgb(128, 205, 248) if not is_raining else color.rgb(88, 98, 115)
                    target_cloud = color.rgb(248, 248, 255, 175) if not is_raining else color.rgb(145, 148, 162, 215)
                elif 17 <= hour < 19:
                    # Senja: oranye kemerahan lembut
                    target_sun = color.rgb(255, 162, 72) if not is_raining else color.rgb(148, 95, 72)
                    target_amb = color.rgb(88, 55, 45, 255) if not is_raining else color.rgb(55, 38, 35, 255)
                    target_sky = color.rgb(248, 138, 88) if not is_raining else color.rgb(115, 82, 82)
                    target_cloud = color.rgb(255, 195, 148, 145) if not is_raining else color.rgb(135, 108, 102, 195)
                else:
                    # Malam: biru gelap lembut (bukan hitam total)
                    target_sun   = color.rgb(35, 48, 92)
                    target_amb   = color.rgb(28, 28, 52, 255)
                    target_sky   = color.rgb(18, 12, 42)
                    target_cloud = color.rgb(45, 45, 72, 75)
            
            self.sun.color = lerp(self.sun.color, target_sun, dt)
            self.ambient.color = lerp(self.ambient.color, target_amb, dt)
            window.color = lerp(window.color, target_sky, dt)
            
            from ursina import scene
            # PERF (diukur, bukan ditebak): setter `scene.fog_color` milik Ursina
            # melintasi SELURUH `scene.entities` tiap kali di-assign — memanggil
            # has_ancestor() untuk tiap entity (yang naik sampai 100 parent) lalu
            # set_shader_input untuk yang butuh. Profil di scene `town`:
            # 2104 has_ancestor + 244 set_shader_input per frame = 51,9 ms dari
            # 79,9 ms total logika (65%), hanya untuk satu baris assignment.
            # window.color di-lerp tiap frame sehingga hampir selalu bernilai
            # sama; selisih di bawah ~1,5/255 tidak mungkin terlihat mata.
            # Jadi: assign hanya kalau warnanya benar-benar berubah.
            wc = window.color
            lama_fog = self._fog_color_terakhir
            if lama_fog is None or max(abs(wc[i] - lama_fog[i]) for i in range(3)) > _FOG_EPS:
                scene.fog_color = wc
                self._fog_color_terakhir = (wc[0], wc[1], wc[2])
            # fog_density juga punya setter yang melintasi semua entity kalau
            # nilainya tuple. Di sini nilainya float dan cuma dua kemungkinan,
            # jadi cukup di-assign saat berpindah indoor/outdoor.
            dens = 0.0 if is_indoor else 0.035
            if dens != self._fog_density_terakhir:
                scene.fog_density = dens
                self._fog_density_terakhir = dens
            
            self._sync_smooth_lighting()

            # Animasi awan melayang dan transisi warnanya
            for cloud in self.clouds:
                cloud.color = lerp(cloud.color, target_cloud, dt)
                cloud.x += 1.2 * dt
                if cloud.x > 70:
                    cloud.x = -20
                    cloud.z = random.uniform(-10, 60)

            # Musim Dingin: salju gantikan hujan (FreeSO snowflake.png particles)
            is_winter   = (s.season_index == 3)
            is_snowing  = is_winter and s.weather in ('Hujan', 'Mendung', 'Badai') and not is_indoor
            is_raining_ = is_raining and not is_winter

            # Animasi Hujan
            for drop in self.rain_drops:
                drop.enabled = is_raining_
                if is_raining_:
                    drop.y -= 25 * dt
                    if drop.y < -0.5:
                        drop.x = self.player.x + random.uniform(-15, 15)
                        drop.z = self.player.z + random.uniform(-15, 15)
                        drop.y = random.uniform(10, 25)

            # Animasi Salju
            for drop in self.snow_drops:
                drop.enabled = is_snowing
                if is_snowing:
                    drop.y -= 3.2 * dt
                    drop.x += math.sin(self._grass_time * 0.9 + drop.z * 0.3) * 0.6 * dt
                    drop.rotation_z += 22 * dt
                    if drop.y < -0.5:
                        drop.x = self.player.x + random.uniform(-15, 15)
                        drop.z = self.player.z + random.uniform(-15, 15)
                        drop.y = random.uniform(10, 20)

    def input(self, key):
        # ── ESC SELALU BEKERJA ─────────────────────────────────────────
        # player.tick() hanya dipanggil kalau panels.mode == 'hud' (lihat
        # update()). Artinya mode apa pun yang macet MEMBEKUKAN pemain total:
        # tidak jalan, waktu berhenti, motif berhenti meluruh.
        #
        # Diukur di _bench/probes/probe_beku.py: mode dialog/panel/pie semuanya
        # memberi jarak tempuh 0,00 unit, dan ESC di mode 'dialog' TIDAK
        # mengembalikan ke hud — pemain terkunci selamanya tanpa jalan keluar.
        # Itu sebab laporan pemilik "jalan saja tidak bisa".
        #
        # Chargen dikecualikan: ia memang layar wajib sebelum main.
        if key == 'escape' and self.panels.mode not in ('hud', 'chargen'):
            try:
                self.panels.close_all()
            except Exception:
                pass
            self.panels.mode = 'hud'    # jaring terakhir kalau close_all lupa
            return

        # Chargen mode — semua input ke ChargenScreen
        if self.panels.mode == 'chargen':
            if self._chargen:
                self._chargen.handle_input(key)
            return

        # Intercept input saat UI / Dialog aktif
        if self.panels.mode == 'dialog':
            if self.panels.is_choice_active():
                if key in ('up arrow', 'q'):
                    self.panels.navigate_dialog_choices(-1)
                elif key in ('down arrow', 'r'):
                    self.panels.navigate_dialog_choices(1)
                elif key.isdigit() and int(key) >= 1:
                    self.panels.select_dialog_choice(int(key))
                elif key in ('space', 'e', 'enter'):
                    self.panels.confirm_dialog_choice()
            else:
                if key in ('space', 'e', 'enter'):
                    self.panels.advance_dialog()
            return

        if self.panels.mode == 'pie':
            if key in ('left arrow', 'q'):
                self.panels.navigate_pie(-1)
            elif key in ('right arrow', 'r'):
                self.panels.navigate_pie(1)
            elif key.isdigit() and int(key) >= 1:
                self.panels.navigate_pie(int(key) - 1 - self.panels._pie_selected)
                self.panels.confirm_pie()
            elif key in ('space', 'e', 'enter'):
                self.panels.confirm_pie()
            elif key == 'escape':
                self.panels.close_pie()
            return

        if self.panels.mode == 'panel':
            if key == 'escape':
                self.panels.close_all()
            elif self.panels._panel_name in ('shop', 'olahan') and key in ('tab', '0'):
                # Warung punya dua sisi (BELI/JUAL); tanpa tombol ini sisi jual
                # tidak bisa dicapai sama sekali.
                self.panels.cycle_market_mode()
            elif self.panels._panel_name in ('shop', 'olahan') and key in ('q', 'r'):
                # Input panel hanya menerima angka 1-9, jadi daftar yang lebih
                # panjang dari sembilan baris butuh halaman.
                self.panels.market_page(-1 if key == 'q' else 1)
            elif key.isdigit():
                msg = self.panels.panel_action(int(key))
                if msg:
                    self.panels.flash_msg(msg)
            return

        if self.panels.mode == 'hud':
            if key == 'left mouse down':
                # Mouse-click untuk membuka Pie Menu NPC atau melihat deskripsi tile
                from ursina import mouse
                if mouse.world_point:
                    wx, wz = mouse.world_point.x, mouse.world_point.z
                    tx, ty = int(round(wx / 2.0)), int(round(wz / 2.0))
                    npc_info = self.entities.get_nearest_npc(tx, ty, max_dist_tiles=1.5)
                    if npc_info:
                        npc_id = npc_info['id']
                        options = self.player._build_pie_options(npc_id)
                        self.panels.open_pie_menu(
                            npc_id, options,
                            lambda nid, act: self.player.execute_pie_action(nid, act, self.entities, self.panels)
                        )
                    else:
                        # Deskripsi objek jika diklik
                        tid = self.world.get_tile(tx, ty)
                        from .config import TILE_NAMES
                        obj_name = TILE_NAMES.get(tid, 'Tanah')
                        self.panels.flash_msg(f"Melihat: {obj_name.replace('_', ' ').title()}", 2.0)
                return

            # Input untuk aksi pemain (gerak/tool/serang/tangkap)
            if self.player.handle_input(key, self.entities, self.panels):
                return

            # Hotkeys menu
            if key == 'i':
                self.panels.open_panel('inventory')
            elif key == 'm':
                self.panels.open_panel('map')
            elif key == 'j':
                self.panels.open_panel('quest')
            elif key == 'h':
                self.panels.open_panel('relations')
            elif key == 'n':
                self.panels.open_panel('catatan')
            elif key == 'k':
                if self.state.scene_name == 'shop':
                    self.panels.open_panel('shop')
                else:
                    self.panels.flash_msg(
                        "Warung Bu Sari ada di Desa. Peti Kirim di kebun "
                        "membeli hasil panen 85% tanpa perlu jalan.", 2.5)
            elif key == 'o':
                # Dapur bisa dibuka dari depan kompor lewat menu perabot; ini
                # jalan pintas supaya pemain yang sudah tahu tidak perlu
                # berdiri persis di tempat yang benar.
                if self.state.scene_name in ('house', 'shop'):
                    self.panels.open_panel('olahan')
                else:
                    self.panels.flash_msg("Mengolah hasil panen dilakukan di dapur rumah.", 2.0)
            elif key == 'u':
                if self.state.scene_name == 'smith':
                    self.panels.open_panel('crafting')
                else:
                    self.panels.flash_msg("Pergi ke Bengkel Budi!")
            elif key == 'f1':
                self.panels.open_panel('help')
            elif key == 'f2':
                self._open_chargen()
            elif key == 'escape':
                # Esc di HUD: save + tampilkan pesan, jangan langsung quit
                # (klik X window untuk benar-benar tutup)
                self.state.save()
                self.panels.flash_msg("Game tersimpan. Tekan X di window untuk keluar.", 3.5)
            elif key == 'f5':
                if self.state.save():
                    self.panels.flash_msg("[F5] Game Tersimpan!")
            elif key == 'f9':
                loaded = GameState.load()
                if loaded:
                    self.state = loaded
                    self.world.load_scene(self.state.scene_name)
                    self.entities.load_scene(self.state.scene_name)
                    self.player.state = self.state
                    # Safety walkable snap check
                    if not self.world.is_walkable(int(round(self.state.player_x)), int(round(self.state.player_y))):
                        found = None
                        for r in range(1, 6):
                            for dx in range(-r, r+1):
                                for dy in range(-r, r+1):
                                    nx, ny = int(round(self.state.player_x)) + dx, int(round(self.state.player_y)) + dy
                                    if self.world.is_walkable(nx, ny):
                                        found = (nx, ny); break
                                if found: break
                            if found: break
                        if found:
                            self.state.player_x, self.state.player_y = float(found[0]), float(found[1])
                    self.player.set_tile_pos(self.state.player_x, self.state.player_y)
                    self.player._set_initial_rotation()
                    self._init_env()
                    self.panels.flash_msg("[F9] Game Dimuat!")

    # ─── CHARACTER CREATION ─────────────────────────────────
    def _open_chargen(self):
        if self._chargen:
            return
        if hasattr(self, 'player') and self.player:
            self.player.rotation_y = (self.camera_yaw + 180.0) % 360.0
        self._chargen = ChargenScreen(
            self.state,
            on_confirm=self._on_chargen_confirm,
            player=self.player,
        )
        self.panels.mode = 'chargen'

    def _on_chargen_confirm(self, state):
        self._chargen = None
        self.player.apply_appearance(state)
        if hasattr(self, 'player') and self.player:
            self.player._set_initial_rotation()
        self.state.save()
        self.panels.mode = 'hud'
        # Tutorial intro untuk first-time player
        from ursina import invoke
        self.panels.flash_msg(f'Selamat datang, {state.char_name}! Petualanganmu dimulai.', 3.5)
        invoke(self.panels.flash_msg, "Pakai WASD untuk jalan, SHIFT untuk lari.", 4.0, delay=4.0)
        invoke(self.panels.flash_msg, "SPACE pakai alat, E bicara dgn NPC, F1 untuk help.", 4.0, delay=8.5)
        invoke(self.panels.flash_msg, "Cek inventori (I), peta (M), quest (J). Selamat bermain!", 4.0, delay=13.0)

    # ─── NEEDS WARNING ──────────────────────────────────────
    def _check_needs_warning(self):
        s = self.state
        for name, val in [('lapar', s.lapar), ('sosial', s.sosial), ('senang', s.senang)]:
            if val <= NEED_CRITICAL and name not in self._needs_warned:
                label = {'lapar': 'Lapar', 'sosial': 'Kesepian', 'senang': 'Bosan'}[name]
                self.panels.flash_msg(f"[!] {label}! Needs kamu kritis.", 2.5)
                self._needs_warned.add(name)
            elif val > NEED_CRITICAL * 1.5 and name in self._needs_warned:
                self._needs_warned.discard(name)

    # ─── ENVIRONMENT INIT ───────────────────────────────────
    def _init_env(self):
        """Snap pencahayaan langsung sesuai scene & jam — dipanggil saat init dan tiap transisi scene."""
        s        = self.state
        hour     = (s.time_minutes / 60.0) % 24.0
        is_indoor= self.world.scene_obj.indoor if self.world.scene_obj else False

        if is_indoor:
            # Indoor: lampu hangat yang cukup terang supaya scene tidak gelap total
            sun_col   = color.rgb(60, 55, 45, 255)
            amb_col   = color.rgb(190, 180, 200, 255)
            sky_col   = color.rgb(20, 15, 25)
            cloud_col = color.rgb(0, 0, 0, 0)
        elif 6 <= hour < 17:
            sun_col   = color.rgb(255, 248, 215)
            amb_col   = color.rgb(95, 90, 78, 255)
            sky_col   = color.rgb(128, 205, 248)
            cloud_col = color.rgb(248, 248, 255, 175)
        elif 17 <= hour < 19:
            sun_col   = color.rgb(255, 162, 72)
            amb_col   = color.rgb(88, 55, 45, 255)
            sky_col   = color.rgb(248, 138, 88)
            cloud_col = color.rgb(255, 195, 148, 145)
        else:
            sun_col   = color.rgb(35, 48, 92)
            amb_col   = color.rgb(28, 28, 52, 255)
            sky_col   = color.rgb(18, 12, 42)
            cloud_col = color.rgb(45, 45, 72, 75)

        self.sun.color     = sun_col
        self.ambient.color = amb_col
        self._sync_smooth_lighting()
        window.color       = sky_col
        if not getattr(self, '_use_unlit_sh', True):
            try:
                from direct.showbase.ShowBaseGlobal import base as _p3d
                _p3d.render.clearLight()
                _p3d.render.clearShader()
                _p3d.render.setLightOff()
            except Exception:
                pass
        for cloud in self.clouds:
            cloud.color = cloud_col

    def _land_player_safely(self, s):
        """Tempatkan pemain di petak yang bisa dijalani pada scene yang baru.

        Kenapa perlu MENJEPIT dulu ke batas peta: koordinat pemain dibawa apa
        adanya lintas scene, jadi masuk 'house' (15x6) dari 'farm' membawa
        koordinat seperti (19,5) — sembilan belas kolom, padahal peta cuma 15.
        Pencarian melebar radius 5 yang lama tidak pernah sampai ke peta, jadi
        pemain mendarat di tile terblokir dan langsung terjepit. Terdeteksi
        otomatis oleh tools/regress.py pada scene house dan shop.
        """
        sc = self.world.scene_obj
        grid = getattr(sc, 'tiles', None)
        tx, ty = int(round(s.player_x)), int(round(s.player_y))
        if grid:
            rows, cols = len(grid), len(grid[0])
            tx = max(0, min(cols - 1, tx))
            ty = max(0, min(rows - 1, ty))
        if self.world.is_walkable(tx, ty):
            s.player_x, s.player_y = float(tx), float(ty)
            return
        # Cari melebar dari titik yang sudah dijepit, cincin demi cincin.
        span = max(len(grid[0]), len(grid)) if grid else 12
        for r in range(1, span + 1):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    nx, ny = tx + dx, ty + dy
                    if self.world.is_walkable(nx, ny):
                        logging.warning(
                            f"[SCENE_T] petak pendaratan terblokir, pindah ke ({nx},{ny})")
                        s.player_x, s.player_y = float(nx), float(ny)
                        return
        logging.error("[SCENE_T] tidak ada petak yang bisa dijalani di scene ini")

    def _camera_offset(self) -> Vec3:
        """Vektor offset kamera dari titik fokus, dari yaw/pitch/dist saat ini."""
        cy = math.radians(self.camera_yaw)
        cp = math.radians(self.camera_pitch)
        return Vec3(math.sin(cy) * math.cos(cp),
                    math.sin(cp),
                    -math.cos(cy) * math.cos(cp)) * self.camera_dist

    def _snap_camera_to_player(self):
        """Tempatkan kamera langsung di posisi idealnya, tanpa lerp.

        Dipakai saat ganti scene dan oleh harness tangkapan layar — tanpa ini
        kamera perlu ~1 detik dt untuk konvergen, jadi frame awal selalu salah.
        """
        self.camera_focus = self.player.position + Vec3(0, CAM_TARGET_LIFT, 0)
        camera.position = self.camera_focus + self._camera_offset()
        camera.look_at(self.camera_focus)
        camera.rotation_z = 0
        self.world.update_wall_cutaway(camera.position, self.camera_focus)

    @staticmethod
    def _is_opengl_pipeline_static() -> bool:
        """True kalau Panda3D pakai pipeline OpenGL (support GLSL).
        Dipanggil saat init untuk skip shader GLSL di Direct3D9."""
        try:
            from direct.showbase.ShowBaseGlobal import base
            return 'gl' in base.pipe.get_type().get_name().lower()
        except Exception:
            return True

    def _sync_smooth_lighting(self):
        """Sinkronisasi uniform sm_sun_color / sm_ambient ke scene root.
        Propagasi otomatis ke semua entity yang pakai smooth_shader."""
        try:
            from ursina import scene
            sun_c = self.sun.color
            amb_c = self.ambient.color
            scene.set_shader_input('sm_sun_color',
                                   Vec3(sun_c.x, sun_c.y, sun_c.z))
            scene.set_shader_input('sm_ambient',
                                   Vec3(amb_c.x, amb_c.y, amb_c.z))
            # Sun direction mengikuti DirectionalLight (arah look_at)
            scene.set_shader_input('sm_sun_dir', Vec3(-0.5, -0.8, -0.4))
        except Exception:
            pass

    def run(self):
        logging.info("Memulai Game Loop utama...")
        self.app.run()

def run():
    game = Game3D()
    game.run()