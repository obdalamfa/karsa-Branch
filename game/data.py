"""
data.py — Tanaman, 31 NPC, dialog, schedule, quest, dungeon, combat, crafting.
Identik dengan v17 — tidak ada perubahan (pure data, bebas dari rendering).
"""

# 'days' = umur yang harus dicapai sebelum bisa dipanen. Satu malam yang
# disiram menambah 2 umur kalau musimnya cocok, 1 kalau tidak — jadi jumlah
# penyiraman yang dibutuhkan (N) adalah ceil(days/2) di musimnya sendiri.
# Energi satu siklus penuh = cangkul 2 + tanam 2 + siram N + panen 2 = 6+N.
# Harga jual disusun supaya (sell-cost)/(6+N) jatuh di pita 3,0-5,7 G/energi;
# lihat docs/EKONOMI.md untuk perhitungan tiap baris.
# Dua angka diubah dari versi lama: lobak 22->26 (dulu 2,4 G/EN, tidak pernah
# layak ditanam lagi setelah hari kedua) dan labu 70->66 (dulu 6,1 G/EN,
# mendominasi semua tanaman lain).
CROPS = {
    'lobak':    {'name':'Lobak','days':2,'sell':26,'cost':5,'seasons':['Semi']},
    'wortel':   {'name':'Wortel','days':3,'sell':35,'cost':8,'seasons':['Semi','Gugur']},
    'stroberi': {'name':'Stroberi','days':4,'sell':55,'cost':12,'seasons':['Semi']},
    'jagung':   {'name':'Jagung','days':4,'sell':48,'cost':10,'seasons':['Panas']},
    'tomat':    {'name':'Tomat','days':5,'sell':65,'cost':14,'seasons':['Panas']},
    'labu':     {'name':'Labu','days':5,'sell':66,'cost':15,'seasons':['Gugur']},
    'bayam':    {'name':'Bayam','days':2,'sell':30,'cost':7,'seasons':['Dingin']},
    'jamur':    {'name':'Jamur','days':3,'sell':55,'cost':12,'seasons':['Dingin']},
}

# ─── CONSUMABLES (python-2d-game buff_effects.py pattern) ────────────────────
# Registry: item_name → {heal_hp, heal_energy, buff, buff_ms, desc}
# Tiga phase lifecycle buff: start (apply), middle (tick), end (revert)
CONSUMABLES = {
    'lobak':     {'heal_hp': 8,  'heal_energy': 5,  'desc': '+8 HP, +5 EN'},
    'wortel':    {'heal_hp': 14, 'heal_energy': 8,  'desc': '+14 HP, +8 EN'},
    'stroberi':  {'heal_hp': 20, 'heal_energy': 12, 'desc': '+20 HP, +12 EN'},
    'jagung':    {'heal_hp': 10, 'heal_energy': 20, 'desc': '+10 HP, +20 EN'},
    'tomat':     {'heal_hp': 16, 'heal_energy': 10, 'desc': '+16 HP, +10 EN'},
    'labu':      {'heal_hp': 28, 'heal_energy': 18, 'desc': '+28 HP, +18 EN'},
    'bayam':     {'heal_hp': 10, 'heal_energy': 28, 'desc': '+10 HP, +28 EN'},
    'jamur':     {'heal_hp': 25, 'heal_energy': 15, 'desc': '+25 HP, +15 EN'},
    # Wild items: efek buff tambahan (start-effect + middle-effect)
    'wild_herb': {'heal_hp': 18, 'heal_energy': 10,
                  'buff': 'regen', 'buff_ms': 12000,
                  'desc': '+18 HP +10 EN, Regen 12 detik'},
    'wild_berry':{'heal_hp': 12, 'heal_energy': 8,
                  'desc': '+12 HP, +8 EN'},
    'mandrake':  {'heal_hp': 60, 'heal_energy': 40,
                  'buff': 'strength', 'buff_ms': 20000,
                  'desc': '+60 HP, +40 EN, Kuat 20 detik!'},
}

WILD_ITEMS = {
    'mandrake':         {'name':'Mandrake','sell':80,'description':'Akar ajaib','dangerous':True},
    'running_mushroom': {'name':'Jamur Lari','sell':45,'description':'Berlari saat didekati'},
    'firefly':          {'name':'Kunang-kunang','sell':25,'description':'Hanya muncul malam'},
    'wild_herb':        {'name':'Herba Liar','sell':15,'description':'Tanaman obat hutan'},
    'wild_berry':       {'name':'Beri Liar','sell':20,'description':'Beri manis'},
    'air_keabadian':    {'name':'Air Keabadian','sell':500,'description':'Air ruqyah dari naga'},
    'ikan_legendaris':  {'name':'Ikan Legendaris','sell':1000,'description':'Ikan raksasa penghuni danau terdalam'},
}

