# -*- coding: utf-8 -*-
"""
调试评价元素结构
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_review_structure():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.taptap.cn/app/258720/review"
        print(f"访问: {url}")
        
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 查找评价元素
        print("\n查找评价元素...")
        review_elements = await page.query_selector_all('.review-item')
        print(f"找到 {len(review_elements)} 个 .review-item 元素")
        
        if len(review_elements) > 0:
            elem = review_elements[0]
            
            # 查找日期元素
            print("\n在第一个评价元素中查找日期...")
            time_elem = await elem.query_selector('.tap-time')
            if time_elem:
                title = await time_elem.get_attribute('title')
                text = await time_elem.text_content()
                print(f"找到 .tap-time:")
                print(f"  title: {title}")
                print(f"  text: {text}")
            else:
                print("未找到 .tap-time， 尝试其他选择器...")
                
                # 尝试其他选择器
                for selector in ['.review-item__updated-time', '[class*="time"]', 'time']:
                    other_elem = await elem.query_selector(selector)
                    if other_elem:
                        title = await other_elem.get_attribute('title')
                        text = await other_elem.text_content()
                        print(f"找到 {selector}:")
                        print(f"  title: {title}")
                        print(f"  text: {text}")
                        break
            
            # 查找用户名
            user_elem = await elem.query_selector('.user-name')
            if user_elem:
                user_name = await user_elem.text_content()
                print(f"\n用户名: {user_name}")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_review_structure())
