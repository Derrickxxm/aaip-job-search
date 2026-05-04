"""Greenhouse平台抓取器"""
from typing import List
from datetime import datetime
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger
from utils.html_parser import parse_html


class GreenhouseScraper(BaseScraper):
    """Greenhouse Job Board抓取器"""

    def fetch_jobs(self) -> List[Job]:
        """抓取Greenhouse Job Board"""
        logger.info(f"Fetching jobs from {self.company_name} (Greenhouse)")

        response = self._request(self.url)
        if not response:
            return []

        soup = parse_html(response.text)
        jobs = []

        # 查找所有职位卡片（tr.job-post）
        job_elements = soup.find_all('tr', class_='job-post')

        for elem in job_elements:
            try:
                # 查找a标签（包含职位信息和链接）
                a_elem = elem.find('a', href=True)
                if not a_elem:
                    continue

                # 提取职位链接
                job_url = a_elem.get('href', '')

                # 提取所有p标签
                all_ps = a_elem.find_all('p')

                if len(all_ps) < 2:
                    continue

                # 第一个p是职位名称
                title_p = all_ps[0]
                # 去除span标签中的New等文字
                for span in title_p.find_all('span', class_='tag-text'):
                    span.decompose()
                title_text = title_p.get_text(separator=' ', strip=True)

                # 第二个p是地点
                location_p = all_ps[1]
                location = location_p.text.strip() if location_p else 'Unknown'

                # 尝试提取部门（从h3 section-header获取）
                department = 'Unknown'
                section = elem.find_previous('h3', class_='section-header')
                if section:
                    department = section.text.strip()

                jobs.append(Job(
                    title=title_text,
                    company=self.company_name,
                    location=location,
                    url=job_url,
                    platform='Greenhouse',
                    scraped_at=datetime.now(),
                    department=department
                ))
            except Exception as e:
                logger.error(f"Error parsing job element: {e}")
                continue

        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
        return jobs


def test_greenhouse_scraper():
    """测试函数"""
    scraper = GreenhouseScraper(
        company_id='benevity',
        company_name='Benevity',
        url='https://job-boards.greenhouse.io/embed/job_board?for=benevity',
        timeout=10,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    jobs = scraper.fetch_jobs()
    print(f"\n找到 {len(jobs)} 个职位:\n")
    for i, job in enumerate(jobs[:10], 1):
        print(f"{i}. {job.title}")
        print(f"   地点: {job.location}")
        print(f"   部门: {job.department}")
        print(f"   链接: {job.url}")
        print()

    if len(jobs) > 10:
        print(f"... 还有 {len(jobs) - 10} 个职位未显示")


if __name__ == '__main__':
    test_greenhouse_scraper()
