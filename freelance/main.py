"""Freelance Project Scanner - Main Pipeline

Usage:
    python -m freelance.main              # Run scanner
    python -m freelance.main --check      # Run only if current hour matches schedule
"""

import argparse
import os
import sys
from datetime import datetime

import yaml

from freelance.compliance.compliance_filter import ComplianceFilter
from freelance.filters.hard_filter import HardFilter
from freelance.filters.skill_matcher import SkillMatcher
from freelance.notification.report import ReportNotifier
from freelance.ranking.ranker import Ranker
from freelance.scrapers.remoteok import RemoteOKScraper
from freelance.scrapers.weworkremotely import WeWorkRemotelyScraper
from freelance.storage.project_storage import ProjectStorage
from freelance.utils.logger import get_logger

logger = get_logger("freelance.main")

os.environ.setdefault(
    'PLAYWRIGHT_BROWSERS_PATH',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.ms-playwright'))
)


def load_config(config_path: str = None) -> dict:
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'freelance.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_candidate_profile(profile_path: str = None) -> dict:
    if profile_path is None:
        profile_path = os.path.join(os.path.dirname(__file__), 'config', 'candidate_profile.yaml')
    with open(profile_path, 'r') as f:
        return yaml.safe_load(f)


def get_enabled_scrapers(config: dict):
    scrapers = []
    platforms = config.get('platforms', {})

    if platforms.get('remoteok', {}).get('enabled', False):
        scrapers.append(RemoteOKScraper(config))

    if platforms.get('weworkremotely', {}).get('enabled', False):
        scrapers.append(WeWorkRemotelyScraper(config))

    return scrapers


def main():
    parser = argparse.ArgumentParser(description='Freelance Project Scanner')
    parser.add_argument('--check', action='store_true',
                        help='Only run if current hour matches schedule')
    parser.add_argument('--dry-run', action='store_true',
                        help='Fetch and filter only; do not call LLM, write report, or update storage')
    parser.add_argument('--include-recorded', action='store_true',
                        help='Include historically recorded projects when regenerating or auditing reports')
    parser.add_argument('--no-mark-recorded', action='store_true',
                        help='Write report without updating historical recorded URLs')
    parser.add_argument('--overwrite-report', action='store_true',
                        help='Overwrite today report instead of appending')
    args = parser.parse_args()

    config = load_config()
    candidate = load_candidate_profile()

    # Schedule check
    if args.check:
        current_hour = datetime.now().hour
        scheduled_hours = config.get('schedule', {}).get('hours', [])
        if current_hour not in scheduled_hours:
            logger.info(f"Current hour {current_hour} not in schedule {scheduled_hours}, skipping")
            return

    logger.info("=" * 60)
    logger.info(
        "Freelance Project Scanner started "
        f"(dry_run: {args.dry_run}, include_recorded: {args.include_recorded}, "
        f"no_mark_recorded: {args.no_mark_recorded}, overwrite_report: {args.overwrite_report})"
    )
    logger.info("=" * 60)

    # Initialize components
    storage = ProjectStorage(config)
    hard_filter = HardFilter(config)
    skill_matcher = SkillMatcher(config)
    ranker = Ranker()
    report = ReportNotifier(config)

    # ===== Stage 1: Fetch =====
    raw_projects = []
    for scraper in get_enabled_scrapers(config):
        try:
            projects = scraper.fetch_projects()
            raw_projects.extend(projects)
        except Exception as e:
            logger.error(f"Scraper {scraper.platform} failed: {e}")
    logger.info(f"Fetched {len(raw_projects)} raw projects")

    # ===== Stage 2: Dedup =====
    new_projects = raw_projects if args.include_recorded else [p for p in raw_projects if not storage.is_recorded(p.url)]
    logger.info(f"After dedup: {len(new_projects)} new projects")

    # ===== Stage 3: Hard filter =====
    candidates = []
    for p in new_projects:
        passed, tag = hard_filter.apply(p)
        if passed:
            candidates.append((p, tag))
        else:
            logger.debug(f"Hard filter rejected: {p.title} ({tag})")
    logger.info(f"After hard filter: {len(candidates)} candidates")

    # ===== Stage 4: Skill matching =====
    matched = []
    for p, tag in candidates:
        is_match, keywords = skill_matcher.is_match(p)
        if is_match:
            matched.append((p, tag, keywords))
        else:
            logger.debug(f"Skill mismatch: {p.title}")
    logger.info(f"After skill match: {len(matched)} matched")

    if args.dry_run:
        logger.info("Dry run enabled, skipping LLM scoring, proposal generation, report write, and storage update")
        for p, tag, keywords in matched[:20]:
            logger.info(
                f"[DRY-RUN] {p.title} @ {p.company} | {p.platform} | {tag} | "
                f"{', '.join(keywords[:8])} | {p.url}"
            )
        if len(matched) > 20:
            logger.info(f"[DRY-RUN] ... {len(matched) - 20} more projects")
        return

    from freelance.proposal.proposal_generator import ProposalGenerator
    from freelance.scoring.scoring_engine import ScoringEngine

    scoring_engine = ScoringEngine(config, candidate)
    proposal_gen = ProposalGenerator(config, candidate)

    # ===== Stage 5: AI Scoring =====
    scored = []
    for p, tag, keywords in matched:
        scored_project = scoring_engine.score(p, keywords, tag)
        scored.append(scored_project)
    logger.info(f"Scored {len(scored)} projects")

    # ===== Stage 6: Compliance check (independent module, single entry point) =====
    compliance_filter = ComplianceFilter()
    for sp in scored:
        result = compliance_filter.check(sp.project)
        sp.company_signable = result['company_signable']
        sp.compliance_flags = result['flags']

    # ===== Stage 7: Proposal generation =====
    for sp in scored:
        sp.proposal_draft = proposal_gen.generate(sp)
    proposal_count = sum(1 for sp in scored if sp.proposal_draft)
    logger.info(f"Generated {proposal_count} proposals")

    # ===== Stage 8: Ranking =====
    ranked = ranker.rank(scored)

    # ===== Stage 9: Output =====
    if ranked:
        report.generate_daily_report(ranked, overwrite=args.overwrite_report)
        if args.no_mark_recorded:
            logger.info("Skipped storage update because --no-mark-recorded is enabled")
        else:
            storage.mark_recorded([sp.project.url for sp in ranked])
        logger.info(f"Generated report with {len(ranked)} projects")

        # Telegram push (if enabled)
        if config.get('notification', {}).get('telegram', {}).get('enabled', False):
            from freelance.notification.telegram import TelegramNotifier
            TelegramNotifier(config).send_summary(ranked)
    else:
        report.generate_daily_report([], overwrite=args.overwrite_report)
        logger.info("No matching projects found")

    logger.info("Freelance Project Scanner completed")


if __name__ == '__main__':
    main()