HUMAN_NPCS = {
    'arya':       {'name':'Arya','type':'human','gift':'jagung',
        'talks':{
            'default': [["Pagi! Hutan utara selalu sejuk."],["Cek tanamanmu, kawan."]],
            'hearts_3': [["Kebun ini dulu milik sahabatku. Dia... sudah pergi."]],
            'hearts_5': [["Paman Arsa pernah bilang ada 'perjanjian' yang harus dijaga. Aku pikir dia bercanda waktu itu."]],
            'hearts_7': [["Dia bilang padaku, 'Arya, kalau ada orang baru datang ke kebun, jaga dia.' Sekarang aku mengerti kenapa."]],
            'hearts_10': [["Kau sudah melakukan apa yang kami tidak bisa. Terima kasih, kawan."]],
            'quest_5': [["Kau mau masuk gua itu? Aku pernah ikut Paman Arsa ke level 3... tapi aku terlalu takut melanjutkan."]],
            'quest_10': [["Kau berhasil sampai ke Naga? Aku tahu kau bisa."]],
            'quest_11': [["Lembah hidup lagi. Cahaya dari gunung... aku bisa merasakannya."]],
        },
        'gift_r':"Wah, makasih!"},
    'sari':       {'name':'Bu Sari','type':'human','gift':'tomat',
        'talks':{
            'default': [["Halo nak, mau beli benih?"],["Mampir ke warung."]],
            'hearts_3': [["Dulu warung ini ramai, nak. Sekarang... ya begini. Tanah semakin tidak subur."]],
            'hearts_5': [["Paman Arsa nitip buku ini sebelum pergi. Aku belum berani buka."]],
            'hearts_7': [["Isinya peta gua dan gambar naga. Aku takut, tapi mungkin kau perlu ini."]],
            'hearts_10': [["Lembah hidup lagi. Warungku ramai lagi. Terima kasih, nak."]],
            'quest_11': [["Pelanggan dari desa sebelah mulai datang lagi! Semua berkat kamu."]],
        },
        'gift_r':"Pas untuk masak!"},
    'raka':       {'name':'Pak Raka','type':'human','gift':'wild_herb',
        'talks':{
            'default': [["Jangan terlalu lelah bertani."],["Kesehatanku menurun."]],
            'hearts_3': [["Penyakit di sini aneh. Bukan penyakit biasa. Tanah sendiri yang sakit."]],
            'hearts_5': [["Kakekku bilang, dulu ada mata air dari gunung. Air itu menyembuhkan segalanya."]],
            'hearts_7': [["Kalau air itu mengalir lagi... mungkin aku bisa benar-benar menyembuhkan orang."]],
            'hearts_10': [["Air Keabadian mengalir lagi. Obat-obatanku jadi lebih manjur. Kau pahlawan."]],
            'quest_11': [["Tidak ada lagi penyakit aneh di desa. Tanah sudah sehat kembali."]],
        },
        'gift_r':"Herba bagus."},
    'maya':       {'name':'Maya','type':'human','gift':'stroberi',
        'talks':{
            'default': [["Aku cari inspirasi lukisan."],["Lembah Karsa indah."]],
            'hearts_3': [["Aku bermimpi tentang gua yang bersinar. Aneh, ya? Padahal aku belum pernah ke sana."]],
            'hearts_5': [["Lihat lukisanku ini. Aku gambar dari mimpi. Tapi ini mirip gua di balik gunung, kan?"]],
            'hearts_7': [["Ini peta dari mimpiku. Mungkin bisa membantumu di dalam gua."]],
            'hearts_10': [["Lembah ini akhirnya secantik dalam mimpiku. Lukisanku jadi lebih berwarna."]],
            'quest_11': [["Aku melukis naga yang bersinar emas. Bukan dari mimpi kali ini \u2014 dari kenyataan."]],
        },
        'gift_r':"Warnanya menginspirasi!"},
    'budi':       {'name':'Budi','type':'human','gift':'lobak',
        'talks':{
            'default': [["Besinya panas!"],
                 ["Bawakan mineral, kubuatkan pickaxe atau pedang."],
                 ["Pickaxe kayu: 50G + 5 kayu."],
                 ["Pedang kayu: 80G + 8 kayu untuk lawan mob gua."]],
            'hearts_3': [["Kakekku dulu penambang paling hebat di sini. Tapi dia melakukan kesalahan besar."]],
            'hearts_5': [["Dia mengambil terlalu banyak kristal dari gua. Naga murka. Sejak itu gua tertutup."]],
            'hearts_7': [["Kalau kau masuk ke gua itu, tolong... minta maaf atas nama keluargaku."]],
            'hearts_10': [["Kau memperbaiki apa yang kakekku rusak. Aku berutang padamu seumur hidup."]],
            'quest_5': [["Pakailah pickaxe ini baik-baik. Jangan seperti kakekku \u2014 jangan ambil lebih dari yang kau butuhkan."]],
            'quest_11': [["Aku bisa menempa dengan mithril lagi! Seperti masa keemasan yang diceritakan kakekku."]],
        },
        'gift_r':"Cemilan."},
    'joko':       {'name':'Pak Joko','type':'human','gift':'wild_berry',
        'talks':{
            'default': [["Pagi enak mancing."],["Ikan terbesar..."]],
            'hearts_3': [["Dulu ikan di danau ini berlimpah. Sekarang makin sedikit. Ada yang salah dengan airnya."]],
            'hearts_5': [["Nelayan tua bilang, air danau terhubung ke mata air gunung. Kalau sumbernya sehat, danaunya sehat."]],
            'hearts_10': [["Ikan kembali berlimpah! Air danau jernih lagi. Ini keajaiban."]],
            'quest_11': [["Aku tangkap ikan sebesar lenganku hari ini! Belum pernah seumur hidupku!"]],
        },
        'gift_r':"Mantap!"},
    'cici':       {'name':'Cici','type':'human','gift':'stroberi',
        'talks':{
            'default': [["Hihi, mau main?"],["Mama bilang jangan ke kuburan malam."]],
            'hearts_3': [["Mama bilang jangan ke kuburan malam. Tapi aku lihat cahaya biru di sana..."]],
            'hearts_5': [["Kak, kau pernah lihat yang aneh-aneh di malam hari? Aku pernah lihat bayangan di kebun."]],
            'hearts_10': [["Kak, lembah ini terasa lebih hangat sekarang. Apa yang kau lakukan?"]],
            'quest_11': [["Hihi! Aku mau jadi penjaga lembah kalau sudah besar! Kayak kakak!"]],
        },
        'gift_r':"Yeyy!"},
    'bowo':       {'name':'Bowo','type':'human','gift':'labu',
        'talks':{
            'default': [["Aku mau jadi petani hebat!"],["Cici cerewet."]],
            'hearts_3': [["Aku mau jadi petani yang lebih hebat dari Paman Arsa! Tapi aku belum tahu caranya."]],
            'hearts_5': [["Kak, ajari aku bertani dong. Aku mau kebunku sendiri suatu hari."]],
            'hearts_10': [["Aku sudah bisa menanam sendiri! Lihat lobakku! Terima kasih sudah mengajariku."]],
            'quest_11': [["Kalau besar nanti, aku mau menjaga kebun ini. Janji!"]],
        },
        'gift_r':"Untuk halloween!"},
    'ningsih':    {'name':'Bu Ningsih','type':'human','gift':'bayam',
        'talks':{
            'default': [["Anak-anak bikin pusing."],["Sisakan sayuran."]],
            'hearts_3': [["Anak-anak susah makan sayur. Padahal sayuran di sini dulu enak sekali."]],
            'hearts_5': [["Tanah berubah, rasa sayuran juga berubah. Seolah lembah kehilangan sesuatu."]],
            'hearts_10': [["Rasa sayurannya kembali seperti dulu! Anak-anak mau makan sayur lagi!"]],
            'quest_11': [["Masakan dengan bahan dari lembah yang sehat... tidak ada yang mengalahkannya."]],
        },
        'gift_r':"Sehat!"},
    'pak_guru':   {'name':'Pak Guru','type':'human','gift':'lobak',
        'talks':{
            'default': [["Pendidikan kunci kemajuan."],["Murid-muridku perlu buku."]],
            'hearts_3': [["Pendidikan tanpa alam adalah kosong. Aku mengajar anak-anak tentang lembah."]],
            'hearts_5': [["Ada buku tua di perpustakaanku. Menceritakan tentang 'Perjanjian Pertama' antara manusia dan penjaga gunung."]],
            'hearts_7': [["Buku itu bilang, siapa yang memulihkan perjanjian akan diberkahi oleh tanah itu sendiri."]],
            'hearts_10': [["Kau membuktikan apa yang tertulis di buku itu. Murid-muridku akan belajar tentang kisahmu."]],
            'quest_11': [["Aku menulis bab baru di buku pelajaran: 'Sang Pemulih Lembah Karsa.'"]],
        },
        'gift_r':"Bergizi."},
    'mbok_jum':   {'name':'Mbok Jum','type':'human','gift':'jamur',
        'talks':{
            'default': [["Eh, anaknya siapa?"],["Dulu lembah ini tidak begini..."]],
            'hearts_3': [["Dulu lembah ini tidak begini, nak. Dulu ada cahaya dari gunung. Tapi itu cerita lama."]],
            'hearts_5': [["Tujuh puluh tahun lalu, aku melihatnya dengan mata kepalaku sendiri. Naga emas, terbang di atas lembah."]],
            'hearts_7': [["Sejak orang-orang mengambil terlalu banyak dari gua, cahaya itu padam. Naga tidak pernah muncul lagi."]],
            'hearts_10': [["Nak... cahaya dari gunung itu... aku bisa melihatnya lagi. Terima kasih."]],
            'quest_11': [["Sebelum aku pergi dari dunia ini, aku ingin melihat naga terbang sekali lagi. Dan kau membuatnya mungkin."]],
        },
        'gift_r':"Buat sayur lodeh!"},
    'jaka_ronda': {'name':'Pak Jaka','type':'human','gift':'kayu',
        'talks':{
            'default': [["Hati-hati malam, banyak yang aneh."],["Ronda berat."]],
            'hearts_3': [["Malam ini mereka lebih gelisah dari biasa. Ada yang berubah di lembah."]],
            'hearts_5': [["Aku bisa merasakan kehadiran mereka, nak. Ibuku... dia bukan orang biasa. Setengah jin."]],
            'hearts_7': [["Makhluk halus di sini bukan jahat. Mereka terjebak. Seperti aku, setengah di dunia ini, setengah di dunia mereka."]],
            'hearts_10': [["Malam-malam jadi lebih tenang. Mereka sudah tidak gelisah lagi. Pekerjaanku jadi lebih ringan."]],
            'quest_11': [["Untuk pertama kalinya dalam hidupku, ronda malam terasa damai."]],
        },
        'gift_r':"Kayu bakar!"},
    'kapten_kuro': {'name':'Kapten Kuro','type':'human','gift':'besi',
        'talks':{
            'default': [["Ahoy! Kulihat kau punya nyali memperbaiki mercusuar itu!"],["Kapal kami, Naga Hitam, datang dari negeri yang jauh."]],
            'hearts_3': [["Kami dulu adalah bajak laut, tapi sekarang kami berdagang. Terutama barang eksotis!"]],
            'hearts_5': [["Mercusuar ini sudah mati puluhan tahun. Kau pasti orang yang istimewa."]],
            'hearts_7': [["Kalau kau butuh senjata atau meriam, carilah aku. Hahaha!"]],
            'hearts_10': [["Kapan-kapan, ikutlah berlayar bersama kami melintasi lautan bebas!"]],
            'quest_11': [["Bahkan Naga Emas dari gunungmu takut melihat moncong Naga Hitam kami! Hahaha!"]],
        },
        'gift_r':"Besi yang kuat untuk meriam!"},
    'kru_kuro': {'name':'Kru Bajak Laut','type':'human','gift':'kayu',
        'talks':{
            'default': [["Hoi! Jangan sentuh tali kapal!"],["Kulihat daratan ini cukup indah."]],
            'hearts_3': [["Kapten kami memang kasar, tapi dia punya hati baja."]],
            'hearts_5': [["Kami terus berlayar karena daratan kami sudah tak bisa dihidupi."]],
            'hearts_7': [["Melihat lembahmu... rasanya ingin menetap."]],
            'hearts_10': [["Mungkin aku akan bertani saja. Kau mau mengajariku?"]],
            'quest_11': [["Lembah ini benar-benar surga! Pantas kau menjaganya."]],
        },
        'gift_r':"Kayu untuk tambal kapal!"},
}

