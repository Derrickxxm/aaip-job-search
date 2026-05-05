"""主程序入口"""
import os
import sys
from datetime import datetime

from utils.config_loader import ConfigLoader
from utils.logger import logger
from storage.job_storage import JobStorage
from filters.job_filter import JobFilter
from notification.local_storage import LocalStorageNotifier
from utils.job_link_validator import JobLinkValidator
from scrapers.greenhouse import GreenhouseScraper
from scrapers.ashby import AshbyScraper
from scrapers.custom import CustomScraper
from scrapers.lever import LeverScraper
from scrapers.jazzhr import JazzHRScraper
from scrapers.bamboohr import BambooHRScraper
from scrapers.jobber import JobberScraper
from scrapers.jobvite import JobviteScraper
from scrapers.shopify import ShopifyScraper
from scrapers.jobbank import JobBankScraper
from scrapers.ahs import AHSScraper


os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', os.path.join(os.getcwd(), '.ms-playwright'))

# 配置文件映射
PROFILES = {
    'tech': {
        'config': 'config/production.yaml',
        'companies': 'config/companies.json',
        'storage': 'storage/jobs.json',
    },
    'nursing': {
        'config': 'config/nursing.yaml',
        'companies': 'config/nursing_companies.json',
        'storage': 'storage/nursing_jobs.json',
    },
}


def get_profile():
    """从命令行参数获取profile"""
    for arg in sys.argv:
        if arg.startswith('--profile='):
            return arg.split('=', 1)[1]
        if arg == '--profile' and sys.argv.index(arg) + 1 < len(sys.argv):
            return sys.argv[sys.argv.index(arg) + 1]
    return 'tech'  # 默认tech


def is_dry_run() -> bool:
    """是否只运行抓取和过滤，不写报告、不更新去重记录"""
    return '--dry-run' in sys.argv


def include_sent() -> bool:
    """是否包含历史已记录职位，用于全量对比和调试"""
    return '--include-sent' in sys.argv or '--include-recorded' in sys.argv


def no_mark_recorded() -> bool:
    """是否不更新历史记录，用于重新生成报告或人工复核"""
    return '--no-mark-recorded' in sys.argv


def overwrite_report() -> bool:
    """是否覆盖当天报告，用于修复过滤规则后重新生成"""
    return '--overwrite-report' in sys.argv


def allow_playwright() -> bool:
    """是否允许启动浏览器兜底抓取"""
    return '--allow-playwright' in sys.argv


def skip_link_validation() -> bool:
    """是否跳过职位链接有效性校验"""
    return '--skip-link-validation' in sys.argv


