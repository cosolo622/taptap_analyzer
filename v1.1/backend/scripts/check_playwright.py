# -*- coding: utf-8 -*-
"""
使用 Playwright 原生方法获取展开后的完整内容
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from models.review import Review
import asyncio
from playwright.async_api import async_playwright

async def get_full_content():
    # 获取老爬虫数据
    db = next(get_db())
    old_review = db.query(Review).filter(Review.user_name == 'azeo34').first()
    
    print('=' * 60)
    print('老爬虫数据（用户 azeo34）')
    print('=' * 60)
    print(f'内容长度: {len(old_review.content or "")} 字')
    print(f'完整内容:\n{old_review.content}')
    print()
    
    print('=' * 60)
    print('使用 Playwright 获取完整内容')
    print('=' * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto('https://www.taptap.cn/app/258720/review', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 获取所有评价
        review_items = await page.query_selector_all('.review-item')
        print(f'找到 {len(review_items)} 条评价')
        
        for i, item in enumerate(review_items):
            # 获取用户名
            user_elem = await item.query_selector('.user-name__text')
            if user_elem:
                user_name = await user_elem.text_content()
                if 'azeo34' in user_name:
                    print(f'\n找到 azeo34 的评价（第{i+1}条）')
                    
                    # 方法1：直接获取 collapse-text-emoji__content 的文本
                    content_elem = await item.query_selector('.collapse-text-emoji__content')
                    if content_elem:
                        # 点击展开按钮
                        expand_btn = await item.query_selector('.collapse-text-emoji__btn')
                        if expand_btn:
                            print('找到展开按钮，点击...')
                            await expand_btn.click()
                            await page.wait_for_timeout(500)
                        
                        # 获取展开后的内容
                        text1 = await content_elem.text_content()
                        print(f'\n方法1 - text_content(): {len(text1)} 字')
                        print(f'内容: {text1[:200]}...')
                        
                        # 方法2：获取 innerHTML 然后解析
                        html = await content_elem.inner_html()
                        print(f'\n方法2 - innerHTML: {len(html)} 字符')
                        print(f'HTML: {html[:300]}...')
                        
                        # 方法3：获取所有文本节点
                        text2 = await content_elem.evaluate('el => el.innerText')
                        print(f'\n方法3 - innerText: {len(text2)} 字')
                        print(f'内容: {text2[:200]}...')
                        
                        # 方法4：获取所有子元素的文本
                        spans = await content_elem.query_selector_all('span')
                        print(f'\n方法4 - 所有 span: {len(spans)} 个')
                        all_text = []
                        for span in spans:
                            t = await span.text_content()
                            if t:
                                all_text.append(t)
                        combined = ' '.join(all_text)
                        print(f'合并后: {len(combined)} 字')
                        print(f'内容: {combined[:200]}...')
                        
                    break
        
        await browser.close()

asyncio.run(get_full_content())
