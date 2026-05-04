"""JazzHR(Resumator)平台抓取器"""
from typing import List
from datetime import datetime
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger


class JazzHRScraper(BaseScraper):
    """JazzHR (Resumator) Job Board抓取器"""

    def fetch_jobs(self) -> List[Job]:
        """抓取JazzHR Job Board（使用Playwright动态渲染）"""
        logger.info(f"Fetching jobs from {self.company_name} (JazzHR)")

        jobs = self._fetch_via_http()
        if jobs:
            logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
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
                page.wait_for_timeout(5000)  # 等待JazzHR widget加载

                # 获取页面HTML
                html = page.content()
                browser.close()

            from utils.html_parser import parse_html
            soup = parse_html(html)

            # 查找职位容器
            jobs_container = soup.find('div', id='resumator-jobs')
            if not jobs_container:
                logger.warning(f"No resumator-jobs container found for {self.company_name}")
                return []

            # 查找所有职位项
            job_elements = jobs_container.find_all('div', class_='resumator-job')

            for elem in job_elements:
                try:
                    # 提取职位标题（可能在div或span中）
                    title_elem = elem.find('div', class_='resumator-job-title')
                    if not title_elem:
                        title_elem = elem.find('span', class_='resumator-job-title')
                    title = title_elem.get_text(strip=True) if title_elem else 'Unknown'

                    # 提取职位链接
                    link_elem = elem.find('a', class_='resumator-job-link')
                    job_url = link_elem.get('href', '') if link_elem else ''

                    if not job_url:
                        continue

                    # 提取地点（可能在resumator-job-info中）
                    info_elem = elem.find('div', class_='resumator-job-info')
                    location = 'Unknown'
                    department = 'Unknown'

                    if info_elem:
                        info_text = info_elem.get_text(strip=True)
                        # 移除"Location:"标签
                        info_text = info_text.replace('Location:', '').strip()
                        if '|' in info_text:
                            parts = info_text.split('|')
                            location = parts[0].strip()
                            department = parts[1].strip() if len(parts) > 1 else 'Unknown'
                        else:
                            location = info_text

                    jobs.append(Job(
                        title=title,
                        company=self.company_name,
                        location=location,
                        url=job_url,
                        platform='JazzHR',
                        scraped_at=datetime.now(),
                        department=department
                    ))
                except Exception as e:
                    logger.error(f"Error parsing job element: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error with JazzHR scraper: {e}")

        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
        return jobs

    def _fetch_via_http(self) -> List[Job]:
        """直接抓取 JazzHR / applytojob 公开职位列表"""
        urls = [
            self.url,
            f"https://{self.company_id}.applytojob.com/apply/jobs/",
        ]
        if self.company_id == 'symend':
            urls.append("https://symend.applytojob.com/apply/jobs/")

        for url in urls:
            response = self._request(url)
            if not response:
                continue

            from utils.html_parser import parse_html
            soup = parse_html(response.text)
            jobs = self._parse_applytojob(soup, url)
            if jobs:
                return jobs

        return []

    def _parse_applytojob(self, soup, source_url: str) -> List[Job]:
        """解析 applytojob.com 表格列表"""
        jobs = []
        seen_urls = set()
        base_url = source_url.split('/apply/')[0] if '/apply/' in source_url else source_url.rstrip('/')

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/apply/jobs/details/' not in href:
                continue

            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            if href.startswith('http'):
                job_url = href
            elif href.startswith('/'):
                job_url = f"{base_url}{href}"
            else:
                job_url = f"{base_url}/{href}"
            job_url = job_url.split('?')[0]

            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)

            location = 'Unknown'
            row = link.find_parent('tr')
            if row:
                cells = [cell.get_text(' ', strip=True) for cell in row.find_all('td')]
                for cell in cells:
                    if cell and cell != title:
                        location = cell
                        break

            jobs.append(Job(
                title=title,
                company=self.company_name,
                location=location,
                url=job_url,
                platform='JazzHR',
                scraped_at=datetime.now(),
                department='Unknown'
            ))

        return jobs


def test_jazzhr_scraper():
    """测试函数"""
    scraper = JazzHRScraper(
        company_id='symend',
        company_name='Symend',
        url='https://symend.com/company/careers/',
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
    test_jazzhr_scraper()
