# -*- coding: utf-8 -*-
"""
创建新表存储新爬虫数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models.database import engine

# 创建新表
create_table_sql = """
CREATE TABLE IF NOT EXISTS reviews_new (
    id SERIAL PRIMARY KEY,
    product_id INTEGER,
    platform_id INTEGER,
    user_name VARCHAR(255),
    content TEXT,
    rating INTEGER,
    review_date DATE,
    sentiment VARCHAR(50),
    problem_category TEXT,
    summary TEXT,
    crawl_date TIMESTAMP,
    raw_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

with engine.begin() as conn:
    conn.execute(text(create_table_sql))

print('新表 reviews_new 创建成功！')
