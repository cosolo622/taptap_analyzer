# -*- coding: utf-8 -*-
"""
验证新爬虫修复结果 - 爬取与老爬虫相同日期范围的评价
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from models.review import Review
from crawler.taptap_crawler_scrapling import TapTapCrawler
import pandas as pd

print('=' * 60)
print('验证新爬虫修复结果')
print('=' * 60)

# 1. 获取数据库中老爬虫数据的日期范围
db = next(get_db())
old_reviews = db.query(Review).order_by(Review.review_date.desc()).limit(10).all()

print(f'\n老爬虫数据日期范围:')
dates = [r.review_date for r in old_reviews if r.review_date]
if dates:
    min_date = min(dates)
    max_date = max(dates)
    print(f'  最早: {min_date}')
    print(f'  最晚: {max_date}')

print(f'\n老爬虫数据样例（前3条）:')
for i, r in enumerate(old_reviews[:3], 1):
    print(f'[{i}] {r.user_name} - {r.rating}星 - {r.review_date}')
    print(f'    内容: {r.content[:80] if r.content else "N/A"}...')

# 2. 用新爬虫爬取相同日期范围的数据
print('\n' + '=' * 60)
print('新爬虫爬取（增加滚动次数，确保获取历史数据）')
print('=' * 60)

crawler = TapTapCrawler(headless=True)
# 增加max_reviews和滚动次数，确保能获取到历史数据
new_reviews = crawler.get_reviews(258720, max_reviews=200)
crawler.close()

print(f'\n新爬虫获取到 {len(new_reviews)} 条评价')

# 3. 对比结果
print('\n' + '=' * 60)
print('对比结果')
print('=' * 60)

# 尝试匹配相同评价
matched = 0
for old in old_reviews[:5]:
    for new in new_reviews:
        # 通过内容匹配
        if old.content and new['content']:
            if old.content[:50] in new['content'] or new['content'][:50] in old.content:
                matched += 1
                print(f'\n✓ 匹配到相同评价:')
                print(f'  老爬虫: {old.user_name} - {len(old.content)}字')
                print(f'  新爬虫: {new["user_name"]} - {len(new["content"])}字')
                print(f'  内容差异: {len(new["content"]) - len(old.content):+d}字')
                break

print(f'\n共匹配到 {matched}/5 条相同评价')

# 4. 生成对比Excel
comparison_data = []
for i in range(min(5, len(old_reviews), len(new_reviews))):
    old = old_reviews[i]
    new = new_reviews[i]
    
    comparison_data.append({
        '序号': i + 1,
        '老爬虫-用户名': old.user_name,
        '新爬虫-用户名': new['user_name'],
        '老爬虫-内容长度': len(old.content or ''),
        '新爬虫-内容长度': len(new['content']),
        '内容差异': len(new['content']) - len(old.content or ''),
        '老爬虫-日期': str(old.review_date) if old.review_date else '',
        '新爬虫-日期': new['review_date'],
    })

df = pd.DataFrame(comparison_data)
output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'output', '爬虫修复验证.xlsx')
df.to_excel(output_path, index=False)
print(f'\n对比文件已保存: {output_path}')
