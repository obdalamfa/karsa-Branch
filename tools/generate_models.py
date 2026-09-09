import math
import os
from pathlib import Path

# --- CORE SHAPE PRIMITIVES ---

def get_unit_box():
    # Flat shaded cube with 24 vertices for perfect normals
    face_definitions = [
        # Front (-Z)
        ([(-0.5, -0.5, -0.5), (-0.5,  0.5, -0.5), ( 0.5,  0.5, -0.5), ( 0.5, -0.5, -0.5)], (0, 0, -1)),
        # Back (+Z)
        ([( 0.5, -0.5,  0.5), ( 0.5,  0.5,  0.5), (-0.5,  0.5,  0.5), (-0.5, -0.5,  0.5)], (0, 0, 1)),
        # Left (-X)
        ([(-0.5, -0.5,  0.5), (-0.5,  0.5,  0.5), (-0.5,  0.5, -0.5), (-0.5, -0.5, -0.5)], (-1, 0, 0)),
        # Right (+X)
        ([( 0.5, -0.5, -0.5), ( 0.5,  0.5, -0.5), ( 0.5,  0.5,  0.5), ( 0.5, -0.5,  0.5)], (1, 0, 0)),
        # Top (+Y)
        ([(-0.5,  0.5, -0.5), (-0.5,  0.5,  0.5), ( 0.5,  0.5,  0.5), ( 0.5,  0.5, -0.5)], (0, 1, 0)),
        # Bottom (-Y)
        ([(-0.5, -0.5,  0.5), (-0.5, -0.5, -0.5), ( 0.5, -0.5, -0.5), ( 0.5, -0.5,  0.5)], (0, -1, 0)),
    ]
    
    verts = []
    norms = []
    uvs = []
    tris = []
    
    for corners, normal in face_definitions:
        start_idx = len(verts)
        verts.extend(corners)
        norms.extend([normal] * 4)
        uvs.extend([(0, 0), (0, 1), (1, 1), (1, 0)])
        tris.append((start_idx, start_idx + 1, start_idx + 2))
        tris.append((start_idx, start_idx + 2, start_idx + 3))
        
    return verts, norms, uvs, tris

def get_unit_cylinder(segments=12):
    verts = []
    norms = []
    uvs = []
    tris = []
    
    # Top cap (Y = 0.5)
    top_start = len(verts)
    verts.append((0, 0.5, 0))
    norms.append((0, 1, 0))
    uvs.append((0.5, 0.5))
    for i in range(segments):
        theta = i * 2 * math.pi / segments
        verts.append((0.5 * math.cos(theta), 0.5, 0.5 * math.sin(theta)))
        norms.append((0, 1, 0))
        uvs.append((0.5 + 0.5 * math.cos(theta), 0.5 + 0.5 * math.sin(theta)))
    for i in range(segments):
        i1 = i + 1
        i2 = (i + 1) % segments + 1
        tris.append((top_start, top_start + i2, top_start + i1))
        
    # Bottom cap (Y = -0.5)
    bot_start = len(verts)
    verts.append((0, -0.5, 0))
    norms.append((0, -1, 0))
    uvs.append((0.5, 0.5))
    for i in range(segments):
        theta = i * 2 * math.pi / segments
        verts.append((0.5 * math.cos(theta), -0.5, 0.5 * math.sin(theta)))
        norms.append((0, -1, 0))
        uvs.append((0.5 + 0.5 * math.cos(theta), 0.5 + 0.5 * math.sin(theta)))
    for i in range(segments):
        i1 = i + 1
        i2 = (i + 1) % segments + 1
        tris.append((bot_start, bot_start + i1, bot_start + i2))
        
    # Side faces
    side_start = len(verts)
    for i in range(segments + 1):
        theta = i * 2 * math.pi / segments
        c, s = math.cos(theta), math.sin(theta)
        # top side vert
        verts.append((0.5 * c, 0.5, 0.5 * s))
        norms.append((c, 0, s))
        uvs.append((i / segments, 1))
        # bot side vert
        verts.append((0.5 * c, -0.5, 0.5 * s))
        norms.append((c, 0, s))
        uvs.append((i / segments, 0))
        
    for i in range(segments):
        a = side_start + 2 * i
        b = a + 1
        c = side_start + 2 * (i + 1)
        d = c + 1
        tris.append((a, c, b))
        tris.append((b, c, d))
        
    return verts, norms, uvs, tris

