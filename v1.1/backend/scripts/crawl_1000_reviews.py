# -*- coding: utf-8 -*-
"""
爬取评价并保存为JSON，等待AI分析

流程：
1. 爬取1000条评价
2. 保存为JSON文件
3. 等待AI分析
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.taptap_crawler_scrapling import TapTapCrawler

def crawl_reviews(game_id: int = 258720, max_reviews: int = 1000):
    """
    爬取评价并保存为JSON
    
    参数:
        game_id: 游戏ID，默认鹅鸭杀
        max_reviews: 最大评价数量
    """
    print(f"开始爬取 {max_reviews} 条评价...")
    
    crawler = TapTapCrawler(headless=True)
    reviews = crawler.get_reviews(game_id, max_reviews)
    crawler.close()
    
    print(f"爬取完成，共 {len(reviews)} 条评价")
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'reviews_1000_raw.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    
    print(f"已保存到: {output_file}")
    
    return reviews


if __name__ == '__main__':
    crawl_reviews(max_reviews=1000)
