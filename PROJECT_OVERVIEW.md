# AAIP Job Aggregator - 项目概览

## 📁 项目结构

```
aaip-job-search/
├── config/                          # 配置文件
│   ├── companies.json           # P0公司列表（6家）
│   ├── production.yaml         # 生产环境配置
│   └── dev.yaml              # 开发环境配置
│
├── scrapers/                        # 抓取器模块
│   ├── base.py                # 基础抓取器类（抽象）
│   ├── greenhouse.py           # Greenhouse平台实现
│   ├── ashby.py              # Ashby平台（待实现）
│   └── custom.py             # 自建网站（待实现）
│
├── filters/                         # 过滤器模块
│   └── job_filter.py         # 职位过滤逻辑
│
├── models/                          # 数据模型
│   └── job.py               # Job数据类
│
├── notification/                    # 通知模块
│   └── email.py             # 邮件通知器
│
├── storage/                         # 存储模块
│   └── job_storage.py       # 历史职位管理
│
├── utils/                           # 工具模块
│   ├── config_loader.py      # 配置加载器
│   └── logger.py            # 日志系统
│
├── scripts/                         # 辅助脚本
│   ├── init.sh              # 初始化环境（安装依赖）
│   ├── run_test.sh          # 手动运行测试
│   ├── test_scraper.py       # 测试单个抓取器
│   ├── deploy_crontab.sh    # 部署crontab
│   ├── view_logs.sh         # 查看实时日志
│   └── clean_history.sh     # 清理历史记录
│
├── logs/                            # 日志目录（自动创建）
│   └── scraper.log         # 运行日志
│
├── storage/                         # 数据存储目录
│   └── jobs.json            # 历史职位URL（去重用）
│
├── main.py                          # 主程序入口
├── requirements.txt                  # Python依赖
├── README.md                        # 项目说明
├── QUICKSTART.md                   # 快速开始指南
├── CHANGELOG.md                    # 更新日志
└── .gitignore                      # Git忽略文件
```

---

## 🎯 核心功能

### 1. 抓取器（Scrapers）

| 文件 | 平台 | 状态 |
|------|--------|------|
| `scrapers/greenhouse.py` | Greenhouse | ✅ 实现完成 |
| `scrapers/ashby.py` | Ashby | 🚧 预留（需JS渲染）|
| `scrapers/custom.py` | 自建网站 | 🚧 预留 |

### 2. 过滤器（Filters）

**`filters/job_filter.py`** 实现以下过滤：

- ✅ **技术栈过滤**：Java, Python, Backend, Software, Platform
- ✅ **级别过滤**：Senior, Staff, Lead, Principal
- ✅ **地点过滤**：Calgary, Alberta, Edmonton, Alberta, Canada Remote
- ✅ **排除过滤**：contract, hourly, internship, junior

### 3. 通知系统（Notification）

**`notification/email.py`** 实现Gmail通知：

- ✅ HTML格式邮件
- ✅ 每次汇总所有匹配职位
- ✅ 一键投递链接
- ✅ 详细的职位信息

### 4. 存储（Storage）

**`storage/job_storage.py`** 管理历史职位：

- ✅ 去重机制（避免重复通知）
- ✅ JSON持久化存储
- ✅ 持续累积已发送URL

---

## 🚀 快速开始（3步）

### 第1步：初始化

```bash
cd /Users/xxm/projects/aaip-job-search
bash scripts/init.sh
```

### 第2步：配置Gmail

编辑 `config/production.yaml`：

```yaml
email:
  sender_email: your_email@gmail.com
  sender_password: your_app_password  # ← 替换为Gmail App Password
  recipient_email: derrick.xu84@gmail.com
```

### 第3步：测试运行

```bash
bash scripts/run_test.sh
```

### 第4步：部署定时任务

```bash
bash scripts/deploy_crontab.sh
```

---

## 📋 配置说明

### config/production.yaml

| 配置项 | 说明 | 默认值 |
|--------|------|---------|
| `email.smtp_server` | SMTP服务器 | smtp.gmail.com |
| `email.smtp_port` | SMTP端口 | 587 |
| `schedule.hours` | 运行小时（每日）| [8, 12, 18] |
| `tech_keywords` | 技术栈关键词 | [Java, Python, ...] |
| `level_keywords` | 岗位级别关键词 | [Senior, Staff, ...] |
| `location_filter` | 接受地点 | [Calgary, Alberta, ...] |
| `exclude_keywords` | 排除关键词 | [contract, hourly, ...] |
| `request.timeout` | HTTP超时（秒）| 10 |
| `request.user_agent` | 浏览器UA | Mozilla/5.0... |

### config/companies.json

当前支持 **6家P0公司**：

| 公司ID | 名称 | 平台 | 状态 |
|--------|------|--------|------|
| benevity | Benevity | Greenhouse | ✅ |
| neofinancial | Neo Financial | Ashby | ⏸ pending |
| helcim | Helcim | Custom | ⏸ pending |
| symend | Symend | Unknown | ⏸ pending |
| attabotics | Attabotics | Unknown | ⏸ pending |
| jobber | Jobber | Custom | ⏸ pending |

---

## 📊 运行流程