def get_unit_cone(segments=12):
    verts = []
    norms = []
    uvs = []
    tris = []
    
    # Bottom cap (Y = -0.5)
    bot_start = len(verts)
    verts.append((0, -0.5, 0))
    norms.append((0, -1, 0))
    uvs.append((0.5, 0.5))
    for i in range(segments):
        theta = i * 2 * math.pi / segments
        verts.append((0.5 * math.cos(theta), -0.5, 0.5 * math.sin(theta)))
        norms.append((0, -1, 0))
        uvs.append((0.5 + 0.5 * math.cos(theta), 0.5 + 0.5 * math.sin(theta)))
    for i in range(segments):
        i1 = i + 1
        i2 = (i + 1) % segments + 1
        tris.append((bot_start, bot_start + i1, bot_start + i2))
        
    # Cone sides
    side_start = len(verts)
    for i in range(segments + 1):
        theta = i * 2 * math.pi / segments
        c, s = math.cos(theta), math.sin(theta)
        verts.append((0.5 * c, -0.5, 0.5 * s))
        nx, ny, nz = c, 0.5, s
        l = math.hypot(nx, math.hypot(ny, nz))
        norms.append((nx/l, ny/l, nz/l))
        uvs.append((i / segments, 0))
        
        verts.append((0, 0.5, 0))
        norms.append((nx/l, ny/l, nz/l))
        uvs.append((i / segments, 1))
        
    for i in range(segments):
        a = side_start + 2 * i
        b = a + 1
        c = side_start + 2 * (i + 1)
        d = c + 1
        tris.append((a, c, b))
        
    return verts, norms, uvs, tris

def get_unit_sphere(segments_u=12, segments_v=8):
    verts = []
    norms = []
    uvs = []
    for j in range(segments_v + 1):
        v = j / segments_v
        theta = v * math.pi
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)
        for i in range(segments_u + 1):
            u = i / segments_u
            phi = u * 2 * math.pi
            sin_phi = math.sin(phi)
            cos_phi = math.cos(phi)
            
            x = 0.5 * sin_theta * cos_phi
            y = 0.5 * cos_theta
            z = 0.5 * sin_theta * sin_phi
            
            verts.append((x, y, z))
            nx, ny, nz = x, y, z
            l = math.hypot(x, math.hypot(y, z))
            if l > 0.0001:
                nx, ny, nz = nx / l, ny / l, nz / l
            norms.append((nx, ny, nz))
            uvs.append((u, v))
            
    tris = []
    for j in range(segments_v):
        for i in range(segments_u):
            a = j * (segments_u + 1) + i
            b = a + 1
            c = a + (segments_u + 1)
            d = c + 1
            tris.append((a, c, b))
            tris.append((b, c, d))
            
    return verts, norms, uvs, tris


# --- MODEL BUILDER CLASS ---

class ModelBuilder:
    def __init__(self):
        self.vertices = []
        self.normals = []
        self.uvs = []
        self.faces = []

    def rotate_point(self, x, y, z, rx, ry, rz):
        # rx, ry, rz in radians
        if rx != 0:
            cx, sx = math.cos(rx), math.sin(rx)
            y, z = y * cx - z * sx, y * sx + z * cx
        if ry != 0:
            cy, sy = math.cos(ry), math.sin(ry)
            x, z = x * cy + z * sy, -x * sy + z * cy
        if rz != 0:
            cz, sz = math.cos(rz), math.sin(rz)
            x, y = x * cz - y * sz, x * sz + y * cz
        return x, y, z

    def add_shape(self, base_mesh_func, pos=(0,0,0), scale=(1,1,1), rot=(0,0,0)):
        base_verts, base_norms, base_uvs, base_tris = base_mesh_func()
        tx, ty, tz = pos
        sx, sy, sz = scale
        rx, ry, rz = rot
        
        start_v = len(self.vertices)
        for x, y, z in base_verts:
            # Scale
            x, y, z = x * sx, y * sy, z * sz
            # Rotate
            x, y, z = self.rotate_point(x, y, z, rx, ry, rz)
            # Translate
            x, y, z = x + tx, y + ty, z + tz
            self.vertices.append((x, y, z))
            
        for nx, ny, nz in base_norms:
            # Rotate normal
            nx, ny, nz = self.rotate_point(nx, ny, nz, rx, ry, rz)
            l = math.hypot(nx, math.hypot(ny, nz))
            if l > 0.0001:
                nx, ny, nz = nx / l, ny / l, nz / l
            self.normals.append((nx, ny, nz))
            
        for u, v in base_uvs:
            self.uvs.append((u, v))
            
        for i0, i1, i2 in base_tris:
            self.faces.append((start_v + i0, start_v + i1, start_v + i2))

    def write_obj(self, filepath):
        lines = ['# Procedural Low-Poly Mesh']
        for x, y, z in self.vertices:
            lines.append(f"v {x:.4f} {y:.4f} {z:.4f}")
        for u, v in self.uvs:
            lines.append(f"vt {u:.4f} {v:.4f}")
        for nx, ny, nz in self.normals:
            lines.append(f"vn {nx:.4f} {ny:.4f} {nz:.4f}")
        for i0, i1, i2 in self.faces:
            v0, v1, v2 = i0 + 1, i1 + 1, i2 + 1
            lines.append(f"f {v0}/{v0}/{v0} {v1}/{v1}/{v1} {v2}/{v2}/{v2}")
            
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('\n'.join(lines), encoding='utf-8')
        print(f"Generated {p.name} with {len(self.vertices)} vertices and {len(self.faces)} faces.")


