# -*- coding: utf-8 -*-
"""
直接查询数据库，查看老爬虫数据和新爬虫数据的对比
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from models.review import Review
from crawler.taptap_crawler_scrapling import TapTapCrawler

print('=' * 60)
print('数据库表结构')
print('=' * 60)

db = next(get_db())

# 查看reviews表的数据
print('\n老爬虫数据（reviews表）:')
old_reviews = db.query(Review).limit(20).all()
print(f'共 {len(old_reviews)} 条')

for r in old_reviews[:5]:
    print(f'\n用户名: {r.user_name}')
    print(f'内容长度: {len(r.content or "")} 字')
    print(f'内容: {r.content[:150] if r.content else "N/A"}...')
    print(f'星级: {r.rating}')
    print(f'日期: {r.review_date}')
    print(f'情感: {r.sentiment}')
    print(f'分类: {r.problem_category}')
    print(f'总结: {r.summary}')

# 用新爬虫爬取
print('\n' + '=' * 60)
print('新爬虫数据')
print('=' * 60)

crawler = TapTapCrawler(headless=True)
new_reviews = crawler.get_reviews(258720, max_reviews=50)
crawler.close()

print(f'\n共 {len(new_reviews)} 条')

# 匹配相同用户名
print('\n' + '=' * 60)
print('匹配相同用户名')
print('=' * 60)

for old in old_reviews:
    for new in new_reviews:
        if old.user_name == new['user_name']:
            print(f'\n用户名: {old.user_name}')
            print(f'老爬虫内容长度: {len(old.content or "")} 字')
            print(f'新爬虫内容长度: {len(new["content"])} 字')
            print(f'老爬虫内容: {old.content[:100] if old.content else "N/A"}...')
            print(f'新爬虫内容: {new["content"][:100]}...')
            print(f'内容一致: {"✓" if old.content == new["content"] else "✗"}')
            break
