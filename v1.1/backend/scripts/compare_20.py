# -*- coding: utf-8 -*-
"""
对比新老爬虫数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from models.review import Review
from crawler.taptap_crawler_scrapling import TapTapCrawler
import pandas as pd

print('=' * 60)
print('新老爬虫数据对比')
print('=' * 60)

# 1. 获取数据库中的老数据
db = next(get_db())
old_reviews = db.query(Review).limit(100).all()

print(f'\n数据库中老爬虫数据: {len(old_reviews)} 条')

# 2. 用新爬虫爬取数据
print('\n新爬虫爬取数据...')
crawler = TapTapCrawler(headless=True)
new_reviews = crawler.get_reviews(258720, max_reviews=100)
crawler.close()

print(f'新爬虫获取到 {len(new_reviews)} 条评价')

# 3. 匹配相同用户名的评价
print('\n匹配相同用户名的评价...')

comparison_data = []
matched_count = 0

for old in old_reviews:
    for new in new_reviews:
        if old.user_name == new['user_name']:
            matched_count += 1
            
            comparison_data.append({
                '序号': matched_count,
                '用户名': old.user_name,
                
                '老爬虫-内容长度': len(old.content or ''),
                '新爬虫-内容长度': len(new.get('content', '')),
                '内容长度差异': len(new.get('content', '')) - len(old.content or ''),
                '内容一致': '✓' if old.content == new.get('content', '') else '✗',
                
                '老爬虫-星级': old.rating,
                '新爬虫-星级': new.get('rating', 0),
                '星级一致': '✓' if old.rating == new.get('rating', 0) else '✗',
                
                '老爬虫-日期': str(old.review_date) if old.review_date else '',
                '新爬虫-日期': new.get('review_date', ''),
                '日期一致': '✓' if str(old.review_date) == new.get('review_date', '') else '✗',
                
                '情感分析': old.sentiment or '未分析',
                '问题分类': old.problem_category or '未分类',
                '一句话总结': old.summary or '无',
                
                '老爬虫-内容': (old.content or '')[:100] + '...' if len(old.content or '') > 100 else (old.content or ''),
                '新爬虫-内容': new.get('content', '')[:100] + '...' if len(new.get('content', '')) > 100 else new.get('content', ''),
            })
            
            if matched_count >= 20:
                break
    
    if matched_count >= 20:
        break

print(f'\n匹配到 {matched_count} 条相同用户名的评价')

# 4. 保存到Excel
if comparison_data:
    df = pd.DataFrame(comparison_data)
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'output', '新老爬虫数据对比_20条.xlsx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='详细对比')
    
    print(f'\n对比文件已保存: {output_path}')
    
    # 5. 打印统计
    print('\n' + '=' * 60)
    print('匹配统计')
    print('=' * 60)
    
    total = len(comparison_data)
    content_match = sum(1 for d in comparison_data if d['内容一致'] == '✓')
    rating_match = sum(1 for d in comparison_data if d['星级一致'] == '✓')
    date_match = sum(1 for d in comparison_data if d['日期一致'] == '✓')
    
    print(f'内容一致: {content_match}/{total} ({content_match/total*100:.1f}%)')
    print(f'星级一致: {rating_match}/{total} ({rating_match/total*100:.1f}%)')
    print(f'日期一致: {date_match}/{total} ({date_match/total*100:.1f}%)')
