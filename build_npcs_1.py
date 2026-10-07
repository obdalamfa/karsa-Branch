exec(open(r"E:/Game Research/Lembah Karsa 3D/npc_common.py").read())

# Batch 1 — warga inti
SPECS = [
    dict(id='arya', H=1.78, skin=SKIN, shirt=RUST, pants=(0.28,0.29,0.20),
         sleeve='short', hair='short', slouch=0.3),
    dict(id='sari', H=1.66, skin=SKIN_L, shirt=KREM, pants=COKLAT,
         bottom='skirt', hat='kerudung', hat_col=TEAL, apron=ABU, slouch=0.2),
    dict(id='raka', H=1.75, skin=SKIN, shirt=TEAL, pants=NAVY,
         sleeve='short', hair='short', hair_col=(0.18,0.14,0.10), slouch=0.4),
    dict(id='maya', H=1.64, skin=SKIN_L, shirt=OLIVE, pants=(0.40,0.24,0.16),
         bottom='skirt', hair='ponytail', slouch=0.15),
    dict(id='budi', H=1.70, skin=SKIN_D, shirt=ABU, pants=COKLAT,
         hair='bald', beard=UBAN, slouch=0.5),
    dict(id='joko', H=1.74, skin=SKIN_D, shirt=OLIVE, pants=COKLAT,
         sleeve='short', hat='caping', hat_col=TAN, hair='short', slouch=0.45),
    dict(id='ningsih', H=1.63, skin=SKIN, shirt=KREM, pants=(0.33,0.25,0.16),
         bottom='skirt', hair='sanggul', slouch=0.25),
]
for s in SPECS:
    try:
        make_npc(s)
    except Exception as e:
        print("FAIL", s['id'], ":", e)
print("BATCH1 NPC DONE")
