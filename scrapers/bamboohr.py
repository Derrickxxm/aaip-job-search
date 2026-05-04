"""BambooHR平台抓取器"""
from typing import List
from datetime import datetime
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger


class BambooHRScraper(BaseScraper):
    """BambooHR Job Board抓取器（需要Playwright渲染）"""

    def fetch_jobs(self) -> List[Job]:
        """抓取BambooHR嵌入式职位列表"""
        logger.info(f"Fetching jobs from {self.company_name} (BambooHR)")

        jobs = []
        if self._playwright_disabled():
            logger.info("Playwright disabled, skipping BambooHR browser scraper")
            return jobs

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({
                    'User-Agent': self.session.headers.get('User-Agent', '')
                })

                logger.info(f"Loading page: {self.url}")
                page.goto(self.url, timeout=30000)
                page.wait_for_timeout(3000)  # 等待BambooHR widget加载

                # 获取页面HTML
                html = page.content()
                browser.close()

            from utils.html_parser import parse_html
            soup = parse_html(html)

            # 当前部门（用于跟踪）
            current_department = 'Unknown'

            # 遍历所有部门
            department_items = soup.find_all('li', class_='BambooHR-ATS-Department-Item')

            for dept_item in department_items:
                # 获取部门名称
                dept_header = dept_item.find('div', class_='BambooHR-ATS-Department-Header')
                if dept_header:
                    current_department = dept_header.get_text(strip=True)

                # 获取该部门下的所有职位
                job_items = dept_item.find_all('li', class_='BambooHR-ATS-Jobs-Item')

                for job_item in job_items:
                    try:
                        # 提取职位链接和标题
                        link_elem = job_item.find('a')
                        if not link_elem:
                            continue

                        title = link_elem.get_text(strip=True)
                        job_url = link_elem.get('href', '')

                        # 补全URL
                        if job_url.startswith('//'):
                            job_url = f"https:{job_url}"
                        elif job_url and not job_url.startswith('http'):
                            job_url = f"https://helcim.bamboohr.com{job_url}"

                        # 提取地点
                        location_elem = job_item.find('span', class_='BambooHR-ATS-Location')
                        location = location_elem.get_text(strip=True) if location_elem else 'Calgary, AB'

                        jobs.append(Job(
                            title=title,
                            company=self.company_name,
                            location=location,
                            url=job_url,
                            platform='BambooHR',
                            scraped_at=datetime.now(),
                            department=current_department
                        ))
                    except Exception as e:
                        logger.error(f"Error parsing job item: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error with BambooHR scraper: {e}")

        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
        return jobs


def test_bamboohr_scraper():
    """测试函数"""
    scraper = BambooHRScraper(
        company_id='helcim',
        company_name='Helcim',
        url='https://www.helcim.com/careers/job-openings/',
        timeout=30,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
    )
    jobs = scraper.fetch_jobs()
    print(f"\n找到 {len(jobs)} 个职位:\n")
    for i, job in enumerate(jobs[:15], 1):
        print(f"{i}. {job.title}")
        print(f"   地点: {job.location}")
        print(f"   部门: {job.department}")
        print(f"   链接: {job.url}\n")


if __name__ == '__main__':
    test_bamboohr_scraper()
