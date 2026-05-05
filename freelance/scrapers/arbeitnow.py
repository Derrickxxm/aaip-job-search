from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from freelance.models.project import FreelanceProject
from freelance.scrapers.base import FreelanceBaseScraper, logger


class ArbeitnowScraper(FreelanceBaseScraper):
    def __init__(self, config: dict):
        super().__init__(platform="arbeitnow", config=config)
        platform_config = config['platforms']['arbeitnow']
        self.api_url = platform_config['url']
        self.pages = platform_config.get('pages', 1)

    def fetch_projects(self) -> List[FreelanceProject]:
        logger.info(f"Fetching projects from Arbeitnow ({self.pages} pages)")
        projects = []
        seen_urls = set()

        for page in range(1, self.pages + 1):
            try:
                response = self.session.get(self.api_url, params={"page": page}, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
            except Exception as e:
                logger.error(f"Failed to fetch Arbeitnow page {page}: {e}")
                continue

            for item in payload.get('data', []):
                project = self._parse_item(item)
                if project and project.url not in seen_urls:
                    seen_urls.add(project.url)
                    projects.append(project)

        logger.info(f"Arbeitnow: fetched {len(projects)} projects")
        return projects

    def _parse_item(self, item: dict) -> Optional[FreelanceProject]:
        title = (item.get('title') or '').strip()
        url = item.get('url') or item.get('slug')
        if not title or not url:
            return None

        description = self._clean_html(item.get('description') or '')
        tags = item.get('tags') or []
        location = item.get('location') or "Remote" if item.get('remote') else item.get('location') or "Unknown"

        return FreelanceProject(
            title=title,
            description=description,
            platform="arbeitnow",
            url=url,
            company=item.get('company_name') or "Unknown",
            location=location,
            posted_at=self._parse_timestamp(item.get('created_at')),
            budget_type="unknown",
            tags=tags,
            project_type=self._infer_project_type(title, description),
        )

    def _clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html or '', 'html.parser')
        return soup.get_text(separator=' ', strip=True)

    def _parse_timestamp(self, value) -> datetime:
        if not value:
            return datetime.now()
        try:
            return datetime.fromtimestamp(int(value))
        except (TypeError, ValueError, OSError):
            return datetime.now()

    def _infer_project_type(self, title: str, description: str) -> str:
        text = f"{title} {description[:800]}".lower()
        if any(term in text for term in ['contract', 'contractor', 'freelance', 'consulting']):
            return "contract"
        if any(term in text for term in ['full-time', 'full time', 'permanent']):
            return "full-time"
        return "unknown"
