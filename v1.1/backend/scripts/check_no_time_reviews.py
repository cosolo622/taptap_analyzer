# -*- coding: utf-8 -*-
"""
检查没有.tap-time的评价的完整HTML
"""
import asyncio
from playwright.async_api import async_playwright

async def check_no_time_reviews():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.taptap.cn/app/258720/review"
        print(f"访问: {url}")
        
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 滚动加载更多
        for _ in range(3):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)
        
        # 查找评价元素
        review_elements = await page.query_selector_all('.review-item')
        print(f"找到 {len(review_elements)} 个评价元素")
        
        no_time_count = 0
        for i, elem in enumerate(review_elements):
            try:
                # 检查是否有 .tap-time
                tap_time = await elem.query_selector('.tap-time')
                
                if not tap_time:
                    no_time_count += 1
                    if no_time_count <= 3:
                        print(f"\n{'='*60}")
                        print(f"评价 [{i+1}] - 没有 .tap-time")
                        
                        # 获取用户名
                        user_elem = await elem.query_selector('.user-name')
                        if user_elem:
                            user_name = await user_elem.text_content()
                            print(f"用户名: {user_name.strip()}")
                        
                        # 获取整个评价的HTML
                        html = await elem.evaluate('el => el.outerHTML')
                        
                        # 查找任何包含日期的元素
                        date_patterns = [
                            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
                            r'\d{1,2}月\d{1,2}日',
                            r'\d+天前',
                            r'\d+小时前',
                            r'昨天',
                            r'前天'
                        ]
                        
                        import re
                        for pattern in date_patterns:
                            matches = re.findall(pattern, html)
                            if matches:
                                print(f"找到日期模式 '{pattern}': {matches[:3]}")
                        
                        # 打印部分HTML
                        print(f"\nHTML片段 (前1000字符):")
                        print(html[:1000])
                        
            except Exception as e:
                print(f"处理第{i+1}个评价时出错: {e}")
        
        print(f"\n总计: {no_time_count} 个评价没有 .tap-time 元素")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(check_no_time_reviews())
