# -*- coding: utf-8 -*-
"""
更新数据库分析字段脚本
将AI分析结果更新到PostgreSQL数据库
"""

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text

ANALYZED_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'reviews_100_ai_analyzed.json')
DATABASE_URL = 'postgresql://postgres:12357951@localhost:5432/public_opinion'


def update_database():
    """
    更新数据库中的分析字段
    
    Returns:
        int: 更新的记录数
    """
    print("开始更新数据库...")
    
    # 读取分析结果
    with open(ANALYZED_FILE, 'r', encoding='utf-8') as f:
        analyzed_reviews = json.load(f)
    
    print(f"读取到 {len(analyzed_reviews)} 条分析结果")
    
    # 创建数据库连接
    engine = create_engine(DATABASE_URL)
    
    updated_count = 0
    
    with engine.begin() as conn:
        for review in analyzed_reviews:
            review_id = review['review_id']
            sentiment = review['sentiment']
            problem_category = review['problem_category']
            summary = review['summary']
            
            # 更新数据库
            update_sql = text("""
                UPDATE reviews 
                SET sentiment = :sentiment,
                    problem_category = :problem_category,
                    summary = :summary
                WHERE review_id = :review_id
            """)
            
            result = conn.execute(update_sql, {
                'sentiment': sentiment,
                'problem_category': problem_category,
                'summary': summary,
                'review_id': review_id
            })
            
            if result.rowcount > 0:
                updated_count += 1
        
        print(f"成功更新 {updated_count} 条记录")
    
    return updated_count


def verify_update():
    """
    验证更新结果
    
    Returns:
        dict: 统计结果
    """
    print("\n验证更新结果...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 统计情感分布
        sentiment_result = conn.execute(text("""
            SELECT sentiment, COUNT(*) as count 
            FROM reviews 
            WHERE sentiment IS NOT NULL 
            GROUP BY sentiment 
            ORDER BY count DESC
        """))
        
        print("\n=== 情感分布 ===")
        sentiment_stats = {}
        for row in sentiment_result:
            print(f"  {row[0]}: {row[1]}条")
            sentiment_stats[row[0]] = row[1]
        
        # 统计问题分类
        category_result = conn.execute(text("""
            SELECT problem_category, COUNT(*) as count 
            FROM reviews 
            WHERE problem_category IS NOT NULL 
            GROUP BY problem_category 
            ORDER BY count DESC
            LIMIT 10
        """))
        
        print("\n=== 问题分类TOP10 ===")
        category_stats = {}
        for row in category_result:
            print(f"  {row[0]}: {row[1]}次")
            category_stats[row[0]] = row[1]
        
        # 统计总结
        summary_result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM reviews 
            WHERE summary IS NOT NULL
        """))
        
        summary_count = summary_result.fetchone()[0]
        print(f"\n=== 一句话总结 ===")
        print(f"  已填充: {summary_count}条")
        
        return {
            'sentiment': sentiment_stats,
            'category': category_stats,
            'summary_count': summary_count
        }


if __name__ == '__main__':
    update_database()
    verify_update()
