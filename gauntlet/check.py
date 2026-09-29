"""Actual engine render and gameplay regression checks. Run from repository root."""
import json
import math
import sys
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from panda3d.core import loadPrcFileData, VirtualFileSystem, VirtualFileMountRamdisk, Filename, PNMImage
loadPrcFileData('', 'window-type offscreen\naudio-library-name null\nmodel-cache-dir')
from ursina import Ursina, camera, color, Vec3, Vec4, Entity, destroy, Text
import ursina
color.rgb = lambda r,g,b,a=255: Vec4(r/255,g/255,b/255,a/255)
color.rgba = color.rgb
vfs = VirtualFileSystem.get_global_ptr()
probe = Filename.from_os_specific(str(ROOT / 'assets/textures/cave_floor.png'))
memory_fallback = not vfs.exists(probe)
if memory_fallback:
    vfs.mount(VirtualFileMountRamdisk(), '/c', 0)
    for root in (Path(ursina.__file__).parent, ROOT / 'assets'):
        for path in root.rglob('*'):
            if path.suffix.lower() in ('.png','.jpg','.obj','.bam','.ttf','.egg','.mtl'):
                fn = Filename.from_os_specific(str(path))
                vfs.make_directory_full(fn.get_dirname())
                vfs.write_file(fn, path.read_bytes(), False)
app = Ursina(window_type='offscreen', size=(1280,900))
from game.state import GameState
from game.world import World3D
from game.entities import EntitiesManager
from game.scenes import SCENES
from game.config import WALKABLE, TILE_SIZE, STAIRS_UP
from game.player import Player3D
from game.controllers.interaction_controller import InteractionController

passed = []
def record(name):
    passed.append(name)
    print('PASS:', name)

def reachable(sc, start):
    seen={start}; queue=deque(seen)
    while queue:
        x,y=queue.popleft()
        for a,b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=a<sc.w and 0<=b<sc.h and (a,b) not in seen and sc.tiles[b][a] in WALKABLE:
                seen.add((a,b)); queue.append((a,b))
    return seen

for name,start in (('mountain',(14,23)), ('naga_cave',(7,9))):
    sc=SCENES[name]; seen=reachable(sc,start)
    for x,y,dest,dx,dy in sc.portals:
        assert (x,y) in seen, (name,x,y)
        assert SCENES[dest].tiles[dy][dx] in WALKABLE
    for other in SCENES.values():
        for _,_,dest,dx,dy in other.portals:
            if dest==name: assert (dx,dy) in seen
    if name=='naga_cave':
        assert {(7,6),(11,8),(13,10),(12,10)} <= seen
    record(name+' portal and arrival connectivity')

s=GameState(scene_name='naga_cave',time_minutes=1200)
w=World3D(s); w.load_scene(s.scene_name)
e=EntitiesManager(s); e.load_scene(s.scene_name)

# Kristal gua: tiap shard harus punya geometri nyata, normal yang menunjuk
# keluar, dan tint di bawah plafon clipping smooth_shader.
#
# Plafon itu nyata, bukan gaya: `_FRAG` mengalikan warna dengan
# (ambient + sun_color*diff), dan puncaknya 0,45 + 1,05 = 1,50 pada pita
# terang. Tint lama (kanal G 201..225, B 213..233) menembus 1,0 di sana
# sehingga faset paling terang terpotong pucat kelabu dan pita toon-nya hilang
# -- kristal terbaca rata. Itu bug rupa yang tidak muncul sebagai "geometri
# nol", jadi diperiksa terpisah di sini.
#
# Shard dikenali dari sidik mesh-nya (5 sisi -> 10 + 5 segitiga = 45 vertex),
# bukan dari daftar warna tetap, supaya penyesuaian tint yang sah tidak
# dilaporkan sebagai "kristal hilang".
_shards=[ent for ent in w._obj_ents
         if ent.model is not None and len(getattr(ent.model,'vertices',[]))==45]
