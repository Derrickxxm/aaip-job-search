# 远程自由职业项目筛选系统 - 技术设计文档

> **定位**: 技术预研版 MVP。PRD 核心平台（Upwork/Contra/Toptal）因反爬和API限制暂不可直接实现，本方案先用可行平台跑通完整链路（抓取 → 硬过滤 → AI评分 → Proposal生成 → 报告/推送），后续逐步接入核心平台。

---

## 1. PRD 平台对齐分析

### PRD 优先平台 vs 技术可行性

| PRD 优先级 | 平台 | 可行性 | 降级原因 | 替代/补齐计划 |
|-----------|------|--------|---------|-------------|
| **优先** | Upwork | **不可行（Phase 1）** | 严格反爬 + Cloudflare，官方API审批周期长（数周），违反ToS有封号风险 | Phase 3：申请官方API；备选：Upwork RSS Feed（公开但数据有限） |
| **优先** | Contra | **待确认** | SPA（React），疑似需登录态，无公开API | Phase 2：Playwright + 登录态调研；若不可行则放弃 |
| **优先** | Toptal | **不可行** | 邀请制平台，项目列表不公开，无API | 无替代，从目标列表移除 |
| **优先** | Freelancer | **可行** | 有公开REST API（`developers.freelancer.com`），无需审批 | **Phase 1B 接入** |
| 次优 | LinkedIn Contract | 中等 | 可通过 Jobs RSS 或 HTML scraping，有速率限制 | Phase 2 |
| 次优 | Remote OK | **可行（首选）** | 公开 JSON API，无认证，结构化数据 | **Phase 1A 接入** |
| 次优 | WeWorkRemotely | **可行（首选）** | 公开 RSS Feed，标准格式 | **Phase 1A 接入** |
| 次优 | Wellfound | 中等 | 需要调研 | Phase 2 |

### 实施策略

Phase 1A（MVP）先用 Remote OK + WeWorkRemotely **跑通完整链路**（含AI评分和Proposal），Phase 1B 接入 Freelancer API 补充项目量，后续逐步攻克核心平台。

---

## 2. 系统架构总览

```
                         ┌──────────────────────────┐
                         │     freelance/main.py     │
                         │      主流程编排            │
                         └─────────┬────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │ RemoteOK       │  │ WeWorkRemotely │  │ Freelancer     │
     │ Scraper        │  │ Scraper        │  │ Scraper        │
     │ (JSON API)     │  │ (RSS Feed)     │  │ (REST API)     │
     └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
             └────────────────────┼────────────────────┘
                                  ▼
                     ┌───────────────────────┐
                     │   ProjectStorage      │
                     │   去重 (URL-based)     │
                     └───────────┬───────────┘
                                 ▼
                     ┌───────────────────────┐
                     │   HardFilter          │
                     │   硬门槛过滤           │
                     │   remote + contract   │
                     │   + budget            │
                     └───────────┬───────────┘
                                 ▼
                     ┌───────────────────────┐
                     │   SkillMatcher        │
                     │   技能关键词匹配       │
                     └───────────┬───────────┘
                                 ▼
                     ┌───────────────────────┐
                     │   ScoringEngine       │
                     │   (LLM) 评分 + 分析   │
                     └───────────┬───────────┘
                                 ▼
                     ┌───────────────────────┐
                     │   ProposalGenerator   │
                     │   (LLM) 投标文案生成   │
                     └───────────┬───────────┘
                                 ▼
                     ┌───────────────────────┐
                     │   Ranker              │
                     │   排序 (score/收入/概率)│
                     └───────────┬───────────┘
                                 ▼
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │ MD Report      │ │ Telegram       │ │ Email          │
     │ (本地文件)     │ │ (Bot API)      │ │ (SMTP)         │
     └────────────────┘ └────────────────┘ └────────────────┘
```

---

## 3. 目录结构

```
freelance/
├── __init__.py
├── main.py                        # 主入口，编排完整链路
├── config/
│   ├── __init__.py
│   ├── freelance.yaml             # 全局配置
│   └── candidate_profile.yaml     # 用户画像（技能、经验、偏好）
├── models/
│   ├── __init__.py
│   ├── project.py                 # FreelanceProject 原始数据模型
│   └── scored_project.py          # ScoredProject 评分后数据模型
├── scrapers/
│   ├── __init__.py
│   ├── base.py                    # FreelanceBaseScraper 基类
│   ├── remoteok.py                # Remote OK (JSON API)
│   └── weworkremotely.py          # WeWorkRemotely (RSS Feed)
├── filters/
│   ├── __init__.py
│   ├── hard_filter.py             # 硬门槛过滤（远程/合同类型/预算）
│   └── skill_matcher.py           # 技能关键词匹配
├── scoring/
│   ├── __init__.py
│   └── scoring_engine.py          # LLM 评分引擎
├── proposal/
│   ├── __init__.py
│   └── proposal_generator.py      # LLM 投标文案生成
├── ranking/
│   ├── __init__.py
│   └── ranker.py                  # 排序策略
├── compliance/
│   ├── __init__.py
│   └── compliance_filter.py       # 合规性检查
├── storage/
│   ├── __init__.py
│   └── project_storage.py         # JSON 去重存储
├── notification/
│   ├── __init__.py
│   ├── report.py                  # Markdown 报告
│   └── telegram.py                # Telegram 推送（Phase 1B）
└── utils/
    ├── __init__.py
    └── logger.py
```

