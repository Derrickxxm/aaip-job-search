from abc import ABC, abstractmethod
from typing import List, Optional

import requests

from freelance.models.project import FreelanceProject
from freelance.utils.logger import get_logger

logger = get_logger(__name__)


class FreelanceBaseScraper(ABC):
    def __init__(self, platform: str, config: dict):
        self.platform = platform
        self.timeout = config.get('request', {}).get('timeout', 15)
        self.user_agent = config.get('request', {}).get(
            'user_agent',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

    @abstractmethod
    def fetch_projects(self) -> List[FreelanceProject]:
        pass

    def _request(self, url: str) -> Optional[requests.Response]:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error {e.response.status_code} fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
