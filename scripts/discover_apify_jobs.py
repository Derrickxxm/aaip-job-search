"""用 Apify 小批量发现阿省 IT 职位。

默认不调用 Apify，只打印计划。必须显式传入 --run-apify 才会消耗额度。
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from filters.job_filter import JobFilter
from models.job import Job
from utils.config_loader import ConfigLoader
from utils.job_ranker import JobRanker


DEFAULT_ENV_PATH = Path("/Users/xxm/projects/findSchool/.env")
DEFAULT_OUTPUT_DIR = Path("/Users/xxm/projects/QuantEngine_markdown_file/12-找工作/apify_jobs")
DEFAULT_CONFIG_PATH = Path("config/production.yaml")

DEFAULT_POSITIONS = [
    "software developer",
    "backend developer",
]
DEFAULT_LOCATIONS = [
    "Calgary, AB",
    "Edmonton, AB",
]


def load_apify_token(env_path: Path = DEFAULT_ENV_PATH) -> str:
    """从环境变量或 findSchool 的 .env 读取 Apify token，不打印 token 内容。"""
    env_token = os.environ.get("APIFY_API_TOKEN", "").strip()
    if env_token:
        return env_token

    if not env_path.exists():
        return ""

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "APIFY_API_TOKEN":
                return value.strip().strip('"').strip("'")
    return ""


def first_value(item: dict[str, Any], keys: list[str]) -> str:
    """从多个可能字段中取第一个非空值。"""
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def normalize_job(item: dict[str, Any], position: str, location: str) -> Job | None:
    """把 Indeed actor 的不同输出字段归一化为 Job。"""
    title = first_value(item, ["positionName", "position", "title", "jobTitle", "name"])
    company = first_value(item, ["company", "companyName", "employer", "hiringOrganizationName"])
    job_location = first_value(item, ["location", "jobLocation", "formattedLocation", "companyLocation"])
    url = first_value(item, ["url", "jobUrl", "link", "jobLink", "externalApplyLink"])
    description = first_value(item, ["description", "jobDescription", "snippet"])

    if not title or not company or not url:
        return None

    if not job_location:
        job_location = location

    return Job(
        title=title,
        company=company,
        location=job_location,
        url=url,
        platform="Apify Indeed",
        scraped_at=datetime.now(),
        department=f"Apify query: {position} | {location}",
        description=description,
    )


def dedupe_jobs(jobs: list[Job]) -> list[Job]:
    """按 URL 去重。"""
    seen = set()
    unique = []
    for job in jobs:
        key = job.url.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)
    return unique


def write_outputs(raw_jobs: list[Job], matched_jobs: list[Job], output_dir: Path) -> tuple[Path, Path]:
    """保存 JSON 和 Markdown 报告。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    json_path = output_dir / f"{today}_apify_indeed_jobs.json"
    md_path = output_dir / f"{today}_apify_indeed_jobs.md"

    payload = {
        "generated_at": datetime.now().isoformat(),
        "raw_count": len(raw_jobs),
        "matched_count": len(matched_jobs),
        "raw_jobs": [job.to_dict() for job in raw_jobs],
        "matched_jobs": [job.to_dict() for job in matched_jobs],
    }
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    lines = [
        f"# {today} Apify Indeed 阿省 IT 职位小批量抓取",
        "",
        "> 省额度模式：用于补充平台职位，不替代 Job Bank / 公司官网日常抓取。",
        "",
        f"- 原始职位数：{len(raw_jobs)}",
        f"- 过滤后匹配数：{len(matched_jobs)}",
        "",
        "## 匹配职位",
        "",
    ]
    if not matched_jobs:
        lines.append("暂无匹配职位。")
    for index, job in enumerate(matched_jobs, 1):
        lines.extend([
            f"### {index}. {job.title}",
            "",
            f"- **公司**: {job.company}",
            f"- **地点**: {job.location}",
            f"- **平台**: {job.platform}",
            f"- **链接**: [查看职位]({job.url})",
            f"- **来源**: {job.department}",
            "",
        ])

    lines.extend([
        "## 原始职位",
        "",
    ])
    for index, job in enumerate(raw_jobs, 1):
        lines.append(f"{index}. [{job.title}]({job.url}) - {job.company} - {job.location}")

    with open(md_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")

    return json_path, md_path


def run_indeed_discovery(
    actor_id: str,
    positions: list[str],
    locations: list[str],
    max_items_per_search: int,
) -> list[Job]:
    """调用 Apify Indeed actor 小批量抓取职位。"""
    try:
        from apify_client import ApifyClient
    except ImportError as exc:
        raise RuntimeError("apify-client is not installed. Run: pip install -r requirements.txt") from exc

    token = load_apify_token()
    if not token:
        raise RuntimeError("APIFY_API_TOKEN not found in environment or /Users/xxm/projects/findSchool/.env")

    client = ApifyClient(token)
    jobs = []
    for position in positions:
        for location in locations:
            run_input = {
                "position": position,
                "location": location,
                "country": "CA",
                "maxItemsPerSearch": max_items_per_search,
                "parseCompanyDetails": False,
                "saveOnlyUniqueItems": True,
                "followApplyRedirects": False,
            }
            run = client.actor(actor_id).call(run_input=run_input)
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                continue
            for item in client.dataset(dataset_id).iterate_items():
                job = normalize_job(item, position, location)
                if job:
                    jobs.append(job)
    return dedupe_jobs(jobs)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="Discover Alberta IT jobs with a tiny Apify budget.")
    parser.add_argument("--run-apify", action="store_true", help="真正调用 Apify；不传则只打印计划")
    parser.add_argument("--actor", default="misceres/indeed-scraper", help="Indeed actor id")
    parser.add_argument("--max-items-per-search", type=int, default=5, help="每个职位/地点组合最多抓取多少条")
    parser.add_argument("--position", action="append", dest="positions", help="可重复传入职位关键词")
    parser.add_argument("--location", action="append", dest="locations", help="可重复传入地点")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="过滤配置文件")
    return parser.parse_args()


def main() -> int:
    """入口。"""
    args = parse_args()
    positions = args.positions or DEFAULT_POSITIONS
    locations = args.locations or DEFAULT_LOCATIONS
    planned_searches = len(positions) * len(locations)

    print("Apify job discovery plan")
    print(f"actor: {args.actor}")
    print(f"positions: {len(positions)}")
    print(f"locations: {len(locations)}")
    print(f"searches: {planned_searches}")
    print(f"max_items_per_search: {args.max_items_per_search}")
    print(f"max_results_planned: {planned_searches * args.max_items_per_search}")
    print(f"token_available: {bool(load_apify_token())}")

    if not args.run_apify:
        print("dry_run: true")
        print("Add --run-apify to spend Apify credits.")
        return 0

    config = ConfigLoader.load_config(args.config)
    job_filter = JobFilter(config)
    raw_jobs = run_indeed_discovery(
        actor_id=args.actor,
        positions=positions,
        locations=locations,
        max_items_per_search=args.max_items_per_search,
    )
    matched_jobs = [job for job in raw_jobs if job_filter.is_match(job)]
    matched_jobs = JobRanker.sort_for_alberta_priority(matched_jobs)
    json_path, md_path = write_outputs(raw_jobs, matched_jobs, Path(args.output_dir))
    print(f"raw_jobs: {len(raw_jobs)}")
    print(f"matched_jobs: {len(matched_jobs)}")
    print(f"json: {json_path}")
    print(f"markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
