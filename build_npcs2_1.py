exec(open(r"E:/Game Research/Lembah Karsa 3D/npc_common2.py").read())

SPECS = [
    dict(id='arya', H=1.78, skin=SKIN, shirt=RUST, pants=(0.32,0.33,0.22),
         collar_col=KREM, hair='short', eye_col=(0.22,0.15,0.10)),
    dict(id='sari', H=1.66, skin=SKIN_L, shirt=KREM, pants=COKLAT, bottom='long_skirt',
         hat='kerudung', hat_col=TEAL, apron=ABU, blush=True),
    dict(id='raka', H=1.75, skin=SKIN, shirt=TEAL, pants=NAVY, sleeve='short',
         hair='spiky', shoe_col=(0.30,0.28,0.25)),
    dict(id='maya', H=1.64, skin=SKIN_L, shirt=OLIVE, pants=(0.48,0.27,0.18),
         bottom='skirt', hair='ponytail', blush=True, eye_col=(0.18,0.24,0.14)),
    dict(id='budi', H=1.70, skin=SKIN_D, shirt=ABU, pants=COKLAT,
         hair='bald', beard=UBAN, buttons=True),
    dict(id='joko', H=1.74, skin=SKIN_D, shirt=OLIVE, pants=COKLAT, sleeve='short',
         hat='caping', hat_col=TAN, hair='short', mustache=RAMBUT),
    dict(id='ningsih', H=1.63, skin=SKIN, shirt=KREM, pants=BATIK,
         bottom='long_skirt', hair='sanggul', blush=True),
]
for s in SPECS:
    try:
        make_npc(s)
    except Exception as e:
        print("FAIL", s['id'], ":", e)
print("BATCH1 v2 DONE")
