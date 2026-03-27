"""
fetch_pool.py — Download & filter VPNGate configs for VPN Rotation.
"""
import requests
import base64
import os
import time
import json
import logging
from datetime import datetime

logger = logging.getLogger("VPNRotation.FetchPool")

VPNGATE_URL = "https://www.vpngate.net/api/iphone/"

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        return json.load(f)

def download_vpn_configs(config: dict = None) -> int:
    """
    Download & filter VPN configs from VPNGate.
    Returns count of downloaded configs.
    """
    if config is None:
        config = load_config()

    preferred_regions = config.get("preferred_regions", ["Japan", "Korea", "Singapore"])
    min_speed_mbps    = config.get("min_speed_mbps", 5)
    max_configs       = config.get("max_configs", 40)
    config_dir        = config.get("config_dir", "config_pool")
    min_speed_bps     = min_speed_mbps * 1_000_000

    logger.info("Fetching VPN list from VPNGate...")

    try:
        response = requests.get(VPNGATE_URL, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch VPN list: {e}")
        return 0

    lines   = response.text.replace('\r', '').split('\n')
    servers = [line.split(',') for line in lines if len(line.split(',')) > 14]
    servers = servers[2:-1]  # skip header and trailing empty line

    # --- Filter by region & speed ---
    filtered = []
    for s in servers:
        try:
            country = s[6]
            speed   = int(s[10])
            if country in preferred_regions and speed > min_speed_bps:
                filtered.append(s)
        except (IndexError, ValueError):
            continue

    # Fallback: jika hasil filter terlalu sedikit, ambil yang tercepat global
    if len(filtered) < 10:
        logger.debug(f"Only {len(filtered)} regional servers found, falling back to global fastest.")
        filtered = servers[:]

    # Sort: speed DESC, ping ASC
    try:
        filtered.sort(key=lambda s: (int(s[10]), -int(s[12])), reverse=True)
    except (IndexError, ValueError):
        pass

    # --- Prepare output directory ---
    os.makedirs(config_dir, exist_ok=True)
    for f in os.listdir(config_dir):
        if f.endswith(".ovpn"):
            os.remove(os.path.join(config_dir, f))

    count = 0
    skipped = 0
    for s in filtered[:max_configs]:
        try:
            country    = s[6]
            ip_addr    = s[1]
            speed_mbps = round(int(s[10]) / 1_000_000, 2)
            ping_ms    = s[12]
            raw_config = base64.b64decode(s[-1]).decode('utf-8')

            # Optimasi: force UDP, kurangi timeout
            # Force UDP untuk performa lebih baik
            raw_config = raw_config.replace('proto tcp', 'proto udp')

            safe_country = country.replace(' ', '_')
            filename = f"{count+1:02d}_{safe_country}_{speed_mbps}Mbps_{ip_addr}.ovpn"
            filepath = os.path.join(config_dir, filename)

            with open(filepath, 'w') as f:
                f.write(raw_config)

            logger.info(f"  [{count+1:02d}] {country:<14} | {speed_mbps:>7.2f} Mbps | {ping_ms:>4} ms | {ip_addr}")
            count += 1
        except Exception as e:
            skipped += 1
            logger.debug(f"Skipped entry: {e}")
            continue

    logger.info(f"Done. {count} configs saved to '{config_dir}/' ({skipped} skipped).")
    return count


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.WARNING,   # sembunyikan INFO saat dijalankan langsung
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    cfg = load_config()
    count = download_vpn_configs(cfg)
    # Hanya tampilkan summary singkat
    print(f"[*] {count} VPN configs ready.")
