#!/usr/bin/env bash
set -euo pipefail

# Heablcoin - Cloud/Server bootstrap (Ubuntu/Debian)
# - Keep it optional/portable: features are enabled only when corresponding env vars are set.
# - This script is intended for operators; it is not executed in CI.

APP_DIR=${APP_DIR:-/opt/heablcoin}
INSTALL_NODE=${INSTALL_NODE:-true}
INSTALL_PM2=${INSTALL_PM2:-true}
INSTALL_DOCKER=${INSTALL_DOCKER:-false}
INSTALL_NGINX=${INSTALL_NGINX:-false}
INSTALL_REDIS_SERVER=${INSTALL_REDIS_SERVER:-false}
INSTALL_PY_DEPS=${INSTALL_PY_DEPS:-true}
EXTRA_PIP=${EXTRA_PIP:-"redis requests python-telegram-bot"}

echo "[setup] bootstrap dependencies (python/node/pm2/docker/nginx/redis)"

if [[ $EUID -ne 0 ]]; then
  echo "[setup] please run as root or via sudo"
  exit 1
fi

apt-get update
apt-get install -y curl git build-essential ca-certificates python3 python3-pip python3-venv

if [[ "${INSTALL_REDIS_SERVER}" == "true" ]]; then
  echo "[setup] install redis-server (optional)"
  apt-get install -y redis-server
fi

if [[ "${INSTALL_NODE}" == "true" ]]; then
  echo "[setup] install nodejs (optional; used for MCP Inspector / pm2)"
  if ! command -v node >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
  fi
fi

if [[ "${INSTALL_PM2}" == "true" ]]; then
  echo "[setup] install pm2 (optional)"
  if command -v npm >/dev/null 2>&1; then
    npm install -g pm2
  else
    echo "[setup] WARN: npm not found; skip pm2"
  fi
fi

if [[ "${INSTALL_DOCKER}" == "true" ]]; then
  echo "[setup] install docker (optional)"
  if ! command -v docker >/dev/null 2>&1; then
    apt-get install -y docker.io docker-compose-plugin
    systemctl enable --now docker || true
  fi
fi

if [[ "${INSTALL_NGINX}" == "true" ]]; then
  echo "[setup] install nginx (optional)"
  apt-get install -y nginx
  systemctl enable --now nginx || true
fi

if [[ "${INSTALL_PY_DEPS}" == "true" && -d "${APP_DIR}" ]]; then
  echo "[setup] create venv under ${APP_DIR}"
  cd "${APP_DIR}"
  python3 -m venv .venv || true
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  if [[ -n "${EXTRA_PIP}" ]]; then
    pip install ${EXTRA_PIP} || true
  fi
fi

echo "[setup] done."
echo "[setup] verify: cd ${APP_DIR} && source .venv/bin/activate && python tests/run_tests.py unit"
