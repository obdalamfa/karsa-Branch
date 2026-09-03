# RESEP — perintah tetap untuk tiap potongan

Satu potongan dinilai dari SATU perintah tangkap. Perintahnya dikunci di sini
supaya ronde 1 dan ronde 5 memotret hal yang sama; kalau pembangun boleh
memilih sudutnya sendiri tiap ronde, "membaik" jadi tidak bisa dibedakan dari
"mencari sudut yang lebih ramah".

Semua dijalankan dari akar worktree. Semua menulis ke `_bench/shots/`.

## Gerbang wajib

Sebelum ronde pertama, dan sesudah tiap potongan:

```
python tools/bar_gate.py check          # harus TERBUKA
python tools/regress.py                 # harus 14/14, 0 gagal
```

`xvfb-run` tidak ada di Windows. `python tools/regress.py` adalah jalur yang
setara di mesin ini — ia membuka jendela sungguhan, bukan buffer kosong.

## Potongan tampilan (satu frame)

| Potongan | Patokan | Perintah |
|---|---|---|
| WAJAH | `character_closeup` | `python tools/capture.py --scene town --out _bench/shots/WAJAH.png --frames 90 --width 1920 --height 1080 --dist 5 --pitch 10 --yaw 180` |
| WARGA | `character_midshot` | `python tools/capture.py --scene town --out _bench/shots/WARGA.png --frames 90 --width 1920 --height 1080 --dist 11 --pitch 22 --yaw 180` |
| HUD | `hud_default` | `python tools/capture.py --scene farm --out _bench/shots/HUD.png --frames 90 --width 1920 --height 1080` |

`--yaw 180` memutar kamera ke DEPAN pemain. Tanpa itu tiap tangkapan layar
kita memperlihatkan punggung, sementara patokannya memperlihatkan wajah — dan
"apakah wajah terbaca sebagai wajah" tidak bisa dijawab dari tengkuk.

HUD ditangkap pada 1920x1080 karena tata letaknya memang dirancang untuk ukuran
itu; pada ukuran lain ia terpotong dan yang dinilai jadi bug ukuran, bukan
desain.

## Potongan gerak (strip 6 ubin)

Strip kita HARUS 6 ubin, sama dengan strip patokan yang dibuat
`tools/klip.py ambil --n 6`. Kalau jumlah ubin berbeda, kritikus bisa menebak
mana yang mana dari bentuknya saja dan "buta" batal.

| Potongan | Patokan | Perintah |
|---|---|---|
| BERKUDA | `gerak_berkuda` | `python tools/capture.py --scene farm --at 20,7 --dist 5.5 --pitch 17 --out _bench/shots/BERKUDA.png --strip 6 --strip-every 7 --hold w --frames 50 --width 960 --height 540 --gif _bench/shots/BERKUDA.gif --aksi naik --target kuda_pegasus` |

BERKUDA TANPA `--yaw`: patokannya kamera dari BELAKANG penunggang, dan itu
kebetulan sudut default permainan. Menambahkan `--yaw` memutar kamera ke depan
sehingga yang terlihat wajah penunggang, bukan punggungnya seperti di patokan.
| PANEN | `gerak_panen` | `python tools/capture.py --scene farm --at <petak ladang> --dist 6 --pitch 18 --yaw 200 --out _bench/shots/PANEN.png --strip 6 --strip-every 3 --frames 50 --width 960 --height 540 --gif _bench/shots/PANEN.gif --keys space` |
| GOSOK | `gerak_gosok` | `python tools/capture.py --scene farm --at 20,6 --dist 4.5 --pitch 11 --yaw 150 --out _bench/shots/GOSOK.png --strip 6 --strip-every 3 --frames 50 --width 960 --height 540 --gif _bench/shots/GOSOK.gif --aksi gosok --target kuda_pegasus` |
| BICARA | `gerak_bicara` | `python tools/capture.py --scene town --at <dekat NPC> --dist 6 --pitch 14 --yaw 200 --out _bench/shots/BICARA.png --strip 6 --strip-every 5 --frames 50 --width 960 --height 540 --gif _bench/shots/BICARA.gif --aksi bicara --target <npc_id>` |

Ubin 960x540 supaya sama dengan `tools/klip.py` (`UBIN_W/UBIN_H`).

**Aksinya harus benar-benar berjalan.** Strip yang keenam ubinnya identik
bukan bukti animasi — ia bukti aksinya tidak pernah terpicu. Periksa sendiri
sebelum menyerahkan: kalau ubinnya sama semua, yang rusak adalah pemicunya,
bukan animasinya.

