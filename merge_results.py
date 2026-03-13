# -*- coding: utf-8 -*-
"""
合并所有分析结果并生成新的Excel
"""

import json
import pandas as pd
from collections import Counter
from datetime import datetime

# 读取所有分析结果
all_results = []

files = [
    './output/analysis_batch_1.json',
    './output/analysis_batch_2.json',
    './output/analysis_batch_3_5.json',
    './output/analysis_batch_6_8.json',
    './output/analysis_batch_9_10.json'
]

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        results = json.load(file)
        all_results.extend(results)

print(f"共合并 {len(all_results)} 条分析结果")

# 读取原始评价数据
with open('./output/reviews_for_analysis.json', 'r', encoding='utf-8') as f:
    original_reviews = json.load(f)

# 合并数据
merged_data = []
for review in original_reviews:
    review_id = review['id']
    analysis = next((r for r in all_results if r['id'] == review_id), None)
    
    if analysis:
        merged_data.append({
            '序号': review_id,
            '日期': review.get('date', ''),
            '用户名': review.get('user_name', ''),
            '星级': review.get('rating', 0),
            '情感': analysis.get('sentiment', ''),
            '问题分类': ', '.join(analysis.get('issues', [])),
            '一句话摘要': analysis.get('summary', ''),
            '评价内容': review.get('content', '')
        })

print(f"合并后共 {len(merged_data)} 条数据")

# 统计分析
sentiments = [d['情感'] for d in merged_data]
sentiment_dist = Counter(sentiments)
print(f"\n情感分布: {dict(sentiment_dist)}")

# 统计问题分类
all_issues = []
for d in merged_data:
    issues = d['问题分类']
    if issues:
        all_issues.extend([i.strip() for i in issues.split(',')])

issue_dist = Counter(all_issues)
print(f"\n问题分类TOP10:")
for issue, count in issue_dist.most_common(10):
    print(f"  {issue}: {count}次")

# 创建DataFrame
df = pd.DataFrame(merged_data)

# 保存Excel
output_file = f'./output/鹅鸭杀_GLM分析_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet1: 评价明细
    df.to_excel(writer, sheet_name='评价明细', index=False)
    
    # Sheet2: 情感分布
    sentiment_df = pd.DataFrame([
        {'情感': k, '数量': v, '占比': f'{v/len(merged_data)*100:.1f}%'}
        for k, v in sentiment_dist.items()
    ])
    sentiment_df.to_excel(writer, sheet_name='情感分布', index=False)
    
    # Sheet3: 问题分类统计
    issue_df = pd.DataFrame([
        {'问题分类': k, '出现次数': v}
        for k, v in issue_dist.most_common(30)
    ])
    issue_df.to_excel(writer, sheet_name='问题分类统计', index=False)

print(f"\n✓ Excel已保存: {output_file}")
