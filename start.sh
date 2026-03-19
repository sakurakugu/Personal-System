#!/usr/bin/env bash
set -euo pipefail

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "未找到 Python，请先安装 Python 3"
    exit 1
fi

if [ "$#" -eq 0 ]; then
    "$PYTHON_CMD" "./tools/1.启动服务端py" --prod --start
else
    "$PYTHON_CMD" "./tools/1.启动服务端py" "$@"
fi