assert len(_shards)==12, f'harap 4 tile x 3 shard = 12 kristal, dapat {len(_shards)}'
for ent in _shards:
    verts=list(ent.model.vertices); normals=list(ent.model.normals)
    assert len(normals)==len(verts), f'normal tidak sepadan: {len(normals)} vs {len(verts)}'
    dx=max(v[0] for v in verts)-min(v[0] for v in verts)
    dy=max(v[1] for v in verts)-min(v[1] for v in verts)
    dz=max(v[2] for v in verts)-min(v[2] for v in verts)
    assert dy>0.5 and dx>0.1 and dz>0.1, f'kristal pipih: dx={dx:.3f} dy={dy:.3f} dz={dz:.3f}'
    cx=sum(v[0] for v in verts)/len(verts)
    cy=sum(v[1] for v in verts)/len(verts)
    cz=sum(v[2] for v in verts)/len(verts)
    outward=0
    for i in range(0,len(verts),3):
        n=normals[i]
        mx=(verts[i][0]+verts[i+1][0]+verts[i+2][0])/3-cx
        my=(verts[i][1]+verts[i+1][1]+verts[i+2][1])/3-cy
        mz=(verts[i][2]+verts[i+1][2]+verts[i+2][2])/3-cz
        if n[0]*mx+n[1]*my+n[2]*mz>0: outward+=1
    total=len(verts)//3
    assert outward>=total*0.8, f'normal menghadap ke dalam: {outward}/{total} keluar'
    c=ent.color
    peak=max(c[0],c[1],c[2])*1.5
    assert peak<=1.002, f'tint menembus plafon clipping: puncak {peak:.3f} > 1,0'
record('cave crystals have real geometry, outward normals, and no clipped tint')

for minute,expected,activity in ((359,{'naga_bijak','banaspati'},'meditating'),
    (360,{'naga_bijak'},'meditating'),(1079,{'naga_bijak'},'meditating'),
    (1080,{'naga_bijak','banaspati'},'meditating'),(0,{'naga_bijak','banaspati'},'sleeping'),
    (300,{'naga_bijak','banaspati'},'meditating')):
    s.time_minutes=minute; e.update(1/60)
    assert set(e.actors)==expected,(minute,set(e.actors))
    assert e.actors['naga_bijak'].activity==activity
    for actor in e.actors.values():
        assert (actor.logical_x,actor.logical_y)==(actor.sched_x,actor.sched_y)
        assert actor.rotation_x==0
record('exact hour visibility and sleep/wake without re-entering cave')

import game.state as state_module
save_path=ROOT/'gauntlet/test-save.json'
s.npc_positions['naga_bijak']['x']=3
s.npc_positions['naga_bijak'].pop('sched_x',None)
with patch.object(state_module,'SAVE_FILE',str(save_path)):
    assert s.save(); loaded=GameState.load(); assert loaded is not None
    e._clear_all(); e=EntitiesManager(loaded); e.load_scene('naga_cave')
    assert e.actors['naga_bijak'].logical_x==7
    assert loaded.inventory==s.inventory
record('actual save/load and obsolete guardian position restoration')
s=loaded