SUPERNATURAL_NPCS = {
    'naga_bijak':    {'name':'Sang Hyang Naga','type':'naga',
        'talks':{
            'default': [["(Naga membuka mata)"],
                 ["Manusia... mengapa kau di sini?"],
                 ["Aku menjaga lembah ribuan tahun."],
                 ["Buktikan keberanianmu \u2014 duel denganku!"],
                 ["(Setelah kalah) Kau pantas dihormati."],
                 ["Ambillah air keabadian."]],
            'hearts_3': [["Manusia... aku sudah ribuan tahun di sini. Menunggu."]],
            'hearts_5': [["Yang terakhir datang, mengambil dan pergi. Keserakahannya melukai tanah ini."]],
            'hearts_7': [["Tapi kau berbeda. Aku bisa merasakan tanah mulai percaya padamu."]],
            'hearts_10': [["Perjanjian baru telah terjalin. Aku akan menjaga lembah ini... bersamamu."]],
            'quest_11': [["Kau pantas. Air Keabadian milikmu. Jaga lembah ini... selamanya."]],
        },
        'gift':'mandrake','gift_r':"Benda dari kedalaman bumi."},
    'jin_kebun':     {'name':'Jin Kebun','type':'jin',
        'talks':{
            'default': [["Hihihi... subur..."],["Aku suka tomat merah!"]],
            'hearts_3': [["Hihihi... kau tahu kenapa aku di sini? Karena aku tak bisa pergi. Tanah ini mengikatku sejak air berhenti mengalir."]],
            'hearts_5': [["Dulu aku merawat setiap tanaman di lembah. Sekarang kekuatanku melemah."]],
            'hearts_7': [["Kalau air mengalir lagi, aku bisa kembali menjaga kebun seperti dulu."]],
            'hearts_10': [["Kekuatanku kembali! Aku akan menjaga kebunmu, manusia baik. Selamanya!"]],
            'quest_11': [["Hihihi! Lihat! Tanamanmu tumbuh dua kali lebih cepat! Itu aku yang bantu!"]],
        },
        'gift':'tomat','gift_r':"Merah! Manis!"},
    'demit_tua':     {'name':'Mbah Demit','type':'demit',
        'talks':{
            'default': [["Dingin..."],["Banyak yang terlupakan."]],
            'hearts_3': [["Banyak yang terlupakan di lembah ini. Termasuk aku."]],
            'hearts_5': [["Aku ingat masa keemasan. Manusia dan kami berdampingan. Keserakahan mengakhiri segalanya."]],
            'hearts_7': [["Seseorang mengambil terlalu banyak kristal dari gua. Aku menyaksikannya."]],
            'hearts_10': [["Akhirnya... seseorang memperbaikinya. Aku bisa beristirahat dengan tenang."]],
            'quest_11': [["Dingin ini... mulai hangat. Terima kasih, nak."]],
        },
        'gift':'jamur','gift_r':"Mengingatkanku masa lalu."},
    'tuyul_pencuri': {'name':'Uyil','type':'tuyul',
        'talks':{
            'default': [["Uang! Hihi!"],["Jangan kejar!"]],
            'hearts_3': [["Uang! Uang! ...tapi perutku tetap lapar."]],
            'hearts_5': [["Dulu aku anak desa ini. Mati kelaparan saat tanah berhenti memberi."]],
            'hearts_7': [["Kalau tanah subur lagi... mungkin aku tidak perlu mencuri."]],
            'hearts_10': [["Perutku kenyang! Tanah memberi cukup untuk semua! Aku tidak mencuri lagi, janji!"]],
            'quest_11': [["Hihi! Aku mau main saja sekarang! Tidak perlu cari uang lagi!"]],
        },
        'gift':'jagung','gift_r':"Kuning seperti emas!"},
    'kuntilanak':    {'name':'Kuntilanak','type':'kuntilanak',
        'talks':{
            'default': [["Hihihihi..."],["Carikan bunga melati..."]],
            'hearts_3': [["Hihihi... jangan takut. Aku hanya mencari bunga melati."]],
            'hearts_5': [["Bunga itu untuk makam anakku. Dia pergi saat lembah dalam masa kelam."]],
            'hearts_7': [["Carikan aku melati... bukan untukku. Untuk dia yang menunggu."]],
            'hearts_10': [["Aku menemukannya. Terima kasih. Aku bisa pergi sekarang... dengan tenang."]],
            'quest_11': [["(Keheningan yang damai. Angin berhembus lembut.)"]],
        },
        'gift':'stroberi','gift_r':"Merah seperti darah."},
    'pocong':        {'name':'Pocong','type':'pocong',
        'talks':{
            'default': [["Tolong... lepaskan..."],["Ingin tenang..."]],
            'hearts_3': [["Tolong... lepaskan ikatanku. Aku sudah lama di sini. Terlalu lama."]],
            'hearts_5': [["Aku terjebak saat gua runtuh. Salah satu korban keserakahan."]],
            'hearts_7': [["Kalau perjanjian dipulihkan... mungkin aku bisa bebas."]],
            'hearts_10': [["(Ikatan terlepas perlahan. Senyum tipis.) Terima kasih."]],
            'quest_11': [["(Pocong telah pergi dengan damai. Hanya angin yang tersisa.)"]],
        },
        'gift':'wild_herb','gift_r':"(Mengangguk)"},
    'genderuwo':     {'name':'Genderuwo','type':'genderuwo',
        'talks':{
            'default': [["GROOAARR!"],["Manusia kecil... berani sekali."]],
            'hearts_3': [["Manusia kecil... aku ditugaskan mengusir kalian. Oleh Naga sendiri."]],
            'hearts_5': [["Tapi... lama-lama aku lupa kenapa. Aku hanya marah. Selalu marah."]],
            'hearts_7': [["Kau tidak seperti mereka. Kau memberi, bukan mengambil."]],
            'hearts_10': [["Hmph. Mungkin aku salah tentang manusia. Tidak semuanya buruk."]],
            'quest_11': [["Aku akan menjaga gunung ini. Bukan untuk mengusir \u2014 tapi untuk melindungi."]],
        },
        'gift':'labu','gift_r':"Hmph. Lumayan."},
    'wewe_gombel':   {'name':'Wewe Gombel','type':'wewe',
        'talks':{
            'default': [["Anak nakal kuculik..."],["Kau bukan anak nakal kan?"]],
            'hearts_3': [["Anak-anak nakal... aku culik untuk dijaga. Karena tidak ada yang menjaga mereka."]],
            'hearts_5': [["Saat lembah kelam, banyak anak ditinggalkan. Aku mengumpulkan mereka."]],
            'hearts_7': [["Sekarang lembah membaik. Mungkin anak-anak tidak perlu dijaga olehku lagi."]],
            'hearts_10': [["Biarkan aku menjaga dari jauh saja. Itu sudah cukup."]],
            'quest_11': [["Anak-anak desa tertawa lagi. Suara paling indah di dunia."]],
        },
        'gift':'bayam','gift_r':"Untuk cucu-cucuku."},
    'banaspati':     {'name':'Banaspati','type':'banaspati',
        'talks':{
            'default': [["(Api berderak)"]],
            'hearts_3': [["(Api membara, tapi lebih redup dari biasa)"]],
            'hearts_5': [["Aku menjaga api agar gua tidak benar-benar mati. Tapi kekuatanku melemah."]],
            'hearts_7': [["Kalau air mengalir... api dan air akan seimbang kembali."]],
            'hearts_10': [["(Api membara terang, hangat, tidak membakar. Kedamaian.)"]],
            'quest_11': [["(Banaspati berpendar lembut, menerangi jalan pulang.)"]],
        },
        'gift':'ore_besi','gift_r':"Makanan keras. Bagus."},
    'leak_bali':     {'name':'Leak','type':'leak',
        'talks':{
            'default': [["Krrhhh..."]],
            'hearts_3': [["Krrhhh... ilmuku datang dari kegelapan. Tapi kegelapan ini bukan pilihanku."]],
            'hearts_5': [["Aku datang mencari kekuatan. Yang kutemukan hanya kekosongan."]],
            'hearts_7': [["Mungkin ada kekuatan yang lebih besar dari ilmu hitam. Kekuatan tanah yang sehat."]],
            'hearts_10': [["Ilmuku berubah. Bukan lagi hitam. Bukan putih. Tapi hijau \u2014 seperti tanah yang hidup."]],
            'quest_11': [["Aku tetap di sini. Menjaga keseimbangan dari sisi gelap. Setiap cahaya butuh bayangan."]],
        },
        'gift':'tomat','gift_r':"Merah segar..."},
    'bidadari':      {'name':'Bidadari','type':'bidadari',
        'talks':{
            'default': [["Selamat datang di Swarga, tempat yang suci."],["Awan di sini terasa begitu lembut."]],
            'hearts_3': [["Kau manusia pertama yang sampai ke sini dalam ratusan tahun."]],
            'hearts_5': [["Tugas kami adalah menjaga keseimbangan langit dan bumi."]],
            'hearts_7': [["Keberanianmu di bawah sana bergema sampai ke langit."]],
            'hearts_10': [["Bunga dari bumi sungguh indah. Terima kasih atas ketulusanmu."]],
            'quest_11': [["Swarga kini bersinar lebih terang berkat pahlawan sepertimu."]],
        },
        'gift':'stroberi','gift_r':"Manis dan merah, sungguh indah."},
    'dewa_angin':    {'name':'Dewa Angin','type':'dewa',
        'talks':{
            'default': [["(Angin berhembus pelan)"],["Siapa yang berani masuk ke istana langit?"]],
            'hearts_3': [["Aku mengendalikan badai dan hembusan sejuk."]],
            'hearts_5': [["Banyak manusia serakah, tapi kau tampaknya berbeda."]],
            'hearts_7': [["Jika kau terus berbuat baik, angin akan selalu membantumu."]],
            'hearts_10': [["Mithril ini sekuat tekadmu. Aku menerimanya."]],
            'quest_11': [["Angin di lembah kini meniupkan kedamaian."]],
        },
        'gift':'ore_mithril','gift_r':"Berkilau seperti bintang!"},
    'petapa_srimana':   {'name':'Petapa Srimana','type':'petapa',
        'talks':{
            'default': [["Om..."],["Pikiran yang tenang adalah awal dari keseimbangan."]],
            'hearts_3': [["Aku adalah Srimana. Petapa Emas yang menjaga inti langit."]],
            'hearts_5': [["Naga Emas di bumi adalah saudaraku dalam menjaga keseimbangan alam."]],
            'hearts_7': [["Jika bumi aman dan tanah kembali bernapas, langit pun akan turun memberkahi."]],
            'hearts_10': [["Emas murni ini... getarannya sama dengan jiwamu yang tulus. Terima kasih."]],
            'quest_11': [["Bawalah berkah dari langit. Kau tidak akan pernah berjalan sendirian lagi."]],
        },
        'gift':'ore_emas','gift_r':"Emas yang bersinar murni."},
}

