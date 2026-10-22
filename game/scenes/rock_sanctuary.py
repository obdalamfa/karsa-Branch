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


def _kristal_pijar_mesh(seed, rgb, sides=5):
    """Kristal yang menyala sendiri, dengan faset tetap terbaca.

    Digambar tanpa cahaya scene (gua sengaja gelap), jadi terang tiap faset
    dipanggang ke warna verteks dari arah cahaya tetap: tanpa itu kristal
    unlit hanyalah siluet satu warna.
    """
    from ursina import Mesh, Vec3, color
    dasar = _crystal_mesh(seed, sides)
    arah = Vec3(.35, .8, -.45).normalized()
    cols = []
    for i in range(0, len(dasar.vertices), 3):
        n = dasar.normals[i]
        terang = .62 + .48 * max(0.0, n.dot(arah)) + .12 * max(0.0, n.y)
        c = tuple(min(255, v * terang) for v in rgb)
        cols.extend([color.rgb(*c)] * 3)
    return Mesh(vertices=dasar.vertices, normals=dasar.normals, colors=cols, mode='triangle')


def _bersihkan_dinding_kubus(world):
    """Matikan dinding kubus bawaan world.py dan keluarkan dari cutaway."""
    for entry in world._wall_ents:
        entry[0].enabled = False
    world._wall_ents.clear()


def _rocks(world, scene, outdoor=False):
    _bersihkan_dinding_kubus(world)
    covered = set()
    for y,row in enumerate(scene.tiles):
        for x,tid in enumerate(row):
            if tid != CV_W or (x,y) in covered:
                continue
            if outdoor and y <= _BARIS_TEBING:
                continue  # bahu lembah dibangun utuh oleh _tebing_menerus()
            if outdoor and x in (14,15) and y <= 2:
                continue  # dark recess behind the mouth, still collision-blocked
            width=1
            while width < 3 and x+width < scene.w and row[x+width]==CV_W and not (outdoor and x+width in (14,15) and y<=2):
                width+=1
            covered.update((x+i,y) for i in range(width))
            seed=x*13+y*7
            # Tebing lembah gunung jauh lebih tinggi dari dinding gua: ia harus
            # terbaca sebagai bahu gunung yang mengapit jalan, bukan pagar batu.
            height=(3.8+1.3*math.sin(seed)) if outdoor else (1.5+.5*math.sin(seed))
            if y < 3: height += 4.6 if outdoor else 1.1
            rgb=(106+seed%12,123+seed%10,111+seed%14) if outdoor else (66+seed%13,80+seed%11,96+seed%15)
            mesh=_rock_mesh(seed, centered=True)
            xx=(x+(width-1)/2)*TS
            e=_part(world,mesh,(xx,GROUND_H+height/2,y*TS),(TS*width*1.02,height,TS*1.02),rgb)
            world._wall_ents.append([e,height,GROUND_H+height/2,x+(width-1)/2,y])
            if False:  # puncak kedua dulu menumpuk jadi tebing berlapis
                # Puncak kedua yang lebih sempit memecah siluet tebing rata.
                h2=height*(.35+.2*abs(math.sin(seed*1.7)))
                e2=_part(world,_rock_mesh(seed+5,centered=True),
                         (xx+.3*math.sin(seed),GROUND_H+height+h2/2-.15,y*TS+.25*math.cos(seed)),
                         (TS*width*.62,h2,TS*.7),tuple(c-8 for c in rgb))
                world._wall_ents.append([e2,h2,GROUND_H+height+h2/2-.15,x+(width-1)/2,y])


# Baris CV_W paling selatan yang ikut tebing menerus. Di bawahnya hanya ada
# dinding batas tipis yang perlu bisa dipotong kamera (cutaway).
_BARIS_TEBING = 10