def main():
    """主函数"""
    profile = get_profile()
    profile_config = PROFILES.get(profile, PROFILES['tech'])
    dry_run = is_dry_run()
    show_sent = include_sent()
    skip_recording = no_mark_recorded()
    replace_report = overwrite_report()
    browser_enabled = allow_playwright()
    link_validation_skipped = skip_link_validation()
    if not browser_enabled:
        os.environ['DISABLE_PLAYWRIGHT'] = '1'

    logger.info("=" * 60)
    logger.info(
        f"Starting AAIP Job Aggregator "
        f"(profile: {profile}, dry_run: {dry_run}, include_sent: {show_sent}, "
        f"no_mark_recorded: {skip_recording}, overwrite_report: {replace_report}, "
        f"allow_playwright: {browser_enabled}, skip_link_validation: {link_validation_skipped})"
    )
    logger.info("=" * 60)

    # 1. 加载配置
    config = ConfigLoader.load_config(profile_config['config'])
    companies = ConfigLoader.load_companies(profile_config['companies'])

    # 2. 初始化组件
    storage = JobStorage(storage_path=profile_config['storage'])
    job_filter = JobFilter(config)

    # 使用本地存储（MD文件）
    vault_dir = config.get('storage', {}).get('vault_dir', '/Users/xxm/projects/QuantEngine_markdown_file/12-找工作')
    local_notifier = None if dry_run else LocalStorageNotifier(vault_dir=vault_dir)

    # 提取请求配置（带默认值）
    request_config = config.get('request', {})
    request_timeout = request_config.get('timeout', 10)
    request_user_agent = request_config.get('user_agent', 'Mozilla/5.0')

    # 3. 抓取所有公司职位
    all_new_jobs = []

    for company in companies:
        # 跳过状态为pending的公司
        if company.get('status') == 'pending':
            logger.info(f"Skipping {company['name']} (status: pending)")
            continue

        # 选择对应的抓取器
        platform = company.get('platform', '')
        company_id = company.get('id')
        company_name = company.get('name')
        url = company.get('careers_url')

        scraper = None
        if platform == 'greenhouse':
            scraper = GreenhouseScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent
            )
        elif platform == 'ashby':
            scraper = AshbyScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent
            )
        elif platform == 'lever':
            scraper = LeverScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent
            )
        elif platform == 'jazzhr':
            scraper = JazzHRScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent
            )
        elif platform == 'bamboohr':
            scraper = BambooHRScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent
            )
        elif platform == 'jobber':
            scraper = JobberScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent
            )
        elif platform == 'jobvite':
            scraper = JobviteScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent
            )
        elif platform == 'shopify':
            scraper = ShopifyScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent
            )
        elif platform == 'jobbank':
            scraper = JobBankScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent,
                config=config
            )
        elif platform == 'ahs':
            scraper = AHSScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent,
                config=config
            )
        elif platform == 'covenant':
            # Covenant Health 也用AHS同一系统
            scraper = AHSScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent,
                config=config
            )
        else:
            scraper = CustomScraper(
                company_id=company_id,
                company_name=company_name,
                url=url,
                timeout=request_timeout,
                user_agent=request_user_agent
            )

        # 抓取职位
        if scraper:
            try:
                jobs = scraper.fetch_jobs()

                # 过滤职位
                matched_jobs = []
                for job in jobs:
                    # 检查去重
                    if storage.is_recorded(job.url) and not show_sent:
                        logger.info(f"Skipping recorded job: {job.title}")
                        continue

                    # 应用过滤规则
                    if job_filter.is_match(job):
                        matched_jobs.append(job)
                        logger.info(f"✓ Matched: {job.title} @ {company_name}")
                    else:
                        logger.info(f"✗ Filtered: {job.title} @ {company_name}")

                all_new_jobs.extend(matched_jobs)

            except Exception as e:
                logger.error(f"Error processing {company_name}: {e}")

    # 4. 保存到本地MD文件
    if all_new_jobs:
        validation_config = config.get('link_validation', {})
        validation_enabled = validation_config.get('enabled', True) and not link_validation_skipped
        if validation_enabled:
            validator = JobLinkValidator(
                timeout=validation_config.get('timeout', 8),
                user_agent=request_user_agent
            )
            before_count = len(all_new_jobs)
            all_new_jobs = validator.filter_active_jobs(all_new_jobs)
            logger.info(f"Link validation kept {len(all_new_jobs)}/{before_count} matching jobs")

        if not all_new_jobs:
            logger.info("No matching jobs left after link validation")
            return

        if show_sent:
            logger.info(f"Found {len(all_new_jobs)} matching jobs including recorded jobs")
        else:
            logger.info(f"Found {len(all_new_jobs)} unrecorded matching jobs")

        if dry_run:
            logger.info("Dry run enabled, skipping report write and storage update")
            for job in all_new_jobs[:20]:
                logger.info(f"[DRY-RUN] {job.title} @ {job.company} | {job.location} | {job.url}")
            if len(all_new_jobs) > 20:
                logger.info(f"[DRY-RUN] ... {len(all_new_jobs) - 20} more jobs")
            return

        # 保存到MD文件（追加到当天报告）
        filepath = local_notifier.save_jobs(all_new_jobs) if replace_report else local_notifier.append_to_daily_report(all_new_jobs)

        # 标记为历史已记录
        if filepath and not skip_recording:
            urls = [job.url for job in all_new_jobs]
            storage.mark_recorded(urls)
            logger.info(f"Marked {len(urls)} jobs as recorded")
        elif filepath:
            logger.info("Skipped storage update because --no-mark-recorded is enabled")
    else:
        logger.info("No new matching jobs found")

    logger.info("=" * 60)
    logger.info("AAIP Job Aggregator completed")
    logger.info("=" * 60)


def check_schedule():
    """检查当前时间是否在预定时间范围内"""
    config = ConfigLoader.load_config()
    scheduled_hours = config.get('schedule', {}).get('hours', [8, 12, 18])

    current_hour = datetime.now().hour
    if current_hour in scheduled_hours:
        logger.info(f"Current hour {current_hour} is in scheduled hours {scheduled_hours}")
        return True
    else:
        logger.info(f"Current hour {current_hour} not in scheduled hours {scheduled_hours}")
        return False


if __name__ == '__main__':
    # 如果传入--check参数，只检查时间
    if '--check' in sys.argv:
        if check_schedule():
            main()
        else:
            logger.info("Skipping: not in scheduled time")
    else:
        # 直接运行（用于手动测试）
        main()
