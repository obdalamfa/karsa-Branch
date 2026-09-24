"""Procedural cave spirits with continuous low-poly silhouettes."""
import math
from ursina import Entity, Mesh, Shader, Vec3, color
from .config import GROUND_H


# Cave-specific material: a generous fill preserves the jade surface in shadow.
# No scene-wide shader is changed, and edge darkening cannot swallow the coil.
_MATERIAL = Shader(language=Shader.GLSL, vertex='''
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
out vec3 normal_world;
void main() {
    normal_world = normalize(mat3(p3d_ModelMatrix) * p3d_Normal);
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
''', fragment='''
#version 140
uniform vec4 p3d_ColorScale;
in vec3 normal_world;
out vec4 fragColor;
void main() {
    vec3 n = normalize(normal_world);
    float key = max(0.0, dot(n, normalize(vec3(-0.4, 0.8, 0.5))));
    float top = max(0.0, n.y);
    vec3 lit = p3d_ColorScale.rgb * (0.72 + 0.35 * key);
    lit += vec3(0.025, 0.045, 0.035) * top;
    fragColor = vec4(lit, p3d_ColorScale.a);
}
''')


def _contact_shadow(actor, radius):
    """One feathered disk, parented to the actor but never to its bobbing flame."""
    verts, shades, tris = [(0,0,0)], [color.rgba(12,25,28,75)], []
    for j in range(33):
        a=j*math.tau/32
        verts.append((math.cos(a)*radius,0,math.sin(a)*radius*.8))
        shades.append(color.rgba(12,25,28,0))
    for j in range(32):
        tris.append((0,j+2,j+1))
    return Entity(parent=actor, y=GROUND_H+.013,
                  model=Mesh(vertices=verts, triangles=tris, colors=shades),
                  unlit=True, double_sided=True)


