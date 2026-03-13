# -*- coding: utf-8 -*-
"""
分析新老爬虫数据差异，找出不一致的原因
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from models.review import Review
from scrapling.fetchers import StealthyFetcher
import re

db = next(get_db())

print('=' * 60)
print('分析新老爬虫数据差异')
print('=' * 60)

# 1. 获取数据库中的老数据（老爬虫爬取的）
old_reviews = db.query(Review).limit(5).all()
print(f'\n数据库中老爬虫数据（前5条）:')
for i, r in enumerate(old_reviews, 1):
    print(f'\n[{i}] {r.user_name} - {r.rating}星 - {r.review_date}')
    print(f'    内容长度: {len(r.content or "")} 字')
    print(f'    内容: {r.content[:150] if r.content else "N/A"}...')

# 2. 用新爬虫获取页面
print('\n' + '=' * 60)
print('新爬虫解析同一页面')
print('=' * 60)

page = StealthyFetcher.fetch('https://www.taptap.cn/app/258720/review', headless=True, wait=5000)
review_items = page.css('.review-item')
print(f'\n页面找到 {len(review_items)} 条评价')

# 3. 详细对比第一条评价
print('\n' + '=' * 60)
print('详细对比第一条评价')
print('=' * 60)

old_first = old_reviews[0]
new_first = review_items[0]

print(f'\n老爬虫第一条:')
print(f'  用户名: {old_first.user_name}')
print(f'  内容: {old_first.content[:200] if old_first.content else "N/A"}...')

print(f'\n新爬虫第一条（原始HTML结构）:')
# 获取所有可能的文本内容
all_texts = []
for elem in new_first.css('*'):
    text = elem.text
    if text and len(text.strip()) > 10:
        all_texts.append((elem.attrib.get('class', ''), text.strip()[:100]))

print(f'  找到 {len(all_texts)} 个文本节点')
for cls, txt in all_texts[:10]:
    print(f'    [{cls[:40]}]: {txt}...')

# 4. 检查老爬虫的选择器在当前页面是否有效
print('\n' + '=' * 60)
print('检查老爬虫选择器在当前页面的效果')
print('=' * 60)

old_selectors = [
    '.review-text',
    '.content',
    '[class*="content"]',
    '.item-text'
]

for sel in old_selectors:
    elems = new_first.css(sel)
    if elems:
        for j, e in enumerate(elems[:2]):
            text = e.text
            print(f'{sel}[{j}]: {len(text) if text else 0} 字 - {text[:80] if text else "N/A"}...')
    else:
        print(f'{sel}: 未找到')

# 5. 检查新爬虫的选择器
print('\n' + '=' * 60)
print('检查新爬虫选择器')
print('=' * 60)

new_selectors = [
    '.collapse-text-emoji__content span',
    '.collapse-text-emoji__content',
    '.review-item__contents',
]

for sel in new_selectors:
    elems = new_first.css(sel)
    if elems:
        for j, e in enumerate(elems[:2]):
            text = e.text
            print(f'{sel}[{j}]: {len(text) if text else 0} 字 - {text[:80] if text else "N/A"}...')
    else:
        print(f'{sel}: 未找到')
