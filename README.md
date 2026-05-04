# 🎯 AAIP Job Aggregator

自动抓取AAIP P0公司职位，匹配你的技术栈和级别，保存到本地MD文件。

## 📋 功能特性

- ✅ 自动抓取P0公司职位（Benevity、Neo Financial等）
- ✅ 智能过滤：技术栈（Java/Python后端）+ 岗位级别（Senior/Staff）
- ✅ 去重机制：避免重复保存
- ✅ 本地MD存储：保存在 `/Users/xxm/projects/QuantEngine_markdown_file` 目录，按日期归档
- ✅ 日志记录：完整追踪抓取历史

## 🚀 快速开始

### 1. 环境准备

```bash
cd /Users/xxm/projects/aaip-job-search
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置（可选）

编辑 `config/production.yaml`，自定义过滤规则：

```yaml
# 可以调整这些配置
tech_keywords:      # 技术栈关键词
level_keywords:     # 岗位级别关键词
location_filter:     # 地点过滤
exclude_keywords:    # 排除关键词
```

### 3. 手动运行测试

```bash
python main.py
```

### 4. 部署定时任务

```bash
# 编辑crontab
crontab -e

# 添加以下行（替换为你的实际路径）
0 8,12,18 * * * cd /Users/xxm/projects/aaip-job-search && /usr/bin/python3 main.py >> logs/scraper.log 2>&1
```

## 📁 项目结构

```
aaip-job-search/
├── config/
│   ├── companies.json           # P0公司配置
│   └── production.yaml         # 运行配置
├── scrapers/
│   ├── base.py                # 基础抓取器
│   ├── greenhouse.py           # Greenhouse平台
│   ├── ashby.py              # Ashby平台（预留）
│   └── custom.py             # 自建网站（预留）
├── filters/
│   └── job_filter.py         # 职位过滤逻辑
├── models/
│   └── job.py               # Job数据模型
├── notification/
│   └── local_storage.py      # 本地MD存储
├── storage/
│   └── jobs.json            # 历史职位存储（去重用）
├── /Users/xxm/projects/QuantEngine_markdown_file/                        # MD文件存储目录
│   └── YYYY-MM-DD_匹配职位.md  # 每日生成的报告
├── logs/
│   └── scraper.log          # 运行日志
├── main.py                  # 主程序入口
├── requirements.txt
└── README.md
```

## 🎯 支持的公司

| 公司 | 平台 | 状态 |
|------|--------|------|
| Benevity | Greenhouse | ✅ |
| Neo Financial | Ashby | 🚧 待实现 |
| Helcim | 自建 | 🚧 待实现 |
| Jobber | 自建 | 🚧 待实现 |
| Symend | 未知 | 🚧 待调研 |
| Attabotics | 未知 | 🚧 待调研 |
| Absorb | 未知 | 🚧 待调研 |
| Showpass | 未知 | 🚧 待调研 |

## 🧧 本地MD文件示例

生成的文件位置：`/Users/xxm/projects/QuantEngine_markdown_file/2026-01-20_匹配职位.md`

```markdown
# 🎯 AAIP 匹配职位报告

**生成时间**: 2026-01-20 08:00:05
**职位数量**: 3

---

## 职位列表

### 1. Senior Staff Developer

