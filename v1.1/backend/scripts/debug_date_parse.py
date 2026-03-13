# -*- coding: utf-8 -*-
"""
调试日期解析问题
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_date():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.taptap.cn/app/258720/review"
        print(f"访问: {url}")
        
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 查找日期元素
        print("\n查找 .tap-time 元素...")
        time_elems = await page.query_selector_all('.tap-time')
        print(f"找到 {len(time_elems)} 个 .tap-time 元素")
        
        for i, elem in enumerate(time_elems[:10]):
            try:
                text = await elem.text_content()
                title = await elem.get_attribute('title')
                outer_html = await elem.evaluate('el => el.outerHTML')
                print(f"\n[{i+1}] 文本: {text}")
                print(f"    title: {title}")
                print(f"    HTML: {outer_html[:200]}")
            except Exception as e:
                print(f"[{i+1}] 错误: {e}")
        
        # 查找其他可能的日期选择器
        print("\n\n查找其他日期选择器...")
        other_selectors = [
            '.review-item__updated-time',
            '[class*="time"]',
            '[class*="date"]',
        ]
        
        for selector in other_selectors:
            elems = await page.query_selector_all(selector)
            if elems:
                print(f"\n{selector}: 找到 {len(elems)} 个")
                for i, elem in enumerate(elems[:3]):
                    try:
                        text = await elem.text_content()
                        title = await elem.get_attribute('title')
                        print(f"  [{i+1}] 文本: {text}, title: {title}")
                    except:
                        pass
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_date())
