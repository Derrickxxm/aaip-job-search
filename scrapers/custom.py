"""自定义网站抓取器（预留）"""
from typing import List
from scrapers.base import BaseScraper
from models.job import Job
from datetime import datetime


class CustomScraper(BaseScraper):
    """自定义网站抓取器"""

    def fetch_jobs(self) -> List[Job]:
        """抓取自定义网站Job Board"""
        print(f"Fetching jobs from {self.company_name} (Custom)")
        print("⚠️  Custom scraper not implemented yet.")
        return []

        # TODO: 根据具体网站HTML结构实现
