"""
rotator.py  —  Core VPN rotation engine for VPN Rotation.
Handles: server selection (smart/random), OpenVPN lifecycle,
         kill-switch management, progress display, and session logging.
"""

import os, time, subprocess, random, sys, threading, json, logging, argparse
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    from rich.live import Live
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

logger = logging.getLogger("VPNRotation.Rotator")
console = Console() if RICH_AVAILABLE else None

# ─── Config ──────────────────────────────────────────────────────────────────

def load_config(path: str = "config.json") -> dict:
    with open(path) as f:
        return json.load(f)

# ─── Session Stats ───────────────────────────────────────────────────────────

session_stats = {
    "start_time"   : datetime.now(),
    "rotations"    : 0,
    "success"      : 0,
    "failed"       : 0,
    "ips_used"     : [],
}

def record_rotation(success: bool, ip: str = ""):
    session_stats["rotations"] += 1
    if success:
        session_stats["success"] += 1
        if ip and ip not in session_stats["ips_used"]:
            session_stats["ips_used"].append(ip)
    else:
        session_stats["failed"] += 1

# ─── Network Helpers ─────────────────────────────────────────────────────────

def get_current_ip(timeout: int = 6) -> str:
    """Return current public IP or a status string."""
    services = [
        ["curl", "-s", "--max-time", str(timeout), "https://api.ipify.org"],
        ["curl", "-s", "--max-time", str(timeout), "ifconfig.me"],
    ]
    for cmd in services:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+2)
            ip = result.stdout.strip()
            if ip:
                return ip
        except Exception:
            continue
    return "Unavailable"

def check_server_reachable(ip: str, port: int = 1194, timeout: int = 2) -> bool:
    """Quick UDP reachability check via netcat."""
    try:
        res = subprocess.run(
            ["nc", "-zu", "-w", str(timeout), ip, str(port)],
            stderr=subprocess.DEVNULL, timeout=timeout+1
        )
        return res.returncode == 0
    except Exception:
        return False

# ─── Server Pool Management ──────────────────────────────────────────────────

verified_pool: list = []
pool_lock = threading.Lock()

def verify_servers_async(configs: list, port: int = 1194):
    """Background thread: probe servers and populate verified_pool."""
    global verified_pool
    temp = []
    sample = random.sample(configs, min(len(configs), 20))
    logger.debug(f"Probing {len(sample)} servers in background...")
    for c in sample:
        try:
            # Filename format: 01_Japan_10.5Mbps_1.2.3.4.ovpn
            ip = c.rsplit('_', 1)[-1].replace('.ovpn', '')
            if check_server_reachable(ip, port):
                temp.append(c)
        except Exception:
            continue
    with pool_lock:
        verified_pool = temp
    logger.debug(f"Background probe complete: {len(temp)} verified servers.")

def pick_server(configs: list) -> tuple[str, str]:
    """Return (filename, mode_label). Prefers verified pool."""
    with pool_lock:
        if verified_pool:
            chosen = verified_pool.pop(0)
            return chosen, "Smart Select ✓"
    return random.choice(configs), "Random Select (warming up)"

# ─── Kill Switch ─────────────────────────────────────────────────────────────

