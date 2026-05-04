#!/bin/bash
# 运行一次测试

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"
export PLAYWRIGHT_BROWSERS_PATH="$PROJECT_DIR/.ms-playwright"

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    PYTHON_CMD="python"
else
    echo "❌ 虚拟环境不存在，请先运行: bash scripts/init.sh"
    exit 1
fi

# 运行主程序
echo "=========================================="
echo "🧪 手动运行测试"
echo "=========================================="
echo ""

$PYTHON_CMD main.py "$@"

echo ""
echo "=========================================="
echo "✅ 测试完成"
echo "=========================================="
echo ""
echo "查看日志："
echo "  tail -f logs/scraper.log"
echo ""
echo "查看生成的MD文件："
echo "  ls -la /Users/xxm/projects/QuantEngine_markdown_file/"
echo ""
