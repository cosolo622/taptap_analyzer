# -*- coding: utf-8 -*-
"""
验证老爬虫选择器在当前页面的效果
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
    
    print('\n测试老爬虫的内容选择器:')
    selectors = [
        '.review-text',
        '.content',
        '[class*="content"]',
        '.item-text'
    ]
    
    for sel in selectors:
        elems = first.css(sel)
        if elems:
            for j in range(min(2, len(elems))):
                text = elems[j].text
                if text:
                    print(f'{sel}[{j}]: {len(text)} 字')
                    print(f'  内容: {text[:100]}...')
                else:
                    print(f'{sel}[{j}]: None')
        else:
            print(f'{sel}: 未找到')
    
    print('\n测试新爬虫的内容选择器:')
    new_selectors = [
        '.collapse-text-emoji__content span',
        '.collapse-text-emoji__content',
        '.review-item__contents',
    ]
    
    for sel in new_selectors:
        elems = first.css(sel)
        if elems:
            for j in range(min(2, len(elems))):
                text = elems[j].text
                if text:
                    print(f'{sel}[{j}]: {len(text)} 字')
                    print(f'  内容: {text[:100]}...')
                else:
                    print(f'{sel}[{j}]: None')
        else:
            print(f'{sel}: 未找到')
