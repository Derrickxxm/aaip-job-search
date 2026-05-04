"""本地存储通知模块"""
import os
import re
from typing import List
from datetime import datetime
from models.job import Job
from utils.logger import logger


class LocalStorageNotifier:
    """本地MD文件存储通知器"""

    def __init__(self, vault_dir: str = '/Users/xxm/projects/QuantEngine_markdown_file/12-找工作'):
        self.vault_dir = vault_dir
        self._ensure_vault_dir()

    def _ensure_vault_dir(self):
        """确保vault目录存在"""
        if not os.path.exists(self.vault_dir):
            os.makedirs(self.vault_dir)
            logger.info(f"Created vault directory: {self.vault_dir}")

    def save_jobs(self, jobs: List[Job]) -> str:
        """
        保存职位到MD文件

        Args:
            jobs: 匹配的职位列表

        Returns:
            文件路径
        """
        if not jobs:
            logger.info("No jobs to save")
            return None

        # 生成文件名：YYYY-MM-DD_匹配职位.md
        filename = f"{datetime.now().strftime('%Y-%m-%d')}_匹配职位.md"
        filepath = os.path.join(self.vault_dir, filename)

        # 构建MD内容
        content = self._build_markdown(jobs)

        # 写入文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved {len(jobs)} jobs to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving to file: {e}")
            return None

    def _build_markdown(self, jobs: List[Job]) -> str:
        """构建Markdown内容"""
        md_lines = [
            f"# 🎯 AAIP 匹配职位报告",
            f"",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**职位数量**: {len(jobs)}",
            f"---",
            f"",
            f"## 职位列表",
            f""
        ]

        # 添加每个职位
        for i, job in enumerate(jobs, 1):
            md_lines.extend([
                f"### {i}. {job.title}",
                f"",
                f"- **公司**: {job.company}",
                f"- **地点**: {job.location}",
                f"- **平台**: {job.platform}",
                f"- **链接**: [查看职位]({job.url})",
                f"- **部门**: {job.department if job.department else 'N/A'}",
                f""
            ])

        # 添加页脚
        md_lines.extend([
            f"---",
            f"",
            f"*此报告由 AAIP Job Aggregator 自动生成*",
            f"*配置路径*: `config/production.yaml`",
            f"*日志路径*: `logs/scraper.log`",
            f""
        ])

        return '\n'.join(md_lines)

    def append_to_daily_report(self, jobs: List[Job]) -> str:
        """
        追加到当天的MD报告（而不是覆盖）

        Args:
            jobs: 新匹配的职位列表

        Returns:
            文件路径
        """
        if not jobs:
            return None

        # 查找当天的文件
        daily_filename = f"{datetime.now().strftime('%Y-%m-%d')}_匹配职位.md"
        filepath = os.path.join(self.vault_dir, daily_filename)

        # 检查文件是否存在
        if os.path.exists(filepath):
            # 读取现有内容
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_content = f.read()

            # 在"职位列表"后追加新职位
            if "## 职位列表" in existing_content:
                # 找到现有编号
                existing_jobs = []
                for line in existing_content.split('\n'):
                    if line.startswith('### '):
                        existing_jobs.append(line)

                last_num = len(existing_jobs) if existing_jobs else 0

                # 追加新职位
                new_content = existing_content.rstrip()

                for job in jobs:
                    last_num += 1
                    new_content += f"\n\n### {last_num}. {job.title}"
                    new_content += f"\n"
                    new_content += f"- **公司**: {job.company}"
                    new_content += f"\n- **地点**: {job.location}"
                    new_content += f"\n- **平台**: {job.platform}"
                    new_content += f"\n- **链接**: [查看职位]({job.url})"
                    new_content += f"\n- **部门**: {job.department if job.department else 'N/A'}"
                    new_content += f"\n"

                # 更新职位数量
                new_content = re.sub(
                    r"\*\*职位数量\*\*: \d+",
                    f"**职位数量**: {last_num}",
                    new_content
                )

                # 写回文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info(f"Appended {len(jobs)} jobs to {filepath}")
                return filepath

        # 文件不存在，创建新文件
        return self.save_jobs(jobs)
