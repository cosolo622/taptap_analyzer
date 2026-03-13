# -*- coding: utf-8 -*-
"""
完整的新旧爬虫数据对比（包含NLP分析结果）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from models.database import get_db
from models.review import Review
from crawler.taptap_crawler_scrapling import TapTapCrawler

print('=' * 60)
print('完整的新旧爬虫数据对比')
print('=' * 60)

# 1. 获取数据库中的老数据
db = next(get_db())
old_reviews = db.query(Review).limit(10).all()
print(f'\n数据库中老爬虫数据: {len(old_reviews)} 条')

# 2. 用新爬虫爬取数据
print('\n启动新爬虫爬取数据...')
crawler = TapTapCrawler(headless=True)
new_reviews = crawler.get_reviews(258720, max_reviews=10)
crawler.close()
print(f'新爬虫爬取数据: {len(new_reviews)} 条')

# 3. 构建详细对比数据
comparison_data = []

for i in range(min(len(old_reviews), len(new_reviews))):
    old = old_reviews[i]
    new = new_reviews[i]
    
    # 内容匹配检查
    content_match = False
    if old.content and new['content']:
        # 检查内容是否包含关系
        if old.content[:50] in new['content'] or new['content'][:50] in old.content:
            content_match = True
    
    comparison_data.append({
        '序号': i + 1,
        
        # 基本信息对比
        '老爬虫-用户名': old.user_name,
        '新爬虫-用户名': new.get('user_name', ''),
        '用户名一致': '✓' if old.user_name == new.get('user_name', '') else '✗',
        
        '老爬虫-星级': old.rating,
        '新爬虫-星级': new.get('rating', 0),
        '星级一致': '✓' if old.rating == new.get('rating', 0) else '✗',
        
        '老爬虫-日期': str(old.review_date) if old.review_date else '',
        '新爬虫-日期': new.get('review_date', ''),
        '日期一致': '✓' if str(old.review_date) == new.get('review_date', '') else '✗',
        
        # 内容对比（关键）
        '老爬虫-内容长度': len(old.content or ''),
        '新爬虫-内容长度': len(new.get('content', '')),
        '内容长度差异': len(new.get('content', '')) - len(old.content or ''),
        '内容匹配': '✓' if content_match else '✗',
        
        '老爬虫-内容(前100字)': (old.content or '')[:100] + '...' if len(old.content or '') > 100 else (old.content or ''),
        '新爬虫-内容(前100字)': new.get('content', '')[:100] + '...' if len(new.get('content', '')) > 100 else new.get('content', ''),
        
        # NLP分析结果（仅老爬虫有）
        '情感分析': old.sentiment or '未分析',
        '问题分类': old.problem_category or '未分类',
        '一句话总结': old.summary or '无',
    })

# 4. 保存到Excel（多个sheet）
output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'output', '新旧爬虫完整对比.xlsx')
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    # Sheet 1: 详细对比
    df = pd.DataFrame(comparison_data)
    df.to_excel(writer, index=False, sheet_name='详细对比')
    
    # 调整列宽
    worksheet = writer.sheets['详细对比']
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 60)
        worksheet.column_dimensions[column_letter].width = adjusted_width
    
    # Sheet 2: 统计摘要
    stats = {
        '指标': ['用户名匹配率', '星级匹配率', '日期匹配率', '内容匹配率', '平均内容长度差异'],
        '数值': [
            f"{sum(1 for d in comparison_data if d['用户名一致'] == '✓')}/{len(comparison_data)}",
            f"{sum(1 for d in comparison_data if d['星级一致'] == '✓')}/{len(comparison_data)}",
            f"{sum(1 for d in comparison_data if d['日期一致'] == '✓')}/{len(comparison_data)}",
            f"{sum(1 for d in comparison_data if d['内容匹配'] == '✓')}/{len(comparison_data)}",
            f"{sum(d['内容长度差异'] for d in comparison_data) / len(comparison_data):.1f} 字"
        ]
    }
    df_stats = pd.DataFrame(stats)
    df_stats.to_excel(writer, index=False, sheet_name='统计摘要')

print(f'\n对比文件已保存: {output_path}')

# 5. 打印统计
total = len(comparison_data)
user_match = sum(1 for d in comparison_data if d['用户名一致'] == '✓')
rating_match = sum(1 for d in comparison_data if d['星级一致'] == '✓')
date_match = sum(1 for d in comparison_data if d['日期一致'] == '✓')
content_match = sum(1 for d in comparison_data if d['内容匹配'] == '✓')
avg_diff = sum(d['内容长度差异'] for d in comparison_data) / len(comparison_data)

print(f'\n匹配统计:')
print(f'  用户名匹配: {user_match}/{total} ({user_match/total*100:.1f}%)')
print(f'  星级匹配: {rating_match}/{total} ({rating_match/total*100:.1f}%)')
print(f'  日期匹配: {date_match}/{total} ({date_match/total*100:.1f}%)')
print(f'  内容匹配: {content_match}/{total} ({content_match/total*100:.1f}%)')
print(f'  平均内容长度差异: {avg_diff:.1f} 字')

# 6. 检查内容长度差异较大的情况
print('\n内容长度差异较大的评价:')
for d in comparison_data:
    if abs(d['内容长度差异']) > 50:
        print(f"  [{d['序号']}] 差异: {d['内容长度差异']:+d} 字")
        print(f"       老: {d['老爬虫-内容长度']} 字")
        print(f"       新: {d['新爬虫-内容长度']} 字")
