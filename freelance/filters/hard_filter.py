from typing import Tuple

from freelance.models.project import FreelanceProject
from freelance.utils.logger import get_logger

logger = get_logger(__name__)


class HardFilter:
    def __init__(self, config: dict):
        self.min_hourly_rate = config['filter']['min_hourly_rate']
        self.min_project_budget = config['filter']['min_project_budget']

    def apply(self, project: FreelanceProject) -> Tuple[bool, str]:
        """Returns (passed, tag).
        Tags: "passed" / "rejected_fulltime" / "rejected_not_remote" /
              "rejected_low_budget" / "pending_ai_review"
        """
        # Gate 1: Must be remote
        if not self._is_remote(project):
            return False, "rejected_not_remote"

        # Gate 2: Must be contract/freelance type
        type_check = self._check_project_type(project)
        if type_check == "fulltime":
            return False, "rejected_fulltime"
        if type_check == "remote_job_board_ambiguous":
            return False, "rejected_remote_job_board_ambiguous"
        type_ambiguous = (type_check == "ambiguous")

        # Gate 3: Budget check
        budget_check = self._check_budget(project)
        if budget_check == "low":
            return False, "rejected_low_budget"
        budget_unknown = (budget_check == "unknown")

        # Either dimension ambiguous -> downgrade to pending_ai_review
        if type_ambiguous or budget_unknown:
            return True, "pending_ai_review"

        return True, "passed"

    def _is_remote(self, project: FreelanceProject) -> bool:
        loc = project.location.lower()
        text = (project.title + " " + project.description[:500]).lower()

        remote_signals = ['remote', 'anywhere', 'worldwide', 'work from home',
                          'distributed', 'location independent']
        onsite_signals = ['onsite', 'on-site', 'in-office', 'hybrid',
                          'must be located in', 'relocation required']

        has_remote = any(s in loc or s in text for s in remote_signals)
        has_onsite = any(s in text for s in onsite_signals)

        # Remote OK platform projects are remote by default
        if project.platform == "remoteok":
            return not has_onsite

        return has_remote and not has_onsite

    def _check_project_type(self, project: FreelanceProject) -> str:
        """Returns "contract" / "fulltime" / "ambiguous" """
        text = (project.title + " " + project.description[:1000]).lower()

        contract_signals = ['contract', 'freelance', 'freelancer', 'project-based',
                            'outsource', 'consulting', 'contractor', 'hourly',
                            'fixed price', 'fixed-price', 'per project', 'gig']
        fulltime_signals = ['full-time', 'full time', 'permanent', 'w-2',
                            'benefits included', 'equity', '401k', 'pto',
                            'annual salary', 'salaried position']

        has_contract = any(s in text for s in contract_signals)
        has_fulltime = any(s in text for s in fulltime_signals)

        # Remote OK / WeWorkRemotely 主要是远程职位板，不是私活平台。
        # 没有明确 contract/freelance 信号时，不进入私活主报告。
        if project.platform in {"remoteok", "weworkremotely"} and not has_contract:
            return "fulltime" if has_fulltime else "remote_job_board_ambiguous"

        if has_contract and not has_fulltime:
            return "contract"
        if has_fulltime and not has_contract:
            return "fulltime"

        # Platform default inference
        if project.platform == "freelancer":
            return "contract"

        return "ambiguous"

    def _check_budget(self, project: FreelanceProject) -> str:
        """Returns "ok" / "low" / "unknown" """
        # Case 1: Explicit hourly rate
        if project.budget_type == "hourly" and project.salary_min:
            return "ok" if project.salary_min >= self.min_hourly_rate else "low"

        # Case 2: Fixed project budget
        if project.budget_type == "fixed" and project.salary_min:
            return "ok" if project.salary_min >= self.min_project_budget else "low"

        # Case 3: Annual salary (Remote OK / WWR job postings)
        # Not directly comparable to freelance budget, defer to AI
        if project.budget_type == "annual_salary":
            return "unknown"

        # Case 4: No budget info at all
        return "unknown"
