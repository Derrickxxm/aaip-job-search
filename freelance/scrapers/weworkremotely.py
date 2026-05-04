import re
from datetime import datetime
from typing import List

import feedparser
from bs4 import BeautifulSoup

from freelance.models.project import FreelanceProject
from freelance.scrapers.base import FreelanceBaseScraper, logger


class WeWorkRemotelyScraper(FreelanceBaseScraper):
    def __init__(self, config: dict):
        super().__init__(platform="weworkremotely", config=config)
        self.feeds = config['platforms']['weworkremotely']['feeds']

    def fetch_projects(self) -> List[FreelanceProject]:
        logger.info(f"Fetching projects from WeWorkRemotely ({len(self.feeds)} feeds)")
        seen_urls = set()
        projects = []

        for feed_url in self.feeds:
            try:
                feed_projects = self._parse_feed(feed_url)
                for p in feed_projects:
                    if p.url not in seen_urls:
                        seen_urls.add(p.url)
                        projects.append(p)
            except Exception as e:
                logger.error(f"Failed to parse WWR feed {feed_url}: {e}")

        logger.info(f"WeWorkRemotely: fetched {len(projects)} projects")
        return projects

    def _parse_feed(self, feed_url: str) -> List[FreelanceProject]:
        response = self._request(feed_url)
        if not response:
            return []

        feed = feedparser.parse(response.text)
        projects = []

        for entry in feed.entries:
            try:
                project = self._parse_entry(entry)
                if project:
                    projects.append(project)
            except Exception as e:
                logger.debug(f"Failed to parse WWR entry: {e}")
                continue

        return projects

    def _parse_entry(self, entry) -> FreelanceProject:
        raw_title = entry.get('title', '').strip()
        if not raw_title:
            return None

        # Title format: "Company: Job Title"
        if ': ' in raw_title:
            company, title = raw_title.split(': ', 1)
        else:
            company = 'Unknown'
            title = raw_title

        url = entry.get('link', '')
        if not url:
            return None

        # Parse published date
        pub_date = entry.get('published_parsed')
        if pub_date:
            posted_at = datetime(*pub_date[:6])
        else:
            posted_at = datetime.now()

        # Get description and clean HTML
        description_html = entry.get('description', '') or entry.get('summary', '')
        description = self._clean_html(description_html)

        # Extract salary from description
        salary_min, salary_max, budget_type, budget_raw = self._extract_salary(description)

        # Location
        location = entry.get('region', 'Remote') or 'Remote'

        # Tags from category
        tags = []
        if hasattr(entry, 'tags'):
            tags = [t.term for t in entry.tags if hasattr(t, 'term')]

        project_type = self._infer_project_type(title, description)

        return FreelanceProject(
            title=title.strip(),
            description=description,
            platform="weworkremotely",
            url=url,
            company=company.strip(),
            location=location,
            posted_at=posted_at,
            salary_min=salary_min,
            salary_max=salary_max,
            budget_type=budget_type,
            budget_raw=budget_raw,
            tags=tags,
            project_type=project_type,
        )

    def _clean_html(self, html: str) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator=' ', strip=True)

    def _extract_salary(self, text: str):
        """Extract salary info from description text.
        Returns (salary_min, salary_max, budget_type, budget_raw)
        """
        # Pattern: $80,000 - $120,000
        range_pattern = r'\$[\d,]+\s*[-–]\s*\$[\d,]+'
        match = re.search(range_pattern, text)
        if match:
            raw = match.group()
            numbers = re.findall(r'[\d,]+', raw)
            if len(numbers) >= 2:
                low = int(numbers[0].replace(',', ''))
                high = int(numbers[1].replace(',', ''))
                # If numbers look like annual salary (> $10k), treat as annual
                if low >= 10000:
                    return low, high, "annual_salary", raw
                else:
                    return low, high, "fixed", raw

        # Pattern: $50/hr or $50/hour
        hourly_pattern = r'\$(\d+)\s*/\s*(?:hr|hour|h)\b'
        match = re.search(hourly_pattern, text, re.IGNORECASE)
        if match:
            rate = int(match.group(1))
            return rate, rate, "hourly", match.group()

        return None, None, "unknown", None

    def _infer_project_type(self, title: str, description: str) -> str:
        text = (title + " " + description[:500]).lower()
        contract_signals = ['contract', 'freelance', 'contractor', 'project-based',
                            'consulting', 'hourly', 'fixed price', 'gig']
        fulltime_signals = ['full-time', 'full time', 'permanent', 'w-2',
                            'benefits included', 'equity', '401k']

        has_contract = any(s in text for s in contract_signals)
        has_fulltime = any(s in text for s in fulltime_signals)

        if has_contract and not has_fulltime:
            return "contract"
        if has_fulltime and not has_contract:
            return "full-time"
        return "unknown"


if __name__ == '__main__':
    import yaml
    config_path = 'freelance/config/freelance.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)

    scraper = WeWorkRemotelyScraper(config)
    projects = scraper.fetch_projects()
    for p in projects[:5]:
        print(f"[{p.platform}] {p.title} @ {p.company}")
        print(f"  URL: {p.url}")
        print(f"  Salary: {p.salary_min}-{p.salary_max} ({p.budget_type})")
        print(f"  Tags: {p.tags}")
        print()
