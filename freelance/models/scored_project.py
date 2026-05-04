from dataclasses import dataclass, field
from typing import List, Optional

from freelance.models.project import FreelanceProject


@dataclass
class ScoredProject:
    project: FreelanceProject

    # Scoring results
    score: int                      # 0-100
    win_probability: str            # "High" / "Medium" / "Low"

    # Hard filter classification tag
    filter_tag: str = "passed"      # "passed" / "pending_ai_review"

    # AI analysis
    match_reasons: List[str] = field(default_factory=list)
    risk_points: List[str] = field(default_factory=list)
    estimated_effort: str = ""
    suggested_rate: str = ""
    rate_strategy: str = ""

    # Compliance (populated by ComplianceFilter, not ScoringEngine)
    company_signable: bool = True
    compliance_flags: List[str] = field(default_factory=list)

    # Proposal draft (populated by ProposalGenerator)
    proposal_draft: Optional[str] = None
