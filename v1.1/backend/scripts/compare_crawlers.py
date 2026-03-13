# -*- coding: utf-8 -*-
"""
同一条评价新旧爬虫解析逻辑对比

对比方式：
1. 从数据库获取老爬虫爬取的评价
2. 用新爬虫重新访问页面，找到相同的评价
3. 对比同一条评价在两种逻辑下的解析结果
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from models.database import get_db
from models.review import Review
from scrapling.fetchers import StealthyFetcher
import re
from datetime import datetime

print('=' * 60)
print('同一条评价新旧爬虫解析逻辑对比')
print('=' * 60)

# 1. 获取数据库中的老数据
db = next(get_db())
old_reviews = db.query(Review).limit(10).all()
print(f'\n数据库中老爬虫数据: {len(old_reviews)} 条')

# 2. 用新爬虫逻辑重新解析页面
print('\n用新爬虫逻辑重新解析页面...')
page = StealthyFetcher.fetch('https://www.taptap.cn/app/258720/review', headless=True, wait=5000)

# 3. 解析页面评价（新爬虫逻辑）
review_items = page.css('.review-item')
print(f'页面找到 {len(review_items)} 条评价')

new_parsed = []
for elem in review_items:
    # 新爬虫解析逻辑
    user_name_elem = elem.css('.user-name__text')
    user_name = user_name_elem[0].text.strip() if user_name_elem and user_name_elem[0].text else '匿名用户'
    
    content_elem = elem.css('.collapse-text-emoji__content span, .review-text, .content, .item-text')
    content = content_elem[0].text.strip() if content_elem and content_elem[0].text else ''
    
    # 星级
    rating = 5
    highlight = elem.css('.review-rate__highlight')
    if highlight:
        style = highlight[0].attrib.get('style', '')
        match = re.search(r'width:\s*(\d+)px', style)
        if match:
            width = int(match.group(1))
            rating = max(1, min(5, round(width / 18)))
    
    # 日期
    review_date = datetime.now().strftime('%Y-%m-%d')
    time_elem = elem.css('.tap-time')
    if time_elem:
        title = time_elem[0].attrib.get('title', '')
        if title:
            match = re.match(r'(\d{4})/(\d{2})/(\d{2})', title)
            if match:
                review_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    
    new_parsed.append({
        'user_name': user_name,
        'content': content,
        'rating': rating,
        'review_date': review_date
    })

# 4. 匹配相同评价（通过内容匹配）
comparison_data = []
for old in old_reviews:
    # 在新解析的数据中找到匹配的评价
    matched_new = None
    for new in new_parsed:
        # 通过内容前50字匹配
        if old.content and new['content']:
            if old.content[:50] in new['content'] or new['content'][:50] in old.content:
                matched_new = new
                break
    
    if matched_new:
        comparison_data.append({
            '序号': len(comparison_data) + 1,
            
            # 用户名对比
            '老爬虫-用户名': old.user_name,
            '新爬虫-用户名': matched_new['user_name'],
            '用户名一致': '✓' if old.user_name == matched_new['user_name'] else '✗',
            
            # 星级对比
            '老爬虫-星级': old.rating,
            '新爬虫-星级': matched_new['rating'],
            '星级一致': '✓' if old.rating == matched_new['rating'] else '✗',
            
            # 日期对比
            '老爬虫-日期': str(old.review_date) if old.review_date else '',
            '新爬虫-日期': matched_new['review_date'],
            '日期一致': '✓' if str(old.review_date) == matched_new['review_date'] else '✗',
            
            # 内容对比
            '老爬虫-内容(前100字)': old.content[:100] + '...' if old.content and len(old.content) > 100 else old.content,
            '新爬虫-内容(前100字)': matched_new['content'][:100] + '...' if len(matched_new['content']) > 100 else matched_new['content'],
            '内容长度': f"老:{len(old.content or '')}字 vs 新:{len(matched_new['content'])}字",
            
            # NLP分析结果（来自老数据）
            '情感': old.sentiment or '未分析',
            '问题分类': old.problem_category or '未分类',
            '一句话总结': old.summary or '无',
        })

# 5. 如果没有匹配到，直接对比前N条
if not comparison_data:
    print('\n未找到匹配的评价，直接对比前N条...')
    for i in range(min(len(old_reviews), len(new_parsed))):
        old = old_reviews[i]
        new = new_parsed[i]
        
        comparison_data.append({
            '序号': i + 1,
            
            # 用户名对比
            '老爬虫-用户名': old.user_name,
            '新爬虫-用户名': new['user_name'],
            '用户名一致': '✓' if old.user_name == new['user_name'] else '✗',
            
            # 星级对比
            '老爬虫-星级': old.rating,
            '新爬虫-星级': new['rating'],
            '星级一致': '✓' if old.rating == new['rating'] else '✗',
            
            # 日期对比
            '老爬虫-日期': str(old.review_date) if old.review_date else '',
            '新爬虫-日期': new['review_date'],
            '日期一致': '✓' if str(old.review_date) == new['review_date'] else '✗',
            
            # 内容对比
            '老爬虫-内容(前100字)': old.content[:100] + '...' if old.content and len(old.content) > 100 else old.content,
            '新爬虫-内容(前100字)': new['content'][:100] + '...' if len(new['content']) > 100 else new['content'],
            '内容长度': f"老:{len(old.content or '')}字 vs 新:{len(new['content'])}字",
            
            # NLP分析结果（来自老数据）
            '情感': old.sentiment or '未分析',
            '问题分类': old.problem_category or '未分类',
            '一句话总结': old.summary or '无',
        })

# 6. 保存到Excel
df = pd.DataFrame(comparison_data)
output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'output', '新旧爬虫数据对比.xlsx')
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='数据对比')
    
    # 调整列宽
    worksheet = writer.sheets['数据对比']
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        worksheet.column_dimensions[column_letter].width = adjusted_width

print(f'\n对比文件已保存: {output_path}')

# 7. 打印统计
if comparison_data:
    total = len(comparison_data)
    user_match = sum(1 for d in comparison_data if d['用户名一致'] == '✓')
    rating_match = sum(1 for d in comparison_data if d['星级一致'] == '✓')
    date_match = sum(1 for d in comparison_data if d['日期一致'] == '✓')
    
    print(f'\n匹配统计:')
    print(f'  用户名匹配: {user_match}/{total} ({user_match/total*100:.1f}%)')
    print(f'  星级匹配: {rating_match}/{total} ({rating_match/total*100:.1f}%)')
    print(f'  日期匹配: {date_match}/{total} ({date_match/total*100:.1f}%)')
