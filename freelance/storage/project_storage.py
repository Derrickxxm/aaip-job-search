import json
import os
from typing import List

from freelance.utils.logger import get_logger

logger = get_logger(__name__)


class ProjectStorage:
    def __init__(self, config: dict):
        self.storage_path = config['storage']['path']
        self._ensure_dir()
        self._recorded_urls = self._load()
        self._sent_urls = self._recorded_urls

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def _load(self) -> set:
        if not os.path.exists(self.storage_path):
            return set()
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                urls = data.get('recorded_urls')
                legacy_urls = data.get('sent_urls', [])
                if urls is None and legacy_urls:
                    logger.info("Loaded legacy sent_urls as recorded_urls")
                return set(urls if urls is not None else legacy_urls)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to load storage: {e}")
            return set()

    def _save(self):
        data = {
            'recorded_urls': sorted(self._recorded_urls),
            'sent_urls': sorted(self._recorded_urls),
            'schema_version': 2,
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def is_sent(self, url: str) -> bool:
        return self.is_recorded(url)

    def is_recorded(self, url: str) -> bool:
        return url in self._recorded_urls

    def mark_sent(self, urls: List[str]):
        self.mark_recorded(urls)

    def mark_recorded(self, urls: List[str]):
        self._recorded_urls.update(urls)
        self._save()
        logger.debug(f"Marked {len(urls)} URLs as recorded (total: {len(self._recorded_urls)})")
