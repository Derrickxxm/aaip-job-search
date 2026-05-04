# AGENTS.md

This file provides guidance to AI coding agents working in this repository.

## Build / Lint / Test Commands

```bash
# Setup and run
bash scripts/init.sh                    # Create .venv, install deps, create directories
pip install -r requirements.txt         # Install dependencies

# Run scraper
python main.py                          # Run scraper (manual execution)
python main.py --check                  # Run only if current hour in scheduled hours

# Testing (manual, no test framework)
bash scripts/run_test.sh                # Wrapper for manual test run (activates venv, runs main.py)
python scripts/test_scraper.py          # Test single scraper (modify to test different scrapers)

# To test a specific scraper, edit scripts/test_scraper.py and change:
# - Import: from scrapers.greenhouse import GreenhouseScraper (or ashby/custom)
# - Scraper instantiation with company-specific parameters
# Then run: python scripts/test_scraper.py

# Deployment
bash scripts/deploy_crontab.sh          # Deploy crontab (runs at 8:00, 12:00, 18:00)

# Utilities
bash scripts/view_logs.sh               # tail -f logs/scraper.log
bash scripts/clean_history.sh           # Reset deduplication (clears storage/jobs.json)
```

Note: No automated linting or type checking is configured. If you add new code, consider running:
- `python -m py_compile <file>` for basic syntax checking
- `ruff check .` or `mypy .` if these tools are added in future

## Code Style Guidelines

### Imports
Order: standard library → third-party → local modules. One import per line.

```python
# Example
from abc import ABC, abstractmethod
from typing import List, Optional
import requests
from models.job import Job
from utils.logger import logger
```

### Formatting
- Indentation: 4 spaces (no tabs)
- Line length: Under 120 characters
- Docstrings: Triple double quotes (`"""`)
- Comments: Chinese documentation strings preferred for this project

### Type Hints
Required for all functions and methods. Use `typing` module.

```python
from typing import List, Optional, Set

def fetch_jobs(self) -> List[Job]:
    """抓取职位列表"""
    pass

def load_config(config_path: str = 'config/production.yaml') -> dict:
    """加载配置文件"""
    pass
```

### Naming Conventions
- Classes: PascalCase (`BaseScraper`, `JobFilter`, `JobStorage`)
- Functions/methods: snake_case (`fetch_jobs`, `load_config`, `is_match`)
- Variables: snake_case (`job_url`, `company_name`)
- Constants: snake_case (`tech_keywords`, `level_keywords`)
- Private methods: underscore prefix (`_load`, `_save`, `_ensure_dir`)
- Module files: snake_case (`job_filter.py`, `config_loader.py`)
- Module directories: snake_case (`scrapers/`, `filters/`, `storage/`)

### Error Handling
- Use try-except with specific exceptions when possible
- Return `None` or empty containers (`[]`, `set()`) on errors (not raise)
- Log/print errors for debugging
- Don't let exceptions propagate up to crash the scraper

```python
try:
    response = self.session.get(url, timeout=self.timeout)
    response.raise_for_status()
    return response
except requests.exceptions.Timeout:
    print(f"Timeout fetching {url}")
    return None
except Exception as e:
    print(f"Error: {e}")
    return []
```

### Logging
Use global logger from `utils.logger` for consistency.

```python
from utils.logger import logger

logger.info("Starting scraper")
logger.error(f"Error processing: {e}")
```
Print statements are also used for operational output (job counts, etc.).

### Classes and OOP
- Use `@dataclass` for data models (see `models/job.py`)
- Inherit from `BaseScraper` for all scrapers (abstract base class in `scrapers/base.py`)
- Static methods for utility functions without instance state

```python
@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    platform: str
    scraped_at: datetime
    department: Optional[str] = None

class JobFilter:
    def __init__(self, config: dict):
        # ...

    @staticmethod
    def load_config(config_path: str) -> dict:
        # ...
```

### File I/O
- Always use `encoding='utf-8'` for file operations
- Use context managers (`with open(...)`)
- Create directories if they don't exist (`os.makedirs`)

```python
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

if not os.path.exists(dir_path):
    os.makedirs(dir_path)
```

### Configuration
- Load config from YAML (`config/production.yaml`) using `ConfigLoader`
- Load company list from JSON (`config/companies.json`)
- Default config defined in `ConfigLoader._default_config()`

### Testing Approach
- No pytest or formal test framework
- Manual testing via `scripts/test_scraper.py`
- Each scraper module has a `test_<scraper>()` function that can be run with:
  ```python
  if __name__ == '__main__':
      test_<scraper>()
  ```
- Modify test_scraper.py to test different platforms/companies

### Adding New Scrapers
1. Create new class in `scrapers/` inheriting from `BaseScraper`
2. Implement `fetch_jobs(self) -> List[Job]` method
3. Return list of `Job` objects (from `models/job.py`)
4. Add company entry to `config/companies.json` with appropriate `platform` field
5. Update `main.py` to instantiate your scraper based on platform name

### Key Files to Understand
- `main.py` - Entry point, orchestrates scraping flow
- `scrapers/base.py` - Abstract base class for all scrapers
- `filters/job_filter.py` - Job filtering logic (tech, level, location, exclusions)
- `storage/job_storage.py` - Deduplication via URL persistence
- `notification/local_storage.py` - Markdown report generation in `/Users/xxm/projects/QuantEngine_markdown_file/`
- `models/job.py` - Job dataclass definition

### Project-Specific Patterns
- Scraper selection: `if platform == 'greenhouse': scraper = GreenhouseScraper(...)`
- Flow: fetch → filter → deduplicate → save → mark sent
- Daily reports: `/Users/xxm/projects/QuantEngine_markdown_file/YYYY-MM-DD_匹配职位.md` (Chinese filename)
- Deduplication: `storage/jobs.json` stores seen URLs
- Schedule: Runs at 8:00, 12:00, 18:00 (configurable)
