"""layout.py — Alat gambar peta ubin.

Kenapa ada: tiap scene sebelumnya menulis `for y in range(...): for x in ...`
sendiri-sendiri. Akibatnya bentuk zona hanya terlihat kalau kode dijalankan,
dan tidak ada satu pun rancangan yang bisa dibaca dari kodenya. Padahal
`docs/TATA_LETAK.md` P3 menuntut zona berupa persegi utuh — itu hal yang harus
kelihatan di sumbernya, bukan cuma di layar.

Semua fungsi di sini menulis LANGSUNG ke matriks `m[y][x]` dan aman terhadap
tepi peta (indeks di luar batas diabaikan, bukan melempar). Sengaja: peta
dirancang dengan menumpuk bentuk, dan bentuk yang sedikit menjorok keluar
adalah hal biasa saat menyetel.

Konvensi koordinat di seluruh proyek: `m[y][x]`, x ke timur, y ke selatan.
"""


def blank(w, h, fill):
    """Matriks w x h berisi satu ubin."""
    return [[fill] * w for _ in range(h)]


def _ok(m, x, y):
    return 0 <= y < len(m) and 0 <= x < len(m[0])


def put(m, x, y, tid):
    if _ok(m, x, y):
        m[y][x] = tid


def rect(m, x0, y0, x1, y1, tid):
    """Isi persegi panjang PADAT, inklusif di kedua ujung.

    Inklusif, bukan setengah terbuka: rancangan peta ditulis sebagai "dari
    ubin 8 sampai ubin 23", dan menerjemahkannya jadi range(8, 24) tiap kali
    adalah sumber salah-satu-ubin yang tidak ada gunanya.
    """
    for y in range(min(y0, y1), max(y0, y1) + 1):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            put(m, x, y, tid)


def outline(m, x0, y0, x1, y1, tid):
    """Isi hanya KELILING persegi panjang. Dipakai untuk pagar kandang.

    Pagar harus mengelilingi sesuatu (TATA_LETAK P5 daftar-periksa); menggambar
    kelilingnya sebagai satu operasi membuat itu tidak mungkin salah.
    """
    xa, xb = min(x0, x1), max(x0, x1)
    ya, yb = min(y0, y1), max(y0, y1)
    for x in range(xa, xb + 1):
        put(m, x, ya, tid)
        put(m, x, yb, tid)
    for y in range(ya, yb + 1):
        put(m, xa, y, tid)
        put(m, xb, y, tid)


def border(m, tid):
    """Pagari seluruh tepi peta. Batas peta harus terbaca sebagai batas."""
    h, w = len(m), len(m[0])
    outline(m, 0, 0, w - 1, h - 1, tid)


def hline(m, x0, x1, y, tid, thick=1):
    """Jalan mendatar. `thick` menambah baris ke SELATAN.

    Jalan utama selalu dua ubin (thick=2): dari pitch 34 sebuah jalan satu ubin
    terbaca sebagai garis, bukan sebagai jalan yang bisa dilalui.
    """
    for dy in range(thick):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            put(m, x, y + dy, tid)


def vline(m, x, y0, y1, tid, thick=1):
    """Jalan tegak. `thick` menambah kolom ke TIMUR."""
    for dx in range(thick):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            put(m, x + dx, y, tid)


def scatter(m, spots, tid):
    """Taruh satu jenis ubin di daftar titik yang DIPILIH TANGAN.

    Sengaja tidak ada versi acak. Taburan acak (`rng.random() < 0.2`) adalah
    cara peta lama membuat hutan, dan hasilnya adalah derau merata yang tidak
    menunjukkan apa pun serta memakan 5 entity per pohon. Kalau sebuah pohon
    layak ada, ia layak dipilih tempatnya.
    """
    for x, y in spots:
        put(m, x, y, tid)


def belt(m, x0, y0, x1, y1, tid, step=2, phase=0):
    """Isi persegi panjang secara berselang — untuk barisan pohon / kebun buah.

    Pohon rapat berjajar terbaca sebagai hutan; pohon berselang terbaca sebagai
    kebun yang ditanam orang. `step=2` memberi satu ubin bersih di antara tiap
    pohon, memenuhi READABILITY §4.3 ("≥ 1 ubin bersih di sekitar tiap objek
    yang bisa dipakai") tanpa perlu menghitung manual.
    """
    n = 0
    for y in range(min(y0, y1), max(y0, y1) + 1):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            if (x + y + phase) % step == 0:
                put(m, x, y, tid)
                n += 1
    return n


def count(m, tid):
    return sum(row.count(tid) for row in m)


def census(m):
    """Sebaran ubin — dipakai laporan dan probe ongkos."""
    out = {}
    for row in m:
        for t in row:
            out[t] = out.get(t, 0) + 1
    return out
