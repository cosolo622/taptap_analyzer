# -*- coding: utf-8 -*-
"""
检查用户名选择器
"""
from scrapling.fetchers import StealthyFetcher

page = StealthyFetcher.fetch('https://www.taptap.cn/app/258720/review', headless=True, wait=5000)

review_items = page.css('.review-item')
print(f'.review-item 数量: {len(review_items)}')

for i, elem in enumerate(review_items[:3]):
    print(f'\n=== 评价 {i+1} ===')
    
    # 检查各种用户名选择器
    selectors = [
        '.user-name__text',
        '.review-item__author-name',
        '.user-name',
    ]
    
    for sel in selectors:
        found = elem.css(sel)
        if found:
            print(f'{sel}: 数量={len(found)}')
            for j, f in enumerate(found[:2]):
                text = f.text
                print(f'  [{j}] text={repr(text)}')
                # 检查子元素
                children = f.css('*')
                if children:
                    for k, child in enumerate(children[:3]):
                        child_text = child.text
                        if child_text:
                            print(f'    child[{k}] text={repr(child_text)}')
        else:
            print(f'{sel}: 未找到')