# --- CREATURE GENERATOR DEFINITIONS ---

def make_mob_kucing(filepath):
    mb = ModelBuilder()
    # Body
    mb.add_shape(get_unit_box, pos=(0, 0.3, 0), scale=(0.4, 0.35, 0.7))
    # Head
    mb.add_shape(get_unit_box, pos=(0, 0.6, 0.3), scale=(0.35, 0.35, 0.35))
    # Snout
    mb.add_shape(get_unit_box, pos=(0, 0.52, 0.47), scale=(0.18, 0.12, 0.1))
    # Ears (Left/Right)
    mb.add_shape(get_unit_cone, pos=(-0.12, 0.82, 0.3), scale=(0.12, 0.18, 0.12), rot=(0, 0, 0.1))
    mb.add_shape(get_unit_cone, pos=(0.12, 0.82, 0.3), scale=(0.12, 0.18, 0.12), rot=(0, 0, -0.1))
    # Legs (FL, FR, BL, BR)
    mb.add_shape(get_unit_cylinder, pos=(-0.15, 0.1, 0.22), scale=(0.1, 0.25, 0.1))
    mb.add_shape(get_unit_cylinder, pos=(0.15, 0.1, 0.22), scale=(0.1, 0.25, 0.1))
    mb.add_shape(get_unit_cylinder, pos=(-0.15, 0.1, -0.22), scale=(0.1, 0.25, 0.1))
    mb.add_shape(get_unit_cylinder, pos=(0.15, 0.1, -0.22), scale=(0.1, 0.25, 0.1))
    # Tail
    mb.add_shape(get_unit_cylinder, pos=(0, 0.42, -0.45), scale=(0.06, 0.4, 0.06), rot=(1.2, 0, 0))
    mb.write_obj(filepath)

def make_mob_sapi(filepath):
    mb = ModelBuilder()
    # Body
    mb.add_shape(get_unit_box, pos=(0, 0.8, 0), scale=(1.0, 0.9, 1.6))
    # Head
    mb.add_shape(get_unit_box, pos=(0, 1.35, 0.8), scale=(0.6, 0.6, 0.6))
    # Snout
    mb.add_shape(get_unit_box, pos=(0, 1.15, 1.12), scale=(0.45, 0.3, 0.35))
    # Horns (Left/Right)
    mb.add_shape(get_unit_cone, pos=(-0.3, 1.7, 0.8), scale=(0.12, 0.3, 0.12), rot=(0, 0, 0.5))
    mb.add_shape(get_unit_cone, pos=(0.3, 1.7, 0.8), scale=(0.12, 0.3, 0.12), rot=(0, 0, -0.5))
    # Ears (Left/Right)
    mb.add_shape(get_unit_box, pos=(-0.4, 1.45, 0.7), scale=(0.25, 0.1, 0.12), rot=(0, 0, -0.3))
    mb.add_shape(get_unit_box, pos=(0.4, 1.45, 0.7), scale=(0.25, 0.1, 0.12), rot=(0, 0, 0.3))
    # Legs (FL, FR, BL, BR)
    mb.add_shape(get_unit_cylinder, pos=(-0.35, 0.35, 0.55), scale=(0.18, 0.7, 0.18))
    mb.add_shape(get_unit_cylinder, pos=(0.35, 0.35, 0.55), scale=(0.18, 0.7, 0.18))
    mb.add_shape(get_unit_cylinder, pos=(-0.35, 0.35, -0.55), scale=(0.18, 0.7, 0.18))
    mb.add_shape(get_unit_cylinder, pos=(0.35, 0.35, -0.55), scale=(0.18, 0.7, 0.18))
    mb.write_obj(filepath)

