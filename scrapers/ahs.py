"""Alberta Health Services 爬虫
使用 SelectMinds/Taleo 平台，需要 Playwright 渲染 JavaScript
https://careers.albertahealthservices.ca
"""
from typing import List
from datetime import datetime
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger


class AHSScraper(BaseScraper):
    """Alberta Health Services 爬虫（Playwright）"""

    # 直接浏览分类页面 + 搜索URL（正确的URL格式）
    CATEGORY_URLS = [
        "/jobs/search?keywords=&location=",  # 所有职位
        "/latest-jobs",  # 最新职位
        "/hot-jobs",  # 热门职位
        "/landingpages/nursing-health-care-aide-opportunities-at-alberta-health-services-34",
        "/landingpages/nursing-health-care-aide-opportunities-at-covenant-health-33",
    ]

    def __init__(self, company_id, company_name, url, timeout=15, user_agent=None, config=None):
        super().__init__(company_id, company_name, url, timeout, user_agent)
        self.config = config or {}
        self.seen_urls = set()
        self.base_url = url.rstrip('/')

    def fetch_jobs(self) -> List[Job]:
        """抓取AHS职位"""
        logger.info(f"Fetching jobs from {self.company_name} (AHS/SelectMinds)")

        if self._playwright_disabled():
            logger.info("Playwright disabled, using AHS HTTP parsing")
            return self._fetch_via_http()

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright not installed. Falling back to HTTP parsing")
            return self._fetch_via_http()

        all_jobs = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=self.session.headers.get('User-Agent', '')
                )
                page = context.new_page()

                for cat_url in self.CATEGORY_URLS:
                    try:
                        jobs = self._browse_page(page, f"{self.base_url}{cat_url}")
                        new_count = 0
                        for job in jobs:
                            if job.url not in self.seen_urls:
                                self.seen_urls.add(job.url)
                                all_jobs.append(job)
                                new_count += 1
                        logger.info(f"AHS: '{cat_url}' → {len(jobs)} found, {new_count} new")
                    except Exception as e:
                        logger.error(f"AHS browse error '{cat_url}': {e}")

                # 也尝试搜索关键词
                search_keywords = ['health care aide', 'nurse', 'cardiac', 'surgical']
                for keyword in search_keywords:
                    try:
                        jobs = self._search_with_form(page, keyword)
                        new_count = 0
                        for job in jobs:
                            if job.url not in self.seen_urls:
                                self.seen_urls.add(job.url)
                                all_jobs.append(job)
                                new_count += 1
                        logger.info(f"AHS search: '{keyword}' → {len(jobs)} found, {new_count} new")
                    except Exception as e:
                        logger.error(f"AHS search error '{keyword}': {e}")

                browser.close()

        except Exception as e:
            logger.error(f"AHS scraper error: {e}")
            logger.info("Falling back to HTTP parsing for AHS/Covenant")
            return self._fetch_via_http()

        logger.info(f"AHS total: {len(all_jobs)} unique jobs")
        return all_jobs

    def _fetch_via_http(self) -> List[Job]:
        """不依赖浏览器的后备抓取路径"""
        all_jobs = []

        urls = [f"{self.base_url}{path}" for path in self.CATEGORY_URLS]
        search_keywords = [
            'health care aide',
            'nurse',
            'licensed practical nurse',
            'patient care',
            'service worker',
            'porter',
            'environmental services',
            'food service',
            'laundry',
            'linen',
            'medical device reprocessing',
            'surgical processor',
            'cardiac',
            'surgical',
            'operating room',
            'perioperative',
        ]
        urls.extend(
            f"{self.base_url}/jobs/search?keywords={keyword.replace(' ', '%20')}&location="
            for keyword in search_keywords
        )

        for url in urls:
            try:
                response = self._request(url)
                if not response:
                    continue
                jobs = self._parse_results(response.text)
                new_count = 0
                for job in jobs:
                    if job.url not in self.seen_urls:
                        self.seen_urls.add(job.url)
                        all_jobs.append(job)
                        new_count += 1
                logger.info(f"AHS HTTP: '{url}' → {len(jobs)} found, {new_count} new")
            except Exception as e:
                logger.error(f"AHS HTTP error '{url}': {e}")

        logger.info(f"AHS HTTP total: {len(all_jobs)} unique jobs")
        return all_jobs

    def _browse_page(self, page, url: str) -> List[Job]:
        """浏览一个分类页面"""
        logger.info(f"AHS loading: {url}")
        page.goto(url, timeout=30000)
        page.wait_for_timeout(5000)

        # 滚动加载更多
        prev_count = 0
        for _ in range(5):
            page.keyboard.press('End')
            page.wait_for_timeout(2000)
            links = page.query_selector_all('a[href*="/jobs/"]')
            if len(links) == prev_count:
                break
            prev_count = len(links)

        html = page.content()
        return self._parse_results(html)

    def _search_with_form(self, page, keyword: str) -> List[Job]:
        """通过搜索表单搜索"""
        page.goto(self.base_url, timeout=30000)
        page.wait_for_timeout(3000)

        # 尝试找到搜索框并输入
        search_input = page.query_selector('input[type="text"][name*="search"], input[type="text"][id*="search"], input.search-input, #keyword')
        if search_input:
            search_input.fill(keyword)
            page.wait_for_timeout(500)
            search_input.press('Enter')
            page.wait_for_timeout(5000)

            # 滚动加载
            for _ in range(3):
                page.keyboard.press('End')
                page.wait_for_timeout(2000)

            html = page.content()
            return self._parse_results(html)

        return []

    def _parse_results(self, html: str) -> List[Job]:
        """解析搜索结果页"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        jobs = []

        # 查找所有 /jobs/ 链接
        job_links = soup.find_all('a', href=True)

        for link in job_links:
            href = link.get('href', '')
            if '/jobs/' not in href:
                continue
            # 排除非职位链接 - "other-jobs-matching" 和导航链接
            if any(x in href for x in ['/jobs/results', '/jobs/search', 'other-jobs-matching',
                                        '/jobs/pipeline', '/latest-jobs', '/hot-jobs']):
                continue

            # 构建完整URL
            if href.startswith('/'):
                job_url = f"{self.base_url}{href}"
            elif not href.startswith('http'):
                job_url = f"{self.base_url}/{href}"
            else:
                job_url = href

            # 去掉query参数以标准化URL
            job_url = job_url.split('?')[0]

            if job_url in self.seen_urls:
                continue

            # 提取标题
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            # 从附近元素提取地点和部门
            parent = link.find_parent(['div', 'li', 'tr', 'article'])
            location = 'Alberta, Canada'
            department = None

            if parent:
                text = parent.get_text(separator='\n', strip=True)
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                for line in lines:
                    # 地点通常包含 Zone 或城市名
                    if any(x in line for x in ['Zone', 'Edmonton', 'Calgary', 'Red Deer', 'Lethbridge', 'Hospital', 'Centre']):
                        if line != title:
                            location = line
                            break
                for line in lines:
                    # 部门通常包含 Nursing, Clinical 等
                    if any(x in line for x in ['Nursing', 'Clinical', 'Care', 'Support', 'Admin', 'Management']):
                        if line != title and line != location:
                            department = line
                            break

            job = Job(
                title=title,
                company=self.company_name,
                location=location,
                url=job_url,
                platform='ahs',
                scraped_at=datetime.now(),
                department=department,
            )
            jobs.append(job)

        return jobs


if __name__ == '__main__':
    """测试AHS爬虫"""
    scraper = AHSScraper(
        company_id='ahs',
        company_name='Alberta Health Services',
        url='https://careers.albertahealthservices.ca',
        timeout=30,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )

    jobs = scraper.fetch_jobs()
    print(f"\n{'='*60}")
    print(f"Found {len(jobs)} jobs total")
    print(f"{'='*60}")

    for i, job in enumerate(jobs[:30], 1):
        print(f"\n{i}. {job.title}")
        print(f"   Location: {job.location}")
        print(f"   Department: {job.department}")
        print(f"   URL: {job.url}")
