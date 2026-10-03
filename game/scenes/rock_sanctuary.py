"""Scene-local rock formations and ritual landmarks; all solids follow tile blockers."""
import math
from game.config import TILE_SIZE as TS, GROUND_H, CV_W, CRYS, LN


def _part(world, model, pos, scale, rgb, **kw):
    from ursina import color
    from game.world import _e
    ent = _e(model, pos, scale, None, color.rgb(*rgb), soft=False, **kw)
    world._obj_ents.append(ent)
    return ent


def _rock_mesh(seed, centered=False):
    """Rock with its base at y=0; centered=True is for wall cutaway only."""
    from ursina import Mesh, Vec3
    # Facets use individual vertices so the light describes real broken planes.
    rings = []
    for level, radius in ((0, .50), (.48, .49), (1, .28)):
        rings.append([(math.cos(i * math.tau / 7) * radius,
                       level + (0 if level == 0 else .06 * math.sin(i * 3 + seed)),
                       math.sin(i * math.tau / 7) * radius) for i in range(7)])
    verts, normals = [], []
    def face(a, b, c):
        a, b, c = Vec3(*a), Vec3(*b), Vec3(*c)
        n = (b-a).cross(c-a).normalized()
        verts.extend((a,b,c)); normals.extend((n,n,n))
    for row in range(2):
        for i in range(7):
            j = (i+1)%7
            face(rings[row][i], rings[row+1][i], rings[row+1][j])
            face(rings[row][i], rings[row+1][j], rings[row][j])
    for i in range(7):
        face(rings[2][i], (0,1.06,0), rings[2][(i+1)%7])
    if centered:
        verts = [Vec3(v.x, v.y-.5, v.z) for v in verts]
    return Mesh(vertices=verts, normals=normals, mode='triangle')


def _crystal_mesh(seed, sides=5):
    """Shard prismatik berfaset datar dengan ujung meruncing.

    `_rock_mesh` menghasilkan gumpalan membulat -- tujuh sisi, tiga cincin, dan
    puncak tumpul -- sehingga kristal terbaca sebagai batu teal, bukan kristal.
    Di sini badannya prismatik (radius nyaris tetap, menyempit 0,72) lalu
    meruncing tajam ke satu titik, dan tiap faset tetap satu bidang datar.
    """
    from ursina import Mesh, Vec3
    twist = math.sin(seed * 2.7) * .35
    rings = []
    for level, radius in ((0, .50), (.74, .50 * .72)):
        rings.append([(math.cos(i * math.tau / sides + twist) * radius,
                       level + (0 if level == 0 else .03 * math.sin(i * 3 + seed)),
                       math.sin(i * math.tau / sides + twist) * radius)
                      for i in range(sides)])
    verts, normals = [], []
    def face(a, b, c):
        a, b, c = Vec3(*a), Vec3(*b), Vec3(*c)
        n = (b-a).cross(c-a).normalized()
        verts.extend((a, b, c)); normals.extend((n, n, n))
    for i in range(sides):
        j = (i+1) % sides
        face(rings[0][i], rings[1][i], rings[1][j])
        face(rings[0][i], rings[1][j], rings[0][j])
    apex = (twist * .12, 1.02, twist * .08)
    for i in range(sides):
        face(rings[1][i], apex, rings[1][(i+1) % sides])
    return Mesh(vertices=verts, normals=normals, mode='triangle')


def _rocks(world, scene, outdoor=False):
    # Remove the default cuboid walls from the visibility/cutaway registry too.
    for entry in world._wall_ents:
        entry[0].enabled = False
    world._wall_ents.clear()
    covered = set()
    for y,row in enumerate(scene.tiles):
        for x,tid in enumerate(row):
            if tid != CV_W or (x,y) in covered:
                continue
            if outdoor and x in (14,15) and y <= 2:
                continue  # dark recess behind the mouth, still collision-blocked
            width=1
            while width < 3 and x+width < scene.w and row[x+width]==CV_W and not (outdoor and x+width in (14,15) and y<=2):
                width+=1
            covered.update((x+i,y) for i in range(width))
            seed=x*13+y*7
            height=(2.4+.7*math.sin(seed)) if outdoor else (1.5+.5*math.sin(seed))
            if y < 3: height += 2.3 if outdoor else 1.1
            rgb=(106+seed%12,123+seed%10,111+seed%14) if outdoor else (84+seed%13,105+seed%11,115+seed%15)
            mesh=_rock_mesh(seed, centered=True)
            xx=(x+(width-1)/2)*TS
            e=_part(world,mesh,(xx,GROUND_H+height/2,y*TS),(TS*width*1.02,height,TS*1.02),rgb)
            world._wall_ents.append([e,height,GROUND_H+height/2,x+(width-1)/2,y])