def _tebing_ubin(world, batu, tinggi, rgb, tanpa_dinding=lambda x, y: False):
    """Tebing dari ubin penghalang sebagai SATU permukaan tanpa lapisan.

    Dulu tiap 1-3 ubin dapat bongkah sendiri ditambah puncak kedua di atasnya:
    puluhan gumpalan yang terbaca bertumpuk dan berlapis. Di sini tinggi
    tebing ditentukan di SUDUT ubin (`tinggi(cx, cy)`) dan dipakai bersama oleh
    ubin tetangga, jadi permukaannya menyambung tanpa jahitan. Dinding tegak
    hanya dibuat di tepi yang berbatasan dengan ubin non-`batu`.

    Tiap ubin tetap entity sendiri dan terdaftar di `world._wall_ents`, karena
    cutaway kamera memendekkan dinding per entity. Satu mesh besar pernah
    menutup seluruh layar saat kamera berada di baliknya.
    """
    from ursina import Mesh
    sel = []
    for y, x in batu.ubin:
        hs = {(i, j): tinggi(x + i, y + j) for i in (0, 1) for j in (0, 1)}
        H = max(hs.values())

        def P(i, j, atas=True):
            ly = (hs[(i, j)] / H - 0.5) if atas else -0.5
            return ((i - 0.5) * TS, ly, (j - 0.5) * TS)

        a_, b_, c_, d_ = P(0, 0), P(1, 0), P(1, 1), P(0, 1)
        v = list((a_, b_, c_, a_, c_, d_) if (x + y) % 2 else (a_, b_, d_, b_, c_, d_))

        def quad(p, q, r, t):
            v.extend((p, q, r, p, r, t))
        if not tanpa_dinding(x, y):
            if not batu(x, y + 1): quad(P(0, 1, False), P(1, 1, False), c_, d_)
            if not batu(x, y - 1): quad(P(1, 0, False), P(0, 0, False), a_, b_)
            if not batu(x - 1, y): quad(P(0, 0, False), P(0, 1, False), d_, a_)
            if not batu(x + 1, y): quad(P(1, 1, False), P(1, 0, False), b_, c_)
        warna = tuple(max(0, min(255, c + ((x * 7 + y * 13) % 9) - 4)) for c in rgb)
        e = _part(world, Mesh(vertices=v, triangles=list(range(len(v)))),
                  (x * TS, GROUND_H + H / 2, y * TS), (1, H, 1), warna, double_sided=True)
        world._wall_ents.append([e, H, GROUND_H + H / 2, x, y])
        sel.append(e)
    return sel


