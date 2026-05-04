import re
from datetime import datetime
from typing import List

from freelance.models.project import FreelanceProject
from freelance.scrapers.base import FreelanceBaseScraper, logger


class RemoteOKScraper(FreelanceBaseScraper):
    def __init__(self, config: dict):
        super().__init__(platform="remoteok", config=config)
        self.api_url = config['platforms']['remoteok']['url']

    def fetch_projects(self) -> List[FreelanceProject]:
        logger.info(f"Fetching projects from Remote OK: {self.api_url}")
        response = self._request(self.api_url)
        if not response:
            return []

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse Remote OK JSON: {e}")
            return []

        projects = []
        # Skip first element (legal notice)
        for item in data[1:]:
            try:
                project = self._parse_item(item)
                if project:
                    projects.append(project)
            except Exception as e:
                logger.debug(f"Failed to parse Remote OK item: {e}")
                continue

        logger.info(f"Remote OK: fetched {len(projects)} projects")
        return projects

    def _parse_item(self, item: dict) -> FreelanceProject:
        title = item.get('position', '').strip()
        if not title:
            return None

        # Build full URL
        url_path = item.get('url', '')
        if not url_path:
            return None
        # API may return full URL or relative path
        if url_path.startswith('http'):
            url = url_path
        else:
            url = f"https://remoteok.com{url_path}"

        # Parse posted date
        date_str = item.get('date', '')
        try:
            posted_at = datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            posted_at = datetime.now()

        # Budget type: Remote OK provides annual salary data
        salary_min = item.get('salary_min')
        salary_max = item.get('salary_max')
        if salary_min:
            salary_min = int(salary_min)
        if salary_max:
            salary_max = int(salary_max)

        budget_type = "annual_salary" if (salary_min or salary_max) else "unknown"

        # Infer project_type from tags/description
        description = item.get('description', '')
        tags = item.get('tags', []) or []
        project_type = self._infer_project_type(title, description, tags)

        return FreelanceProject(
            title=title,
            description=description,
            platform="remoteok",
            url=url,
            company=item.get('company', 'Unknown'),
            location=item.get('location', 'Remote'),
            posted_at=posted_at,
            salary_min=salary_min,
            salary_max=salary_max,
            budget_type=budget_type,
            tags=tags,
            project_type=project_type,
        )

    def _infer_project_type(self, title: str, description: str, tags: list) -> str:
        text = (title + " " + " ".join(tags) + " " + description[:500]).lower()
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

    scraper = RemoteOKScraper(config)
    projects = scraper.fetch_projects()
    for p in projects[:5]:
        print(f"[{p.platform}] {p.title} @ {p.company}")
        print(f"  URL: {p.url}")
        print(f"  Salary: {p.salary_min}-{p.salary_max} ({p.budget_type})")
        print(f"  Tags: {p.tags}")
        print()
