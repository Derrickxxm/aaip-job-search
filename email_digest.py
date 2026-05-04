"""Gmail 邮件摘要主入口

抓取 Gmail 中的招聘邮件和 LinkedIn 通知，翻译为中文，保存到每日 Markdown 报告。

用法:
    python email_digest.py              # 抓取今天的邮件
    python email_digest.py --days 3     # 抓取最近 3 天
    python email_digest.py --check      # 仅在预定时间运行（与 main.py 联动）
"""
import sys
from datetime import datetime

from utils.config_loader import ConfigLoader
from utils.logger import logger
from utils.translator import Translator
from fetchers.gmail_fetcher import GmailFetcher
from notification.email_report import EmailReportNotifier


def main(days: int = 1):
    """主函数"""
    logger.info("=" * 60)
    logger.info("Starting Gmail Email Digest")
    logger.info("=" * 60)

    # 加载配置
    config = ConfigLoader.load_config('config/production.yaml')
    gmail_config = config.get('gmail', {})
    translation_config = config.get('translation', {})

    credentials_path = gmail_config.get('credentials_path', 'config/gmail_credentials.json')
    token_path = gmail_config.get('token_path', 'config/gmail_token.json')
    vault_dir = config.get('storage', {}).get(
        'vault_dir', '/Users/xxm/projects/QuantEngine_markdown_file/12-找工作'
    )

    # 1. 抓取 Gmail 邮件
    fetcher = GmailFetcher(
        credentials_path=credentials_path,
        token_path=token_path
    )

    try:
        emails = fetcher.fetch_emails(days=days)
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("请先运行: python scripts/setup_gmail_auth.py")
        sys.exit(1)

    if not emails:
        logger.info("No matching emails found")
        logger.info("=" * 60)
        logger.info("Gmail Email Digest completed")
        logger.info("=" * 60)
        return

    logger.info(f"Fetched {len(emails)} emails")

    # 2. 翻译邮件内容
    model = translation_config.get('model', 'claude-haiku-4-5-20251001')
    translator = Translator(model=model)

    results = []
    for email in emails:
        context = f"主题: {email.subject} | 发件人: {email.sender} | 类型: {email.email_type}"
        translation = translator.translate(email.body, context=context)
        results.append((email, translation))
        logger.info(f"Translated: {email.subject[:50]}")

    # 3. 保存到 Markdown 报告
    notifier = EmailReportNotifier(vault_dir=vault_dir)
    filepath = notifier.append_to_daily_report(results)

    if filepath:
        logger.info(f"Report saved to: {filepath}")
    else:
        logger.error("Failed to save email report")

    logger.info("=" * 60)
    logger.info("Gmail Email Digest completed")
    logger.info("=" * 60)


def check_schedule() -> bool:
    """检查当前时间是否在预定时间范围内"""
    config = ConfigLoader.load_config('config/production.yaml')
    scheduled_hours = config.get('schedule', {}).get('hours', [8, 12, 18])

    current_hour = datetime.now().hour
    if current_hour in scheduled_hours:
        logger.info(f"Current hour {current_hour} is in scheduled hours {scheduled_hours}")
        return True
    else:
        logger.info(f"Current hour {current_hour} not in scheduled hours {scheduled_hours}")
        return False


if __name__ == '__main__':
    # 解析参数
    days = 1
    if '--days' in sys.argv:
        idx = sys.argv.index('--days')
        if idx + 1 < len(sys.argv):
            try:
                days = int(sys.argv[idx + 1])
            except ValueError:
                logger.warning(f"Invalid --days value, using default: 1")

    if '--check' in sys.argv:
        if check_schedule():
            main(days=days)
        else:
            logger.info("Skipping: not in scheduled time")
    else:
        main(days=days)
