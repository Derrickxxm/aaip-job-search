from typing import List

from freelance.models.project import FreelanceProject
from freelance.models.scored_project import ScoredProject
from freelance.utils.logger import get_logger

logger = get_logger(__name__)

class ScoringEngine:
    def __init__(self, config: dict, candidate_profile: dict):
        self.provider = config.get('scoring', {}).get('provider', 'codex')
        self.model = config['scoring'].get('model')
        self.rule_threshold = config['scoring']['rule_score_threshold']
        self.max_llm = config['scoring']['max_llm_per_run']
        self.candidate_profile = candidate_profile
        self._llm_count = 0

        if self.provider != 'codex':
            logger.warning("Unsupported scoring provider '%s'; falling back to local codex rules", self.provider)
            self.provider = 'codex'

    def score(self, project: FreelanceProject,
              matched_keywords: List[str],
              filter_tag: str) -> ScoredProject:
        # Step 1: Rule-based pre-scoring
        rule_score = self._rule_based_score(project, matched_keywords)

        llm_result = self._codex_score(project, matched_keywords, filter_tag, rule_score)

        return ScoredProject(
            project=project,
            score=llm_result['score'],
            win_probability=llm_result['win_probability'],
            match_reasons=llm_result['match_reasons'],
            risk_points=llm_result['risk_points'],
            estimated_effort=llm_result['estimated_effort'],
            suggested_rate=llm_result['suggested_rate'],
            rate_strategy=llm_result['rate_strategy'],
            filter_tag=filter_tag,
            company_signable=True,
            compliance_flags=[],
        )

    def _rule_based_score(self, project: FreelanceProject, matched_keywords: List[str]) -> int:
        score = 0

        # Skill match (0-40)
        kw_count = len(matched_keywords)
        if kw_count >= 3:
            score += 40
        elif kw_count == 2:
            score += 30
        elif kw_count == 1:
            score += 15

        # Budget level (0-25)
        if project.budget_type == "hourly" and project.salary_min:
            if project.salary_min >= 60:
                score += 25
            elif project.salary_min >= 40:
                score += 18
            elif project.salary_min >= 30:
                score += 10
        elif project.budget_type == "fixed" and project.salary_min:
            if project.salary_min >= 10000:
                score += 25
            elif project.salary_min >= 5000:
                score += 18
            elif project.salary_min >= 2000:
                score += 10

        # Project clarity (0-15) by description length
        desc_len = len(project.description)
        if desc_len >= 500:
            score += 15
        elif desc_len >= 200:
            score += 10
        elif desc_len >= 50:
            score += 5

        # Client quality (0-10) — only Freelancer has data, default 5
        score += 5

        # Competition intensity (0-10) — can't judge at rule level, default 5
        score += 5

        return min(score, 100)

    def _codex_score(self, project: FreelanceProject,
                     matched_keywords: List[str],
                     filter_tag: str,
                     rule_score: int) -> dict:
        """本地 Codex 规则评分：不调用外部 LLM，保证可离线生成报告"""
        title = project.title.lower()
        description = project.description.lower()
        combined = f"{title}\n{description}"

        score = rule_score
        reasons = []
        risks = []

        high_value_skills = {
            'python', 'java', 'backend', 'api', 'fastapi', 'spring', 'data pipeline',
            'data engineer', 'aws', 'cloud', 'docker', 'kubernetes', 'terraform',
            'llm', 'openai', 'chatgpt', 'ai', 'automation', 'trading', 'payment',
            'fintech', 'full stack', 'fullstack',
        }
        strong_matches = [kw for kw in matched_keywords if kw.lower() in high_value_skills]
        if strong_matches:
            score += min(15, len(strong_matches) * 4)
            reasons.append(f"核心技能匹配: {', '.join(strong_matches[:6])}")

        if any(word in combined for word in ['contract', 'freelance', 'consultant', 'consulting']):
            score += 8
            reasons.append("项目形态更接近可承接合同/咨询")

        if any(word in combined for word in ['integration', 'migration', 'automation', 'pipeline', 'backend', 'api']):
            score += 8
            reasons.append("需求类型适合用后端、自动化或数据管道经验切入")

        if project.budget_type == 'annual_salary':
            score -= 18
            risks.append("看起来更像全职招聘，未必适合私活承接")
        elif project.budget_type == 'unknown':
            score -= 8
            risks.append("预算未披露，需要先确认付款方式和范围")

        if filter_tag == 'pending_ai_review':
            score -= 5
            risks.append("硬门槛信息不完整，需要人工确认是否真是项目")

        if any(word in combined for word in ['manager', 'account executive', 'sales', 'counsel', 'legal']):
            score -= 15
            risks.append("标题包含非交付型岗位信号，可能不是技术私活")

        score = max(0, min(score, 100))
        if score >= 75:
            win_probability = 'High'
        elif score >= 55:
            win_probability = 'Medium'
        else:
            win_probability = 'Low'

        if not reasons:
            reasons.append(f"匹配关键词: {', '.join(matched_keywords[:6])}")
        if not risks:
            risks.append("需要确认客户预算、时区、交付范围和签约主体")

        return {
            'score': score,
            'win_probability': win_probability,
            'match_reasons': reasons,
            'risk_points': risks,
            'estimated_effort': self._estimate_effort(project),
            'suggested_rate': self._suggest_rate(project, score),
            'rate_strategy': self._rate_strategy(project, score),
        }

    def _default_low_score(self, project: FreelanceProject, rule_score: int = 0) -> dict:
        return {
            'score': rule_score,
            'win_probability': 'Low',
            'match_reasons': [],
            'risk_points': ['Rule-based score below threshold, no LLM analysis'],
            'estimated_effort': '',
            'suggested_rate': '',
            'rate_strategy': '',
        }

    def _format_budget(self, project: FreelanceProject) -> str:
        if project.budget_type == "hourly" and project.salary_min:
            return f"${project.salary_min}/hr"
        elif project.budget_type == "fixed" and project.salary_min:
            low = f"${project.salary_min:,}"
            high = f" - ${project.salary_max:,}" if project.salary_max else ""
            return f"{low}{high} (fixed)"
        elif project.budget_type == "annual_salary" and project.salary_min:
            low = f"${project.salary_min:,}"
            high = f" - ${project.salary_max:,}" if project.salary_max else ""
            return f"{low}{high} (annual salary reference)"
        return "Not disclosed"

    def _estimate_effort(self, project: FreelanceProject) -> str:
        desc_len = len(project.description)
        title = project.title.lower()
        if any(word in title for word in ['lead', 'staff', 'principal', 'architect']):
            return "2-4 weeks discovery + phased delivery"
        if desc_len >= 800:
            return "2-3 weeks"
        if desc_len >= 250:
            return "1-2 weeks"
        return "Initial paid discovery: 3-5 days"

    def _suggest_rate(self, project: FreelanceProject, score: int) -> str:
        if project.budget_type == "hourly" and project.salary_min:
            floor = max(project.salary_min, 60 if score >= 70 else 50)
            return f"${floor}/hr+"
        if project.budget_type == "fixed" and project.salary_min:
            return f"Start with paid discovery, then fixed milestones from ${project.salary_min:,}+"
        return "$60-85/hr or paid discovery milestone"

    def _rate_strategy(self, project: FreelanceProject, score: int) -> str:
        if project.budget_type == "annual_salary":
            return "Only pursue if they accept B2B contract or part-time consulting."
        if score >= 70:
            return "Position as senior delivery partner; avoid underpricing."
        return "Qualify scope first, propose a small paid diagnostic milestone."

    def _format_candidate(self) -> str:
        cp = self.candidate_profile
        lines = [
            f"Experience: {cp.get('experience_years', 'N/A')} years",
            f"Core skills: {', '.join(cp.get('core_skills', []))}",
            f"Advanced skills: {', '.join(cp.get('advanced_skills', []))}",
            f"Preferred projects: {', '.join(cp.get('preferred_projects', []))}",
        ]
        return '\n'.join(lines)
