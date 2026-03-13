# -*- coding: utf-8 -*-
"""
鹅鸭杀评价爬取脚本

使用Selenium获取真实评价数据并生成分析报告。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium_crawler import crawl_taptap_reviews
from sentiment import analyze_reviews_batch
from classifier import classify_reviews_batch, get_category_statistics
from exporter import ExcelExporter
from datetime import datetime

def main():
    print("\n" + "="*60)
    print("       鹅鸭杀 TapTap 评价分析")
    print("="*60)
    
    app_id = 258720
    days = 14
    max_reviews = 200
    
    print(f"\n[1/4] 使用Selenium爬取评价 (过去{days}天)...")
    reviews = crawl_taptap_reviews(app_id, days=days, max_reviews=max_reviews)
    
    if not reviews:
        print("❌ 未获取到评价数据")
        return
    
    print(f"✓ 获取到 {len(reviews)} 条评价\n")
    
    print("[2/4] 情感分析...")
    reviews = analyze_reviews_batch(reviews)
    
    # 统计情感分布
    sentiment_dist = {'正向': 0, '中性': 0, '负向': 0}
    for r in reviews:
        sentiment_dist[r.get('sentiment_label', '中性')] += 1
    print(f"✓ 情感分布: 正向 {sentiment_dist['正向']}, 中性 {sentiment_dist['中性']}, 负向 {sentiment_dist['负向']}\n")
    
    print("[3/4] 评价分类...")
    reviews = classify_reviews_batch(reviews)
    stats = get_category_statistics(reviews)
    print(f"✓ 分类完成，主要问题类型:")
    for cat, count in sorted(stats['primary_distribution'].items(), key=lambda x: -x[1])[:5]:
        print(f"   - {cat}: {count} 条")
    print()
    
    print("[4/4] 导出Excel...")
    exporter = ExcelExporter()
    # 使用时间戳避免文件冲突
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = exporter.export(reviews, stats, f"鹅鸭杀_{timestamp}")
    print(f"✓ 文件已保存: {filepath}\n")
    
    # 打印摘要
    print("\n" + "="*60)
    print("分析摘要 - 鹅鸭杀")
    print("="*60)
    
    total = len(reviews)
    print(f"\n📊 基本统计:")
    print(f"   总评价数: {total}")
    
    if total > 0:
        avg_rating = sum(r.get('rating', 0) for r in reviews) / total
        print(f"   平均星级: {avg_rating:.2f}")
        
        print(f"\n📈 情感分布:")
        for label in ['正向', '中性', '负向']:
            count = sentiment_dist[label]
            pct = count / total * 100 if total > 0 else 0
            bar = '█' * int(pct / 5)
            print(f"   {label}: {count} ({pct:.1f}%) {bar}")
        
        print(f"\n📋 问题分类TOP5:")
        sorted_cats = sorted(stats['primary_distribution'].items(), key=lambda x: -x[1])[:5]
        for i, (cat, count) in enumerate(sorted_cats, 1):
            pct = count / total * 100 if total > 0 else 0
            print(f"   {i}. {cat}: {count} ({pct:.1f}%)")
        
        # 打印多标签分类统计
        print(f"\n📋 多标签分类统计（含所有匹配）:")
        sorted_all = sorted(stats.get('all_primaries_distribution', {}).items(), key=lambda x: -x[1])[:5]
        for i, (cat, count) in enumerate(sorted_all, 1):
            print(f"   {i}. {cat}: 出现 {count} 次")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
