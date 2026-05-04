"""Job Bank Canada 爬虫
加拿大政府官方招聘平台 - https://www.jobbank.gc.ca
支持按关键词、地点搜索护理/医疗岗位
"""
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger


class JobBankScraper(BaseScraper):
    """Job Bank Canada 爬虫"""

    BASE_URL = "https://www.jobbank.gc.ca/jobsearch/jobsearch"

    # NOC 2021 职业代码 - 比关键词搜索精准得多
    # 使用 fn21 参数过滤
    # 现实可做的岗位（不含 NP 31302 - 需要硕士学位）
    NOC_CODES = {
        '33102': 'Health Care Aides / Nurse Aides',       # 现在就能做
        '44101': 'Home Support Workers / Caregivers',     # 低语言入口：家庭支持、陪护、caregiver
        '65201': 'Dietary Aides / Kitchen Helpers',       # 养老院/医院后勤入口
        '65310': 'Light Duty Cleaners / Housekeepers',    # 养老院/医院housekeeping入口
        '32101': 'Licensed Practical Nurses',              # 考下LPN后
        '31301': 'Registered Nurses',                      # 考下RN后
    }

    # 搜索配置 - 仅 Alberta
    SEARCH_QUERIES = [
        # Edmonton - HCA + home support/caregiver + 后勤入口 + LPN + RN
        ({'fn21': ['33102', '32101', '31301'], 'location': 'Edmonton, AB'}, 'Edmonton nursing'),
        ({'fn21': ['44101', '65201', '65310'], 'location': 'Edmonton, AB'}, 'Edmonton entry care/support'),
        # Calgary
        ({'fn21': ['33102', '32101', '31301'], 'location': 'Calgary, AB'}, 'Calgary nursing'),
        ({'fn21': ['44101', '65201', '65310'], 'location': 'Calgary, AB'}, 'Calgary entry care/support'),
        # 全 Alberta
        ({'fn21': ['33102', '32101', '31301'], 'location': 'Alberta'}, 'Alberta nursing'),
        ({'fn21': ['44101', '65201', '65310'], 'location': 'Alberta'}, 'Alberta entry care/support'),
        # 当前最现实入口关键词
        ({'term': 'caregiver', 'location': 'Alberta'}, 'caregiver AB'),
        ({'term': 'companion', 'location': 'Alberta'}, 'companion AB'),
        ({'term': 'home support worker', 'location': 'Alberta'}, 'home support worker AB'),
        ({'term': 'personal support worker', 'location': 'Alberta'}, 'personal support worker AB'),
        ({'term': 'senior care', 'location': 'Alberta'}, 'senior care AB'),
        ({'term': 'dietary aide', 'location': 'Alberta'}, 'dietary aide AB'),
        ({'term': 'kitchen helper', 'location': 'Alberta'}, 'kitchen helper AB'),
        ({'term': 'housekeeper', 'location': 'Alberta'}, 'housekeeper AB'),
        ({'term': 'cleaner', 'location': 'Alberta'}, 'cleaner AB'),
        ({'term': 'laundry aide', 'location': 'Alberta'}, 'laundry aide AB'),
        # Alberta 专科关键词补充
        ({'term': 'cardiac nurse', 'location': 'Alberta'}, 'cardiac nurse AB'),
        ({'term': 'surgical nurse', 'location': 'Alberta'}, 'surgical nurse AB'),
        ({'term': 'operating room nurse', 'location': 'Alberta'}, 'OR nurse AB'),
        ({'term': 'perioperative', 'location': 'Alberta'}, 'perioperative AB'),
        ({'term': 'vascular', 'location': 'Alberta'}, 'vascular AB'),
        ({'term': 'cath lab', 'location': 'Alberta'}, 'cath lab AB'),
    ]

    def __init__(self, company_id, company_name, url, timeout=15, user_agent=None, config=None):
        super().__init__(company_id, company_name, url, timeout, user_agent)
        self.config = config or {}
        self.seen_urls = set()  # 本次运行内去重

    def fetch_jobs(self) -> List[Job]:
        """抓取所有搜索配置的职位"""
        all_jobs = []

        for query_config, desc in self.SEARCH_QUERIES:
            try:
                jobs = self._search_jobs(query_config)
                new_count = 0
                for job in jobs:
                    if job.url not in self.seen_urls:
                        self.seen_urls.add(job.url)
                        all_jobs.append(job)
                        new_count += 1
                logger.info(f"JobBank: {desc} → {len(jobs)} found, {new_count} new")
            except Exception as e:
                logger.error(f"JobBank search error '{desc}': {e}")

        logger.info(f"JobBank total: {len(all_jobs)} unique jobs")
        return all_jobs

    def _search_jobs(self, query_config: dict, max_pages: int = 5) -> List[Job]:
        """搜索一个配置组合"""
        jobs = []

        for page in range(1, max_pages + 1):
            # 构建URL
            params = []
            if 'fn21' in query_config:
                # NOC 代码过滤 - 可以多个
                for noc in query_config['fn21']:
                    params.append(f"fn21={noc}")
            if 'term' in query_config:
                params.append(f"searchstring={query_config['term'].replace(' ', '+')}")
            params.append(f"locationstring={query_config['location'].replace(' ', '+')}")
            params.append(f"sort=D")
            params.append(f"page={page}")

            url = f"{self.BASE_URL}?{'&'.join(params)}"

            response = self._request(url)
            if not response:
                break

            page_jobs = self._parse_search_results(response.text)
            if not page_jobs:
                break  # 没有更多结果

            jobs.extend(page_jobs)

        return jobs

    def _parse_search_results(self, html: str) -> List[Job]:
        """解析搜索结果页面

        Job Bank HTML结构（实际）：
        <a class="resultJobItem" href="/jobsearch/jobposting/ID;jsessionid=...">
          <h3 class="title">
            <span class="flag">...badges...</span>
            <span class="noctitle">Job Title Here</span>
          </h3>
          <ul class="list-unstyled">
            <li class="date">March 10, 2026</li>
            <li class="business">Company Name</li>
            <li class="location">Location City (Province)</li>
            <li class="salary">Salary $xx to $yy hourly</li>
            <li class="source">Job Bank Job number: 12345</li>
          </ul>
        </a>
        """
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')

        # 找到所有职位链接
        job_links = soup.find_all('a', href=lambda h: h and '/jobsearch/jobposting/' in h)

        for link in job_links:
            href = link.get('href', '')

            # 提取职位ID
            try:
                job_id = href.split('/jobposting/')[1].split(';')[0].split('?')[0]
            except (IndexError, ValueError):
                continue

            job_url = f"https://www.jobbank.gc.ca/jobsearch/jobposting/{job_id}"

            if job_url in self.seen_urls:
                continue

            # 提取标题 - 从 span.noctitle 获取（干净的职位名）
            noctitle = link.find('span', class_='noctitle')
            if noctitle:
                title = noctitle.get_text(strip=True)
            else:
                continue

            if not title or len(title) < 3:
                continue

            # 提取公司 - li.business
            company = 'Unknown'
            biz = link.find('li', class_='business')
            if biz:
                company = biz.get_text(strip=True)

            # 提取地点 - li.location
            location = 'Unknown'
            loc = link.find('li', class_='location')
            if loc:
                location = loc.get_text(strip=True).replace('Location', '').strip()

            # 提取薪资 - li.salary
            salary = None
            sal = link.find('li', class_='salary')
            if sal:
                salary = sal.get_text(strip=True).replace('Salary', '').strip()

            job = Job(
                title=title,
                company=company,
                location=location,
                url=job_url,
                platform='jobbank',
                scraped_at=datetime.now(),
                department=salary,  # 暂用department字段存薪资信息
            )
            jobs.append(job)

        return jobs


if __name__ == '__main__':
    """测试Job Bank爬虫"""
    scraper = JobBankScraper(
        company_id='jobbank',
        company_name='Job Bank Canada',
        url='https://www.jobbank.gc.ca',
        timeout=15,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )

    jobs = scraper.fetch_jobs()
    print(f"\n{'='*60}")
    print(f"Found {len(jobs)} jobs total")
    print(f"{'='*60}")

    for i, job in enumerate(jobs[:20], 1):
        print(f"\n{i}. {job.title}")
        print(f"   Company: {job.company}")
        print(f"   Location: {job.location}")
        print(f"   Salary: {job.department}")
        print(f"   URL: {job.url}")
