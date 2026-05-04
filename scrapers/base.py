"""基础抓取器类"""
import os
from abc import ABC, abstractmethod
from typing import List
import requests
from models.job import Job
from utils.logger import logger


os.environ.setdefault(
    'PLAYWRIGHT_BROWSERS_PATH',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.ms-playwright'))
)


class BaseScraper(ABC):
    """抓取器基类"""

    def __init__(self, company_id: str, company_name: str, url: str, timeout: int = 10, user_agent: str = None):
        self.company_id = company_id
        self.company_name = company_name
        self.url = url
        self.timeout = timeout
        self.session = requests.Session()
        if user_agent:
            self.session.headers.update({'User-Agent': user_agent})

    @abstractmethod
    def fetch_jobs(self) -> List[Job]:
        """抓取职位列表（子类实现）"""
        pass

    def _request(self, url: str) -> requests.Response:
        """发送HTTP请求"""
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

    def _playwright_disabled(self) -> bool:
        """是否禁用浏览器兜底"""
        return os.environ.get('DISABLE_PLAYWRIGHT') == '1'
