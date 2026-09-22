---
judul: Ekonomi
tipe: sistem
modul: game/economy.py
baris: 388
status: jalan
pemanggil: 4
tags: [sistem, ekonomi, status/jalan]
---

# Ekonomi — satu sumber kebenaran untuk nilai barang

`game/economy.py`.

## Masalah yang diselesaikan

Harga tersebar di **empat tempat yang tidak saling tahu**:

| Tempat | Siapa yang membacanya |
|---|---|
| `CROPS['sell']` | hanya panen |
| `WILD_ITEMS['sell']` | hanya dicetak ke layar — tidak pernah membayar |
| `MINERALS['sell']` | **tidak dibaca siapa pun** |
| `SHOP_ITEMS['price']` | hanya beli |

Akibatnya rantai nilai tidak pernah tersambung: panen langsung mencetak emas
**sekaligus** menaruh barangnya di tas, jadi menjual tidak pernah ada gunanya
dan gudang penuh barang tanpa harga.

## Rantai yang dibangun

```
benih --beli--> tanam --siram--> panen ┬─ jual mentah
                                       ├─ OLAH jadi produk (+~40%)
                                       └─ jadikan PAKAN ternak
                                                  │
                                            hasil ternak --> jual
```

## Status sambungan

Dipakai `interaction_controller`, `time_controller`, `data.py`, `panels.py`,
dan memanggil `husbandry` ([[Ternak]]).

## Tautan

[[Palawija]] · [[Ternak]]
