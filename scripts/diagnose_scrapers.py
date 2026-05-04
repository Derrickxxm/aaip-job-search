"""诊断各公司抓取和过滤结果，不写报告、不更新去重记录"""
import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(PROJECT_ROOT / '.ms-playwright'))

from filters.job_filter import JobFilter
from main import PROFILES
from scrapers.ahs import AHSScraper
from scrapers.ashby import AshbyScraper
from scrapers.bamboohr import BambooHRScraper
from scrapers.custom import CustomScraper
from scrapers.greenhouse import GreenhouseScraper
from scrapers.jazzhr import JazzHRScraper
from scrapers.jobbank import JobBankScraper
from scrapers.jobber import JobberScraper
from scrapers.jobvite import JobviteScraper
from scrapers.lever import LeverScraper
from scrapers.shopify import ShopifyScraper
from storage.job_storage import JobStorage
from utils.config_loader import ConfigLoader


SCRAPERS = {
    'greenhouse': GreenhouseScraper,
    'ashby': AshbyScraper,
    'lever': LeverScraper,
    'jazzhr': JazzHRScraper,
    'bamboohr': BambooHRScraper,
    'jobber': JobberScraper,
    'jobvite': JobviteScraper,
    'shopify': ShopifyScraper,
    'jobbank': JobBankScraper,
    'ahs': AHSScraper,
    'covenant': AHSScraper,
}


def make_scraper(company: dict, config: dict, timeout: int, user_agent: str):
    if os.environ.get('DISABLE_PLAYWRIGHT') == '1' and company.get('platform') in {'bamboohr', 'jobber'}:
        raise RuntimeError('Playwright disabled for diagnostics')

    cls = SCRAPERS.get(company.get('platform'), CustomScraper)
    kwargs = {
        'company_id': company.get('id'),
        'company_name': company.get('name'),
        'url': company.get('careers_url'),
        'timeout': timeout,
        'user_agent': user_agent,
    }
    if company.get('platform') in {'jobbank', 'ahs', 'covenant'}:
        kwargs['config'] = config
    return cls(**kwargs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', default='tech', choices=sorted(PROFILES))
    parser.add_argument('--include-sent', action='store_true', help='包含历史已记录职位')
    parser.add_argument('--sample-size', type=int, default=5)
    parser.add_argument('--allow-playwright', action='store_true')
    args = parser.parse_args()

    if not args.allow_playwright:
        os.environ['DISABLE_PLAYWRIGHT'] = '1'

    profile = PROFILES[args.profile]
    config = ConfigLoader.load_config(profile['config'])
    companies = ConfigLoader.load_companies(profile['companies'])
    storage = JobStorage(profile['storage'])
    job_filter = JobFilter(config)

    request_config = config.get('request', {})
    timeout = request_config.get('timeout', 10)
    user_agent = request_config.get('user_agent', 'Mozilla/5.0')

    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = PROJECT_ROOT / 'logs' / f'diagnose_{args.profile}_{now}.md'
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Diagnose {args.profile}",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- include_sent: {args.include_sent}",
        f"- allow_playwright: {args.allow_playwright}",
        "",
        "| Company | Platform | Status | Raw | Matched All | Recorded | Unrecorded | Seconds | Error |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    total_raw = total_matched = total_recorded = total_unrecorded = 0
    samples = []

    for company in companies:
        if company.get('status') == 'pending':
            lines.append(
                f"| {company.get('name')} | {company.get('platform')} | pending | 0 | 0 | 0 | 0 | 0.0 | |"
            )
            continue

        start = time.monotonic()
        error = ''
        jobs = []
        try:
            scraper = make_scraper(company, config, timeout, user_agent)
            jobs = scraper.fetch_jobs()
        except Exception as e:
            error = f"{type(e).__name__}: {e}".replace('|', '\\|').replace('\n', ' ')[:240]

        matched = [job for job in jobs if job_filter.is_match(job)]
        recorded = [job for job in matched if storage.is_recorded(job.url)]
        unrecorded = [job for job in matched if not storage.is_recorded(job.url)]
        displayed = matched if args.include_sent else unrecorded
        elapsed = time.monotonic() - start

        total_raw += len(jobs)
        total_matched += len(matched)
        total_recorded += len(recorded)
        total_unrecorded += len(unrecorded)

        lines.append(
            f"| {company.get('name')} | {company.get('platform')} | active | "
            f"{len(jobs)} | {len(matched)} | {len(recorded)} | {len(unrecorded)} | {elapsed:.1f} | {error} |"
        )

        for job in displayed[:args.sample_size]:
            samples.append((company.get('name'), storage.is_recorded(job.url), job))

    lines.extend([
        "",
        "## Totals",
        "",
        f"- raw: {total_raw}",
        f"- matched_all: {total_matched}",
        f"- recorded: {total_recorded}",
        f"- unrecorded: {total_unrecorded}",
        "",
        "## Samples",
        "",
    ])

    for company_name, is_sent, job in samples:
        status = "RECORDED" if is_sent else "UNRECORDED"
        lines.extend([
            f"### {status} - {job.title}",
            f"- company: {company_name}",
            f"- location: {job.location}",
            f"- department: {job.department or 'N/A'}",
            f"- url: {job.url}",
            "",
        ])

    out_path.write_text('\n'.join(lines), encoding='utf-8')
    print(out_path)
    print(
        f"raw={total_raw} matched_all={total_matched} "
        f"recorded={total_recorded} unrecorded={total_unrecorded}"
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
