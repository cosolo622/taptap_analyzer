# -*- coding: utf-8 -*-
"""
爬虫测试脚本
用于调试爬虫功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.taptap_crawler import TapTapCrawler

def test_crawler():
    print("开始测试爬虫...")
    
    with TapTapCrawler(headless=False) as crawler:
        print(f"WebDriver 已初始化: {crawler.driver}")
        
        game_id = 258720
        url = f"https://www.taptap.cn/app/{game_id}/review"
        print(f"访问: {url}")
        
        crawler.driver.get(url)
        
        import time
        time.sleep(5)
        
        print(f"页面标题: {crawler.driver.title}")
        print(f"当前 URL: {crawler.driver.current_url}")
        
        page_source = crawler.driver.page_source
        print(f"页面源码长度: {len(page_source)}")
        
        review_elements = crawler.driver.find_elements("css selector", ".review-item, [class*='review']")
        print(f"找到评价元素数量: {len(review_elements)}")
        
        if review_elements:
            print("\n前3个评价元素的内容片段:")
            for i, elem in enumerate(review_elements[:3]):
                try:
                    print(f"\n[{i+1}] {elem.text[:200]}...")
                except:
                    print(f"[{i+1}] 无法获取文本")
        
        reviews = crawler.get_reviews(game_id, max_reviews=5)
        print(f"\n爬取到 {len(reviews)} 条评价")
        
        for i, r in enumerate(reviews, 1):
            print(f"\n[{i}] {r.get('user_name', 'N/A')} - {r.get('rating', 'N/A')}星")
            print(f"    日期: {r.get('review_date', 'N/A')}")
            print(f"    内容: {r.get('content', 'N/A')[:100]}...")

if __name__ == '__main__':
    test_crawler()
