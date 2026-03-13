# -*- coding: utf-8 -*-
"""
详细对比25条同一条评论的字段差异
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from models.database import get_db
from models.review import Review
from crawler.taptap_crawler_scrapling import TapTapCrawler

print('=' * 60)
print('详细对比25条同一条评论的字段差异')
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
print('\n' + '=' * 60)
print('匹配相同用户名的评价，详细对比25条')
print('=' * 60)

comparison_data = []
matched_count = 0

for old in old_reviews:
    for new in new_reviews:
        if old.user_name == new['user_name']:
            matched_count += 1
            
            # 详细对比每个字段
            comparison_data.append({
                '序号': matched_count,
                '用户名': old.user_name,
                
                # 内容对比
                '老爬虫-内容长度': len(old.content or ''),
                '新爬虫-内容长度': len(new.get('content', '')),
                '内容长度差异': len(new.get('content', '')) - len(old.content or ''),
                '内容一致': '✓' if old.content == new.get('content', '') else '✗',
                
                # 完整内容对比
                '老爬虫-完整内容': old.content or '',
                '新爬虫-完整内容': new.get('content', ''),
                
                # 星级对比
                '老爬虫-星级': old.rating,
                '新爬虫-星级': new.get('rating', 0),
                '星级一致': '✓' if old.rating == new.get('rating', 0) else '✗',
                
                # 日期对比
                '老爬虫-日期': str(old.review_date) if old.review_date else '',
                '新爬虫-日期': new.get('review_date', ''),
                '日期一致': '✓' if str(old.review_date) == new.get('review_date', '') else '✗',
                
                # NLP分析结果（来自老数据）
                '情感分析': old.sentiment or '未分析',
                '问题分类': old.problem_category or '未分类',
                '一句话总结': old.summary or '无',
            })
            
            if matched_count >= 25:
                break
    
    if matched_count >= 25:
        break

print(f'\n匹配到 {matched_count} 条相同用户名的评价')

# 4. 保存到Excel
if comparison_data:
    df = pd.DataFrame(comparison_data)
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'output', '新老爬虫详细对比_25条.xlsx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: 详细对比
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
            adjusted_width = min(max_length + 2, 80)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
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
    
    # 内容长度差异统计
    avg_diff = sum(d['内容长度差异'] for d in comparison_data) / total
    print(f'平均内容长度差异: {avg_diff:.1f} 字')
    
    # 打印前5条详细对比
    print('\n' + '=' * 60)
    print('前5条详细对比')
    print('=' * 60)
    
    for d in comparison_data[:5]:
        print(f"\n[{d['序号']}] 用户名: {d['用户名']}")
        print(f"老爬虫内容({d['老爬虫-内容长度']}字): {d['老爬虫-完整内容'][:150]}...")
        print(f"新爬虫内容({d['新爬虫-内容长度']}字): {d['新爬虫-完整内容'][:150]}...")
        print(f"内容长度差异: {d['内容长度差异']}字")
        print(f"内容一致: {d['内容一致']}")
        print(f"星级一致: {d['星级一致']} (老:{d['老爬虫-星级']} vs 新:{d['新爬虫-星级']})")
        print(f"日期一致: {d['日期一致']} (老:{d['老爬虫-日期']} vs 新:{d['新爬虫-日期']})")
