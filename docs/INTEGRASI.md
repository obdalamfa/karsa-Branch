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

---

# Vonis konflik merge feature/3d-mobs (2 Sep 2026)

143 konflik awal. **118 di antaranya `.pyc`** — bytecode yang seharusnya tidak
pernah dilacak git; semuanya dikeluarkan dari indeks dan `.gitignore` diperketat.
Sisanya 25 berkas / 58 blok kode nyata. Tiap satunya dibaca.

Aturannya satu: **yang sedang DINILAI tetap milik sisi visual; yang BELUM PERNAH
ADA diambil dari 3d-mobs.**

| Berkas | Blok | Vonis |
|---|---|---|
| `.gitignore` | 1 | **mereka** (jauh lebih lengkap) + catatan bytecode kita |
| `lembah_karsa_3d_save.json` | — | **kita** (dihapus di sisi mereka; permainan membacanya saat boot) |
| `game/state.py` | 3 | **keduanya** — motif kita + SELURUH field Sims mereka + tulis-atomik mereka |
| `game/animal.py` | 1 | **keduanya** — `ayun_kaki()` kita (dipakai berkuda) + `update_anim()` mereka |
| `game/animal_models.py` | seluruh | **keduanya** — ternak+kaki kita + 10 fungsi entitas liar mereka |
| `game/scenes/scene_base.py` | seluruh | **keduanya** — `Scene(paint=)` kita + pembangun ruangan mereka (superset) |
| `game/controllers/interaction_controller.py` | 12 | **campur** — blok 5/9/10/11 mereka (relasi + `lamar_kerja`), sisanya kita |
| `game/controllers/time_controller.py` | 2 | **campur** — mesin motif kita + tahap hidup & kelaparan mereka + DUA laporan pagi |
| `game/entities.py` | 6 | **kita** (jalur spawn avatar TSO) + `load_texture_file`/`MODEL_COLORS` mereka |
| `game/panels.py` | 7 | **kita** (HUD sudah menang buta) + `_build_batin`/`_build_buy`/`_build_pause` mereka; `emote()` DITULIS ULANG |
| `game/scenes/props.py` | 8 | **kita** (town.py bergantung zone_paint) + `scatter_obj_props` mereka |
| `game/scenes/{clinic,shop,smith,studio}.py` | 1 ea | **mereka** (interior lebih kaya) + koordinat portal KITA |
| `game/scenes/{greenhouse,mountain}.py` | 1 ea | **mereka** |
| `game/scenes/town.py` | seluruh | **kita** (kerja DESA, ada di tangkapan layar yang dinilai) |
| `game/scenes/farm.py` | seluruh | **kita** |
| `game/player.py` | seluruh | **kita** — berkuda, tangan, wajah, klip TSO |
| `game/world.py` | seluruh | **kita** — tekstur terrain, sebaran, normal mesh prosedural |
| `game/app.py` | seluruh | **kita** |
| `game/smooth_shader.py` | 4 | **kita** — bahu sorot, normal dua-sisi |
| `game/grass_shader.py` | 1 | **kita** |
| `game/sky.py` | 1 | **kita** — perbaikan langit magenta |

## Empat kali merge ini gagal boot, dan semuanya satu pelajaran

**Struktur kendali tidak bisa digabung sepotong-sepotong.**

1. `entities.py` — mencampur cabang `if`/`else` dari dua sisi di dalam SATU
   fungsi menghasilkan `else:` yatim di baris 730. Diperbaiki dengan mengambil
   jalur spawn utuh dari satu sisi, lalu menambahkan helper tingkat-modul
   sisi lain secara terpisah.
2. `panels.py` — mengambil blok HUD dari sisi visual ikut menghapus `emote()`,
   yang ternyata hanya ada di sisi 3d-mobs DI DALAM blok itu, padahal
   `interaction_controller` yang baru digabung memanggilnya.
3. `panels.py` lagi — `_build_batin`, `_build_buy`, `_build_pause` hilang dengan
   cara yang sama, dan game GAGAL DIBANGUN TOTAL (`AttributeError` saat boot).
4. `props.py` — mengambil sisi visual menghilangkan `scatter_obj_props`,
   sehingga `mountain`, `lake`, dan `cemetery` gagal boot dengan `ImportError`.

Polanya sama tiap kali: sebuah nama dipanggil dari bagian berkas yang datang
dari SATU sisi, sementara definisinya jatuh di dalam blok yang dimenangkan sisi
LAIN. Cara mendeteksinya murah dan harus dilakukan tiap kali:

    # metode dipanggil tapi tidak didefinisikan
    grep -oE "self\.(_[a-zA-Z]\w*)\(" berkas.py | sort -u
    # nama yang di-import dari satu modul tapi tidak ada di sana
    grep -rE "from .*props import" game/

## `emote()` ditulis ulang, bukan diambil

Versi 3d-mobs menaruh tiap emote di `self._emotes` dan menyerahkan pemudarannya
ke loop tick DI DALAM blok HUD — blok yang kalah. Mengambilnya berarti menukar
kemenangan buta dengan sebuah animasi teks. Versi di pohon ini menjadwalkan
penghapusannya sendiri lewat `invoke(destroy, e, delay=dur)`: tidak ada state
bersama, dan tidak ada dua tempat yang harus ingat.

## Yang dimenangkan sisi visual TIDAK dibuang

Perubahan sisi 3d-mobs untuk berkas-berkas itu diarsipkan utuh sebagai diff di
`_bench/port/` — 2.601 baris total. Port sepotong-sepotong dari sana, jangan
merge ulang cabangnya:

    _bench/port/game_scenes_props.py.diff   1805 baris
    _bench/port/game_app.py.diff             336 baris
    _bench/port/game_scenes_town.py.diff     243 baris
    _bench/port/game_world.py.diff           231 baris
    _bench/port/game_scenes_farm.py.diff     160 baris
    _bench/port/game_player.py.diff          145 baris
    _bench/port/game_smooth_shader.py.diff    26 baris
    _bench/port/game_sky.py.diff              18 baris
    _bench/port/game_grass_shader.py.diff     10 baris
