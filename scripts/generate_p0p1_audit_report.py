#!/usr/bin/env python3
"""生成当前找工作方案 P0/P1 审查报告。"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List


OUTPUT_DIR = Path("/Users/xxm/projects/QuantEngine_markdown_file/12-找工作")
OUTPUT_FILE = OUTPUT_DIR / "2026-05-04_方案P0_P1审查_5轮100条.md"


Find = Dict[str, str]


def finding(round_name: str, severity: str, title: str, evidence: str, impact: str, fix: str) -> Find:
    """构造单条问题。"""
    return {
        "round": round_name,
        "severity": severity,
        "title": title,
        "evidence": evidence,
        "impact": impact,
        "fix": fix,
    }


def build_findings() -> List[Find]:
    """返回5轮、共100条P0/P1问题。"""
    findings: List[Find] = []

    findings.extend([
        finding("第1轮 策略/资格", "P0", "护理当前策略和真实英语能力断层", "用户确认目前英语完全不能沟通。", "AHS/Covenant/HCA等岗位即使不要求RN，也可能因为安全沟通无法通过面试或上岗。", "把护理主线改成先低语言环境支持岗位+每日英语训练，HCA作为过渡目标。"),
        finding("第1轮 策略/资格", "P0", "实际可投入口岗位覆盖为0", "护理排序报告A类低语言门槛岗位数量为0。", "最现实入口没有数据来源，报告会把精力推向不可行岗位。", "新增私营home care、华人社区、养老陪护、家庭支持、Kijiji/社区渠道。"),
        finding("第1轮 策略/资格", "P0", "没有开放工签健康服务限制检查", "系统未记录工签是否允许health care/child care等场景。", "即使有开放工签，也可能因为体检或限制条款不能合法从事部分照护岗位。", "在候选人档案加入work permit restrictions字段和投递前检查。"),
        finding("第1轮 策略/资格", "P0", "美国加州RN路径被误当成阿省RN风险", "用户确认现在考的是美国加州方向。", "NCLEX或加州路径不能自动等同于阿省RN许可，错误投RN会浪费时间。", "把CRNA阿省RN流程拆成独立清单：学历评估、语言、NCLEX适用性、注册类别。"),
        finding("第1轮 策略/资格", "P0", "未建立不能使用RN头衔的防护", "妻子未取得阿省RN许可。", "简历/自我介绍若误用RN可能触发合规风险。", "生成护理简历时强制使用海外护士经验/护理背景，不写Alberta RN。"),
        finding("第1轮 策略/资格", "P0", "没有按当下可上岗性筛掉受监管职位", "报告仍保留大量RN/LPN/GN/Assistant Head Nurse类岗位。", "会让行动清单看起来很多，实际可投很少。", "每个职位增加can_apply_now布尔字段和原因。"),
        finding("第1轮 策略/资格", "P0", "缺少英语路径的硬指标", "策略文档没有把英语从建议变成每日/每周任务。", "当前最大瓶颈无法被系统推进。", "加入CLB/IELTS/CELPIP目标、口语场景训练和周复盘。"),
        finding("第1轮 策略/资格", "P0", "AAIP/PR路径没有和职位类型绑定", "报告只按职位可行性排序，没有标注是否支持阿省路径。", "可能找到短工但不能帮助长期身份目标。", "每个岗位增加AAIP/PR relevance字段。"),
        finding("第1轮 策略/资格", "P1", "缺少CPR/急救/无犯罪/疫苗清单", "护理策略未列入这些常见入职前置材料。", "即使拿到面试也可能卡在入职前条件。", "建立pre-employment checklist并标注已完成/缺失。"),
        finding("第1轮 策略/资格", "P1", "没有区分家庭照护和机构照护", "当前护理机会主要来自AHS/Covenant/Job Bank。", "低英语阶段更可能从家庭/社区支持进入，数据结构没有体现。", "增加care setting分类：private home、agency、facility、hospital。"),
        finding("第1轮 策略/资格", "P1", "没有地域搬迁成本字段", "排序只看岗位，不看城市和通勤。", "偏远城市岗位可能理论可行但家庭成本过高。", "加入city_priority、relocation_cost、commute字段。"),
        finding("第1轮 策略/资格", "P1", "没有雇主沟通语言字段", "当前系统不知道岗位是否可能中文/双语环境。", "英语不能沟通阶段会错过真正可行的华人雇主。", "按招聘文本和雇主类型标注language_fit。"),
        finding("第1轮 策略/资格", "P1", "没有护理面试话术准备", "文档给策略但没有生成低英语面试脚本。", "机会来了也难以转化。", "生成固定英文短句、电话接听模板、雇主短信模板。"),
        finding("第1轮 策略/资格", "P1", "没有加拿大本地推荐人策略", "系统未追踪reference来源。", "照护岗位常看重可信任和本地推荐。", "添加社区志愿、培训机构、家庭雇主推荐路径。"),
        finding("第1轮 策略/资格", "P1", "没有收入紧急程度排序", "IT、护理、私活三条线没有按现金流优先级统一排序。", "容易把时间花在长期路径而不是近期养家。", "建立家庭机会看板：本周现金流、1个月、3个月、移民价值。"),
        finding("第1轮 策略/资格", "P1", "没有投递禁区说明", "报告未明确哪些岗位现在不应投。", "会浪费简历和心理成本。", "把RN/LPN/GN/Head Nurse设为许可后再投。"),
        finding("第1轮 策略/资格", "P1", "没有个人档案结构化", "妻子许可、英语、工签、证书信息散落在聊天和文档。", "后续过滤器无法自动判断。", "新增candidate_profile_nursing.yaml。"),
        finding("第1轮 策略/资格", "P1", "没有把美国RN进度纳入时间线", "加州考试信息未进入系统计划。", "中长期护理路径无法预测。", "建立US RN与Alberta RN并行里程碑。"),
        finding("第1轮 策略/资格", "P1", "没有风险口径", "文档没有提醒雇主沟通中如何描述海外护士身份。", "可能被误解为本地持证护士。", "生成合规自我介绍：international nursing background, not registered in Alberta yet。"),
        finding("第1轮 策略/资格", "P1", "没有失败反馈机制", "投递后没有原因分类。", "无法知道卡在英语、许可、简历还是岗位不匹配。", "加入rejection_reason和next_action字段。"),
    ])

    findings.extend([
        finding("第2轮 护理数据/排序", "P0", "护理报告A类为0仍输出为策略入口", "排序报告显示A类低语言门槛支持岗位（0）。", "最需要的职位没有一个，说明抓取目标错位。", "先补数据源再谈排序。"),
        finding("第2轮 护理数据/排序", "P0", "HCA被过度乐观归为过渡目标", "B类33个主要仍是正规机构岗位。", "英语完全不能沟通时，HCA面试和上岗仍是高风险。", "B类再细分：可立即尝试/需基础英语/需证书。"),
        finding("第2轮 护理数据/排序", "P0", "RN/LPN/GN占比过高", "C类许可后再投67个，占105个去重岗位的大多数。", "机会数量看起来多，但当前不可投占主体。", "默认隐藏C类，只在长期路径单独展示。"),
        finding("第2轮 护理数据/排序", "P0", "来源过窄", "护理活跃来源只有AHS、Covenant、Job Bank。", "医院和公共系统不适合当前低英语入口。", "加入home care agencies、retirement homes、community boards。"),
        finding("第2轮 护理数据/排序", "P0", "重复职位先进入正式报告", "AHS/Covenant镜像职位后来才在排序报告去重。", "正式报告和存储会高估机会并污染历史记录。", "抓取后先规范化job id再写报告和存储。"),
        finding("第2轮 护理数据/排序", "P0", "Assistant Head Nurse曾进入可见机会池", "后续脚本才把head nurse归到许可后再投。", "管理岗比RN许可要求更高，误投成本更大。", "受监管/管理岗硬排除出当前行动清单。"),
        finding("第2轮 护理数据/排序", "P0", "Unit Clerk等沟通岗未硬降级", "D类才5个，说明非护理但高沟通岗位识别弱。", "英语不能沟通时这类岗位不可作为入口。", "添加communication_heavy规则。"),
        finding("第2轮 护理数据/排序", "P0", "没有证书要求抽取", "报告没有抽取HCA directory、CPR、证书要求。", "岗位是否能投无法判断。", "解析职位详情中的requirements并结构化。"),
        finding("第2轮 护理数据/排序", "P1", "Job Bank质量未分层", "Job Bank职位混杂，且company/location可能Unknown。", "会把低质量或不清晰职位混入行动清单。", "按雇主可信度和要求完整度评分。"),
        finding("第2轮 护理数据/排序", "P1", "没有联系电话/线下投递字段", "低语言阶段可能更适合熟人/线下渠道。", "只靠网页投递转化率低。", "为护理入口岗位加入phone/email/in-person字段。"),
        finding("第2轮 护理数据/排序", "P1", "没有班次筛选", "护理/照护岗位常有night/evening/weekend。", "家庭安排和通勤风险不可见。", "抽取shift字段并加入排序。"),
        finding("第2轮 护理数据/排序", "P1", "没有体力要求标签", "照护岗位对搬扶、站立、驾驶有要求。", "不适合岗位会浪费投递。", "抽取lifting、driver license、vehicle字段。"),
        finding("第2轮 护理数据/排序", "P1", "没有语言关键词库", "未匹配Mandarin/Cantonese/Chinese bilingual。", "华人照护机会无法被优先抓出。", "新增中文/双语语言关键词和加权。"),
        finding("第2轮 护理数据/排序", "P1", "没有雇主类型黑名单", "可疑中介或不清晰家庭雇主未识别。", "存在付款和合规风险。", "加入employer_risk_score。"),
        finding("第2轮 护理数据/排序", "P1", "没有按投递材料准备度排序", "所有岗位只按可行性大类列出。", "用户不知道今天能投哪几个。", "增加ready_to_apply_today字段。"),
        finding("第2轮 护理数据/排序", "P1", "没有护理简历版本绑定", "报告未说明每类岗位用哪版简历。", "用RN经验简历投低门槛岗位可能过强或不合规。", "生成caregiver/HCA/long-term RN三版简历映射。"),
        finding("第2轮 护理数据/排序", "P1", "没有投递批次建议", "重复公司不同地点是否都投没有系统策略。", "可能被同一ATS视为乱投。", "同公司多地点设定主投1-2个、备选若干。"),
        finding("第2轮 护理数据/排序", "P1", "没有雇主ATS去重", "同一公司不同URL可能同一job id。", "投递记录会重复或误判机会数量。", "用company+external job id做主键。"),
        finding("第2轮 护理数据/排序", "P1", "没有岗位标题规范化", "assistant/head/unit/attendant混合依赖字符串判断。", "新增标题变化会漏判。", "建立nursing_role_taxonomy。"),
        finding("第2轮 护理数据/排序", "P1", "没有人工复核队列", "低置信度分类没有集中展示。", "错分岗位难以及时纠正。", "输出needs_review护理职位列表。"),
    ])

    findings.extend([
        finding("第3轮 IT/私活", "P0", "IT报告混入销售/客户成功类岗位", "IT报告edge-title-keyword-hits为17。", "数量被放大，用户会把时间花在低匹配岗位。", "把TAM、pre-sales、go-to-market、solutions engineer单独降级。"),
        finding("第3轮 IT/私活", "P0", "IT职位没有P0/P1可投排序", "正式报告37条但没有今日优先投递清单。", "技术岗位搜索结果不能直接转成行动。", "按技术匹配、身份友好、远程/加拿大、seniority生成Top 10。"),
        finding("第3轮 IT/私活", "P0", "大量高价值公司仍pending", "IBM、Cisco、Amazon、RBC、TD等在pending或custom未实现。", "IT机会池不足，之前4条数据问题会复发。", "优先补HTTP/API可抓来源，pending不计入覆盖。"),
        finding("第3轮 IT/私活", "P0", "custom scraper未实现", "scrapers/custom.py直接提示not implemented。", "配置里的高价值自定义来源实际抓不到。", "按公司拆专用scraper或禁用并标明原因。"),
        finding("第3轮 IT/私活", "P0", "私活报告不是私活机会", "远程项目报告79条，80处待确认，136处未披露。", "大量全职远程岗位被当成私活，不能直接养家。", "分离freelance contract和remote full-time。"),
        finding("第3轮 IT/私活", "P0", "私活预算不可用", "未披露出现136次。", "无法判断现金流和投入产出。", "预算未知默认进入人工确认，不进Top proposal。"),
        finding("第3轮 IT/私活", "P0", "私活草稿仍有中文残留", "报告中核心技能出现89次。", "英文proposal不专业，直接复制会损害转化。", "重新生成报告并加英文-only校验。"),
        finding("第3轮 IT/私活", "P0", "Codex切换不彻底", "freelance.yaml仍保留claude模型和ANTHROPIC_API_KEY。", "未来运行者会误以为还依赖Claude。", "删除或改名为local/codex字段。"),
        finding("第3轮 IT/私活", "P1", "IT关键词Technical/Solutions过宽", "production.yaml包含Technical、Solutions。", "容易匹配售前、支持、解决方案岗位。", "把这些关键词改为弱信号，必须配合工程关键词。"),
        finding("第3轮 IT/私活", "P1", "Manager既是level又会误杀方向", "level_keywords包含Manager。", "技术管理可行，但客户/销售管理不一定。", "Manager需与Engineering/Software/Platform同现。"),
        finding("第3轮 IT/私活", "P1", "Unknown地点被允许", "location_filter包含Unknown。", "可能混入不支持加拿大/远程的岗位。", "Unknown默认降级，详情确认后再进入主清单。"),
        finding("第3轮 IT/私活", "P1", "IT没有签证/加拿大雇佣友好评分", "报告只显示匹配职位。", "开放/封闭工签转换和PR目标没有被职位排序利用。", "增加immigration_fit_score。"),
        finding("第3轮 IT/私活", "P1", "IT没有技能缺口解释", "报告不说明为什么匹配。", "难以针对性改简历。", "输出matched_keywords和missing_keywords。"),
        finding("第3轮 IT/私活", "P1", "IT没有简历版本映射", "Java/AI/DevOps/Manager岗位混在一起。", "同一简历投不同方向命中率低。", "按岗位簇绑定resume_variant。"),
        finding("第3轮 IT/私活", "P1", "私活合规默认过宽", "ScoredProject company_signable默认True。", "NDA/竞业/付款风险容易漏掉。", "默认Unknown，只有通过过滤后才True。"),
        finding("第3轮 IT/私活", "P1", "私活平台覆盖不够", "freelancer、contra disabled。", "真正短单来源不足。", "先补Upwork/RFP/Contra/Freelancer或手动导入。"),
        finding("第3轮 IT/私活", "P1", "私活没有交付周期评分", "报告不区分1周小单和长期全职。", "不利于近期现金流。", "加入duration_fit和first_cash_date。"),
        finding("第3轮 IT/私活", "P1", "私活没有客户可信度评分", "报告缺少付款验证/历史评价。", "可能浪费时间或遇到付款风险。", "加入client_risk_score。"),
        finding("第3轮 IT/私活", "P1", "私活proposal没有个性化证据", "模板主要依靠关键词。", "转化率会低。", "从项目描述抽痛点和交付物。"),
        finding("第3轮 IT/私活", "P1", "IT与私活没有统一时间预算", "两条线独立输出。", "16年IT经验应优先高概率路径，但系统没安排。", "建立每日2小时私活、2小时IT投递等节奏。"),
    ])

    findings.extend([
        finding("第4轮 数据/存储/报告", "P0", "sent_urls语义仍污染核心存储", "storage/jobs.json、nursing_jobs.json、freelance_projects.json均使用sent_urls。", "用户从未投递却被系统当作已发送/已处理。", "迁移为seen_urls/recorded_urls，并保留投递表applications。"),
        finding("第4轮 数据/存储/报告", "P0", "一次生成报告会阻止再次干净生成", "私活二次运行因storage已记录导致0新项目。", "修复报告文字后无法自然重出同日报告。", "增加--report-only、--force-regenerate、--no-mark-recorded。"),
        finding("第4轮 数据/存储/报告", "P0", "正式报告和历史记录耦合", "main.py生成报告后立即mark_sent。", "看过不等于已投，且报告质量差时也污染历史。", "将scraped、reviewed、applied三种状态分离。"),
        finding("第4轮 数据/存储/报告", "P0", "Playwright仍可能触发Chrome崩溃", "已出现Chrome for Testing crash dialog。", "自动化运行会打断用户电脑，影响信任。", "默认禁用已做，但还需隔离浏览器profile和无头健康检查。"),
        finding("第4轮 数据/存储/报告", "P0", "源码配置仍残留Claude依赖", "production.yaml translation和freelance.yaml model/api_key_env仍指向Claude/ANTHROPIC。", "与以后只用Codex的方向冲突。", "清理Claude字段或明确legacy unused。"),
        finding("第4轮 数据/存储/报告", "P0", "报告没有数据源健康页", "失败的pending/custom/Playwright源不在主报告显著展示。", "用户只看到数量少，不知道哪里坏。", "每日输出source health dashboard。"),
        finding("第4轮 数据/存储/报告", "P0", "未实现的scraper仍在战略配置中", "custom scraper not implemented yet。", "配置看似覆盖，实际没有数据。", "未实现平台不得进入active策略覆盖。"),
        finding("第4轮 数据/存储/报告", "P0", "同一天报告可能追加旧内容", "local_storage/report生成逻辑按日期文件写入。", "修复后报告版本可能混杂。", "报告文件用run_id或覆盖策略，保留archive。"),
        finding("第4轮 数据/存储/报告", "P1", "metadata与实际公司数量不一致", "companies metadata total 30，但实际p0+p1+p2+p3为32。", "覆盖率判断不可信。", "加载时校验metadata并自动生成。"),
        finding("第4轮 数据/存储/报告", "P1", "nursing metadata无数量字段", "nursing_companies只有target描述。", "无法快速判断来源覆盖变化。", "补active/pending/count元数据。"),
        finding("第4轮 数据/存储/报告", "P1", "没有结构化run summary", "诊断结果在logs和md报告之间分散。", "长期趋势不可比较。", "保存每次run JSON summary。"),
        finding("第4轮 数据/存储/报告", "P1", "没有数据质量阈值", "A类为0、私活待确认80仍可生成正式报告。", "坏报告不会失败。", "设置质量门槛和醒目警告。"),
        finding("第4轮 数据/存储/报告", "P1", "Unknown字段没有集中统计", "多个scraper使用Unknown。", "字段缺失会影响排序却不提示。", "报告顶部输出unknown rate。"),
        finding("第4轮 数据/存储/报告", "P1", "没有URL规范化", "AHS/Covenant镜像和query参数可能造成重复。", "去重不稳定。", "normalize_url和external_id优先。"),
        finding("第4轮 数据/存储/报告", "P1", "没有抓取异常分类", "失败只写日志。", "不知道是网络、反爬、解析还是配置错。", "scraper返回status/error_type。"),
        finding("第4轮 数据/存储/报告", "P1", "没有CLI帮助暴露新语义", "main.py使用手动sys.argv解析。", "参数越来越多后易错。", "改argparse并写--help。"),
        finding("第4轮 数据/存储/报告", "P1", "clean_history脚本仍写sent_urls", "scripts/clean_history.sh输出sent_urls。", "清理语义继续误导。", "迁移脚本同步改名。"),
        finding("第4轮 数据/存储/报告", "P1", "没有备份/恢复策略", "storage文件直接改写。", "误清理会丢历史。", "写入前自动备份并可恢复。"),
        finding("第4轮 数据/存储/报告", "P1", "没有人工标注回流", "用户判断某岗位不合适后不能训练规则。", "同类误报会反复出现。", "添加manual_labels.json并参与过滤。"),
        finding("第4轮 数据/存储/报告", "P1", "没有测试覆盖核心过滤", "项目无正式测试框架。", "关键词修复后容易回归。", "至少为短关键词、护理分类、去重加pytest。"),
    ])

    findings.extend([
        finding("第5轮 执行/运营", "P0", "没有每日行动清单", "三个报告各自输出。", "用户不知道今天先做哪10件事。", "生成daily_action_plan.md：IT、护理、私活统一排序。"),
        finding("第5轮 执行/运营", "P0", "没有投递CRM", "系统只记录URL，不记录投递状态。", "无法管理follow-up和转化率。", "新增applications.csv/json：applied/interview/rejected/follow_up_date。"),
        finding("第5轮 执行/运营", "P0", "没有护理低英语现实策略的来源闭环", "文档写了现实策略，但抓取源没有跟上。", "系统说一套、数据做一套。", "把新增护理来源作为P0修复任务。"),
        finding("第5轮 执行/运营", "P0", "没有家庭现金流优先级", "IT找工、护理、私活没有统一ROI。", "短期养家目标无法被系统优化。", "所有机会统一打分cash_now/career/immigration。"),
        finding("第5轮 执行/运营", "P0", "没有身份路径风险提醒", "工签转换、AAIP、PR目标没有被纳入机会排序。", "可能找到工作但不帮助身份。", "对每条机会标注immigration_path_fit。"),
        finding("第5轮 执行/运营", "P0", "没有明确停止线", "不可行岗位仍大量出现。", "精力被消耗。", "设定stop rules：无英语不投高沟通岗，无许可不投受监管岗。"),
        finding("第5轮 执行/运营", "P0", "没有复盘指标", "不知道每周投递多少、回复多少、哪个方向有效。", "系统无法进化。", "每周生成conversion report。"),
        finding("第5轮 执行/运营", "P0", "没有简历/cover letter质量检查", "报告只给职位，不确认材料是否匹配。", "投递转化会低。", "每个Top岗位生成材料差异建议。"),
        finding("第5轮 执行/运营", "P1", "没有一键生成投递包", "用户还要手工拼简历、邮件、proposal。", "效率低。", "为Top岗位生成application package。"),
        finding("第5轮 执行/运营", "P1", "没有电话/短信跟进模板", "护理低门槛岗位常需要直接联系。", "仅网页投递不足。", "生成短信、电话、微信式英文模板。"),
        finding("第5轮 执行/运营", "P1", "没有日历提醒", "follow-up和证书截止时间不跟踪。", "机会容易漏。", "输出calendar_tasks.ics或markdown提醒。"),
        finding("第5轮 执行/运营", "P1", "没有雇主黑名单/白名单", "用户无法沉淀经验。", "重复踩坑。", "维护employer_notes.yaml。"),
        finding("第5轮 执行/运营", "P1", "没有家庭成员分工", "哪些事情你做、你老婆做、系统做不清晰。", "执行负担会回到用户身上。", "每日计划标注owner。"),
        finding("第5轮 执行/运营", "P1", "没有语言学习和投递联动", "英语学习与岗位类型分离。", "学了不一定能用于面试。", "按本周岗位生成情景英语。"),
        finding("第5轮 执行/运营", "P1", "没有官方资料引用检查", "策略文档缺少逐条来源日期。", "移民/许可类信息变化后容易过时。", "高风险策略必须附官方链接和检查日期。"),
        finding("第5轮 执行/运营", "P1", "没有变更日志", "多次修复后用户不知道哪些逻辑变了。", "难以信任结果。", "每次报告写入rules_changed。"),
        finding("第5轮 执行/运营", "P1", "没有异常弹窗处理说明", "Chrome crash曾出现但报告未记录。", "用户会误以为系统失控。", "运行摘要记录是否启用浏览器和失败原因。"),
        finding("第5轮 执行/运营", "P1", "没有机会老化机制", "职位下线或过期未检测。", "可能投到已关闭岗位。", "定期复查URL并标记expired。"),
        finding("第5轮 执行/运营", "P1", "没有多语言输出策略", "护理低英语阶段需要中文内部说明、英文对外材料。", "对外材料可能混入中文。", "报告内部中文，投递材料强制英文校验。"),
        finding("第5轮 执行/运营", "P1", "没有下一轮修复路线图", "100条问题没有落到开发任务。", "审查价值无法转化为系统改进。", "按P0先做数据源、状态模型、报告质量门禁、日行动清单。"),
    ])

    if len(findings) != 100:
        raise RuntimeError(f"Expected 100 findings, got {len(findings)}")
    return findings


def render(findings: List[Find]) -> str:
    """渲染Markdown报告。"""
    severity_count = Counter(item["severity"] for item in findings)
    round_count = Counter(item["round"] for item in findings)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# 当前找工作方案 P0/P1 审查报告（5轮100条）",
        "",
        f"- 生成时间: {now}",
        "- 审查范围: IT找工、护理找工、远程私活、抓取/去重/报告系统、执行闭环",
        f"- 总问题数: {len(findings)}",
        f"- P0: {severity_count['P0']}",
        f"- P1: {severity_count['P1']}",
        "",
        "## 轮次统计",
        "",
    ]

    for round_name, count in round_count.items():
        lines.append(f"- {round_name}: {count}")

    lines.extend([
        "",
        "## 最先修的10个",
        "",
        "1. 护理新增真正低语言入口来源，解决A类为0。",
        "2. 护理岗位增加can_apply_now，默认隐藏RN/LPN/GN/Head Nurse。",
        "3. 把sent_urls迁移成seen_urls/recorded_urls，并新增applications投递表。",
        "4. 私活报告拆分freelance contract和remote full-time。",
        "5. 私活proposal重新生成并加英文-only校验。",
        "6. 清理Claude/ANTHROPIC残留配置，统一Codex/local评分。",
        "7. IT报告降级TAM、pre-sales、solutions、go-to-market等边缘岗位。",
        "8. 生成统一daily_action_plan，按现金流、身份价值、成功率排序。",
        "9. 为护理建立工签限制、证书、英语、许可清单。",
        "10. 加报告质量门禁：A类为0、预算未知过高、source失败过多时必须醒目标红。",
        "",
        "## 100条问题清单",
        "",
        "| # | 轮次 | 级别 | 问题 | 证据 | 影响 | 修复方向 |",
        "|---:|---|---|---|---|---|---|",
    ])

    for idx, item in enumerate(findings, 1):
        lines.append(
            f"| {idx} | {item['round']} | {item['severity']} | {item['title']} | "
            f"{item['evidence']} | {item['impact']} | {item['fix']} |"
        )

    lines.extend([
        "",
        "## 结论",
        "",
        "当前系统不是没有价值，真正的问题是三条主线的可执行性没有被统一建模。",
        "护理的最大缺口是数据源和英语现实；IT的最大缺口是岗位质量分层；私活的最大缺口是把远程全职当成项目机会。",
        "系统层最大缺口是看过、记录过、投递过三种状态混在一起。",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    """入口。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    findings = build_findings()
    OUTPUT_FILE.write_text(render(findings), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")
    print(f"Findings: {len(findings)}")


if __name__ == "__main__":
    main()
