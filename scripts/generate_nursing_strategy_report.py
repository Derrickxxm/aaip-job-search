"""生成护理求职策略和按可行性排序的护理机会报告"""
import re
from datetime import datetime
from pathlib import Path


VAULT_DIR = Path("/Users/xxm/projects/QuantEngine_markdown_file/12-找工作/nursing")
SOURCE_REPORT = VAULT_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_匹配职位.md"
STRATEGY_DOC = VAULT_DIR / "护理求职策略_开放工签_未取得RN许可.md"
SORTED_REPORT = VAULT_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_护理机会_按当前可行性排序.md"


def parse_jobs(path: Path) -> list[dict]:
    """从现有 Markdown 报告解析职位"""
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"\n### \d+\. ", text)
    jobs = []

    for block in blocks[1:]:
        lines = block.strip().splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        job = {"title": title}
        for line in lines:
            if line.startswith("- **公司**:"):
                job["company"] = line.split(":", 1)[1].strip()
            elif line.startswith("- **地点**:"):
                job["location"] = line.split(":", 1)[1].strip()
            elif line.startswith("- **平台**:"):
                job["platform"] = line.split(":", 1)[1].strip()
            elif line.startswith("- **链接**:"):
                match = re.search(r"\((.*?)\)", line)
                job["url"] = match.group(1) if match else ""
            elif line.startswith("- **部门**:"):
                job["department"] = line.split(":", 1)[1].strip()
        jobs.append(job)

    return jobs


def canonical_job_key(job: dict) -> str:
    """用职位编号去重，AHS/Covenant 镜像会出现同一 job id"""
    url = job.get("url", "")
    match = re.search(r"/jobs/.*-(\d+)$", url)
    if match:
        return match.group(1)
    return "|".join([
        job.get("title", "").lower(),
        job.get("location", "").lower(),
        job.get("company", "").lower(),
    ])


def dedupe_jobs(jobs: list[dict]) -> tuple[list[dict], int]:
    """按 job id 去重，同一职位优先保留更匹配 company 域名的版本"""
    by_key: dict[str, dict] = {}

    for job in jobs:
        key = canonical_job_key(job)
        existing = by_key.get(key)
        if not existing:
            by_key[key] = job
            continue

        existing_url = existing.get("url", "")
        current_url = job.get("url", "")
        existing_company = existing.get("company", "").lower()
        current_company = job.get("company", "").lower()

        current_matches_domain = (
            "covenant" in current_company and "covenanthealth.ca" in current_url
        ) or (
            "alberta health services" in current_company and "albertahealthservices.ca" in current_url
        )
        existing_matches_domain = (
            "covenant" in existing_company and "covenanthealth.ca" in existing_url
        ) or (
            "alberta health services" in existing_company and "albertahealthservices.ca" in existing_url
        )

        if current_matches_domain and not existing_matches_domain:
            by_key[key] = job

    return list(by_key.values()), len(jobs) - len(by_key)


