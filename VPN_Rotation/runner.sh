#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  VPN Rotation — runner.sh
#  Usage:
#    ./runner.sh                  # fetch + rotate (no kill switch)
#    ./runner.sh --kill-switch    # fetch + rotate + enable kill switch
#    ./runner.sh --no-fetch       # rotate with existing configs
# ─────────────────────────────────────────────────────────────

set -e

KILL_SWITCH=false
FETCH=true

for arg in "$@"; do
  case $arg in
    --kill-switch) KILL_SWITCH=true ;;
    --no-fetch)    FETCH=false ;;
  esac
done

# ── Check dependencies ────────────────────────────────────────
for dep in openvpn nc curl python3; do
  if ! command -v "$dep" &>/dev/null; then
    echo "[-] Missing dependency: $dep"
    exit 1
  fi
done

# ── Activate venv if present ─────────────────────────────────
if [ -d "venv" ]; then
  source venv/bin/activate
  echo "[*] Virtual environment activated."
fi

# ── Step 1: Fetch configs ─────────────────────────────────────
if [ "$FETCH" = true ]; then
  echo "[*] Fetching VPN configs..."
  python3 fetch_pool.py
fi

# ── Step 2: Run rotator ───────────────────────────────────────
ARGS="--config config.json"

if [ "$KILL_SWITCH" = true ]; then
  ARGS="$ARGS --kill-switch"
fi

# Banner ditampilkan oleh rotator.py
python3 rotator.py $ARGS
