"""分析Helcim职位页面"""
from playwright.sync_api import sync_playwright


def analyze_helcim():
    """分析Helcim页面"""
    url = 'https://www.helcim.com/careers/job-openings/'

    print(f"分析 Helcim: {url}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        try:
            print("正在加载页面...")
            page.goto(url, timeout=60000)

            # 等待更长时间
            print("等待页面渲染...")
            page.wait_for_timeout(5000)

            # 获取页面标题
            title = page.title()
            print(f"页面标题: {title}\n")

            # 获取页面HTML
            html = page.content()
            print(f"HTML长度: {len(html)} 字符\n")

            # 查找iframe
            iframes = page.query_selector_all('iframe')
            print(f"找到 {len(iframes)} 个iframe")

            for i, iframe in enumerate(iframes):
                src = iframe.get_attribute('src') or ''
                print(f"  iframe[{i}]: {src[:100]}...")

            # 常见的ATS平台关键词
            ats_keywords = ['greenhouse', 'lever', 'ashby', 'workday', 'bamboo', 'jazz', 'resumator', 'workable', 'breezy']
            html_lower = html.lower()

            print("\n检查ATS平台:")
            for kw in ats_keywords:
                if kw in html_lower:
                    print(f"  ✅ 发现 {kw}")

            # 查找所有链接
            print("\n职位相关链接:")
            all_links = page.query_selector_all('a[href]')

            job_links = []
            for link in all_links:
                href = link.get_attribute('href') or ''
                text = link.inner_text().strip()[:60]

                # 职位关键词
                keywords = ['job', 'career', 'position', 'apply', 'opening', 'developer', 'engineer', 'manager', 'analyst']
                href_lower = href.lower()
                text_lower = text.lower()

                if any(kw in href_lower or kw in text_lower for kw in keywords):
                    if text and len(text) > 5:
                        job_links.append((href, text))
                        print(f"  [{text}] -> {href}")

            # 保存HTML用于分析
            with open('/tmp/helcim_page.html', 'w') as f:
                f.write(html)
            print(f"\n完整HTML已保存到 /tmp/helcim_page.html")

            browser.close()

        except Exception as e:
            print(f"错误: {e}")

            # 即使出错也保存当前HTML
            try:
                html = page.content()
                with open('/tmp/helcim_page.html', 'w') as f:
                    f.write(html)
                print(f"部分HTML已保存")
            except:
                pass

            browser.close()


if __name__ == '__main__':
    analyze_helcim()