def _disc(world, x, z, radius, rgb, y=0.215, inner=0):
    from ursina import Mesh
    vertices=[]
    for i in range(64):
        a,b=i*math.tau/64,(i+1)*math.tau/64
        pts=[(x+math.cos(a)*inner,y,z+math.sin(a)*inner),
             (x+math.cos(a)*radius,y,z+math.sin(a)*radius),
             (x+math.cos(b)*radius,y,z+math.sin(b)*radius),
             (x+math.cos(b)*inner,y,z+math.sin(b)*inner)]
        vertices.extend([pts[0],pts[2],pts[1],pts[0],pts[3],pts[2]])
    return _part(world,Mesh(vertices=vertices,normals=[(0,1,0)]*len(vertices)),(0,0,0),(1,1,1),rgb,double_sided=True)


def _ground_patch(world, x, z, rx, rz, rgb, seed, height=.202):
    """Low-contrast sediment facets; flush with the ground and non-blocking."""
    from ursina import Mesh
    rim=[]
    for i in range(8):
        a=i*math.tau/8
        r=.85+.15*math.sin(seed+i*2.3)
        rim.append((x+math.cos(a)*rx*r,height,z+math.sin(a)*rz*r))
    for i in range(8):
        shift=(i+seed)%3-1
        _part(world,Mesh(vertices=[(x,height,z),rim[(i+1)%8],rim[i]],normals=[(0,1,0)]*3),
              (0,0,0),(1,1,1),tuple(c+shift for c in rgb),double_sided=True)


def build_cavern(world, scene):
    from ursina import color
    # Rebuild the cave as a coherent surface, not 180 alternating textures.
    for e in world._tile_ents:
        e.enabled = False
    for e in world._obj_ents:
        if e.model:
            e.enabled = False
        else:
            e.color = color.rgb(170,205,215)
    _part(world,'cube',((scene.w-1)*TS/2,.1,(scene.h-1)*TS/2),(scene.w*TS,.2,scene.h*TS),(82,99,112))
    _rocks(world,scene)
    for x,z,rx,rz in ((6,8,3.6,5),(23,7,4,3),(5,18,4,3),(22,18,4,3),(14,3,3,2)):
        _ground_patch(world,x,z,rx,rz,(85,103,114),x+z)
    # Sparse strata seams, not an alternating checkerboard. Flush decoration.
    for y in range(1,11):
        for x in range(1,14):
            if scene.tiles[y][x]==CV_W or (x-7)**2+(y-6)**2<4:
                continue
            if (x*3+y*7)%5==0:
                _part(world,'cube',(x*TS,.204,y*TS),(1.15,.005,.018),(72,89,101),rotation=(0,(x+y)%3*17,0))
    for x,y,r in ((7,6,1.75),(11,8,.7)):
        _disc(world,x*TS,y*TS,r,(65,83,87),.224)
    # A calm ceremonial medallion anchors the guardian, with a clear approach.
    _disc(world,7*TS,6*TS,3.5,(108,135,140))
    _disc(world,7*TS,6*TS,3.45,(128,117,78),.219,3.32)
    _disc(world,7*TS,6*TS,2.85,(143,172,169),.22,2.78)
    for y in (7.7,8.6,9.5,10.4,11):
        _part(world,'cube',(7*TS,.219,y*TS),(1.7,.018,1.30),(145,159,159))
    # Sanctuary carved into the rear wall, safely behind the celestial portal.
    for x in (6,8):
        _part(world,'cube',(x*TS,1.15,TS),(1.1,1.9,1.0),(166,170,157))
        _part(world,'cube',(x*TS,2.18,TS),(1.45,.25,1.3),(136,130,99))
    _part(world,'cube',(7*TS,2.48,TS),(5.4,.36,1.3),(150,171,170))
    _part(world,'cube',(7*TS,2.73,TS),(5.85,.16,1.55),(134,124,87))
    # Stair destinations have distinct low relief landing plates.
    for x,y,up in ((7,5,True),(13,10,False)):
        _part(world,'cube',(x*TS,.22,y*TS),(1.75,.035,1.75),(129,120,83) if up else (46,59,72))
        for i in range(4):
            _part(world,'cube',(x*TS,.245,y*TS-.57+i*.37),(1.4,.025,.14),(180,166,118) if up else (120,140,153))
    for y,row in enumerate(scene.tiles):
        for x,tid in enumerate(row):
            if tid==CRYS:
                _disc(world,x*TS,y*TS,.85,(65,82,91),.212)
                for k in range(3):
                    # Seed ikut koordinat tile. Sebelumnya `_rock_mesh(k)` hanya
                    # punya tiga mesh tetap, jadi keempat klaster kristal di gua
                    # ini identik satu sama lain.
                    seed=x*17+y*29+k
                    # Tint lama (107..151, 201..225, 213..233) dikali 1,50 pada
                    # pita terang smooth_shader menembus 1,0 di kanal G dan B,
                    # sehingga faset paling terang terpotong pucat kelabu dan
                    # pita toon-nya hilang. Batas amannya base <= 170; nilai di
                    # bawah duduk tepat di bawah batas itu supaya faset terang
                    # mencapai ~(147,249,252) tanpa clipping. Menurunkan tint
                    # lebih jauh dari ini adalah kegagalan yang berlawanan --
                    # kristal jadi rimbun gelap, bukan jenuh.
                    _part(world,_crystal_mesh(seed),(x*TS+(k-1)*.36,.2,y*TS+(k%2)*.3),
                          (.48,.9+k*.33,.48),(78+10*k,142+12*k,150+9*k),
                          rotation=(0,(seed*47)%360,0))
            elif tid==LN:
                _disc(world,x*TS,y*TS,.53,(67,83,92),.212)
                _part(world,'cube',(x*TS,.53,y*TS),(.6,.65,.6),(137,143,138))
                _part(world,'cube',(x*TS,.91,y*TS),(.83,.13,.83),(140,131,104))
                _part(world,'sphere',(x*TS,1.1,y*TS),(.36,.4,.36),(255,208,105),smooth=False)


