from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class FreelanceProject:
    title: str
    description: str
    platform: str                   # remoteok / weworkremotely / freelancer
    url: str
    company: str
    location: str                   # "Remote" / "Anywhere" / specific location
    posted_at: datetime
    scraped_at: datetime = field(default_factory=datetime.now)

    # Budget info (raw values)
    budget_raw: Optional[str] = None
    hourly_rate_raw: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    budget_type: str = "unknown"    # "hourly" / "fixed" / "annual_salary" / "unknown"

    # Project metadata
    tags: List[str] = field(default_factory=list)
    project_type: Optional[str] = None  # "contract" / "freelance" / "full-time" / "unknown"
    client_info: Optional[str] = None
