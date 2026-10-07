exec(open(r"E:/Game Research/Lembah Karsa 3D/npc_common2.py").read())

SPECS = [
    dict(id='cici', H=1.12, kid=True, skin=SKIN_L, shirt=PINK, pants=PINK,
         bottom='skirt', hair='buns', blush=True, eye_col=(0.20,0.14,0.10)),
    dict(id='bowo', H=1.15, kid=True, skin=SKIN, shirt=TEAL, pants=(0.36,0.36,0.33),
         bottom='shorts', sleeve='short', hair='short', shoe_col=(0.45,0.30,0.18)),
    dict(id='pak_guru', H=1.72, skin=SKIN, shirt=PUTIH, pants=HITAM,
         hat='peci', hat_col=HITAM, hair='short', glasses=True, buttons=True),
    dict(id='mbok_jum', H=1.52, skin=SKIN_D, shirt=COKLAT, pants=(0.33,0.24,0.15),
         bottom='long_skirt', hair='sanggul', hair_col=UBAN, stick='tongkat'),
    dict(id='jaka_ronda', H=1.76, skin=SKIN, shirt=(0.25,0.25,0.26), pants=NAVY,
         sleeve='short', hair='short', sash=RUST, stick='kentongan'),
    dict(id='kapten_kuro', H=1.77, skin=SKIN_D, shirt=NAVY, pants=HITAM,
         hat='captain', hat_col=NAVY, beard=(0.28,0.24,0.20), buttons=True,
         collar_col=KREM),
    dict(id='kru_kuro', H=1.73, skin=SKIN, shirt=PUTIH, pants=NAVY, sleeve='short',
         hair='bandana', hat_col=RUST, stripes=NAVY),
]
for s in SPECS:
    try:
        make_npc(s)
    except Exception as e:
        print("FAIL", s['id'], ":", e)
print("BATCH2 v2 DONE")
