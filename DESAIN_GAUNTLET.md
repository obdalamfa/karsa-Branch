# DESAIN ULANG — GAUNTLET LOOP
### Lembah Karsa 3D · menyatukan semua sistem yang sudah dibangun

> Dokumen ini punya dua bagian: **AUDIT** (fakta, diverifikasi di kode) dan
> **DESAIN** (usulan). Keduanya sengaja dipisah agar tak tertukar.

---

## 0. Inti gagasan

Game ini sekarang punya **dua dunia yang tak saling bicara**:

| | Permukaan | Gua |
|---|---|---|
| Rasa | tenang, mengurus hidup | seharusnya tegang |
| Sistem | 10 sistem Sims (S1-S10) | tempur + tambang |
| Kenyataan | matang | **tak ada tekanan** |

**Gauntlet loop** menyatukannya jadi satu **pendulum**:

```
   PERMUKAAN                    GUA (gauntlet)
   bangun modal      ──────►    belanjakan modal
   (motif, alat,                (motif menetes, tak ada
    bekal, relasi)               pemulihan, makin dalam
                                 makin berbahaya)
        ▲                              │
        │                              ▼
        └──────  PULANG membawa hasil ─┘
                 (atau pulang dgn tangan hampa)
```

**Kuncinya:** kita **tidak menambah sumber daya baru**. Motif Sims (S1) yang
sudah ada **menjadi jam pasir gauntlet**. Itu sebabnya desain ini memakai apa
yang sudah dibangun, bukan menempel sistem asing.

---

## 1. AUDIT — kenapa gua sekarang TIDAK tegang

Tujuh temuan, semuanya diverifikasi langsung di kode.

| # | Temuan | Bukti | Dampak |
|---|---|---|---|
| **A1** | **Tak ada batas bawaan.** Inventaris tanpa kapasitas; `upgrades['bag']` cuma flag mati | `state.py:59` — tak ada kode yang membacanya | Tak ada keputusan "bawa apa pulang" |
| **A2** | **Turun-naik gratis.** Tangga tak memungut biaya apa pun | `player.py:931-953` — hanya `dungeon_level ±1` | Bisa yo-yo; tak ada komitmen |
| **A3** | **Obor cuma barang jualan.** Ada di `WILD_ITEMS` & resep, tapi tak ada mekanik cahaya | `data.py:50,64` | Kegelapan tak jadi ancaman |
| **A4** | **Mati nyaris tanpa hukuman.** HP 25%, energi 1/3, balik lantai 1 — **barang bawaan utuh** | `combat_controller.py:516-519` | Mati = rugi waktu, bukan rugi taruhan |
| **A5** | **Tidur memulihkan SEGALANYA.** `energy` & `hp` langsung penuh | `time_controller.py:67-68` | Modal gratis tiap pagi; tak ada biaya jangka panjang |
| **A6** | **Kesulitan mentok cepat.** `n_mobs = min(3 + level//2, 8)` | `dungeon.py:156` | Lantai 10 ≈ lantai 20 |
| **A7** | **Air mancur naga = flag mati.** Di-reset tiap hari, tak pernah dipakai | 2 kemunculan: definisi + reset | Pemulih yang sudah dirancang, terbuang |

**Yang sudah benar (jangan diubah):**
- ✅ Tak bisa tidur di gua (`try_sleep` menuntut `scene_name == 'house'`) — pembatas alami sudah ada.
- ✅ Motif tetap meluruh di gua (tick jalan di semua scene) — **jam gauntlet sudah berdetak, tinggal diberi taring.**
- ✅ Mob punya telegraph & bisa dielak — dasar tempur yang adil sudah ada.

**Kesimpulan audit:** gua tidak butuh sistem baru. Ia butuh **konsekuensi**.

---

## 2. DESAIN — Gauntlet Loop

### 2.1 Motif = jam pasir

Di dalam gua **tak ada satu pun objek Sims** (tak ada ranjang, toilet, kulkas).
Motif terus menetes; mood ikut jatuh; dan mood **sudah** memengaruhi kecepatan
aksi & sosial (S4). Tambahkan satu sambungan: **mood juga memengaruhi tempur**.

> Makin dalam kau turun, makin lemah dirimu. Itulah inti Gauntlet — dan kita
> mendapatkannya gratis dari sistem yang sudah ada.

### 2.2 Empat tekanan (naik bertahap, bukan sekaligus)

1. **Bekal terbatas** — bawa makanan & obor; keduanya habis dipakai.
2. **Cahaya** — obor menyala menetes; gelap = penglihatan sempit + mob lebih galak.
3. **Beban** — kapasitas bawaan nyata (`upgrades['bag']` akhirnya hidup). Bijih berat.
4. **Taruhan** — pingsan = **kehilangan sebagian muatan**, bukan sekadar waktu.

### 2.3 Keputusan push-your-luck

Tiap tangga turun menyodorkan satu pertanyaan jujur:

> *Motif 40%, tas 70% penuh, obor tinggal 1. Turun (bijih lebih baik) atau pulang?*

