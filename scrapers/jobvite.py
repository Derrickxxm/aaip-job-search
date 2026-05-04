"""Jobvite平台抓取器"""
from typing import List
from datetime import datetime
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger


class JobviteScraper(BaseScraper):
    """Jobvite Job Board抓取器（支持直接API调用和Playwright备选）"""

    def fetch_jobs(self) -> List[Job]:
        """抓取Jobvite Job Board"""
        logger.info(f"Fetching jobs from {self.company_name} (Jobvite)")

        jobs = []

        # 方法1: 尝试直接API调用
        api_jobs = self._fetch_via_api()
        if api_jobs:
            return api_jobs

        # 方法2: 直接解析公开 HTML
        html_jobs = self._fetch_via_http()
        if html_jobs:
            return html_jobs

        # 方法3: 使用Playwright绕过Cloudflare
        return self._fetch_via_playwright()

    def _fetch_via_api(self) -> List[Job]:
        """通过API直接获取职位数据"""
        try:
            # 提取company_id (drillinginfo from URL)
            # URL格式: https://jobs.jobvite.com/drillinginfo/
            company_id = self.url.split('/')[-2] if self.url.endswith('/') else self.url.split('/')[-1]

            api_url = f"https://jobs.jobvite.com/api/jobs/{company_id}"

            logger.info(f"Trying API: {api_url}")
            response = self._request(api_url)

            if not response:
                logger.info("API request failed, trying HTML")
                return []

            if response.status_code == 200:
                data = response.json()
                logger.info(f"API response type: {type(data)}, keys: {list(data.keys())[:5]}")
                return self._parse_jobvite_json(data)
            else:
                logger.info(f"API returned status {response.status_code}, trying HTML")
                return []

        except Exception as e:
            logger.info(f"API method failed: {e}, trying HTML")
            return []

    def _fetch_via_http(self) -> List[Job]:
        """通过公开 HTML 页面获取职位数据"""
        response = self._request(self.url)
        if not response:
            return []

        try:
            from utils.html_parser import parse_html
            soup = parse_html(response.text)
            jobs = self._parse_jobvite_html(soup)
            if jobs:
                logger.info(f"Found {len(jobs)} jobs in Jobvite HTML")
            return jobs
        except Exception as e:
            logger.info(f"HTML method failed: {e}")
            return []

    def _fetch_via_playwright(self) -> List[Job]:
        """使用Playwright绕过Cloudflare获取职位数据"""
        jobs = []

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
                page.wait_for_timeout(5000)  # 等待Cloudflare验证和页面加载

                # 获取页面HTML
                html = page.content()
                browser.close()

            from utils.html_parser import parse_html
            soup = parse_html(html)

            # 尝试从HTML中查找职位数据
            # Jobvite通常会将数据嵌入在script标签中
            for script in soup.find_all('script'):
                content = script.get_text()
                if 'job' in content.lower() and ('open' in content.lower() or 'posting' in content.lower()):
                    try:
                        import json
                        # 尝试解析JSON
                        if '{' in content:
                            # 找到JSON开始
                            start = content.find('{')
                            # 找到匹配的结束
                            brace_count = 0
                            for i in range(start, len(content)):
                                if content[i] == '{':
                                    brace_count += 1
                                elif content[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_str = content[start:i+1]
                                        data = json.loads(json_str)
                                        return self._parse_jobvite_json(data)
                    except Exception as e:
                        logger.debug(f"Failed to parse script JSON: {e}")
                        continue

            # 如果没找到JSON数据，尝试解析HTML中的职位链接
            return self._parse_jobvite_html(soup)

        except Exception as e:
            logger.error(f"Error with Jobvite Playwright scraper: {e}")
            return []

        return jobs

    def _parse_jobvite_json(self, data: dict) -> List[Job]:
        """解析Jobvite API返回的JSON数据"""
        jobs = []

        try:
            # Jobvite API可能返回不同的结构
            # 常见格式1: { "jobs": [...] }
            # 常见格式2: { "open": [...] } or { "postings": [...] }
            job_list = []

            for key in ['jobs', 'open', 'postings', 'listings']:
                if key in data and isinstance(data[key], list):
                    job_list = data[key]
                    break

            if not job_list:
                logger.info(f"No job list found in JSON data. Keys: {list(data.keys())}")
                return []

            logger.info(f"Found {len(job_list)} jobs in JSON")

            for job_data in job_list:
                try:
                    # 提取职位信息（根据实际API结构调整）
                    title = job_data.get('title') or job_data.get('jobTitle') or 'Unknown'

                    # 提取位置
                    location_data = job_data.get('location') or job_data.get('jobLocation') or {}
                    if isinstance(location_data, dict):
                        location = location_data.get('city', 'Unknown')
                        state = location_data.get('state', '')
                        country = location_data.get('country', '')
                        if state:
                            location += f', {state}'
                        if country:
                            location += f', {country}'
                    else:
                        location = str(location_data) if location_data else 'Unknown'

                    # 提取URL
                    job_url = job_data.get('url') or job_data.get('applyUrl') or job_data.get('jobUrl') or ''

                    # 如果URL是相对路径，补全
                    if job_url and not job_url.startswith('http'):
                        company_id = self.url.split('/')[-2] if self.url.endswith('/') else self.url.split('/')[-1]
                        job_url = f"https://jobs.jobvite.com/{company_id}{job_url}"

                    # 提取部门
                    department = job_data.get('department') or job_data.get('category') or 'Unknown'

                    if not title or title == 'Unknown':
                        continue

                    jobs.append(Job(
                        title=title,
                        company=self.company_name,
                        location=location,
                        url=job_url,
                        platform='Jobvite',
                        scraped_at=datetime.now(),
                        department=department
                    ))
                except Exception as e:
                    logger.error(f"Error parsing job data: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing Jobvite JSON: {e}")

        return jobs

    def _parse_jobvite_html(self, soup) -> List[Job]:
        """解析Jobvite HTML页面中的职位"""
        jobs = []

        try:
            # 查找所有职位项（使用新的结构）
            # Jobvite使用 jv-job-item 类
            job_items = soup.find_all('div', class_='jv-job-item')

            for job_item in job_items:
                try:
                    # 提取职位链接
                    link_elem = job_item.find('a', href=True)
                    if not link_elem:
                        continue

                    href = link_elem.get('href', '')
                    title = link_elem.get_text(strip=True)

                    # 过滤职位链接
                    if not title or len(title) < 5:
                        continue

                    # 补全URL
                    if href.startswith('http'):
                        job_url = href
                    elif href.startswith('/'):
                        job_url = f"https://jobs.jobvite.com{href}"
                    else:
                        continue

                    # 提取地点（从 jv-job-list-location 类中）
                    location = 'Unknown'
                    location_elem = job_item.find('div', class_='jv-job-list-location')
                    if location_elem:
                        location_text = location_elem.get_text(' ', strip=True)
                        # 清理文本（移除多余的空格和换行）
                        location_text = ' '.join(location_text.split())
                        if location_text:
                            location = location_text
                        else:
                            location = 'Unknown'
                    else:
                        # 尝试从父级元素提取
                        parent = link_elem.parent
                        if parent:
                            parent_text = parent.get_text(' ', strip=True)
                            # 简单的地点识别
                            if 'alberta' in parent_text.lower():
                                location = 'Alberta, Canada'
                            elif 'calgary' in parent_text.lower():
                                location = 'Calgary, Alberta, Canada'
                            elif 'remote' in parent_text.lower():
                                location = 'Remote'

                    # 提取部门（如果有的话）
                    department = 'Unknown'

                    jobs.append(Job(
                        title=title,
                        company=self.company_name,
                        location=location,
                        url=job_url,
                        platform='Jobvite',
                        scraped_at=datetime.now(),
                        department=department
                    ))
                except Exception as e:
                    logger.error(f"Error parsing job item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing Jobvite HTML: {e}")

        return jobs


def test_jobvite_scraper():
    """测试函数"""
    scraper = JobviteScraper(
        company_id='enverus',
        company_name='Enverus',
        url='https://jobs.jobvite.com/drillinginfo/',
        timeout=30,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
    )

    jobs = scraper.fetch_jobs()
    print(f"\n找到 {len(jobs)} 个职位:\n")
    for i, job in enumerate(jobs[:10], 1):
        print(f"{i}. {job.title}")
        print(f"   地点: {job.location}")
        print(f"   部门: {job.department}")
        print(f"   链接: {job.url}\n")

    if len(jobs) > 10:
        print(f"... 还有 {len(jobs) - 10} 个职位未显示")


if __name__ == '__main__':
    test_jobvite_scraper()