def classify_job(job: dict) -> tuple[str, int, str]:
    """返回分类、排序分、说明"""
    title = job["title"].lower()
    company = job.get("company", "")
    company_clean = company.lower()
    location = job.get("location", "").lower()

    regulated_rn_lpn = [
        "registered nurse",
        "licensed practical nurse",
        "graduate nurse",
        " rn ",
        " lpn ",
        "r.n.",
        "l.p.n.",
        "psychiatric nurse",
        "nurse practitioner",
        "head nurse",
    ]
    if any(key in f" {title} " for key in regulated_rn_lpn):
        return (
            "隐藏：需要RN/LPN许可",
            300,
            "需要对应护理注册和 practice permit；现在先收藏，不作为主投。",
        )

    hca_keys = [
        "health care aide",
        "healthcare aide",
        "care aide",
        "home care",
        "continuing care",
    ]
    if any(key in title for key in hca_keys):
        if "home care" in title:
            return (
                "隐藏：上门照护/家庭照护",
                245,
                "HCA Home Care 通常是上门服务；当前先不作为她的开放工签主路径。",
            )
        score = 10
        if "edmonton" in location or "calgary" in location:
            score -= 3
        if company in {"Alberta Health Services", "Covenant Health"}:
            return (
                "P3. 准备后投：HCA/长期照护",
                score,
                "经验匹配，但英语完全不能沟通时短期难度较高；先准备 CLHA/HCA 注册、英语证明或等效评估，等能做基础沟通后重点投。",
            )
        return (
            "P3. 准备后投：HCA/长期照护",
            score + 5,
            "照护类岗位方向正确，但仍需确认英语、HCA注册、CPR、背景调查和免疫记录要求。",
        )

    household_caregiver_keys = [
        "child caregiver",
        "live-in caregiver",
        "family caregiver",
        "nanny",
        "babysitter",
        "private home",
        "private household",
        "domestic",
    ]
    if any(key in title for key in household_caregiver_keys) or "private household" in company_clean:
        return (
            "隐藏：私人家庭/住家照护",
            270,
            "不作为主线：这类更接近住家保姆/私人家庭服务，和她20年护理经验、职业尊严、后续HCA/RN路径关联弱。",
        )

    care_agency_signals = [
        "care",
        "health",
        "support",
        "services",
        "transitions",
        "project",
        "foundation",
        "seniors",
        "senior",
    ]
    direct_home_support_keys = [
        "personal support worker",
        "personal support",
        "home support worker",
        "home support",
        "senior support",
        "respite worker",
        "personal care attendant",
        "attendant for persons with disabilities",
    ]
    if any(key in title for key in direct_home_support_keys) and any(key in company_clean for key in care_agency_signals):
        return (
            "隐藏：上门照护/家庭照护",
            250,
            "personal support/home support 很容易变成上门家庭照护；当前不作为她的开放工签主路径。",
        )

    if any(key in title for key in direct_home_support_keys):
        return (
            "隐藏：上门照护/家庭照护",
            255,
            "personal support/home support 很容易变成上门家庭照护；当前不作为她的开放工签主路径。",
        )

    institution_signals = [
        "alberta health services",
        "covenant health",
        "senior",
        "seniors",
        "retirement",
        "long term",
        "long-term",
        "foundation",
        "manor",
        "villa",
        "health",
        "hospital",
    ]
    institutional_support_keys = [
        "service worker",
        "porter",
        "portering",
        "environmental services",
        "medical device reprocessing",
        "surgical processor",
        "linen",
        "laundry",
        "dietary aide",
        "kitchen aide",
        "kitchen helper",
        "food service",
        "support service",
    ]
    is_institution = any(key in company_clean for key in institution_signals)
    if is_institution and any(key in title for key in institutional_support_keys):
        if any(key in title for key in ["environmental", "cleaner", "housekeeper", "housekeeping"]):
            return (
                "隐藏：环境服务/清洁消毒",
                275,
                "Environmental Services 本质多为医院清洁/消毒；当前不作为她的开放工签主路径。",
            )
        if any(key in title for key in ["medical device reprocessing", "surgical processor"]):
            return (
                "P1. 先查证书：MDR/消毒供应",
                20,
                "医疗系统内的专业支持岗，和护理背景有关联；先确认是否要求 MDR 证书，若只要求可培训则优先投。",
            )
        if any(key in title for key in ["service worker", "porter", "portering"]):
            return (
                "P0. 最优先：Service Worker/Porter/OR支持",
                10,
                "医疗系统内支持岗，不需要 RN/LPN 许可；比低关联岗位更值得用开放工签去争取。",
            )
        return (
            "P2. 现金流备选：医疗机构Food/Laundry/Linen",
            40,
            "医疗/养老机构内后勤岗位。对护理路径帮助弱于 Service Worker/MDR，但比私人家庭和普通岗位更稳。",
        )

    generic_cashflow_keys = [
        "hotel housekeeper",
        "housekeeper",
        "housekeeping",
        "cleaner",
        "window cleaner",
        "office cleaner",
        "fast-food",
        "food counter",
        "dishwasher",
        "barista",
        "cook's helper",
        "restaurant",
    ]
    if any(key in title for key in generic_cashflow_keys):
        return (
            "隐藏：普通现金流岗位",
            280,
            "普通清洁、餐饮或酒店岗位不进入当前护理主路径；如果家庭现金流需要，另按非护理现金流清单单独处理。",
        )

    if any(key in title for key in ["unit clerk", "clinical informatics", "attendant", "patient", "operating room"]):
        return (
            "隐藏：英语/系统要求偏高",
            260,
            "通常需要较强英语、医学术语或系统记录能力；当前先收藏，英语提升后再看。",
        )

    return (
        "隐藏：匹配不确定",
        220,
        "护理相关但当前资格匹配不确定；英语完全不能沟通时不建议主投。",
    )


