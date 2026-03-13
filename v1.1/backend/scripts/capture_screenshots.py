# -*- coding: utf-8 -*-
"""
截图验证前端页面状态
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def capture_screenshots():
    """捕获前端页面截图"""
    
    # 截图保存目录
    screenshot_dir = r'c:\Users\Administrator\Documents\trae_projects\99multi\taptap_analyzer\v1.1\output\screenshots'
    os.makedirs(screenshot_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        print('=' * 60)
        print('开始截图验证')
        print('=' * 60)
        
        # 1. 截图首页 - 实时舆情数据
        print('\n[1/4] 截图首页 - 实时舆情数据...')
        try:
            await page.goto('http://localhost:3000/', wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)  # 等待数据加载
            await page.screenshot(path=os.path.join(screenshot_dir, '01_homepage.png'), full_page=True)
            print('  ✓ 首页截图完成')
        except Exception as e:
            print(f'  ✗ 首页截图失败: {e}')
        
        # 2. 截图数据更新页面
        print('\n[2/4] 截图数据更新页面...')
        try:
            # 点击数据更新菜单
            await page.click('text=数据更新')
            await page.wait_for_timeout(2000)
            await page.screenshot(path=os.path.join(screenshot_dir, '02_dataupdate.png'), full_page=True)
            print('  ✓ 数据更新页面截图完成')
        except Exception as e:
            print(f'  ✗ 数据更新页面截图失败: {e}')
        
        # 3. 截图评价明细页面
        print('\n[3/4] 截图评价明细页面...')
        try:
            await page.click('text=评价明细')
            await page.wait_for_timeout(2000)
            await page.screenshot(path=os.path.join(screenshot_dir, '03_reviews.png'), full_page=True)
            print('  ✓ 评价明细页面截图完成')
        except Exception as e:
            print(f'  ✗ 评价明细页面截图失败: {e}')
        
        # 4. 截图负面舆情监控页面
        print('\n[4/4] 截图负面舆情监控页面...')
        try:
            await page.click('text=负面舆情监控')
            await page.wait_for_timeout(2000)
            await page.screenshot(path=os.path.join(screenshot_dir, '04_negative.png'), full_page=True)
            print('  ✓ 负面舆情监控页面截图完成')
        except Exception as e:
            print(f'  ✗ 负面舆情监控页面截图失败: {e}')
        
        await browser.close()
        
        print('\n' + '=' * 60)
        print(f'截图完成，保存位置: {screenshot_dir}')
        print('=' * 60)

if __name__ == '__main__':
    asyncio.run(capture_screenshots())