---

## 4. 数据模型

### 4.1 FreelanceProject（原始抓取数据）

```python
@dataclass
class FreelanceProject:
    title: str
    description: str
    platform: str                   # remoteok / weworkremotely / freelancer
    url: str
    company: str
    location: str                   # "Remote" / "Anywhere" / 具体地点
    posted_at: datetime
    scraped_at: datetime = field(default_factory=datetime.now)

    # 预算信息（原始值）
    budget_raw: Optional[str] = None          # 原始预算文本 "$5000" / "$3k-$8k"
    hourly_rate_raw: Optional[str] = None     # 原始时薪文本 "$50/hr"
    salary_min: Optional[int] = None          # 解析后最低值（美元）
    salary_max: Optional[int] = None          # 解析后最高值（美元）
    budget_type: str = "unknown"              # "hourly" / "fixed" / "annual_salary" / "unknown"

    # 项目元数据
    tags: List[str] = field(default_factory=list)
    project_type: Optional[str] = None        # "contract" / "freelance" / "full-time" / "unknown"
    client_info: Optional[str] = None
```

### 4.2 ScoredProject（AI评分后数据）

```python
@dataclass
class ScoredProject:
    project: FreelanceProject

    # 评分结果
    score: int                      # 0-100 综合评分
    win_probability: str            # "High" / "Medium" / "Low"

    # 硬过滤分类标签（来自 HardFilter）
    filter_tag: str = "passed"      # "passed" / "pending_ai_review"

    # AI 分析
    match_reasons: List[str] = field(default_factory=list)
    risk_points: List[str] = field(default_factory=list)
    estimated_effort: str = ""      # "2-3 weeks" / "1 month"
    suggested_rate: str = ""        # "$60/hr" / "$5000 fixed"
    rate_strategy: str = ""         # "按小时计费，预估总工时40h"

    # 合规性（由 ComplianceFilter 填充，不由 ScoringEngine 填充）
    company_signable: bool = True
    compliance_flags: List[str] = field(default_factory=list)

    # 投标文案（由 ProposalGenerator 填充）
    proposal_draft: Optional[str] = None
```

### 4.3 budget_type 区分规则

Remote OK 和 WeWorkRemotely 返回的薪资数据本质上是年薪（招聘岗位），不能直接当项目预算用。需要明确区分：

```python
# budget_type 判定逻辑
if platform == "freelancer":
    budget_type = "fixed" or "hourly"  # Freelancer API 明确标注
elif salary_min or salary_max:
    budget_type = "annual_salary"       # Remote OK / WWR 的 salary 字段
elif budget_raw:
    budget_type = "fixed"               # 从 description 正则提取的项目价
elif hourly_rate_raw:
    budget_type = "hourly"              # 从 description 正则提取的时薪
else:
    budget_type = "unknown"
```

---

## 5. 平台 Scraper 设计

### 5.1 FreelanceBaseScraper

```python
class FreelanceBaseScraper(ABC):
    def __init__(self, platform: str, config: dict):
        self.platform = platform
        self.timeout = config.get('request', {}).get('timeout', 15)
        self.user_agent = config.get('request', {}).get('user_agent', '...')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

    @abstractmethod
    def fetch_projects(self) -> List[FreelanceProject]:
        pass

    def _request(self, url: str) -> Optional[requests.Response]:
        # 同现有 BaseScraper._request()，含 timeout/error handling
        pass
```

### 5.2 Remote OK Scraper

**数据源**: `https://remoteok.com/api` (公开 JSON API)

**API 响应结构**:
```json
[
  {"legal": "..."},
  {
    "id": "1130874",
    "position": "Senior Python Developer",
    "company": "Acme Corp",
    "description": "<p>HTML description...</p>",
    "tags": ["python", "senior", "developer"],
    "location": "Remote",
    "salary_min": 80000,
    "salary_max": 120000,
    "date": "2026-03-25T10:00:00+00:00",
    "url": "/remote-jobs/1130874",
    "apply_url": "https://..."
  }
]
```

**字段映射**:

| API 字段 | FreelanceProject 字段 |
|----------|----------------------|
| position | title |
| company | company |
| description | description |
| tags | tags |
| location | location |
| salary_min | salary_min |
| salary_max | salary_max |
| — | budget_type = "annual_salary" |
| date | posted_at |
| url (拼接 `https://remoteok.com`) | url |
| — | platform = "remoteok" |
| — | project_type：从 tags/description 推断 |

