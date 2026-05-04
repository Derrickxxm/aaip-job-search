import re
from typing import List, Tuple

from freelance.models.project import FreelanceProject
from freelance.utils.logger import get_logger

logger = get_logger(__name__)

# These keywords are too broad — only match in title + tags, not description
TITLE_ONLY_KEYWORDS = {
    'ai', 'rag', 'cloud', 'express', 'automation', 'infrastructure',
}

# Exclude keywords that only apply to title (not description),
# because they cause false positives when matching substrings in descriptions
# e.g. "intern" matches "internal", "international", "internet"
TITLE_ONLY_EXCLUDE = {
    'junior', 'intern', 'internship', 'entry level', 'entry-level',
    'customer service', 'data entry',
}


class SkillMatcher:
    def __init__(self, config: dict):
        self.strong_keywords = config['filter']['strong_keywords']
        self.exclude_keywords = config['filter']['exclude_keywords']
        self.min_matches = config['filter'].get('min_keyword_matches', 2)

    def is_match(self, project: FreelanceProject) -> Tuple[bool, List[str]]:
        """Returns (is_match, matched_keywords_list)"""
        title_tags = (project.title + ' ' + ' '.join(project.tags)).lower()
        full_text = (title_tags + ' ' + project.description[:2000]).lower()

        # Exclusion check: some keywords only checked against title+tags
        for kw in self.exclude_keywords:
            if kw in TITLE_ONLY_EXCLUDE:
                # Use word boundary for title-only excludes to avoid
                # "intern" matching "internal"/"internet"
                if re.search(r'\b' + re.escape(kw) + r'\b', title_tags):
                    logger.debug(f"Excluded by title keyword '{kw}': {project.title}")
                    return False, []
            else:
                if kw in full_text:
                    logger.debug(f"Excluded by keyword '{kw}': {project.title}")
                    return False, []

        # Skill matching: broad keywords only check title+tags
        matched_keywords = []
        for kw in self.strong_keywords:
            if kw in TITLE_ONLY_KEYWORDS:
                if kw in title_tags:
                    matched_keywords.append(kw)
            else:
                if kw in full_text:
                    matched_keywords.append(kw)

        return len(matched_keywords) >= self.min_matches, matched_keywords
