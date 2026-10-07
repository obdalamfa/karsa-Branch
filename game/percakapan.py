"""percakapan.py — Pembuka percakapan yang tahu JAM, TEMPAT, dan KEGIATAN.

Dialog lama memilih satu baris dari `talks` menurut hati dan tahap quest
saja: Sari mengucapkan "Halo nak, mau beli benih?" pukul 22:00 di alun-alun
sama persis seperti pukul 08:00 di balik meja warungnya. Di sini satu kalimat
pembuka dipilih dari keadaan saat itu dan DISISIPKAN sebelum baris hati/quest
yang sudah ada -- tidak ada cerita lama yang hilang.

Urutan prioritas (yang paling khusus menang):
  1. kegiatan jadwal  (sedang memancing, menempa, tidur, ...)
  2. tempat           (ditemui di luar tempat biasanya)
  3. cuaca hujan/badai
  4. waktu            (pagi, siang, sore, malam, larut)

Pilihan di dalam satu kelompok diputar menurut hari + jumlah obrolan, jadi
dua obrolan berturut-turut tidak mengulang kalimat yang sama.
"""
from __future__ import annotations


def waktu(jam: int) -> str:
    if 5 <= jam < 10:
        return 'pagi'
    if 10 <= jam < 15:
        return 'siang'
    if 15 <= jam < 18:
        return 'sore'
    if 18 <= jam < 23:
        return 'malam'
    return 'larut'


# Tempat biasa tiap warga: di sana komentar "tempat" tidak dipakai, karena
# berdiri di warungnya sendiri bukan hal yang perlu dikomentari.
TEMPAT_KERJA = {
    'sari': 'shop', 'raka': 'clinic', 'maya': 'studio', 'budi': 'smith',
    'joko': 'lake', 'ningsih': 'farm', 'pak_guru': 'town', 'mbok_jum': 'town',
    'arya': 'farm', 'cici': 'farm', 'bowo': 'farm', 'jaka_ronda': 'town',
    'kapten_kuro': 'beach', 'kru_kuro': 'beach',
}

NAMA_TEMPAT = {
    'farm': 'kebun', 'town': 'alun-alun', 'lake': 'danau', 'beach': 'pantai',
    'mountain': 'lereng gunung', 'cemetery': 'kuburan', 'shop': 'warung',
    'clinic': 'klinik', 'studio': 'studio', 'smith': 'bengkel',
    'greenhouse': 'rumah kaca', 'house': 'rumahmu', 'naga_cave': 'gua',
    'swarga': 'swarga',
}

