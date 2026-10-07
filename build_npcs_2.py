exec(open(r"E:/Game Research/Lembah Karsa 3D/npc_common.py").read())

# Batch 2 — anak-anak, tetua, ronda, kru kapal
SPECS = [
    dict(id='cici', H=1.12, skin=SKIN_L, shirt=P_PNK, pants=(0.45,0.40,0.36),
         bottom='skirt', hair='buns', slouch=0.0),
    dict(id='bowo', H=1.15, skin=SKIN, shirt=TEAL, pants=(0.30,0.30,0.28),
         sleeve='short', hair='short', slouch=0.0),
    dict(id='pak_guru', H=1.72, skin=SKIN, shirt=(0.60,0.58,0.52), pants=HITAM,
         hat='peci', hat_col=HITAM, hair='short', slouch=0.3),
    dict(id='mbok_jum', H=1.52, skin=SKIN_D, shirt=COKLAT, pants=(0.30,0.22,0.14),
         bottom='skirt', hair='sanggul', hair_col=UBAN, slouch=0.85),
    dict(id='jaka_ronda', H=1.76, skin=SKIN, shirt=(0.22,0.22,0.22), pants=NAVY,
         sleeve='short', hair='short', sash=RUST, stick='kentongan', slouch=0.35),
    dict(id='kapten_kuro', H=1.77, skin=SKIN_D, shirt=NAVY, pants=HITAM,
         hat='captain', hat_col=NAVY, beard=(0.25,0.22,0.18), slouch=0.3),
    dict(id='kru_kuro', H=1.73, skin=SKIN, shirt=(0.50,0.48,0.42), pants=NAVY,
         sleeve='short', hair='bandana', hat_col=RUST, slouch=0.4),
]
for s in SPECS:
    try:
        make_npc(s)
    except Exception as e:
        print("FAIL", s['id'], ":", e)
print("BATCH2 NPC DONE")