class _Batu:
    """Predikat ubin-penghalang + daftar ubinnya, untuk `_tebing_ubin`."""

    def __init__(self, tiles, cocok):
        self.t, self.cocok = tiles, cocok
        self.h, self.w = len(tiles), len(tiles[0])
        self.ubin = [(y, x) for y in range(self.h) for x in range(self.w) if self(x, y)]

    def __call__(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.cocok(x, y, self.t[y][x])


def _tebing_menerus(world, scene):
    """Bahu lembah dan dinding belakang gua di lereng gunung."""
    batu = _Batu(scene.tiles, lambda x, y, tid: tid == CV_W and y <= _BARIS_TEBING)

    def tinggi(cx, cy):
        naik = (_BARIS_TEBING + 1 - cy) * 0.75          # makin ke utara makin tinggi
        gel = 1.4 * math.sin(cx * 0.55 + 1.3) + 0.9 * math.sin(cx * 1.37 + cy * 0.8)
        h = max(3.0, 5.0 + naik + gel)
        if 13 <= cx <= 17 and cy <= 3:
            h = min(h, 8.0)          # atap lorong, di bawah puncak mulut gua (8,5 m)
        return h

    _tebing_ubin(world, batu, tinggi, (108, 124, 112),
                 tanpa_dinding=lambda x, y: 13 <= x <= 16)   # lorong gua: atap saja


def _dinding_gua(world, tiles, cocok, rgb=(64, 78, 94), dasar=1.9):
    """Dinding gua sebagai tebing menerus, lebih rendah dari tebing luar."""
    batu = _Batu(tiles, cocok)

    def tinggi(cx, cy):
        gel = 0.55 * math.sin(cx * 0.9 + cy * 0.4) + 0.35 * math.sin(cx * 2.1 - cy * 1.7)
        belakang = 1.1 if cy <= 1 else 0.0            # dinding utara menjulang
        return max(1.2, dasar + gel + belakang)

    return _tebing_ubin(world, batu, tinggi, rgb)


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
    _part(world,'cube',((scene.w-1)*TS/2,.1,(scene.h-1)*TS/2),(scene.w*TS,.2,scene.h*TS),(70,84,98))
    _bersihkan_dinding_kubus(world)
    _dinding_gua(world, scene.tiles, lambda x, y, tid: tid == CV_W)
    for x,z,rx,rz in ((6,8,3.6,5),(23,7,4,3),(5,18,4,3),(22,18,4,3),(14,3,3,2)):
        _ground_patch(world,x,z,rx,rz,(62,76,90),x+z)
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
    from game.scenes.fx_suasana import kolam_cahaya, pijar, halo, Partikel
    for y,row in enumerate(scene.tiles):
        for x,tid in enumerate(row):
            if tid==CRYS:
                _disc(world,x*TS,y*TS,.85,(40,52,62),.212)
                kolam_cahaya(world,x*TS,y*TS,3.2,(70,210,220),kuat=.42)
                for k in range(3):
                    # Seed ikut koordinat tile supaya keempat klaster berbeda.
                    seed=x*17+y*29+k
                    pijar(world,_kristal_pijar_mesh(seed,(70+18*k,196+14*k,206+10*k)),
                          (x*TS+(k-1)*.36,.2,y*TS+(k%2)*.3),(.48,.9+k*.33,.48),
                          (255,255,255),rotation=(0,(seed*47)%360,0))
                halo(world,(x*TS,1.0,y*TS),1.9,(90,220,230),kuat=.30)
            elif tid==LN:
                _disc(world,x*TS,y*TS,.53,(44,56,66),.212)
                _part(world,'cube',(x*TS,.53,y*TS),(.6,.65,.6),(110,114,112))
                _part(world,'cube',(x*TS,.91,y*TS),(.83,.13,.83),(118,108,84))
                pijar(world,'sphere',(x*TS,1.1,y*TS),(.34,.42,.34),(255,196,96))
                pijar(world,'sphere',(x*TS,1.16,y*TS),(.18,.26,.18),(255,244,200))
                halo(world,(x*TS,1.12,y*TS),1.6,(255,170,80),kuat=.50)
                kolam_cahaya(world,x*TS,y*TS,3.6,(255,150,70),kuat=.38)

    # Lingkaran ritual memancarkan cahaya emas tipis di bawah sang penjaga.
    kolam_cahaya(world,7*TS,6*TS,4.6,(230,190,110),kuat=.22)
    for r in (3.4, 2.8):
        _cincin_pijar(world,7*TS,6*TS,r,(240,205,130))
    # Debu kristal melayang di seluruh ruang, bara kecil di atas tiap obor.
    Partikel(world,1*TS,13*TS,1*TS,10*TS,.4,3.2,30,(140,235,240),
             ukuran=.05,naik=.08,goyang=.25,seed=11)
    for y,row in enumerate(scene.tiles):
        for x,tid in enumerate(row):
            if tid==LN:
                Partikel(world,x*TS-.25,x*TS+.25,y*TS-.25,y*TS+.25,1.15,2.4,5,
                         (255,180,90),ukuran=.035,naik=.55,goyang=.18,seed=x*7+y)


def _cincin_pijar(world, x, z, r, rgb, y=.226, tebal=.06):
    from ursina import Mesh
    from game.scenes.fx_suasana import _aditif, _daftar
    from ursina import Entity, color
    from ursina.shaders import unlit_shader
    verts = []
    for i in range(72):
        a, b = i * math.tau / 72, (i + 1) * math.tau / 72
        p = [(math.cos(a)*(r-tebal), 0, math.sin(a)*(r-tebal)), (math.cos(a)*(r+tebal), 0, math.sin(a)*(r+tebal)),
             (math.cos(b)*(r+tebal), 0, math.sin(b)*(r+tebal)), (math.cos(b)*(r-tebal), 0, math.sin(b)*(r-tebal))]
        verts.extend([p[0], p[2], p[1], p[0], p[3], p[2]])
    e = Entity(model=Mesh(vertices=verts), position=(x, y, z), color=color.rgba(*rgb, 150),
               shader=unlit_shader, double_sided=True)
    _aditif(e)
    _daftar(world, e)


def _pinus(world, wx, wz):
    """Pinus gunung: batang lurus dan empat kerucut daun yang menyempit ke atas."""
    from ursina.models.procedural.cone import Cone
    from game.config import TREE_H
    v = abs(math.sin(wx * 17.3 + wz * 29.1))
    s = .85 + .3 * v
    ents = [_part(world, 'cylinder', (wx, TREE_H * .3 * s, wz), (.36, TREE_H * .6 * s, .36),
                  (116 + int(v * 20), 92 + int(v * 14), 72))]
    for k, (r, h, y) in enumerate(((1.9, 1.7, .55), (1.55, 1.5, .9), (1.15, 1.3, 1.22), (.72, 1.1, 1.5))):
        warna = (46 + k * 9 + int(v * 10), 86 + k * 10 + int(v * 12), 70 + k * 6)
        ents.append(_part(world, Cone(resolution=8), (wx, TREE_H * y * s, wz),
                          (r * s, h * s, r * s), warna, rotation=(0, v * 90 + k * 20, 0)))
    return ents


def _puncak_mesh(seed):
    """Gunung jauh: faset terpanggang, kaki biru berkabut, puncak bersalju."""
    from ursina import Mesh, Vec3, color
    rng = __import__('random').Random(seed)
    n = 9
    cincin = []
    for lvl, rad in ((0.0, 1.0), (0.38, 0.66), (0.66, 0.36)):
        cincin.append([Vec3(math.cos(i * math.tau / n) * rad * rng.uniform(.8, 1.15),
                            lvl + rng.uniform(-.04, .04),
                            math.sin(i * math.tau / n) * rad * rng.uniform(.8, 1.15)) for i in range(n)])
    puncak = Vec3(rng.uniform(-.08, .08), 1.0, rng.uniform(-.08, .08))
    arah = Vec3(.4, .7, -.55).normalized()
    verts, cols = [], []
    def segi(a, b, c):
        nrm = (b - a).cross(c - a).normalized()
        if nrm.y < 0:
            nrm = -nrm
        tinggi = (a.y + b.y + c.y) / 3
        if tinggi > .6:
            dasar = (232, 238, 246)
        elif tinggi > .3:
            dasar = (150, 164, 178)
        else:
            dasar = (126, 144, 160)
        terang = .72 + .38 * max(0.0, nrm.dot(arah))
        col = color.rgb(*(min(255, c_ * terang) for c_ in dasar))
        verts.extend((a, b, c)); cols.extend((col, col, col))
    for k in range(2):
        for i in range(n):
            j = (i + 1) % n
            segi(cincin[k][i], cincin[k + 1][i], cincin[k + 1][j])
            segi(cincin[k][i], cincin[k + 1][j], cincin[k][j])
    for i in range(n):
        segi(cincin[2][i], puncak, cincin[2][(i + 1) % n])
    return Mesh(vertices=verts, colors=cols, mode='triangle')


def _pegunungan_jauh(world, scene):
    """Cincin pegunungan di luar peta, ditambah dataran luas di bawahnya."""
    from game.scenes.fx_suasana import pijar
    cx, cz = (scene.w - 1) * TS / 2, (scene.h - 1) * TS / 2
    _part(world, 'cube', (cx, .05, cz), (520, .1, 520), (78, 102, 76))
    rng = __import__('random').Random(77)
    for i in range(18):
        a = i * math.tau / 18 + rng.uniform(-.12, .12)
        d = rng.uniform(85, 140)
        tinggi = rng.uniform(34, 70)
        lebar = tinggi * rng.uniform(.9, 1.3)
        pijar(world, _puncak_mesh(i * 13 + 5), (cx + math.cos(a) * d, -2, cz + math.sin(a) * d),
              (lebar, tinggi, lebar), (255, 255, 255), double_sided=True)


def _padang(world, scene):
    """Rumput tidak lagi satu hijau rata: petak gelap, bunga liar, kerikil."""
    from game.config import G
    rng = __import__('random').Random(31)
    rumput = [(x, y) for y, row in enumerate(scene.tiles) for x, t in enumerate(row) if t == G]
    rng.shuffle(rumput)
    for x, y in rumput[:18]:
        _ground_patch(world, x * TS, y * TS, rng.uniform(1.0, 1.9), rng.uniform(.9, 1.7),
                      (78, 108, 70), x * 5 + y, .214)
    for x, y in rumput[18:58]:
        warna = rng.choice(((236, 214, 86), (238, 238, 232), (176, 140, 214), (232, 132, 120)))
        for _ in range(rng.randint(3, 6)):
            _part(world, 'sphere', (x * TS + rng.uniform(-.8, .8), .3, y * TS + rng.uniform(-.8, .8)),
                  (.14, .1, .14), warna)
    for x, y in rumput[58:78]:
        for _ in range(rng.randint(2, 4)):
            s = rng.uniform(.18, .38)
            _part(world, _rock_mesh(x * 3 + y), (x * TS + rng.uniform(-.7, .7), .2, y * TS + rng.uniform(-.7, .7)),
                  (s, s * .55, s), (128, 132, 124), rotation=(0, rng.uniform(0, 360), 0))


def build_mountain_landscape(world, scene):
    from game.scenes.props import default_prop_builder
    from game.config import G,P,D,DR,TR,DT
    default_prop_builder(world,scene,pembangun_pohon=_pinus)
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
    _tebing_menerus(world,scene)
    # Penyaring di atas ikut mematikan tutup rumput bertekstur (yang diayun
    # angin) dan sebaran helai rumput -- lereng jadi satu hijau polos.
    for e in world._grass_ents:
        e.enabled=True
    for e in getattr(world,'_sebaran_ents',()):
        e.enabled=True
    _pegunungan_jauh(world,scene)
    _padang(world,scene)
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
    from ursina.shaders import unlit_shader
    _gelap=_part(world,Mesh(vertices=verts),(0,0,0),(1,1,1),(6,8,9),smooth=False,
                 double_sided=True,shader=unlit_shader)
    try:
        _gelap.setFogOff(); _gelap.setLightOff()
    except Exception:
        pass
    _mulut_gua(world)
    _lore_lama(world, scene)


def _mulut_gua(world):
    """Mulut gua sungguhan di ujung jalur: SATU tebing utuh berlubang lengkung.

    Sebelumnya ujung jalan hanya diapit dua batu dan langit biru tembus di
    antaranya. Percobaan pertama memakai model Blender `mulut_gua` (cincin
    bongkah) ditambah gumpalan penutup -- hasilnya berlapis-lapis, bukan satu
    bukit. Sekarang mukanya satu permukaan menerus: kontur luar berbentuk
    punggung bukit, kontur dalam lengkung pintu, dan keduanya disambung
    sebagai satu cangkang tebal. Lubangnya diisi kegelapan, obor di kedua sisi.
    """
    from ursina import Mesh
    cx, cz = 14.5 * TS, 2.9 * TS          # tengah ambang ubin DR
    gy = GROUND_H
    n = 18
    ow, oh = 7.0, 8.5                     # kontur luar (punggung bukit)
    iw, ih = 2.3, 3.9                     # kontur dalam (lubang pintu)
    tebal = 3.0

    def kasar(i, amp):
        # Derau tetap per titik: tepi bukit tidak licin seperti busur jangka.
        return 1.0 + amp * math.sin(i * 2.399 + 0.7) * math.cos(i * 1.31)

    luar, dalam = [], []
    for i in range(n + 1):
        t = math.pi * i / n
        r = kasar(i, 0.06) if 0 < i < n else 1.0
        luar.append((math.cos(t) * ow * r, max(0.0, math.sin(t) ** 0.7 * oh * r)))
        dalam.append((math.cos(t) * iw, math.sin(t) ** 0.55 * ih))

    v = []
    def tri(a, b, c):
        v.extend((a, b, c))
    def quad(a, b, c, d):
        tri(a, b, c); tri(a, c, d)
    def P(xy, z):
        return (cx + xy[0], gy + xy[1], cz + z)

    zf, zb = 0.0, -tebal                   # muka depan menghadap jalur (+z)
    for i in range(n):
        lo, lo2, di, di2 = luar[i], luar[i + 1], dalam[i], dalam[i + 1]
        quad(P(lo, zf), P(lo2, zf), P(di2, zf), P(di, zf))        # muka depan
        quad(P(lo2, zb), P(lo, zb), P(di, zb), P(di2, zb))        # muka belakang
        quad(P(lo, zb), P(lo2, zb), P(lo2, zf), P(lo, zf))        # punggung bukit
        quad(P(di2, zb), P(di, zb), P(di, zf), P(di2, zf))        # langit-langit lorong
    _part(world, Mesh(vertices=v, triangles=list(range(len(v)))), (0, 0, 0), (1, 1, 1),
          (108, 124, 112), double_sided=True)

    # Kegelapan di dalam lorong dan dinding belakang yang menutup langit.
    # Tanpa cahaya dan kabut: kalau ikut diterangi, kabut jarak mewarnainya
    # biru langit dan lubangnya terbaca tembus, bukan gelap.
    from ursina.shaders import unlit_shader
    for pos, skala, rgb in (((cx, gy + ih / 2, cz - tebal - 0.2), (iw * 2.2, ih + 0.4, 0.3), (6, 8, 9)),
                            ((cx, gy + 0.02, cz - tebal / 2), (iw * 2, 0.04, tebal), (20, 22, 22))):
        e = _part(world, 'cube', pos, skala, rgb, shader=unlit_shader)
        try:
            e.setFogOff(); e.setLightOff()
        except Exception:
            pass
    for sx in (-1, 1):
        x = cx + sx * (iw + 0.9)
        _part(world, 'cube', (x, gy + 0.75, cz + 0.6), (0.09, 1.5, 0.09), (72, 52, 36))
        _part(world, 'cube', (x, gy + 1.6, cz + 0.6), (0.22, 0.3, 0.22), (255, 168, 70))


def _shrine(world, wx, wz):
    """Altar batu kecil -- sisa titik sembahyang di persimpangan jalan lama.

    Dulu `SHRINE` di grid mountain.py; tidak punya builder atau tekstur
    sendiri (lihat `objects.py`/`world.py`), jadi di sini ditaruh sebagai
    primitif polos lewat `_part()`, sama seperti batu dan tambalan tanah di
    atas -- bukan ubin grid, supaya tidak ikut dibaca `_rocks()` maupun
    pathfinder.
    """
    alas   = _part(world, 'cube', (wx, GROUND_H + 0.09, wz), (TS*0.62, 0.18, TS*0.62), (118, 112, 100))
    tubuh  = _part(world, 'cube', (wx, GROUND_H + 0.46, wz), (TS*0.30, 0.56, TS*0.30), (132, 128, 118))
    puncak = _part(world, 'cube', (wx, GROUND_H + 0.80, wz), (TS*0.38, 0.10, TS*0.38), (96, 92, 84))


def _debris(world, wx, wz, putar=0.0):
    """Onggokan kecil -- sisa peralatan perkebunan karet yang ditinggalkan.

    Sama seperti `_shrine`: dulu ubin `DEBRIS`, tanpa builder/tekstur sendiri,
    sekarang dua kotak kayu lapuk yang diputar beda sudut supaya tidak
    terbaca sebagai satu balok utuh.
    """
    a = _part(world, 'cube', (wx - 0.10, GROUND_H + 0.11, wz + 0.06),
              (TS*0.34, 0.22, TS*0.28), (82, 70, 54), rotation=(0, putar, 0))
    b = _part(world, 'cube', (wx + 0.14, GROUND_H + 0.07, wz - 0.10),
              (TS*0.24, 0.14, TS*0.20), (72, 62, 50), rotation=(0, putar + 41.0, 0))


def _lore_lama(world, scene):
    """Jejak lore dari mountain.py lama (sebelum rock_sanctuary menggantinya).

    Tata letak tangan yang lama (lahan karet bekas, shrine di persimpangan
    jalan, debris peralatan, lentera di tepi jalan, nisan dekat cabang
    kuburan) memakai grid bebas yang tidak punya padanan 1:1 di geometri
    rect/vline prosedural sekarang. Elemen-elemennya dipindah ke titik
    TERBUKA yang setara secara naratif pada peta baru, dan ditaruh lewat
    `_part()`/builder prop langsung -- BUKAN lewat `scene.tiles` -- supaya
    tidak mengubah dinding `CV_W` yang dibaca `_rocks()` atau grid yang
    dibaca pathfinder. Koordinat dalam UBIN, dikonversi ke dunia di sini.
    """
    from game.scenes.props import build_lantern, build_grave

    # Shrine: dua altar di sisi pelataran gua, menggantikan dua SHRINE lama
    # di persimpangan jalan (m[12][12], m[18][16]).
    for tx, ty in ((10, 8), (19, 12)):
        _shrine(world, tx * TS, ty * TS)

    # Debris: sisa peralatan perkebunan, dulu tersebar lima titik lebar;
    # di sini empat titik di lereng terbuka, kiri dan kanan.
    for i, (tx, ty) in enumerate(((8, 13), (20, 9), (4, 17), (26, 18))):
        _debris(world, tx * TS, ty * TS, putar=i * 53.0)

    # Lentera: di tepi jalan utama (bukan DI jalannya), tiga titik dari
    # pelataran gua sampai turunan ke desa.
    for tx, ty in ((12, 5), (17, 9), (12, 18)):
        build_lantern(world, tx * TS, ty * TS)

    # Nisan: kuburan lama di dekat cabang jalan menuju portal (2,24) ->
    # cemetery, digeser dari kolom jalan (x=2-3 dan y=19-20 dipakai
    # vline/hline) ke bahu jalan di sebelahnya.
    for tx, ty in ((5, 21), (4, 22), (7, 22), (5, 23)):
        build_grave(world, tx * TS, ty * TS)


# ═══ GUA BERTINGKAT (DUNGEON) ═══════════════════════════════════════════════
# Warna urat bijih: harus terbaca dari jauh di lantai gelap, jadi dipijarkan.
_WARNA_BIJIH = {
    'ORE_TBG': (214, 128, 66),    # tembaga
    'ORE_BSI': (176, 182, 206),   # besi
    'ORE_EMS': (255, 214, 84),    # emas
    'ORE_KRS': (196, 150, 255),   # kristal
    'ORE_MTH': (130, 232, 255),   # mithril
}


def build_dungeon(world, scene):
    """Gua bertingkat: lantai batu gelap menyatu, dinding tebing, bijih nyata.

    Sebelumnya dungeon memakai builder bawaan, yang membaca peta PLACEHOLDER
    (semua lantai) dan bukan `state.dungeon_tiles` hasil generator. Akibatnya:
    bijih tambang tidak pernah digambar (world.py menyerahkannya ke builder),
    lantai `cave_floor` terbakar putih oleh bloom, dan dinding hanya kubus
    gelap. Menambang memuat ulang scene, jadi builder ini ikut terpanggil lagi
    dan bijih yang sudah ditambang hilang dengan sendirinya.
    """
    import random
    from game import config as K
    from game.scenes.fx_suasana import kolam_cahaya, pijar, halo, Partikel
    tiles = getattr(world.state, 'dungeon_tiles', None) or scene.tiles
    lvl = max(1, int(getattr(world.state, 'dungeon_level', 1) or 1))
    rng = random.Random(lvl * 101 + 7)
    h_, w_ = len(tiles), len(tiles[0])
    bijih = {getattr(K, n): rgb for n, rgb in _WARNA_BIJIH.items()}
    tampak = {K.STAIRS_UP, K.STAIRS_DOWN, K.W, K.DCK, K.LLY}

    for e in world._tile_ents:
        tx, ty = int(round(e.x / TS)), int(round(e.z / TS))
        if not (0 <= ty < h_ and 0 <= tx < w_) or tiles[ty][tx] not in tampak:
            e.enabled = False
    _bersihkan_dinding_kubus(world)

    # Makin dalam makin dingin: coklat tanah di lantai atas, biru di bawah.
    t = min(1.0, (lvl - 1) / 14)
    def campur(a, b):
        return tuple(int(x + (y - x) * t) for x, y in zip(a, b))
    # Lantai lebih terang dari dinding: jalur harus terbaca sekilas, karena
    # tinggi dinding saja tidak cukup dari kamera atas yang serong.
    lantai, dinding = campur((104, 94, 82), (72, 84, 108)), campur((54, 50, 47), (38, 46, 64))

    _part(world, 'cube', ((w_ - 1) * TS / 2, .1, (h_ - 1) * TS / 2), (w_ * TS, .2, h_ * TS), lantai)
    for _ in range(6):
        x, z = rng.uniform(2, w_ - 3) * TS, rng.uniform(2, h_ - 3) * TS
        _ground_patch(world, x, z, rng.uniform(2, 4), rng.uniform(2, 3.5),
                      tuple(c - 8 for c in lantai), int(x + z))
    _dinding_gua(world, tiles, lambda x, y, tid: tid == K.CV_W, dinding, dasar=2.2)

    lantai_bebas = []
    for y in range(h_):
        for x in range(w_):
            tid = tiles[y][x]
            wx, wz = x * TS, y * TS
            if tid in bijih:
                rgb = bijih[tid]
                _part(world, _rock_mesh(x * 31 + y * 17), (wx, .2, wz), (1.55, 1.05, 1.55), dinding)
                for k in range(3):
                    seed = x * 13 + y * 7 + k
                    pijar(world, _kristal_pijar_mesh(seed, rgb),
                          (wx + (k - 1) * .32, .55 + .2 * (k % 2), wz + (k % 2 - .5) * .3),
                          (.26, .42 + .12 * k, .26), (255, 255, 255),
                          rotation=(15 * (k - 1), (seed * 53) % 360, 0))
                if tid in (K.ORE_EMS, K.ORE_KRS, K.ORE_MTH):
                    halo(world, (wx, .9, wz), 1.1, rgb, kuat=.22)
            elif tid == K.CRYS:
                for k in range(3):
                    seed = x * 17 + y * 29 + k
                    pijar(world, _kristal_pijar_mesh(seed, (70 + 18 * k, 196 + 14 * k, 206 + 10 * k)),
                          (wx + (k - 1) * .36, .2, wz + (k % 2) * .3), (.48, .9 + k * .33, .48),
                          (255, 255, 255), rotation=(0, (seed * 47) % 360, 0))
                kolam_cahaya(world, wx, wz, 3.0, (70, 210, 220), kuat=.38)
                halo(world, (wx, 1.0, wz), 1.7, (90, 220, 230), kuat=.28)
            elif tid == K.STAIRS_DOWN:
                kolam_cahaya(world, wx, wz, 2.6, (90, 150, 255), kuat=.40)
            elif tid == K.STAIRS_UP:
                kolam_cahaya(world, wx, wz, 2.6, (255, 190, 110), kuat=.40)
            elif tid in (K.CV_F, K.MINED):
                lantai_bebas.append((x, y))

    # Obor di lantai yang menempel dinding: penerang yang terbaca dari mana saja.
    tepi = [(x, y) for x, y in lantai_bebas
            if sum(tiles[y + dy][x + dx] == K.CV_W
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                   if 0 <= x + dx < w_ and 0 <= y + dy < h_) >= 2]
    rng.shuffle(tepi)
    for x, y in tepi[:5]:
        wx, wz = x * TS, y * TS
        _part(world, 'cube', (wx, .6, wz), (.12, 1.0, .12), (70, 52, 38))
        pijar(world, 'sphere', (wx, 1.18, wz), (.22, .3, .22), (255, 178, 90))
        halo(world, (wx, 1.2, wz), 1.3, (255, 160, 80), kuat=.45)
        kolam_cahaya(world, wx, wz, 3.4, (255, 140, 60), kuat=.30)
    Partikel(world, 1 * TS, (w_ - 2) * TS, 1 * TS, (h_ - 2) * TS, .4, 2.8, 26,
             (150, 200, 240) if t > .4 else (230, 190, 140),
             ukuran=.045, naik=.06, goyang=.25, seed=lvl)
