# -*- coding: utf-8 -*-
"""
调试特定用户的日期解析
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_specific_users():
    target_users = ['花卷云舒', '不屈的钦王', '店长', '友利奈绪']
    
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
        
        for i, elem in enumerate(review_elements[:30]):
            try:
                # 查找用户名
                user_elem = await elem.query_selector('.user-name')
                if user_elem:
                    user_name = await user_elem.text_content()
                    user_name = user_name.strip()
                    
                    if user_name in target_users:
                        print(f"\n{'='*50}")
                        print(f"找到目标用户: {user_name}")
                        
                        # 查找日期元素
                        time_elem = await elem.query_selector('.tap-time')
                        if time_elem:
                            title = await time_elem.get_attribute('title')
                            text = await time_elem.text_content()
                            html = await time_elem.evaluate('el => el.outerHTML')
                            print(f"  title属性: {title}")
                            print(f"  文本内容: {text}")
                            print(f"  HTML: {html[:300]}")
                        else:
                            print("  未找到 .tap-time 元素")
            except Exception as e:
                print(f"处理第{i+1}个评价时出错: {e}")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_specific_users())
