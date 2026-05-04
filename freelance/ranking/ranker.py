from typing import List

from freelance.models.scored_project import ScoredProject


class Ranker:
    def rank(self, scored_projects: List[ScoredProject]) -> List[ScoredProject]:
        return sorted(scored_projects, key=lambda p: (
            -p.score,
            -self._income_potential(p),
            -self._win_prob_value(p),
        ))

    def _income_potential(self, p: ScoredProject) -> int:
        proj = p.project
        if proj.budget_type == "hourly" and proj.salary_max:
            return proj.salary_max * 160  # ~1 month
        if proj.budget_type == "fixed" and proj.salary_max:
            return proj.salary_max
        return 0

    def _win_prob_value(self, p: ScoredProject) -> int:
        return {"High": 3, "Medium": 2, "Low": 1}.get(p.win_probability, 0)