## Menyusun lembar buta

Dijalankan ORKESTRATOR, bukan pembangun dan bukan kritikus:

```
python tools/bar_gate.py pair --ours _bench/shots/<ID>.png --ref <slug> \
    --out _bench/sheets/<ID>_r<N>.png --key <di luar repo>/key_<ID>_r<N>.json
# strip gerak pakai --tegak
python tools/bar_gate.py reveal --key <...> --pilih <A|B>
```

Kunci ditulis di luar `_bench/` supaya kritikus yang menjelajah direktori tidak
bisa menemukannya secara tidak sengaja.

## `--aksi` — kenapa ada

`gosok` dan `bicara` bukan tombol; keduanya pilihan di dalam pie menu. Dari
baris perintah keduanya tadinya tidak bisa difoto sama sekali, dan BRIEF-nya
sendiri menulis: fitur yang tidak bisa difoto kritikus itu tidak ada.
`--aksi <nama> --target <id>` memanggil `execute_pie_action` — jalur yang SAMA
dengan yang dipanggil pie menu, bukan pintu belakang yang melewati logikanya.
Kalau aksinya melempar, capture BERISIK dan keluar dengan kode 2, karena aksi
yang gagal diam-diam menghasilkan strip beku dan strip beku terbaca sebagai
"animasinya belum ada".

Terbukti jalan (dipakai untuk membuat garis dasar):
`--scene farm --at 20,6 --dist 7 --pitch 16 --yaw 200 --aksi gosok --target kuda_pegasus`

## BERKUDA belum ada sama sekali

Menaiki kuda BUKAN fitur yang perlu diperhalus — ia belum ada. Yang sudah ada:

- `kuda_pegasus` sudah muncul di scene `farm` pada petak (20, 5) — lihat
  `game/data.py` (`'kuda_pegasus': [(0, 20, 5, 'farm', 'grazing')]`).
- Modelnya ada: `_kuda()` di `game/animal_models.py`.
- Aksi pie-menu untuk hewan sudah ada (`gosok`, `beri_makan`, ...) di
  `game/controllers/interaction_controller.py` (`build_pie_options`,
  `execute_pie_action`).

Yang belum ada: naik, turun, dan bergerak SEBAGAI penunggang.

Tambahkan aksi `naik` ke jalur pie-menu yang sudah ada — bukan tombol baru dan
bukan jalur khusus harness — supaya `--aksi naik --target kuda_pegasus` menempuh
kode yang sama dengan yang ditempuh pemain. Saat menunggang, tombol WASD harus
menggerakkan kuda beserta penunggangnya, dan kamera harus tetap mengikuti.

Patokannya (`_bench/refs/gerak_berkuda.png`) adalah kamera orang-ketiga dari
BELAKANG — sudut yang sama dengan kamera permainan kita. Yang terlihat di sana:
penunggang duduk di pelana dengan badan ikut naik-turun mengikuti langkah kuda,
kaki kuda mengayun, dan dunia mengalir lewat dengan mantap. Yang akan langsung
ketahuan kalau salah: penunggang yang MENEMPEL kaku di punggung kuda, dan kuda
yang meluncur tanpa kakinya bergerak.

## Aksi yang DITOLAK terlihat persis seperti animasi yang belum dibuat

`execute_pie_action` tidak melempar saat aksinya ditolak — ia menampilkan
pesan lalu return biasa. Selama beberapa ronde harness memotret penolakan itu
dan menghasilkan strip enam-ubin-identik, yang lalu terbaca sebagai "animasi
menggosok belum ada". Diukur: GOSOK 0,0% gerak sementara `CAPTURE_AKSI`
melaporkan sukses.

`capture.py` sekarang memeriksa EFEKNYA, bukan kembalinya fungsi: kalau
`player._attack_anim` tidak menjadi > 0 sesudah aksi dipanggil, ia keluar
dengan CAPTURE_FAIL dan kode 2.

Kalau kamu melihat strip beku, urutan memeriksanya:
1. Apakah `CAPTURE_FAIL` muncul? Berarti aksinya ditolak, bukan hilang.
2. Apakah avatarnya TSO? Pivot prosedural (`_pivot_shoulder_r`) TIDAK
   menggerakkan avatar TSO sama sekali — petakan modenya ke klip TSO di
   `_KLIP_TSO` (game/player.py).
3. Apakah kameranya masih membingkai yang dinilai? Tata letak scene berubah
   seiring pekerjaan; resep yang basi memotret pagar, bukan hewan.