# 'product' hanya label lama. Yang benar-benar dibaca adalah
# economy.ANIMAL_PRODUCE, yang dikunci per JENIS ('type') bukan per id — dulu
# peta hasil ternak dikunci 'sapi_betina'/'ayam'/'kambing' yang tidak pernah
# cocok dengan id di sini, jadi tidak satu pun hewan pernah menghasilkan.
ANIMAL_NPCS = {
    'sapi_betsy':      {'name':'Betsy','type':'sapi','talks':[["Moo..."]],'product':'susu'},
    'ayam_kuning':     {'name':'Pio','type':'ayam','talks':[["Petok!"]],'product':'telur'},
    'kambing_jenggot': {'name':'Jenggot','type':'kambing','talks':[["Mbekkk..."]],'product':'wol'},
    'bebek_donald':    {'name':'Donald','type':'bebek','talks':[["Wek wek!"]],'product':'telur'},
    'domba_woolly':    {'name':'Woolly','type':'domba','talks':[["Bee..."]],'product':'wol'},
    'kuda_pegasus':    {'name':'Pegasus','type':'kuda','talks':[["Hiiyaa!"]],'product':None},
    'kucing_oren':     {'name':'Oren','type':'kucing','talks':[["Meong"]],'product':None},
    'rubah_hutan':     {'name':'Reynard','type':'rubah','talks':[["(Mengintai)"]],'product':None},
    'kelinci_putih':   {'name':'Pinky','type':'kelinci','talks':[["(Hidung berkedut)"]],'product':None},
}

