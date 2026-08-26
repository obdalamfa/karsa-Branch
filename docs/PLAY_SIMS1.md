# PLAY_SIMS1.md — Autopsy: why The Sims 1 (2000) is still played in 2026

**Dibuat:** 2026-08-23 · **Untuk:** builder Lembah Karsa 3D
**Metode:** sumber primer & teknis, bukan nostalgia. Sumber utama:

| Sumber | Jenis | Dipakai untuk |
|---|---|---|
| `riperiperi/FreeSO` — `TSOClient/tso.simantics/Primitives/VMFindBestAction.cs` | kode + komentar penulis reimplementasi | §3 seluruhnya (algoritma advertising) |
| FreeSO — `Entities/VMTS1MotiveDecay.cs` | kode, tabel konstanta TS1 | §6 laju decay + rumus mood |
| FreeSO — `Files/Formats/IFF/Chunks/TTAB.cs` | kode, tabel atenuasi | §3 falloff jarak |
| FreeSO — `Engine/VMQueuedAction.cs` | kode, enum prioritas | §1, §5 antrian |
| FreeSO — `Model/VMMotive.cs`, `Primitives/VMSetBalloonHeadline.cs` | kode, enum | §5 kanal umpan balik |
| Will Wright, wawancara *New York Times*, 4 Feb 2025 | primer | §4 kenapa gagal itu lucu |
| Mark Brown (GMTK), *The Genius AI Behind The Sims* | retrospektif desain | §3, §4 |
| Don Hopkins (programmer UI The Sims), tulisan pie menu | primer | §5 |

> **Catatan kejujuran.** Setiap angka di dokumen ini yang saya kutip dari kode
> FreeSO ditandai **[FreeSO]**. Angka yang saya *usulkan* karena sumber aslinya
> ada di dalam `global.iff` dan tidak bisa saya ekstrak ditandai **[usulan]**.
> Jangan tukar keduanya diam-diam.

---

## 0. Tesis dalam tiga kalimat

The Sims 1 bertahan 25 tahun bukan karena grafis, karakter, atau cerita — tidak
punya ketiganya. Ia bertahan karena ia adalah **mesin tekanan yang selalu
berjalan, selalu terbaca, dan selalu bisa disalahkan pada diri sendiri**: delapan
angka yang turun tanpa henti, sebuah dunia yang penuh objek yang berteriak
"aku bisa memperbaiki angkamu", dan seorang aktor bodoh di tengahnya yang akan
memilih hal terdekat yang cukup baik — kadang salah, selalu di depan mata.

Bagian yang orang ingat (kolam renang tanpa tangga, kebakaran kompor, genangan
pipis) adalah **output** dari mesin itu, bukan fitur yang ditulis seseorang.

---

## 1. Core loop

### Satu kalimat

> **Waktu menggerus delapan kebutuhan; objek yang kamu beli mengiklankan diri
> sebagai obat untuk kebutuhan itu; kamu membelanjakan waktu dan simoleon untuk
> membeli obat yang lebih cepat, supaya besok kamu punya lebih banyak jam bebas
> untuk hal yang kamu pilih sendiri.**

### Diagram loop

```
            ┌───────────────── WAKTU (tidak pernah berhenti) ─────────────────┐
            │                                                                  │
            v                                                                  │
    ┌───────────────────┐                                                      │
    │  MOTIF MELURUH    │  hunger comfort hygiene bladder                      │
    │  (8 angka, -100.. │  energy  fun     social  room                        │
    │   +100, tiap 2    │                                                      │
    │   menit sim)      │─────────► MOOD = (Σ 7 motif + Room) / 8              │
    └───────────────────┘                    │                                 │
            ▲                                │  mood MENGGERBANGI hasil:       │
            │ diisi ulang                    │  kerja, sosial, skill, promosi  │
            │                                v                                 │
    ┌───────────────────┐   skor    ┌────────────────┐   1 aksi   ┌───────────┐│
    │ OBJEK MENGIKLANKAN│──────────►│  ANTRIAN 8 SLOT│───────────►│ ANIMASI + ││
    │ Δmotif + atenuasi │ autonomi  │ prio 50 > 2 > 0│  per waktu │ SUARA     ││
    │ (jarak menghukum) │ prio 2    └────────────────┘            │ (terbaca) ││
    └───────────────────┘                    ▲                    └───────────┘│
            ▲                                │                          │      │
            │                    klik pemain │ prio 50                  │      │
            │                    (selalu menang)                        │      │
            │                                                           v      │
            │                                                   MOTIF DIBAYAR ─┘
            │
    ┌───────────────────┐        ┌──────────────┐        ┌───────────────────┐
    │  BUY MODE         │◄───────│  SIMOLEON §  │◄───────│ KERJA / HASIL     │
    │  (belanjakan)     │ harga  │  (langka)    │  gaji  │ (digerbangi mood  │
    └───────────────────┘        └──────────────┘        │  + skill + hadir) │
            │                                            └───────────────────┘
            │                                                     ▲
            └──► objek lebih baik = iklan lebih besar = motif      │
                 terisi lebih cepat = jam bebas lebih banyak ──────┘
                 = skill + sosial naik = promosi = §  ──────► BESOK
```

### Terjemahan kolom

| Pertanyaan | Jawaban The Sims 1 |
|---|---|
| **Apa yang menciptakan tekanan?** | Peluruhan motif yang berjalan real-time dan **tidak bisa dijeda tanpa menjeda seluruh dunia**. Ditambah dua tenggat eksternal yang bukan kamu yang atur: mobil jemputan kerja (jam tetap, klakson, pergi tanpa kamu) dan tagihan. |
| **Apa yang meredakan tekanan?** | Objek. Bukan tombol, bukan menu — **benda fisik yang harus didatangi**, punya harga, punya tempat, bisa rusak, bisa dipakai orang lain. |
| **Apa yang pemain belanjakan?** | Dua mata uang: **jam sim** (langka: 16 jam bangun, dikurangi 8 jam kerja) dan **simoleon** (langka: §20.000 awal, gaji harian kecil). Objek mahal menukar simoleon menjadi jam. |
| **Apa yang pemain dapat?** | Bukan skor. Yang didapat adalah **penurunan biaya perawatan**: kasur mahal mengisi energy lebih cepat → bangun lebih pagi → waktu untuk skill → promosi → simoleon → kasur lebih mahal. Itu satu-satunya kurva progresi di game ini. |
| **Kenapa kembali besok?** | Tiga jangkar. (a) **Jadwal**: mobil jemputan besok pagi jam 8 — sesi berakhir di tengah kalimat. (b) **Investasi tak selesai**: kamu baru membangun setengah kamar mandi. (c) **Cerita yang kamu karang sendiri**: satu-satunya orang yang tahu kenapa Betty membenci Bob adalah kamu. |

