import yaml

from freelance.models.scored_project import ScoredProject
from freelance.utils.logger import get_logger

logger = get_logger(__name__)

PROPOSAL_PROMPT = """你是一位资深自由职业开发者，正在为以下项目撰写投标文案。
请用英文撰写，语气专业但不生硬，控制在 150-250 词。

## 候选人画像
{candidate_profile}

## 项目信息
- 标题: {title}
- 描述: {description_truncated}
- 预算: {budget_info}
- 匹配技能: {matched_keywords}

## AI 分析结果
- 建议报价: {suggested_rate}
- 报价策略: {rate_strategy}

## 输出格式（直接输出文案，不要加任何标题或说明）:
[开头：直击客户痛点，说明你理解他们的需求]

[相关经验：1-2个最相关的项目经历]

[方案思路：你会如何实现，用什么技术栈]

[收尾：CTA，如 "Happy to discuss further" 或 "Available to start this week"]
"""


class ProposalGenerator:
    def __init__(self, config: dict, candidate_profile: dict):
        self.provider = config.get('proposal', {}).get('provider', 'codex')
        self.model = config['proposal'].get('model')
        self.min_score = config['proposal']['min_score_to_generate']
        self.max_per_run = config['proposal']['max_proposals_per_run']
        self.candidate_profile = candidate_profile
        self._count = 0
        self._limit_logged = False

        if self.provider != 'codex':
            logger.warning("Unsupported proposal provider '%s'; falling back to local codex template", self.provider)
            self.provider = 'codex'

    def generate(self, scored_project: ScoredProject) -> str | None:
        """Generate proposal draft for high-scoring projects."""
        if scored_project.score < self.min_score:
            return None

        if self._count >= self.max_per_run:
            if not self._limit_logged:
                logger.info("Proposal generation limit reached")
                self._limit_logged = True
            return None

        self._count += 1
        return self._generate_template(scored_project)

    def _generate_template(self, sp: ScoredProject) -> str:
        """本地模板投标草稿，不调用外部 LLM"""
        project = sp.project
        skills = self._extract_skills(sp)
        budget = self._format_budget(project)

        return (
            f"I understand you are looking for help with {project.title}. "
            f"My background is 16 years in backend architecture, payment systems, distributed systems, "
            f"data pipelines, and AI/LLM automation, so this looks aligned with the kind of work I can deliver reliably.\n\n"
            f"The strongest fit I see is around {skills}. I would first clarify the expected workflow, data sources, "
            f"integration points, and acceptance criteria, then propose a small paid discovery or first milestone so you can "
            f"validate the approach before committing to a larger build.\n\n"
            f"For implementation, I can work with Python, Java/Spring Boot, FastAPI, APIs, databases, cloud deployment, "
            f"and automation tooling depending on your stack. Budget noted: {budget}. "
            f"My suggested approach is: {sp.rate_strategy}\n\n"
            f"Happy to review the current system or requirements and suggest a concrete delivery plan."
        )

    def _extract_skills(self, sp: ScoredProject) -> str:
        for reason in sp.match_reasons:
            if reason.startswith('核心技能匹配:'):
                return reason.split(':', 1)[1].strip()
        if sp.project.tags:
            return ', '.join(sp.project.tags[:4])
        return 'backend systems, automation, and data workflows'

    def _build_prompt(self, sp: ScoredProject) -> str:
        return PROPOSAL_PROMPT.format(
            candidate_profile=yaml.dump(self.candidate_profile, allow_unicode=True),
            title=sp.project.title,
            description_truncated=sp.project.description[:1500],
            budget_info=self._format_budget(sp.project),
            matched_keywords=', '.join(sp.match_reasons),
            suggested_rate=sp.suggested_rate,
            rate_strategy=sp.rate_strategy,
        )

    def _format_budget(self, project) -> str:
        if project.budget_type == "hourly" and project.salary_min:
            return f"${project.salary_min}/hr"
        elif project.budget_type == "fixed" and project.salary_min:
            return f"${project.salary_min:,} - ${project.salary_max:,}" if project.salary_max else f"${project.salary_min:,}"
        elif project.budget_type == "annual_salary" and project.salary_min:
            low = f"${project.salary_min:,}"
            high = f" - ${project.salary_max:,}" if project.salary_max else ""
            return f"{low}{high} (annual salary)"
        return "Not disclosed"
