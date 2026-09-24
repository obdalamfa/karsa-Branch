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
(ROOT/'gauntlet/results.json').write_text(json.dumps({'passed':passed,'memory_vfs_fallback':memory_fallback,
    'interactive_playthrough':False},indent=2),encoding='utf-8')
print('RESULT:',len(passed),'checks passed; memory VFS:',memory_fallback)