**Yang perlu diperhatikan:** loop ini **tidak punya kondisi menang**. Yang
menahan pemain adalah keterikatan pada state yang mereka bangun sendiri, bukan
janji akhir. Untuk Lembah Karsa itu justru kabar baik — misteri StrangerVille
kita bisa menjadi tulang punggung yang The Sims 1 sengaja tidak punya.

---

## 2. Lima menit pertama

Rekonstruksi sesi pertama pemain baru. Struktur layar dan urutan mode adalah
fakta; penanda menit adalah rekonstruksi. **Tidak ada tutorial wajib.**

### 0:00 – 0:30 · Layar Neighborhood

Yang di layar: peta isometrik satu lingkungan, ±10 kavling. Sebagian berisi
rumah dengan keluarga siap pakai, sebagian tanah kosong bertanda harga. Tombol
besar: **"Create a family"**. Kursor melayang di atas kavling → muncul nama
keluarga dan harga.

**Yang diajarkan:** ini dunia berskala rumah, bukan berskala kota. Kamu memilih
*satu* titik. Keputusan pertama murah dan bisa dibatalkan.

### 0:30 – 1:30 · Create-A-Sim

Yang di layar: satu sim berputar di tengah, nama depan/belakang, pilihan kulit /
usia (dewasa atau anak) / kelamin / pakaian — dan yang penting: **25 poin
kepribadian** untuk dibagi ke lima batang: **Neat, Outgoing, Active, Playful,
Nice**. Total terkunci: menaikkan satu berarti menurunkan yang lain.

**Yang diajarkan:** sim bukan avatar kosong. Kelima batang itu adalah janji
bahwa "sim ini akan berperilaku berbeda dari sim itu" — dan janji itu ditepati:
`Active` mengubah laju peluruhan Comfort, `Outgoing` mengubah laju peluruhan
Social, dan seluruh lima dipakai sebagai pengali dalam skor autonomi (§3).
Keluarga baru mulai dengan **§20.000** berapa pun jumlah anggotanya.

### 1:30 – 2:00 · Live mode, detik pertama di kavling

Yang di layar, tepat setelah kavling dimuat:

- Kamera **dimetrik 2:1 ortografis**, dinding dekat dipotong jadi tunggul
  setinggi lutut sehingga interior terbaca.
- **Panel kontrol biru di kiri-bawah** — dan ini adalah guru sesungguhnya:
  tab Live/Buy/Build, jam, tanggal, angka **§**, tiga tombol kecepatan + jeda,
  potret sim, **delapan termometer motif**, dan satu **bar mood**.
- Sim berdiri di kavling. Di atas kepalanya **plumbob** berputar — hijau.
- Kotak antrian aksi kosong di dekat potret.

**Yang diajarkan, tanpa satu kata pun:** delapan batang itu **bergerak**.
Pelan, tapi bergerak, dari kanan ke kiri, terus-menerus, bahkan saat pemain diam.
Gerakan menarik mata. Pemain belum tahu apa itu "Bladder", tapi sudah tahu bahwa
ada delapan hal yang **memburuk**.

### 2:00 – 3:00 · Klik pertama — seluruh tata bahasa game diajarkan sekaligus

Pemain mengklik sesuatu. Apa pun. **Pie menu terbuka di posisi kursor** dengan
daftar kata kerja untuk objek itu (kulkas: *Have a Snack / Serve Meal*; kursi:
*Sit*; sim lain: *Talk / Hug / Joke*). Opsi yang belum boleh dipakai tampil
redup, tidak hilang.

Lalu — dan ini bagian yang mengajar — **sim tidak langsung teleportasi**. Sim
berjalan ke objek (rute terlihat), memutar animasi khusus objek itu selama
puluhan detik game, dan **satu termometer naik, terlihat, saat animasi berjalan**.

**Yang diajarkan dalam sepuluh detik:**
1. Setiap benda menjawab gestur yang sama (klik). Tidak ada verba tersembunyi.
2. Aksi memakan **waktu**, bukan instan → waktu adalah sumber daya.
3. Objek → animasi → batang naik. Rantai sebab-akibat lengkap dalam satu tayangan.
4. Ikon aksi muncul di kotak antrian, dan **klik ikon itu membatalkannya**.

Sementara itu, karena **free will menyala secara default**, sim juga melakukan
sesuatu sendiri dalam beberapa puluh detik pertama — memamerkan kata kerja yang
belum pemain temukan.

### 3:00 – 4:00 · Kegagalan terjadwal pertama

Bladder dan Hunger jatuh ke oranye lalu merah. Tiga hal terjadi **bersamaan**:

- Termometer berubah merah dan plumbob memudar dari hijau menuju merah.
- Sim mengeluarkan suara distress non-verbal (Simlish) — **afek tanpa bahasa**.
- **Balon pikiran** muncul di atas kepalanya berisi **gambar objek yang
  memperbaikinya**: toilet, atau kulkas.

**Yang diajarkan:** game baru saja memberi jawaban dalam bentuk gambar. Pemain
tidak perlu membaca apa pun. Dan pemain baru saja belajar bahwa **kegagalan
diumumkan sebelum terjadi** — ada ramp, bukan tebing.

### 4:00 – 5:00 · Loop kedua menempel

Biasanya ada yang tidak ada di rumah (tidak ada toilet, tidak ada kasur).
Pemain menekan **Buy**. Katalog terbuka: barang, **harga**, deskripsi. Pemain
menyeret satu benda ke lantai, angka **§** turun di depan mata.

Lalu telepon berdering / koran datang → pekerjaan → **mobil jemputan datang jam
tertentu besok pagi**.

**Yang diajarkan:** simoleon adalah cara mengubah masalah motif menjadi masalah
uang, dan pekerjaan adalah cara mengubahnya kembali. Dan ada **jam** di dunia ini
yang bukan kamu yang mengaturnya.

### Rangkuman: siapa gurunya

| Guru | Mekanisme |
|---|---|
| **Gerakan** | Batang yang bergerak saat pemain diam memaksa perhatian. |
| **Satu gestur universal** | Klik → pie menu. Berlaku pada **semua** hal. Tidak ada yang perlu dihafal. |
| **Latensi** | Sim berjalan dan beranimasi, jadi sebab dan akibat terpisah cukup lama untuk dilihat, tapi cukup dekat untuk dihubungkan. |
| **Ikon, bukan teks** | Balon pikiran menampilkan *objek*, bukan kalimat. Nol beban baca. |
| **Free will** | Sim mendemonstrasikan verba yang belum ditemukan pemain. Tutorial yang berjalan sendiri. |
| **Opsi terkunci tetap terlihat** | Pie menu redup = "ada lebih banyak, nanti". |

