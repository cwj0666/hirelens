#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

mkdir -p "${PROJECT_ROOT}/data/runtime"
export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

cd "${PROJECT_ROOT}"

if adk web --help 2>&1 | grep -q -- "--host"; then
  exec adk web --host "${ADK_WEB_HOST:-0.0.0.0}" --port "${ADK_WEB_PORT:-8000}" src
fi

exec adk web --port "${ADK_WEB_PORT:-8000}" src
