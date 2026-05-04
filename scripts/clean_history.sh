#!/bin/bash
# 清理历史数据

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
STORAGE_FILE="$SCRIPT_DIR/storage/jobs.json"

echo "=========================================="
echo "🧹 清理历史职位记录"
echo "=========================================="

if [ -f "$STORAGE_FILE" ]; then
    read -p "确认清理所有历史职位URL？（y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo '{"recorded_urls": [], "sent_urls": [], "schema_version": 2, "last_updated": null}' > "$STORAGE_FILE"
        echo "✅ 已清理历史职位记录"
    else
        echo "❌ 取消清理"
    fi
else
    echo "ℹ️  历史记录文件不存在"
fi
echo ""