> **Untuk kita:** dari enam guru itu, kita saat ini punya **nol**. `panels.py:139-141`
> menyiapkan slot termometer lalu membiarkannya list kosong. Tanpa batang yang
> bergerak, tiga need kita (`lapar`/`sosial`/`senang`) tidak pernah menjadi
> tekanan — mereka hanya angka di file save.

---

## 3. Sistem advertising — jantung game

Ini bagian yang harus dibaca dua kali. Semua di bawah ini berasal dari
`FreeSO/TSOClient/tso.simantics/Primitives/VMFindBestAction.cs`, termasuk blok
komentar penulisnya sendiri yang menjelaskan cara kerja autonomi The Sims.

### 3.1 Bentuk data: apa yang objek pancarkan

Setiap objek membawa **tree table** (`TTAB`). Setiap baris = satu interaksi.
Tiap interaksi membawa daftar **motive advertisement**, satu per motif yang
diiklankan: **[FreeSO]**

```
TTABMotiveEntry:
    MotiveIndex          # motif mana (Hunger, Energy, …)
    EffectRangeMinimum   # "min"  — gerbang: hanya berlaku kalau motif sim <= min
    EffectRangeDelta     # "delta"— besar iklan (ditambahkan ke min → nilai absolut)
    PersonalityModifier  # indeks 0..22: kepribadian/skill mana yang memodulasi

TTABInteraction:
    ActionFunction, TestFunction   # BHAV aksi & BHAV pengecekan
    MotiveEntries[]                # semua iklan
    ActiveMotiveEntries[]          # hanya yang non-nol (cache)
    AttenuationCode  : uint        # 0=custom 1=none 2=low 3=medium 4=high
    AttenuationValue : float       # dipakai kalau code == 0
    AutonomyThreshold: uint
    JoiningIndex     : int         # interaksi ini bisa "ikut" ke objek yang sedang dipakai
    AutoFirst        : bool        # true = selalu ambil skor tertinggi, jangan acak
```

**Kunci arsitektural:** iklan menempel pada **interaksi**, bukan pada objek.
Kulkas tidak "memberi +40 hunger"; interaksi *Have a Snack* pada kulkas
mengiklankan hunger, sementara interaksi *Clean* pada kulkas yang sama
mengiklankan room. Objek yang sama menawarkan beberapa janji berbeda.

### 3.2 Kurva kontribusi — kenapa sim tidak makan saat kenyang

Sebelum apa pun, tiap motif mentah dipetakan lewat **interaction contribution
curve** menjadi "effective motive". Komentar penulis FreeSO, verbatim:

> "These curves generally make motive changes more evident at lower values, and
> cap them at a specific value. This prevents people from considering sleeping
> at 50% energy, but also allows other motives like fun to use a much higher cap."

Artinya kurva itu **cekung dan jenuh**: turunan besar di nilai rendah, hampir
datar di nilai tinggi. Konsekuensinya, seluruh sistem "prioritas kebutuhan"
muncul **gratis** dari bentuk kurva — tidak ada tabel prioritas di mana pun.
Sim yang lapar −80 menganggap +20 hunger jauh lebih berharga daripada sim yang
lapar +40 menganggap +20 hunger yang sama.

Kurva asli hidup di `global.iff` (tidak berhasil saya ekstrak). Tabel titik
kontrol berikut menghasilkan perilaku yang sama dan bisa langsung dipakai:
**[usulan]**

```
# C_fisik(x) — Hunger, Bladder, Energy, Comfort, Hygiene
#   curam di bawah 0, jenuh di atas +40  (cap rendah: kebutuhan tubuh)
x :  -100  -80  -60  -40  -20    0   20   40   60   80  100
C :  -100  -78  -58  -40  -24  -10    0    6   10   12   13

# C_sosial(x) — Fun, Social
#   lereng lebih landai, cap jauh lebih tinggi  (masih menarik saat sudah cukup)
x :  -100  -80  -60  -40  -20    0   20   40   60   80  100
C :  -100  -82  -64  -47  -31  -16    0   14   26   36   45

# C_linear(x) — Mood, Room
C(x) = x
```

Interpolasi linier antar titik. Perhatikan turunan `C_fisik` di x = −80 (≈1.1
per poin) versus di x = +60 (≈0.10 per poin): faktor **11×**. Itulah seluruh
"prioritas Maslow" yang sering dibicarakan orang.

### 3.3 Happy — fungsi objektif

**[FreeSO]** Sembilan motif berbobot, dan perhatikan **Mood ikut di dalamnya**
(jadi dihitung dua kali, sengaja):

```
WeightMotives = [Energy, Comfort, Hunger, Hygiene, Bladder, Mood, Room, Social, Fun]
w[i] = 1/9 untuk TS1        # seragam; Hot Date+ memakai kurva HappyWeight
happy_part[i] = C_i(motive[i]) * w[i]
base_happy    = Σ happy_part
```

### 3.4 Algoritma pemilihan — lengkap, siap diimplementasi

**[FreeSO]** — ini terjemahan langsung `VMFindBestAction.Execute`:

