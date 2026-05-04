# AAIP Job Aggregator - TODO List

> 最后更新: 2026-01-24

---

## 🔥 高优先级

### P1/P2 待开发爬虫

| 公司 | 平台 | 优先级 | 状态 | 备注 |
|------|------|--------|------|------|
| IBM Canada | custom (Lever嵌入) | P1 | 待开发 | Platform / AI，需确认 hiring entity |
| Cisco Canada | custom (Lever嵌入) | P1 | 待开发 | Platform / Networking |
| Morgan Stanley | custom (Lever嵌入) | P1 | 待开发 | FinTech，完美匹配支付/金融经验 |
| Amazon Canada | custom | P2 | 待开发 | FAANG，使用Amazon自建招聘系统 |
| Ubisoft Montreal | custom (Algolia) | P2 | 待开发 | 游戏巨头，需开发Algolia API爬虫 |
| Lightspeed Commerce | custom | P2 | 待开发 | POS/电商SaaS |

### P3 企业级招聘系统爬虫

| 公司 | 平台 | 优先级 | 状态 | 备注 |
|------|------|--------|------|------|
| RBC | Phenom People | P3 | 待开发 | 加拿大最大银行，职位量大 |
| TD Bank | Workday | P3 | 待开发 | 五大银行，稳定工签友好 |
| Scotiabank | SAP SuccessFactors | P3 | 待开发 | 国际化银行，技术部门庞大 |

### 系统优化

- [ ] 优化Shopify爬虫：目前从slug提取标题不准确，考虑访问单个职位页面获取完整信息
- [ ] 测试定时任务稳定性（运行1周观察）
- [ ] 添加错误通知机制（爬虫失败时发送通知）

---

## 🟡 中优先级

### 爬虫优化

- [x] ~~Lever 平台爬虫~~ (已完成 - Attabotics, Wealthsimple)
- [x] ~~JazzHR 平台爬虫~~ (已完成 - Symend)
- [x] ~~BambooHR 平台爬虫~~ (已完成 - Helcim)
- [x] ~~Jobber 自定义爬虫~~ (已完成)
- [x] ~~Jobvite 平台爬虫~~ (已完成 - Enverus)
- [x] ~~Shopify 自定义爬虫~~ (已完成 - 使用Playwright)
- [ ] 优化抓取速度（当前 ~5-30秒/公司）
- [ ] 添加请求重试机制（带指数退避）
- [ ] 添加请求限流（防止 IP 被封）
- [ ] 添加User-Agent轮换

### 过滤规则优化

- [ ] 评估重复职位问题（同一职位在不同城市发布）
- [ ] 根据实际输出微调过滤规则
- [ ] 考虑添加 JD 内容匹配（不仅仅是标题）
- [ ] 添加薪资范围过滤（如果职位页面提供）

### 存储优化

- [ ] 实现 `cleanup_old_urls()` 方法（防止 jobs.json 无限增长）
- [ ] 添加日志轮转（防止 scraper.log 过大）
- [ ] 添加职位去重更智能的算法（相似标题+公司）

---

## 🟢 低优先级

### 功能扩展

- [ ] 邮件通知功能（notification/email.py 已有 stub）
- [ ] Web Dashboard 可视化
- [ ] Slack/Discord 通知集成
- [ ] 职位详情页抓取（薪资、技术栈、JD全文等）
- [ ] 添加职位推荐评分系统（基于匹配度打分）

### 代码质量

- [ ] 添加单元测试
- [ ] 添加 CI/CD（GitHub Actions）
- [ ] 添加类型检查（mypy）
- [ ] 添加代码格式化（black/isort）
- [ ] 添加性能监控（抓取耗时统计）

### 平台支持

- [ ] LinkedIn Jobs API 集成
- [ ] Indeed API 集成
- [ ] Glassdoor 集成

### 其他改进

- [ ] 添加公司评分系统（Glassdoor评分、工签友好度等）
- [ ] 支持多个用户配置文件（不同技能栈）
- [ ] 生成每周/月职位趋势报告

---

## ✅ 已完成

### v3.1 - 全加拿大扩展 (2026-01-24)
- [x] Shopify 自定义爬虫（Playwright动态渲染）
- [x] 扩展地点过滤到全加拿大（ON, BC, QC）
- [x] 添加 P2 公司类别（全加拿大工签友好）
- [x] 添加 P3 公司类别（大银行等企业）
- [x] 修复 Hootsuite Greenhouse URL
- [x] 支持 P0/P1/P2/P3 四层公司分类
- [x] Wealthsimple (Lever) - 8个匹配职位
- [x] Hootsuite (Greenhouse) - 1个匹配职位

