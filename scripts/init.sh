#!/bin/bash
# 初始化脚本：设置环境和安装依赖

set -e

echo "=========================================="
echo "🎯 AAIP Job Aggregator - 初始化"
echo "=========================================="

# 1. 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv .venv
else
    echo "✓ 虚拟环境已存在"
fi

# 2. 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate
export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/.ms-playwright"

# 3. 安装依赖
echo "📥 安装依赖包..."
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium

# 4. 创建必要目录
echo "📁 创建目录结构..."
mkdir -p logs
mkdir -p storage
mkdir -p vault
touch storage/jobs.json

# 5. 完成
echo ""
echo "=========================================="
echo "✅ 初始化完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 可选：编辑 config/production.yaml 自定义过滤规则"
echo "  2. 运行测试：bash scripts/run_test.sh"
echo "  3. 部署定时任务：bash deploy_crontab.sh"
echo ""
echo "生成的MD文件会保存在："
echo "  /Users/xxm/projects/QuantEngine_markdown_file/YYYY-MM-DD_匹配职位.md"
echo ""
