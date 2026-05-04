"""存储模块：管理历史职位记录"""
import json
import os
from typing import Set
from datetime import datetime
from utils.logger import logger


class JobStorage:
    """职位存储管理器"""

    def __init__(self, storage_path: str = 'storage/jobs.json'):
        self.storage_path = storage_path
        self._ensure_storage_dir()
        self.recorded_urls = self._load()
        # 兼容旧代码路径。业务语义是 recorded，不是 applied/sent。
        self.sent_urls = self.recorded_urls

    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        dir_path = os.path.dirname(self.storage_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    def _load(self) -> Set[str]:
        """加载历史已记录的职位URL"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                recorded_urls = data.get('recorded_urls')
                legacy_sent_urls = data.get('sent_urls', [])
                urls = recorded_urls if recorded_urls is not None else legacy_sent_urls
                if recorded_urls is None and legacy_sent_urls:
                    logger.info("Loaded legacy sent_urls as recorded_urls")
                logger.info(f"Loaded {len(urls)} historical job URLs")
                return set(urls)
        except FileNotFoundError:
            logger.info("No existing storage found, starting fresh")
            return set()
        except Exception as e:
            logger.error(f"Error loading storage: {e}")
            return set()

    def _save(self):
        """保存历史已记录的职位URL"""
        try:
            data = {
                'recorded_urls': sorted(self.recorded_urls),
                'sent_urls': sorted(self.recorded_urls),  # legacy compatibility
                'schema_version': 2,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.recorded_urls)} job URLs to storage")
        except Exception as e:
            logger.error(f"Error saving storage: {e}")

    def is_sent(self, url: str) -> bool:
        """检查职位URL是否已记录过（兼容旧方法名）"""
        return self.is_recorded(url)

    def is_recorded(self, url: str) -> bool:
        """检查职位URL是否已记录过"""
        return url in self.recorded_urls

    def mark_sent(self, urls: list):
        """标记职位为已记录（兼容旧方法名）"""
        self.mark_recorded(urls)

    def mark_recorded(self, urls: list):
        """标记职位为已记录，不代表已经投递"""
        for url in urls:
            self.recorded_urls.add(url)
        self._save()

    def cleanup_old_urls(self, days: int = 30):
        """清理超过N天的URL（防止文件过大）"""
        # TODO: 实现基于时间的清理
        pass