def make_mob_kambing(filepath):
    mb = ModelBuilder()
    # Body
    mb.add_shape(get_unit_box, pos=(0, 0.65, 0), scale=(0.6, 0.6, 1.0))
    # Head
    mb.add_shape(get_unit_box, pos=(0, 1.05, 0.5), scale=(0.35, 0.45, 0.4))
    # Snout
    mb.add_shape(get_unit_box, pos=(0, 0.9, 0.72), scale=(0.25, 0.22, 0.25))
    # Horns (Left/Right)
    mb.add_shape(get_unit_cone, pos=(-0.12, 1.3, 0.45), scale=(0.08, 0.4, 0.08), rot=(-0.4, 0, 0.1))
    mb.add_shape(get_unit_cone, pos=(0.12, 1.3, 0.45), scale=(0.08, 0.4, 0.08), rot=(-0.4, 0, -0.1))
    # Beard
    mb.add_shape(get_unit_cone, pos=(0, 0.7, 0.65), scale=(0.08, 0.25, 0.08), rot=(-0.2, 0, 0))
    # Legs (FL, FR, BL, BR)
    mb.add_shape(get_unit_cylinder, pos=(-0.22, 0.28, 0.35), scale=(0.12, 0.55, 0.12))
    mb.add_shape(get_unit_cylinder, pos=(0.22, 0.28, 0.35), scale=(0.12, 0.55, 0.12))
    mb.add_shape(get_unit_cylinder, pos=(-0.22, 0.28, -0.35), scale=(0.12, 0.55, 0.12))
    mb.add_shape(get_unit_cylinder, pos=(0.22, 0.28, -0.35), scale=(0.12, 0.55, 0.12))
    mb.write_obj(filepath)

def make_mob_bebek(filepath):
    mb = ModelBuilder()
    # Body
    mb.add_shape(get_unit_box, pos=(0, 0.45, 0), scale=(0.45, 0.45, 0.6))
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 0.8, 0.25), scale=(0.3, 0.3, 0.3))
    # Beak
    mb.add_shape(get_unit_box, pos=(0, 0.75, 0.45), scale=(0.2, 0.08, 0.22))
    # Wings (Left/Right)
    mb.add_shape(get_unit_box, pos=(-0.24, 0.5, 0), scale=(0.06, 0.25, 0.45))
    mb.add_shape(get_unit_box, pos=(0.24, 0.5, 0), scale=(0.06, 0.25, 0.45))
    # Legs (Left/Right)
    mb.add_shape(get_unit_cylinder, pos=(-0.12, 0.15, 0), scale=(0.06, 0.25, 0.06))
    mb.add_shape(get_unit_cylinder, pos=(0.12, 0.15, 0), scale=(0.06, 0.25, 0.06))
    # Feet (Left/Right)
    mb.add_shape(get_unit_box, pos=(-0.12, 0.02, 0.08), scale=(0.15, 0.03, 0.22))
    mb.add_shape(get_unit_box, pos=(0.12, 0.02, 0.08), scale=(0.15, 0.03, 0.22))
    mb.write_obj(filepath)

def make_mob_domba(filepath):
    mb = ModelBuilder()
    # Body (puffy look)
    mb.add_shape(get_unit_sphere, pos=(0, 0.7, 0), scale=(0.85, 0.85, 1.2))
    # Head
    mb.add_shape(get_unit_box, pos=(0, 0.95, 0.6), scale=(0.32, 0.32, 0.38))
    # Ears (Left/Right)
    mb.add_shape(get_unit_box, pos=(-0.22, 0.95, 0.5), scale=(0.2, 0.08, 0.08), rot=(0, 0, -0.4))
    mb.add_shape(get_unit_box, pos=(0.22, 0.95, 0.5), scale=(0.2, 0.08, 0.08), rot=(0, 0, 0.4))
    # Legs (FL, FR, BL, BR)
    mb.add_shape(get_unit_cylinder, pos=(-0.28, 0.28, 0.38), scale=(0.14, 0.55, 0.14))
    mb.add_shape(get_unit_cylinder, pos=(0.28, 0.28, 0.38), scale=(0.14, 0.55, 0.14))
    mb.add_shape(get_unit_cylinder, pos=(-0.28, 0.28, -0.38), scale=(0.14, 0.55, 0.14))
    mb.add_shape(get_unit_cylinder, pos=(0.28, 0.28, -0.38), scale=(0.14, 0.55, 0.14))
    mb.write_obj(filepath)

def make_mob_kuda(filepath):
    mb = ModelBuilder()
    # Body
    mb.add_shape(get_unit_box, pos=(0, 1.0, 0), scale=(0.8, 0.8, 1.6))
    # Neck
    mb.add_shape(get_unit_box, pos=(0, 1.5, 0.65), scale=(0.35, 0.7, 0.35), rot=(0.4, 0, 0))
    # Head
    mb.add_shape(get_unit_box, pos=(0, 1.9, 0.9), scale=(0.4, 0.4, 0.65))
    # Ears (Left/Right)
    mb.add_shape(get_unit_cone, pos=(-0.15, 2.15, 0.7), scale=(0.08, 0.22, 0.08))
    mb.add_shape(get_unit_cone, pos=(0.15, 2.15, 0.7), scale=(0.08, 0.22, 0.08))
    # Wings (Left/Right)
    mb.add_shape(get_unit_box, pos=(-0.45, 1.3, -0.15), scale=(0.06, 0.6, 1.1), rot=(0.2, 0.3, 0.2))
    mb.add_shape(get_unit_box, pos=(0.45, 1.3, -0.15), scale=(0.06, 0.6, 1.1), rot=(0.2, -0.3, -0.2))
    # Legs (FL, FR, BL, BR)
    mb.add_shape(get_unit_cylinder, pos=(-0.3, 0.45, 0.55), scale=(0.16, 0.9, 0.16))
    mb.add_shape(get_unit_cylinder, pos=(0.3, 0.45, 0.55), scale=(0.16, 0.9, 0.16))
    mb.add_shape(get_unit_cylinder, pos=(-0.3, 0.45, -0.55), scale=(0.16, 0.9, 0.16))
    mb.add_shape(get_unit_cylinder, pos=(0.3, 0.45, -0.55), scale=(0.16, 0.9, 0.16))
    mb.write_obj(filepath)