def _tube(points, radii, sides=9, flatten=1.0):
    """Solid tapered sweep with explicit normals and closed ends."""
    points = [Vec3(*p) for p in points]
    vertices, normals, triangles = [], [], []
    for i, point in enumerate(points):
        tangent = (points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        reference = Vec3(0,1,0) if abs(tangent.y)<.92 else Vec3(0,0,1)
        side = tangent.cross(reference).normalized()
        up = side.cross(tangent).normalized()
        for j in range(sides):
            angle = j*math.tau/sides
            radial = side*math.cos(angle)+up*math.sin(angle)*flatten
            vertices.append(point+radial*radii[i])
            # Elliptical sections need inverse-axis normals, not radial normals.
            normal = side*math.cos(angle)+up*math.sin(angle)/flatten
            normals.append(normal.normalized())
    for i in range(len(points)-1):
        for j in range(sides):
            a,b=i*sides+j,i*sides+(j+1)%sides
            triangles.extend(((a,a+sides,b),(b,a+sides,b+sides)))
    for ring,direction in ((0,-1),(len(points)-1,1)):
        tangent=(points[min(ring+1,len(points)-1)]-points[max(0,ring-1)]).normalized()*direction
        start=len(vertices)
        vertices.append(points[ring]); normals.append(tangent)
        for j in range(sides):
            vertices.append(vertices[ring*sides+j]); normals.append(tangent)
        for j in range(sides):
            a,b=start+1+j,start+1+(j+1)%sides
            triangles.append((start,b,a) if direction>0 else (start,a,b))
    return Mesh(vertices=vertices,triangles=triangles,normals=normals,mode='triangle')


def build_guardian(actor, kind):
    root=Entity(parent=actor,y=GROUND_H)
    actor._guardian_motion = root
    actor._guardian_kind = kind
    actor._guardian_time = 0.0
    actor._guardian_embers = []
    # Satu-satunya penanda apakah penunggu ini melayang. Pemanggil di
    # entities.py memakainya untuk memutuskan bobbing; sebelumnya keputusan itu
    # diambil dari `hasattr(actor, '_guardian_visual')`, yang hanya benar secara
    # kebetulan karena cabang naga_bijak `return` lebih awal.
    actor._guardian_floats = (kind != 'naga_bijak')
    _contact_shadow(actor, 1.15 if kind == 'naga_bijak' else .60)

    def tube(points,radii,tint,sides=9,flatten=1.,glowing=False):
        entity=Entity(parent=root,model=_tube(points,radii,sides,flatten),color=color.rgb(*tint))
        if glowing:
            entity.unlit=True
        else:
            entity.shader = _MATERIAL
        return entity

    jade,light_jade=(72,166,139),(108,195,157)
    gold,ivory=(208,160,68),(243,221,161)
    if kind=='naga_bijak':
        # Thin tail flows into a complete coil, then a poised S-shaped neck.
        path,widths=[],[]
        for i in range(39):
            t=i/38
            angle=-.55+t*math.tau*1.17
            radius=1.08-.52*t
            path.append((math.cos(angle)*radius,.24+.18*t,math.sin(angle)*radius))
            widths.append(.025+.25*min(t*3,1))
        path += [(.12,.61,.59),(-.07,.91,.51),(-.16,1.23,.36),(-.12,1.54,.30),(0,1.81,.40),(0,1.93,.62)]
        widths += [.27,.255,.235,.235,.28,.28]
        tube(path,widths,jade,12)
        for x,y,z,w in [(-.07,.83,.70,.20),(-.14,1.05,.65,.18),(-.15,1.28,.58,.18),(-.09,1.51,.53,.19)]:
            tube([(x-w,y,z),(x,y-.025,z+.05),(x+w,y,z)],[.065,.073,.065],gold,6)
        tube([(0,1.88,.43),(0,1.91,.68),(0,1.82,1.05)],[.29,.34,.20],light_jade,8,.75)
        tube([(0,1.69,.71),(0,1.67,1.05)],[.24,.18],(38,47,42),8,.22)
        tube([(0,1.61,.63),(0,1.60,1.04)],[.23,.17],gold,8,.30)
        for s in (-1,1):
            tube([(s*.22,2.03,.46),(s*.37,2.25,.30),(s*.41,2.51,.15)],[.105,.07,.003],gold,7)
            tube([(s*.30,1.97,.69),(s*.41,2.,.53),(s*.57,2.05,.43)],[.095,.07,.001],jade,6)
            tube([(s*.26,1.88,.79),(s*.275,1.88,.88)],[.085,.074],ivory,8,.50,True)
            tube([(s*.28,1.885,.875),(s*.285,1.885,.899)],[.034,.033],(19,34,34),6,.75,True)
            tube([(s*.14,1.78,1.04),(s*.41,1.76,1.12),(s*.66,1.90,1.13)],[.035,.022,.001],ivory,6)
            tube([(s*.14,1.69,.93),(s*.14,1.57,.96)],[.04,.001],ivory,5)
        for i in range(8,36,4):
            x,y,z=path[i]
            tube([(x,y+widths[i]*.85,z),(x*.96,y+widths[i]+.19,z*.96)],[.11,.001],gold,4,.45)
        for y,z in ((1.03,.25),(1.32,.13),(1.58,.08)):
            tube([(-.13,y,z),(-.13,y+.12,z-.22)],[.11,.001],gold,4,.5)
        return 2.8

    # Curled flame tongues and an incandescent core, rather than stacked balls.
    tube([(0,.48,0),(0,.84,0),(.02,1.20,0),(-.10,1.54,0),(.08,1.94,0),(.03,2.40,0)],
         [.04,.42,.49,.33,.18,.001],(211,64,28),10,.85,True)
    for s,height in ((-1,1.95),(1,1.80)):
        tube([(s*.22,.71,0),(s*.44,1.05,0),(s*.56,1.40,.02),(s*.43,height,.04)],
             [.20,.23,.14,.001],(243,118,29),7,.75,True)
    tube([(0,.61,.29),(0,.98,.32),(-.02,1.32,.31),(.10,1.62,.24),(.04,1.94,.16)],
         [.03,.29,.32,.18,.001],(255,189,53),9,.50,True)
    tube([(0,.74,.40),(0,1.05,.46),(.03,1.34,.45),(-.03,1.63,.35)],
         [.03,.19,.17,.001],(255,234,133),8,.5,True)
    for s in (-1,1):
        tube([(s*.065,1.25,.54),(s*.22,1.31,.50)],[.068,.043],(67,31,29),4,.65,True)
        tube([(s*.09,1.25,.573),(s*.17,1.28,.553)],[.021,.018],(255,249,193),5,.6,True)
    tube([(-.15,1.02,.53),(0,.96,.57),(.15,1.02,.53)],[.037,.053,.037],(80,31,27),5,.50,True)
    for x,y,z in [(-.68,1.9,.03),(.47,2.16,-.07),(-.21,2.59,0)]:
        ember = tube([(x,y,z),(x+.025,y+.12,z),(x+.07,y+.22,z)],[.025,.035,.001],(255,182,49),5,1,True)
        actor._guardian_embers.append(ember)
    # Hanya banaspati yang punya simpul bobbing; naga_bijak tidak pernah sampai
    # baris ini. Penanda `_guardian_floats` di atas yang menyatakannya.
    actor._guardian_visual=root
    return 2.9


def update_guardian(actor, dt):
    """Secondary idle motion; existing actor code still owns hovering and facing."""
    root = getattr(actor, '_guardian_motion', None)
    if root is None:
        return
    actor._guardian_time += max(0.0, dt)
    t = actor._guardian_time
    if actor._guardian_kind == 'naga_bijak':
        # Scaling about the floor leaves the coil grounded.
        root.scale_y = 1 + math.sin(t*1.35)*.008
    else:
        root.scale_y = 1 + math.sin(t*4.1)*.022 + math.sin(t*7.3)*.01
        root.scale_x = 1 + math.sin(t*3.2)*.022
        root.rotation_z = math.sin(t*1.8)*1.5
        for i, ember in enumerate(actor._guardian_embers):
            ember.y = math.sin(t*2.0+i*2.1)*.07
            ember.x = math.sin(t*1.6+i*1.4)*.035
