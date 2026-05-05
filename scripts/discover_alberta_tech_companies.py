"""用 Apify 小批量发现阿省科技公司。

默认不调用 Apify，只打印计划。必须显式传入 --run-apify 才会消耗额度。
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_ENV_PATH = Path("/Users/xxm/projects/findSchool/.env")
DEFAULT_OUTPUT_DIR = Path("/Users/xxm/projects/QuantEngine_markdown_file/12-找工作/company_discovery")

DEFAULT_QUERIES = [
    "software company Calgary",
    "software company Edmonton",
    "SaaS company Calgary",
    "AI company Edmonton",
]


def load_apify_token(env_path: Path = DEFAULT_ENV_PATH) -> str:
    """从 findSchool 的 .env 读取 Apify token，不打印 token 内容。"""
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


def normalize_place(item: dict[str, Any], query: str) -> dict[str, Any]:
    """把 Google Maps actor 的不同输出字段归一化。"""
    title = item.get("title") or item.get("name") or item.get("businessName") or ""
    website = item.get("website") or item.get("url") or item.get("websiteUrl") or ""
    phone = item.get("phone") or item.get("phoneNumber") or ""
    address = item.get("address") or item.get("street") or item.get("formattedAddress") or ""
    city = item.get("city") or item.get("locatedIn") or ""
    categories = item.get("categories") or item.get("categoryName") or item.get("category") or []
    if isinstance(categories, str):
        categories = [categories]

    return {
        "name": str(title).strip(),
        "website": str(website).strip(),
        "phone": str(phone).strip(),
        "address": str(address).strip(),
        "city": str(city).strip(),
        "categories": categories,
        "source_query": query,
        "source": "apify_google_maps",
    }


def dedupe_companies(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按 website/name 去重。"""
    seen = set()
    unique = []
    for company in companies:
        website = company.get("website", "").rstrip("/").lower()
        name = company.get("name", "").lower()
        key = website or name
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(company)
    return unique


def write_outputs(companies: list[dict[str, Any]], output_dir: Path) -> tuple[Path, Path]:
    """保存 JSON 和 Markdown 报告。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    json_path = output_dir / f"{today}_alberta_tech_companies_apify_seed.json"
    md_path = output_dir / f"{today}_alberta_tech_companies_apify_seed.md"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(companies, file, ensure_ascii=False, indent=2)

    lines = [
        f"# {today} 阿省科技公司 Apify 小批量发现",
        "",
        "> 省额度模式：只用于扩充公司池，不作为日常职位抓取。",
        "",
        f"- 公司数：{len(companies)}",
        "",
        "| 公司 | 城市 | 官网 | 来源查询 |",
        "|---|---|---|---|",
    ]
    for company in companies:
        name = company.get("name", "")
        city = company.get("city", "")
        website = company.get("website", "")
        query = company.get("source_query", "")
        website_text = f"[官网]({website})" if website else ""
        lines.append(f"| {name} | {city} | {website_text} | {query} |")

    with open(md_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")

    return json_path, md_path


def run_google_maps_discovery(actor_id: str, queries: list[str], limit_per_query: int) -> list[dict[str, Any]]:
    """调用 Apify Google Maps actor 小批量抓取。"""
    try:
        from apify_client import ApifyClient
    except ImportError as exc:
        raise RuntimeError("apify-client is not installed. Run: pip install -r requirements.txt") from exc

    token = load_apify_token()
    if not token:
        raise RuntimeError("APIFY_API_TOKEN not found in environment or /Users/xxm/projects/findSchool/.env")

    client = ApifyClient(token)
    companies = []
    for query in queries:
        run_input = {
            "searchStringsArray": [query],
            "locationQuery": "Alberta, Canada",
            "maxCrawledPlacesPerSearch": limit_per_query,
            "language": "en",
        }
        run = client.actor(actor_id).call(run_input=run_input)
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            continue
        for item in client.dataset(dataset_id).iterate_items():
            companies.append(normalize_place(item, query))
    return dedupe_companies(companies)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="Discover Alberta tech companies with a tiny Apify budget.")
    parser.add_argument("--run-apify", action="store_true", help="真正调用 Apify；不传则只打印计划")
    parser.add_argument("--actor", default="vortex_data/google-maps", help="Google Maps actor id")
    parser.add_argument("--limit-per-query", type=int, default=20, help="每个查询最多抓取多少家公司")
    parser.add_argument("--query", action="append", dest="queries", help="可重复传入自定义查询")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    return parser.parse_args()


def main() -> int:
    """入口。"""
    args = parse_args()
    queries = args.queries or DEFAULT_QUERIES

    print("Apify company discovery plan")
    print(f"actor: {args.actor}")
    print(f"queries: {len(queries)}")
    print(f"limit_per_query: {args.limit_per_query}")
    print(f"max_results_planned: {len(queries) * args.limit_per_query}")
    print(f"token_available: {bool(load_apify_token())}")

    if not args.run_apify:
        print("dry_run: true")
        print("Add --run-apify to spend Apify credits.")
        return 0

    companies = run_google_maps_discovery(args.actor, queries, args.limit_per_query)
    json_path, md_path = write_outputs(companies, Path(args.output_dir))
    print(f"companies_found: {len(companies)}")
    print(f"json: {json_path}")
    print(f"markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