def make_mob_rubah(filepath):
    mb = ModelBuilder()
    # Body
    mb.add_shape(get_unit_box, pos=(0, 0.35, 0), scale=(0.42, 0.35, 0.8))
    # Head
    mb.add_shape(get_unit_box, pos=(0, 0.65, 0.38), scale=(0.3, 0.3, 0.35))
    # Snout
    mb.add_shape(get_unit_cone, pos=(0, 0.56, 0.65), scale=(0.12, 0.26, 0.12), rot=(1.57, 0, 0))
    # Ears (Left/Right)
    mb.add_shape(get_unit_cone, pos=(-0.12, 0.86, 0.38), scale=(0.1, 0.25, 0.1), rot=(0, 0, 0.15))
    mb.add_shape(get_unit_cone, pos=(0.12, 0.86, 0.38), scale=(0.1, 0.25, 0.1), rot=(0, 0, -0.15))
    # Legs (FL, FR, BL, BR)
    mb.add_shape(get_unit_cylinder, pos=(-0.16, 0.15, 0.25), scale=(0.08, 0.3, 0.08))
    mb.add_shape(get_unit_cylinder, pos=(0.16, 0.15, 0.25), scale=(0.08, 0.3, 0.08))
    mb.add_shape(get_unit_cylinder, pos=(-0.16, 0.15, -0.25), scale=(0.08, 0.3, 0.08))
    mb.add_shape(get_unit_cylinder, pos=(0.16, 0.15, -0.25), scale=(0.08, 0.3, 0.08))
    # Tail
    mb.add_shape(get_unit_cone, pos=(0, 0.45, -0.55), scale=(0.18, 0.5, 0.18), rot=(-1.1, 0, 0))
    mb.write_obj(filepath)

def make_mob_kelinci(filepath):
    mb = ModelBuilder()
    # Body
    mb.add_shape(get_unit_sphere, pos=(0, 0.25, 0), scale=(0.35, 0.35, 0.45))
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 0.5, 0.16), scale=(0.26, 0.26, 0.26))
    # Ears (Left/Right)
    mb.add_shape(get_unit_box, pos=(-0.08, 0.75, 0.12), scale=(0.06, 0.35, 0.1), rot=(-0.2, 0, 0.1))
    mb.add_shape(get_unit_box, pos=(0.08, 0.75, 0.12), scale=(0.06, 0.35, 0.1), rot=(-0.2, 0, -0.1))
    # Legs (FL, FR, BL, BR)
    mb.add_shape(get_unit_cylinder, pos=(-0.1, 0.1, 0.12), scale=(0.06, 0.18, 0.06))
    mb.add_shape(get_unit_cylinder, pos=(0.1, 0.1, 0.12), scale=(0.06, 0.18, 0.06))
    mb.add_shape(get_unit_cylinder, pos=(-0.1, 0.1, -0.12), scale=(0.06, 0.18, 0.06))
    mb.add_shape(get_unit_cylinder, pos=(0.1, 0.1, -0.12), scale=(0.06, 0.18, 0.06))
    # Tail
    mb.add_shape(get_unit_sphere, pos=(0, 0.28, -0.24), scale=(0.09, 0.09, 0.09))
    mb.write_obj(filepath)

def make_mob_ayam(filepath):
    mb = ModelBuilder()
    # Body
    mb.add_shape(get_unit_box, pos=(0, 0.32, 0), scale=(0.32, 0.38, 0.4))
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 0.6, 0.18), scale=(0.2, 0.2, 0.2))
    # Beak
    mb.add_shape(get_unit_cone, pos=(0, 0.58, 0.3), scale=(0.06, 0.12, 0.06), rot=(1.57, 0, 0))
    # Comb
    mb.add_shape(get_unit_box, pos=(0, 0.72, 0.15), scale=(0.03, 0.1, 0.12))
    # Legs (Left/Right)
    mb.add_shape(get_unit_cylinder, pos=(-0.08, 0.1, 0), scale=(0.03, 0.18, 0.03))
    mb.add_shape(get_unit_cylinder, pos=(0.08, 0.1, 0), scale=(0.03, 0.18, 0.03))
    mb.write_obj(filepath)

