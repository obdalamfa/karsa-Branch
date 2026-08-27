# TAHAPAN — dari tambal-menambal ke penyempurnaan

Urutannya bukan selera. Tiap tahap membuka tahap berikutnya, dan tahap yang
dilompati akan menagih ongkosnya belakangan.

---

## Tahap 0 — Amankan kerja ✅ SELESAI

Commit `09ef02f`, 96 file, 12.296 baris. Sebelum ini seluruh sesi ada di
working tree tanpa jaring apa pun, dan satu agen sudah pernah menjalankan
`git stash` di tengah kerja agen lain.

---

## Tahap 1 — Jaring pengaman ✅ SELESAI (dan terus bertambah)

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

Empat pemeriksaan ditambahkan setelah cacat-cacat yang hanya bisa DILIHAT
ternyata bertahan berbulan-bulan justru karena hanya bisa dilihat: tiap
screenshot dinilai dengan mata, dan mata memaafkan.

| Cek | Kegagalan nyata yang melatarinya |
|---|---|
| `hud_muat` | jam, tanggal, nama scene, dan ekor baris kontrol tumbuh lewat tepi layar |
| `hud_terbaca` | bar motif tertimbun latar panelnya sendiri — warnanya benar, yang sampai ke mata tidak |
| `rumput_catur` | tint ubin terkunci ke paritas `(tx+ty) % 2`, jadi ladang terbaca sebagai papan catur |
| `avatar_warna` | warga desa jadi gumpalan putih di mesin tanpa instalasi TSO |

Aturannya: **tiap pemeriksaan diuji GAGAL dulu pada kode lama sebelum
dipercaya.** Dua di antaranya lulus pada uji negatifnya sendiri di percobaan
pertama dan harus diperketat — `avatar_warna` bahkan dua kali. Cek yang tidak
pernah bisa gagal tidak membuktikan apa pun, dan lebih berbahaya daripada
tidak ada cek, karena ia memberi rasa aman.

---

## Tahap 2 — Verifikasi yang sudah terlanjur ada

`economy.py`, `husbandry.py`, `crops.py`, `tool_models.py` mendarat di disk
saat agennya mati. **Belum ada yang membuktikan isinya berfungsi.** Sekarang
ada belasan sistem berstatus tidak jelas.

Aturannya: tidak ada fitur baru sampai yang ada terbukti jalan atau ditandai
rusak dengan jujur. Sistem setengah jadi yang diklaim selesai lebih berbahaya
daripada sistem yang belum dibuat.

---

## Tahap 3 — Performa 🔨 SUDAH DIPROFIL

`tools/profile_frame.py` memisahkan waktu frame jadi Python dan render, plus
cProfile dan hitungan GeomNode/Geom.

### Peringatan yang harus dibaca sebelum angka mana pun

Container sesi web ini **tidak punya GPU** — `/dev/dri` tidak ada dan Mesa
jatuh ke `llvmpipe`, rasterizer perangkat lunak di CPU. Di sana biaya frame
didominasi fill rate: mountain 158 ms di 1280×720 turun jadi 77 ms di 640×360
untuk seperempat piksel, artinya ~50 ms biaya tetap + ~108 ms fill.

Di mesin ber-GPU susunannya terbalik. Jadi **angka ms/frame dari sini tidak
boleh dipakai menilai target 30 FPS, dan tidak boleh dipakai memilih
optimasi.** Angka "104 ms per frame" yang beredar dari sesi-sesi sebelumnya
juga angka llvmpipe, bukan angka mesin pemilik.

Yang tetap sah diukur di sini karena tidak bergantung GPU: jumlah
Entity/GeomNode/Geom, waktu Python per frame, dan jumlah panggilan di
cProfile. Optimasi yang dipilih dari tiga angka itu menolong di mesin mana
pun.

### Yang sudah diukur

| scene | entity | GeomNode | Geom | python ms |
|---|--:|--:|--:|--:|
| mountain | 2.177 | 2.224 | 2.224 | ~24 |
| town | 1.884 | 1.906 | 1.906 | ~27 |
| farm | 1.257 | 1.390 | 1.390 | ~16 |

**GeomNode ≈ jumlah entity: hampir tiap entity satu batch sendiri.** Itu
masalah di mesin mana pun, bukan cuma di llvmpipe.

`flattenStrong()` **tidak menggabung apa pun** (1.993 → 1.993), bahkan setelah
`clearModelNodes()`. Jadi batching tidak bisa didapat dengan memanggil satu
fungsi; ia menuntut terrain dibangun sebagai mesh gabungan sejak awal, bukan
sebagai N entity kubus. Itu perombakan `world.py` yang besar, dan payoff-nya
**tidak bisa diukur di container ini** — jadi keputusannya milik pemilik, bukan
milikku.

### Yang sudah diperbaiki

Uniform rumput dipindah dari per-entity ke induknya. `update_time()` dulu
memanggil `set_shader_input` dua kali untuk tiap entity rumput, tiap frame — di
mountain 488 × 2 = 976 panggilan per frame, dan cProfile menunjukkannya sebagai
biaya Python terbesar di luar render (39.320 panggilan dalam 40 frame). Shader
input diwariskan ke keturunan, jadi sekarang dua panggilan. `_update` Ursina
turun 28,4 → 23,8 ms per frame. Penghematan ini portabel: ia sama besarnya di
mesin ber-GPU.

Sisa biaya Python didominasi Ursina sendiri (`has_disabled_ancestor` 2.044
panggilan per frame) — itu berbanding lurus dengan jumlah entity, jadi ia ikut
turun hanya kalau entity-nya berkurang.

Dijaga `rumput_lambai` di regress.py, yang menguji dua-duanya: piksel benar
bergeser saat `grs_time` berubah, DAN tidak ada entity rumput yang memasang
`grs_time` sendiri — karena input entity menimpa input induknya, dan satu
entity yang tertinggal akan membeku sendirian tanpa error apa pun.

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

## Patokan luar — lihat `docs/PATOKAN.md`

Gauntlet loop melawan Story of Seasons: A Wonderful Life **belum bisa
dijalankan** dari sesi web: egress-nya cuma GitHub (Steam dan Wikipedia
terukur ditolak) dan `_bench/refs/` kosong. Kritikus tanpa frame patokan akan
mengarang perbandingan lalu meluluskan semuanya — kegagalan nomor satu menurut
skill-nya sendiri.

`tools/bar_gate.py` sudah dipasang supaya itu tidak bisa terjadi diam-diam:
`check` menolak jalan tanpa patokan, `pair` mengacak urutan A/B dan memisahkan
kuncinya, `reveal` memutuskan lanjut-atau-ulang di luar agen mana pun.
`_bench/.gitignore` sekarang mengizinkan `refs/` supaya patokan yang diambil
tidak hilang lagi.

---

## Yang TIDAK akan dikejar

**Open world Sims 3.** Lima belas scene terpisah dengan frame rate segini
membuat itu lubang tanpa dasar. Yang dikejar cukup menghilangkan *rasa*
loading: transisi instan, kamera mempertahankan sudut, mendarat di tempat
yang masuk akal. Ini penyimpangan yang disengaja, bukan kesetaraan dengan TS3,
dan tidak akan diakui sebagai kesetaraan.