def all_npcs():
    return list(HUMAN_NPCS.keys()) + list(SUPERNATURAL_NPCS.keys()) + list(ANIMAL_NPCS.keys())

SCHEDULES = {
    'arya':       [(6, 12, 12, 'farm', 'walking'), (12, 15, 15, 'town', 'walking'),
                   (18, 5, 5, 'farm', 'resting')],
    'sari':       [(6, 4, 4, 'shop', 'preparing'), (8, 4, 4, 'shop', 'working'),
                   (18, 15, 15, 'town', 'walking'), (21, 5, 5, 'shop', 'sleeping')],
    'raka':       [(6, 6, 6, 'clinic', 'working'), (13, 12, 18, 'town', 'strolling'),
                   (17, 6, 6, 'clinic', 'reading')],
    'maya':       [(8, 10, 10, 'studio', 'painting'), (14, 20, 10, 'mountain', 'sketching'),
                   (20, 10, 10, 'studio', 'sleeping')],
    'budi':       [(7, 7, 7, 'smith', 'forging'), (19, 12, 12, 'town', 'drinking'),
                   (22, 7, 7, 'smith', 'sleeping')],
    'joko':       [(4, 8, 8, 'lake', 'fishing'), (10, 9, 8, 'lake', 'fishing'),
                   (15, 4, 4, 'shop', 'shopping'), (18, 8, 8, 'lake', 'fishing'),
                   (22, 8, 8, 'lake', 'sleeping')],
    'cici':       [(7, 10, 14, 'farm', 'playing'), (13, 22, 18, 'town', 'wandering'),
                   (18, 5, 5, 'farm', 'home')],
    'bowo':       [(7, 7, 16, 'farm', 'helping'), (12, 15, 12, 'town', 'school'),
                   (17, 5, 5, 'farm', 'home')],
    'ningsih':    [(6, 4, 4, 'farm', 'cooking'), (12, 4, 4, 'farm', 'cooking'),
                   (18, 12, 12, 'town', 'gossiping'), (21, 4, 4, 'farm', 'sleeping')],
    'pak_guru':   [(7, 12, 8, 'town', 'teaching'), (15, 22, 18, 'town', 'reading'),
                   (20, 12, 8, 'town', 'sleeping')],
    'mbok_jum':   [(6, 18, 14, 'town', 'cooking'), (14, 18, 14, 'town', 'serving'),
                   (21, 18, 14, 'town', 'sleeping')],
    'jaka_ronda': [(0, -1, -1, 'hidden', 'sleeping'), (18, 12, 14, 'town', 'patroling'),
                   (4, -1, -1, 'hidden', 'sleeping')],
    'kapten_kuro': [(0, 20, 16, 'beach', 'jaga_kapal'), (8, 20, 16, 'beach', 'inspeksi'),
                    (14, 19, 15, 'beach', 'istirahat'), (20, 20, 16, 'beach', 'jaga_kapal')],
    'kru_kuro': [(0, 21, 15, 'beach', 'bersih_bersih'), (7, 18, 14, 'beach', 'angkat_barang'),
                 (12, 19, 13, 'beach', 'makan'), (18, 21, 15, 'beach', 'bersih_bersih')],
    'naga_bijak':    [(0, 7, 6, 'naga_cave', 'sleeping'), (5, 7, 6, 'naga_cave', 'meditating')],
    'jin_kebun':     [(0, -1, -1, 'hidden', 'dormant'), (19, 5, 8, 'farm', 'helping'),
                      (4, -1, -1, 'hidden', 'dormant')],
    'demit_tua':     [(0, -1, -1, 'hidden', 'dormant'), (20, 5, 20, 'mountain', 'haunting'),
                      (4, -1, -1, 'hidden', 'dormant')],
    'tuyul_pencuri': [(0, -1, -1, 'hidden', 'sleeping'), (1, 5, 5, 'farm', 'stealing'),
                      (5, -1, -1, 'hidden', 'sleeping')],
    'kuntilanak':    [(0, -1, -1, 'hidden', 'dormant'), (20, 3, 12, 'lake', 'haunting'),
                      (4, -1, -1, 'hidden', 'dormant')],
    'pocong':        [(0, -1, -1, 'hidden', 'dormant'), (21, 8, 19, 'cemetery', 'jumping'),
                      (3, -1, -1, 'hidden', 'dormant')],
    'genderuwo':     [(0, -1, -1, 'hidden', 'dormant'), (19, 14, 12, 'mountain', 'roaming'),
                      (5, -1, -1, 'hidden', 'dormant')],
    'wewe_gombel':   [(0, 11, 2, 'mountain', 'patroling'), (4, -1, -1, 'hidden', 'dormant'),
                      (20, 11, 2, 'mountain', 'patroling')],
    'banaspati':     [(0, 13, 10, 'naga_cave', 'hovering'), (6, -1, -1, 'hidden', 'dormant'),
                      (18, 13, 10, 'naga_cave', 'hovering')],
    'leak_bali':     [(0, 2, 2, 'cemetery', 'hovering'), (5, -1, -1, 'hidden', 'dormant'),
                      (19, 2, 2, 'cemetery', 'hovering')],
    'bidadari':      [(0, 10, 15, 'swarga', 'meditating')],
    'dewa_angin':    [(0, 15, 5, 'swarga', 'hovering')],
    'petapa_srimana':[(0, 20, 15, 'swarga', 'meditating')],
    'sapi_betsy':      [(0, 18, 5, 'farm', 'grazing')],
    'ayam_kuning':     [(0, 16, 5, 'farm', 'pecking')],
    'kambing_jenggot': [(0, 19, 6, 'farm', 'grazing')],
    'bebek_donald':    [(0, 9, 9, 'lake', 'swimming')],
    'domba_woolly':    [(0, 17, 7, 'farm', 'grazing')],
    'kuda_pegasus':    [(0, 20, 5, 'farm', 'grazing')],
    'kucing_oren':     [(0, 7, 9, 'farm', 'lounging')],
    'rubah_hutan':     [(0, 22, 18, 'mountain', 'prowling')],
    'kelinci_putih':   [(0, 15, 18, 'mountain', 'hopping')],
}

