"""日志模块"""
import logging
import os
from datetime import datetime


def setup_logging(log_dir: str = 'logs', log_file: str = 'scraper.log'):
    """配置日志系统"""
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_path = os.path.join(log_dir, log_file)

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )

    return logging.getLogger(__name__)


# 全局logger
logger = setup_logging()