```python
def pilih_aksi_otonom(sim, dunia):
    # 0) Kalau antrian sudah punya aksi berprioritas lebih tinggi dari
    #    prioritas-diri sim, jangan berpikir sama sekali.
    if any(a.priority > sim.priority for a in sim.queue):
        return None

    atten_tabel = [0, 0, 0.01, 0.02, 0.03] if sim.is_visitor else [0, 0, 0.1, 0.3, 0.6]
    skor_min    = 1e-6 if sim.posture > 0 else 1e-7      # FCNS 2 di global.iff

    happy_part = [C[i](sim.motive[m]) * w[i] for i, m in enumerate(WEIGHT_MOTIVES)]
    base_happy = sum(happy_part)

    kandidat = []
    for obj in dunia.objek_dengan_autonomi:
        if obj.di_luar_dunia: continue
        obj = obj.multitile_group.leader           # satu skor per grup multi-tile

        # jarak dalam TILE (lantai dihitung 320 unit lalu dibagi 16)
        dz   = (sim.level - obj.level) * 320
        dist = sqrt((sim.x-obj.x)**2 + (sim.y-obj.y)**2 + dz**2) / 16.0

        sedang_dipakai = obj.flag_occupied

        for entry in obj.tree_table.auto_interactions:
            # objek sedang dipakai: hanya interaksi "joinable" yang lolos
            if sedang_dipakai and not obj.tree_table.punya_joining(entry.index):
                continue
            iklan = entry.active_motive_entries
            if not iklan: continue                 # objek tidak mengiklankan apa pun

            # BHAV pengecekan, dengan param0 = 1 ("ini pengecekan otonom").
            # Pengecekan boleh MENULIS ULANG min/delta/personality secara dinamis.
            hasil = sim.thread.check_action(obj.get_action(entry.index, sim))
            if hasil is None: continue

            skor = base_happy
            for ad in iklan:
                m    = ad.motive_index
                mn   = entry.motive_entries[m].effect_range_minimum
                mx   = entry.motive_entries[m].effect_range_delta
                pers = entry.motive_entries[m].personality_modifier
                mn, mx, pers = hasil.override(m, mn, mx, pers)   # dari check tree

                if mx == 0 and mn > 0:             # data cacat: perlakukan 0..min
                    mx, mn = mn, 0
                mx += mn                           # delta → nilai absolut

                nilai_kini = sim.motive[m]
                # GERBANG: iklan bermin hanya berlaku kalau motif sudah di bawah min
                if mn != 0 and nilai_kini > mn:
                    continue

                wi = WEIGHT_INDEX[m]
                if wi == -1: continue
                skor -= happy_part[wi]             # buang kontribusi motif ini

                pmul = 1.0
                if 0 < pers < 23:
                    pmul = sim.person_data[VARY_BY[pers]] / 1000.0   # 0..1
                    if pers < 13:
                        if pers % 2 == 0: pmul = 1.0 - pmul          # slot genap = terbalik
                    else:
                        pmul *= 2.0                                   # skill: 0..2
                # tambahkan kontribusi PREDIKSI
                skor += C[wi](nilai_kini + (mx * pmul) / 1000.0) * w[wi]

            skor -= base_happy                     # jadikan DELTA happy
            atten = (entry.attenuation_value
                     if entry.attenuation_code == 0 or entry.attenuation_code >= len(atten_tabel)
                     else atten_tabel[entry.attenuation_code])

            skor = skor / (1.0 + atten * dist)     # <<< FALLOFF JARAK

            if skor > skor_min:
                kandidat.append((skor, obj, entry))

    if not kandidat: return None
    kandidat.sort(key=lambda k: -k[0])
    # ambil 4 teratas yang benar-benar bebas (use_count == 0) atau joinable
    top4 = ambil_4_yang_bebas(kandidat)

    pilihan = top4[0]
    if not pilihan.entry.auto_first:
        # ROULETTE BERBOBOT di antara 4 teratas  <<< sumber "kebodohan" yang lucu
        total = sum(k.skor for k in top4)
        r = random(0, 10000); acc = 0
        for k in top4:
            acc += (k.skor / total) * 10000
            if r <= acc: pilihan = k; break

    sim.queue.enqueue(pilihan.aksi, priority=AUTONOMOUS)   # = 2
```

### 3.5 Bentuk skoring, diringkas ke satu baris

Karena `base_happy` saling meniadakan kecuali untuk motif yang diiklankan,
seluruh algoritma **setara dengan**:

```
                Σ_m∈iklan  [ C_m(motif_m + Δ_m·p_m) − C_m(motif_m) ] · w_m
   skor  =     ─────────────────────────────────────────────────────────────
                                1 + atenuasi · jarak_tile
```

dengan:

| Simbol | Arti | Nilai |
|---|---|---|
| `Δ_m` | nilai iklan (delta), **dibagi 1000** saat dipakai | dari TTAB. Komentar FreeSO: *"Motive delta is divided by 1000 for some reason. I don't really agree with this, but it matches numbers with TS 1.0."* |
| `p_m` | pengali kepribadian/skill | `kepribadian/1000` ∈ [0,1]; slot genap dibalik jadi `1−x`; skill ×2 → ∈ [0,2] |
| `w_m` | bobot motif | 1/9 seragam di TS1 |
| `C_m` | kurva kontribusi | cekung & jenuh (§3.2) |
| `atenuasi` | falloff jarak | **[FreeSO]** `[custom, none, low, med, high] = [0, 0, 0.1, 0.3, 0.6]`; pengunjung `[0, 0, 0.01, 0.02, 0.03]` |
| `jarak_tile` | Euklid 3D, lantai = 320 unit, hasil dibagi 16 | |

**Baca tabel atenuasi itu sebagai jangkauan siar:**

| Kode | Nilai | Skor tersisa @1 tile | @5 tile | @20 tile | Artinya |
|---|---|---|---|---|---|
| none | 0.0 | 100% | 100% | 100% | terdengar dari seluruh kavling (telepon, kebakaran) |
| low | 0.1 | 91% | 67% | 33% | terdengar dari seluruh rumah |
| medium | 0.3 | 77% | 40% | 14% | terdengar dari lantai yang sama |
| high | 0.6 | 63% | 25% | 8% | praktis hanya di ruangan yang sama |

Ini bukan radius keras. Objek yang cukup menggoda tetap menang dari jauh — dan
itulah kenapa sim berjalan melintasi rumah untuk kulkas saat kelaparan, tapi
duduk di kursi terdekat saat cuma sedikit tidak nyaman.

### 3.6 Enam properti yang membuat sistem ini bagus (dan wajib ditiru)

1. **Logika ada di objek, bukan di sim.** Menambah objek baru = menambah
   perilaku baru, tanpa menyentuh AI. Ini alasan 7 expansion pack bisa terbit
   tanpa merombak apa pun.
2. **Gerbang `min` menghasilkan urgensi tanpa state machine.** Iklan
   "hanya berlaku kalau motifmu di bawah X" adalah satu baris `if`, bukan
   sistem prioritas.
3. **Iklan boleh negatif.** Objek bisa aktif **menolak** dipakai saat motif
   sudah tinggi. Skor akhir yang ≤ 0 dibuang oleh `skor_min`.
4. **Check tree bisa menulis ulang iklan saat runtime.** Kompor yang kosong
   berhenti mengiklankan hunger tanpa perlu tabel state terpisah.
5. **Prediksi, bukan reaksi.** Skor dihitung dari `Happy(setelah) − Happy(sekarang)`.
   Sim membandingkan masa depan, bukan masa kini.
6. **Roulette 4-teratas.** Sim **bukan** pengoptimal. Ini disengaja (§4).

### 3.7 Antrian dan prioritas

**[FreeSO]** `VMQueuePriority`:

```
Maximum = 100     # tidak bisa dibatalkan (kebakaran, meninggal)
UserDriven = 50   # klik pemain
ParentIdle = 40
ParentExit = 30
Autonomous = 2    # free will
Idle = 0          # animasi diam
```

Aturan yang membuat game ini terasa responsif: **aksi otonom tidak pernah
menghapus aksi pemain**, dan pencarian aksi otonom bahkan **tidak dijalankan**
kalau antrian sudah berisi sesuatu yang lebih penting. Batas praktis antrian:
**8 aksi**; slot paling kiri sedang berjalan; klik ikon = batalkan aksi itu.

