# AAIP Job Aggregator - 技术设计文档

> 版本: v1.1
> 日期: 2026-01-20
> 作者: Claude Code

---

## 目录

1. [项目概述](#1-项目概述)
2. [P0公司平台分析](#2-p0公司平台分析)
3. [详细设计](#3-详细设计)
4. [配置更新](#4-配置更新)
5. [main.py修改](#5-mainpy修改)
6. [测试计划](#6-测试计划)

---

## 1. 项目概述

### 1.1 P0 公司覆盖状态

| 公司 | 平台 | 爬虫文件 | 状态 | 可直接使用 |
|------|------|----------|------|------------|
| Benevity | Greenhouse | `greenhouse.py` | ✅ 已实现 | ✅ |
| Neo Financial | Ashby | `ashby.py` | ✅ 已实现 | ✅ |
| Attabotics | Lever | `lever.py` | 📝 设计完成 | ✅ |
| Symend | JazzHR | `jazzhr.py` | 📝 设计完成 | ✅ |
| Helcim | BambooHR | `bamboohr.py` | 📝 设计完成 | ✅ |
| Jobber | Custom | `jobber.py` | 📝 设计完成 | ✅ |

### 1.2 新增爬虫清单

```
scrapers/
├── base.py          # 基类（已有）
├── greenhouse.py    # ✅ 已实现
├── ashby.py         # ✅ 已实现
├── lever.py         # 📝 待创建
├── jazzhr.py        # 📝 待创建
├── bamboohr.py      # 📝 待创建
└── jobber.py        # 📝 待创建
```

---

## 2. P0公司平台分析

### 2.1 Attabotics - Lever 平台

**招聘页面**: https://attabotics.com/careers/
**实际职位列表**: https://jobs.lever.co/attabotics/

**DOM 结构**:
```html
<div class="postings-wrapper">
  <div class="posting" data-qa="posting-item">
    <a class="posting-title" href="/attabotics/{job-id}">
      <h5>Senior Software Engineer</h5>
    </a>
    <div class="posting-categories">
      <span class="sort-by-location posting-category">Calgary, AB</span>
      <span class="sort-by-team posting-category">Engineering</span>
    </div>
  </div>
</div>
```

---

### 2.2 Symend - JazzHR 平台

**招聘页面**: https://symend.com/company/careers/

**DOM 结构**:
```html
<div id="resumator-jobs">
  <div class="resumator-job">
    <a class="resumator-job-link" href="https://symend.applytojob.com/apply/xxx">
      <span class="resumator-job-title">Senior Backend Engineer</span>
    </a>
    <span class="resumator-job-info">Calgary, AB | Engineering</span>
  </div>
</div>
```

---

### 2.3 Helcim - BambooHR 平台

**招聘页面**: https://www.helcim.com/careers/job-openings/

**实际分析结果** (Playwright 抓取):
```html
<li class="BambooHR-ATS-Department-Item">
  <div class="BambooHR-ATS-Department-Header">Software Development</div>
  <ul class="BambooHR-ATS-Jobs-List">
    <li class="BambooHR-ATS-Jobs-Item">
      <a href="//helcim.bamboohr.com/careers/308">Manager, Software Engineering</a>
      <span class="BambooHR-ATS-Location">Calgary, AB</span>
    </li>
    <li class="BambooHR-ATS-Jobs-Item">
      <a href="//helcim.bamboohr.com/careers/314">Principal Engineer</a>
      <span class="BambooHR-ATS-Location">Calgary, AB</span>
    </li>
  </ul>
</li>
```

**关键选择器**:
- 职位项: `li.BambooHR-ATS-Jobs-Item`
- 职位链接: `li.BambooHR-ATS-Jobs-Item > a`
- 地点: `span.BambooHR-ATS-Location`
- 部门: `.BambooHR-ATS-Department-Header`

---

### 2.4 Jobber - 自建网站

**招聘页面**: https://www.getjobber.com/about/careers/

**实际分析结果** (Playwright 抓取):
```
职位链接格式: https://www.getjobber.com/careers/{job-slug}/
链接文本格式: "Job Title\n Location"
```

**示例职位**:
- `Senior Software Engineer` -> `/careers/senior-software-engineer-remote-canada-8cc365d8/`
- `Staff Software Engineer` -> `/careers/staff-software-engineer-remote-canada-9a73f2a3/`
- `Staff Data Engineer` -> `/careers/staff-data-engineer-remote-canada-304636d8/`

**关键选择器**:
- 职位链接: `a[href*="/careers/"][href$="/"]` (排除 `/about/careers/`)
- 链接文本包含职位名称和地点，用换行符分隔

---

## 3. 详细设计

### 3.1 Lever 爬虫 (Attabotics)

**文件**: `scrapers/lever.py`

```python
"""Lever平台抓取器"""
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger


class LeverScraper(BaseScraper):
    """Lever Job Board抓取器"""

    def fetch_jobs(self) -> List[Job]:
        """抓取Lever Job Board"""
        logger.info(f"Fetching jobs from {self.company_name} (Lever)")

        response = self._request(self.url)
        if not response:
            return []

        soup = BeautifulSoup(response.text, 'lxml')
        jobs = []

        # 查找所有职位卡片
        posting_elements = soup.find_all('div', class_='posting')

        for elem in posting_elements:
            try:
                # 提取职位链接和标题
                title_link = elem.find('a', class_='posting-title')
                if not title_link:
                    continue

                title = title_link.get_text(strip=True)
                job_url = title_link.get('href', '')

                # 补全URL
                if job_url and not job_url.startswith('http'):
                    job_url = f"https://jobs.lever.co{job_url}"

                # 提取分类信息
                categories = elem.find('div', class_='posting-categories')
                location = 'Unknown'
                department = 'Unknown'

                if categories:
                    loc_span = categories.find('span', class_='sort-by-location')
                    if loc_span:
                        location = loc_span.get_text(strip=True)

                    team_span = categories.find('span', class_='sort-by-team')
                    if team_span:
                        department = team_span.get_text(strip=True)

                jobs.append(Job(
                    title=title,
                    company=self.company_name,
                    location=location,
                    url=job_url,
                    platform='Lever',
                    scraped_at=datetime.now(),
                    department=department
                ))
            except Exception as e:
                logger.error(f"Error parsing job element: {e}")
                continue

        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
        return jobs


def test_lever_scraper():
    """测试函数"""
    scraper = LeverScraper(
        company_id='attabotics',
        company_name='Attabotics',
        url='https://jobs.lever.co/attabotics/',
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
    test_lever_scraper()
```

---

### 3.2 JazzHR 爬虫 (Symend)

**文件**: `scrapers/jazzhr.py`

```python
"""JazzHR(Resumator)平台抓取器"""
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger


class JazzHRScraper(BaseScraper):
    """JazzHR (Resumator) Job Board抓取器"""

    def fetch_jobs(self) -> List[Job]:
        """抓取JazzHR Job Board"""
        logger.info(f"Fetching jobs from {self.company_name} (JazzHR)")

        response = self._request(self.url)
        if not response:
            return []

        soup = BeautifulSoup(response.text, 'lxml')
        jobs = []

        # 查找职位容器
        jobs_container = soup.find('div', id='resumator-jobs')
        if not jobs_container:
            logger.warning(f"No resumator-jobs container found for {self.company_name}")
            return []

        # 查找所有职位项
        job_elements = jobs_container.find_all('div', class_='resumator-job')

        for elem in job_elements:
            try:
                # 提取职位链接
                link_elem = elem.find('a', class_='resumator-job-link')
                if not link_elem:
                    continue

                job_url = link_elem.get('href', '')

                # 提取职位标题
                title_elem = elem.find('span', class_='resumator-job-title')
                title = title_elem.get_text(strip=True) if title_elem else 'Unknown'

                # 提取职位信息 (地点 | 部门)
                info_elem = elem.find('span', class_='resumator-job-info')
                location = 'Unknown'
                department = 'Unknown'

                if info_elem:
                    info_text = info_elem.get_text(strip=True)
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

        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
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
```

---

### 3.3 BambooHR 爬虫 (Helcim)

**文件**: `scrapers/bamboohr.py`

```python
"""BambooHR平台抓取器"""
from typing import List
from datetime import datetime
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger


class BambooHRScraper(BaseScraper):
    """BambooHR Job Board抓取器（需要Playwright渲染）"""

    def fetch_jobs(self) -> List[Job]:
        """抓取BambooHR嵌入式职位列表"""
        logger.info(f"Fetching jobs from {self.company_name} (BambooHR)")

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
                page.wait_for_timeout(3000)  # 等待BambooHR widget加载

                # 获取页面HTML
                html = page.content()
                browser.close()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')

            # 当前部门（用于跟踪）
            current_department = 'Unknown'

            # 遍历所有部门
            department_items = soup.find_all('li', class_='BambooHR-ATS-Department-Item')

            for dept_item in department_items:
                # 获取部门名称
                dept_header = dept_item.find('div', class_='BambooHR-ATS-Department-Header')
                if dept_header:
                    current_department = dept_header.get_text(strip=True)

                # 获取该部门下的所有职位
                job_items = dept_item.find_all('li', class_='BambooHR-ATS-Jobs-Item')

                for job_item in job_items:
                    try:
                        # 提取职位链接和标题
                        link_elem = job_item.find('a')
                        if not link_elem:
                            continue

                        title = link_elem.get_text(strip=True)
                        job_url = link_elem.get('href', '')

                        # 补全URL
                        if job_url.startswith('//'):
                            job_url = f"https:{job_url}"
                        elif job_url and not job_url.startswith('http'):
                            job_url = f"https://helcim.bamboohr.com{job_url}"

                        # 提取地点
                        location_elem = job_item.find('span', class_='BambooHR-ATS-Location')
                        location = location_elem.get_text(strip=True) if location_elem else 'Calgary, AB'

                        jobs.append(Job(
                            title=title,
                            company=self.company_name,
                            location=location,
                            url=job_url,
                            platform='BambooHR',
                            scraped_at=datetime.now(),
                            department=current_department
                        ))
                    except Exception as e:
                        logger.error(f"Error parsing job item: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error with BambooHR scraper: {e}")

        logger.info(f"Found {len(jobs)} jobs from {self.company_name}")
        return jobs


def test_bamboohr_scraper():
    """测试函数"""
    scraper = BambooHRScraper(
        company_id='helcim',
        company_name='Helcim',
        url='https://www.helcim.com/careers/job-openings/',
        timeout=30,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
    )
    jobs = scraper.fetch_jobs()
    print(f"\n找到 {len(jobs)} 个职位:\n")
    for i, job in enumerate(jobs[:15], 1):
        print(f"{i}. {job.title}")
        print(f"   地点: {job.location}")
        print(f"   部门: {job.department}")
        print(f"   链接: {job.url}\n")


if __name__ == '__main__':
    test_bamboohr_scraper()
```

---

### 3.4 Jobber 爬虫

**文件**: `scrapers/jobber.py`

```python
"""Jobber自建网站抓取器"""
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models.job import Job
from utils.logger import logger
import re


class JobberScraper(BaseScraper):
    """Jobber Career Page抓取器"""

    def fetch_jobs(self) -> List[Job]:
        """抓取Jobber职位列表"""
        logger.info(f"Fetching jobs from {self.company_name} (Jobber)")

        response = self._request(self.url)
        if not response:
            return []

        soup = BeautifulSoup(response.text, 'lxml')
        jobs = []

        # 查找所有职位链接
        # 格式: /careers/{job-slug}/
        # 排除: /about/careers/ 和其他非职位链接
        all_links = soup.find_all('a', href=True)

        seen_urls = set()

        for link in all_links:
            try:
                href = link.get('href', '')

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
```

---

## 4. 配置更新

### 4.1 companies.json 完整配置

```json
{
  "p0_companies": [
    {
      "id": "benevity",
      "name": "Benevity",
      "platform": "greenhouse",
      "careers_url": "https://job-boards.greenhouse.io/embed/job_board?for=benevity",
      "risk_score": 1,
      "tech_match": 3,
      "notes": "Ruby on Rails为主，但有后端通用岗位",
      "status": "active"
    },
    {
      "id": "neofinancial",
      "name": "Neo Financial",
      "platform": "ashby",
      "careers_url": "https://jobs.ashbyhq.com/neofinancial.com",
      "risk_score": 2,
      "tech_match": 5,
      "notes": "Java + Kotlin + Python，完美匹配",
      "status": "active"
    },
    {
      "id": "helcim",
      "name": "Helcim",
      "platform": "bamboohr",
      "careers_url": "https://www.helcim.com/careers/job-openings/",
      "risk_score": 1,
      "tech_match": 5,
      "notes": "支付平台 + Java，完美匹配",
      "status": "active"
    },
    {
      "id": "symend",
      "name": "Symend",
      "platform": "jazzhr",
      "careers_url": "https://symend.com/company/careers/",
      "risk_score": 2,
      "tech_match": 4,
      "notes": "Python + Java + 数据平台",
      "status": "active"
    },
    {
      "id": "attabotics",
      "name": "Attabotics",
      "platform": "lever",
      "careers_url": "https://jobs.lever.co/attabotics/",
      "risk_score": 2,
      "tech_match": 3,
      "notes": "偏机器人/嵌入式，有后端岗",
      "status": "active"
    },
    {
      "id": "jobber",
      "name": "Jobber",
      "platform": "jobber",
      "careers_url": "https://www.getjobber.com/about/careers/",
      "risk_score": 1,
      "tech_match": 3,
      "notes": "Ruby on Rails为主，后端通用",
      "status": "active"
    }
  ]
}
```

---

## 5. main.py 修改

在 `main.py` 中添加新平台的导入和判断逻辑：

```python
# 新增导入
from scrapers.lever import LeverScraper
from scrapers.jazzhr import JazzHRScraper
from scrapers.bamboohr import BambooHRScraper
from scrapers.jobber import JobberScraper

# 在 platform 判断中添加
elif platform == 'lever':
    scraper = LeverScraper(
        company_id=company_id,
        company_name=company_name,
        url=url,
        timeout=request_timeout,
        user_agent=request_user_agent
    )
elif platform == 'jazzhr':
    scraper = JazzHRScraper(
        company_id=company_id,
        company_name=company_name,
        url=url,
        timeout=request_timeout,
        user_agent=request_user_agent
    )
elif platform == 'bamboohr':
    scraper = BambooHRScraper(
        company_id=company_id,
        company_name=company_name,
        url=url,
        timeout=request_timeout,
        user_agent=request_user_agent
    )
elif platform == 'jobber':
    scraper = JobberScraper(
        company_id=company_id,
        company_name=company_name,
        url=url,
        timeout=request_timeout,
        user_agent=request_user_agent
    )
```

---

## 6. 测试计划

### 6.1 单元测试

| 爬虫 | 测试命令 | 预期结果 |
|------|----------|----------|
| Lever | `python scrapers/lever.py` | 显示 Attabotics 职位 |
| JazzHR | `python scrapers/jazzhr.py` | 显示 Symend 职位 |
| BambooHR | `python scrapers/bamboohr.py` | 显示 Helcim 职位 |
| Jobber | `python scrapers/jobber.py` | 显示 Jobber 职位 |

### 6.2 集成测试

```bash
# 1. 清理历史数据
bash scripts/clean_history.sh

# 2. 运行主程序
python main.py

# 3. 检查输出
cat /Users/xxm/projects/QuantEngine_markdown_file/$(date +%Y-%m-%d)_匹配职位.md

# 4. 检查日志
tail -100 logs/scraper.log
```

### 6.3 验收清单

- [ ] Lever 爬虫正常抓取 Attabotics 职位
- [ ] JazzHR 爬虫正常抓取 Symend 职位
- [ ] BambooHR 爬虫正常抓取 Helcim 职位
- [ ] Jobber 爬虫正常抓取 Jobber 职位
- [ ] 职位过滤规则正常工作
- [ ] 去重机制正常工作
- [ ] MD报告正确生成

---

## 附录: 平台识别速查表

| URL 特征 | 平台 | 爬虫文件 |
|----------|------|----------|
| `greenhouse.io` | Greenhouse | `greenhouse.py` |
| `ashbyhq.com` | Ashby | `ashby.py` |
| `lever.co` | Lever | `lever.py` |
| 页面含 `resumator-jobs` | JazzHR | `jazzhr.py` |
| 页面含 `BambooHR-ATS` | BambooHR | `bamboohr.py` |
| `getjobber.com/careers/` | Jobber | `jobber.py` |

---

*文档结束 - 版本 v1.1*