def make_mob_tikus_gua(filepath):
    mb = ModelBuilder()
    # Body
    mb.add_shape(get_unit_box, pos=(0, 0.15, 0), scale=(0.28, 0.22, 0.42))
    # Head
    mb.add_shape(get_unit_box, pos=(0, 0.28, 0.22), scale=(0.18, 0.18, 0.22))
    # Ears (Left/Right)
    mb.add_shape(get_unit_sphere, pos=(-0.08, 0.36, 0.18), scale=(0.08, 0.08, 0.08))
    mb.add_shape(get_unit_sphere, pos=(0.08, 0.36, 0.18), scale=(0.08, 0.08, 0.08))
    # Legs (FL, FR, BL, BR)
    mb.add_shape(get_unit_cylinder, pos=(-0.1, 0.05, 0.12), scale=(0.05, 0.1, 0.05))
    mb.add_shape(get_unit_cylinder, pos=(0.1, 0.05, 0.12), scale=(0.05, 0.1, 0.05))
    mb.add_shape(get_unit_cylinder, pos=(-0.1, 0.05, -0.12), scale=(0.05, 0.1, 0.05))
    mb.add_shape(get_unit_cylinder, pos=(0.1, 0.05, -0.12), scale=(0.05, 0.1, 0.05))
    # Tail
    mb.add_shape(get_unit_cylinder, pos=(0, 0.15, -0.32), scale=(0.02, 0.3, 0.02), rot=(-1.2, 0, 0))
    mb.write_obj(filepath)

# --- SUPERNATURAL GHOSTS / DEITIES ---

def make_mob_kuntilanak(filepath):
    mb = ModelBuilder()
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 1.75, 0), scale=(0.25, 0.25, 0.25))
    # Hair
    mb.add_shape(get_unit_box, pos=(0, 1.35, -0.12), scale=(0.4, 1.0, 0.15))
    # Torso
    mb.add_shape(get_unit_cylinder, pos=(0, 1.3, 0), scale=(0.22, 0.65, 0.22))
    # Skirt/Dress
    mb.add_shape(get_unit_cone, pos=(0, 0.6, 0), scale=(0.32, 0.85, 0.32))
    # Arms (Left/Right spooky pose)
    mb.add_shape(get_unit_cylinder, pos=(-0.3, 1.35, 0.12), scale=(0.07, 0.55, 0.07), rot=(1.4, 0.2, 0))
    mb.add_shape(get_unit_cylinder, pos=(0.3, 1.35, 0.12), scale=(0.07, 0.55, 0.07), rot=(1.4, -0.2, 0))
    mb.write_obj(filepath)

def make_mob_tuyul(filepath):
    mb = ModelBuilder()
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 0.65, 0), scale=(0.2, 0.2, 0.2))
    # Torso
    mb.add_shape(get_unit_box, pos=(0, 0.42, 0), scale=(0.16, 0.28, 0.16))
    # Legs (Left/Right)
    mb.add_shape(get_unit_cylinder, pos=(-0.06, 0.12, 0), scale=(0.05, 0.22, 0.05))
    mb.add_shape(get_unit_cylinder, pos=(0.06, 0.12, 0), scale=(0.05, 0.22, 0.05))
    # Arms (Left/Right)
    mb.add_shape(get_unit_cylinder, pos=(-0.11, 0.42, 0.06), scale=(0.045, 0.22, 0.045), rot=(1.2, 0.3, 0))
    mb.add_shape(get_unit_cylinder, pos=(0.11, 0.42, 0.06), scale=(0.045, 0.22, 0.045), rot=(1.2, -0.3, 0))
    mb.write_obj(filepath)

def make_mob_wewe(filepath):
    mb = ModelBuilder()
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 1.65, 0), scale=(0.28, 0.28, 0.28))
    # Hair
    mb.add_shape(get_unit_box, pos=(0, 1.35, -0.15), scale=(0.48, 0.75, 0.18))
    # Torso
    mb.add_shape(get_unit_box, pos=(0, 1.2, 0), scale=(0.38, 0.55, 0.28))
    # Saggy Breasts
    mb.add_shape(get_unit_sphere, pos=(-0.11, 1.1, 0.2), scale=(0.16, 0.16, 0.16))
    mb.add_shape(get_unit_sphere, pos=(0.11, 1.1, 0.2), scale=(0.16, 0.16, 0.16))
    # Dress
    mb.add_shape(get_unit_cylinder, pos=(0, 0.55, 0), scale=(0.32, 0.75, 0.32))
    # Arms
    mb.add_shape(get_unit_cylinder, pos=(-0.28, 1.15, 0), scale=(0.09, 0.55, 0.09))
    mb.add_shape(get_unit_cylinder, pos=(0.28, 1.15, 0), scale=(0.09, 0.55, 0.09))
    mb.write_obj(filepath)

