# -*- coding: utf-8 -*-
"""
重新分析页面结构，找到正确的内容选择器
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapling.fetchers import StealthyFetcher

page = StealthyFetcher.fetch('https://www.taptap.cn/app/258720/review', headless=True, wait=5000)

review_items = page.css('.review-item')
print(f'找到 {len(review_items)} 条评价')

if review_items:
    first = review_items[0]
    
    print('\n第一个评价的所有子元素（带文本）:')
    children = first.css('*')
    
    for i, child in enumerate(children):
        cls = child.attrib.get('class', '')
        text = (child.text or '').strip()
        if text and len(text) > 20:
            print(f'[{i}] class="{cls[:60]}"')
            print(f'    text: {text[:150]}...')
            print()