# Integritas save. Pemeriksaan di atas hanya membuktikan bolak-balik yang
# BERSIH, sehingga tidak satu pun dari tiga cacat nyata di bawah ini tertangkap:
# penulisan yang memotong berkas hidup lebih dulu, save rusak yang berubah jadi
# game baru lalu menimpa satu-satunya salinan, dan field dinamis yang dibuang
# diam-diam saat dimuat.
import logging
logging.disable(logging.CRITICAL)
with patch.object(state_module,'SAVE_FILE',str(save_path)):
    # 1. Atomik: kegagalan saat MERAKIT save tidak boleh menyentuh berkas lama.
    #    Dulu `open(SAVE_FILE,'w')` memotongnya sebelum json.dump dijalankan.
    save_path.write_text('{"char_name":"PEMAIN LAMA","gold":4242}',encoding='utf-8')
    sebelum=save_path.read_bytes()
    with patch.object(GameState,'sync_motives',side_effect=RuntimeError('sengaja digagalkan')):
        assert GameState().save() is False, 'save yang gagal harus mengembalikan False'
    assert save_path.read_bytes()==sebelum, 'save yang gagal menyentuh berkas lama'

    # 2. Save rusak dipindahkan, bukan ditinggalkan untuk ditimpa save baru.
    save_path.write_text('{ ini bukan json',encoding='utf-8')
    hasil,status=GameState.load_with_status()
    assert hasil is None and status=='corrupt', (hasil,status)
    assert not save_path.exists(), 'berkas rusak seharusnya sudah dipindahkan'
    karantina=sorted(save_path.parent.glob(save_path.name+'.corrupt-*'))
    assert karantina, 'berkas rusak tidak ditemukan setelah dikarantina'
    assert karantina[0].read_text(encoding='utf-8')=='{ ini bukan json', \
        'isi berkas rusak berubah saat dikarantina'
    for k in karantina: k.unlink()

    # 3. 'absent' harus bisa dibedakan dari 'corrupt'. Dulu keduanya sama-sama
    #    None, dan itulah yang membuat kehilangan data tidak terlihat.
    assert GameState.load_with_status()==(None,'absent')

    # 4. Field dinamis yang ditulis kode lain harus bertahan bolak-balik.
    #    `animal_care` ditulis husbandry.care_of() tapi bukan field dataclass,
    #    jadi dulu ditulis ke JSON lalu dibuang lagi saat dimuat.
    s.animal_care={'sapi_1':{'kenyang':0,'sakit':True}}
    assert s.save()
    ulang,status=GameState.load_with_status()
    assert status=='ok'
    assert ulang.animal_care==s.animal_care, ulang.animal_care

    # 5. Hanya field dataclass yang diterima. Dulu `hasattr` juga menerima nama
    #    method, sehingga kunci bernama `save` membayangi method save().
    save_path.write_text(json.dumps({'char_name':'X','save':'BUKAN FIELD','mv':'BUKAN FIELD'}),encoding='utf-8')
    ulang,status=GameState.load_with_status()
    assert status=='ok' and callable(getattr(ulang,'save')), 'method save() terbayangi'

    # 6. Nilai liar dipulihkan, bukan meledak di frame pertama. panels.py
    #    mengindeks SEASON_NAMES[season_index] tiap frame tanpa penjaga.
    save_path.write_text(json.dumps({'season_index':99,'soil':[],'mobs':{}}),encoding='utf-8')
    ulang,status=GameState.load_with_status()
    assert ulang.season_index==0 and ulang.soil=={} and ulang.mobs==[], \
        (ulang.season_index,ulang.soil,ulang.mobs)
    save_path.unlink(missing_ok=True)
logging.disable(logging.NOTSET)
record('save is atomic, corrupt files quarantined, dynamic fields survive')

panels=Mock()
pl=SimpleNamespace(state=s)
controller=InteractionController(pl,w)
for key in ('naga_bijak','banaspati'):
    assert any(opt[0]=='amati' and opt[2] for opt in controller.build_pie_options(key))
    assert any(opt[0]=='sapa_halus' and not opt[2] for opt in controller.build_pie_options(key))
    s.npc_hearts[key]=1
    assert any(opt[0]=='sapa_halus' and opt[2] for opt in controller.build_pie_options(key))
    controller.execute_pie_action(key,'sapa_halus',e,panels)
    panels.start_dialog.assert_called_with(key,s)
controller.execute_pie_action('naga_bijak','naga_riddle',e,panels)
panels.start_dialog.assert_called_with('naga_bijak',s,node_key='naga_riddle_start')
assert e.get_nearest_npc(7,6,max_dist_tiles=0)=={'id':'naga_bijak'}
assert e.get_nearest_npc(7,7,max_dist_tiles=.5) is None
s.inventory['besi']=1
s.npc_hearts['banaspati']=0
assert any(opt[0]=='tawarkan' and opt[2] for opt in controller.build_pie_options('banaspati'))
pl.get_tile_pos=lambda:(9,7)
controller.execute_pie_action('banaspati','tawarkan',e,panels)
panels.start_dialog.assert_called_with('banaspati',s,node_key='gift_confirm')
controller.complete_gift_gifting('banaspati',panels)
assert s.inventory['besi']==0 and s.npc_hearts['banaspati']==1
assert any(opt[0]=='sapa_halus' and opt[2] for opt in controller.build_pie_options('banaspati'))
record('guardian dialogue, interaction radius and obtainable iron gift progression')

