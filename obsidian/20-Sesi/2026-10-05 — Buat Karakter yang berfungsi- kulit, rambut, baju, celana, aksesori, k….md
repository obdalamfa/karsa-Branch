---
judul: "Buat Karakter yang berfungsi: kulit, rambut, baju, celana, aksesori, keahlian"
tipe: sesi
tanggal: 2026-10-05
commit: 0943a09
skala: 8 file sumber, +524 / −194 baris
tags: [sesi]
---

# 2026-10-05 — Buat Karakter yang berfungsi: kulit, rambut, baju, celana, aksesori, keahlian

## Pesan commit

Sebelumnya pilihan chargen tidak berpengaruh apa pun: penerapnya ditulis
untuk model voxel/Vitaboy lama, sedangkan pemain memakai rig GLB.

- game/rupa_pemain.py: pewarnaan ulang tekstur GLB saat runtime. Baju vs
  celana dari topeng UV (segitiga digolongkan dari tinggi verteks), kulit
  dan rambut dari uji piksel. Tekstur dipasang di TextureStage asli (UV
  glTF di 'texcoord.0'; stage bawaan mencuplik satu piksel pojok).
  Aksesori kepala dibangun saat runtime dan diposisikan dari kotak batas
  kepala sebenarnya -- duduk menutup ubun-ubun, tidak melayang.
- game/keahlian.py: enam keahlian dengan kait nyata (_spend_energy,
  sell_price, give_gift, lempar kail, speed, maks energi/HP), idempoten
  lewat state.keahlian_terpasang.
- game/chargen.py: panel krem berbingkai kayu (bahasa yang sama dengan
  kotak dialog), pratinjau = pemain sungguhan, HUD disembunyikan.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/app.py` | +5 | −0 |
| `game/chargen.py` | +174 | −191 |
| `game/controllers/interaction_controller.py` | +6 | −2 |
| `game/economy.py` | +8 | −0 |
| `game/keahlian.py` | +46 | −0 |
| `game/player.py` | +14 | −1 |
| `game/rupa_pemain.py` | +269 | −0 |
| `game/state.py` | +2 | −0 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Bukti spesifik untuk commit ini **tidak tercatat** saat dikerjakan (sesi panjang, catatan ditulis belakangan). Diperiksa visual lewat tangkapan layar; regresi penuh pertama sesudahnya ada di 17d570b.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Swarga gagal `cahaya_global` di regresi (juga di 17d570b dan HEAD sebelumnya) — belum diselidiki.
- `hud_terbaca` gagal acak tergantung urutan scene pada larian penuh; lulus kalau scene diuji sendiri.
- Bug pemilik yang masih antri: suasana semua scene disamakan dengan farm (#2/#9), animasi pakai alat (#11), kedip farm (#3) belum dikonfirmasi pemilik, pohon/kelapa dan interior gua via Blender.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
