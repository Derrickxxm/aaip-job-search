"""Jobber自建网站抓取器"""
from typing import List
from datetime import datetime
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger
import re


class JobberScraper(BaseScraper):
    """Jobber Career Page抓取器"""

    def fetch_jobs(self) -> List[Job]:
        """抓取Jobber职位列表（使用Playwright + Stealth绕过Cloudflare）"""
        logger.info(f"Fetching jobs from {self.company_name} (Jobber)")

        jobs = []
        if self._playwright_disabled():
            logger.info("Playwright disabled, skipping Jobber browser scraper")
            return jobs

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return []

        try:
            from playwright_stealth import Stealth
        except ImportError:
            logger.error("playwright-stealth not installed. Run: pip install playwright-stealth")
            return []

        try:
            with sync_playwright() as p:
                # 使用non-headless模式（可见浏览器）来绕过Cloudflare
                # headless=False 可能会弹出浏览器窗口
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )
                
                # 创建Stealth对象
                stealth = Stealth()
                
                # 先创建context，再应用stealth
                context = browser.new_context()
                stealth.apply_stealth_sync(context)
                
                page = context.new_page()

                # 添加更多浏览器特征
                page.set_extra_http_headers({
                    'User-Agent': self.session.headers.get('User-Agent', ''),
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                })

                logger.info(f"Loading page: {self.url}")
                page.goto(self.url, timeout=60000)
                page.wait_for_timeout(15000)  # 增加等待时间到15秒

                # 检查是否被Cloudflare拦截
                title = page.title()
                if 'Just a moment' in title or 'Attention Required' in title:
                    logger.warning("Still blocked by Cloudflare after stealth")
                    browser.close()
                    return []

                # 获取页面HTML
                html = page.content()
                browser.close()

            from utils.html_parser import parse_html
            soup = parse_html(html)

            # 查找所有职位链接
            # 格式: /careers/{job-slug}/
            # 排除: /about/careers/ 和其他非职位链接
            all_links = soup.find_all('a', href=True)

            seen_urls = set()

            for link in all_links:
                try:
                    href = str(link.get('href', ''))

                    # 匹配职位链接模式
                    # 必须是 /careers/ 开头，后面有job slug，不能是 /about/careers/
                    if not re.match(r'^(https://www\.getjobber\.com)?/careers/[a-z0-9-]+/$', href):
                        continue

                    # 排除非职位页面
                    if '/about/careers/' in href:
                        continue

                    # 构建完整URL
                    if href.startswith('/'):
                        job_url = f"https://www.getjobber.com{href}"
                    else:
                        job_url = href

                    # 去重
                    if job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)

                    # 获取链接文本（包含职位名称和地点）
                    link_text = link.get_text(strip=True)

                    # 解析文本：格式通常是 "Job Title\n Location" 或 "Job Title Location"
                    parts = link_text.split('\n')
                    if len(parts) >= 2:
                        title = parts[0].strip()
                        location = parts[-1].strip()
                    else:
                        # 尝试从URL提取职位名称
                        slug = href.rstrip('/').split('/')[-1]
                        # 转换 slug: senior-software-engineer-remote-canada-xxx -> Senior Software Engineer
                        title_parts = slug.rsplit('-', 2)[0]  # 去掉末尾的location和id
                        title = title_parts.replace('-', ' ').title()
                        location = 'Remote, Canada'

                    # 过滤太短的标题（可能是导航链接）
                    if len(title) < 5:
                        continue

                    jobs.append(Job(
                        title=title,
                        company=self.company_name,
                        location=location,
                        url=job_url,
                        platform='Jobber',
                        scraped_at=datetime.now(),
                        department='Unknown'
                    ))
                except Exception as e:
                    logger.error(f"Error parsing link: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error with Jobber scraper: {e}")

        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
        return jobs


def test_jobber_scraper():
    """测试函数"""
    scraper = JobberScraper(
        company_id='jobber',
        company_name='Jobber',
        url='https://www.getjobber.com/about/careers/',
        timeout=10,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
    )
    jobs = scraper.fetch_jobs()
    print(f"\n找到 {len(jobs)} 个职位:\n")
    for i, job in enumerate(jobs[:15], 1):
        print(f"{i}. {job.title}")
        print(f"   地点: {job.location}")
        print(f"   链接: {job.url}\n")


if __name__ == '__main__':
    test_jobber_scraper()