QUEST_STAGES = [
    {'s':0,'t':'Baru Datang','d':'Cek kotak pos depan rumah'},
    {'s':1,'t':'Petani Pemula','d':'Tanam & siram 3 lobak'},
    {'s':2,'t':'Panen Pertama','d':'Panen 3 lobak'},
    {'s':3,'t':'Ekonomi Desa','d':'Kumpulkan 150G'},
    {'s':4,'t':'Alat Lebih Baik','d':'Beli upgrade di Bengkel'},
    {'s':5,'t':'Eksplorasi Gua','d':'Crafting pickaxe & masuk gua'},
    {'s':6,'t':'Penambang Pemula','d':'5 tembaga + 3 besi'},
    {'s':7,'t':'Pendekar Karsa','d':'Pedang besi & bunuh 5 mob'},
    {'s':8,'t':'Misteri Kuburan','d':'Tangkap 1 makhluk halus'},
    {'s':9,'t':'Kedalaman','d':'Capai gua level 10'},
    {'s':10,'t':'Boss Naga','d':'Kalahkan Sang Hyang Naga'},
    {'s':11,'t':'TAMAT','d':'Air Keabadian milikmu!'},
]

MINERALS = {
    'tembaga':  {'name':'Tembaga','sell':30,'min_level':1,'tier':1},
    'besi':     {'name':'Besi','sell':60,'min_level':3,'tier':2},
    'emas':     {'name':'Emas','sell':120,'min_level':6,'tier':3},
    'kristal':  {'name':'Kristal Cahaya','sell':90,'min_level':4,'tier':2},
    'mithril':  {'name':'Mithril','sell':250,'min_level':10,'tier':4},
}

PICKAXE_RECIPES = [
    {'tier':1,'name':'Pickaxe Kayu',    'cost_gold':50,   'needs':{'kayu':5}},
    {'tier':2,'name':'Pickaxe Tembaga', 'cost_gold':120,  'needs':{'kayu':3,'tembaga':3}},
    {'tier':3,'name':'Pickaxe Besi',    'cost_gold':250,  'needs':{'besi':5}},
    {'tier':4,'name':'Pickaxe Emas',    'cost_gold':500,  'needs':{'emas':3,'besi':5}},
    {'tier':5,'name':'Pickaxe Mithril', 'cost_gold':1200, 'needs':{'mithril':3,'emas':3}},
]

SWORD_RECIPES = [
    {'id':'sword_kayu',    'name':'Pedang Kayu',    'cost_gold':80,   'damage':10, 'needs':{'kayu':8}},
    {'id':'sword_besi',    'name':'Pedang Besi',    'cost_gold':200,  'damage':25, 'needs':{'besi':6,'kayu':2}},
    {'id':'sword_emas',    'name':'Pedang Emas',    'cost_gold':600,  'damage':45, 'needs':{'emas':4,'besi':4}},
    {'id':'sword_mithril', 'name':'Pedang Mithril', 'cost_gold':1500, 'damage':80, 'needs':{'mithril':5}},
]

MOB_TEMPLATES = {
    'kelelawar':  {'name':'Kelelawar', 'hp':15,  'damage':5,  'min_lvl':1,  'max_lvl':6,
                   'speed':2.5, 'drops':{'kayu':1},              'xp':5},
    'tikus_gua':  {'name':'Tikus Gua', 'hp':12,  'damage':4,  'min_lvl':1,  'max_lvl':4,
                   'speed':2.0, 'drops':{'tembaga':1},           'xp':3},
    'genderuwo':  {'name':'Genderuwo', 'hp':50,  'damage':15, 'min_lvl':5,  'max_lvl':12,
                   'speed':1.5, 'drops':{'besi':1,'kayu':2},     'xp':15},
    'banaspati':  {'name':'Banaspati', 'hp':60,  'damage':20, 'min_lvl':6,  'max_lvl':13,
                   'speed':2.0, 'drops':{'kristal':1},           'xp':20},
    'kuntilanak': {'name':'Kuntilanak','hp':45,  'damage':18, 'min_lvl':7,  'max_lvl':12,
                   'speed':1.8, 'drops':{'kristal':1},           'xp':18},
    'leak':       {'name':'Leak',      'hp':90,  'damage':30, 'min_lvl':10, 'max_lvl':12,
                   'speed':2.2, 'drops':{'emas':1,'mithril':1},  'xp':35},
    'pocong':     {'name':'Pocong',    'hp':100, 'damage':25, 'min_lvl':9,  'max_lvl':12,
                   'speed':1.0, 'drops':{'emas':2},              'xp':30},
}

BHUTAKALA_BOSS = {
    'name':'Bhutakala', 'hp':1000, 'damage':80, 'speed':1.8,
    'spawn_level':13, 'drops':{'ikan_legendaris':1, 'mithril':10, 'emas':20},
}

DUNGEON_MAX_LEVEL = 13
DUNGEON_TILES_W   = 24
DUNGEON_TILES_H   = 18

