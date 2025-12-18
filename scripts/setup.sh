#!/usr/bin/env bash
set -euo pipefail

echo "[setup] install base dependencies (Python/Node/Redis)"

if [[ $EUID -ne 0 ]]; then
  echo "[setup] please run as root or via sudo"
  exit 1
fi

apt-get update
apt-get install -y curl git build-essential python3 python3-pip python3-venv redis-server

curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
npm install -g pm2

echo "[setup] create venv under /opt/heablcoin (if present)"
cd /opt/heablcoin 2>/dev/null || exit 0
python3 -m venv .venv || true
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[setup] done. run 'python tests/run_tests.py unit' to verify."
