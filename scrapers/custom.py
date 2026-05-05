"""自定义网站抓取器"""
from datetime import datetime
from typing import Any
from typing import List
from urllib.parse import urljoin

from models.job import Job
from scrapers.base import BaseScraper
from utils.html_parser import parse_html
from utils.logger import logger


class CustomScraper(BaseScraper):
    """自定义网站抓取器"""

    JOB_TITLE_KEYWORDS = [
        'software',
        'developer',
        'backend',
        'java',
        'platform',
        'devops',
        'cloud',
        'sre',
        'site reliability',
        'data engineer',
        'full stack',
        'fullstack',
        'digital architect',
        'engineering manager',
    ]

    JOB_LINK_HINTS = [
        'job',
        'career',
        'position',
        'opening',
        'requisition',
        'posting',
        'greenhouse',
        'lever',
        'ashby',
        'workday',
        'successfactors',
        'jobvite',
    ]

    def fetch_jobs(self) -> List[Job]:
        """抓取普通 careers 页面中的基础职位链接。

        这个解析器刻意保守：只把链接文本像职位标题、URL 像职位详情的条目拿出来。
        对 Workday / SuccessFactors 等复杂平台，后续仍应实现专门 scraper。
        """
        logger.info(f"Fetching jobs from {self.company_name} (Custom)")

        response = self._request(self.url)
        if not response:
            return []

        soup = parse_html(response.text)
        jobs = []
        seen_urls = set()

        for link in soup.find_all('a', href=True):
            title = link.get_text(separator=' ', strip=True)
            href = link.get('href', '').strip()
            if not title or not href:
                continue

            title_clean = ' '.join(title.split())
            title_lower = title_clean.lower()
            href_lower = href.lower()

            if len(title_clean) < 6 or len(title_clean) > 140:
                continue
            if not any(keyword in title_lower for keyword in self.JOB_TITLE_KEYWORDS):
                continue
            if not any(hint in href_lower for hint in self.JOB_LINK_HINTS):
                continue

            job_url = urljoin(self.url, href)
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)

            location = self._infer_location(link)
            department = self._infer_department(link)
            jobs.append(Job(
                title=title_clean,
                company=self.company_name,
                location=location,
                url=job_url,
                platform='Custom',
                scraped_at=datetime.now(),
                department=department,
            ))

        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
        return jobs

    def _infer_location(self, link: Any) -> str:
        """从链接附近文本中粗略推断地点。"""
        nearby_text = self._nearby_text(link)
        location_terms = [
            'Calgary, AB',
            'Edmonton, AB',
            'Sherwood Park, AB',
            'Calgary',
            'Edmonton',
            'Alberta',
            'Remote Canada',
            'Canada Remote',
            'Canada',
        ]
        nearby_lower = nearby_text.lower()
        for term in location_terms:
            if term.lower() in nearby_lower:
                return term
        return 'Unknown'

    def _infer_department(self, link: Any) -> str:
        """从链接附近文本中粗略推断部门。"""
        nearby_text = self._nearby_text(link)
        for department in ['Engineering', 'Technology', 'Product', 'Data', 'IT']:
            if department.lower() in nearby_text.lower():
                return department
        return 'Unknown'

    @staticmethod
    def _nearby_text(link: Any) -> str:
        """取父级卡片附近文本。"""
        parent = link
        for _ in range(3):
            parent = parent.parent if parent else None
            if not parent:
                break
            text = parent.get_text(separator=' ', strip=True)
            if text and len(text) > len(link.get_text(strip=True)):
                return ' '.join(text.split())
        return link.get_text(separator=' ', strip=True)