### v3.0 - P0/P1 公司完成 (2026-01-21)
- [x] Lever 平台抓取器（Attabotics）
- [x] JazzHR 平台抓取器（Symend）
- [x] BambooHR 平台抓取器（Helcim，需要Playwright）
- [x] Jobber 自定义抓取器
- [x] Jobvite 平台抓取器（Enverus）
- [x] 完成 P0 六家公司配置
- [x] 添加 P1 公司分类
- [x] 部署 crontab 定时任务（每天 8:00, 12:00, 18:00）

### v0.2.1 - 代码修复
- [x] 删除 greenhouse.py 死代码
- [x] 修复 job_filter.py 变量引用错误
- [x] 修复 local_storage.py 正则替换
- [x] 清理 tech_keywords 配置
- [x] 统一使用 logger 替换 print
- [x] 补充 companies.json status 字段
- [x] main.py 添加配置默认值

### v0.2.0 - Neo Financial
- [x] Ashby 平台抓取器
- [x] Neo Financial 公司配置
- [x] 自动地点识别

### v0.1.x - 基础功能
- [x] Greenhouse 平台抓取器
- [x] Benevity 公司抓取
- [x] 技术栈/级别/地点过滤
- [x] 去重机制
- [x] 本地 MD 文件存储
- [x] Crontab 定时任务
- [x] 日志系统

---

## 📊 当前系统状态

### 激活公司统计
- **总计**: 23家公司 (14家已激活, 9家待开发)
- **P0 (AB省核心)**: 6/6 激活 ✅
- **P1 (大公司AB省)**: 1/4 激活
- **P2 (全加拿大工签友好)**: 4/6 激活
- **P3 (加拿大五大银行)**: 0/3 激活

### 最新测试结果 (2026-01-24)
- **匹配职位数**: 28个
- **来源分布**:
  - Benevity: 7个
  - Neo Financial: 8个
  - Helcim: 4个
  - Wealthsimple: 8个
  - Hootsuite: 1个

### 平台支持情况
- ✅ Greenhouse (Benevity, Hootsuite)
- ✅ Ashby (Neo Financial)
- ✅ Lever (Attabotics, Wealthsimple)
- ✅ JazzHR (Symend)
- ✅ BambooHR (Helcim)
- ✅ Jobber Custom (Jobber)
- ✅ Jobvite (Enverus)
- ✅ Shopify Custom (Shopify)
- ⏸️ Phenom People (RBC - 待开发)
- ⏸️ Workday (TD Bank - 待开发)
- ⏸️ SAP SuccessFactors (Scotiabank - 待开发)
- ⏸️ Amazon Custom (Amazon - 待开发)
- ⏸️ Algolia API (Ubisoft - 待开发)

---

## 📋 开发指南

### 添加新公司

1. 在 `config/companies.json` 添加公司配置
2. 如果是新平台，在 `scrapers/` 创建新爬虫
3. 在 `main.py` 添加平台判断逻辑和import
4. 测试：`python main.py`

### 开发新平台爬虫

```bash
# 1. 创建爬虫文件
cp scrapers/base.py scrapers/new_platform.py

# 2. 实现 fetch_jobs() 方法

# 3. 添加测试函数
python scrapers/new_platform.py

# 4. 集成到main.py
```

### 测试单个爬虫

```bash
# Greenhouse (Benevity, Hootsuite)
python scrapers/greenhouse.py

# Ashby (Neo Financial)
python scrapers/ashby.py

# Lever (Wealthsimple)
python scrapers/lever.py

# Shopify
python scrapers/shopify.py
```

### 清理历史数据

```bash
bash scripts/clean_history.sh
```

### 查看运行日志

```bash
bash scripts/view_logs.sh
```

### 手动运行测试

```bash
# 直接运行（不检查时间）
python main.py

# 带时间检查运行
python main.py --check
```

---

## 🎯 近期目标

1. **观察当前系统稳定性**（1-2周）
   - 监控定时任务执行情况
   - 收集匹配职位质量反馈
   - 观察是否有误报/漏报

2. **根据效果决定下一步**
   - 如果职位数量不够 → 开发 P2 公司爬虫 (Amazon/Ubisoft/Lightspeed)
   - 如果想扩大覆盖面 → 开发 P3 银行爬虫 (RBC/TD/Scotiabank)
   - 如果想提高质量 → 优化过滤规则，添加JD内容分析

3. **系统优化**
   - 优化Shopify爬虫准确性
   - 添加日志轮转
   - 实现旧数据清理机制