with patch('game.player.sound_play'):
    for name in ('mountain','naga_cave'):
        for x,y,dest,dx,dy in SCENES[name].portals:
            state=GameState(scene_name=name)
            player=SimpleNamespace(state=state,world=SimpleNamespace(scene_obj=SCENES[name]),_portal_cd=0)
            assert Player3D._check_portals(player,x,y)
            assert (state.scene_name,state.player_x,state.player_y)==(dest,float(dx),float(dy))
            assert not Player3D._check_portals(player,x,y)
    state=GameState(scene_name='naga_cave')
    player=SimpleNamespace(state=state,world=w,_portal_cd=0,
        quest_controller=SimpleNamespace(check_dungeon_lore=lambda *a:None))
    player._generate_and_enter_dungeon=lambda: Player3D._generate_and_enter_dungeon(player)
    assert Player3D._check_portals(player,13,10)
    assert state.scene_name=='dungeon' and state.dungeon_level==1 and state.dungeon_tiles
    assert state.dungeon_tiles[int(state.player_y)][int(state.player_x)] in WALKABLE
    player._portal_cd=0
    player.world=SimpleNamespace(scene_obj=SCENES['dungeon'],get_tile=lambda x,y:STAIRS_UP)
    assert Player3D._check_portals(player,0,0)
    assert (state.scene_name,state.player_x,state.player_y)==('naga_cave',12.,10.)
record('real portal cooldown, dungeon generation and return transition')

# Blok pembaruan penunggu pernah tergandakan di entities.py: `update_guardian`
# dipanggil dua kali per frame, sehingga `_guardian_time` maju 2x dt dan napas
# naga serta ayunan api banaspati berjalan dua kali kecepatan rancangan.
# Bug rupa seperti ini tidak terbaca dari screenshot, jadi dihitung.
from game import guardian_models as _gm
_calls={}
_real_update=_gm.update_guardian
def _counted(actor,dt):
    _calls[actor.actor_id]=_calls.get(actor.actor_id,0)+1
    return _real_update(actor,dt)
_gm.update_guardian=_counted
try:
    s.time_minutes=1200
    e.load_scene('naga_cave')
    e._npc_sched_t=0
    assert {'naga_bijak','banaspati'} <= set(e.actors), set(e.actors)
    _calls.clear(); e.update(1/60)
    assert _calls=={'naga_bijak':1,'banaspati':1}, _calls
    # Naga tetap membumi, banaspati melayang. Penanda inilah yang menentukan
    # bobbing, bukan keberadaan `_guardian_visual` secara kebetulan.
    assert e.actors['banaspati']._guardian_floats is True
    assert e.actors['naga_bijak']._guardian_floats is False
finally:
    _gm.update_guardian=_real_update
record('guardian visual update runs exactly once per frame')

def shot(name,focus,dist=19,yaw=0,pitch=34):
    camera.fov=60; camera.orthographic=False
    ya,pi=math.radians(yaw),math.radians(pitch)
    camera.position=Vec3(*focus)+Vec3(math.sin(ya)*math.cos(pi),math.sin(pi),-math.cos(ya)*math.cos(pi))*dist
    camera.look_at(Vec3(*focus)); camera.rotation_z=0
    w.update_wall_cutaway(camera.position,Vec3(*focus))
    for _ in range(8): app.graphicsEngine.renderFrame()
    image=PNMImage(); app.win.get_screenshot(image)
    target=Filename.from_os_specific(str(ROOT/'gauntlet'/f'{name}.png'))
    if memory_fallback: vfs.make_directory_full(target.get_dirname())
    assert image.write(target), str(target)
    if memory_fallback: (ROOT/'gauntlet'/f'{name}.png').write_bytes(vfs.read_file(target,False))

s.time_minutes=1200; s.scene_name='naga_cave'; e.update(1/60)
shot('cave-overview',(14,1,11),36)
shot('cave-gameplay',(14,1,12))
shot('guardians-front',(17,1,14),16,180,25)
for name,focus,dist in (('mountain',(29,1,16),48),):
    s.scene_name=name; w.load_scene(name)
    s.npc_positions['wewe_gombel']['scene']='mountain'
    s.npc_positions['wewe_gombel']['x']=11
    s.npc_positions['wewe_gombel']['y']=2
    e.load_scene(name)
    assert w.is_walkable(int(e.actors['wewe_gombel'].logical_x),int(e.actors['wewe_gombel'].logical_y))
    assert all(w.is_walkable(int(p['x']),int(p['y'])) for p in s.wild_entities if p['scene']==name)
    shot(name+'-overview',focus,dist)
    shot(name+'-entrance',(29,1,10),24,180,34)