P = {
    'sari': {
        'pagi':  ["Pagi, Nak! Benih baru saja datang, masih segar.",
                  "Embunnya tebal hari ini. Bagus buat tanam sayur daun."],
        'siang': ["Siang begini warung paling ramai. Mau titip apa?",
                  "Panas, ya? Duduk sebentar, ada es teh di belakang."],
        'sore':  ["Sore, Nak. Sebentar lagi Ibu tutup, cepat pilih."],
        'malam': ["Lho, malam-malam masih keluyuran? Hati-hati di jalan."],
        'larut': ["Ibu sudah mau tidur, Nak... besok pagi saja, ya."],
        'hujan': ["Hujan begini benih jadi murah. Petani pada di rumah."],
        'tempat': {'town': "Ibu cari angin di alun-alun. Seharian di warung bikin pegal."},
        'kegiatan': {'preparing': "Pagi-pagi Ibu harus menata rak dulu. Sebentar, ya.",
                     'walking': "Ibu jalan-jalan sore, lihat-lihat dagangan orang."},
    },
    'raka': {
        'pagi':  ["Pagi. Sudah sarapan? Jangan bertani dengan perut kosong."],
        'siang': ["Matahari sedang tinggi. Banyak minum air, ya."],
        'sore':  ["Sore. Pasien hari ini sedikit, syukurlah."],
        'malam': ["Malam. Kalau badanmu pegal, istirahat. Itu resep paling murah."],
        'larut': ["Kau belum tidur? Kurang tidur itu musuh petani."],
        'hujan': ["Hujan begini banyak yang masuk angin. Pakai baju hangat."],
        'tempat': {'town': "Saya jalan sebentar. Dokter juga perlu udara segar."},
        'kegiatan': {'working': "Sebentar, saya sedang mencatat rekam medis.",
                     'reading': "Saya sedang membaca jurnal. Ada penyakit tanaman baru di kota."},
    },
    'maya': {
        'pagi':  ["Cahaya pagi ini... lihat bayangannya, panjang sekali."],
        'siang': ["Siang terlalu terang. Warna jadi datar."],
        'sore':  ["Jam emas! Semua jadi oranye. Aku suka sore."],
        'malam': ["Malam punya warnanya sendiri. Biru tua, hampir ungu."],
        'larut': ["Inspirasi datang di jam aneh. Aku belum mau tidur."],
        'hujan': ["Hujan membuat lembah seperti cat air yang luntur."],
        'tempat': {'mountain': "Dari lereng ini seluruh lembah kelihatan. Aku sedang membuat sketsa."},
        'kegiatan': {'painting': "Jangan goyang meja! Catnya belum kering.",
                     'sketching': "Diam sebentar... ya, pose itu. Boleh kugambar?"},
    },
    'budi': {
        'pagi':  ["Pagi! Tungku baru kunyalakan, besi belum merah."],
        'siang': ["Panasnya dobel di sini. Matahari plus bara."],
        'sore':  ["Sore. Satu cangkul lagi, lalu aku istirahat."],
        'malam': ["Malam. Kopi dan cerita, itu jatahku sesudah kerja."],
        'larut': ["Mataku sudah berat. Besok saja kalau mau pesan alat."],
        'hujan': ["Hujan bagus buat menempa. Bengkel tidak terlalu panas."],
        'tempat': {'town': "Aku ke sini cari minum. Jangan bilang Mbok Jum aku kemari lagi."},
        'kegiatan': {'forging': "Mundur sedikit! Percikannya bisa kena bajumu.",
                     'drinking': "Duduk, duduk! Satu gelas wedang jahe untukmu."},
    },
    'joko': {
        'pagi':  ["Ssst... ikan paling lapar di pagi buta."],
        'siang': ["Siang begini ikan sembunyi di dasar. Sabar saja."],
        'sore':  ["Sore enak. Angin dari danau sejuk."],
        'malam': ["Ikan lele keluar malam-malam. Itu targetku."],
        'larut': ["Kau mau ikut begadang di pinggir danau?"],
        'hujan': ["Hujan rintik itu berkah. Ikan naik ke permukaan."],
        'tempat': {'shop': "Umpan habis, jadi aku belanja ke Bu Sari."},
        'kegiatan': {'fishing': "Jangan berisik, pelampungnya baru bergerak!",
                     'shopping': "Kail nomor tujuh... ah, kosong lagi."},
    },
    'ningsih': {
        'pagi':  ["Pagi! Sayuran di rumah kaca minta disiram duluan."],
        'siang': ["Anak-anak belum pulang. Rumah sepi, enak buat kerja."],
        'sore':  ["Sore, sebentar lagi masak. Cici pasti kelaparan."],
        'malam': ["Malam. Anak-anak susah disuruh tidur, pusing aku."],
        'larut': ["Akhirnya semua tidur. Ini jam satu-satunya buat aku sendiri."],
        'hujan': ["Hujan! Untung jemuran sudah kuangkat."],
        'tempat': {'town': "Aku ke alun-alun mau ngobrol sama ibu-ibu. Kabar apa hari ini?"},
        'kegiatan': {'cooking': "Aku lagi masak sayur bening. Mau mampir makan?",
                     'gossiping': "Eh, kau dengar? Katanya ada cahaya aneh di gunung semalam."},
    },
    'pak_guru': {
        'pagi':  ["Selamat pagi. Pagi adalah waktu terbaik untuk belajar."],
        'siang': ["Selamat siang. Anak-anak baru selesai pelajaran berhitung."],
        'sore':  ["Selamat sore. Buku apa yang sedang kau baca?"],
        'malam': ["Selamat malam. Lampu minyakku tinggal sedikit."],
        'larut': ["Sudah larut. Belajar terlalu malam tidak baik."],
        'hujan': ["Hujan. Waktu yang tepat untuk membaca, bukan?"],
        'tempat': {},
        'kegiatan': {'teaching': "Maaf, saya sedang mengajar. Duduklah di belakang kalau mau ikut.",
                     'reading': "Ini catatan sejarah lembah. Ada nama pamanmu di sini."},
    },
    'mbok_jum': {
        'pagi':  ["Pagi, Le. Lodeh sudah matang, mau sepiring?"],
        'siang': ["Siang begini warung Mbok penuh tukang."],
        'sore':  ["Sore. Mbok ingat sore-sore dulu di lembah ini..."],
        'malam': ["Malam, Le. Jangan dekat-dekat kuburan kalau sudah gelap."],
        'larut': ["Mbok sudah tua, jam segini mata tidak mau melek."],
        'hujan': ["Hujan begini enaknya wedang jahe sama singkong rebus."],
        'tempat': {},
        'kegiatan': {'cooking': "Jangan ganggu Mbok, santannya bisa pecah.",
                     'serving': "Ayo duduk, Le. Mbok ambilkan nasi."},
    },
    'arya': {
        'pagi':  ["Pagi! Hutan utara paling sejuk jam segini."],
        'siang': ["Siang. Rusa-rusa sedang berteduh, hutan sepi."],
        'sore':  ["Sore. Burung-burung pulang ke sarang."],
        'malam': ["Malam di hutan itu bukan untuk orang baru. Percayalah."],
        'larut': ["Kau juga tidak bisa tidur? Hutan ribut malam ini."],
        'hujan': ["Hujan menghapus jejak binatang. Hari buruk buat berburu."],
        'tempat': {'town': "Aku ke kota cuma kalau terpaksa. Terlalu ramai."},
        'kegiatan': {'walking': "Aku sedang memeriksa pagar. Ada babi hutan yang suka merusak.",
                     'resting': "Istirahat dulu. Kaki ini sudah keliling lembah seharian."},
    },
    'cici': {
        'pagi':  ["Pagiii! Aku bangun duluan dari Bowo!"],
        'siang': ["Main yuk! Aku tahu tempat capung yang banyak!"],
        'sore':  ["Sebentar lagi Mama panggil pulang..."],
        'malam': ["Kata Mama anak kecil tidak boleh keluar malam. Ssst!"],
        'larut': ["Hoaaam... aku mimpi naga tadi."],
        'hujan': ["Hujan! Ayo main lompat genangan!"],
        'tempat': {'town': "Aku jalan-jalan sendiri ke kota! Jangan bilang Mama, ya."},
        'kegiatan': {'playing': "Aku lagi kejar kupu-kupu! Itu, itu, yang kuning!"},
    },
    'bowo': {
        'pagi':  ["Pagi, Kak! Aku bantu siram tanaman, ya?"],
        'siang': ["Kak, cangkulnya berat tidak? Aku mau coba!"],
        'sore':  ["Kak, kapan tomatku panen?"],
        'malam': ["Aku belum ngantuk. Ceritakan soal kota dong, Kak."],
        'larut': ["Aku pura-pura tidur biar Mama tidak marah."],
        'hujan': ["Hujan! Tanamanku tidak usah disiram hari ini, kan?"],
        'tempat': {'town': "Aku sekolah di sini! Pak Hadi galak tapi baik."},
        'kegiatan': {'helping': "Lihat, Kak! Barisanku lurus, kan?",
                     'school': "Tadi aku dapat nilai sembilan berhitung!"},
    },
    'jaka_ronda': {
        'pagi':  ["Pagi... aku baru selesai ronda. Ngantuk sekali."],
        'siang': ["Siang. Biasanya jam segini aku masih tidur."],
        'sore':  ["Sore. Senter sudah kuisi, siap jaga malam."],
        'malam': ["Malam. Tetap di jalan yang terang, ya."],
        'larut': ["Ssst. Barusan aku dengar suara dari arah kuburan."],
        'hujan': ["Ronda sambil hujan-hujanan... nasib."],
        'tempat': {},
        'kegiatan': {'patroling': "Siapa di sana?! Oh, kau. Bikin kaget saja."},
    },
    'kapten_kuro': {
        'pagi':  ["Pagi, pelaut darat! Angin timur bagus untuk berlayar."],
        'siang': ["Matahari di atas tiang! Waktunya awak makan."],
        'sore':  ["Laut sore itu jujur. Ia menunjukkan badai yang akan datang."],
        'malam': ["Bintang-bintang adalah peta. Kau bisa membacanya?"],
        'larut': ["Kapten tidak tidur sebelum kapalnya aman."],
        'hujan': ["Hah! Ini cuma gerimis bagi orang yang pernah melewati topan."],
        'tempat': {},
        'kegiatan': {'jaga_kapal': "Tetap di dermaga. Kapalku tidak menerima tamu sembarangan.",
                     'inspeksi': "Tali ini sudah aus. Siapa yang bertugas kemarin?!"},
    },
    'kru_kuro': {
        'pagi':  ["Pagi! Geladak harus kinclong sebelum Kapten bangun."],
        'siang': ["Akhirnya jam makan! Perutku sudah konser dari tadi."],
        'sore':  ["Sore. Barang dari kota belum diangkut semua."],
        'malam': ["Malam, kawan. Mau dengar lagu pelaut?"],
        'larut': ["Jangan bilang Kapten aku tidur di geladak."],
        'hujan': ["Hujan, berarti geladak tidak perlu dipel. Hehe."],
        'tempat': {},
        'kegiatan': {'bersih_bersih': "Awas licin! Baru kupel.",
                     'angkat_barang': "Bantu angkat peti ini, dong. Berat!"},
    },
}

UMUM = {
    'pagi': "Pagi.", 'siang': "Siang.", 'sore': "Sore.", 'malam': "Malam.", 'larut': "Sudah larut...",
}


def pembuka(npc_id: str, state) -> str | None:
    """Satu kalimat pembuka sesuai keadaan sekarang, atau None."""
    data = P.get(npc_id)
    if data is None:
        return None
    jam = state.get_hour()
    pos = state.npc_positions.get(npc_id, {})
    scene = pos.get('scene') or getattr(state, 'scene_name', '')
    kegiatan = pos.get('activity', '')
    hujan = getattr(state, 'weather', '') in ('Hujan', 'Badai')
    w = waktu(jam)

    pilihan = None
    if kegiatan and kegiatan in data.get('kegiatan', {}):
        pilihan = [data['kegiatan'][kegiatan]]
    elif scene != TEMPAT_KERJA.get(npc_id) and scene in data.get('tempat', {}):
        pilihan = [data['tempat'][scene]]
    elif hujan and data.get('hujan'):
        pilihan = data['hujan']
    else:
        pilihan = data.get(w) or [UMUM[w]]
    n = getattr(state, 'day', 0) + state.npc_dialog_index.get(npc_id, 0)
    return pilihan[n % len(pilihan)]