Itu **satu-satunya** keputusan yang perlu diciptakan. Sisanya sudah ada.

### 2.4 Titik aman (pacing)

Tiap **5 lantai** ada **kamar mata air** (hidupkan A7): isi sebagian motif,
sekali per kunjungan. Ini memberi ritme "napas" dan menjadikan lantai 5/10/15
sebagai penanda kemajuan — bukan sekadar angka.

---

## 3. Peran tiap sistem yang sudah dibangun

Ini bagian terpenting: **tak ada sistem yang jadi hiasan.**

| Sistem | Perannya dalam gauntlet |
|---|---|
| **S1 Motif** | **Jam pasir.** Sumber tekanan utama |
| **S2 Objek** | **Ketiadaannya** yang bicara — gua sengaja kosong dari objek |
| **S3 Autonomi** | **Dimatikan di gua** (Sim tak bisa "mengurus diri" saat menyelam) |
| **S4 Mood** | Mood buruk → aksi lambat **+ tempur melemah** (sambungan baru) |
| **S5 Relasi** | Sahabat ≥5 hati bisa **membekali** atau **menolong** saat pingsan (kurangi kehilangan) |
| **S6 Skill** | **Kebugaran** = daya tahan gauntlet; **Kerajinan** = obor lebih awet |
| **S7 Bangun/Beli** | Perabot rumah = **pemulihan lebih cepat** → lari berikutnya lebih jauh |
| **S8 Rumah tangga** | **Tagihan = alasan turun.** Tekanan ekonomi mendorong ke gua |
| **S9 Aspirasi** | Memberi arah jangka panjang & hadiah untuk kedalaman |
| **S10 Tahap hidup** | **Anak dilarang menyelam**; lansia lebih cepat lelah tapi lebih bijak |
| Tani/Peti Kirim | Pemasukan **aman & lambat** — kontras terhadap gua yang **cepat & berisiko** |
| Quest 11 tahap | Kerangka cerita; kedalaman jadi tolok ukurnya |

**Ekonomi jadi punya dua kutub:**
- **Bertani** = untung kecil, risiko nol, butuh waktu
- **Menyelam** = untung besar, bisa rugi, butuh persiapan

Itu pilihan bermakna — yang selama ini belum ada.

---

## 4. Angka usulan (titik awal, wajib disetel saat playtest)

| Hal | Usulan |
|---|---|
| Kapasitas tas | 20 slot (+15 bila `upgrades['bag']`) |
| Berat bijih | 2 slot; permata 1; makanan 1 |
| Obor | 1 obor = ±90 detik nyala |
| Gelap | jarak pandang −60%, mob +25% damage |
| Motif di gua | peluruhan ×1.5 |
| Mati | kehilangan **50%** muatan (sahabat: 25%) |
| Mata air | tiap 5 lantai, isi 60% motif, sekali/kunjungan |
| Bijih per lantai | nilai ×(1 + 0.15·lantai) |
| Mob | hapus batas 8 → `3 + level*0.8` |

---

## 5. Rencana bangun (bertahap, tiap tahap bisa diuji)

| Tahap | Isi | Kenapa urutannya begini |
|---|---|---|
| **G1** | Kapasitas tas + berat barang | Menciptakan keputusan "bawa apa" — fondasi |
| **G2** | Bekal & obor + mekanik gelap | Memberi jam yang terlihat pemain |
| **G3** | Motif ×1.5 di gua + autonomi mati + mood→tempur | Menyalakan jam pasir |
| **G4** | Taruhan: pingsan = kehilangan muatan (relasi meringankan) | Memberi risiko nyata |
| **G5** | Kamar mata air tiap 5 lantai (hidupkan A7) | Memberi ritme & penanda |
| **G6** | Skala kesulitan & nilai bijih per kedalaman | Menyeimbangkan imbalan |

Tiap tahap: asersi di `smoke_boot.py` + commit terpisah.

---

## 6. Risiko jujur

1. **Bisa jadi menyebalkan.** Empat tekanan sekaligus itu banyak. Karena itu
   G1-G6 bertahap — berhenti kapan saja bila sudah terasa cukup tegang.
2. **Kehilangan muatan itu menyakitkan.** Kalau terlalu pahit, turunkan ke 25%
   atau hanya bijih (bukan quest item). **Item quest tak boleh hilang** —
   kalau tidak, quest bisa macet permanen (kita sudah pernah kena bug itu).
3. **Save lama.** Semua field baru harus punya default aman (pola yang sudah
   kita pakai di S1-S10).
4. **Belum ada yang diuji dengan bermain.** Semua angka di atas adalah tebakan
   terdidik, bukan hasil playtest.

---

## 7. Keputusan yang kubutuhkan darimu

1. **Sekeras apa?** (a) Tegang tapi ramah · (b) Betul-betul menghukum
2. **Kehilangan muatan** saat pingsan: ya / hanya bijih / tidak sama sekali
3. **Mulai dari tahap mana?** Rekomendasiku **G1 → G3** dulu (tas + jam pasir):
   itu sudah mengubah rasa permainan, dan paling sedikit risikonya.
