# 快速开始指南

## 1️⃣ 安装和配置

### 步骤1：初始化环境

```bash
cd /Users/xxm/projects/aaip-job-search
bash scripts/init.sh
```

### 步骤2：配置过滤规则（可选）

编辑 `config/production.yaml`，自定义：

```yaml
# 技术栈关键词
tech_keywords:
  - Java
  - Python
  - Backend
  - Software
  - Platform
  - Engineer
  - Developer
  - Data
  - ML

# 岗位级别关键词
level_keywords:
  - Senior
  - Staff
  - Lead
  - Principal
  - Director
  - Architect

# 地点过滤
location_filter:
  - Calgary, Alberta
  - Edmonton, Alberta
  - Alberta, Canada
  - Canada, Remote
  - Toronto, Ontario
  - Vancouver, British Columbia

# 排除关键词
exclude_keywords:
  - contract
  - hourly
  - internship
  - junior
  - intern
```

---

## 2️⃣ 测试运行

### 手动测试（推荐首次使用）

```bash
bash scripts/run_test.sh
```

或测试单个抓取器：

```bash
python scripts/test_scraper.py
```

预期输出：
```
==========================================
🧪 手动运行测试
==========================================

Fetching jobs from Benevity (Greenhouse)
Found 27 jobs from Benevity
✓ Matched: Senior Staff Developer @ Benevity
✓ Matched: Director, Software Development @ Benevity
...
✅ Saved 2 jobs to /Users/xxm/projects/QuantEngine_markdown_file/2026-01-20_匹配职位.md
```

---

## 3️⃣ 部署定时任务

### 自动部署crontab

```bash
bash scripts/deploy_crontab.sh
```

### 手动添加（如果脚本失败）

```bash
crontab -e
```

添加以下行：

```cron
0 8,12,18 * * * cd /Users/xxm/projects/aaip-job-search && /usr/bin/python3 main.py >> logs/scraper.log 2>&1
```

---

## 4️⃣ 查看结果

### 查看生成的MD报告

```bash
# 查看最新的报告
ls -lt /Users/xxm/projects/QuantEngine_markdown_file/

# 打开当天的报告
open /Users/xxm/projects/QuantEngine_markdown_file/$(date +%Y-%m-%d)_匹配职位.md
```

### 实时查看日志

```bash
bash scripts/view_logs.sh
```

---

## 5️⃣ 常用命令

| 命令 | 说明 |
|------|------|
| `bash scripts/run_test.sh` | 手动运行一次（测试用）|
| `bash scripts/view_logs.sh` | 实时查看日志 |
| `bash scripts/clean_history.sh` | 清理历史职位记录 |
| `ls -lt /Users/xxm/projects/QuantEngine_markdown_file/` | 查看生成的MD报告 |
| `crontab -l` | 查看当前定时任务 |
| `crontab -e` | 编辑定时任务 |

---

## 🐛 故障排查

### 问题1：抓取403错误

```
requests.exceptions.HTTPError: 403 Client Error
```

**解决**：
- 暂时无法解决，可能需要添加更多Headers
- 可以在`config/production.yaml`中修改`user_agent`

### 问题2：没有生成MD文件

**检查**：
1. 查看日志：`tail -n 100 logs/scraper.log`
2. 检查 vault 目录：`ls -la /Users/xxm/projects/QuantEngine_markdown_file/`
3. 手动运行测试：`bash scripts/run_test.sh`

### 问题3：crontab不执行

**检查**：
```bash
# 查看crontab
crontab -l

# 检查python路径
which python3

# 手动测试命令
cd /Users/xxm/projects/aaip-job-search && python3 main.py
```

---

## 📊 预期效果

### MD报告示例

文件位置：`/Users/xxm/projects/QuantEngine_markdown_file/2026-01-20_匹配职位.md`

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

---

*此报告由 AAIP Job Aggregator 自动生成*
*配置路径*: `config/production.yaml`
*日志路径*: `logs/scraper.log`
```

### 日志示例

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

---

## 📈 下一步

- [ ] 测试实际Benevity页面HTML结构
- [ ] 根据实际情况调整解析逻辑
- [ ] 添加Neo Financial（Ashby平台）
- [ ] 添加Helcim、Jobber
- [ ] 优化过滤规则

---

**需要帮助？** 查看日志文件：`logs/scraper.log`