record('five actual-engine screenshots with gameplay camera convention')

# Lapisan objek terpasang (`Scene.objects`). Fase 5a baru DATA-nya -- belum ada
# yang merender -- jadi yang dibuktikan di sini adalah invariannya, bukan
# tampilannya: validasi menolak entri rusak, jenis memetakan ke ubin yang sudah
# ada, dan bolak-balik lewat dict mempertahankannya.
from game.objects import OBJECT_KINDS as _KINDS, solid_kind as _solid, tile_dari_kind as _tile
from game.config import BLOCKING as _BLOCK
from game.scenes.scene_base import Scene as _Scene
assert len(_KINDS)>=15, len(_KINDS)
for _k,_tid in _KINDS.items():
    assert _tile(_k)==_tid
    # Sifat memblokir harus IKUT grid, bukan daftar kedua yang bisa berbeda.
    assert _solid(_k)==(_tid in _BLOCK), _k
_probe=_Scene('probe','Probe',[[0,0],[0,0]])
# `x`/`y` adalah koordinat UBIN, `h` ketinggian -- konvensi yang sama dengan
# `portals` dan `npc_positions`. Versi pertama pemeriksaan ini masih memakai
# skema lama (`x`/`z`), dan kedua entri sahnya langsung tertolak karena `y`
# hilang: pemeriksaannya yang benar, datanya yang basi.
_probe.objects=[{'kind':'kompor','x':1.5,'y':2.5},
                {'kind':'jam','x':0.0,'y':0.0,'rot_y':-90},
                {'kind':'tidak_ada','x':1,'y':1},
                {'kind':'kompor','x':float('nan'),'y':1},
                {'kind':'kompor'},
                'bukan dict']
assert len(_probe.objects)==2, _probe.objects
assert _probe.objects[1]['rot_y']==270.0, _probe.objects[1]
assert _probe.objects[0]['scale']==1.0
# Penugasan LANGSUNG sesudah konstruksi juga harus tervalidasi. Versi pertama
# hanya memvalidasi di __init__, sehingga editor -- yang memang menulis
# `scene.objects = [...]` -- bisa menyelipkan daftar mentah yang baru meledak
# jauh kemudian di `to_dict`. Ketahuan dari uji data kotor, bukan dari membaca.
_probe.objects=[{'kind':'peti','x':1,'y':1},'bukan dict']
assert len(_probe.objects)==1, _probe.objects
assert _Scene.from_dict(_probe.to_dict()).objects==_probe.objects
record('placed-object layer maps kinds to tiles and rejects malformed entries')

# Objek terpasang benar-benar DIRENDER, dan di posisi yang benar. Yang paling
# mudah salah di sini adalah KONVENSINYA: `x`/`y` adalah koordinat ubin, bukan
# satuan dunia, dan `h` ketinggian di atas tanah. Salah satu saja dan perabot
# muncul di tempat yang salah tanpa satu pun error.
from game.config import TILE_SIZE as _TS2, GROUND_H as _GH2
from game.objects import OBJECT_TINGGI as _OTINGGI
w.load_scene('farm')
_obj=[e for e in w._obj_ents if getattr(e,'is_object',False)]
assert len(_obj)==3, f'harap 3 objek terpasang di farm, dapat {len(_obj)}'
assert len(_obj)==len(SCENES['farm'].objects)
for o,e in zip(SCENES['farm'].objects,_obj):
    hx,hz=o['x']*_TS2, o['y']*_TS2
    hy=_GH2+o['h']+_TS2*_OTINGGI.get(o['kind'],0.6)*o['scale']/2.0
    assert abs(e.x-hx)<0.01 and abs(e.z-hz)<0.01, (o,(e.x,e.y,e.z),hx,hz)
    assert abs(e.y-hy)<0.01, (o,(e.x,e.y,e.z),hy)
    assert abs(e.rotation_y-o['rot_y'])<0.01, (o,e.rotation_y)
# Jam sengaja diberi `h` 1,15 m supaya ketinggian ikut terbukti, bukan cuma
# bidang datar.
_jam=[o for o in SCENES['farm'].objects if o['kind']=='jam']
assert _jam and _jam[0]['h']>1.0, 'farm butuh satu objek berketinggian'
record('placed objects render at the tile coordinates they were given')