def enable_kill_switch(vpn_iface: str = "tun0"):
    """Block all non-VPN traffic via iptables."""
    rules = [
        ["sudo", "iptables", "-F"],
        ["sudo", "iptables", "-A", "OUTPUT", "-o", "lo",            "-j", "ACCEPT"],
        ["sudo", "iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "53",   "-j", "ACCEPT"],
        ["sudo", "iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "1194", "-j", "ACCEPT"],
        ["sudo", "iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "443",  "-j", "ACCEPT"],
        ["sudo", "iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "80",   "-j", "ACCEPT"],
        ["sudo", "iptables", "-A", "OUTPUT", "-o", vpn_iface,       "-j", "ACCEPT"],
        ["sudo", "iptables", "-A", "OUTPUT",                        "-j", "DROP"],
    ]
    for rule in rules:
        subprocess.run(rule, stderr=subprocess.DEVNULL)
    logger.info("Kill switch ENABLED.")

def disable_kill_switch():
    """Restore default iptables policy."""
    subprocess.run(["sudo", "iptables", "-F"], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "iptables", "-P", "OUTPUT", "ACCEPT"], stderr=subprocess.DEVNULL)
    logger.info("Kill switch DISABLED.")

# ─── Display Helpers ─────────────────────────────────────────────────────────

BANNER = r"""
 ██╗   ██╗██████╗ ███╗   ██╗    ██████╗  ██████╗ ████████╗ █████╗ ████████╗██╗ ██████╗ ███╗   ██╗
 ██║   ██║██╔══██╗████╗  ██║    ██╔══██╗██╔═══██╗╚══██╔══╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
 ██║   ██║██████╔╝██╔██╗ ██║    ██████╔╝██║   ██║   ██║   ███████║   ██║   ██║██║   ██║██╔██╗ ██║
 ╚██╗ ██╔╝██╔═══╝ ██║╚██╗██║    ██╔══██╗██║   ██║   ██║   ██╔══██║   ██║   ██║██║   ██║██║╚██╗██║
  ╚████╔╝ ██║     ██║ ╚████║    ██║  ██║╚██████╔╝   ██║   ██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║
   ╚═══╝  ╚═╝     ╚═╝  ╚═══╝    ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                              🛡️  Stealth VPN Rotation System  |  Powered by VPNGate
"""

def print_banner():
    if RICH_AVAILABLE:
        console.print(Panel(BANNER, style="bold cyan", expand=False))
    else:
        print(BANNER)

def print_status_table(server: str, first_ip: str, new_ip: str, mode: str):
    if not RICH_AVAILABLE:
        print(f"  Server  : {server}")
        print(f"  Old IP  : {first_ip}")
        print(f"  New IP  : {new_ip}")
        print(f"  Mode    : {mode}")
        return

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key",   style="bold green")
    table.add_column("Value", style="white")

    elapsed = str(datetime.now() - session_stats["start_time"]).split('.')[0]

    table.add_row("Server",    server)
    table.add_row("Old IP",    f"[dim]{first_ip}[/dim]")
    table.add_row("New IP",    f"[bold green]{new_ip}[/bold green]")
    table.add_row("Mode",      mode)
    table.add_row("Rotations", f"{session_stats['rotations']} ({session_stats['success']} ok / {session_stats['failed']} failed)")
    table.add_row("Uptime",    elapsed)

    console.print(Panel(table, title="[bold cyan]VPN Rotation — Connection Status[/bold cyan]", border_style="cyan"))

def wait_with_progress(seconds: int):
    """Countdown before next rotation."""
    if RICH_AVAILABLE:
        with Progress(
            TextColumn("[bold cyan]Next rotation in"),
            BarColumn(bar_width=40, complete_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("", total=seconds)
            while not progress.finished:
                time.sleep(1)
                progress.advance(task)
    else:
        for i in range(seconds, 0, -1):
            sys.stdout.write(f"\r  [*] Next rotation in {i:3d}s ")
            sys.stdout.flush()
            time.sleep(1)
        print()

# ─── VPN Lifecycle ───────────────────────────────────────────────────────────

def kill_existing_vpn():
    subprocess.run(["sudo", "pkill", "-9", "openvpn"], stderr=subprocess.DEVNULL)
    time.sleep(0.5)

def connect_vpn(config_path: str, pass_file: str, ciphers: str, timeout: int) -> tuple[bool, subprocess.Popen]:
    """
    Spawn openvpn and wait for 'Initialization Sequence Completed'.
    Uses readline() loop (never exits early on slow output).
    Returns (success, process).
    """
    process = subprocess.Popen(
        [
            "sudo", "openvpn",
            "--config",          config_path,
            "--auth-user-pass",  pass_file,
            "--data-ciphers",    ciphers,
            "--verb",            "3",
            "--connect-timeout", "15",   # timeout per koneksi (CLI arg, bukan di .ovpn)
            "--resolv-retry",    "2",    # retry DNS maksimal 2x
            "--tls-timeout",     "10",   # TLS negotiation timeout
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,                           # line-buffered
    )

    start       = time.time()
    success     = False
    fail_reason = ""
    log_buffer  = []   # simpan log di buffer, jangan langsung print

    while True:
        line = process.stdout.readline()

        if not line:
            fail_reason = "process exited unexpectedly (check openvpn/sudo)"
            break

        line = line.strip()
        log_buffer.append(line)

        # ── Success — jangan print apapun, terminal tetap bersih ─
        if "Initialization Sequence Completed" in line:
            success = True
            break

        # ── Known failures ───────────────────────────────────────
        if "AUTH_FAILED" in line:
            fail_reason = "authentication failed (check pass.txt)"
            break
        if "TLS Error" in line:
            fail_reason = "TLS handshake error"
            break
        if "RESOLVE" in line and "error" in line.lower():
            fail_reason = "DNS resolution failed"
            break
        if "Connection refused" in line:
            fail_reason = "server refused connection"
            break

        # ── Timeout ──────────────────────────────────────────────
        if time.time() - start > timeout:
            fail_reason = f"timed out after {timeout}s"
            break

    if not success:
        logger.debug(f"OpenVPN failed: {fail_reason}")
        logger.debug(f"Last log: {log_buffer[-1] if log_buffer else 'none'}")
        try:
            process.terminate()
            process.wait(timeout=3)
        except Exception:
            pass

    return success, process

# ─── Main Loop ───────────────────────────────────────────────────────────────

def start_vpn(config: dict, kill_switch: bool = False):
    # Resolve ke absolute path agar sudo tidak kehilangan working dir
    base_dir     = os.path.dirname(os.path.abspath(__file__))
    config_dir   = os.path.join(base_dir, config.get("config_dir", "config_pool"))
    pass_file    = os.path.join(base_dir, config.get("pass_file",  "pass.txt"))
    interval     = config.get("interval",   300)
    ciphers      = config.get("ciphers",    "AES-128-CBC:AES-256-GCM")
    vpn_port     = config.get("vpn_port",   1194)
    conn_timeout = config.get("connect_timeout", 20)  # batas atas loop, openvpn sudah timeout sendiri di 15s

    # Validasi pass.txt sebelum masuk loop
    if not os.path.isfile(pass_file):
        logger.error(f"pass.txt tidak ditemukan: {pass_file}")
        logger.error("Buat file pass.txt berisi dua baris:\nvpn\nvpn")
        sys.exit(1)

    os.system("sudo ls > /dev/null")  # cache sudo credentials

    if kill_switch:
        enable_kill_switch()

    # Banner hanya tampil sekali
    if RICH_AVAILABLE:
        console.clear()
        print_banner()

    attempt = 0   # counter untuk tampilan trying

    while True:
        configs = [f for f in os.listdir(config_dir) if f.endswith(".ovpn")]
        if not configs:
            logger.error(f"No .ovpn files in '{config_dir}'. Run fetch_pool.py first.")
            sys.exit(1)

        # Background server probe
        threading.Thread(
            target=verify_servers_async,
            args=(configs, vpn_port),
            daemon=True
        ).start()

        selected, mode = pick_server(configs)
        config_path = os.path.join(config_dir, selected)

        try:
            country_tag = selected.split('_')[1]
            ip_tag      = selected.rsplit('_', 1)[-1].replace('.ovpn', '')
        except IndexError:
            country_tag = selected
            ip_tag      = ""

        attempt += 1
        first_ip = get_current_ip()
        kill_existing_vpn()

        # Tampilkan status trying — satu baris, bersih
        if RICH_AVAILABLE:
            with console.status(
                f"  [bold yellow][ {attempt} ][/bold yellow]"
                f"  [bold cyan]{country_tag}[/bold cyan]"
                f"  [dim]{ip_tag}[/dim]"
                f"  [dim]({mode})[/dim]",
                spinner="dots"
            ):
                success, process = connect_vpn(config_path, pass_file, ciphers, conn_timeout)
        else:
            print(f"  [{attempt}] Trying {country_tag} {ip_tag} ...")
            success, process = connect_vpn(config_path, pass_file, ciphers, conn_timeout)

        new_ip = get_current_ip() if success else "—"
        record_rotation(success, new_ip)

        if success:
            # Hard clear — hapus semua output sebelumnya tanpa sisa
            os.system("clear")
            print_banner()
            print_status_table(selected, first_ip, new_ip, mode)
            attempt = 0
            wait_with_progress(interval)
        else:
            if RICH_AVAILABLE:
                console.print(
                    f"  [dim]↳ Failed [{country_tag} {ip_tag}] — retrying...[/dim]"
                )
            time.sleep(5)

# ─── Entry Point ─────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="🛡️  VPN Rotation — Automatic VPN rotation via VPNGate"
    )
    parser.add_argument(
        "--config", default="config.json",
        help="Path to config.json (default: config.json)"
    )
    parser.add_argument(
        "--interval", type=int, default=None,
        help="Override rotation interval in seconds"
    )
    parser.add_argument(
        "--kill-switch", action="store_true",
        help="Enable iptables kill switch (blocks non-VPN traffic)"
    )
    parser.add_argument(
        "--fetch", action="store_true",
        help="Fetch fresh VPN configs before starting"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose/debug logging"
    )
    return parser.parse_args()


def setup_logging(verbose: bool, log_dir: str = "logs"):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ]
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)

    cfg = load_config(args.config)
    if args.interval:
        cfg["interval"] = args.interval

    if args.fetch:
        from fetch_pool import download_vpn_configs
        download_vpn_configs(cfg)

    try:
        start_vpn(cfg, kill_switch=args.kill_switch)
    except KeyboardInterrupt:
        kill_existing_vpn()
        if args.kill_switch:
            disable_kill_switch()
        uptime = str(datetime.now() - session_stats["start_time"]).split('.')[0]
        print(f"\n\n  [*] VPN Rotation stopped. Uptime: {uptime} | Rotations: {session_stats['rotations']} | IPs used: {len(session_stats['ips_used'])}")
