"""Lever平台抓取器"""
from typing import List
from datetime import datetime
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger
from utils.html_parser import parse_html


class LeverScraper(BaseScraper):
    """Lever Job Board抓取器"""

    def fetch_jobs(self) -> List[Job]:
        """抓取Lever Job Board"""
        logger.info(f"Fetching jobs from {self.company_name} (Lever)")

        response = self._request(self.url)
        if not response:
            return []

        soup = parse_html(response.text)
        jobs = []

        # 查找所有职位卡片
        posting_elements = soup.find_all('div', class_='posting')

        for elem in posting_elements:
            try:
                # 提取职位链接和标题
                title_link = elem.find('a', class_='posting-title')
                if not title_link:
                    continue

                title = title_link.get_text(strip=True)
                job_url = title_link.get('href', '')

                # 补全URL
                if job_url and not job_url.startswith('http'):
                    job_url = f"https://jobs.lever.co{job_url}"

                # 提取分类信息
                categories = elem.find('div', class_='posting-categories')
                location = 'Unknown'
                department = 'Unknown'

                if categories:
                    loc_span = categories.find('span', class_='sort-by-location')
                    if loc_span:
                        location = loc_span.get_text(strip=True)

                    team_span = categories.find('span', class_='sort-by-team')
                    if team_span:
                        department = team_span.get_text(strip=True)

                jobs.append(Job(
                    title=title,
                    company=self.company_name,
                    location=location,
                    url=job_url,
                    platform='Lever',
                    scraped_at=datetime.now(),
                    department=department
                ))
            except Exception as e:
                logger.error(f"Error parsing job element: {e}")
                continue

        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
        return jobs


def test_lever_scraper():
    """测试函数"""
    scraper = LeverScraper(
        company_id='attabotics',
        company_name='Attabotics',
        url='https://jobs.lever.co/attabotics/',
        timeout=10,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
    )
    jobs = scraper.fetch_jobs()
    print(f"\n找到 {len(jobs)} 个职位:\n")
    for i, job in enumerate(jobs[:10], 1):
        print(f"{i}. {job.title}")
        print(f"   地点: {job.location}")
        print(f"   部门: {job.department}")
        print(f"   链接: {job.url}\n")


if __name__ == '__main__':
    test_lever_scraper()
