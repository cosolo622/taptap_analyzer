# -*- coding: utf-8 -*-
"""
测试新爬虫日期解析
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.taptap_crawler_scrapling import TapTapCrawler

async def test_date():
    crawler = TapTapCrawler(headless=True)
    
    # 初始化浏览器
    await crawler._init_browser()
    
    url = "https://www.taptap.cn/app/258720/review"
    print(f"访问: {url}")
    
    await crawler.page.goto(url, wait_until='networkidle')
    await crawler.page.wait_for_timeout(3000)
    
    # 解析评价
    print("\n解析评价...")
    reviews = await crawler._parse_reviews()
    
    print(f"\n获取到 {len(reviews)} 条评价")
    
    for i, r in enumerate(reviews[:10]):
        print(f"[{i+1}] {r['user_name']}: {r['review_date']} ({r['rating']}星)")
    
    await crawler.close_async()

if __name__ == '__main__':
    asyncio.run(test_date())
