# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AAIP Job Aggregator is a Python-based job scraping system that fetches job postings from Alberta tech companies, filters them by tech stack and seniority level, and saves matching jobs to daily Markdown reports in `/Users/xxm/projects/QuantEngine_markdown_file/`.

## Commands

```bash
# Setup
bash scripts/init.sh                    # Create .venv, install deps, create directories
pip install -r requirements.txt         # Install dependencies
pip install playwright && playwright install chromium  # For BambooHR scraper

# Run
python main.py                          # Run scraper (manual)
python main.py --check                  # Run only if current hour in scheduled hours
bash scripts/run_test.sh                # Wrapper for manual test run

# Test individual scrapers
python scrapers/greenhouse.py           # Test Greenhouse (Benevity)
python scrapers/ashby.py                # Test Ashby (Neo Financial)
python scrapers/lever.py                # Test Lever (Attabotics)
python scrapers/jazzhr.py               # Test JazzHR (Symend)
python scrapers/bamboohr.py             # Test BambooHR (Helcim) - requires Playwright
python scrapers/jobber.py               # Test Jobber

# Deployment
bash scripts/deploy_crontab.sh          # Deploy crontab (runs at 8:00, 12:00, 18:00)

# Utilities
bash scripts/view_logs.sh               # tail -f logs/scraper.log
bash scripts/clean_history.sh           # Reset deduplication (clears storage/jobs.json)
python scripts/test_scraper.py          # Test single scraper
```

## Architecture

### Data Flow

```
main.py
  → Load config (config/production.yaml) & companies (config/companies.json)
  → For each active company:
      → Select scraper (Greenhouse/Ashby/Lever/JazzHR/BambooHR/Jobber/Custom based on platform)
      → scraper.fetch_jobs() → List[Job]
      → JobFilter.is_match() filters by tech/level/location/exclusions
      → JobStorage.is_sent() deduplicates
  → LocalStorageNotifier.append_to_daily_report() → /Users/xxm/projects/QuantEngine_markdown_file/YYYY-MM-DD_匹配职位.md
  → JobStorage.mark_sent() persists seen URLs
```

### Key Modules

- **scrapers/base.py**: Abstract `BaseScraper` class - all scrapers inherit from this
- **scrapers/greenhouse.py**: Scrapes Greenhouse job boards (JSON API)
- **scrapers/ashby.py**: Scrapes Ashby job boards (BeautifulSoup HTML parsing)
- **scrapers/lever.py**: Scrapes Lever job boards (BeautifulSoup HTML parsing)
- **scrapers/jazzhr.py**: Scrapes JazzHR/Resumator job boards (BeautifulSoup HTML parsing)
- **scrapers/bamboohr.py**: Scrapes BambooHR embedded widgets (Playwright + BeautifulSoup)
- **scrapers/jobber.py**: Scrapes Jobber custom career pages (BeautifulSoup HTML parsing)
- **scrapers/custom.py**: Fallback scraper for unrecognized platforms
- **filters/job_filter.py**: `JobFilter.is_match(job)` applies all filter rules from config
- **models/job.py**: `Job` dataclass with title, company, location, url, department, platform
- **storage/job_storage.py**: `JobStorage` loads/saves `storage/jobs.json` for deduplication
- **notification/local_storage.py**: `LocalStorageNotifier` generates/appends daily MD reports

### Configuration

- **config/production.yaml**: Filter keywords (tech_keywords, level_keywords, exclude_keywords, location_filter), request settings (timeout, user_agent), schedule hours
- **config/companies.json**: Array of company objects with id, name, platform, careers_url, status (active/pending)

### Platform Detection

main.py:51-112 uses the `platform` field from companies.json to select the appropriate scraper:

- `greenhouse` → GreenhouseScraper (JSON API)
- `ashby` → AshbyScraper (HTML parsing)
- `lever` → LeverScraper (HTML parsing)
- `jazzhr` → JazzHRScraper (HTML parsing)
- `bamboohr` → BambooHRScraper (Playwright + HTML parsing)
- `jobber` → JobberScraper (HTML parsing)
- fallback → CustomScraper (stub implementation)

## Adding a New Company

1. Add entry to `config/companies.json` with `"status": "active"`
2. If platform is greenhouse/ashby/lever/jazzhr/bamboohr/jobber, existing scrapers handle it
3. For custom platforms, implement in `scrapers/custom.py` or create new scraper extending `BaseScraper`

## Adding a New Scraper

1. Create `scrapers/{platform}.py` extending `BaseScraper`
2. Implement `fetch_jobs()` method returning `List[Job]`
3. Add test function and `if __name__ == '__main__'` block for standalone testing
4. Import scraper in main.py:1-17
5. Add platform detection logic in main.py:51-112
6. Update companies.json with platform value
7. Test with `python scrapers/{platform}.py`

## Special Requirements

- **BambooHR scraper**: Requires Playwright (`pip install playwright && playwright install chromium`) for JavaScript rendering
- **Deduplication**: storage/jobs.json tracks sent URLs - use `bash scripts/clean_history.sh` to reset
- **Schedule checking**: `python main.py --check` only runs if current hour matches schedule.hours in config

## Output

- **/Users/xxm/projects/QuantEngine_markdown_file/YYYY-MM-DD_匹配职位.md**: Daily job reports (Chinese filename)
- **logs/scraper.log**: Append-only execution log
- **storage/jobs.json**: Persisted URLs for deduplication

## Documentation

- **TODO.md**: Project roadmap and pending tasks
- **docs/DESIGN.md**: Technical design for new features (Lever, JazzHR, Helcim, Jobber scrapers)
- **README.md**: Project overview and usage guide
- **QUICKSTART.md**: Quick start guide
- **PROJECT_OVERVIEW.md**: Detailed project structure