def write_strategy_doc() -> None:
    """写入当前实际策略文档"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"""# 护理求职策略：开放工签 + 未取得阿省 RN 许可 + 英语暂不能沟通

**更新时间**: {now}

## 当前结论

她的开放工签要用在能提高家庭现金流、保留职业路径、又不把她压到私人家庭保姆或普通清洁的位置上。

当前只保留两条护理相关路径：

1. **优先主投：医疗系统支持岗**
   AHS、Covenant、医院、长期护理机构里的 Service Worker、Porter、Food Service、Dietary Aide、Laundry/Linen、Medical Device Reprocessing、Surgical Processor。

2. **过渡目标：HCA/正规机构照护**
   Health Care Aide、Care Aide、Continuing Care、长期护理机构照护。英语完全不能沟通时不大量投，先准备材料和基础沟通。

明确排除：

- 私人家庭、上门照护/home support、住家 caregiver、child caregiver、nanny、babysitter。
- 普通清洁、酒店 housekeeping、office/window/house cleaner。
- RN/LPN/GN：未取得阿省 practice permit 前不主投。
- Unit Clerk、Clinical Informatics 等大量电话、记录和系统沟通岗位：英语上来前不主投。

## 为什么这样排

- 私人家庭和普通清洁对她 20 年护士经验利用率低，也很难转成后续 RN/HCA 路径。
- 医疗系统支持岗虽然不是护士岗，但能带来本地医疗环境、reference、内部岗位认知和真实工作英语。
- HCA 最贴近护理经验，但当前最大短板是英语沟通和阿省 HCA/CLHA 材料，不是“有没有开放工签”。
- AAIP 路线要注意当前 occupation、工作经验和 job offer 的一致性。不要为了短期入职选一个以后解释不清的低关联职业。

## 其它省事但不浪费工签的备选

这些不属于护理主线，但比私人家庭和普通清洁更适合作为现金流备选：

- **医院/养老机构物资岗**: Stores Attendant、Supply Attendant、Materials Handler、Inventory Clerk。优先医疗机构。
- **仓库/电商后仓**: Warehouse Associate、Order Picker、Packer、Sorter。英语要求低，入职快，但和护理路径关联弱。
- **生产/包装线**: Production Worker、Packaging Worker、Assembler。适合先现金流，但要确认全职、雇主正规、职业是否适合后续 AAIP。
- **机构厨房后场**: Food Service Worker、Kitchen Helper、Dietary Aide。只投医院、学校、养老机构，不投普通餐馆快餐。
- **MDR/消毒供应方向**: Medical Device Reprocessing、Sterile Processing、Surgical Processor。最值得关注，但要逐条确认是否要求证书。

执行顺序：

1. P0：Service Worker、Porter、OR 支持岗。当前最合适，先投。
2. P1：MDR/消毒供应。和护理背景最贴近，但先确认是否硬性要求证书。
3. P2：医疗/养老机构 Food Service、Laundry、Linen。作为现金流备选，不当最终职业路径。
4. P3：HCA/长期照护。等英语和 HCA/CLHA 材料后再提高投递量。
5. 非护理现金流：仓库、生产、包装。只有当 P0-P2 不够时再单独开搜索。

