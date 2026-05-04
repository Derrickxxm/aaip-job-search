"""Job数据模型"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Job:
    """职位数据模型"""
    title: str
    company: str
    location: str
    url: str
    platform: str
    scraped_at: datetime
    department: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'url': self.url,
            'platform': self.platform,
            'scraped_at': self.scraped_at.isoformat(),
            'department': self.department,
            'description': self.description
        }

    def __str__(self) -> str:
        return f"{self.title} @ {self.company} ({self.location})"
