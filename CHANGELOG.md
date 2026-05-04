# 更新日志

## [2026-01-20 v0.2.0] - Neo Financial支持（Ashby平台）

### 新增功能
- ✅ Ashby平台抓取器（使用Playwright渲染JavaScript）
- ✅ Neo Financial公司职位抓取
- ✅ Playwright浏览器安装脚本
- ✅ 自动地点识别（Alberta/Calgary/Toronto/Vancouver/Remote）

### 新增依赖
- `playwright>=1.40.0` - JavaScript渲染引擎

### 使用方法

#### 1. 安装Playwright
```bash
bash scripts/install_playwright.sh
```

#### 2. 测试Neo Financial抓取
```bash
python scrapers/ashby.py
```

#### 3. 运行主程序（包含Neo Financial）
```bash
python main.py
```

### 技术实现
- Playwright启动无头Chromium浏览器
- 等待React页面完全加载（5秒）
- BeautifulSoup解析HTML
- 自动识别地点（基于关键词匹配）

### 配置变更
- Neo Financial状态从`pending`改为active

### 已知限制
- ⚠️  Ashby页面结构可能需要后续调整
- ⚠️  Playwright首次运行需要下载浏览器（~200MB）
- ⚠️  抓取速度较慢（~10-20秒每家公司）

### 待办事项
- [ ] 用户安装Playwright并测试
- [ ] 根据实际Ashby页面结构调整解析逻辑
- [ ] 添加Helcim、Jobber等公司
- [ ] 优化抓取速度

---

## [2026-01-20 v0.1.3] - HTML解析修复（关键）

### Bug修复
- ✅ 修复Greenhouse抓取器：正确提取职位名称和地点
  - 修复"New"标签混在职位名称中的问题
  - 正确提取地点信息（从`<p class="body body__secondary body__metadata">`）
  - 添加正则表达式清理职位名称末尾的标签文本
- ✅ 优化职位提取：使用`get_text(separator=' ')`保留分隔符
- ✅ 添加部门提取：从`<h3 class="section-header">`获取部门信息

### 问题修复对比

**之前**：
```
职位: Product Manager, Benevity API EcosystemNew  ← "New"混在里面
地点: Unknown  ← 没有提取到
```

**现在**：
```
职位: Product Manager, Benevity API Ecosystem  ← 干净的名称
地点: Calgary, Alberta, Canada  ← 正确的地点
部门: Product  ← 正确的部门
```

### 临时解决方案
- ✅ 添加清理脚本：`scripts/clean_and_reset.sh`

### 待办事项
- [ ] 用户测试：`bash scripts/clean_and_reset.sh && python main.py`
- [ ] 验证职位名称和地点正确
- [ ] 评估重复职位问题（同一职位不同城市）
- [ ] 优化过滤规则

---

## [2026-01-20 v0.1.2] - 过滤器修复

### Bug修复
- ✅ 修复HTML实体解码问题（`&amp;` → `&`）
- ✅ 添加调试输出：显示每个过滤步骤的匹配结果
- ✅ 优化过滤逻辑：先解码HTML实体再匹配

### 问题分析
- ❌ 所有职位都被过滤：HTML实体编码导致关键词匹配失败
  - `Product Owner, Data Platform &amp; Analytics` → `amp; analytics` 不匹配 `analytics`

### 待办事项
- [ ] 用户重新测试：`python main.py 2>&1 | tee /tmp/test_output.log`
- [ ] 根据调试输出调整过滤规则
- [ ] 添加Neo Financial（需要Playwright）
- [ ] 添加Helcim、Jobber等公司

---

## [2026-01-20 v0.1.1] - HTML解析修复

### Bug修复
- ✅ 修复Greenhouse抓取器：根据实际HTML结构调整CSS选择器
  - 原：`div.opening` / `div.job`（不存在）
  - 新：`tr.job-post`（正确）
- ✅ 修复职位提取：使用 `a` 标签 + `p` 标签结构
- ✅ 修复地点提取：第二个 `p` 标签，class包含 `metadata`
- ✅ 添加测试函数：`test_greenhouse_scraper()`

### 配置变更
- ❌ 移除：Gmail邮件配置
- ✅ 新增：本地MD存储（`/Users/xxm/projects/QuantEngine_markdown_file/` 目录）
- ✅ 优化：扩展地点过滤（包含Toronto、Vancouver）
- ✅ 优化：扩展技术栈关键词（包含ML、DevOps、Manager、Product Owner）

### 待办事项
- [ ] 用户测试：运行 `bash scripts/run_test.sh`
- [ ] 根据实际输出优化过滤规则
- [ ] 添加Neo Financial（需要Playwright）
- [ ] 添加Helcim、Jobber等公司

---

## [2026-01-20 v0.1.0] - 第一版本

### 新增功能
- ✅ Greenhouse平台抓取器
- ✅ Benevity公司职位抓取
- ✅ 技术栈过滤
- ✅ 岗位级别过滤
- ✅ 地点过滤
- ✅ 去重机制
- ✅ 本地MD文件存储
- ✅ Crontab定时任务
- ✅ 日志系统

### 已知限制
- ⚠️  Greenhouse抓取器需要根据实际HTML结构调整

### 待办事项
- [ ] 测试实际Benevity页面HTML结构
- [ ] 根据实际情况调整解析逻辑
- [ ] 添加Neo Financial（需要Playwright）
- [ ] 添加Helcim、Jobber等公司
