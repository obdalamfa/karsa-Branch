# TAHAPAN — dari tambal-menambal ke penyempurnaan

Urutannya bukan selera. Tiap tahap membuka tahap berikutnya, dan tahap yang
dilompati akan menagih ongkosnya belakangan.

---

## Tahap 0 — Amankan kerja ✅ SELESAI

Commit `09ef02f`, 96 file, 12.296 baris. Sebelum ini seluruh sesi ada di
working tree tanpa jaring apa pun, dan satu agen sudah pernah menjalankan
`git stash` di tengah kerja agen lain.

---

## Tahap 1 — Jaring pengaman 🔨 SEDANG DIKERJAKAN

**`tools/regress.py`** — boot tiap scene, buktikan ia dirender, dan periksa
hal-hal yang memang PERNAH rusak di proyek ini.

Kenapa ini duluan, bukan fitur: verifikasi manual sudah gagal **dua kali**
sesi ini. WASD dinyatakan beres padahal belum, dan dua kali sebuah metode
disisipkan di tengah fungsi sehingga fungsi induknya mati total. Keduanya
ketahuan karena kebetulan diuji ulang. Yang ketiga tidak akan ketahuan.

Yang diperiksa, tiap satu terikat kegagalan nyata:

| Cek | Kegagalan nyata yang melatarinya |
|---|---|
| entity bergeometri nol | bug NodePath-bersama, terjadi **dua kali** |
| frame kosong / hampir semua langit | "rumah ga muncul" |
| pemain di tile bisa-jalan | terjepit permanen |
| motif dalam rentang, mood terhingga | mesin motif baru |
| save bolak-balik utuh | format save berubah, save lama tidak boleh rusak |
| ms per frame | 4–29 FPS, belum pernah diprofil |

**Selesai kalau:** perintahnya jalan, mengeluarkan tabel LULUS/GAGAL, dan
melaporkan kondisi SEKARANG apa adanya — termasuk yang gagal.

---

## Tahap 2 — Verifikasi yang sudah terlanjur ada

`economy.py`, `husbandry.py`, `crops.py`, `tool_models.py` mendarat di disk
saat agennya mati. **Belum ada yang membuktikan isinya berfungsi.** Sekarang
ada belasan sistem berstatus tidak jelas.

Aturannya: tidak ada fitur baru sampai yang ada terbukti jalan atau ditandai
rusak dengan jujur. Sistem setengah jadi yang diklaim selesai lebih berbahaya
daripada sistem yang belum dibuat.

---

## Tahap 3 — Performa

4–29 FPS, belum pernah diprofil, jumlah entity terus naik (1126 di kandang).
Setiap perbaikan visual dinikmati lewat slideshow.

Dua jalan: optimasi bertahap (batching, culling, kurangi entity) yang aman,
atau perombakan renderer yang berisiko. Mulai dari yang pertama **sambil
mengukur**. Kalau mentok di bawah 30 FPS, itu keputusan besar tentang seberapa
jauh Ursina sanggup dibawa — dan itu keputusan pemilik, bukan keputusanku.

---

## Tahap 4 — Wishes

**Ini yang membuat game punya alasan untuk dipedulikan.** Sekarang sudah ada
kebutuhan, objek, aksi, antrian — tapi pemain bisa main lima menit lalu
bertanya "terus?".

Jawaban The Sims 3 adalah Wishes: sim memunculkan keinginan kontekstual,
pemain menjanjikan beberapa, memenuhinya membayar Lifetime Happiness. Itu
memberi arah **tanpa** mencabut kebebasan — dan "kebebasannya seru" adalah
kata-kata pemilik sendiri.

Prioritas tertinggi setelah fondasi bersih. Di atas seni apa pun.

---

## Tahap 5 — Autonomi

Termurah, dampak paling besar. `choose_action()` dan `autonomy_candidates()`
**sudah dibangun dan teruji**; belum ada yang memanggilnya. Begitu tersambung
ke NPC, desa mulai hidup sendiri.

---

## Tahap 6 — Traits dan moodlets

Lima sifat per sim yang benar-benar mengubah perilaku dan wish yang muncul.
Mood jadi jumlah moodlet bernama dengan ikon dan timer, bukan rata-rata —
moodlet menjelaskan dengan kata-kata kenapa sim merasa begitu. Sekalian
delapan motif dipangkas jadi enam (Sims 3): Nyaman dan Ruangan jadi moodlet.

---

## Tahap 7 — Misteri dan entitas

Mesin tahapan ala StrangerVille, ekonomi petunjuk, dan mob yang benar-benar
memanipulasi cerita. Bahasa rupa dari logo: halo gerigi, mata dalam daun,
sulur, dan **akar yang berupa jalur sirkuit siku-siku**.

Sengaja di sini, bukan karena tidak penting, tapi karena StrangerVille bekerja
justru karena kehidupan biasa terus berjalan normal di sekelilingnya. Kalau
kehidupan biasanya belum ada, horornya tidak punya latar untuk mengganggu.

---

## Tahap 8 — Audio

Musik masih terasa seram; agennya gagal empat kali kena limit sesi. Materi
seramnya tidak dibuang — dipindah ke kuburan, gua, dan dungeon. Kontras itu
justru yang membuat lapisan horor bekerja.

---

## Yang TIDAK akan dikejar

**Open world Sims 3.** Lima belas scene terpisah dengan frame rate segini
membuat itu lubang tanpa dasar. Yang dikejar cukup menghilangkan *rasa*
loading: transisi instan, kamera mempertahankan sudut, mendarat di tempat
yang masuk akal. Ini penyimpangan yang disengaja, bukan kesetaraan dengan TS3,
dan tidak akan diakui sebagai kesetaraan.