def build_mountain_landscape(world, scene):
    from game.scenes.props import default_prop_builder
    from game.config import G,P,D,DR,TR,DT
    default_prop_builder(world,scene)
    # Replace the broken checker/road textures locally, leaving tree geometry.
    for e in world._tile_ents:
        if e.model and e.scale_x < scene.w*TS*2:
            e.enabled=False
    for e in world._obj_ents:
        if e.model and (e.y < .25 or (abs(e.z-3*TS)<.01 and any(abs(e.x-x*TS)<.01 for x in (14,15)))):
            e.enabled=False
    _part(world,'cube',((scene.w-1)*TS/2,.1,(scene.h-1)*TS/2),(scene.w*TS,.2,scene.h*TS),(91,120,79))
    for y,row in enumerate(scene.tiles):
        for x,tid in enumerate(row):
            if tid in (D,P,DR):
                rgb=(143,136,112) if tid in (P,DR) else (119,129,108)
                _part(world,'cube',(x*TS,.21,y*TS),(TS,.02,TS),rgb)
                if tid==P and (x+y)%3==0:
                    _part(world,'cube',(x*TS,.225,y*TS),(1.5,.01,.024),(116,111,94),rotation=(0,8*(y%3),0))
            if tid in (TR,DT):
                _disc(world,x*TS,y*TS,.82,(72,98,65),.212)
    for x,z,rx,rz,rgb in ((19,19,5,4,(123,132,111)),(39,21,5,6,(115,125,105)),
                           (23,10,2,4,(126,134,115)),(35,9,2,3,(115,125,105)),
                           (15,31,5,5,(94,123,82)),(42,34,6,5,(87,116,76))):
        _ground_patch(world,x,z,rx,rz,rgb,x+z,.223)
    _rocks(world,scene,True)
    # The irregular dark silhouette and broad overlapping overhang form one
    # continuous mouth. Solids remain behind the walkable door thresholds.
    from ursina import Mesh
    outline=[(-2.15,.2),(-2.45,1.9),(-2.2,4.5),(-.8,5.1),
             (.7,5.1),(2.2,4.5),(2.3,1.7),(2.15,.2)]
    verts=[]
    for i in range(len(outline)):
        j=(i+1)%len(outline)
        verts.extend([(29,1.8,3.94),(29+outline[i][0],outline[i][1],3.94),
                      (29+outline[j][0],outline[j][1],3.94)])
    _part(world,Mesh(vertices=verts),(0,0,0),(1,1,1),(20,29,30),smooth=False,double_sided=True)
    for x in (13,16):
        _part(world,_rock_mesh(x),(x*TS,.2,2*TS),(2.3,4.35,2.5),(111,128,116))
    # Base-origin rocks overlap above the opening, eliminating sky pinholes.
    _part(world,_rock_mesh(31),(29,3.3,3.5),(8.4,2.65,3.7),(114,130,116))
    _part(world,_rock_mesh(43),(28.2,4.4,2.3),(9.5,2.0,3.6),(119,134,122))
