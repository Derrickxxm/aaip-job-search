"""Shopify自定义抓取器"""
from typing import List
from datetime import datetime
import re
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed for Shopify scraper")


class ShopifyScraper(BaseScraper):
    """Shopify职位抓取器"""

    def fetch_jobs(self) -> List[Job]:
        """抓取Shopify职位"""
        logger.info(f"Fetching jobs from {self.company_name} (Shopify Custom)")

        jobs = self._fetch_via_http()
        if jobs:
            logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
            return jobs

        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return []

        jobs = []

        # 获取user agent
        user_agent = self.session.headers.get('User-Agent', 'Mozilla/5.0')

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=user_agent)
                
                # 访问职位页面
                page.goto(self.url, timeout=self.timeout * 1000)
                
                # 等待页面加载完成
                page.wait_for_load_state('networkidle', timeout=30000)
                
                # 获取页面内容
                html_content = page.content()
                browser.close()
                
                jobs = self._parse_job_links(html_content)
                
        except Exception as e:
            logger.error(f"Error fetching Shopify jobs: {e}")
            return []
        
        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
        return jobs

    def _fetch_via_http(self) -> List[Job]:
        """直接解析 Shopify careers 静态 HTML"""
        response = self._request(self.url)
        if not response:
            return []

        return self._parse_job_links(response.text)

    def _parse_job_links(self, html_content: str) -> List[Job]:
        """从页面 HTML 中提取职位链接"""
        jobs = []
        job_links = re.findall(r'/careers/([a-zA-Z0-9-]+_[a-f0-9-]+)', html_content)

        logger.info(f"Found {len(job_links)} job links on Shopify careers page")

        for job_slug in dict.fromkeys(job_links[:50]):
            try:
                job_url = f"https://www.shopify.com/careers/{job_slug}"
                title_slug = job_slug.split('_')[0]
                title = title_slug.replace('-', ' ').title()

                jobs.append(Job(
                    title=title,
                    company=self.company_name,
                    location="Remote",
                    url=job_url,
                    platform='Shopify Custom',
                    scraped_at=datetime.now(),
                    department='Unknown'
                ))
            except Exception as e:
                logger.debug(f"Error parsing job {job_slug}: {e}")
                continue

        return jobs


def test_shopify_scraper():
    """测试函数"""
    scraper = ShopifyScraper(
        company_id='shopify',
        company_name='Shopify',
        url='https://www.shopify.com/careers',
        timeout=30,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )

    jobs = scraper.fetch_jobs()
    print(f"\n找到 {len(jobs)} 个职位:\n")
    for i, job in enumerate(jobs[:10], 1):
        print(f"{i}. {job.title}")
        print(f"   地点: {job.location}")
        print(f"   链接: {job.url}")
        print()

    if len(jobs) > 10:
        print(f"... 还有 {len(jobs) - 10} 个职位未显示")


if __name__ == '__main__':
    test_shopify_scraper()
