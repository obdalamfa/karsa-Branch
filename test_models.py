import os
import sys
from pathlib import Path
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Filename

def test_all_models():
    print("Initializing headless ShowBase for model validation...")
    base = ShowBase(windowType='none')
    
    models_dir = Path(__file__).resolve().parent / 'assets' / 'models'
    
    models_to_test = [
        'mob_kucing',
        'mob_sapi',
        'mob_kambing',
        'mob_bebek',
        'mob_domba',
        'mob_kuda',
        'mob_rubah',
        'mob_kelinci',
        'mob_ayam',
        'mob_tikus_gua',
        'mob_kuntilanak',
        'mob_tuyul',
        'mob_wewe',
        'mob_banaspati',
        'mob_leak',
        'mob_jin',
        'mob_demit',
        'mob_bidadari',
        'mob_dewa',
        'mob_petapa',
    ]
    
    success_count = 0
    failure_count = 0
    
    for name in models_to_test:
        path = models_dir / f"{name}.obj"
        if not path.exists():
            print(f"[-] ERROR: File not found: {path}")
            failure_count += 1
            continue
            
        try:
            fn = Filename.fromOsSpecific(str(path))
            m = base.loader.loadModel(fn)
            if m:
                print(f"[+] SUCCESS: Loaded {name}.obj")
                success_count += 1
            else:
                print(f"[-] FAILURE: Loader returned None for {name}.obj")
                failure_count += 1
        except Exception as e:
            print(f"[-] CRASH: Failed to load {name}.obj - {e}")
            failure_count += 1
            
    print(f"\nValidation Summary: {success_count}/{len(models_to_test)} models loaded successfully.")
    if failure_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    test_all_models()
