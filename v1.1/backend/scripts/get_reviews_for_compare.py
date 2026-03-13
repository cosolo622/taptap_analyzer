# -*- coding: utf-8 -*-
"""
获取新老评价数据进行对比
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from models.review import Review
import json

db = next(get_db())

# 获取老爬虫数据
old_reviews = db.query(Review).limit(50).all()
print(f'老爬虫数据: {len(old_reviews)} 条')

# 保存到JSON文件
data = []
for r in old_reviews:
    data.append({
        'user_name': r.user_name,
        'content': r.content,
        'rating': r.rating,
        'review_date': str(r.review_date) if r.review_date else '',
        'old_sentiment': r.sentiment,
        'old_category': r.problem_category,
        'old_summary': r.summary
    })

output_path = 'output/old_reviews_for_compare.json'
os.makedirs('output', exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'数据已保存到: {output_path}')
