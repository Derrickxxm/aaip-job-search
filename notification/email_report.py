"""邮件摘要 Markdown 生成器"""
import os
from datetime import datetime
from typing import List, Tuple

from fetchers.gmail_fetcher import EmailMessage
from utils.logger import logger


class EmailReportNotifier:
    """邮件摘要报告生成器，输出到与职位报告同目录的 MD 文件"""

    def __init__(self, vault_dir: str = '/Users/xxm/projects/QuantEngine_markdown_file/12-找工作'):
        self.vault_dir = vault_dir
        self._ensure_vault_dir()

    def _ensure_vault_dir(self):
        if not os.path.exists(self.vault_dir):
            os.makedirs(self.vault_dir)
            logger.info(f"Created vault directory: {self.vault_dir}")

    def _get_daily_filepath(self) -> str:
        filename = f"{datetime.now().strftime('%Y-%m-%d')}_邮件摘要.md"
        return os.path.join(self.vault_dir, filename)

    def save_emails(self, results: List[Tuple[EmailMessage, str]]) -> str:
        """
        新建每日邮件摘要文件

        Args:
            results: [(EmailMessage, 中文翻译), ...]

        Returns:
            文件路径
        """
        if not results:
            logger.info("No emails to save")
            return None

        filepath = self._get_daily_filepath()
        content = self._build_markdown(results)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved {len(results)} email summaries to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving email report: {e}")
            return None

    def append_to_daily_report(self, results: List[Tuple[EmailMessage, str]]) -> str:
        """
        追加到当天的邮件摘要文件，文件不存在则新建

        Args:
            results: [(EmailMessage, 中文翻译), ...]

        Returns:
            文件路径
        """
        if not results:
            return None

        filepath = self._get_daily_filepath()

        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_content = f.read()

            # 找到现有邮件数量
            existing_count = existing_content.count('\n### ')

            new_content = existing_content.rstrip()
            for i, (email, translation) in enumerate(results, existing_count + 1):
                new_content += self._format_email_entry(i, email, translation)

            # 更新邮件数量
            import re
            new_total = existing_count + len(results)
            new_content = re.sub(
                r'\*\*邮件数量\*\*: \d+',
                f'**邮件数量**: {new_total}',
                new_content
            )

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"Appended {len(results)} emails to {filepath}")
            return filepath

        return self.save_emails(results)

    def _build_markdown(self, results: List[Tuple[EmailMessage, str]]) -> str:
        """构建完整 Markdown 内容"""
        lines = [
            "# 📧 每日邮件摘要",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**邮件数量**: {len(results)}",
            "",
            "---",
            "",
            "## 邮件列表",
            ""
        ]

        for i, (email, translation) in enumerate(results, 1):
            lines.append(self._format_email_entry(i, email, translation))

        lines.extend([
            "",
            "---",
            "",
            "*此报告由 AAIP Job Aggregator 自动生成*",
            ""
        ])

        return '\n'.join(lines)

    def _format_email_entry(self, index: int, email: EmailMessage, translation: str) -> str:
        """格式化单封邮件条目"""
        # 邮件类型标签
        type_label = "LinkedIn 消息" if email.email_type == "linkedin" else "招聘邮件"

        # 处理发件人显示名
        sender_display = email.sender
        if '<' in email.sender:
            # 提取 "Name <email>" 格式中的名字
            sender_display = email.sender.split('<')[0].strip().strip('"')

        # 格式化邮件正文（截断并缩进引用）
        body_preview = email.body[:500].replace('\n', '\n> ') if email.body else "(无正文)"

        entry = f"""
### {index}. {type_label}: {email.subject}
- **发件人**: {email.sender}
- **显示名**: {sender_display}
- **时间**: {email.date}
- **类型**: {type_label}

**📝 中文摘要**:
{translation}

**📄 原文**:
> {body_preview}
"""
        return entry
