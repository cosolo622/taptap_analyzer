# -*- coding: utf-8 -*-
"""
用老爬虫（Selenium）验证当前页面能获取什么内容
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.taptap_crawler import TapTapCrawler as OldCrawler
from models.database import get_db
from models.review import Review

print('=' * 60)
print('老爬虫（Selenium）验证')
print('=' * 60)

# 用老爬虫爬取
crawler = OldCrawler(headless=True)
old_new_reviews = crawler.get_reviews(258720, max_reviews=10)
crawler.close()

print(f'\n老爬虫获取到 {len(old_new_reviews)} 条评价')

for i, r in enumerate(old_new_reviews[:5], 1):
    print(f'\n[{i}] {r["user_name"]} - {r["rating"]}星 - {r["review_date"]}')
    print(f'    内容长度: {len(r["content"])} 字')
    print(f'    内容: {r["content"][:150]}...')

# 对比数据库中的老数据
db = next(get_db())
db_reviews = db.query(Review).filter(Review.user_name == old_new_reviews[0]["user_name"]).first()

if db_reviews:
    print(f'\n数据库中该用户的数据:')
    print(f'    内容长度: {len(db_reviews.content or "")} 字')
    print(f'    内容: {db_reviews.content[:150]}...')
    
    print(f'\n对比:')
    print(f'    老爬虫新爬取: {len(old_new_reviews[0]["content"])} 字')
    print(f'    数据库中老数据: {len(db_reviews.content or "")} 字')
    print(f'    差异: {len(old_new_reviews[0]["content"]) - len(db_reviews.content or "")} 字')
