# -*- coding: utf-8 -*-
"""
完整对比25条同一条评论的所有字段
包括：问题分类（大类子类子子类3个）和一句话总结
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from models.database import get_db
from models.review import Review
from crawler.taptap_crawler_scrapling import TapTapCrawler
from nlp import analyze_review_sentiment, classify_review

print('=' * 60)
print('完整对比25条同一条评论的所有字段')
print('=' * 60)

# 1. 获取数据库中的老数据
db = next(get_db())
old_reviews = db.query(Review).limit(50).all()
print(f'\n数据库中老爬虫数据: {len(old_reviews)} 条')

# 2. 用新爬虫爬取数据
print('\n新爬虫爬取数据...')
crawler = TapTapCrawler(headless=True)
new_reviews = crawler.get_reviews(258720, max_reviews=200)
crawler.close()
print(f'新爬虫获取到 {len(new_reviews)} 条评价')

# 3. 匹配相同用户名的评价，详细对比
print('\n匹配相同用户名的评价...')

comparison_data = []
matched_count = 0

for old in old_reviews:
    for new in new_reviews:
        if old.user_name == new['user_name']:
            matched_count += 1
            
            # 对新爬虫数据进行NLP分析（函数接受字典参数）
            new_sentiment_result = analyze_review_sentiment(new)
            new_sentiment = new_sentiment_result.get('sentiment_label', '中性')
            new_classify = classify_review(new)
            
            # 解析老爬虫的分类（可能是逗号分隔的多个分类）
            old_categories = (old.problem_category or '').split(',') if old.problem_category else []
            old_category_1 = old_categories[0].strip() if len(old_categories) > 0 else ''
            old_category_2 = old_categories[1].strip() if len(old_categories) > 1 else ''
            old_category_3 = old_categories[2].strip() if len(old_categories) > 2 else ''
            
            # 解析新爬虫的分类（classify_review返回字典）
            new_all_primaries = new_classify.get('all_primary_categories', [])
            new_all_secondaries = new_classify.get('all_secondary_categories', [])
            new_category_1 = new_all_primaries[0] if len(new_all_primaries) > 0 else ''
            new_category_2 = new_all_secondaries[0] if len(new_all_secondaries) > 0 else ''
            new_category_3 = new_all_secondaries[1] if len(new_all_secondaries) > 1 else ''
            
            # 详细对比每个字段
            comparison_data.append({
                '序号': matched_count,
                '用户名': old.user_name,
                
                # 内容对比
                '老爬虫-内容长度': len(old.content or ''),
                '新爬虫-内容长度': len(new.get('content', '')),
                '内容长度差异': len(new.get('content', '')) - len(old.content or ''),
                '内容一致': '✓' if old.content == new.get('content', '') else '✗',
                
                # 星级对比
                '老爬虫-星级': old.rating,
                '新爬虫-星级': new.get('rating', 0),
                '星级一致': '✓' if old.rating == new.get('rating', 0) else '✗',
                
                # 日期对比
                '老爬虫-日期': str(old.review_date) if old.review_date else '',
                '新爬虫-日期': new.get('review_date', ''),
                '日期一致': '✓' if str(old.review_date) == new.get('review_date', '') else '✗',
                
                # 情感分析对比
                '老爬虫-情感': old.sentiment or '未分析',
                '新爬虫-情感': new_sentiment,
                '情感一致': '✓' if old.sentiment == new_sentiment else '✗',
                
                # 问题分类对比（大类）
                '老爬虫-分类大类': old_category_1,
                '新爬虫-分类大类': new_category_1,
                '分类大类一致': '✓' if old_category_1 == new_category_1 else '✗',
                
                # 问题分类对比（子类）
                '老爬虫-分类子类': old_category_2,
                '新爬虫-分类子类': new_category_2,
                '分类子类一致': '✓' if old_category_2 == new_category_2 else '✗',
                
                # 问题分类对比（子子类）
                '老爬虫-分类子子类': old_category_3,
                '新爬虫-分类子子类': new_category_3,
                '分类子子类一致': '✓' if old_category_3 == new_category_3 else '✗',
                
                # 一句话总结对比
                '老爬虫-一句话总结': old.summary or '无',
                '新爬虫-一句话总结': '无',  # 新爬虫暂无总结功能
                '总结一致': '✗',
            })
            
            if matched_count >= 25:
                break
    
    if matched_count >= 25:
        break

print(f'\n匹配到 {matched_count} 条相同用户名的评价')

# 4. 保存到Excel
if comparison_data:
    df = pd.DataFrame(comparison_data)
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', '新老爬虫完整对比_25条.xlsx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='完整对比')
        
        # 调整列宽
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
    
    # 5. 打印统计
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
    print(f'分类子子类一致: {sum(1 for d in comparison_data if d["分类子子类一致"] == "✓")}/{total}')
    print(f'总结一致: {sum(1 for d in comparison_data if d["总结一致"] == "✓")}/{total}')
