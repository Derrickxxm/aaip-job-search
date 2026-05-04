#!/usr/bin/env python3
"""测试单个抓取器"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.greenhouse import GreenhouseScraper
from utils.config_loader import ConfigLoader


def test_benevity():
    """测试Benevity抓取"""
    print("=" * 60)
    print("测试: Benevity (Greenhouse)")
    print("=" * 60)

    config = ConfigLoader.load_config()
    scraper = GreenhouseScraper(
        company_id='benevity',
        company_name='Benevity',
        url='https://job-boards.greenhouse.io/embed/job_board?for=benevity',
        timeout=config['request']['timeout'],
        user_agent=config['request']['user_agent']
    )

    jobs = scraper.fetch_jobs()

    print(f"\n找到 {len(jobs)} 个职位:\n")
    for i, job in enumerate(jobs[:10], 1):  # 只显示前10个
        print(f"{i}. {job.title}")
        print(f"   地点: {job.location}")
        print(f"   链接: {job.url}")
        print()

    if len(jobs) > 10:
        print(f"... 还有 {len(jobs) - 10} 个职位未显示")


if __name__ == '__main__':
    test_benevity()
