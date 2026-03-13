# -*- coding: utf-8 -*-
"""
检查日期在HTML中的具体位置
"""
import asyncio
from playwright.async_api import async_playwright

async def check_date_location():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.taptap.cn/app/258720/review"
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 滚动加载更多
        for _ in range(3):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)
        
        review_elements = await page.query_selector_all('.review-item')
        
        for i, elem in enumerate(review_elements[:5]):
            tap_time = await elem.query_selector('.tap-time')
            user_elem = await elem.query_selector('.user-name')
            user_name = (await user_elem.text_content()).strip() if user_elem else '未知'
            
            print(f"\n[{i+1}] {user_name}")
            print(f"  有.tap-time: {tap_time is not None}")
            
            if not tap_time:
                # 获取完整HTML
                html = await elem.evaluate('el => el.outerHTML')
                
                # 查找日期在哪个元素中
                import re
                date_match = re.search(r'(\d{4}/\d{1,2}/\d{1,2})', html)
                if date_match:
                    date_str = date_match.group(1)
                    # 找到日期前后100个字符
                    start = max(0, date_match.start() - 100)
                    end = min(len(html), date_match.end() + 100)
                    context = html[start:end]
                    print(f"  日期: {date_str}")
                    print(f"  上下文: ...{context}...")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(check_date_location())
