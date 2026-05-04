import os
from datetime import datetime
from typing import List

from freelance.models.scored_project import ScoredProject
from freelance.utils.logger import get_logger

logger = get_logger(__name__)


class ReportNotifier:
    def __init__(self, config: dict):
        self.vault_dir = config['output']['vault_dir']
        self.filename_prefix = config['output']['filename_prefix']

    def generate_daily_report(self, ranked_projects: List[ScoredProject], overwrite: bool = False):
        os.makedirs(self.vault_dir, exist_ok=True)

        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"{today}_{self.filename_prefix}.md"
        filepath = os.path.join(self.vault_dir, filename)

        content = self._build_report(ranked_projects)

        # 默认追加；修复报告或复核时可以覆盖当天报告
        mode = 'w' if overwrite or not os.path.exists(filepath) else 'a'
        with open(filepath, mode, encoding='utf-8') as f:
            if mode == 'a':
                f.write('\n\n---\n\n')
            f.write(content)

        logger.info(f"Report written to {filepath}")

    def _build_report(self, projects: List[ScoredProject]) -> str:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        high = sum(1 for p in projects if p.score >= 70)
        mid = sum(1 for p in projects if 40 <= p.score < 70)
        pending = sum(1 for p in projects if p.filter_tag == "pending_ai_review")
        platforms = set(p.project.platform for p in projects)

        lines = [
            "# 远程项目匹配报告",
            "",
            f"**日期**: {now}",
            f"**匹配数量**: {len(projects)} (高分: {high}, 中分: {mid}, 待确认: {pending})",
            f"**数据来源**: {', '.join(sorted(platforms))}",
            "",
            "## 质量说明",
            "",
        ]

        if not projects:
            lines.extend([
                "- 当前没有通过“明确contract/freelance + 预算可判断”门槛的私活项目。",
                "- Remote OK / WeWorkRemotely 主要是远程全职职位板；没有明确contract信号的机会不会再进入私活主清单。",
                "- 下一步应新增真正私活来源：Upwork、Freelancer、Contra、Toptal/RFP、人工导入客户线索。",
                "",
            ])
        elif pending / len(projects) > 0.5:
            lines.extend([
                "- **P0**: 待确认项目超过50%，不要直接批量投标。",
                "- 预算未知或类型不明的机会只能作为人工复核队列。",
                "",
            ])

        lines.extend([
            "---",
        ])

        for i, sp in enumerate(projects, 1):
            p = sp.project
            icon = "🔥" if sp.score >= 70 else "📋"
            pending_tag = " [待确认]" if sp.filter_tag == "pending_ai_review" else ""

            lines.append("")
            lines.append(f"## {icon} {i}. {p.title} [Score: {sp.score} | Win: {sp.win_probability}]{pending_tag}")
            lines.append("")
            lines.append(f"- **公司**: {p.company}")
            lines.append(f"- **平台**: {p.platform}")
            lines.append(f"- **预算**: {self._format_budget(p)}")
            lines.append(f"- **类型**: {p.project_type or 'Unknown'}")
            if p.tags:
                lines.append(f"- **标签**: {', '.join(p.tags)}")
            lines.append(f"- **链接**: [查看项目]({p.url})")

            if sp.match_reasons:
                lines.append("")
                lines.append("### 匹配分析")
                for reason in sp.match_reasons:
                    lines.append(f"- ✅ {reason}")

            if sp.risk_points:
                lines.append("")
                lines.append("### 风险点")
                for risk in sp.risk_points:
                    lines.append(f"- ⚠️ {risk}")

            if sp.estimated_effort or sp.suggested_rate:
                lines.append("")
                lines.append("### 建议")
                if sp.estimated_effort:
                    lines.append(f"- **预估工作量**: {sp.estimated_effort}")
                if sp.suggested_rate:
                    lines.append(f"- **建议报价**: {sp.suggested_rate}")
                if sp.rate_strategy:
                    lines.append(f"- **策略**: {sp.rate_strategy}")

            if sp.proposal_draft:
                lines.append("")
                lines.append("### 投标草稿")
                for line in sp.proposal_draft.strip().split('\n'):
                    lines.append(f"> {line}")
                lines.append(">")
                lines.append("> ⚡ *建议人工审核后再投*")

            # Compliance status
            lines.append("")
            lines.append("### 合规状态")
            if sp.compliance_flags:
                for flag in sp.compliance_flags:
                    lines.append(f"> ⚠️ 合规提示: {flag}")
            else:
                lines.append("✅ 适合公司主体签约")

            lines.append("")
            lines.append("---")

        lines.append("")
        lines.append("*数据来源: [Remote OK](https://remoteok.com), [WeWorkRemotely](https://weworkremotely.com)*")
        lines.append("*由 Freelance Project Scanner 自动生成*")

        return '\n'.join(lines)

    def _format_budget(self, project) -> str:
        if project.budget_type == "hourly" and project.salary_min:
            return f"${project.salary_min}/hr"
        elif project.budget_type == "fixed" and project.salary_min:
            low = f"${project.salary_min:,}"
            high = f" - ${project.salary_max:,}" if project.salary_max else ""
            return f"{low}{high} (固定价格)"
        elif project.budget_type == "annual_salary":
            if project.salary_min and project.salary_max:
                return f"年薪参考: ${project.salary_min:,} - ${project.salary_max:,}"
            elif project.salary_min:
                return f"年薪参考: ${project.salary_min:,}+"
            return "年薪参考 (金额未披露)"
        return "未披露"