# Tekstur objek terpasang harus SAMA dengan tekstur ubin yang sama di grid.
# `dermaga` hanya punya tekstur di `TILE_TEX`, dan perender yang cuma memeriksa
# `OBJ_TEX` membuatnya jadi kotak kelabu sementara dermaga di grid bertekstur --
# dua wajah untuk satu benda.
from game.world import OBJ_TEX as _OTEX, TILE_TEX as _TTEX
from game.objects import OBJECT_KINDS as _OKINDS, tile_dari_kind as _tdk
_tanpa_tekstur=sorted(k for k in _OKINDS if not (_OTEX.get(_tdk(k)) or _TTEX.get(_tdk(k))))
# Dua jenis ini memang tidak punya tekstur di MANA PUN, termasuk di grid -- itu
# celah yang sudah ada sebelum lapisan objek, dan daftarnya dipatok di sini
# supaya jenis BARU yang lupa diberi tekstur langsung ketahuan.
assert _tanpa_tekstur==['kursi','televisi'], _tanpa_tekstur
assert _OTEX.get(_tdk('dermaga')) is None and _TTEX.get(_tdk('dermaga'))=='dock'
record('placed objects reuse the grid texture, including TILE_TEX-only kinds')

# Viewport editor peta. Editor bekerja dengan entity, game menyimpan GRID UBIN;
# `karsa_tiles.LayerUbin` menjembatani keduanya untuk ditampilkan dan disunting.
# Yang diperiksa di sini bukan "apakah terlihat bagus" -- itu perlu mata -- tapi
# bahwa jumlahnya benar, tiap entity bisa dipetakan balik ke koordinat ubinnya,
# dan satu perubahan mendarat di scene DAN di viewport sekaligus. Kalau keduanya
# bisa berbeda, editor menampilkan peta yang tidak sama dengan yang disimpan.
import ursina_editor.karsa_tiles as _kt
_layer=_kt.LayerUbin(SCENES['farm'])
assert _layer.jumlah_entity()==SCENES['farm'].w*SCENES['farm'].h, \
    f"viewport punya {_layer.jumlah_entity()} entity, seharusnya satu per ubin"
for (x,y),ent in list(_layer.ubin.items())[:40]:
    assert _layer.koordinat(ent)==(x,y), (x,y,_layer.koordinat(ent))
assert _layer.koordinat(object()) is None, 'entity asing dianggap ubin'
_palet=_kt.palet()
assert len(_palet)==51, f'palet harus mencakup 51 ubin, dapat {len(_palet)}'
_bertekstur=sum(1 for _,_,ada in _palet if ada)
assert _bertekstur>=47, f'hanya {_bertekstur} ubin punya tekstur'
# Satu perubahan harus mendarat di scene DAN viewport.
from game.config import G as _G, FN as _FN
_lama=SCENES['farm'].tiles[0][0]
# Nilai barunya WAJIB berbeda dari yang lama. Versi pertama pemeriksaan ini
# menulis `_FN` ke ubin yang memang sudah `_FN` (perbatasan utara farm), jadi
# assertion-nya sudah benar sebelum `set()` dipanggil sekalipun -- dan ia tetap
# lulus walau `set()` sengaja dirusak agar tidak menyentuh scene. Ketahuan dari
# uji suntik, bukan dari membaca ulang.
_baru=_G if _lama!=_G else _FN
assert _baru!=_lama, 'uji ini butuh dua nilai ubin yang berbeda'
_sebelum=_layer.ubin[(0,0)]
assert _layer.set(0,0,_baru), 'set() mengembalikan False'
assert SCENES['farm'].tiles[0][0]==_baru, 'perubahan tidak mendarat di scene'
assert _layer.ubin[(0,0)] is not _sebelum, 'viewport tidak dibangun ulang'
assert _layer.koordinat(_layer.ubin[(0,0)])==(0,0)
assert _layer.set(0,0,_lama), 'gagal mengembalikan ubin'
assert SCENES['farm'].tiles[0][0]==_lama, 'pemulihan tidak mendarat di scene'
assert not _layer.set(-1,0,_G), 'koordinat di luar peta harus ditolak'
destroy(_layer.root)
record('map editor viewport mirrors the tile grid and edits land in both')