def make_mob_banaspati(filepath):
    mb = ModelBuilder()
    # Core Head
    mb.add_shape(get_unit_sphere, pos=(0, 0.75, 0), scale=(0.38, 0.38, 0.38))
    # Flame Orbs (surrounding it)
    mb.add_shape(get_unit_cone, pos=(0.18, 0.95, 0.08), scale=(0.14, 0.38, 0.14), rot=(0.2, 0, 0.3))
    mb.add_shape(get_unit_cone, pos=(-0.18, 0.95, -0.08), scale=(0.14, 0.38, 0.14), rot=(-0.2, 0, -0.3))
    mb.add_shape(get_unit_cone, pos=(0, 1.12, 0), scale=(0.18, 0.45, 0.18), rot=(0, 0, 0))
    mb.add_shape(get_unit_cone, pos=(0.08, 0.85, -0.18), scale=(0.11, 0.32, 0.11), rot=(-0.3, 0, 0.15))
    mb.add_shape(get_unit_cone, pos=(-0.08, 0.85, 0.18), scale=(0.11, 0.32, 0.11), rot=(0.3, 0, -0.15))
    mb.write_obj(filepath)

def make_mob_leak(filepath):
    mb = ModelBuilder()
    # Giant Head
    mb.add_shape(get_unit_sphere, pos=(0, 0.95, 0), scale=(0.48, 0.48, 0.48))
    # Fangs (Left/Right)
    mb.add_shape(get_unit_cone, pos=(-0.16, 0.72, 0.32), scale=(0.08, 0.28, 0.08), rot=(3.14, 0, 0))
    mb.add_shape(get_unit_cone, pos=(0.16, 0.72, 0.32), scale=(0.08, 0.28, 0.08), rot=(3.14, 0, 0))
    # Eyes
    mb.add_shape(get_unit_sphere, pos=(-0.18, 1.1, 0.35), scale=(0.11, 0.11, 0.11))
    mb.add_shape(get_unit_sphere, pos=(0.18, 1.1, 0.35), scale=(0.11, 0.11, 0.11))
    # Tongue
    mb.add_shape(get_unit_box, pos=(0, 0.62, 0.38), scale=(0.14, 0.04, 0.48), rot=(0.4, 0, 0))
    # Hair Tufts (Left/Right/Top)
    mb.add_shape(get_unit_cone, pos=(-0.32, 1.1, 0), scale=(0.14, 0.38, 0.14), rot=(0, 0, 1.2))
    mb.add_shape(get_unit_cone, pos=(0.32, 1.1, 0), scale=(0.14, 0.38, 0.14), rot=(0, 0, -1.2))
    mb.add_shape(get_unit_cone, pos=(0, 1.32, -0.1), scale=(0.14, 0.38, 0.14), rot=(-0.4, 0, 0))
    mb.write_obj(filepath)

def make_mob_jin(filepath):
    mb = ModelBuilder()
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 1.45, 0), scale=(0.26, 0.26, 0.26))
    # Torso
    mb.add_shape(get_unit_cylinder, pos=(0, 0.95, 0), scale=(0.28, 0.55, 0.28))
    # Smoke Base (floating)
    mb.add_shape(get_unit_cone, pos=(0, 0.32, 0), scale=(0.32, 0.65, 0.32), rot=(3.14, 0, 0))
    # Arms
    mb.add_shape(get_unit_cylinder, pos=(-0.26, 1.05, 0), scale=(0.08, 0.45, 0.08))
    mb.add_shape(get_unit_cylinder, pos=(0.26, 1.05, 0), scale=(0.08, 0.45, 0.08))
    mb.write_obj(filepath)

def make_mob_demit(filepath):
    mb = ModelBuilder()
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 1.35, 0), scale=(0.24, 0.24, 0.24))
    # Horns
    mb.add_shape(get_unit_cone, pos=(-0.12, 1.52, 0.08), scale=(0.05, 0.26, 0.05), rot=(0.2, 0, 0.25))
    mb.add_shape(get_unit_cone, pos=(0.12, 1.52, 0.08), scale=(0.05, 0.26, 0.05), rot=(0.2, 0, -0.25))
    # Torso
    mb.add_shape(get_unit_box, pos=(0, 0.92, 0), scale=(0.32, 0.45, 0.28))
    # Robe/Cloak
    mb.add_shape(get_unit_cone, pos=(0, 0.38, 0), scale=(0.42, 0.75, 0.42))
    # Arms
    mb.add_shape(get_unit_cylinder, pos=(-0.24, 0.85, 0), scale=(0.07, 0.45, 0.07))
    mb.add_shape(get_unit_cylinder, pos=(0.24, 0.85, 0), scale=(0.07, 0.45, 0.07))
    mb.write_obj(filepath)

