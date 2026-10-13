---
judul: Gauntlet Oktober 2026 — 10 Milestone
tipe: tahapan
dibuat: 2026-10-13
jadwal: Selasa 13 – Jumat 16 Okt 2026, tiap 07.00 & 15.00 WIB
bar: A Short Hike (screenshot/footage rilis), plus regresi 14/14
tags: [tahapan, gauntlet]
---

# Gauntlet Oktober 2026 — 10 Milestone

**Bar:** *A Short Hike* (adamgryu, 2019). Dibandingkan langsung dari
screenshot/footage rilis, bukan dari deskripsi. Syarat terukurnya:
`python tools/regress.py` 14/14 lulus.

**Cara kerja per milestone:** builder dan kritikus dijalankan sebagai subagen
terpisah dengan konteks segar. Kritikus menaruh capture kita di samping bar
secara buta (label dibuang), memilih mana yang lebih baik, lalu menyebut satu
celah terbesar. Ulangi sampai kita menang. Milestone non-visual tidak diadu
lewat gambar; kritikusnya memvonis dari bukti uji.

**Aturan CLAUDE.md tetap berlaku:** milestone tanpa bukti (larian regresi,
probe `_bench/`, atau angka) tidak dicentang.

| # | Milestone | Definition of done (harus ada bukti) | Status |
|---|---|---|---|
| M1 | Regresi hijau lagi | swarga `cahaya_global` lulus; `hud_terbaca` lulus 3 larian penuh berturut-turut | ⬜ |
| M2 | Penjaga arah WASD memvonis | cek `arah_maju` jadi pemeriksaan gagal/lulus tanpa menuduh scene sehat; terbukti gagal bila bug dipasang kembali | ⬜ |
| M3 | Alat capture gauntlet | skrip mengambil capture tiap scene dari jalur asli `app.py` (aturan #2) ke `_bench/gauntlet/`; galeri bar *A Short Hike* tersimpan | ⬜ |
| M4 | Farm mengalahkan bar | kritikus buta memilih capture farm kita atas *A Short Hike* | ⬜ |
| M5 | Suasana batch 1 setara farm | town, beach, house dan studio menang blind | ⬜ |
| M6 | Suasana batch 2 setara farm | mountain, lake, cemetery dan swarga menang blind; sisa scene dicatat | ⬜ |
| M7 | Tahap 4 Wishes — mesin | wish lahir dari motif/hubungan, terpenuhi, dan berakibat; probe menempuh jalur asli | ⬜ |
| M8 | Wishes terlihat pemain | wish muncul di dialog berpotret/HUD dan lulus cek `hud_terbaca` | ⬜ |
| M9 | Animasi memakai alat | cangkul, siram dan kapak punya pose yang bisa dibedakan di capture; menang blind atas klip *A Short Hike* | ⬜ |
| M10 | Pohon & gua Blender + 5 menit pertama | aset pohon/gua terpasang dan punya pemanggil (aturan #4); probe main 5 menit dari layar judul sampai panen pertama | ⬜ |

## Jadwal

Satu slot = satu milestone. Delapan slot untuk sepuluh milestone, jadi slot
yang selesai lebih awal langsung lanjut ke milestone berikutnya.

| Slot | Target |
|---|---|
| Sel 07.00 | M1 |
| Sel 15.00 | M2 |
| Rab 07.00 | M3 |
| Rab 15.00 | M4 |
| Kam 07.00 | M5 |
| Kam 15.00 | M6 + M7 |
| Jum 07.00 | M8 + M9 |
| Jum 15.00 | M10 + penutupan |
