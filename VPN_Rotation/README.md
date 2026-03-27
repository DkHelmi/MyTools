# 🛡️ IP Rotator — Stealth VPN Rotation System

Automatically rotate your public IP address every N minutes using free [VPNGate](https://www.vpngate.net) servers and OpenVPN.

> Built for privacy research, network testing, and educational purposes.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔄 Auto Rotation | Rotates IP on a configurable interval (default: 5 min) |
| 🧠 Smart Server Select | Background probe picks lowest-latency verified server |
| 🌏 Region Filter | Prefer Asia-Pacific servers for lower ping |
| 🚫 Kill Switch | Optional iptables rule — blocks traffic if VPN drops |
| 📊 Session Stats | Tracks uptime, rotation count, and IPs used |
| 📁 Session Logging | Saves each session log to `logs/` |
| 🎨 Rich UI | Beautiful terminal display via `rich` library |
| ⚙️ Config File | Fully configurable via `config.json` |

---

## 📋 Requirements

| Requirement | Notes |
|---|---|
| Linux (Debian/Ubuntu recommended) | iptables kill switch requires Linux |
| Python 3.10+ | |
| `openvpn` | `sudo apt install openvpn` |
| `netcat` | `sudo apt install netcat-openbsd` |
| `curl` | Usually pre-installed |

---

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/VPN_Rotation.git
cd VPN_Rotation

# 2. Create a virtual environment & install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run (fetch fresh configs + start rotating)
bash runner.sh
```

---

## 🛠️ Usage

### Basic

```bash
bash runner.sh                  # fetch configs + start rotating
bash runner.sh --kill-switch    # enable iptables kill switch
bash runner.sh --no-fetch       # use existing configs (no re-fetch)
```

### Advanced (direct Python)

```bash
python3 rotator.py --help

Options:
  --config PATH       Path to config.json (default: config.json)
  --interval SECONDS  Override rotation interval
  --kill-switch       Enable iptables kill switch
  --fetch             Fetch fresh VPN configs before starting
  --verbose, -v       Enable debug logging
```

### Examples

```bash
# Rotate every 10 minutes with kill switch
python3 rotator.py --interval 600 --kill-switch

# Use a custom config file
python3 rotator.py --config my_config.json

# Fetch new servers + rotate + verbose logging
python3 rotator.py --fetch --verbose
```

---

## ⚙️ Configuration (`config.json`)

```json
{
  "vpn": {
    "config_dir"     : "config_pool",
    "pass_file"      : "pass.txt",
    "ciphers"        : "AES-128-CBC:AES-256-GCM",
    "vpn_port"       : 1194,
    "connect_timeout": 45
  },
  "rotation": {
    "interval"  : 300,
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

---

## 📁 Project Structure

```
VPN_rotation/
├── rotator.py          # Core rotation engine
├── fetch_pool.py       # Download & filter VPNGate configs
├── config_loader.py    # Config helper
├── runner.sh           # Convenience shell script
├── config.json         # All settings
├── pass.txt            # VPN credentials (gitignored!)
├── requirements.txt
├── .gitignore
├── config_pool/        # Downloaded .ovpn files (gitignored)
└── logs/               # Session logs (gitignored)
```

---

## 🔐 Credentials (`pass.txt`)

VPNGate servers use a shared username/password:

```
vpn
vpn
```

> ⚠️ `pass.txt` is listed in `.gitignore` — **never commit credentials to git.**

---

## ⚠️ Disclaimer

This tool uses [VPNGate](https://www.vpngate.net), a free academic VPN project by University of Tsukuba.
Use responsibly and in accordance with your local laws and the terms of service of any platform you access.
The authors are not responsible for misuse.

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
