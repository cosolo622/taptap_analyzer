# -*- coding: utf-8 -*-
"""
验证新爬虫修复结果
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from models.review import Review
from crawler.taptap_crawler_scrapling import TapTapCrawler

print('=' * 60)
print('验证新爬虫修复结果')
print('=' * 60)

db = next(get_db())
old_review = db.query(Review).filter(Review.user_name == 'azeo34').first()

if old_review:
    print(f'\n老爬虫数据（用户 azeo34）:')
    print(f'  内容长度: {len(old_review.content or "")} 字')
    print(f'  内容: {old_review.content[:200]}...')

print('\n' + '=' * 60)
print('新爬虫爬取数据')
print('=' * 60)

crawler = TapTapCrawler(headless=True)
new_reviews = crawler.get_reviews(258720, max_reviews=50)
crawler.close()

print(f'\n新爬虫获取到 {len(new_reviews)} 条评价')

# 找到 azeo34 的评价
for r in new_reviews:
    if 'azeo34' in r.get('user_name', ''):
        print(f'\n新爬虫数据（用户 azeo34）:')
        print(f'  内容长度: {len(r.get("content", ""))} 字')
        print(f'  内容: {r.get("content", "")[:200]}...')
        
        # 对比
        if old_review:
            old_len = len(old_review.content or "")
            new_len = len(r.get("content", ""))
            print(f'\n对比结果:')
            print(f'  老爬虫: {old_len} 字')
            print(f'  新爬虫: {new_len} 字')
            print(f'  差异: {new_len - old_len:+d} 字')
            
            if new_len == old_len:
                print('  ✓ 内容长度一致!')
            elif new_len > old_len:
                print('  ✗ 新爬虫内容更长')
            else:
                print('  ✗ 新爬虫内容更短')
        break
