import bpy, os, glob

# Audit dimensi semua model di MAIN repo assets/models (sumber game berjalan)
SRC = "E:/Game Research/Lembah Karsa 3D/assets/models"

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()

names = []
for p in sorted(glob.glob(SRC + "/*.obj")):
    base = os.path.basename(p)[:-4]
    if any(base.endswith(sfx) for sfx in ('_idle', '_walk1', '_walk2')):
        continue
    names.append(base)

print("== AUDIT DIMENSI (X lebar, Y depth, Z tinggi) ==")
for n in names:
    try:
        bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
        bpy.ops.wm.obj_import(filepath=SRC + "/" + n + ".obj",
                              forward_axis='NEGATIVE_Y', up_axis='Z')
        ms = [o for o in bpy.context.selected_objects if o.type == 'MESH']
        if not ms:
            print(f"{n}: NO MESH"); continue
        o = ms[0]
        d = o.dimensions
        nmat = len(o.data.materials)
        print(f"{n}: {d.x:.2f} x {d.y:.2f} x {d.z:.2f}  ({len(o.data.vertices)}v, {nmat} mats)")
    except Exception as e:
        print(f"{n}: ERROR {e}")

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
print("AUDIT DONE")
