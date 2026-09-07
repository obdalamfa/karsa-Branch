# INTEGRASI — menyatukan pekerjaan dari banyak sesi ke satu sumber

Pekerjaan proyek ini tersebar di belasan cabang dari sesi obrolan yang berbeda.
Dokumen ini menetapkan cabang mana yang jadi sumber tunggal, urutan menariknya,
dan — sama pentingnya — **apa yang sengaja TIDAK ditarik**.

Ditulis 2 Sep 2026. Angka konflik di bawah diukur dengan
`git merge-tree --write-tree HEAD <cabang>`, bukan ditebak. Ukur ulang sebelum
memakainya; angkanya bergeser tiap kali sumber bergerak.

## Sumbernya: `claude/lembah-karsa-3d-visuals-6729d1`

Dipilih bukan karena paling baru, tapi karena satu-satunya yang punya **bukti**:
dua potongan (HUD dan permukaan tanah) sudah MENANG penilaian buta melawan
Story of Seasons: A Wonderful Life, dan seluruh isinya lolos `tools/regress.py`
14/14 di tiap commit.

## Kenapa bertahap, dan kenapa itu bisa

Repo ini punya gerbang objektif: `python tools/regress.py` harus 14/14 scene
lulus, 0 pemeriksaan gagal. Itulah yang membuat integrasi bertahap aman —
tiap langkah bisa DIBUKTIKAN tidak merusak, bukan diharapkan tidak merusak.
Proyek tanpa gerbang seperti ini terpaksa merge sekaligus dan berdoa.

Aturannya satu: **satu langkah, satu regresi, satu commit.** Langkah yang
membuat regresi merah tidak dihitung selesai.

Catatan mesin: mesin ini sesekali menghasilkan frame HITAM yang membuat regresi
merah palsu — gejalanya `frame_kosong` dan nilai `(0,0,0)` di banyak scene
sekaligus. Kalau itu muncul, JALANKAN ULANG sekali sebelum menyimpulkan langkah
itu merusak sesuatu. Ini sudah pernah menipu satu sesi penuh.

## Urutan, dari risiko terkecil

### 1. `fix/town-magenta-sky` — 1 commit, **0 konflik**, 2 berkas
Memperbaiki langit magenta di `town` siang hari (warna karangan, bukan tekstur
hilang). Tarik lebih dulu: nol risiko, dan ia menutup bug nyata yang ditemukan
saat menangkap bukti potongan BICARA.

    git merge --no-ff fix/town-magenta-sky
    python tools/regress.py

### 2. `origin/claude/lembah-karsa-livestock-interactions-5s1z13` — 31 commit, 7 konflik, 24 berkas
Penghalusan interaksi ternak: memerah dilakukan di bawah perut bukan di atas
punggung, tinggi punggung domba dikoreksi, vonis dua belas aksi, lawan bicara
berpaling alih-alih mematah.

Tumpang tindih LANGSUNG dengan yang baru dikerjakan di sumber (`husbandry.py`,
`interaction_controller.py`, `animal_models.py`, `animal.py`), jadi ketujuh
konfliknya nyata dan harus diadili satu per satu — bukan diselesaikan dengan
`-X ours`/`-X theirs`. Idiom kodenya sama (komentar Indonesia, commit naratif),
jadi keputusannya biasanya jelas saat kedua sisi dibaca.

Perhatian khusus: sumber sudah mengubah `husbandry.clean()` supaya menyikat
hewan yang SUDAH bersih tetap boleh. Jangan biarkan versi lama mengembalikannya
— penolakan itu membuat animasi menggosok tidak pernah bisa dijalankan sama
sekali di hari pertama.

### 3. `feature/3d-mobs` — 79 commit, **83 konflik, 561 berkas** → PORT, BUKAN MERGE
Isinya paling berharga di seluruh repo:

- skill & karier (naik dengan MELAKUKAN, kerja berjadwal, promosi)
- mode Bangun/Beli (beli, pasang, jual objek dengan Simoleon)
- rumah tangga & Simoleon (anggota, setoran, tagihan berkala)
- aspirasi & keinginan + tahap hidup
- pose BERTAHAN untuk aksi objek (Sim benar-benar duduk/tidur/mandi)
- walk cycle 4-frame, pose NPC per-aktivitas
- combat & mob, gua, naga
- `PANDUAN.md` — panduan pemain

