# Lembah Karsa 3D — Rencana Desain (Indie Game Designer)

## Visi
Game RPG-pertanian Indonesia bergaya **pixel-art 3D** (ala Shaman Quest): dunia
folklore Jawa yang lembap & atmosferik, dapat dimainkan dengan jelas. Bertani →
jelajah → lawan makhluk halus relik → bangun hubungan dengan warga.

## Pilar Desain
1. **Jelas & bisa dimainkan** — pemain selalu paham apa yang dilihat & dilakukan.
2. **Identitas visual konsisten** — pixel-art 3D + grain halus, palet earthy.
3. **Karakter bermakna** — tiap NPC/mob terbaca perannya dari penampilan.
4. **UI fungsional** — inventory Harvest Moon, HUD ringkas ala Doom.

---

## WORKSTREAM 1 — Visual Pass (pixel-art 3D)
- [x] Pixelation halus 960×540 + grain "pasir"
- [ ] Audit screenshot tiap scene → catat yang aneh/tak muncul
- [ ] Hapus sisa grid magenta (sumber: cek tile path/road & z-fighting)
- [ ] Palet earthy lembap (hijau lumut, coklat) — konsisten
- [ ] Kabut tanah tipis (atmosfer rimba) — opsional

## WORKSTREAM 2 — Karakter (NPC manusia & mob humanlike)
**Pakai Vitaboy + atribut sesuai peran.**
- [ ] Audit `vitaboy_npc.py` / `vitaboy_baked.py` — apa yang bisa ditambah
- [ ] Atribut per-peran (aksesori prosedural di atas avatar):
  - Bu Sari (warung) → celemek + penutup kepala
  - Pak Budi (pandai besi) → apron kulit + palu
  - Pak Raka (klinik/dokter) → jas + tas
  - Maya (studio) → selempang buku
  - Petapa → sudah jadi dewa arca emas (selesai)
- [ ] Mob humanlike (genderuwo, pocong) → tetap relik artefak (selesai)

## WORKSTREAM 3 — Mob non-manusia (referensi internet)
- [ ] Cari referensi visual: kucing kampung, kambing/ayam, naga Jawa,
      kelelawar, jamur berjalan
- [ ] Terjemahkan ke bentuk yang terbaca (mesh/material relik atau sprite)
- [ ] Pastikan skala & posisi benar (sudah ada _MODEL_TRANSFORM)

## WORKSTREAM 4 — Inventory ala Harvest Moon
- [ ] Ganti panel teks → **grid slot bergambar** (ikon item + jumlah)
- [ ] Kategori: alat / benih / hasil panen / bahan / item khusus
- [ ] Navigasi kursor (arrow/WASD) + highlight slot terpilih
- [ ] Ikon: pakai tekstur item yang ada / generate ikon sederhana

## WORKSTREAM 5 — GUI ringkas ala Doom
- [ ] HUD bar bawah yang rapi: HP / Energi / Emas / alat aktif / jam
- [ ] Hilangkan teks bertumpuk di pojok → panel terstruktur
- [ ] Font & spacing konsisten, ikon bukan teks panjang
- [ ] Indikator status (lapar/sosial/senang) jadi ikon kecil

---

## Urutan Eksekusi yang Disarankan (langkah kecil + verifikasi screenshot)
1. **Pixelation halus** (selesai) → screenshot konfirmasi ukuran piksel
2. **Audit visual** semua screenshot → daftar bug nyata
3. **HUD Doom** (cepat, dampak besar pada "kejelasan")
4. **Inventory Harvest Moon** (grid slot)
5. **Atribut Vitaboy per-peran** (NPC terbaca)
6. **Mob non-manusia** (referensi + terapkan)
7. **Polish palet/kabut** (atmosfer akhir)

> Prinsip: SATU workstream → eksekusi → screenshot → verifikasi → lanjut.
> Tidak menumpuk perubahan tanpa melihat hasil.
