"""职位排序工具"""
from typing import List

from models.job import Job


class JobRanker:
    """按当前求职策略排序职位"""

    @staticmethod
    def sort_for_alberta_priority(jobs: List[Job]) -> List[Job]:
        """Calgary / Edmonton / Alberta 优先，其次 Canada Remote"""
        return sorted(jobs, key=JobRanker._alberta_priority_key)

    @staticmethod
    def _alberta_priority_key(job: Job) -> tuple[int, str, str]:
        location = (job.location or '').lower()
        company = (job.company or '').lower()
        title = (job.title or '').lower()
        non_alberta_city_terms = [
            'vancouver',
            'victoria',
            'toronto',
            'mississauga',
            'waterloo',
            'kitchener',
            'ottawa',
            'montreal',
            'winnipeg',
            'halifax',
            'oakville',
        ]
        has_non_alberta_city = any(term in location for term in non_alberta_city_terms)

        if 'calgary' in location and not has_non_alberta_city:
            location_rank = 0
        elif 'edmonton' in location and not has_non_alberta_city:
            location_rank = 1
        elif 'calgary' in location or 'edmonton' in location:
            location_rank = 2
        elif 'sherwood park' in location or 'alberta' in location or ', ab' in location:
            location_rank = 3
        elif 'remote' in location and 'canada' in location:
            location_rank = 4
        else:
            location_rank = 9

        return location_rank, company, title