83 konflik di 561 berkas berarti hasil `git merge` di sini tidak bermakna:
seluruh waktu habis mengadili konflik, dan yang keluar tidak teruji. Untungnya
sebagian besar isinya **modul baru**, dan modul baru justru paling bersih kalau
di-port satu per satu.

Urutkan dari yang paling sedikit menyentuh berkas yang sudah ramai
(`player.py`, `panels.py`, `world.py`):

1. skill & karier — sistem sendiri, sentuhan ke berkas lama paling sedikit
2. rumah tangga & Simoleon — bersandar pada economy yang sudah ada
3. mode Bangun/Beli — butuh HUD; hati-hati, HUD sumber sudah MENANG buta
4. aspirasi & keinginan + tahap hidup
5. pose bertahan & walk cycle — bertabrakan dengan kerja animasi di sumber
6. combat & mob — paling besar, paling terakhir

Tiap nomor: satu cabang kerja, satu regresi hijau, satu commit yang menyebut
dari mana ia diambil.

### 4. Cabang overhaul visual — **JANGAN DI-MERGE**
`claude/compassionate-dubinsky-0bfba8`, `claude/magical-taussig-df3971`,
`claude/loving-hamilton-32afda` sama-sama membawa `e434cff` — "Overhaul visual
& sistem: Disco Elysium/Shaman aesthetic, HUD Doom, aset CC0".

Itu arah seni yang BERBEDA dan sudah ditinggalkan. Arah sekarang Story of
Seasons / FreeSO, dan HUD arah sekarang sudah MENANG penilaian buta melawan
patokan. Menarik overhaul Doom ke dalamnya membuang kemenangan yang sudah
dibuktikan, bukan menambahnya.

Kalau ada aset di sana yang masih ingin dipakai, ambil **asetnya saja**
(`git checkout <cabang> -- assets/<berkas>`), jangan cabangnya.

`claude/loving-hamilton-32afda` juga memuat snapshot combat/mob — abaikan,
`feature/3d-mobs` versinya lebih lengkap.

### 5. `claude/charming-lehmann-1b13fd` — 1 commit, 57 konflik, 397 berkas
Isinya sinkronisasi ASET (NPC/mob/props/pohon baked + pose, sumbu Y-up).
Hampir semuanya berkas aset, bukan kode. Ambil selektif per berkas setelah
langkah 3 selesai, dan verifikasi tiap model dengan tangkapan layar — sumbu
Y-up pernah membuat prop tergeletak di tanah dan berwarna putih.

## Cabang yang sudah tidak perlu diapa-apakan

Ini semua 0 commit unik terhadap sumber — isinya sudah ada di dalamnya:
`claude/dazzling-lichterman-bbab90`, `claude/keen-sutherland-656cc1`,
`claude/loving-banach-ca263e`, `claude/mystifying-kowalevski-24ce6c`,
`claude/nice-shamir-93f5de`, `claude/gauntlet-loop-overhaul-f1af15`,
`origin/claude/lanjutkan-apakah-bisa-ya8ip3`, `master`.

## Yang harus ikut tumbuh, kalau tidak semuanya membusuk diam-diam

`tools/regress.py` sekarang menjaga 14 scene plus otonomi dan arah WASD. Sistem
yang di-port di langkah 3 TIDAK dijaga apa pun. Tiap sistem yang masuk harus
membawa satu pemeriksaan, kalau tidak ia akan rusak tanpa suara.

Itu bukan kekhawatiran teoretis. Dalam satu sesi saja ditemukan EMPAT bug
berbentuk sama, dan tidak satu pun melempar exception:

- aksi pie-menu yang DITOLAK diam-diam, terbaca sebagai "animasi belum dibuat"
- animasi alat yang berbicara ke rig prosedural sementara yang dirender rig TSO
- frame hitam pekat yang lolos sebagai `CAPTURE_OK`
- alat yang digantung di pivot yang tidak menggerakkan satu vertex pun

Semuanya gagal DIAM. Gerbang yang tidak tumbuh bersama fiturnya adalah gerbang
yang perlahan berhenti menjaga apa pun.

## Setelah semuanya masuk

Jadikan `claude/lembah-karsa-3d-visuals-6729d1` (atau hasil merge-nya ke
`master`) satu-satunya cabang hidup, lalu hapus sisanya supaya tidak ada lagi
yang bertanya "versi mana yang benar". Sebelum menghapus, pastikan tiap cabang
benar-benar 0 commit unik:

    git log --oneline master..<cabang>
