#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/heablcoin}
VENV_DIR=${VENV_DIR:-$APP_DIR/.venv}
DEPLOY_MODE=${DEPLOY_MODE:-pipeline_worker}  # pipeline_worker|mcp_server|inspector|all
RUN_TESTS=${RUN_TESTS:-integration}          # none|unit|integration|all
PM2_PREFIX=${PM2_PREFIX:-heablcoin}
PIPELINE_SCRIPT=${PIPELINE_SCRIPT:-src/core/cloud/pipeline_worker.py}
MCP_ENTRY=${MCP_ENTRY:-Heablcoin.py}

cd "$APP_DIR"
git pull --ff-only

python3 -m venv "$VENV_DIR" || true
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

if [[ "${RUN_TESTS}" != "none" ]]; then
  python tests/run_tests.py "${RUN_TESTS}"
fi

if command -v pm2 >/dev/null 2>&1; then
  if [[ "${DEPLOY_MODE}" == "pipeline_worker" || "${DEPLOY_MODE}" == "all" ]]; then
    echo "[deploy] start pipeline worker via pm2"
    PYTHONIOENCODING=utf-8 PYTHONUTF8=1 RUN_ONCE=false pm2 start "$PIPELINE_SCRIPT" \
      --name "${PM2_PREFIX}-pipeline-worker" \
      --interpreter "$VENV_DIR/bin/python" || pm2 restart "${PM2_PREFIX}-pipeline-worker"
  fi

  if [[ "${DEPLOY_MODE}" == "mcp_server" || "${DEPLOY_MODE}" == "all" ]]; then
    echo "[deploy] start MCP server via pm2 (not recommended for stdio; prefer local MCP client)"
    PYTHONIOENCODING=utf-8 PYTHONUTF8=1 pm2 start "$MCP_ENTRY" \
      --name "${PM2_PREFIX}-mcp" \
      --interpreter "$VENV_DIR/bin/python" || pm2 restart "${PM2_PREFIX}-mcp"
  fi

  if [[ "${DEPLOY_MODE}" == "inspector" || "${DEPLOY_MODE}" == "all" ]]; then
    echo "[deploy] start MCP Inspector via pm2"
    pm2 start --name "${PM2_PREFIX}-inspector" --interpreter bash -- -lc \
      "cd '${APP_DIR}' && npx @modelcontextprotocol/inspector --server-command '${VENV_DIR}/bin/python ${APP_DIR}/${MCP_ENTRY}'" \
      || pm2 restart "${PM2_PREFIX}-inspector"
  fi

  pm2 save
else
  echo "[deploy] WARN: pm2 not found, skip process management"
fi

echo "[deploy] pm2 status:"
if command -v pm2 >/dev/null 2>&1; then
  pm2 status || true
fi