> **Untuk kita:** `game/config.py:101-103` sudah berisi
> `QUEUE_USER_DRIVEN=50 / QUEUE_AUTONOMOUS=2 / QUEUE_IDLE=0` — angka yang
> **persis sama** dengan enum FreeSO. Seseorang di proyek ini sudah membaca
> sumber yang benar. `QUEUE_AUTONOMOUS` dan `QUEUE_IDLE` saat ini tidak pernah
> dibaca siapa pun. Menyambungkannya ke `behavior_vm.BehaviorThread.push_action`
> (yang sudah menyortir berdasarkan prioritas) adalah pekerjaan satu sore.

---

## 4. Kenapa gagal itu menyenangkan

### Nama propertinya

> **Kegagalan di The Sims bersifat GENERATIF, bukan SUBTRAKTIF.**
> Setiap kegagalan **menambah** sesuatu ke dunia — objek baru, animasi baru,
> interaksi baru, karakter baru — alih-alih mencabut sesuatu dari pemain.

Genangan pipis bukan pesan error. Ia adalah **objek** dengan sprite, dengan
posisi, dengan pie menu-nya sendiri (*Mop*), yang mengiklankan Room negatif ke
seluruh ruangan, dan yang akan diinjak sim lain. Nyawa yang habis melahirkan
**batu nisan** — objek permanen di halaman, yang bisa diratapi, dipindahkan,
atau dijual. Kebakaran memanggil **pemadam kebakaran**, karakter baru yang
masuk ke rumahmu.

Bandingkan dengan game lain: kalah = layar merah, mundur ke checkpoint,
dunia dikembalikan. Di sini kalah = dunia bertambah kaya.

### Enam mekanisme yang menghasilkan properti itu

**(a) Ramp, bukan tebing.** Motif turun dari +100 ke −100 dalam hitungan jam
sim, dan setiap tahap punya sinyal sendiri: batang menguning → memerah →
plumbob memudar → balon pikiran → animasi rewel → penolakan → pingsan. Pemain
**melihat bencana datang selama sepuluh menit**. Karena kamu melihatnya datang,
itu salahmu. Karena itu salahmu, itu lucu, bukan tidak adil.

**(b) AI sengaja dibodohkan.** Ini didokumentasikan oleh perancangnya sendiri.
Will Wright, wawancara *New York Times*, 4 Februari 2025:

> "In early versions of the game, the autonomy was too good. Almost anything the
> player did was worse than the Sims running on autopilot."

Jawabannya bukan menaikkan kesulitan — melainkan **menurunkan kompetensi sim**
dan menambah kekacauan. Mekanisme teknisnya masih terlihat di kode: **roulette
berbobot di antara 4 kandidat teratas** (§3.4). Sim yang selalu memilih
optimum adalah sim yang tidak butuh pemain, dan sim yang tidak butuh pemain
bukan mainan.

**(c) Ketidakteraturan dipilih di atas akurasi, secara sadar.** Contoh yang
terdokumentasi: Maxis membuang "urinal buffer rule" (aturan yang menjaga jarak
antar-sim di toilet) sebelum rilis, karena perilaku yang teratur terasa bisa
ditebak. Memilih toilet secara acak menghasilkan momen lucu. **Mereka memilih
kelucuan di atas simulasi.**

**(d) Kegagalan punya kanal umpan balik sendiri di dalam engine.** Enum balon di
FreeSO memuat `RouteFailure` sebagai grup terpisah **[FreeSO]** — mesin ini
punya cara khusus untuk mengatakan "aku tidak bisa sampai ke sana". Kegagalan
bukan pengecualian; ia bagian dari kosakata.

**(e) Penolakan adalah pengajaran.** Sim yang menolak masuk kerja karena mood
terlalu rendah baru saja mengajarkan aturan yang tidak pernah tertulis di mana
pun. Frustrasi dan pembelajaran datang dalam paket yang sama.

**(f) Kepenulisan yang ambigu.** Karena free will menyala, pemain **tidak bisa
memastikan** apakah sim itu memilih sendiri atau menuruti perintahnya. Celah
itulah tempat cerita tumbuh. Wright:

> "It was fascinating to me how readily people would build a story around this."

### Aturan implementasi yang bisa langsung dipakai

| Aturan | Bentuk konkret |
|---|---|
| **Kegagalan melahirkan objek** | Setiap keadaan gagal harus memunculkan entitas di dunia dengan pie menu-nya sendiri. Tidak ada kegagalan yang hanya berupa teks. |
| **Kegagalan diumumkan ≥3 tahap** | warna → balon → animasi → konsekuensi. Jangan pernah langsung ke konsekuensi. |
| **Jangan pernah pilih argmax murni** | Roulette di antara N teratas. `N=4`. Ini bukan bug; ini fiturnya. |
| **Kegagalan bisa dipulihkan dengan harga** | Pemadam kebakaran, pel, dokter. Harga = simoleon/waktu, bukan progres. |
| **Kegagalan tidak pernah menghapus save** | Tidak ada game over. Kematian meninggalkan objek. |

> **Untuk Lembah Karsa:** ini juga resep horornya. StrangerVille berhasil karena
> yang biasa tetap berjalan normal di sekeliling yang salah. Entitas kita
> (`docs/entity-logo.svg` — akar yang ternyata kabel) paling menakutkan kalau ia
> muncul sebagai **objek yang mengiklankan motif dengan sangat baik**: bangku
> yang memberi Comfort +80 dan diam-diam menaikkan sesuatu yang tidak ada di
> panel. Sistem advertising bukan hanya mesin gameplay — ia adalah alat horor.

---

## 5. Legibility — pemain selalu tahu apa dan kenapa

The Sims 1 memakai **belasan kanal umpan balik yang berjalan bersamaan**, tiap
kanal membawa satu jenis informasi, dengan latensi berbeda. Tidak satu pun
berupa paragraf teks.

### Daftar lengkap kanal

