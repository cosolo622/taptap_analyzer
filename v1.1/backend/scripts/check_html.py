# -*- coding: utf-8 -*-
"""
检查 HTML 内容，找出为什么内容被截断
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapling.fetchers import PlayWrightFetcher
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
print('分析 HTML 结构')
print('=' * 60)

page = PlayWrightFetcher.fetch(
    'https://www.taptap.cn/app/258720/review', 
    headless=True, 
    wait=5000,
    network_idle=True
)

# 点击展开按钮
playwright_page = page.page if hasattr(page, 'page') else None
if playwright_page:
    playwright_page.evaluate('''
        document.querySelectorAll('.collapse-text-emoji__btn, [class*="expand"], [class*="more"]').forEach(btn => {
            try { btn.click(); } catch(e) {}
        });
    ''')
    import time
    time.sleep(1)

review_items = page.css('.review-item')

# 找到 azeo34 的评价
for i, item in enumerate(review_items):
    user_elem = item.css('.user-name__text')
    if user_elem and user_elem[0].text and 'azeo34' in user_elem[0].text:
        print(f'\n找到 azeo34 的评价（第{i+1}条）')
        
        # 检查 HTML 内容
        content_elem = item.css('.collapse-text-emoji__content')
        if content_elem:
            html = content_elem[0].html if hasattr(content_elem[0], 'html') else ''
            print(f'\nHTML 长度: {len(html)} 字符')
            print(f'HTML 内容:\n{html[:1000]}...')
            
            # 检查是否有多个 span
            spans = content_elem[0].css('span')
            print(f'\n找到 {len(spans)} 个 span 元素')
            for j, span in enumerate(spans[:5]):
                print(f'span[{j}]: {span.text[:100] if span.text else "None"}...')
        
        # 检查整个评价元素的 HTML
        print(f'\n整个评价元素的 HTML 长度: {len(item.html) if hasattr(item, "html") else "N/A"}')
        
        break
