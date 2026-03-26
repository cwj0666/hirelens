#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

mkdir -p "${PROJECT_ROOT}/data/runtime"
export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

exec streamlit run "${PROJECT_ROOT}/src/hirelens/streamlit_app.py" \
  --server.address=0.0.0.0 \
  --server.port="${STREAMLIT_PORT:-8501}" \
  --server.headless=true \
  --browser.gatherUsageStats=false