| # | Kanal | Letak | Membawa apa | Latensi | Ada di kita? |
|---|---|---|---|---|---|
| 1 | **8 termometer motif** | panel biru kiri-bawah | nilai absolut tiap motif, −100..+100, berwarna | kontinu | ❌ slot kosong `panels.py:139-141` |
| 2 | **Bar mood** | di bawah termometer | agregat = rata-rata 8 motif | kontinu | ❌ |
| 3 | **Plumbob** | melayang di atas kepala sim | **mood**, hijau pekat → pucat → merah; juga menandai "ini sim aktif" | kontinu | ❌ |
| 4 | **Balon pikiran (`Balloon`)** | atas kepala | **ikon objek** yang sim inginkan / sedang dipikirkan | ~detik | ❌ |
| 5 | **Balon percakapan (`Conversation`)** | antara dua sim | topik obrolan sebagai ikon; kedua sim menampilkan ikon reaksi | selama sosial | ❌ |
| 6 | **Balon motif (`Motive`)** | atas kepala | motif spesifik yang sedang kritis | saat kritis | ❌ |
| 7 | **Balon relasi (`Relationship`)** | atas kepala | ❤ / 💔 naik-turun saat interaksi sosial | per interaksi | ❌ |
| 8 | **Balon gagal-rute (`RouteFailure`)** | atas kepala | "aku tidak bisa sampai ke sana" | saat gagal | ❌ |
| 9 | **Balon progres (`Progress`)** | atas kepala | aksi panjang sedang berjalan (memasak, belajar) | selama aksi | ❌ |
| 10 | **Balon uang (`Money`)** | atas kepala | § masuk/keluar | seketika | ❌ |
| 11 | **Ikon antrian aksi** | dekat potret sim | **8 slot**, kiri = sedang berjalan; ikon = objek target; **klik = batal** | kontinu | ⚠ satu angka `[ANT:n]` |
| 12 | **Animasi khusus per objek** | dunia | *apa* yang sedang dilakukan; siluet unik per aksi | kontinu | ⚠ ada Vitaboy, tidak dipakai |
| 13 | **Simlish** | audio | **afek** (senang/kesal/panik) tanpa bahasa | kontinu | ❌ |
| 14 | **SFX objek** | audio | objek mana yang aktif, dari luar layar | seketika | ✅ ada 23 SFX |
| 15 | **Pie menu redup** | kursor | verba yang ada tapi belum boleh | saat klik | ✅ sudah benar |
| 16 | **Cutaway dinding** | dunia | sim mana pun selalu terlihat, tak pernah tertutup | kontinu | ✅ sudah diperbaiki |
| 17 | **Jam + § + tanggal** | panel biru | tekanan eksternal | kontinu | ⚠ ada, tercecer di sudut |
| 18 | **Tombol kecepatan + jeda** | panel biru | kendali atas laju tekanan | kontinu | ❌ |
| 19 | **Harga di Buy mode** | katalog | biaya keputusan, sebelum diambil | saat browsing | ❌ |
| 20 | **Warna latar potret sim** | panel | ringkasan "sim ini butuh perhatian" saat kamu melihat sim lain | kontinu | ❌ |

Enum grup balon **[FreeSO]** (`VMSetBalloonHeadlineOperandGroup`) — ini adalah
daftar kanal resmi mesinnya:
`OldStyle(0) · Balloon(1) · Conversation(2) · Motive(3) · Relationship(4) ·
Headline(5) · Debug(6) · Algorithmic(7) · RouteFailure(8) · Progress(9) ·
Magic(10) · Money(255)`.

### Tiga prinsip yang dipakai berulang

1. **Redundansi silang-indera.** Setiap kejadian penting muncul minimal di dua
   kanal berbeda: *bladder kritis* = batang merah **+** plumbob memudar **+**
   suara **+** balon **+** animasi menyilang kaki. Pemain yang sedang melihat
   Buy mode tetap tertangkap oleh audio.
2. **Ikon menggantikan kalimat.** Nol beban baca, nol lokalisasi, nol waktu
   parsing. Balon pikiran menampilkan **gambar objeknya**.
3. **Setiap kanal punya satu pekerjaan.** Plumbob = mood, tidak pernah yang
   lain. Antrian = niat. Animasi = aksi. Balon = alasan. Tidak ada kanal yang
   membawa dua makna — jadi tidak ada yang perlu dihafal.

### Urutan pembangunan yang saya sarankan untuk kita

Kanal 1, 2, 3, 4, 11 adalah **80% keterbacaan dengan 20% pekerjaan**, dan
keempatnya butuh data yang sudah kita miliki. Kanal 3 (plumbob) adalah yang
paling murah dari semuanya: satu oktahedron, satu `color = lerp(merah, hijau, mood)`,
satu `billboard`. Kanal 4 (balon ikon) memerlukan katalog objek dulu.

---

## 6. Delapan motif: laju peluruhan nyata dan rumus mood

Semua angka di bagian ini **[FreeSO]**, dari `VMTS1MotiveDecay.Constants`.

### Skala dan tick

- Setiap motif adalah bilangan bulat dalam **[−100, +100]**. Lantai −100
  dipaksakan (`if (motive < -100) motive = -100`).
- Peluruhan berjalan **satu tick per 2 menit-sim** (`minutes/2 != LastMinute`).
- Akumulator per motif dalam **1/1000 poin**; saat ≥1000, satu poin penuh
  dikurangi dan sisanya disimpan. Ini mencegah pembulatan menumpuk.

### Tabel konstanta TS1 verbatim

```
[0]  energy span               180
[1]  wake hours                16
[2]  wake hour                 7
[3]  energy drift              0.01
[4]  hunger to bladder         0.3
[5]  hunger decrement ratio    0.0021
[6]  social decrement base     0.055
[7]  social decrement mult     0.000125
[8]  ent(fun) dec awake        0.25
[9]  ent mult asleep           1
[10] hyg decrement awake       0.17
[11] hyg decrement asleep      0.08
[12] blad decrement awake      0.3
[13] blad decrement asleep     0.15
[14] comfort decrement active  0.4
[15] comfort decrement lazy    0.6
[16] comfort decrement         0.5
```

### Peluruhan per motif, dikonversi ke satuan yang bisa dipakai

