#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/heablcoin}
VENV_DIR=${VENV_DIR:-$APP_DIR/.venv}
PM2_NAME=${PM2_NAME:-heablcoin-mcp}

cd "$APP_DIR"
git pull --ff-only

python3 -m venv "$VENV_DIR" || true
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

python tests/run_tests.py integration

pm2 start Heablcoin.py --name "$PM2_NAME" --interpreter "$VENV_DIR/bin/python" --env MCP_MODE=server || pm2 restart "$PM2_NAME"
pm2 save

echo "[deploy] pm2 status:"
pm2 status "$PM2_NAME"
