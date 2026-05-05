"""Ashby平台抓取器（使用Playwright渲染）"""
import json
from typing import List
from datetime import datetime
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger


class AshbyScraper(BaseScraper):
    """Ashby Job Board抓取器（使用Playwright动态渲染）"""

    def fetch_jobs(self) -> List[Job]:
        """抓取Ashby Job Board"""
        logger.info(f"Fetching jobs from {self.company_name} (Ashby)")

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

                # 等待职位链接加载（更智能的等待）
                try:
                    # 从URL中提取公司名称，如 neofinancial.com -> neofinancial
                    company_slug = self.url.split('/')[-1].split('.')[0] if '/' in self.url else 'job'
                    selector = f'a[href*="/{company_slug}/"]'
                    page.wait_for_selector(selector, timeout=10000)
                    logger.info(f"Job links loaded successfully")
                except Exception as e:
                    logger.warning(f"Wait for selector failed: {e}, continuing anyway")

                page.wait_for_timeout(2000)  # 额外等待2秒确保完全加载

                # 获取页面HTML
                html = page.content()
                browser.close()

            from utils.html_parser import parse_html
            soup = parse_html(html)

            logger.debug(f"HTML loaded successfully, size: {len(html)} chars")

            # 查找所有a标签
            all_links = soup.find_all('a', href=True)
            logger.debug(f"Found {len(all_links)} total links")

            # 从URL中提取公司标识符用于匹配
            # 例如: https://jobs.ashbyhq.com/neofinancial.com -> neofinancial
            # 或: https://jobs.ashbyhq.com/neofinancial -> neofinancial
            url_parts = self.url.rstrip('/').split('/')
            company_identifier = url_parts[-1].split('.')[0] if url_parts else ''

            logger.info(f"Looking for job links matching: /{company_identifier}/")

            # 筛选包含公司标识符的职位链接（排除公司主页本身）
            job_links = []
            for link in all_links:
                href = link.get('href', '')
                # 匹配 /neofinancial/xxx 格式，但排除 /neofinancial 本身
                if href and f'/{company_identifier}/' in href and href != f'/{company_identifier}':
                    job_links.append(link)

            logger.info(f"Found {len(job_links)} job links")

            # 解析职位
            for link_elem in job_links:
                try:
                    href = str(link_elem.get('href', ''))
                    if not href:
                        continue

                    # 构建完整URL
                    if href.startswith('http'):
                        job_url = href
                    elif href.startswith('/'):
                        job_url = f'https://jobs.ashbyhq.com{href}'
                    else:
                        job_url = f'https://jobs.ashbyhq.com/{href}'

                    # 获取职位名称（链接的文本内容）
                    full_text = link_elem.get_text(strip=True)

                    # 文本格式通常是: "Job Title + Department • Location • Type • Mode"
                    # 例如: "Staff Data ScientistCore Technology • Calgary, AB • Full time • On-site"
                    # 需要分离出职位名称

                    # 尝试按 department/location 标记分割
                    if '•' in full_text:
                        parts = full_text.split('•')
                        # 第一部分包含职位名称和部门，需要进一步分离
                        title_and_dept = parts[0].strip()

                        # 常见部门关键词
                        dept_keywords = ['Core Technology', 'Technology', 'Engineering', 'Product', 'Marketing',
                                       'Finance & Accounting', 'Finance', 'Credit Risk', 'Risk', 'Credit',
                                       'People', 'Mortgages', 'Design', 'Data', 'Analytics', 'Operations', 'Core']

                        # 尝试分离职位名称和部门（从最长的关键词开始匹配，避免误匹配）
                        title = title_and_dept
                        department = 'Unknown'

                        # 按长度排序，优先匹配长关键词
                        dept_keywords_sorted = sorted(dept_keywords, key=len, reverse=True)

                        for dept_key in dept_keywords_sorted:
                            if dept_key in title_and_dept:
                                # 找到最后一次出现的位置（部门通常在最后）
                                idx = title_and_dept.rfind(dept_key)
                                if idx > 0:
                                    # 检查是否是职位名称的一部分（前面应该没有逗号或其他职位标识）
                                    # 简单判断：如果前面紧跟的不是空格，说明是粘连的部门名
                                    if idx == 0 or title_and_dept[idx-1] not in ' ,':
                                        title = title_and_dept[:idx].strip()
                                        department = title_and_dept[idx:].strip()
                                        break

                        # 提取地点（第二部分）
                        location = parts[1].strip() if len(parts) > 1 else 'Unknown'
                    else:
                        # 如果没有•分隔符，整个文本就是标题
                        title = full_text
                        department = 'Unknown'
                        location = 'Unknown'

                    # 过滤掉太短的标题（可能是噪音）
                    if not title or len(title) < 5:
                        continue

                    jobs.append(Job(
                        title=title,
                        company=self.company_name,
                        location=location,
                        url=job_url,
                        platform='Ashby',
                        scraped_at=datetime.now(),
                        department=department
                    ))
                except Exception as e:
                    logger.error(f"Error parsing job: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error with Ashby scraper: {e}")

        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
        return jobs

    def _fetch_via_http(self) -> List[Job]:
        """直接解析 Ashby 首屏 JSON 数据，避免依赖浏览器"""
        response = self._request(self.url)
        if not response:
            return []

        marker = 'window.__appData = '
        start = response.text.find(marker)
        if start < 0:
            logger.info("Ashby HTTP app data not found, trying Playwright")
            return []

        try:
            json_start = start + len(marker)
            data, _ = json.JSONDecoder().raw_decode(response.text[json_start:])
        except json.JSONDecodeError as e:
            logger.info(f"Ashby HTTP JSON parse failed: {e}, trying Playwright")
            return []

        if not isinstance(data, dict):
            logger.info("Ashby app data is not a JSON object")
            return []

        postings = data.get('jobBoard', {}).get('jobPostings', [])
        slug = data.get('organization', {}).get('hostedJobsPageSlug') or self.url.rstrip('/').split('/')[-1]

        jobs = []
        for posting in postings:
            try:
                if not posting.get('isListed', True):
                    continue

                title = (posting.get('title') or '').strip()
                posting_id = posting.get('id')
                if not title or not posting_id:
                    continue

                location = (
                    posting.get('locationName')
                    or posting.get('locationExternalName')
                    or 'Unknown'
                )
                secondary_locations = posting.get('secondaryLocations') or []
                if secondary_locations:
                    extra_locations = [
                        loc.get('locationName') or loc.get('locationExternalName')
                        for loc in secondary_locations
                        if loc.get('locationName') or loc.get('locationExternalName')
                    ]
                    if extra_locations:
                        location = '; '.join([location] + extra_locations)

                department = (
                    posting.get('departmentName')
                    or posting.get('departmentExternalName')
                    or posting.get('teamName')
                    or posting.get('teamExternalName')
                    or 'Unknown'
                )

                jobs.append(Job(
                    title=title,
                    company=self.company_name,
                    location=location,
                    url=f'https://jobs.ashbyhq.com/{slug}/{posting_id}',
                    platform='Ashby',
                    scraped_at=datetime.now(),
                    department=department
                ))
            except Exception as e:
                logger.error(f"Error parsing Ashby HTTP posting: {e}")
                continue

        return jobs


def test_ashby_scraper():
    """测试函数"""
    scraper = AshbyScraper(
        company_id='neofinancial',
        company_name='Neo Financial',
        url='https://jobs.ashbyhq.com/neofinancial',
        timeout=30,
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
    test_ashby_scraper()