| Motif | Rumus per tick (poin) | Per jam-sim (bangun) | Waktu +100 → 0 | Catatan |
|---|---|---|---|---|
| **Hunger** | `0.0021 · (100 + Hunger)` | 6 @H=0 … **12 @H=100** | **≈11,6 jam** | Satu-satunya yang **non-linear**. Turun cepat saat kenyang, melambat saat lapar, berhenti di −100. Kurva: `H(t) = −100 + 200·e^(−0.002t)`, t dalam tick. |
| **Comfort** | `0.4` Active>666 · `0.5` =666 · `0.6` Active<666 | 12 / **15** / 18 | **≈6,7 jam** | Motif tercepat. Sim *malas* kehilangan comfort lebih cepat → lebih sering duduk. Kepribadian masuk ke laju peluruhan, bukan cuma ke pilihan. |
| **Hygiene** | `0.17` bangun · `0.08` tidur | **5,1** (2,4 tidur) | ≈19,6 jam | Paling lambat dari motif tubuh. Mandi sekali sehari cukup — sengaja. |
| **Bladder** | `0.3` bangun (`0.15` tidur) `+ 0.3 · r_Hunger` | **≈12,6 @H=100** | **≈8 jam** | **Tersambung ke Hunger**: makan mempercepat bladder. Satu-satunya kopling antar-motif di seluruh sistem, dan yang paling sering menghasilkan komedi. |
| **Energy** | `180 / (30 · 16)` = `0.375` | **11,25** | 16 jam turun 180 poin | Persis **energy span 180 dibagi 16 jam bangun**. Tidur (`SleepState = −1`) memulihkan **+1,286/tick = +38,6/jam** → 180 poin dalam ≈4,7 jam. Sim bangun otomatis pada jam **7** kalau Energy ≥ 80. |
| **Fun** | `0.25` bangun, **0 saat tidur** | **7,5** | ≈13,3 jam | Berhenti total saat tidur. |
| **Social** | `0.055 + 0.000125 · Outgoing` (Outgoing 0..1000) | 1,65 … **5,4** | ≈30–120 jam | Paling lambat. **Peringatan bug:** di kode FreeSO `ToFixed1000(0.000125)` terpotong menjadi **0**, jadi jalur TS1 di FreeSO hanya memakai basis 0,055. Pakai bentuk float-nya, bukan fixed-point-nya. |
| **Room** | **tidak meluruh** | — | — | Dihitung ulang tiap tick dari ruangan tempat sim berdiri: pencahayaan + nilai dekorasi objek − kotoran/kerusakan. Di FreeSO dibaca dari sistem lighting (`Light.RoomScore`). Ini satu-satunya motif yang **dikendalikan oleh Build/Buy mode, bukan oleh aksi**. |

### Rumus mood — verbatim

```
Mood = ( Hunger + Comfort + Hygiene + Bladder + Energy + Fun + Social + Room ) / 8
```

Rata-rata aritmetik **delapan** motif, termasuk Room. Rentang hasil −100..+100.
Sederhana sekali — dan itu keputusan desain, bukan kemalasan: pemain bisa
melakukan aritmetika ini di kepala sambil melihat panel.

Dua konsekuensi yang sering tidak disadari:

1. **Room adalah 1/8 dari mood, gratis, permanen, dan tidak pernah meluruh.**
   Membeli lampu dan lukisan menaikkan lantai mood seluruh keluarga selamanya.
   Ini yang membuat Buy mode terasa seperti progresi, bukan belanja hiasan.
2. **Mood juga menjadi salah satu dari 9 motif dalam perhitungan Happy autonomi
   (§3.3)** — jadi mood dihitung dua kali dalam pengambilan keputusan sim.
   Sim yang mood-nya jatuh menjadi lebih putus asa secara global, bukan cuma
   pada motif yang bermasalah.

### Bacaan yang harus diambil untuk desain kita

- **Tiga tempo berbeda menciptakan ritme.** Cepat (Comfort ~7 jam, Bladder ~8 jam)
  = interupsi konstan. Sedang (Hunger ~12 jam, Energy 16 jam) = struktur hari.
  Lambat (Hygiene ~20 jam, Social berhari-hari) = struktur minggu. **Tiga skala
  waktu adalah minimum.** Need kita saat ini semuanya lambat dan seragam
  (`config.py:96-98`: 0.020/0.015/0.012 → 3,5 s.d. 5,8 **hari**). Tidak ada
  yang pernah mendesak. Tidak ada tekanan. Itu sebabnya need kita tidak terasa.
- **Satu motif non-linear sudah cukup** (Hunger). Sisanya konstan.
- **Satu kopling antar-motif sudah cukup** (Hunger → Bladder), dan itu yang
  paling sering dikenang orang.
- **Kepribadian masuk ke laju peluruhan**, bukan cuma ke pilihan aksi.

---

## 7. Yang TIDAK layak ditiru

Blak-blakan. Kita tidak sedang membuat museum.

### A. Motif dan kebutuhan

1. **Bladder sebagai motif terpisah.** Lucu satu kali, tugas rumah selamanya.
   Di dunia kita (desa Indonesia, horor spiritual pelan), termometer kandung
   kemih merusak nada. **Gabungkan Hygiene + Bladder menjadi satu motif
   `Badan`** dan simpan komedi genangannya sebagai *kejadian* langka, bukan
   sebagai batang yang harus dijaga sepanjang waktu.
2. **Delapan batang itu terlalu banyak untuk dibaca sekilas.** Sims 2 dan
   seterusnya mempertahankan delapan tapi menambahkan agregat (mood + wants).
   Untuk kita: **lima motif** cukup — `Lapar`, `Badan`, `Tenaga`, `Senang`,
   `Sosial` — plus `Ruang` yang tidak meluruh dan berasal dari Build/Buy.
   Lima batang bisa dibaca dalam satu sakadik mata; delapan tidak.
3. **Spiral maut motif.** Sekali tertinggal, tidak ada jalan mengejar: motif
   rendah → mood rendah → aksi gagal → motif lebih rendah. Satu-satunya obat di
   TS1 adalah muat-ulang save. **Tambahkan lantai belas kasihan**: di bawah
   ambang tertentu, laju peluruhan melambat, dan aksi pemulihan mendapat bonus.
4. **Fixed-point 1/1000 dan pembagian ajaib "/1000" pada nilai iklan.** Itu
   artefak 1999 dan sudah menghasilkan bug nyata (`ToFixed1000(0.000125) == 0`).
   Pakai float. Normalkan `min` dan `delta` ke satuan yang sama.

### B. Struktur dunia

5. **Satu kavling aktif, sisa dunia beku.** Ini pembunuh langsung untuk kita.
   Pelajaran StrangerVille adalah **yang biasa harus tetap berjalan di sekeliling
   yang salah**. Kalau desa berhenti bernapas saat pemain masuk rumah, horornya
   mati. NPC kita sudah punya `SCHEDULES` untuk 36 entitas — jalankan sebagai
   simulasi ringan di luar layar.
6. **Tanpa penuaan, tanpa tahap hidup, tanpa genetika.** Anak-anak TS1 tidak
   pernah tumbuh. Dunia yang tidak berubah adalah dunia yang akhirnya
   ditinggalkan. Ditambahkan di The Sims 2 — dan itulah alasan utama orang
   pindah. Kita tidak butuh penuaan penuh, tapi butuh **sesuatu yang berubah
   permanen**: itulah gunanya `quest_stage` dan eskalasi entitas.
7. **Tanpa tujuan, tanpa wants/fears, tanpa cerita.** TS1 murni memberi kamu
   uang dan kebutuhan; "kenapa" seluruhnya dipasok pemain. Itu bekerja pada tahun
   2000 untuk demografi yang belum pernah melihat apa pun seperti itu. **Kita
   punya misteri; itu adalah tulang punggung yang sengaja tidak dimiliki TS1,
   dan tidak boleh kita buang demi kemurnian.**

