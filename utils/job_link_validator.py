"""职位链接有效性校验"""
import re
from typing import List

import requests

from models.job import Job
from utils.logger import logger


class JobLinkValidator:
    """校验职位链接是否仍然可打开"""

    def __init__(self, timeout: int = 8, user_agent: str = 'Mozilla/5.0'):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})

    def filter_active_jobs(self, jobs: List[Job]) -> List[Job]:
        """过滤掉明确失效的职位链接"""
        active_jobs = []
        for job in jobs:
            if self.is_active(job):
                active_jobs.append(job)
            else:
                logger.info(f"Dropped inactive job link: {job.title} @ {job.company} | {job.url}")
        return active_jobs

    def is_active(self, job: Job) -> bool:
        """判断职位链接是否有效"""
        try:
            response = self.session.get(job.url, timeout=self.timeout, allow_redirects=True)
        except requests.exceptions.Timeout:
            logger.warning(f"Link validation timeout, keeping job: {job.url}")
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Link validation request failed, dropping job: {job.url} ({e})")
            return False

        if response.status_code >= 400:
            logger.info(f"Inactive job link HTTP {response.status_code}: {job.url}")
            return False

        page_text = self._clean_text(response.text)
        page_title = self._extract_title(page_text)

        if self._has_inactive_title(page_title):
            logger.info(f"Inactive job link by title '{page_title}': {job.url}")
            return False

        if self._has_inactive_body(page_text):
            logger.info(f"Inactive job link by body content: {job.url}")
            return False

        return True

    @staticmethod
    def _clean_text(text: str) -> str:
        """压缩空白，便于匹配"""
        return re.sub(r'\s+', ' ', text).strip().lower()

    @staticmethod
    def _extract_title(page_text: str) -> str:
        """提取HTML标题"""
        match = re.search(r'<title[^>]*>(.*?)</title>', page_text, re.IGNORECASE)
        return match.group(1).strip() if match else ''

    @staticmethod
    def _has_inactive_title(title: str) -> bool:
        """标题中出现明确失效信号"""
        if not title:
            return False
        inactive_patterns = [
            '404',
            'not found',
            'page not found',
            'job not found',
            'position not found',
        ]
        return any(pattern in title for pattern in inactive_patterns)

    @staticmethod
    def _has_inactive_body(page_text: str) -> bool:
        """正文中出现明确职位失效信号"""
        inactive_patterns = [
            'job not found',
            'position not found',
            'the job you requested was not found',
            'the position you requested was not found',
            'this job is no longer available',
            'this position is no longer available',
            'the job you are looking for is no longer available',
            'the position you are looking for is no longer available',
            'this job posting is no longer available',
            'this posting is no longer available',
        ]
        return any(pattern in page_text for pattern in inactive_patterns)