**注意**：
- 跳过 `response[0]`（法律声明）
- Cloudflare 缓存 1 小时，不要频繁请求
- 法律要求：输出中需注明数据来源

### 5.3 WeWorkRemotely Scraper

**数据源**: RSS Feed（多个分类）

```
https://weworkremotely.com/categories/remote-programming-jobs.rss
https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss
https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss
```

**RSS Item 结构**:
```xml
<item>
  <title>Flexport: Product Data Analyst II</title>
  <region>Anywhere in the World</region>
  <category>Full-Stack Programming</category>
  <description>HTML-encoded job description...</description>
  <pubDate>Mon, 24 Mar 2026 14:00:00 +0000</pubDate>
  <link>https://weworkremotely.com/remote-jobs/flexport-...</link>
</item>
```

**实现要点**:
- `<title>` 格式 `"Company: Job Title"`，用 `: ` 分割
- 多个 feed 合并，按 `<link>` 去重
- 薪资从 `<description>` 正则提取：
  ```python
  r'\$[\d,]+\s*[-–]\s*\$[\d,]+'      # $80,000 - $120,000
  r'\$[\d,]+/(?:hr|hour|year|yr)'      # $50/hr
  ```
- project_type 从 description 关键词推断（contract/freelance/full-time）

### 5.4 Freelancer Scraper（Phase 1B）

**数据源**: `https://www.freelancer.com/api/projects/0.1/projects/active/`

**优势**: 公开 REST API，项目有明确的 budget/hourly 标注，有 client 评分数据。

**待调研**: API 是否需要注册 OAuth App、速率限制。

### 5.5 核心平台补齐计划

