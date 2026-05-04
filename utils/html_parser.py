"""HTML解析辅助函数"""
from bs4 import BeautifulSoup
from bs4 import FeatureNotFound

from utils.logger import logger


def parse_html(html: str) -> BeautifulSoup:
    """解析HTML，lxml不可用时退回Python内置解析器"""
    try:
        return BeautifulSoup(html, 'lxml')
    except FeatureNotFound:
        logger.warning("lxml parser unavailable, falling back to html.parser")
        return BeautifulSoup(html, 'html.parser')
