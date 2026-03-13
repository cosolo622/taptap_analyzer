# -*- coding: utf-8 -*-
"""
深入分析：检查页面是否有展开按钮，以及获取完整内容
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from models.review import Review
from scrapling.fetchers import StealthyFetcher
import time

db = next(get_db())

# 获取老爬虫数据
old_review = db.query(Review).filter(Review.user_name == 'azeo34').first()
print('=' * 60)
print('老爬虫数据（用户 azeo34）')
print('=' * 60)
print(f'内容长度: {len(old_review.content or "")} 字')
print(f'完整内容:\n{old_review.content}')
print()

# 获取页面
print('=' * 60)
print('分析页面结构')
print('=' * 60)

page = StealthyFetcher.fetch('https://www.taptap.cn/app/258720/review', headless=True, wait=5000)
review_items = page.css('.review-item')

# 找到 azeo34 的评价
for i, item in enumerate(review_items):
    user_elem = item.css('.user-name__text')
    if user_elem and user_elem[0].text and 'azeo34' in user_elem[0].text:
        print(f'\n找到 azeo34 的评价（第{i+1}条）')
        
        # 尝试各种选择器
        print('\n尝试各种内容选择器:')
        
        selectors = [
            '.collapse-text-emoji__content',
            '.collapse-text-emoji__content span',
            '.review-item__contents',
            '.review-item__content',
            '[class*="collapse-text"]',
            '.heading-m14-w14',
        ]
        
        for sel in selectors:
            elems = item.css(sel)
            if elems:
                for j, e in enumerate(elems[:2]):
                    text = e.text or ''
                    if len(text) > 50:
                        print(f'\n{sel}[{j}]: {len(text)} 字')
                        print(f'内容: {text[:150]}...')
        
        # 获取所有包含长文本的元素
        print('\n\n所有包含长文本的元素:')
        all_elems = item.css('*')
        for elem in all_elems:
            text = elem.text or ''
            if len(text) > 100:
                cls = elem.attrib.get('class', '')
                print(f'\n[{cls[:50]}]: {len(text)} 字')
                print(f'内容: {text[:200]}...')
        
        break