| 平台 | 预研方式 | 时间线 |
|------|---------|--------|
| Upwork | 1) 测试 RSS Feed (https://www.upwork.com/ab/feed/jobs/rss?...) 2) 申请官方 API 3) Playwright + cookie | Phase 3 |
| Contra | Playwright 抓包，检查 GraphQL 端点 | Phase 2 |
| LinkedIn | Jobs RSS 或 `linkedin.com/jobs/search/?f_WT=2&f_JT=C` HTML scraping | Phase 2 |

---

## 6. 硬门槛过滤（HardFilter）

PRD 硬条件：**必须远程** + **必须合同/外包/自由职业** + **预算达标**。

### 6.1 HardFilter 类

```python
class HardFilter:
    def __init__(self, config: dict):
        self.min_hourly_rate = config['filter']['min_hourly_rate']       # 30
        self.min_project_budget = config['filter']['min_project_budget'] # 2000

    def apply(self, project: FreelanceProject) -> Tuple[bool, str]:
        """返回 (是否通过, 分类标签)
        分类: "passed" / "rejected_fulltime" / "rejected_not_remote" /
              "rejected_low_budget" / "pending_ai_review"

        pending_ai_review 表示硬门槛有部分信息缺失（预算不明 或 项目类型不明确），
        不直接拒绝，但降级交给 AI 评分时额外评估风险。
        """

        # Gate 1: 必须远程
        if not self._is_remote(project):
            return False, "rejected_not_remote"

        # Gate 2: 必须是 contract/freelance 类型
        type_check = self._check_project_type(project)
        if type_check == "fulltime":
            return False, "rejected_fulltime"
        type_ambiguous = (type_check == "ambiguous")

        # Gate 3: 预算检查
        budget_check = self._check_budget(project)
        if budget_check == "low":
            return False, "rejected_low_budget"
        budget_unknown = (budget_check == "unknown")

        # 任一维度不明确 → 降级为 pending_ai_review
        # 设计说明: PRD 要求"必须是 contract/freelance"，但 Remote OK / WWR
        # 的大量项目不会在描述中显式标注项目类型。如果严格拒绝 ambiguous，
        # 会丢失大量潜在合适项目。因此这里有意识地放宽为"降级而非拒绝"，
        # 由 AI 评分环节再做二次判断（见 ScoringEngine 的 filter_tag 处理）。
        if type_ambiguous or budget_unknown:
            return True, "pending_ai_review"

        return True, "passed"
```

### 6.2 远程检查 `_is_remote()`

```python
def _is_remote(self, project):
    loc = project.location.lower()
    text = (project.title + " " + project.description[:500]).lower()

    remote_signals = ['remote', 'anywhere', 'worldwide', 'work from home',
                      'distributed', 'location independent']
    onsite_signals = ['onsite', 'on-site', 'in-office', 'hybrid',
                      'must be located in', 'relocation required']

    has_remote = any(s in loc or s in text for s in remote_signals)
    has_onsite = any(s in text for s in onsite_signals)

    # Remote OK 平台的项目默认远程
    if project.platform == "remoteok":
        return not has_onsite

    return has_remote and not has_onsite
```

### 6.3 项目类型检查 `_check_project_type()`

```python
def _check_project_type(self, project) -> str:
    """返回 "contract" / "fulltime" / "ambiguous" """
    text = (project.title + " " + project.description[:1000]).lower()

    contract_signals = ['contract', 'freelance', 'freelancer', 'project-based',
                        'outsource', 'consulting', 'contractor', 'hourly',
                        'fixed price', 'fixed-price', 'per project', 'gig']
    fulltime_signals = ['full-time', 'full time', 'permanent', 'w-2',
                        'benefits included', 'equity', '401k', 'pto',
                        'annual salary', 'salaried position']

    has_contract = any(s in text for s in contract_signals)
    has_fulltime = any(s in text for s in fulltime_signals)

    if has_contract and not has_fulltime:
        return "contract"
    if has_fulltime and not has_contract:
        return "fulltime"

    # 平台默认推断
    if project.platform == "freelancer":
        return "contract"   # Freelancer 平台天然是外包

    return "ambiguous"  # 不确定 → HardFilter 会降级为 pending_ai_review
```

### 6.4 预算检查 `_check_budget()`

```python
def _check_budget(self, project) -> str:
    """返回 "ok" / "low" / "unknown" """

    # Case 1: 有明确时薪
    if project.budget_type == "hourly" and project.salary_min:
        return "ok" if project.salary_min >= self.min_hourly_rate else "low"

    # Case 2: 有固定项目价
    if project.budget_type == "fixed" and project.salary_min:
        return "ok" if project.salary_min >= self.min_project_budget else "low"

    # Case 3: 年薪数据（Remote OK / WWR 的招聘岗位）
    # 年薪 ≠ 自由职业预算，不用这个数据做硬过滤
    # 但可以作为"收入潜力"参考，交给评分引擎处理
    if project.budget_type == "annual_salary":
        return "unknown"  # 不做硬过滤，降级给AI评估

    # Case 4: 完全无预算信息
    return "unknown"
```

### 6.5 "pending_ai_review" 的处理

硬门槛过滤后，项目分三档：

| 分类 | 触发条件 | 处理 |
|------|---------|------|
| `passed` | 三项硬门槛全部明确通过 | 进入技能匹配 → AI评分 → 正常输出 |
| `pending_ai_review` | 远程确认，但项目类型 ambiguous 或预算 unknown | 进入技能匹配 → AI评分（Prompt 中注入 filter_tag，要求 LLM 额外判断项目类型和预算合理性）→ 输出时标注"待确认"标签 |
| `rejected_*` | 明确命中 fulltime / not_remote / low_budget | 直接丢弃，记录日志 |

> **对 PRD 的有意识放宽**: PRD 要求"必须是 contract/freelance/outsourcing"，但 Remote OK 和 WeWorkRemotely 上大量项目不会在描述中显式标注类型。如果严格拒绝所有 ambiguous 项目，Phase 1A 的项目量会极少。因此将 ambiguous 降级为 `pending_ai_review` 而非硬拒，由 AI 评分做二次判断。待 Phase 1B 接入 Freelancer（项目类型字段明确）后，可重新收紧此规则。

---

## 7. 技能匹配（SkillMatcher）

```python
class SkillMatcher:
    def __init__(self, config: dict):
        self.strong_keywords = config['filter']['strong_keywords']
        self.exclude_keywords = config['filter']['exclude_keywords']

    def is_match(self, project: FreelanceProject) -> Tuple[bool, List[str]]:
        """返回 (是否匹配, 命中的关键词列表)"""
        searchable = ' '.join([
            project.title,
            ' '.join(project.tags),
            project.description[:2000]
        ]).lower()

        # 排除检查
        for kw in self.exclude_keywords:
            if kw in searchable:
                return False, []

        # 技能匹配
        matched_keywords = [kw for kw in self.strong_keywords if kw in searchable]
        return len(matched_keywords) > 0, matched_keywords
```

**关键词配置**:

```yaml
filter:
  strong_keywords:
    - python
    - java
    - backend
    - back-end
    - back end
    - api
    - openai
    - llm
    - chatgpt
    - ai
    - automation
    - trading
    - crypto
    - data pipeline
    - data engineer
    - distributed
    - microservice
    - payment
    - fintech
    - fastapi
    - spring boot

  exclude_keywords:
    - junior
    - intern
    - internship
    - entry level
    - entry-level
    - wordpress
    - shopify theme
    - data entry
    - virtual assistant
    - customer service
    - graphic design
    - video editing
    - social media manager
```

---

## 8. 评分引擎（ScoringEngine）

### 8.1 评分维度

按 PRD 权重：

| 因素 | 权重 | 数据来源 |
|------|------|---------|
| 技能匹配度 | 40% | SkillMatcher 命中关键词数量 + LLM 深度分析 |
| 预算水平 | 25% | budget_type + salary_min/max |
| 项目清晰度 | 15% | LLM 判断 description 质量 |
| 客户质量 | 10% | client_info（Freelancer 有评分；其他平台由 LLM 推断） |
| 竞争强度 | 10% | LLM 根据项目特征估算 |

### 8.2 实现方式：规则预打分 + LLM 精评

```python
class ScoringEngine:
    def __init__(self, config: dict, candidate_profile: dict):
        self.llm_client = anthropic.Anthropic()
        self.model = config['scoring']['model']  # claude-haiku-4-5-20251001
        self.rule_threshold = config['scoring']['rule_score_threshold']  # 40
        self.max_llm = config['scoring']['max_llm_per_run']  # 30
        self.candidate_profile = candidate_profile

    def score(self, project: FreelanceProject,
              matched_keywords: List[str],
              filter_tag: str) -> ScoredProject:
        """
        评分引擎只负责评分和分析，不做合规检查。
        合规检查由独立的 ComplianceFilter 在主流程中执行。

        Args:
            filter_tag: "passed" 或 "pending_ai_review"，
                        后者会在 LLM Prompt 中注入额外指令，
                        要求 AI 对项目类型和预算合理性做二次判断。
        """

        # Step 1: 规则预打分（快速，不消耗API）
        rule_score = self._rule_based_score(project, matched_keywords)

        # Step 2: LLM 精评（仅对规则预打分 >= threshold 的项目调用）
        if rule_score >= self.rule_threshold:
            llm_result = self._llm_score(project, matched_keywords, filter_tag)
        else:
            llm_result = self._default_low_score(project)

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
            # 合规字段由主流程填充，评分引擎不负责
            company_signable=True,
            compliance_flags=[],
        )
```

> **职责边界**: ScoringEngine 只输出评分和分析结果。合规字段（`company_signable`、`compliance_flags`）由主流程调用独立的 `ComplianceFilter` 填充，避免两套入口。

### 8.3 规则预打分（无LLM）

```python
def _rule_based_score(self, project, matched_keywords) -> int:
    score = 0

    # 技能匹配度 (0-40)
    kw_count = len(matched_keywords)
    if kw_count >= 3: score += 40
    elif kw_count == 2: score += 30
    elif kw_count == 1: score += 15

    # 预算水平 (0-25)
    if project.budget_type == "hourly" and project.salary_min:
        if project.salary_min >= 60: score += 25
        elif project.salary_min >= 40: score += 18
        elif project.salary_min >= 30: score += 10
    elif project.budget_type == "fixed" and project.salary_min:
        if project.salary_min >= 10000: score += 25
        elif project.salary_min >= 5000: score += 18
        elif project.salary_min >= 2000: score += 10
    # annual_salary / unknown: 不加分也不扣分

    # 项目清晰度 (0-15) — 按 description 长度粗估
    desc_len = len(project.description)
    if desc_len >= 500: score += 15
    elif desc_len >= 200: score += 10
    elif desc_len >= 50: score += 5

    # 客户质量 (0-10) — 仅 Freelancer 有数据，其他默认5分
    score += 5

    # 竞争强度 (0-10) — 规则层面无法判断，默认5分
    score += 5

    return min(score, 100)
```

### 8.4 LLM 精评 Prompt

```python
SCORING_PROMPT = """你是一个自由职业项目评估专家。请基于以下候选人画像和项目信息，给出评估。

## 候选人画像
{candidate_profile}

## 项目信息
- 标题: {title}
- 平台: {platform}
- 预算: {budget_info}
- 标签: {tags}
- 描述: {description_truncated}

## 已匹配关键词
{matched_keywords}

## 请输出以下 JSON（不要输出其他内容）:
{{
  "score": <0-100 综合评分>,
  "win_probability": "<High/Medium/Low>",
  "match_reasons": ["<原因1>", "<原因2>"],
  "risk_points": ["<风险1>", "<风险2>"],
  "estimated_effort": "<预估工作量，如 2-3 weeks>",
  "suggested_rate": "<建议报价，如 $60/hr 或 $5000 fixed>",
  "rate_strategy": "<报价策略说明>"
}}
"""
```

### 8.5 API 成本控制

| 策略 | 说明 |
|------|------|
| 规则预打分门槛 | 预打分 < 40 的项目不调 LLM，直接给默认低分 |
| 使用 Haiku | 评分用 `claude-haiku-4-5-20251001`，成本约 $0.001/次 |
| Description 截断 | LLM 输入只取 description 前 1500 字符 |
| 批量上限 | 每轮最多对 30 个项目调 LLM |
| 预估日成本 | 3次/天 × ~15个项目/次 × $0.001 ≈ **$0.05/天** |

---

## 9. 投标文案生成（ProposalGenerator）

### 9.1 生成结构（对齐 PRD）

```
1. 开头 — 针对客户需求定制，不超过2句
2. 相关经验 — 匹配的项目经历（从 candidate_profile 提取）
3. 解决方案思路 — 针对项目的技术方案概要
4. 收尾 + CTA — 行动号召
```

### 9.2 类接口

```python
class ProposalGenerator:
    def __init__(self, config: dict, candidate_profile: dict):
        self.llm_client = anthropic.Anthropic()
        self.model = config['proposal']['model']  # claude-sonnet-4-6
        self.min_score = config['proposal']['min_score_to_generate']  # 60
        self.max_per_run = config['proposal']['max_proposals_per_run']  # 10
        self.candidate_profile = candidate_profile

    def generate(self, scored_project: ScoredProject) -> Optional[str]:
        """为高分项目生成投标草稿。返回 Proposal 文本或 None。"""
        if scored_project.score < self.min_score:
            return None

        prompt = self._build_prompt(scored_project)
        response = self.llm_client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def _build_prompt(self, sp: ScoredProject) -> str:
        return PROPOSAL_PROMPT.format(
            candidate_profile=yaml.dump(self.candidate_profile),
            title=sp.project.title,
            description_truncated=sp.project.description[:1500],
            budget_info=self._format_budget(sp.project),
            matched_keywords=', '.join(sp.match_reasons),
            suggested_rate=sp.suggested_rate,
            rate_strategy=sp.rate_strategy,
        )
```

### 9.3 Prompt

```python
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
```

### 9.4 生成策略

| 策略 | 说明 |
|------|------|
| 仅对高分项目生成 | score >= 60 才生成 Proposal |
| 使用 Sonnet | Proposal 质量要求高，用 `claude-sonnet-4-6` |
| 生成的是草稿 | 标注"建议人工审核后再投"，不做全自动投标 |
| 预估成本 | 每次 ~$0.005，日均 5 个高分项目 ≈ $0.025/天 |

---

## 10. 排序策略（Ranker）

### 10.1 排序规则

按 PRD 要求，三级排序：

```python
class Ranker:
    def rank(self, scored_projects: List[ScoredProject]) -> List[ScoredProject]:
        return sorted(scored_projects, key=lambda p: (
            -p.score,                           # 1. 评分最高
            -self._income_potential(p),          # 2. 收入潜力最大
            -self._win_prob_value(p),            # 3. 中标概率最高
        ))

    def _income_potential(self, p: ScoredProject) -> int:
        proj = p.project
        if proj.budget_type == "hourly" and proj.salary_max:
            return proj.salary_max * 160   # 假设1个月
        if proj.budget_type == "fixed" and proj.salary_max:
            return proj.salary_max
        return 0

    def _win_prob_value(self, p: ScoredProject) -> int:
        return {"High": 3, "Medium": 2, "Low": 1}.get(p.win_probability, 0)
```

---

## 11. 合规性过滤（ComplianceFilter）

### 11.1 PRD 合规要求

- 所有项目必须通过用户公司签约
- 不得以个人身份接单
- 避免被认定为为其他雇主工作（封闭工签限制）

### 11.2 合规检查规则

```python
class ComplianceFilter:
    def check(self, project: FreelanceProject) -> dict:
        flags = []
        company_signable = True
        text = (project.title + " " + project.description[:1000]).lower()

        # 检查1: 是否疑似 employer-style 全职雇佣
        employer_signals = ['w-2', 'must be employee', 'employment agreement',
                            'non-compete', 'exclusive', 'full-time only',
                            'payroll', 'direct hire']
        for signal in employer_signals:
            if signal in text:
                flags.append(f"疑似雇佣关系: 包含 '{signal}'")
                company_signable = False

        # 检查2: 是否要求特定国家工作许可
        visa_signals = ['must be authorized to work in',
                        'us citizens only', 'clearance required',
                        'work permit required']
        for signal in visa_signals:
            if signal in text:
                flags.append(f"工作许可限制: 包含 '{signal}'")

        # 检查3: 是否要求 onsite（与远程检查互补）
        if 'onsite' in text or 'on-site' in text or 'in-office' in text:
            flags.append("要求到场工作")
            company_signable = False

        return {
            'company_signable': company_signable,
            'flags': flags
        }
```

### 11.3 输出中的合规提示

每个项目输出时，如果有合规 flag，会在报告中显示：

```markdown
> ⚠️ 合规提示: 疑似雇佣关系（包含 'non-compete'）— 建议确认是否接受公司主体签约
```

---

## 12. 候选人画像配置

### freelance/config/candidate_profile.yaml

```yaml
name: "[公司名称]"
entity_type: "Canadian Corporation"
experience_years: 16

core_skills:
  - Java 后端架构（16年）
  - Python + Pandas
  - 分布式系统
  - 高并发 / 高性能系统
  - 支付系统

advanced_skills:
  - 量化交易系统（crypto）
  - 数据管道（Data Pipeline）
  - AI / LLM 集成（OpenAI, Claude）
  - 自动化系统
  - FastAPI / Spring Boot

preferred_projects:
  - AI 自动化
  - ChatGPT / LLM 集成
  - 后端系统开发
  - 交易系统 / 量化相关
  - 数据工程

portfolio_highlights:
  - "Built a high-frequency crypto trading system processing 10K+ orders/sec"
  - "Designed distributed payment platform handling $50M+ annual transactions"
  - "Developed AI-powered automation pipeline integrating OpenAI APIs"
  - "Architected microservices backend serving 1M+ daily active users"
```

该文件供 ScoringEngine 和 ProposalGenerator 读取，用于生成个性化评分和投标文案。

---

## 13. 通知管道（Notification Pipeline）

### 13.1 Markdown 报告（Phase 1A）

**文件命名**: `YYYY-MM-DD_远程项目.md`

**报告结构**:

```markdown
# 远程项目匹配报告

**日期**: 2026-03-25 14:00:05
**匹配数量**: 5 (高分: 2, 中分: 2, 待确认: 1)
**数据来源**: Remote OK, WeWorkRemotely

---

## 🔥 1. AI Customer Support Automation [Score: 87 | Win: High]

- **公司**: TechStartup Inc
- **平台**: Remote OK
- **预算**: 未披露 (年薪参考: $80K-$120K)
- **类型**: Contract
- **标签**: python, openai, automation
- **链接**: [查看项目](https://remoteok.com/remote-jobs/...)

### 匹配分析
- ✅ Python + OpenAI 高度匹配，16年后端架构经验
- ✅ 自动化系统与核心能力吻合
- ⚠️ 预算未明确披露

### 风险点
- 客户无历史评价
- 项目范围可能扩大

### 建议
- **预估工作量**: 2-3 weeks
- **建议报价**: $55/hr（按小时）或 $4,500（固定价格，预留 buffer）
- **策略**: 按小时计费，首期限定 scope，降低双方风险

### 投标草稿
> I noticed you're looking for an AI-powered customer support system — this is
> exactly what I've been building for the past 2 years. I recently developed a
> similar automation pipeline using Python + OpenAI that reduced manual support
> tickets by 60%...
>
> ⚡ *建议人工审核后再投*

### 合规状态
✅ 适合公司主体签约

---

## 2. Backend API Developer [Score: 72 | Win: Medium]
...

---

*数据来源: [Remote OK](https://remoteok.com), [WeWorkRemotely](https://weworkremotely.com)*
*由 Freelance Project Scanner 自动生成*
```

### 13.2 Telegram 推送（Phase 1B）

```python
class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_summary(self, scored_projects: List[ScoredProject]):
        """推送高分项目摘要"""
        high_score = [p for p in scored_projects if p.score >= 70]
        if not high_score:
            return

        msg = f"🎯 发现 {len(high_score)} 个高分远程项目:\n\n"
        for p in high_score[:5]:
            msg += f"• [{p.score}分] {p.project.title}\n"
            msg += f"  {p.win_probability} | {p.suggested_rate}\n"
            msg += f"  {p.project.url}\n\n"

        self._send(msg)
```

配置:
```yaml
notification:
  telegram:
    enabled: false               # Phase 1B 启用
    bot_token_env: TELEGRAM_BOT_TOKEN
    chat_id_env: TELEGRAM_CHAT_ID
  email:
    enabled: false               # Phase 2
```

---

## 14. 配置文件汇总

### freelance/config/freelance.yaml

```yaml
schedule:
  interval_hours: 6              # 每6小时抓取一次（对齐 PRD）
  hours: [2, 8, 14, 20]          # 具体时间点

platforms:
  remoteok:
    enabled: true
    url: https://remoteok.com/api
  weworkremotely:
    enabled: true
    feeds:
      - https://weworkremotely.com/categories/remote-programming-jobs.rss
      - https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss
      - https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss
  freelancer:
    enabled: false               # Phase 1B
    url: https://www.freelancer.com/api/projects/0.1/projects/active/
  contra:
    enabled: false               # 待调研

filter:
  strong_keywords:
    - python
    - java
    - backend
    - back-end
    - back end
    - api
    - openai
    - llm
    - chatgpt
    - ai
    - automation
    - trading
    - crypto
    - data pipeline
    - data engineer
    - distributed
    - microservice
    - payment
    - fintech
    - fastapi
    - spring boot

  exclude_keywords:
    - junior
    - intern
    - internship
    - entry level
    - entry-level
    - wordpress
    - shopify theme
    - data entry
    - virtual assistant
    - customer service
    - graphic design
    - video editing
    - social media manager

  min_hourly_rate: 30
  min_project_budget: 2000

scoring:
  model: claude-haiku-4-5-20251001
  api_key_env: ANTHROPIC_API_KEY
  rule_score_threshold: 40       # 预打分低于此值不调 LLM
  max_llm_per_run: 30            # 每轮最多 LLM 评分数

proposal:
  model: claude-sonnet-4-6
  api_key_env: ANTHROPIC_API_KEY
  min_score_to_generate: 60      # score >= 60 才生成 Proposal
  max_proposals_per_run: 10

output:
  vault_dir: /Users/xxm/projects/QuantEngine_markdown_file/12-找工作
  filename_prefix: "远程项目"

notification:
  telegram:
    enabled: false
    bot_token_env: TELEGRAM_BOT_TOKEN
    chat_id_env: TELEGRAM_CHAT_ID
  email:
    enabled: false

storage:
  path: freelance/storage/freelance_projects.json

request:
  timeout: 15
  user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

debug:
  enabled: true
```

---

## 15. 主流程（Main Pipeline）

```python
def main():
    config = load_config('freelance/config/freelance.yaml')
    candidate = load_candidate_profile()

    # 初始化组件
    storage = ProjectStorage(config)
    hard_filter = HardFilter(config)
    skill_matcher = SkillMatcher(config)
    scoring_engine = ScoringEngine(config, candidate)
    proposal_gen = ProposalGenerator(config, candidate)
    ranker = Ranker()
    report = ReportNotifier(config)

    # ===== Stage 1: 抓取 =====
    raw_projects = []
    for scraper in get_enabled_scrapers(config):
        raw_projects.extend(scraper.fetch_projects())
    logger.info(f"Fetched {len(raw_projects)} raw projects")

    # ===== Stage 2: 去重 =====
    new_projects = [p for p in raw_projects if not storage.is_sent(p.url)]
    logger.info(f"After dedup: {len(new_projects)} new projects")

    # ===== Stage 3: 硬门槛过滤 =====
    candidates = []         # (project, filter_tag)
    for p in new_projects:
        passed, tag = hard_filter.apply(p)
        if passed:
            candidates.append((p, tag))
        else:
            logger.debug(f"Hard filter rejected: {p.title} ({tag})")
    logger.info(f"After hard filter: {len(candidates)} candidates")

    # ===== Stage 4: 技能匹配 =====
    matched = []            # (project, filter_tag, matched_keywords)
    for p, tag in candidates:
        is_match, keywords = skill_matcher.is_match(p)
        if is_match:
            matched.append((p, tag, keywords))
        else:
            logger.debug(f"Skill mismatch: {p.title}")
    logger.info(f"After skill match: {len(matched)} matched")

    # ===== Stage 5: AI 评分 =====
    scored = []
    for p, tag, keywords in matched:
        scored_project = scoring_engine.score(p, keywords, tag)
        scored.append(scored_project)
    logger.info(f"Scored {len(scored)} projects")

    # ===== Stage 6: 合规检查（独立模块，统一入口）=====
    compliance_filter = ComplianceFilter()
    for sp in scored:
        result = compliance_filter.check(sp.project)
        sp.company_signable = result['company_signable']
        sp.compliance_flags = result['flags']

    # ===== Stage 7: Proposal 生成 =====
    for sp in scored:
        sp.proposal_draft = proposal_gen.generate(sp)  # 内部判断 score 门槛

    # ===== Stage 8: 排序 =====
    ranked = ranker.rank(scored)

    # ===== Stage 9: 输出 =====
    if ranked:
        report.generate_daily_report(ranked)
        storage.mark_sent([sp.project.url for sp in ranked])
        logger.info(f"Generated report with {len(ranked)} projects")

        # Telegram 推送（如果启用）
        if config['notification']['telegram']['enabled']:
            TelegramNotifier(config).send_summary(ranked)
    else:
        logger.info("No matching projects found")
```

---

## 16. 依赖

```
# 现有
requests
beautifulsoup4
pyyaml

# 新增
feedparser>=6.0            # WeWorkRemotely RSS
anthropic>=0.40.0          # Claude API (评分 + Proposal)
```

---

## 17. Phase 路线图

| Phase | 内容 | 交付物 | 预估成本 |
|-------|------|--------|---------|
| **1A** | Remote OK + WWR scraper，硬过滤，技能匹配，AI评分，Proposal生成，MD报告 | 完整链路可运行 | ~$0.08/天 API |
| **1B** | Freelancer API 接入，Telegram 推送 | 增加项目来源 + 实时通知 | 同上 |
| **2** | Contra 调研 + 接入，LinkedIn Contract，Wellfound | 扩大覆盖面 | 需 Playwright |
| **3** | Upwork（官方API申请 / RSS / 浏览器自动化） | 接入核心平台 | 待定 |
| **4** | 自动投标（浏览器自动化 + 人工审核流程） | 半自动投标 | 谨慎推进 |

---

## 18. 待决策事项

1. **candidate_profile.yaml 中的公司名称和 portfolio** — 需要你填写真实信息
2. **Telegram Bot** — 是否现在就创建？需要 BotFather 创建 bot + 获取 chat_id
3. **Freelancer API** — 是否需要我先调研注册流程和 API 限制？
4. **LLM 选型** — 评分用 Haiku、Proposal 用 Sonnet，这个分配是否 OK？
