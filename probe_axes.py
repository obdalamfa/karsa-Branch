import sys, os
from panda3d.core import loadPrcFileData, Filename
loadPrcFileData('', 'window-type none')
if '--nocache' in sys.argv:
    loadPrcFileData('', 'model-cache-dir')
from direct.showbase.ShowBase import ShowBase
base = ShowBase()
MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'models')
for name in ['prop_mercusuar_rusak', 'npc_arya', 'humanoid', 'prop_kurofune', 'pohon_tropis']:
    p = os.path.join(MODELS, name + '.obj')
    m = base.loader.loadModel(Filename.fromOsSpecific(p))
    lo, hi = m.getTightBounds(); d = hi - lo
    print('%-24s X=%.2f Y=%.2f Z=%.2f' % (name, d.x, d.y, d.z))
print('PROBE DONE')
