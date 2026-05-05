from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from freelance.models.project import FreelanceProject
from freelance.scrapers.base import FreelanceBaseScraper, logger


class FreelancerScraper(FreelanceBaseScraper):
    def __init__(self, config: dict):
        super().__init__(platform="freelancer", config=config)
        platform_config = config['platforms']['freelancer']
        self.api_url = platform_config['url']
        self.limit = platform_config.get('limit', 100)
        self.queries = platform_config.get('queries', [])

    def fetch_projects(self) -> List[FreelanceProject]:
        logger.info(f"Fetching projects from Freelancer ({len(self.queries)} queries)")
        projects = []
        seen_urls: Set[str] = set()

        for query in self.queries:
            for project in self._fetch_query(query):
                if project.url in seen_urls:
                    continue
                seen_urls.add(project.url)
                projects.append(project)

        logger.info(f"Freelancer: fetched {len(projects)} projects")
        return projects

    def _fetch_query(self, query: str) -> List[FreelanceProject]:
        params = {
            "limit": self.limit,
            "full_description": "true",
            "job_details": "true",
            "query": query,
        }
        try:
            response = self.session.get(self.api_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch Freelancer query '{query}': {e}")
            return []

        items = payload.get('result', {}).get('projects', [])
        projects = []
        for item in items:
            try:
                project = self._parse_item(item)
                if project:
                    projects.append(project)
            except Exception as e:
                logger.debug(f"Failed to parse Freelancer item: {e}")

        return projects

    def _parse_item(self, item: Dict[str, Any]) -> Optional[FreelanceProject]:
        title = (item.get('title') or '').strip()
        if not title:
            return None

        url = self._build_url(item)
        if not url:
            return None

        budget = item.get('budget') or {}
        minimum = budget.get('minimum')
        maximum = budget.get('maximum')
        budget_type = self._budget_type(item)
        currency = self._currency_code(budget)
        budget_raw = self._budget_raw(minimum, maximum, currency)

        tags = []
        for job in item.get('jobs') or []:
            if isinstance(job, dict) and job.get('name'):
                tags.append(job['name'])

        posted_at = self._parse_time(item)
        owner = item.get('owner_id') or item.get('upgrades', {}).get('user_id')

        return FreelanceProject(
            title=title,
            description=item.get('description') or item.get('preview_description') or '',
            platform="freelancer",
            url=url,
            company=f"Freelancer client {owner}" if owner else "Freelancer client",
            location="Remote / Worldwide",
            posted_at=posted_at,
            budget_raw=budget_raw,
            salary_min=self._safe_int(minimum),
            salary_max=self._safe_int(maximum),
            budget_type=budget_type,
            tags=tags,
            project_type="contract",
            client_info=item.get('owner_id') and f"owner_id={item.get('owner_id')}",
        )

    def _build_url(self, item: Dict[str, Any]) -> Optional[str]:
        seo_url = item.get('seo_url')
        if seo_url:
            if seo_url.startswith('http'):
                return seo_url
            return f"https://www.freelancer.com/projects/{seo_url.strip('/')}"

        project_id = item.get('id')
        if project_id:
            return f"https://www.freelancer.com/projects/{project_id}"

        return None

    def _budget_type(self, item: Dict[str, Any]) -> str:
        text = f"{item.get('type', '')} {item.get('hourly_project_info', '')}".lower()
        if 'hourly' in text:
            return "hourly"
        return "fixed"

    def _currency_code(self, budget: Dict[str, Any]) -> str:
        currency = budget.get('currency') or {}
        if isinstance(currency, dict):
            return currency.get('code') or currency.get('sign') or ''
        return str(currency) if currency else ''

    def _budget_raw(self, minimum: Any, maximum: Any, currency: str) -> Optional[str]:
        if minimum is None and maximum is None:
            return None
        prefix = f"{currency} " if currency else ""
        if minimum is not None and maximum is not None:
            return f"{prefix}{minimum}-{maximum}"
        return f"{prefix}{minimum or maximum}"

    def _parse_time(self, item: Dict[str, Any]) -> datetime:
        timestamp = item.get('time_submitted') or item.get('submitdate')
        if timestamp:
            try:
                return datetime.fromtimestamp(int(timestamp))
            except (TypeError, ValueError, OSError):
                return datetime.now()
        return datetime.now()

    def _safe_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None