# ── LORE ITEMS — fragmen cerita yang bisa dikumpulkan ─────
LORE_ITEMS = {
    'fragmen_prasasti_1': {
        'name': 'Fragmen Prasasti I',
        'found_at': 'dungeon_5',
        'text': 'Siapa yang mengambil tanpa memberi, tanah akan berhenti memberi.',
    },
    'fragmen_prasasti_2': {
        'name': 'Fragmen Prasasti II',
        'found_at': 'dungeon_10',
        'text': 'Naga tidak tidur. Naga menunggu. Menunggu yang pantas.',
    },
    'fragmen_prasasti_3': {
        'name': 'Fragmen Prasasti III',
        'found_at': 'dungeon_14',
        'text': 'Air mengalir untuk yang pantas. Yang pantas bukan yang kuat — tapi yang menjaga.',
    },
    'buku_paman_arsa': {
        'name': 'Buku Catatan Paman Arsa',
        'found_at': 'npc_sari_hearts_6',
        'text': 'Peta gua dengan catatan tangan: "Perjanjian harus dipulihkan. Aku tidak cukup kuat. Maafkan aku."',
    },
    'peta_mimpi_maya': {
        'name': 'Peta Mimpi Maya',
        'found_at': 'npc_maya_hearts_7',
        'text': 'Sketsa detail interior gua yang belum pernah dikunjungi Maya. Mimpinya menunjukkan jalan.',
    },
    'surat_paman_arsa_2': {
        'name': 'Surat Kedua Paman Arsa',
        'found_at': 'quest_11',
        'text': 'Kalau kau membaca ini, berarti lembah sudah aman. Aku bangga padamu. Aku tidak pernah pergi — aku selalu di sini, di dalam tanah yang kau rawat. Jaga Lembah Karsa. Selamanya.',
    },
}

# ── SEASONAL EVENT DATA ──────────────────────────────────
SEASONAL_EVENTS = {
    'semi': {
        'name': 'Festival Tanam',
        'day': 14,
        'scene': 'farm',
        'desc': 'Penduduk desa berkumpul untuk menanam bersama. Tradisi kuno yang hampir terlupakan.',
    },
    'panas': {
        'name': 'Malam Api Unggun',
        'day': 14,
        'scene': 'lake',
        'desc': 'Semua berkumpul di tepi danau. Mbok Jum bercerita tentang Zaman Keemasan.',
    },
    'gugur': {
        'name': 'Hari Arwah',
        'day': 14,
        'scene': 'cemetery',
        'desc': 'Kuburan bercahaya biru. Makhluk halus lebih aktif, tapi tidak berbahaya.',
    },
    'dingin': {
        'name': 'Malam Terpanjang',
        'day': 14,
        'scene': 'mountain',
        'desc': 'Salju pertama turun. Rahasia tersembunyi di balik gunung.',
    },
}

# ── SHOP — barang yang dijual Bu Sari di warung ──────────
# Daftar benih DITURUNKAN dari CROPS, tidak ditulis tangan lagi. Dulu harga
# benih hidup di dua tempat (CROPS['cost'] dan daftar literal di sini) dan
# tidak ada yang menjaga keduanya sama; sekarang mustahil menyimpang.
# Harga jual-kembali setiap barang ada di game/economy.py — selalu di bawah
# harga beli, supaya beli-lalu-jual-ulang tidak jadi mesin uang.
# ─── TERNAK YANG BISA DIBELI ─────────────────────────────
# Sebelum ini kesembilan hewan di ANIMAL_NPCS muncul gratis sejak hari pertama,
# jadi "membeli ternak" tidak punya arti — kandangnya sudah penuh sebelum
# pemain melakukan apa pun. Sekarang ternak penghasil harus dibeli dulu; hewan
# yang tidak menghasilkan (kuda, kucing, rubah, kelinci) tetap ada apa adanya
# karena mereka bukan ternak, mereka penghuni.
#
# HARGANYA DITURUNKAN, BUKAN DIKARANG. Untung harian satu ekor =
# nilai hasil / siklus - 18G pakan sehari (FEED_DAY_VALUE). Harga = untung
# harian x 28 hari (DAYS_PER_SEASON), yaitu balik modal tepat satu musim:
#
#   ayam    telur 32 / 1 hari = 32,0 - 18 = 14,0/hari  x28 =  392G
#   bebek   telur 32 / 1 hari = 32,0 - 18 = 14,0/hari  x28 =  392G
#   sapi    susu  42 / 1 hari = 42,0 - 18 = 24,0/hari  x28 =  672G
#   kambing wol   58 / 2 hari = 29,0 - 18 = 11,0/hari  x28 =  308G
#   domba   wol   58 / 2 hari = 29,0 - 18 = 11,0/hari  x28 =  308G
#
# Yang terlihat begitu angkanya disusun begini: WOL PALING TIDAK MENGUNTUNGKAN
# per hari meski nilainya tertinggi, karena siklus 2 hari membelah dua
# pemasukannya sementara pakan tetap dibayar tiap hari. Itu temuan neraca,
# bukan keputusan — dicatat di sini supaya terlihat, bukan diam-diam ditambal.
LIVESTOCK_FOR_SALE = {
    'kambing_jenggot': 308,
    'domba_woolly':    308,
    'ayam_kuning':     392,
    'bebek_donald':    392,
    'sapi_betsy':      672,
}

SHOP_ITEMS = [
    {'id': f'{_k}_seed', 'name': f"Benih {_c['name']}", 'price': int(_c['cost']),
     'season': '/'.join(_c['seasons']) or 'all', 'crop': _k}
    for _k, _c in CROPS.items()
] + [
    # Jerami = satu hari-pakan untuk satu ekor ternak. Harganya (18G) adalah
    # patokan yang dipakai economy.py untuk menilai pakan buatan sendiri.
    {'id': 'jerami', 'name': 'Jerami',  'price': 18, 'season': 'all', 'crop': None},
    {'id': 'kayu',   'name': 'Kayu',    'price': 20, 'season': 'all', 'crop': None},
] + [
    # Ternak. `animal` menandai baris ini bukan barang tas: panels._buy_shop_item
    # memindahkannya ke kandang, bukan ke inventori.
    {'id': _aid, 'name': ANIMAL_NPCS[_aid]['name'], 'price': _harga,
     'season': 'all', 'crop': None, 'animal': _aid}
    for _aid, _harga in LIVESTOCK_FOR_SALE.items()
]

