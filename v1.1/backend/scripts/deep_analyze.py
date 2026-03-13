# -*- coding: utf-8 -*-
"""
深入分析页面结构，找到获取完整内容的方法
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapling.fetchers import StealthyFetcher
from models.database import get_db
from models.review import Review

# 获取老爬虫数据
db = next(get_db())
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
        
        # 获取所有文本内容
        print('\n该评价元素的所有文本内容:')
        all_text = item.text
        print(f'总文本长度: {len(all_text)} 字')
        print(f'内容: {all_text[:500]}...')
        
        # 尝试获取完整内容
        print('\n尝试各种选择器:')
        
        # 1. collapse-text-emoji__content span
        content1 = item.css('.collapse-text-emoji__content span')
        if content1:
            print(f'.collapse-text-emoji__content span: {len(content1[0].text or "")} 字')
        
        # 2. 直接获取 collapse-text-emoji__content 的所有子元素文本
        content2 = item.css('.collapse-text-emoji__content')
        if content2:
            # 获取所有子元素的文本
            all_span_text = ' '.join([span.text for span in content2[0].css('span') if span.text])
            print(f'所有 span 文本合并: {len(all_span_text)} 字')
            print(f'内容: {all_span_text[:200]}...')
        
        # 3. 检查是否有展开按钮
        expand_btn = item.css('[class*="expand"], [class*="more"], .collapse-text-emoji__btn')
        if expand_btn:
            print(f'\n找到展开按钮: {expand_btn[0].attrib.get("class")}')
        
        break
