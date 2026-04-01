# VPN Rotation

Ganti IP publik kamu secara otomatis menggunakan server VPN gratis dari [VPNGate](https://www.vpngate.net).

> Untuk keperluan riset privasi, pengujian jaringan, dan edukasi.

---

## Fitur Utama

- **Ganti IP otomatis** — IP berubah setiap 5 menit (bisa diatur)
- **Pilih server terbaik** — Otomatis cari server tercepat yang bisa dihubungi
- **Prioritas wilayah Asia** — Jepang, Korea, Singapura, dll (ping lebih rendah)
- **Kill switch** — Blokir semua koneksi kalau VPN putus, IP asli tidak bocor
- **Statistik & log** — Catat semua sesi dan IP yang pernah dipakai
- **Tampilan rapi** — Pakai library `rich` di terminal

---

## Kebutuhan

- Linux (Debian/Ubuntu)
- Python 3.10+
- `openvpn`, `netcat`, `curl`

```bash
sudo apt install openvpn netcat-openbsd curl
```

---

## Cara Pakai

```bash
# 1. Masuk ke folder project
cd VPN_Rotation

# 2. Buat virtual environment & install dependensi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Jalankan
bash runner.sh
```

### Opsi Tambahan

```bash
# Ganti IP setiap 10 menit + kill switch
python3 rotator.py --interval 600 --kill-switch

# Jalankan tanpa download ulang server
bash runner.sh --no-fetch

# Mode verbose (log detail)
python3 rotator.py --fetch --verbose
```

---

## Pengaturan (`config.json`)

Semua pengaturan ada di satu file ini, tidak perlu edit kode.

| Parameter | Fungsi | Default |
|---|---|---|
| `interval` | Jeda antar ganti IP (detik) | `300` (5 menit) |
| `max_configs` | Jumlah server yang diunduh | `40` |
| `preferred_regions` | Negara prioritas | Jepang, Korea, dll |
| `min_speed_mbps` | Kecepatan minimum server | `5` Mbps |
| `connect_timeout` | Batas waktu koneksi | `20` detik |

---

## Kredensial VPN (`pass.txt`)

Semua server VPNGate pakai username dan password yang sama:

```
vpn
vpn
```

> File ini sudah di-`.gitignore` — jangan commit ke git.

---

## Disclaimer

Tool ini menggunakan [VPNGate](https://www.vpngate.net), proyek VPN akademik gratis dari Universitas Tsukuba, Jepang. Gunakan secara bertanggung jawab dan sesuai hukum yang berlaku di wilayahmu. Penulis tidak bertanggung jawab atas penyalahgunaan tool ini.
