# VPN Rotation

Tool ini secara otomatis mengganti IP publik kamu setiap 5 menit menggunakan server VPN gratis dari [VPNGate](https://www.vpngate.net) dan OpenVPN.

> Dibuat untuk keperluan riset privasi, pengujian jaringan, dan edukasi.

---

## Apa Saja yang Bisa Tool Ini Lakukan?

| Fitur | Penjelasan Singkat |
|---|---|
| Ganti IP Otomatis | IP diganti secara berkala sesuai interval yang kamu set (default: 5 menit) |
| Pemilihan Server | Di background, tool ini ngecek server mana yang paling bisa dihubungi, baru dipilih |
| Filter Wilayah | Prioritaskan server Asia (Jepang, Korea, dll) buat ping lebih rendah |
| Kill Switch | Kalau VPN putus di tengah jalan, semua koneksi internet diblokir, IP asli tidak bocor |
| Statistik Sesi | Pantau berapa kali sudah ganti, berapa sukses, dan IP apa saja yang pernah dipakai |
| Log Sesi | Setiap sesi disimpan di folder `logs/` |
| Tampilan Terminal | UI terminal yang rapi menggunakan library `rich` |
| Mudah Dikonfigurasi | Semua pengaturan cukup di satu file: `config.json` |

---

## Yang Perlu Disiapkan

| Kebutuhan | Catatan |
|---|---|
| Linux (Debian/Ubuntu disarankan) | Kill switch butuh `iptables` yang ada di Linux |
| Python 3.10 ke atas | |
| `openvpn` | Install via: `sudo apt install openvpn` |
| `netcat` | Install via: `sudo apt install netcat-openbsd` |
| `curl` | Biasanya sudah terinstall |

---

## Cara Pakai 

```bash
# 1. Clone repo ini
cd VPN_Rotation

# 2. Buat virtual environment & install dependensi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Jalankan (ambil server baru + mulai rotasi)
bash runner.sh
```

--- 

### Contoh Penggunaan

```bash
# Ganti IP setiap 10 menit + aktifkan kill switch
python3 rotator.py --interval 600 --kill-switch

# Pakai file config custom
python3 rotator.py --config my_config.json

# Ambil server baru + mulai dengan log detail
python3 rotator.py --fetch --verbose
```

---

## Pengaturan (`config.json`)

Semua pengaturan ada di sini — tidak perlu edit kode sama sekali.

```json
{
  "vpn": {
    "config_dir"     : "config_pool",
    "pass_file"      : "pass.txt",
    "ciphers"        : "AES-128-CBC:AES-256-GCM",
    "vpn_port"       : 1194,
    "connect_timeout": 20
  },
  "rotation": {
    "interval"   : 300,
    "max_configs": 40
  },
  "filter": {
    "preferred_regions" : ["Japan", "Korea", "Singapore", "Thailand", "Vietnam"],
    "min_speed_mbps"    : 5,
    "fallback_to_global": true
  },
  "logging": {
    "log_dir": "logs",
    "verbose": false
  }
}
```

| Parameter | Penjelasan |
|---|---|
| `interval` | Jeda antar pergantian IP (dalam detik). Default 300 = 5 menit |
| `max_configs` | Maksimal berapa server yang diunduh |
| `preferred_regions` | Negara yang diprioritaskan saat memilih server |
| `min_speed_mbps` | Kecepatan minimum server yang boleh dipilih |
| `connect_timeout` | Batas waktu mencoba koneksi ke satu server |


---

## Kredensial VPN (`pass.txt`)

Server VPNGate menggunakan username dan password yang sama untuk semua orang:

```
vpn
vpn
```

> File `pass.txt` sudah masuk `.gitignore` — **jangan pernah commit file ini ke git.**

---

## Disclaimer

Tool ini menggunakan [VPNGate](https://www.vpngate.net), proyek VPN akademik gratis dari Universitas Tsukuba, Jepang.
Gunakan secara bertanggung jawab dan sesuai hukum yang berlaku di wilayahmu.
Penulis tidak bertanggung jawab atas penyalahgunaan tool ini.

---