## 立即动作

1. 检查开放工签是否有 health services restriction；如果有，先体检并申请移除。
2. 简历只做两版：医疗系统支持岗版、HCA/正规照护版。
3. 每天练 30-60 分钟工作场景英语：报到、听指令、确认任务、安全提醒、求助、交接。
4. 护理岗位报告只看 A/B 两类；隐藏项不再浪费投递时间。
5. 如果 A/B 机会不足，再开一个“非护理现金流”搜索配置，专门抓医疗物资、仓库、生产、机构厨房。
"""
    STRATEGY_DOC.write_text(content, encoding="utf-8")


def write_sorted_report(jobs: list[dict]) -> None:
    """写入排序后的机会报告"""
    grouped: dict[str, list[tuple[int, str, dict]]] = {}
    for job in jobs:
        category, score, note = classify_job(job)
        grouped.setdefault(category, []).append((score, note, job))

    for category in grouped:
        grouped[category].sort(key=lambda item: (item[0], item[2].get("company", ""), item[2]["title"]))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = sum(len(items) for items in grouped.values())
    category_counts = {category: len(items) for category, items in grouped.items()}
    visible_categories = [
        "P0. 最优先：Service Worker/Porter/OR支持",
        "P1. 先查证书：MDR/消毒供应",
        "P2. 现金流备选：医疗机构Food/Laundry/Linen",
        "P3. 准备后投：HCA/长期照护",
    ]
    visible_count = sum(category_counts.get(category, 0) for category in visible_categories)
    hidden_count = total - visible_count
    lines = [
        "# 护理机会：只保留当前最佳路径",
        "",
        f"**生成时间**: {now}",
        f"**来源文件**: `{SOURCE_REPORT}`",
        f"**原始去重职位数**: {total}",
        f"**推荐输出职位数**: {visible_count}",
        f"**已隐藏职位数**: {hidden_count}",
        "",
        "## 当前口径",
        "",
        "- 排序标准：职业路径匹配度 > 当前可入职概率 > 英语压力 > 是否能支持后续 HCA/RN/医疗系统路径。",
        "- 不输出私人家庭、上门照护/home support、住家 caregiver、普通清洁、酒店 housekeeping、Environmental Services、标题含 cleaner/housekeeper 的岗位、RN/LPN/GN、英语/系统要求明显偏高的岗位。",
        "- P0 最值得先投；P1 先查证书；P2 是现金流备选；P3 等英语和 HCA 材料后再投。",
        "",
        "## 隐藏项统计",
        "",
    ]

    for category, count in sorted(category_counts.items()):
        if category not in visible_categories:
            lines.append(f"- {category}: {count}")

    for category in visible_categories:
        items = grouped.get(category, [])
        lines.extend(["", f"## {category}（{len(items)}）", ""])
        for index, (_, note, job) in enumerate(items, 1):
            lines.extend([
                f"### {index}. {job['title']}",
                "",
                f"- **公司**: {job.get('company', 'N/A')}",
                f"- **地点**: {job.get('location', 'N/A')}",
                f"- **部门**: {job.get('department', 'N/A')}",
                f"- **链接**: [查看职位]({job.get('url', '')})",
                f"- **现在是否主投**: {'是' if category.startswith('P0.') else '先确认条件' if category.startswith('P1.') else '现金流备选' if category.startswith('P2.') else '准备后投'}",
                f"- **当前判断**: {note}",
                "",
            ])

    SORTED_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not SOURCE_REPORT.exists():
        raise FileNotFoundError(f"Source report not found: {SOURCE_REPORT}")
    parsed_jobs = parse_jobs(SOURCE_REPORT)
    jobs, duplicate_count = dedupe_jobs(parsed_jobs)
    write_strategy_doc()
    write_sorted_report(jobs)
    print(STRATEGY_DOC)
    print(SORTED_REPORT)
    print(f"jobs={len(jobs)} duplicates_removed={duplicate_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