```
定时任务触发（8:00 / 12:00 / 18:00）
    ↓
加载配置（config/production.yaml）
    ↓
加载公司列表（config/companies.json）
    ↓
遍历公司
    ↓
    ├─→ Benevity: GreenhouseScraper.fetch_jobs()
    ├─→ Neo Financial: AshbyScraper.fetch_jobs() [pending]
    └─→ 其他: CustomScraper.fetch_jobs() [pending]
    ↓
获取职位列表
    ↓
应用过滤规则
    ├─→ 技术栈匹配？
    ├─→ 级别匹配？
    ├─→ 地点匹配？
    └─→ 排除词检查？
    ↓
去重检查（storage/jobs.json）
    ↓
有新职位？
    ├─→ 是：发送邮件 → 标记已发送
    └─→ 否：记录日志
    ↓
写入日志（logs/scraper.log）
    ↓
结束
```

---

## 🛠️ 脚本说明

### scripts/init.sh
**初始化环境**

- 创建Python虚拟环境（.venv）
- 安装依赖（pip install -r requirements.txt）
- 创建必要目录（logs/, storage/）
- 提示配置Gmail

### scripts/run_test.sh
**手动运行测试**

- 激活虚拟环境
- 执行 `python main.py`
- 输出结果到控制台

### scripts/test_scraper.py
**测试单个抓取器**

- 只测试Benevity抓取
- 显示前10个职位
- 用于调试

### scripts/deploy_crontab.sh
**部署定时任务**

- 检查现有crontab
- 生成新定时任务
- 自动写入crontab

### scripts/view_logs.sh
**查看实时日志**

- 使用 `tail -f` 监控日志
- 按 Ctrl+C 退出

### scripts/clean_history.sh
**清理历史记录**

- 清空 storage/jobs.json
- 重新开始去重追踪

---

## 📝 日志示例

**成功运行**：
```
2026-01-20 08:00:01 - INFO - ============================================================
2026-01-20 08:00:01 - INFO - Starting AAIP Job Aggregator
2026-01-20 08:00:01 - INFO - Loaded config from config/production.yaml
2026-01-20 08:00:01 - INFO - Loaded 6 companies
2026-01-20 08:00:02 - INFO - Loaded 0 historical job URLs
2026-01-20 08:00:02 - INFO - Skipping Neo Financial (status: pending)
2026-01-20 08:00:02 - INFO - Skipping Helcim (status: pending)
2026-01-20 08:00:02 - INFO - Fetching jobs from Benevity (Greenhouse)
2026-01-20 08:00:03 - INFO - Found 27 jobs from Benevity
2026-01-20 08:00:04 - INFO - ✓ Matched: Senior Staff Developer @ Benevity
2026-01-20 08:00:04 - INFO - ✓ Matched: Director, Software Development @ Benevity
2026-01-20 08:00:04 - INFO - ✗ Filtered: Product Manager @ Benevity
2026-01-20 08:00:05 - INFO - Found 2 new matching jobs
2026-01-20 08:00:05 - INFO - ✅ Email sent successfully to derrick.xu84@gmail.com
2026-01-20 08:00:06 - INFO - Saved 2 job URLs to storage
2026-01-20 08:00:06 - INFO - ============================================================
```

**无新职位**：
```
2026-01-20 12:00:01 - INFO - ============================================================
2026-01-20 12:00:01 - INFO - Starting AAIP Job Aggregator
2026-01-20 12:00:02 - INFO - Loaded 156 historical job URLs
2026-01-20 12:00:03 - INFO - Found 27 jobs from Benevity
2026-01-20 12:00:04 - INFO - All jobs already sent
2026-01-20 12:00:04 - INFO - No new matching jobs found
2026-01-20 12:00:05 - INFO - ============================================================
```

---

## 🎯 邮件示例

**主题**：`🎯 发现 3 个匹配的新职位！`

**正文**（HTML格式）：

```
以下是今天匹配的职位：

📌 Senior Staff Developer
   公司: Benevity
   地点: Toronto, Ontario, Canada
   平台: Greenhouse
   [查看职位]

📌 Director, Software Development
   公司: Benevity
   地点: Toronto, Ontario, Canada
   平台: Greenhouse
   [查看职位]

📌 Senior ML Operations
   公司: Benevity
   地点: Toronto, Ontario, Canada
   平台: Greenhouse
   [查看职位]

---
此邮件由 AAIP Job Aggregator 自动发送
```

---

## 🐛 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| Gmail认证失败 | App Password错误 | 重新生成App Password |
| 403抓取错误 | User-Agent被封 | 修改config中的user_agent |
| 没有收到邮件 | 被垃圾邮件拦截 | 检查垃圾箱 |
| crontab不执行 | python路径错误 | 使用 `which python3` 检查路径 |
| 找不到模块 | 虚拟环境未激活 | 先执行 `source .venv/bin/activate` |

---

## 📈 后续计划

### Phase 2：扩容（预计5-7天）

- [ ] 实现 Ashby 平台抓取器（Neo Financial）
- [ ] 实现自定义网站抓取器（Helcim、Jobber）
- [ ] 优化 HTML 解析逻辑（根据实际页面调整）
- [ ] 添加错误重试机制

### Phase 3：增强（预计7-10天）

- [ ] Web Dashboard（Flask/FastAPI）
- [ ] Telegram/Slack 通知支持
- [ ] 历史职位查询界面
- [ ] 投递记录追踪

---

## 📞 支持

**文档**：
- `README.md` - 项目概述
- `QUICKSTART.md` - 快速开始指南
- `CHANGELOG.md` - 更新日志

**日志文件**：
- `logs/scraper.log` - 完整运行日志

**代码位置**：
- `/Users/xxm/projects/aaip-job-search`

---

**最后更新**: 2026-01-20
**版本**: v0.1.0
