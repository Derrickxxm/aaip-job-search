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
        'engineer',
        'developer',
        'backend',
        'front-end',
        'frontend',
        'java',
        'platform',
        'devops',
        'cloud',
        'sre',
        'site reliability',
        'qa',
        'quality assurance',
        'automation',
        'security',
        'database',
        'infrastructure',
        'mobile',
        'architect',
        'analyst',
        'technical',
        'ai engineer',
        'machine learning',
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

        direct_job = self._extract_direct_job(soup)
        if direct_job:
            jobs.append(direct_job)
            seen_urls.add(direct_job.url)

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

    def _extract_direct_job(self, soup: Any) -> Job | None:
        """当 careers_url 本身就是职位详情页时，直接生成一个职位。"""
        title = self._page_job_title(soup)
        if not title:
            return None

        title_lower = title.lower()
        page_text = soup.get_text(separator=' ', strip=True)
        page_text_lower = page_text.lower()

        has_job_title = any(keyword in title_lower for keyword in self.JOB_TITLE_KEYWORDS)
        has_job_body = any(keyword in page_text_lower for keyword in ['apply', 'job description', 'about the role'])
        if not has_job_title or not has_job_body:
            return None

        return Job(
            title=title,
            company=self.company_name,
            location=self._infer_location_from_text(page_text),
            url=self.url,
            platform='Custom',
            scraped_at=datetime.now(),
            department=self._infer_department_from_text(page_text),
        )

    @staticmethod
    def _page_job_title(soup: Any) -> str | None:
        """从详情页提取职位标题。"""
        title_keywords = CustomScraper.JOB_TITLE_KEYWORDS

        for selector in ['h1', 'h2']:
            for heading in soup.find_all(selector):
                title = ' '.join(heading.get_text(separator=' ', strip=True).split())
                title_lower = title.lower()
                if 6 <= len(title) <= 140 and any(keyword in title_lower for keyword in title_keywords):
                    return title

        page_title = soup.find('title')
        if page_title:
            title = ' '.join(page_title.get_text(separator=' ', strip=True).split())
            title = title.split('|')[0].split(' - ')[0].strip()
            title_lower = title.lower()
            if 6 <= len(title) <= 140 and any(keyword in title_lower for keyword in title_keywords):
                return title
        return None

    def _infer_location(self, link: Any) -> str:
        """从链接附近文本中粗略推断地点。"""
        return self._infer_location_from_text(self._nearby_text(link))

    @staticmethod
    def _infer_location_from_text(text: str) -> str:
        """从文本中粗略推断地点。"""
        location_terms = [
            'Calgary, Alberta',
            'Calgary, AB',
            'Edmonton, Alberta',
            'Edmonton, AB',
            'Sherwood Park, AB',
            'St. Albert, Alberta',
            'St. Albert, AB',
            'Calgary',
            'Edmonton',
            'Sherwood Park',
            'St. Albert',
            'Alberta',
            'Remote Canada',
            'Canada Remote',
            'Canada',
        ]
        text_lower = text.lower()
        for term in location_terms:
            if term.lower() in text_lower:
                return term
        return 'Unknown'

    def _infer_department(self, link: Any) -> str:
        """从链接附近文本中粗略推断部门。"""
        return self._infer_department_from_text(self._nearby_text(link))

    @staticmethod
    def _infer_department_from_text(text: str) -> str:
        """从文本中粗略推断部门。"""
        for department in ['Engineering', 'Technology', 'Product', 'Data', 'IT']:
            if department.lower() in text.lower():
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
