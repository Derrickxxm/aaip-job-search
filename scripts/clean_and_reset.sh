#!/bin/bash
# 清理历史数据，重新开始测试

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🧹 清理历史数据"
echo "=========================================="

# 清空storage/jobs.json
echo '{"recorded_urls": [], "sent_urls": [], "schema_version": 2, "last_updated": null}' > storage/jobs.json
echo "✅ 已清空 storage/jobs.json"

# 删除旧的MD文件
rm -f /Users/xxm/projects/QuantEngine_markdown_file/*_匹配职位.md
echo "✅ 已删除旧的MD文件"

echo ""
echo "=========================================="
echo "✅ 清理完成！"
echo "=========================================="
echo ""
echo "现在可以重新运行测试："
echo "  python3 main.py"
echo ""