def make_mob_bidadari(filepath):
    mb = ModelBuilder()
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 1.65, 0), scale=(0.22, 0.22, 0.22))
    # Halo Ring
    mb.add_shape(get_unit_cylinder, pos=(0, 1.88, 0), scale=(0.24, 0.03, 0.24))
    # Torso
    mb.add_shape(get_unit_cylinder, pos=(0, 1.2, 0), scale=(0.2, 0.48, 0.2))
    # Dress
    mb.add_shape(get_unit_cone, pos=(0, 0.52, 0), scale=(0.3, 0.85, 0.3))
    # Wings (Left/Right)
    mb.add_shape(get_unit_box, pos=(-0.32, 1.2, -0.12), scale=(0.04, 0.38, 0.75), rot=(0.1, 0.2, 0.1))
    mb.add_shape(get_unit_box, pos=(0.32, 1.2, -0.12), scale=(0.04, 0.38, 0.75), rot=(0.1, -0.2, -0.1))
    mb.write_obj(filepath)

def make_mob_dewa(filepath):
    mb = ModelBuilder()
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 1.65, 0), scale=(0.24, 0.24, 0.24))
    # Halo Ring
    mb.add_shape(get_unit_cylinder, pos=(0, 1.9, 0), scale=(0.26, 0.03, 0.26))
    # Torso
    mb.add_shape(get_unit_cylinder, pos=(0, 1.15, 0), scale=(0.26, 0.52, 0.26))
    # Bottom Cloud
    mb.add_shape(get_unit_sphere, pos=(0, 0.55, 0), scale=(0.38, 0.38, 0.38))
    mb.add_shape(get_unit_sphere, pos=(0.18, 0.48, 0), scale=(0.28, 0.28, 0.28))
    mb.add_shape(get_unit_sphere, pos=(-0.18, 0.48, 0), scale=(0.28, 0.28, 0.28))
    # Arms
    mb.add_shape(get_unit_cylinder, pos=(-0.26, 1.1, 0), scale=(0.08, 0.48, 0.08))
    mb.add_shape(get_unit_cylinder, pos=(0.26, 1.1, 0), scale=(0.08, 0.48, 0.08))
    mb.write_obj(filepath)

def make_mob_petapa(filepath):
    mb = ModelBuilder()
    # Head
    mb.add_shape(get_unit_sphere, pos=(0, 1.45, 0), scale=(0.24, 0.24, 0.24))
    # Caping Hat
    mb.add_shape(get_unit_cone, pos=(0, 1.56, 0), scale=(0.42, 0.12, 0.42))
    # Torso
    mb.add_shape(get_unit_box, pos=(0, 1.0, 0), scale=(0.28, 0.48, 0.22))
    # Robe/Skirt
    mb.add_shape(get_unit_cylinder, pos=(0, 0.42, 0), scale=(0.3, 0.65, 0.3))
    # Staff (Tongkat)
    mb.add_shape(get_unit_cylinder, pos=(0.32, 0.75, 0.18), scale=(0.035, 1.3, 0.035), rot=(0.1, 0, 0))
    mb.write_obj(filepath)


# --- MAIN GENERATOR FUNCTION ---

def main():
    dest_dir = Path(__file__).resolve().parent / 'assets' / 'models'
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    generators = {
        'mob_kucing': make_mob_kucing,
        'mob_sapi': make_mob_sapi,
        'mob_kambing': make_mob_kambing,
        'mob_bebek': make_mob_bebek,
        'mob_domba': make_mob_domba,
        'mob_kuda': make_mob_kuda,
        'mob_rubah': make_mob_rubah,
        'mob_kelinci': make_mob_kelinci,
        'mob_ayam': make_mob_ayam,
        'mob_tikus_gua': make_mob_tikus_gua,
        'mob_kuntilanak': make_mob_kuntilanak,
        'mob_tuyul': make_mob_tuyul,
        'mob_wewe': make_mob_wewe,
        'mob_banaspati': make_mob_banaspati,
        'mob_leak': make_mob_leak,
        'mob_jin': make_mob_jin,
        'mob_demit': make_mob_demit,
        'mob_bidadari': make_mob_bidadari,
        'mob_dewa': make_mob_dewa,
        'mob_petapa': make_mob_petapa,
    }
    
    print(f"Generating {len(generators)} low-poly models in {dest_dir}...")
    for name, gen_func in generators.items():
        out_path = dest_dir / f"{name}.obj"
        gen_func(out_path)
    print("All models successfully generated!")

if __name__ == '__main__':
    main()
