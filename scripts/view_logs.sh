#!/bin/bash
# 查看实时日志

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
LOG_FILE="$SCRIPT_DIR/logs/scraper.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ 日志文件不存在: $LOG_FILE"
    exit 1
fi

echo "=========================================="
echo "📋 实时日志监控"
echo "=========================================="
echo "按 Ctrl+C 退出"
echo ""

tail -f "$LOG_FILE"
