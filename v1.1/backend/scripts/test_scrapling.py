# -*- coding: utf-8 -*-
"""
Scrapling 爬虫测试脚本
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.taptap_crawler_scrapling import TapTapCrawler

def test_scrapling():
    print("=" * 50)
    print("测试 Scrapling 爬虫")
    print("=" * 50)
    
    try:
        print("\n正在初始化爬虫...")
        crawler = TapTapCrawler(headless=False)
        
        print(f"爬虫已初始化，headless={crawler.headless}")
        
        game_id = 258720
        url = f"https://www.taptap.cn/app/{game_id}/review"
        print(f"\n访问: {url}")
        
        print("\n开始爬取评价...")
        reviews = crawler.get_reviews(game_id, max_reviews=5)
        
        print(f"\n爬取完成，共 {len(reviews)} 条评价")
        
        for i, r in enumerate(reviews, 1):
            print(f"\n[{i}] {r.get('user_name', 'N/A')} - {r.get('rating', 'N/A')}星")
            print(f"    日期: {r.get('review_date', 'N/A')}")
            print(f"    内容: {r.get('content', 'N/A')[:100]}...")
        
        crawler.close()
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_scrapling()
