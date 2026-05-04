#!/bin/bash
# 安装Playwright浏览器

set -e

echo "=========================================="
echo "📦 安装Playwright浏览器"
echo "=========================================="

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "❌ 虚拟环境不存在，请先运行: bash scripts/init.sh"
    exit 1
fi

# 安装Playwright
echo "安装Playwright浏览器..."
playwright install chromium

echo ""
echo "=========================================="
echo "✅ Playwright安装完成！"
echo "=========================================="
echo ""
echo "现在可以测试Neo Financial抓取："
echo "  python scrapers/ashby.py"
echo ""
