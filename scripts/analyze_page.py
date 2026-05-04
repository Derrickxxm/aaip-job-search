"""分析职位页面结构的脚本"""
from playwright.sync_api import sync_playwright
import sys


def analyze_page(url: str, company: str):
    """使用Playwright分析页面结构"""
    print(f"\n{'='*60}")
    print(f"分析 {company} 页面: {url}")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        try:
            page.goto(url, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=15000)

            # 获取页面标题
            title = page.title()
            print(f"页面标题: {title}\n")

            # 查找可能的职位容器
            print("="*40)
            print("查找职位相关元素...")
            print("="*40)

            # 常见的职位相关选择器
            selectors_to_try = [
                # 通用职位选择器
                ('a[href*="job"]', '包含job的链接'),
                ('a[href*="career"]', '包含career的链接'),
                ('a[href*="position"]', '包含position的链接'),
                ('a[href*="opening"]', '包含opening的链接'),
                ('a[href*="apply"]', '包含apply的链接'),

                # 常见类名
                ('.job-card', 'job-card类'),
                ('.job-listing', 'job-listing类'),
                ('.job-item', 'job-item类'),
                ('.career-item', 'career-item类'),
                ('.position-item', 'position-item类'),
                ('.opening', 'opening类'),

                # Lever特征
                ('.posting', 'posting类 (Lever)'),
                ('.posting-title', 'posting-title类 (Lever)'),

                # Greenhouse特征
                ('.job-post', 'job-post类 (Greenhouse)'),

                # JazzHR特征
                ('#resumator-jobs', 'resumator-jobs ID (JazzHR)'),
                ('.resumator-job', 'resumator-job类 (JazzHR)'),

                # iframe (有些公司用iframe嵌入)
                ('iframe[src*="greenhouse"]', 'Greenhouse iframe'),
                ('iframe[src*="lever"]', 'Lever iframe'),
                ('iframe[src*="ashby"]', 'Ashby iframe'),
                ('iframe[src*="workday"]', 'Workday iframe'),
                ('iframe[src*="bamboo"]', 'BambooHR iframe'),
            ]

            found_elements = []
            for selector, desc in selectors_to_try:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"\n✅ {desc}: 找到 {len(elements)} 个元素")
                        found_elements.append((selector, desc, len(elements)))

                        # 显示前3个元素的信息
                        for i, elem in enumerate(elements[:3]):
                            text = elem.inner_text()[:80].replace('\n', ' ')
                            href = elem.get_attribute('href') or ''
                            print(f"   [{i+1}] text: '{text}...'")
                            if href:
                                print(f"       href: {href}")
                except:
                    pass

            # 输出HTML片段用于分析
            print("\n" + "="*40)
            print("页面HTML片段 (body前2000字符)...")
            print("="*40)

            body_html = page.inner_html('body')[:3000]
            print(body_html)

            # 查找所有链接并过滤职位相关的
            print("\n" + "="*40)
            print("所有可能的职位链接...")
            print("="*40)

            all_links = page.query_selector_all('a[href]')
            job_keywords = ['job', 'career', 'position', 'opening', 'apply', 'hire', 'work']

            job_links = []
            for link in all_links:
                href = link.get_attribute('href') or ''
                text = link.inner_text().strip()[:50]

                # 检查href或text是否包含职位关键词
                href_lower = href.lower()
                text_lower = text.lower()

                if any(kw in href_lower or kw in text_lower for kw in job_keywords):
                    if text and len(text) > 3:  # 过滤太短的文本
                        job_links.append((href, text))

            # 去重并显示
            seen = set()
            for href, text in job_links:
                key = (href, text)
                if key not in seen:
                    seen.add(key)
                    print(f"  - [{text}] -> {href}")

            browser.close()

            return found_elements

        except Exception as e:
            print(f"❌ 错误: {e}")
            browser.close()
            return []


if __name__ == '__main__':
    # 分析 Helcim
    print("\n" + "#"*60)
    print("# HELCIM 页面分析")
    print("#"*60)
    analyze_page('https://www.helcim.com/careers/job-openings/', 'Helcim')

    print("\n\n")

    # 分析 Jobber
    print("\n" + "#"*60)
    print("# JOBBER 页面分析")
    print("#"*60)
    analyze_page('https://www.getjobber.com/about/careers/', 'Jobber')
