#!/bin/bash
# 部署crontab定时任务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
PYTHON_PATH=$(which python3)

echo "=========================================="
echo "⏰ 部署定时任务（Crontab）"
echo "=========================================="

# 读取现有crontab
CURRENT_CRON=$(crontab -l 2>/dev/null || true)

# 检查是否已存在
if echo "$CURRENT_CRON" | grep -q "aaip-job-search"; then
    echo "⚠️  检测到已存在的定时任务"
    read -p "是否覆盖？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消部署"
        exit 0
    fi
    # 删除旧任务
    CURRENT_CRON=$(echo "$CURRENT_CRON" | grep -v "aaip-job-search")
fi

# 生成新任务
NEW_CRON="
0 8,12,18 * * * cd $SCRIPT_DIR && $PYTHON_PATH main.py >> $SCRIPT_DIR/logs/scraper.log 2>&1
"

# 追加到crontab
echo "$CURRENT_CRON$NEW_CRON" | crontab -

echo "✅ 定时任务已部署"
echo ""
echo "定时任务详情："
echo "  - 每天 8:00, 12:00, 18:00 运行"
echo "  - 日志路径: $SCRIPT_DIR/logs/scraper.log"
echo ""
echo "查看当前crontab："
echo "  crontab -l"
echo ""
echo "编辑crontab："
echo "  crontab -e"
echo ""
