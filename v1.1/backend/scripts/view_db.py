# -*- coding: utf-8 -*-
"""
查看 PostgreSQL 数据库表结构
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from sqlalchemy import text

db = next(get_db())

# 查看所有表
print('=' * 60)
print('PostgreSQL 数据库表列表')
print('=' * 60)
result = db.execute(text("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
"""))
for row in result:
    print(f'  - {row[0]}')

# 查看各表的数据量
print('\n' + '=' * 60)
print('各表数据量')
print('=' * 60)
tables = ['products', 'platforms', 'reviews', 'crawl_logs', 'alert_rules']
for table in tables:
    try:
        count = db.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
        print(f'  {table}: {count} 条记录')
    except Exception as e:
        print(f'  {table}: 错误 - {e}')

# 查看 reviews 表结构
print('\n' + '=' * 60)
print('reviews 表结构')
print('=' * 60)
result = db.execute(text("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'reviews'
    ORDER BY ordinal_position
"""))
for row in result:
    print(f'  {row[0]}: {row[1]} (nullable: {row[2]})')
