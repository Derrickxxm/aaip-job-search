"""过滤器模块"""
import re

from models.job import Job
from utils.logger import logger


class JobFilter:
    """职位过滤器"""

    def __init__(self, config: dict):
        self.tech_keywords = [k.lower() for k in config.get('tech_keywords', [])]
        self.strong_role_keywords = [k.lower() for k in config.get('strong_role_keywords', [])]
        self.weak_role_keywords = [k.lower() for k in config.get('weak_role_keywords', [])]
        self.domain_keywords = [k.lower() for k in config.get('domain_keywords', [])]
        self.generic_it_role_keywords = [k.lower() for k in config.get('generic_it_role_keywords', [])]
        self.baseline_role_keywords = [k.lower() for k in config.get('baseline_role_keywords', [])]
        self.level_keywords = [k.lower() for k in config.get('level_keywords', [])]
        self.location_filter = [l.lower() for l in config.get('location_filter', [])]
        self.exclude_keywords = [k.lower() for k in config.get('exclude_keywords', [])]
        self.customer_facing_role_keywords = [
            k.lower() for k in config.get('customer_facing_role_keywords', [])
        ]
        self.engineering_anchor_keywords = [
            k.lower() for k in config.get('engineering_anchor_keywords', [])
        ]
        self.debug_enabled = config.get('debug', {}).get('enabled', False)

        # HTML实体解码映射
        from html import unescape
        self.unescape = unescape

    def _clean_text(self, text: str) -> str:
        """清理文本（解码HTML实体）"""
        # 解码HTML实体（&amp; → &）
        cleaned = self.unescape(text)
        # 潬成小写
        return cleaned.lower()

    @staticmethod
    def _matches_keyword(text: str, keyword: str) -> bool:
        """匹配关键词，单词型关键词要求完整单词，避免 intern 命中 intermediate"""
        if keyword == 'intern':
            return re.search(r'\bintern(ship)?\b|\bintern(?=[a-z])', text) is not None
        if keyword == 'co-op':
            return re.search(r'\bco[- ]op\b', text) is not None
        if keyword.replace('-', '').isalnum() and ' ' not in keyword:
            return re.search(rf'\b{re.escape(keyword)}\b', text) is not None
        return keyword in text

    def _matches_any(self, text: str, keywords: list[str]) -> bool:
        """检查文本是否命中任一关键词"""
        return any(self._matches_keyword(text, keyword) for keyword in keywords)

    def _title_department_text(self, job: Job) -> tuple[str, str]:
        """返回清洗后的标题，以及标题+部门组合文本"""
        title_clean = self._clean_text(job.title)
        department_clean = self._clean_text(job.department or '')
        return title_clean, f"{title_clean} {department_clean}".strip()

    def matches_tech_stack(self, job: Job) -> bool:
        """检查是否匹配目标技术/工程岗位"""
        title_clean, searchable_text = self._title_department_text(job)

        # 强岗位词直接通过，避免 Software Developer 这类基础职位被级别词误杀。
        if self._matches_any(title_clean, self.strong_role_keywords):
            return True

        # 精准技术词直接通过，配置里不再放 Engineer/Developer/Technical 这类泛词。
        if self._matches_any(title_clean, self.tech_keywords):
            return True

        # 泛岗位词必须和工程锚点或目标领域同时出现，降低 Solutions/Support/泛IT误入。
        has_weak_role = self._matches_any(title_clean, self.weak_role_keywords)
        has_engineering_anchor = self._matches_any(searchable_text, self.engineering_anchor_keywords)
        has_domain = self._matches_any(searchable_text, self.domain_keywords)
        matched = has_weak_role and (has_engineering_anchor or has_domain)

        if not matched and self.debug_enabled:
            logger.debug(f"Tech stack NOT matched: '{job.title}'")
        return matched

    def matches_level(self, job: Job) -> bool:
        """检查是否匹配岗位级别"""
        title_clean = self._clean_text(job.title)
        matched = (
            self._matches_any(title_clean, self.level_keywords)
            or self._matches_any(title_clean, self.baseline_role_keywords)
            or self._matches_any(title_clean, self.strong_role_keywords)
        )
        if not matched and self.debug_enabled:
            logger.debug(f"Level NOT matched: '{job.title}' (keywords: {self.level_keywords[:3]}...)")
        return matched

    def matches_location(self, job: Job) -> bool:
        """检查是否匹配地点"""
        location_clean = self._clean_text(job.location)

        alberta_terms = [
            'calgary',
            'edmonton',
            'alberta',
            'sherwood park',
            ', ab',
            ' ab,',
            ' ab ',
        ]
        non_alberta_city_terms = [
            'vancouver',
            'victoria',
            'toronto',
            'mississauga',
            'waterloo',
            'kitchener',
            'ottawa',
            'montreal',
            'winnipeg',
            'halifax',
            'oakville',
        ]

        has_alberta_location = any(term in location_clean for term in alberta_terms)
        has_non_alberta_city = any(term in location_clean for term in non_alberta_city_terms)

        # 外省城市列表不进入IT主报告。即使同时列出Calgary/Edmonton，也先不放主投清单，避免误导。
        if has_non_alberta_city:
            if self.debug_enabled:
                logger.debug(f"Location NOT matched: '{job.location}' (contains non-Alberta city)")
            return False

        # 阿省城市/省份明确命中，直接接受。
        if has_alberta_location:
            return True

        # Canada Remote可以接受，但不能是外省城市列表加一个Canada Remote的泛地点。
        is_canada_remote = 'remote' in location_clean and 'canada' in location_clean
        if is_canada_remote and not has_non_alberta_city:
            return True

        # 否则检查是否在Alberta
        matched = any(loc in location_clean for loc in self.location_filter)
        if not matched and self.debug_enabled:
            logger.debug(f"Location NOT matched: '{job.location}' (filter: {self.location_filter[:3]}...)")
        return matched

    def should_exclude(self, job: Job) -> bool:
        """检查是否应该排除"""
        title_clean = self._clean_text(job.title)
        matched_keyword = None
        for keyword in self.exclude_keywords:
            if self._matches_keyword(title_clean, keyword):
                matched_keyword = keyword
                break
        if matched_keyword and self.debug_enabled:
            logger.debug(f"Excluded by keyword: '{job.title}' (found: '{matched_keyword}')")
        return matched_keyword is not None

    def is_generic_it_support_role(self, job: Job) -> bool:
        """过滤桌面支持、Help Desk、泛IT运维等非主攻岗位"""
        if not self.generic_it_role_keywords:
            return False

        title_clean = self._clean_text(job.title)
        matched = self._matches_any(title_clean, self.generic_it_role_keywords)
        if matched and self.debug_enabled:
            logger.debug(f"Excluded generic IT/support role: '{job.title}'")
        return matched

    def is_customer_facing_edge_role(self, job: Job) -> bool:
        """过滤售前、客户成功、GTM等边缘岗位，除非标题中同时有明确工程锚点"""
        if not self.customer_facing_role_keywords:
            return False

        title_clean = self._clean_text(job.title)
        has_edge_signal = any(
            self._matches_keyword(title_clean, keyword)
            for keyword in self.customer_facing_role_keywords
        )
        if not has_edge_signal:
            return False

        has_engineering_anchor = any(
            self._matches_keyword(title_clean, keyword)
            for keyword in self.engineering_anchor_keywords
        )
        if has_engineering_anchor:
            return False

        if self.debug_enabled:
            logger.debug(f"Excluded customer-facing edge role: '{job.title}'")
        return True

    def is_match(self, job: Job) -> bool:
        """综合判断是否匹配"""
        # 先检查排除项
        if self.should_exclude(job):
            logger.debug(f"Final: FILTERED (excluded)")
            return False

        if self.is_customer_facing_edge_role(job):
            logger.debug("Final: FILTERED (customer-facing edge role)")
            return False

        if self.is_generic_it_support_role(job):
            logger.debug("Final: FILTERED (generic IT/support role)")
            return False

        # 检查技术栈、级别、地点
        tech_match = self.matches_tech_stack(job)
        level_match = self.matches_level(job)
        location_match = self.matches_location(job)
        final_match = tech_match and level_match and location_match

        if self.debug_enabled:
            logger.debug(f"Final: {'MATCHED' if final_match else 'FILTERED'} (tech={tech_match}, level={level_match}, loc={location_match})")
        return final_match
