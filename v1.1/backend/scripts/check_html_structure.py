# -*- coding: utf-8 -*-
"""
检查评价元素的完整HTML结构
"""
import asyncio
from playwright.async_api import async_playwright

async def check_html_structure():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.taptap.cn/app/258720/review"
        print(f"访问: {url}")
        
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 滚动加载更多
        for _ in range(2):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)
        
        # 查找评价元素
        review_elements = await page.query_selector_all('.review-item')
        print(f"找到 {len(review_elements)} 个评价元素")
        
        for i, elem in enumerate(review_elements[:5]):
            print(f"\n{'='*60}")
            print(f"评价 [{i+1}]")
            
            # 获取用户名
            user_elem = await elem.query_selector('.user-name')
            if user_elem:
                user_name = await user_elem.text_content()
                print(f"用户名: {user_name.strip()}")
            
            # 查找所有可能包含时间的元素
            print("\n查找日期相关元素:")
            
            # 1. .tap-time
            tap_time = await elem.query_selector('.tap-time')
            if tap_time:
                title = await tap_time.get_attribute('title')
                text = await tap_time.text_content()
                print(f"  .tap-time: title={title}, text={text}")
            else:
                print("  .tap-time: 未找到")
            
            # 2. .review-item__updated-time
            updated_time = await elem.query_selector('.review-item__updated-time')
            if updated_time:
                title = await updated_time.get_attribute('title')
                text = await updated_time.text_content()
                print(f"  .review-item__updated-time: title={title}, text={text}")
            else:
                print("  .review-item__updated-time: 未找到")
            
            # 3. 查找所有包含 time 的类名
            time_elements = await elem.query_selector_all('[class*="time"]')
            if time_elements:
                print(f"  找到 {len(time_elements)} 个包含'time'的元素:")
                for j, te in enumerate(time_elements[:3]):
                    cls = await te.get_attribute('class')
                    text = await te.text_content()
                    title = await te.get_attribute('title')
                    print(f"    [{j+1}] class={cls}, text={text}, title={title}")
            
            # 4. 查找 header 区域
            header = await elem.query_selector('.review-item__header, .header')
            if header:
                header_html = await header.evaluate('el => el.innerHTML')
                print(f"\n  header区域HTML片段: {header_html[:500]}")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(check_html_structure())