### C. Pekerjaan dan ekonomi

8. **Karier sebagai kotak hitam.** Sim naik mobil jemputan, hilang 8 jam, pulang
   membawa §. Delapan jam waktu nyata-permainan tanpa apa pun untuk dilihat atau
   diputuskan. Itu bukan gameplay, itu jeda iklan. Kalau kita butuh ekonomi,
   ikat ke hal yang terlihat di kavling (bertani, kerajinan, menjaga warung).
9. **Tagihan lewat pos, yang harus diklik.** Administrasi tanpa keputusan.

### D. Antarmuka dan kontrol

10. **Pie menu bersarang dalam.** Bentuk radialnya benar dan wajib ditiru; tapi
    submenu tiga level di TS1 menyakitkan di trackpad modern. **Maksimal satu
    level bersarang.**
11. **Hanya tiga kecepatan, tanpa lompat-ke-kejadian.** Malam hari adalah
    delapan jam menonton orang tidur. Butuh "percepat sampai sesuatu terjadi".
12. **Ikon antrian 8-slot yang mungil.** Konsepnya wajib (antrian terlihat,
    klik untuk batal), ukurannya tidak.
13. **Tanpa autosave.** Tidak perlu dibahas.
14. **Build mode modal tanpa jaring pengaman.** Undo, eyedropper, dan aturan
    refund adalah penyempurnaan game-game berikutnya. Kalau kita membangun
    Build mode, mulai dari sana, jangan dari 2000.

### E. Perutean

15. **Rute yang rapuh.** Mesin TS1 punya kanal balon **khusus** untuk kegagalan
    rute (`RouteFailure`) karena rutenya cukup sering gagal sampai butuh UI
    sendiri. Kita **sudah punya** A* 8-arah dengan smoothing dan
    `_nearest_walkable` di `game/pathfinder.py` — kualitasnya lebih baik dari
    aslinya. **Tiru antriannya, jangan tiru kegagalan rutenya.**

### F. Yang layak ditiru prinsipnya, bukan implementasinya

16. **Simlish.** Prinsipnya benar dan penting — Matt Brown (Maxis):
    *"If we used actual language, the game would flatten and shrink, and everyone
    would be having the same experience."* Afek vokal non-linguistik membuat
    pemain memproyeksikan makna. Tapi **sintesis suku kata yang buruk lebih
    parah daripada tidak ada**. Alternatif murah dengan hasil setara: gumaman
    berpitch-acak dari beberapa sampel vokal pendek, dimodulasi oleh mood.
    Untuk kita, ini juga peluang: gumaman berbahasa-Jawa/Sunda yang dipotong
    sampai tidak terpahami akan terdengar tepat dan tidak asing.
17. **Free will global on/off.** Idenya benar; sakelarnya terlalu kasar dan
    tidak per-sim. Berikan slider, dan yang lebih penting: **tunjukkan
    alasannya** — balon "kenapa" saat sim memilih sendiri. TS1 tidak pernah
    memberi tahu kenapa; itu sumber frustrasi terbesar yang tersisa.

---

## 8. Ringkasan yang bisa dieksekusi untuk Lembah Karsa

Diurut berdasarkan (dampak pada keterbacaan permainan) ÷ (biaya).

| # | Pekerjaan | Sudah ada apa | Yang perlu ditulis |
|---|---|---|---|
| 1 | **Termometer motif + bar mood + plumbob** | data need di `state.py:63-65`; slot UI di `panels.py:139-141` (kosong) | isi slot, tambah entitas oktahedron ber-billboard, `color = lerp(merah, hijau, mood)` |
| 2 | **Tiga tempo peluruhan** | `config.py:96-98` (semua terlalu lambat, seragam) | ganti ke rasio §6: satu cepat (~7 jam), satu sedang (~12 jam), satu lambat (~hari) |
| 3 | **Katalog `OBJECTS` dengan iklan** | belum ada sama sekali; `data.py` sudah punya idiom tabel | `{id, nama, harga, footprint, interaksi:[{verb, ads:{motif:(min,delta,pers)}, atten}]}` |
| 4 | **Skorer autonomi** | `behavior_vm.py` VM lengkap, queue berprioritas sudah benar | ±80 baris: `pilih_aksi_otonom()` dari §3.4, dengan kurva §3.2 |
| 5 | **Sambungkan prioritas antrian** | `config.py:101-103` sudah berisi angka FreeSO yang benar | pakai `QUEUE_AUTONOMOUS` saat mengantre dari skorer; jangan pernah timpa `QUEUE_USER_DRIVEN` |
| 6 | **Balon ikon** | butuh #3 dulu (ikon = ikon objek) | billboard quad + atlas ikon |
| 7 | **Pie menu radial pada objek** | `interaction_controller.py:447-491` sudah kondisional + pratinjau efek motif — filosofinya sudah benar | ubah target dari NPC-saja ke objek, dan bentuk dari list ke busur |

---

## Lampiran: sumber

- FreeSO — `TSOClient/tso.simantics/Primitives/VMFindBestAction.cs` (algoritma autonomi lengkap + komentar penulis) — https://github.com/riperiperi/FreeSO
- FreeSO — `TSOClient/tso.simantics/Entities/VMTS1MotiveDecay.cs` (konstanta peluruhan TS1, rumus mood)
- FreeSO — `TSOClient/tso.simantics/Entities/VMAvatarMotiveDecay.cs` (varian TSO, nama tuning yang sama)
- FreeSO — `TSOClient/tso.files/Formats/IFF/Chunks/TTAB.cs` (tabel atenuasi, struktur iklan)
- FreeSO — `TSOClient/tso.simantics/Engine/VMQueuedAction.cs` (`VMQueuePriority`)
- FreeSO — `TSOClient/tso.simantics/Model/VMMotive.cs` (enum 16 motif)
- FreeSO — `TSOClient/tso.simantics/Primitives/VMSetBalloonHeadline.cs` (grup balon)
- Will Wright, wawancara *The New York Times*, 4 Feb 2025 — dikutip via TheGamer (7 Feb 2025) dan PC Gamer
- Mark Brown, *The Genius AI Behind The Sims*, GMTK
- Don Hopkins, *The Design and Implementation of Pie Menus* (Dr. Dobb's Journal, Des 1991) + *Pie Menu Central*
- Rhys Simpson, *Volcanic: an Open Source SimAntics IDE* (freeso.org/stuff/Volcanic.pdf — 403 saat diakses; dikutip lewat rujukan sekunder)
- The Sims Wiki: Plumbob, Free will, Action queue (verifikasi perilaku UI)