- **公司**: Benevity
- **地点**: Toronto, Ontario, Canada
- **平台**: Greenhouse
- **链接**: [查看职位](https://hub.benevity.com/job-postings?gh_jid=5741002004)
- **部门**: Engineering

### 2. Director, Software Development

- **公司**: Benevity
- **地点**: Toronto, Ontario, Canada
- **平台**: Greenhouse
- **链接**: [查看职位](https://hub.benevity.com/job-postings?gh_jid=5740903004)
- **部门**: Engineering

### 3. Senior ML Operations

- **公司**: Benevity
- **地点**: Toronto, Ontario, Canada
- **平台**: Greenhouse
- **链接**: [查看职位](https://hub.benevity.com/job-postings?gh_jid=5736268004)
- **部门**: Data

---

*此报告由 AAIP Job Aggregator 自动生成*
*配置路径*: `config/production.yaml`
*日志路径*: `logs/scraper.log`
```

## 🔍 过滤规则

### 技术栈过滤
匹配以下关键词：
- Java
- Python
- Backend
- Software
- Platform
- Engineer
- Developer
- Data
- ML
- DevOps

### 岗位级别过滤
匹配以下关键词：
- Senior
- Staff
- Lead
- Principal
- Director
- Architect
- Manager
- Product Owner

### 地点过滤
只接受 Alberta / Toronto / Vancouver 的职位：
- Calgary, Alberta
- Edmonton, Alberta
- Alberta, Canada
- Canada, Remote
- Toronto, Ontario
- Vancouver, British Columbia

### 排除过滤
自动排除以下职位：
- Contract
- Hourly
- Internship
- Junior
- Student
- Coordinator

## 📊 运行日志

查看日志：
```bash
tail -f logs/scraper.log
```

示例输出：
```
2026-01-20 08:00:01 - INFO - ============================================================
2026-01-20 08:00:01 - INFO - Starting AAIP Job Aggregator
2026-01-20 08:00:01 - INFO - ============================================================
2026-01-20 08:00:02 - INFO - Loaded config from config/production.yaml
2026-01-20 08:00:02 - INFO - Loaded 6 companies
2026-01-20 08:00:02 - INFO - Loaded 0 historical job URLs
2026-01-20 08:00:02 - INFO - Skipping Neo Financial (status: pending)
2026-01-20 08:00:02 - INFO - Skipping Helcim (status: pending)
2026-01-20 08:00:02 - INFO - Fetching jobs from Benevity (Greenhouse)
2026-01-20 08:00:03 - INFO - Found 27 jobs from Benevity
2026-01-20 08:00:04 - INFO - ✓ Matched: Senior Staff Developer @ Benevity
2026-01-20 08:00:04 - INFO - ✓ Matched: Director, Software Development @ Benevity
2026-01-20 08:00:04 - INFO - ✗ Filtered: Product Manager @ Benevity
2026-01-20 08:00:05 - INFO - Found 2 new matching jobs
2026-01-20 08:00:05 - INFO - ✅ Saved 2 jobs to /Users/xxm/projects/QuantEngine_markdown_file/2026-01-20_匹配职位.md
2026-01-20 08:00:06 - INFO - Marked 2 jobs as sent
2026-01-20 08:00:06 - INFO - ============================================================
2026-01-20 08:00:06 - INFO - AAIP Job Aggregator completed
2026-01-20 08:00:06 - INFO - ============================================================
```

## 🛠️ 故障排查

### 问题1：抓取403错误
```
requests.exceptions.HTTPError: 403 Client Error
```
**解决**：
- 在 `config/production.yaml` 中添加User-Agent
- 或更换抓取时间间隔

### 问题2：没有生成MD文件
**检查**：
1. 查看日志：`tail -n 50 logs/scraper.log`
2. 检查 `/Users/xxm/projects/QuantEngine_markdown_file/` 目录是否存在
3. 手动运行 `python main.py` 测试

### 问题3：职位没有过滤到
**检查**：
1. 查看 `config/production.yaml` 中的过滤规则
2. 调整 `tech_keywords` 或 `level_keywords`
3. 重新运行测试

## 📈 后续计划

- [ ] Phase 2：添加Neo Financial（Ashby平台，需要Playwright）
- [ ] Phase 2：添加Helcim、Jobber等公司（自定义抓取）
- [ ] Phase 3：优化HTML解析（根据实际页面结构）
- [ ] Phase 3：Web Dashboard可视化（可选）

## 📝 License

MIT License

---

**作者**: Derrick Xu (AAIP Job Search Assistant)
**最后更新**: 2026-01-20
