# -*- coding: utf-8 -*-
"""
完整对比25条同一条评论的所有字段
使用GLM分析模块，与老项目保持一致
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from models.database import get_db
from models.review import Review
from crawler.taptap_crawler_scrapling import TapTapCrawler
from nlp import analyze_reviews_batch_glm

print('=' * 60)
print('完整对比25条同一条评论的所有字段（使用GLM分析）')
print('=' * 60)

db = next(get_db())
old_reviews = db.query(Review).limit(50).all()
print(f'\n数据库中老爬虫数据: {len(old_reviews)} 条')

print('\n新爬虫爬取数据...')
crawler = TapTapCrawler(headless=True)
new_reviews = crawler.get_reviews(258720, max_reviews=200)
crawler.close()
print(f'新爬虫获取到 {len(new_reviews)} 条评价')

print('\n使用GLM分析新爬虫数据（降级方案：关键词匹配）...')
new_reviews_analyzed = analyze_reviews_batch_glm(new_reviews, use_glm=False)

print('\n匹配相同用户名的评价...')

comparison_data = []
matched_count = 0

for old in old_reviews:
    for new in new_reviews_analyzed:
        if old.user_name == new['user_name']:
            matched_count += 1
            
            old_categories = [c.strip() for c in (old.problem_category or '').split(',') if c.strip()]
            old_issues = []
            for cat in old_categories:
                if '-' in cat:
                    parts = cat.split('-')
                    old_issues.append({
                        'primary': parts[0].strip(),
                        'secondary': parts[1].strip() if len(parts) > 1 else ''
                    })
            
            new_issues = new.get('issues', [])
            new_issues_parsed = []
            for issue in new_issues:
                if '-' in issue:
                    parts = issue.split('-')
                    new_issues_parsed.append({
                        'primary': parts[0].strip(),
                        'secondary': parts[1].strip() if len(parts) > 1 else ''
                    })
            
            old_category_1 = old_issues[0]['primary'] if len(old_issues) > 0 else ''
            old_category_2 = old_issues[0]['secondary'] if len(old_issues) > 0 else ''
            old_category_3 = old_issues[1]['secondary'] if len(old_issues) > 1 else ''
            
            new_category_1 = new_issues_parsed[0]['primary'] if len(new_issues_parsed) > 0 else ''
            new_category_2 = new_issues_parsed[0]['secondary'] if len(new_issues_parsed) > 0 else ''
            new_category_3 = new_issues_parsed[1]['secondary'] if len(new_issues_parsed) > 1 else ''
            
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
                
                '老爬虫-情感': old.sentiment or '未分析',
                '新爬虫-情感': new.get('sentiment', '中性'),
                '情感一致': '✓' if old.sentiment == new.get('sentiment') else '✗',
                
                '老爬虫-问题分类': old.problem_category or '无',
                '新爬虫-问题分类': ', '.join(new.get('issues', [])) if new.get('issues') else '无',
                '分类一致': '✓' if old.problem_category == ', '.join(new.get('issues', [])) else '✗',
                
                '老爬虫-分类大类': old_category_1,
                '新爬虫-分类大类': new_category_1,
                '分类大类一致': '✓' if old_category_1 == new_category_1 else '✗',
                
                '老爬虫-分类子类': old_category_2,
                '新爬虫-分类子类': new_category_2,
                '分类子类一致': '✓' if old_category_2 == new_category_2 else '✗',
                
                '老爬虫-一句话总结': old.summary or '无',
                '新爬虫-一句话总结': new.get('summary', '无'),
                '总结一致': '✓' if old.summary == new.get('summary') else '✗',
            })
            
            if matched_count >= 25:
                break
    
    if matched_count >= 25:
        break

print(f'\n匹配到 {matched_count} 条相同用户名的评价')

if comparison_data:
    df = pd.DataFrame(comparison_data)
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', '新老爬虫完整对比_25条_GLM.xlsx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='完整对比')
        
        worksheet = writer.sheets['完整对比']
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
    
    print('\n' + '=' * 60)
    print('匹配统计')
    print('=' * 60)
    
    total = len(comparison_data)
    print(f'内容一致: {sum(1 for d in comparison_data if d["内容一致"] == "✓")}/{total}')
    print(f'星级一致: {sum(1 for d in comparison_data if d["星级一致"] == "✓")}/{total}')
    print(f'日期一致: {sum(1 for d in comparison_data if d["日期一致"] == "✓")}/{total}')
    print(f'情感一致: {sum(1 for d in comparison_data if d["情感一致"] == "✓")}/{total}')
    print(f'分类大类一致: {sum(1 for d in comparison_data if d["分类大类一致"] == "✓")}/{total}')
    print(f'分类子类一致: {sum(1 for d in comparison_data if d["分类子类一致"] == "✓")}/{total}')
    print(f'一句话总结一致: {sum(1 for d in comparison_data if d["总结一致"] == "✓")}/{total}')
