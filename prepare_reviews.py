# -*- coding: utf-8 -*-
"""
读取评价数据，准备让GLM分析
"""

import pandas as pd
import json

# 读取Excel
df = pd.read_excel('./output/鹅鸭杀_20260227_181757_评价分析_20260227.xlsx', sheet_name='评价明细')

print(f"共 {len(df)} 条评价")
print(f"列名: {list(df.columns)}")

# 提取需要的字段
reviews = []
for idx, row in df.iterrows():
    review = {
        'id': idx + 1,
        'user_name': row.get('用户名', ''),
        'rating': row.get('星级', 0),
        'date': row.get('日期', ''),
        'content': row.get('评价内容', ''),
    }
    reviews.append(review)

# 保存为JSON
with open('./output/reviews_for_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(reviews, f, ensure_ascii=False, indent=2)

print(f"\n已保存到 reviews_for_analysis.json")

# 打印前5条
print("\n前5条评价预览:")
for r in reviews[:5]:
    print(f"\n【{r['id']}】{r['user_name']} | {r['rating']}星 | {r['date']}")
    print(f"内容: {r['content'][:100]}...")
