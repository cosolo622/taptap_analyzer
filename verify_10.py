# -*- coding: utf-8 -*-
"""
验证脚本 - 只爬10条验证星级和日期
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium_crawler import crawl_taptap_reviews

print("爬取10条评价验证...")
reviews = crawl_taptap_reviews(258720, days=14, max_reviews=10)

print(f"\n获取到 {len(reviews)} 条评价\n")
print("="*80)

for i, r in enumerate(reviews, 1):
    print(f"\n【评价 {i}】")
    print(f"  用户名: {r.get('user_name', '未知')}")
    print(f"  星级: {r.get('rating', 0)} 星")
    print(f"  日期: {r.get('review_date', '未知')}")
    print(f"  游戏时长: {r.get('play_time_str', '未知')}")
    print(f"  设备: {r.get('device', '未知')}")
    print(f"  内容: {r.get('content', '')[:60]}...")
    print("-"*80)
