# -*- coding: utf-8 -*-
"""
生成新旧爬虫数据对比文件
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from models.database import get_db
from models.review import Review

db = next(get_db())

# 获取所有评价数据
reviews = db.query(Review).all()
print(f'数据库中共有 {len(reviews)} 条评价')

# 构建对比数据
data = []
for r in reviews:
    data.append({
        'ID': r.id,
        '用户名': r.user_name,
        '评价日期': str(r.review_date) if r.review_date else '',
        '星级': r.rating,
        '评价内容': r.content[:100] + '...' if r.content and len(r.content) > 100 else r.content,
        '情感': r.sentiment or '未分析',
        '问题分类': r.problem_category or '未分类',
        '一句话总结': r.summary or '无',
        '爬取日期': str(r.crawl_date) if r.crawl_date else ''
    })

# 保存到Excel
df = pd.DataFrame(data)
output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'output', '新旧爬虫数据对比.xlsx')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_excel(output_path, index=False, sheet_name='数据对比')

print(f'对比文件已保存: {output_path}')
print(f'共 {len(data)} 条数据')
