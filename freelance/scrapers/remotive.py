from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from freelance.models.project import FreelanceProject
from freelance.scrapers.base import FreelanceBaseScraper, logger


class RemotiveScraper(FreelanceBaseScraper):
    def __init__(self, config: dict):
        super().__init__(platform="remotive", config=config)
        platform_config = config['platforms']['remotive']
        self.api_url = platform_config['url']
        self.categories = platform_config.get('categories', [])

    def fetch_projects(self) -> List[FreelanceProject]:
        logger.info(f"Fetching projects from Remotive ({len(self.categories)} categories)")
        projects = []
        seen_urls = set()

        for category in self.categories:
            try:
                response = self.session.get(
                    self.api_url,
                    params={"category": category},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as e:
                logger.error(f"Failed to fetch Remotive category '{category}': {e}")
                continue

            for item in payload.get('jobs', []):
                project = self._parse_item(item)
                if project and project.url not in seen_urls:
                    seen_urls.add(project.url)
                    projects.append(project)

        logger.info(f"Remotive: fetched {len(projects)} projects")
        return projects

    def _parse_item(self, item: dict) -> Optional[FreelanceProject]:
        title = (item.get('title') or '').strip()
        url = item.get('url')
        if not title or not url:
            return None

        description = self._clean_html(item.get('description') or '')
        salary = item.get('salary')
        posted_at = self._parse_date(item.get('publication_date'))

        tags = [item.get('category', '')]
        tags.extend(item.get('tags') or [])
        tags = [tag for tag in tags if tag]

        return FreelanceProject(
            title=title,
            description=description,
            platform="remotive",
            url=url,
            company=item.get('company_name') or "Unknown",
            location=item.get('candidate_required_location') or "Remote",
            posted_at=posted_at,
            budget_raw=salary,
            budget_type="annual_salary" if salary else "unknown",
            tags=tags,
            project_type=self._infer_project_type(title, description),
        )

    def _clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html or '', 'html.parser')
        return soup.get_text(separator=' ', strip=True)

    def _parse_date(self, value: str) -> datetime:
        if not value:
            return datetime.now()
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            return datetime.now()

    def _infer_project_type(self, title: str, description: str) -> str:
        text = f"{title} {description[:800]}".lower()
        if any(term in text for term in ['contract', 'contractor', 'freelance', 'consulting']):
            return "contract"
        if any(term in text for term in ['full-time', 'full time', 'permanent']):
            return "full-time"
        return "unknown"
