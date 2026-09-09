"""Konversi OBJ buatan sesi ini dari Z-up -> Y-up (konvensi OBJ standar
yang dipakai loader Panda3D game). Rotasi -90 deg sumbu X: (x,y,z)->(x,z,-y).
Berlaku untuk baris 'v ' dan 'vn ' saja; UV/face tidak berubah. Idempoten
TIDAK — jangan jalankan dua kali (pakai marker komentar)."""
import os

DIRS = [
    r"E:/Game Research/Lembah Karsa 3D/assets/models",
    r"E:/Game Research/Lembah Karsa 3D/game/assets/models",
    r"E:/Game Research/Lembah Karsa 3D/.claude/worktrees/charming-lehmann-1b13fd/assets/models",
]

ANIMALS = ['ayam','bebek','kucing','kambing','sapi','kelinci','domba','kuda','rubah','jago']
FOLKLORE = ['genderuwo','pocong','kelelawar','kuntilanak','tuyul','wewe','banaspati',
            'leak','jin','demit','bidadari','tikus_gua','dewa']
NPCS = ['arya','sari','raka','maya','budi','joko','ningsih','cici','bowo',
        'pak_guru','mbok_jum','jaka_ronda','kapten_kuro','kru_kuro']
PROPS = ['scarecrow','kandang_ayam','gerobak','cangkul','ember','jerami',
         'peti_sayur','karung','pagar_kayu','mercusuar_rusak','mercusuar','kurofune']
TREES = ['pohon_tropis','pohon_kelapa','pohon_mati']

NAMES = []
for a in ANIMALS:
    NAMES += [f'mob_{a}', f'mob_{a}_idle', f'mob_{a}_walk1', f'mob_{a}_walk2']
for f in FOLKLORE:
    NAMES.append(f'mob_{f}')
for n in NPCS:
    NAMES += [f'npc_{n}', f'npc_{n}_idle', f'npc_{n}_walk1', f'npc_{n}_walk2']
for p in PROPS:
    NAMES.append(f'prop_{p}')
NAMES += TREES
NAMES += ['naga', 'petapa_srimana', 'petapa_srimana_galak']

MARKER = "# axis-converted-to-Y-up\n"

def convert(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    if lines and lines[0] == MARKER:
        return 'skip (sudah)'
    out = [MARKER]
    for ln in lines:
        if ln.startswith('v ') or ln.startswith('vn '):
            parts = ln.split()
            tag = parts[0]
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            # rotasi -90 sumbu X: ketinggian Z lama -> Y baru
            out.append(f"{tag} {x:.6f} {z:.6f} {-y:.6f}\n")
        else:
            out.append(ln)
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(out)
    return 'OK'

total_ok = 0; total_skip = 0; missing = 0
for d in DIRS:
    for n in NAMES:
        p = os.path.join(d, n + '.obj')
        if not os.path.exists(p):
            missing += 1; continue
        r = convert(p)
        if r == 'OK': total_ok += 1
        else: total_skip += 1
print(f"converted={total_ok}  skipped={total_skip}  missing={missing}")
