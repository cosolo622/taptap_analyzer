# -*- coding: utf-8 -*-
"""
调试新老爬虫内容解析差异
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapling.fetchers import StealthyFetcher
from models.database import get_db
from models.review import Review

print('=' * 60)
print('调试新老爬虫内容解析差异')
print('=' * 60)

# 1. 获取数据库中的老数据
db = next(get_db())
old_review = db.query(Review).first()
print(f'\n老爬虫第一条评价:')
print(f'  用户名: {old_review.user_name}')
print(f'  内容长度: {len(old_review.content or "")} 字')
print(f'  内容前200字: {old_review.content[:200] if old_review.content else "N/A"}...')

# 2. 用新爬虫获取页面
print('\n' + '=' * 60)
print('新爬虫解析页面')
print('=' * 60)

page = StealthyFetcher.fetch('https://www.taptap.cn/app/258720/review', headless=True, wait=5000)

# 3. 尝试不同的内容选择器
review_items = page.css('.review-item')
print(f'\n找到 {len(review_items)} 条评价')

if review_items:
    first = review_items[0]
    
    print('\n测试不同的内容选择器:')
    
    # 老爬虫的选择器
    selectors_old = [
        '.review-text',
        '.content', 
        '[class*="content"]',
        '.item-text'
    ]
    
    # 新爬虫的选择器
    selectors_new = [
        '.collapse-text-emoji__content span',
        '.collapse-text-emoji__content',
        '.review-item__contents',
        '.review-item__content'
    ]
    
    print('\n老爬虫选择器:')
    for sel in selectors_old:
        elems = first.css(sel)
        if elems and elems[0].text:
            text = elems[0].text.strip()
            print(f'  {sel}: {len(text)} 字 - {text[:80]}...')
        else:
            print(f'  {sel}: 未找到或为空')
    
    print('\n新爬虫选择器:')
    for sel in selectors_new:
        elems = first.css(sel)
        if elems and elems[0].text:
            text = elems[0].text.strip()
            print(f'  {sel}: {len(text)} 字 - {text[:80]}...')
        else:
            print(f'  {sel}: 未找到或为空')
    
    # 查看元素内部结构
    print('\n第一个评价元素的所有子元素（带文本）:')
    children = first.css('*')
    for i, child in enumerate(children[:30]):
        cls = child.attrib.get('class', '')
        text = (child.text or '').strip()
        if text and len(text) > 10:
            print(f'  [{i}] class="{cls[:50]}"')
            print(f'       text: {text[:100]}...')
