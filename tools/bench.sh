#!/usr/bin/env bash
# bench.sh — perbarui Karsa Bench dengan satu perintah.
#
# Halaman progres cuma berguna kalau memperbaruinya lebih murah daripada
# mengabaikannya. Sebelum ini butuh tiga perintah dan mengingat urutannya:
# ambil tangkapan layar tiap potongan, jalankan regresi, lalu bangun halaman.
# Yang butuh diingat akan lupa dijalankan, dan halaman yang basi lebih buruk
# daripada tidak ada halaman — ia terlihat seperti keadaan sekarang.
#
#   bash tools/bench.sh          tangkapan + regresi + halaman
#   bash tools/bench.sh --cepat  lewati regresi (tangkapan + halaman saja)
#
# Sesudahnya: publish _bench/progress.html sebagai Artifact ke URL yang sama.
set -uo pipefail
cd "$(dirname "$0")/.."

CEPAT=0
[[ "${1:-}" == "--cepat" ]] && CEPAT=1

# id | scene | jam | argumen kamera tambahan
# Sengaja sejajar dengan _bench/slices.json: id di sini HARUS sama dengan id
# potongannya, karena progress_page.py mencocokkan shots/<id>*.png dengan
# potongan lewat nama berkas.
POTONGAN=(
  "TANAH|farm|10|"
  "DEKAT|farm|10|--dist 6 --pitch 18"
  "HUD|farm|10|"
  "WAJAH|farm|9|--dist 7 --pitch 15"
  "WARGA|farm|9|--dist 12 --pitch 25"
  "DESA|town|13|--dist 26 --pitch 40"
  "KANDANG|house|11|--dist 11 --pitch 28"
  "SENJA|farm|18|"
)

mkdir -p _bench/shots
echo "== tangkapan layar per potongan =="
gagal=0
for baris in "${POTONGAN[@]}"; do
  IFS='|' read -r id scene jam ekstra <<< "$baris"
  # shellcheck disable=SC2086
  if xvfb-run -a python tools/capture.py --out "_bench/shots/${id}.png" \
       --scene "$scene" --hour "$jam" --frames 60 $ekstra >/dev/null 2>&1; then
    printf '  OK      %-8s %s jam %s\n' "$id" "$scene" "$jam"
  else
    printf '  GAGAL   %-8s %s jam %s\n' "$id" "$scene" "$jam"
    gagal=$((gagal + 1))
  fi
done

if [[ $CEPAT -eq 0 ]]; then
  echo
  echo "== regresi =="
  xvfb-run -a python tools/regress.py 2>&1 | tail -6
fi

echo
echo "== gerbang patokan =="
python tools/bar_gate.py check 2>&1 | tail -4

echo
echo "== halaman =="
python tools/progress_page.py

if [[ $gagal -gt 0 ]]; then
  echo
  echo "PERINGATAN: $gagal tangkapan gagal — halaman memakai yang lama untuk itu."
  exit 1
fi