# Logika sesi penyuntingan peta (`SesiKarsa`), terpisah dari tombolnya supaya
# bisa diperiksa di sini. Yang dibuktikan: klik pada entity yang BUKAN ubin
# ditolak alih-alih crash, klik pada ubin mengubah scene lewat jalur yang sama
# dengan yang dipakai UI, dan simpan benar-benar menulis berkas yang bisa
# dibaca ulang.
import shutil as _shutil
import ursina_editor.karsa_panel as _kp
import ursina_editor.karsa_scene as _ksc
_sesi=_kp.SesiKarsa()
assert len(_sesi.daftar())==15, len(_sesi.daftar())
_sesi.buka('farm')
assert _sesi.scene is not None and _sesi.layer is not None and not _sesi.kotor
assert _sesi.klik(None) is False and _sesi.klik(object()) is False, \
    'klik bukan-ubin harus ditolak, bukan crash'
from game.config import G as _G2
_x,_y=3,3
_lama3=_sesi.scene.tiles[_y][_x]
_sesi.pilih_ubin(_FN if _lama3!=_FN else _G2)
assert _sesi.klik(_sesi.layer.ubin[(_x,_y)]) is True
assert _sesi.scene.tiles[_y][_x]==_sesi.tid_aktif!=_lama3, 'klik tidak mengubah ubin'
assert _sesi.kotor, 'sesi tidak menandai dirinya kotor setelah disunting'
_sesi.tutup()
assert _sesi.scene is None and _sesi.layer is None
try:
    _kp.SesiKarsa().simpan(); assert False, 'simpan tanpa scene harus menolak'
except RuntimeError:
    pass
# Jalur simpan diuji di direktori TERISOLASI supaya berkas scene asli tidak
# pernah tersentuh oleh harness.
_asli_dir=_ksc.DIR_SCENE
_ksc.DIR_SCENE=ROOT/'gauntlet'/'_scene_test'
try:
    _ksc.DIR_SCENE.mkdir(exist_ok=True)
    _s2=_kp.SesiKarsa(); _s2.buka('farm')
    _s2.pilih_ubin(_G2); _s2.klik(_s2.layer.ubin[(3,3)])
    _p=_s2.simpan()
    assert _p.exists() and not _s2.kotor, 'simpan tidak menulis atau tidak membersihkan kotor'
    _ulang,_sumber=_ksc.muat('farm')
    assert _ulang.tiles[3][3]==_G2, 'ubin hasil simpan tidak terbaca kembali'
    assert _ulang.w==_s2.scene.w and _ulang.h==_s2.scene.h
    assert len(_ulang.portals)==len(_s2.scene.portals)
finally:
    _ksc.DIR_SCENE=_asli_dir
    _shutil.rmtree(ROOT/'gauntlet'/'_scene_test', ignore_errors=True)
record('map editing session paints, rejects non-tiles, and saves readable files')

# Head-seek. `daftarkan_pemain()` di entities.py adalah SATU-SATUNYA penulis
# `_PEMAIN_AKTIF`, dan ia tidak pernah dipanggil dari mana pun -- padahal
# docstring-nya sendiri mengklaim "Dipanggil Player3D.__init__". Akibatnya
# `_PEMAIN_AKTIF[0]` selalu None, `_lihat_pemain` di entities.update() selalu
# None, dan cabang head-seek tidak pernah menyala. Itu ikut mematikan
# satu-satunya bagian `animator.py` yang masih punya pemanggil hidup
# (HeadSeekController). Dijalankan paling akhir supaya Player3D yang dibangun
# di sini tidak ikut muncul di kelima screenshot di atas.
import game.entities as _entities_mod
_entities_mod._PEMAIN_AKTIF[0]=None
_probe_player=Player3D(s,w)
assert _entities_mod._PEMAIN_AKTIF[0] is _probe_player, \
    'Player3D tidak mendaftarkan diri; head-seek NPC akan mati'
record('player registers itself for NPC head-seek')

(ROOT/'gauntlet/results.json').write_text(json.dumps({'passed':passed,'memory_vfs_fallback':memory_fallback,
    'interactive_playthrough':False},indent=2),encoding='utf-8')
print('RESULT:',len(passed),'checks passed; memory VFS:',memory_fallback)
