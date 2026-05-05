import re
from datetime import datetime
from typing import List, Optional

import feedparser
from bs4 import BeautifulSoup

from freelance.models.project import FreelanceProject
from freelance.scrapers.base import FreelanceBaseScraper, logger


class RSSSourceScraper(FreelanceBaseScraper):
    def __init__(self, config: dict):
        super().__init__(platform="rss", config=config)
        self.feeds = config['platforms']['rss']['feeds']

    def fetch_projects(self) -> List[FreelanceProject]:
        logger.info(f"Fetching projects from RSS sources ({len(self.feeds)} feeds)")
        projects = []
        seen_urls = set()

        for feed_config in self.feeds:
            feed_projects = self._parse_feed(feed_config)
            for project in feed_projects:
                if project.url in seen_urls:
                    continue
                seen_urls.add(project.url)
                projects.append(project)

        logger.info(f"RSS sources: fetched {len(projects)} projects")
        return projects

    def _parse_feed(self, feed_config: dict) -> List[FreelanceProject]:
        name = feed_config['name']
        url = feed_config['url']
        response = self._request(url)
        if not response:
            return []

        feed = feedparser.parse(response.text)
        projects = []
        for entry in feed.entries:
            try:
                project = self._parse_entry(name, entry)
                if project:
                    projects.append(project)
            except Exception as e:
                logger.debug(f"Failed to parse RSS entry from {name}: {e}")

        return projects

    def _parse_entry(self, source_name: str, entry) -> Optional[FreelanceProject]:
        title = (entry.get('title') or '').strip()
        url = entry.get('link')
        if not title or not url:
            return None

        description = self._clean_html(entry.get('summary') or entry.get('description') or '')
        budget_min, budget_max, budget_type, budget_raw = self._extract_budget(f"{title} {description}")

        return FreelanceProject(
            title=title,
            description=description,
            platform=f"rss:{source_name}",
            url=url,
            company=source_name,
            location="Remote / Worldwide",
            posted_at=self._parse_date(entry),
            budget_raw=budget_raw,
            salary_min=budget_min,
            salary_max=budget_max,
            budget_type=budget_type,
            tags=[source_name],
            project_type=self._infer_project_type(title, description),
        )

    def _clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html or '', 'html.parser')
        return soup.get_text(separator=' ', strip=True)

    def _parse_date(self, entry) -> datetime:
        parsed = entry.get('published_parsed') or entry.get('updated_parsed')
        if parsed:
            return datetime(*parsed[:6])
        return datetime.now()

    def _extract_budget(self, text: str):
        hourly_match = re.search(r'\$(\d{2,3})\s*/?\s*(?:hr|hour|h)\b', text, re.IGNORECASE)
        if hourly_match:
            rate = int(hourly_match.group(1))
            return rate, rate, "hourly", hourly_match.group(0)

        fixed_match = re.search(r'\$(\d{1,3}(?:,\d{3})+|\d{4,6})\b', text)
        if fixed_match:
            amount = int(fixed_match.group(1).replace(',', ''))
            if amount >= 1000:
                return amount, amount, "fixed", fixed_match.group(0)

        return None, None, "unknown", None

    def _infer_project_type(self, title: str, description: str) -> str:
        text = f"{title} {description[:800]}".lower()
        contract_signals = [
            'hiring', 'for hire', 'contract', 'contractor', 'freelance',
            'consulting', 'part-time', 'part time', 'gig', 'project',
        ]
        fulltime_signals = ['full-time', 'full time', 'permanent', 'employee']

        has_contract = any(term in text for term in contract_signals)
        has_fulltime = any(term in text for term in fulltime_signals)
        if has_contract and not has_fulltime:
            return "contract"
        if has_fulltime and not has_contract:
            return "full-time"
        return "unknown"