# ─── BRANCHING DIALOGUE TREES ────────────────────────────
BRANCHING_DIALOGUES = {
    # ─── ARYA BRANCH ───
    'arya_history_start': {
        'text': "Arya: Kebun ini menyimpan misteri besar yang belum terpecahkan. Apakah kau merasa lelah mengurus tanah ini?",
        'choices': [
            {'text': "Sangat menyenangkan!", 'next': 'arya_history_happy', 'effect': {'hearts': {'arya': 1.0}, 'sosial': 15}},
            {'text': "Cukup melelahkan...", 'next': 'arya_history_tired', 'effect': {'energy': 10, 'give_item': 'wild_berry', 'sosial': 5}}
        ]
    },
    'arya_history_happy': {
        'text': "Arya: Haha! Semangatmu persis seperti Paman Arsa dahulu. Jaga terus ketulusan jiwamu, kawan.",
        'choices': []
    },
    'arya_history_tired': {
        'text': "Arya: Wajar saja. Ini, ambillah Beri Liar yang kutemukan di hutan tadi. Istirahatlah yang cukup.",
        'choices': []
    },

    # ─── BU SARI BRANCH ───
    'sari_gossip_start': {
        'text': "Bu Sari: Pamanmu dulu orang yang sangat tertutup, tapi dia menyimpan banyak rahasia. Mau tahu sesuatu?",
        'choices': [
            {'text': "Mau sekali! (Butuh 2❤)", 'next': 'sari_gossip_secret', 'condition': {'min_hearts': {'sari': 2.0}}},
            {'text': "Tidak usah, terima kasih.", 'next': 'sari_gossip_decline'}
        ]
    },
    'sari_gossip_secret': {
        'text': "Bu Sari: Pamanmu sering sekali mendaki gunung sendirian di tengah malam. Kudengar dia menaruh peta rahasia di dalam Gua Hyang level 10.",
        'choices': []
    },
    'sari_gossip_decline': {
        'text': "Bu Sari: Ya sudah kalau begitu. Cek benih-benih sayuran segar dariku jika butuh ya.",
        'choices': []
    },

    # ─── PAK BUDI BRANCH ───
    'budi_riddle_start': {
        'text': "Budi: Logam apa yang menurutmu paling berkilau dan indah di dunia ini, anak muda?",
        'choices': [
            {'text': "Tembaga — Merah membara!", 'next': 'budi_riddle_tembaga', 'effect': {'sosial': 5}},
            {'text': "Emas — Berkilau murni!", 'next': 'budi_riddle_emas', 'effect': {'sosial': 10}},
            {'text': "Mithril — Cahaya bintang!", 'next': 'budi_riddle_mithril', 'effect': {'hearts': {'budi': 1.5}, 'sosial': 15}}
        ]
    },
    'budi_riddle_tembaga': {
        'text': "Budi: Logam pemula yang kuat! Bagus untuk melatih tangan bertanitmu.",
        'choices': []
    },
    'budi_riddle_emas': {
        'text': "Budi: Berkilau indah, tapi agak terlalu lunak. Namun, harganya memang sangat tinggi!",
        'choices': []
    },
    'budi_riddle_mithril': {
        'text': "Budi: Luar biasa! Mithril adalah logam legendaris para dewa. Kau benar-benar mengerti keindahan metalurgi!",
        'choices': []
    },

    # ─── SANG HYANG NAGA BRANCH ───
    'naga_riddle_start': {
        'text': "Sang Hyang Naga: Manusia... Aku telah menyaksikan ribuan tahun keserakahan bangsamu. Katakan, apa yang paling berharga di lembah ini?",
        'choices': [
            {'text': "Emas dan Mithril berlimpah.", 'next': 'naga_riddle_gold', 'effect': {'hearts': {'naga_bijak': -2.0}}},
            {'text': "Ketulusan untuk merawat tanah.", 'next': 'naga_riddle_sincere', 'effect': {'hearts': {'naga_bijak': 2.0}, 'give_item': 'air_keabadian', 'naga_defeated': True}}
        ]
    },
    'naga_riddle_gold': {
        'text': "Sang Hyang Naga: Keserakahan yang membutakan! Bersiaplah menghadapi kemurkaanku!",
        'choices': []
    },
    'naga_riddle_sincere': {
        'text': "Sang Hyang Naga: Bagus... Kau berbeda dari penambang serakah dahulu. Ambillah Air Keabadian ini sebagai tanda restuku.",
        'choices': []
    },

    # ─── MAYA BRANCH (QUEST START & DELIVERY) ───
    'maya_quest_start': {
        'text': "Maya: Ah, matahari hari ini sangat indah! Aku ingin melukis Stroberi yang segar dan merah, tapi aku belum punya buahnya. Bisakah kau membantuku?",
        'choices': [
            {'text': "Tentu, akan kubawakan!", 'next': 'maya_quest_accept', 'effect': {'start_side_quest': 'maya_strawberry'}},
            {'text': "Maaf, aku sedang sibuk.", 'next': 'maya_quest_decline'}
        ]
    },
    'maya_quest_accept': {
        'text': "Maya: Yey! Terima kasih banyak! Aku akan menunggumu di kebun atau di studioku ya.",
        'choices': []
    },
    'maya_quest_decline': {
        'text': "Maya: Sayang sekali... Lukisanku terpaksa harus ditunda dulu kalau begitu.",
        'choices': []
    },
    'maya_quest_delivery': {
        'text': "Maya: Oh! Apakah itu buah Stroberi segar yang kubutuhkan?",
        'choices': [
            {'text': "Ya, ini untukmu. (Serahkan 1 Stroberi)", 'next': 'maya_quest_complete', 'condition': {'has_item': 'stroberi'}, 'effect': {'complete_side_quest': 'maya_strawberry', 'take_item': 'stroberi', 'gold': 100, 'hearts': {'maya': 1.5}}},
            {'text': "Belum, aku masih mencarinya.", 'next': 'maya_quest_not_yet'}
        ]
    },
    'maya_quest_complete': {
        'text': "Maya: Indah sekali! Warna merahnya sangat menginspirasiku. Ini, ambillah 100G sebagai ucapan terima kasihku!",
        'choices': []
    },
    'maya_quest_not_yet': {
        'text': "Maya: Baik bersabarlah, aku sangat menantikan buah stroberi itu untuk dilukis!",
        'choices': []
    },

    # ─── GIFT CONFIRMATION BRANCH (Premium Gifting) ───
    'gift_confirm': {
        'text': "Apakah kamu yakin ingin memberikan item ini sebagai hadiah?",
        'choices': [
            {'text': "Ya, berikan.", 'next': 'gift_yes'},
            {'text': "Tidak, simpan saja.", 'next': 'gift_no'}
        ]
    },
    'gift_yes': {
        'text': "Hadiah berhasil diberikan!",
        'choices': []
    },
    'gift_no': {
        'text': "Pemberian hadiah dibatalkan.",
        'choices': []
    }
}

# ─── SIDE QUESTS CATALOG ────────────────────────────────
SIDE_QUESTS = {
    'maya_strawberry': {
        'name': 'Stroberi Maya',
        'desc': 'Bawakan 1 Stroberi segar untuk lukisan Maya.'
    }
}
