# -*- coding: utf-8 -*-
"""
导入分析后的评价数据到数据库
将"中性偏负"合并到"负向"
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, init_db
from models.review import Review
from models.product import Product
from models.platform import Platform


def normalize_sentiment(sentiment):
    """
    标准化情感标签，将"中性偏负"合并到"负向"
    
    Args:
        sentiment: 原始情感标签
        
    Returns:
        标准化后的情感标签：正向/负向/中性
    """
    if sentiment == "中性偏负":
        return "负向"
    return sentiment


def import_reviews_with_analysis(json_file, analysis_data):
    """
    导入评价数据到数据库，包含分析结果
    
    Args:
        json_file: 原始评价JSON文件路径
        analysis_data: 分析结果字典 {review_id: {sentiment, problem_category, summary}}
    """
    init_db()
    
    db = SessionLocal()
    
    try:
        # 获取或创建产品
        product = db.query(Product).filter(Product.name == '鹅鸭杀').first()
        if not product:
            product = Product(name='鹅鸭杀', code='goose_goose_duck')
            db.add(product)
            db.commit()
            print(f"创建产品: {product.name}")
        
        # 获取或创建平台
        platform = db.query(Platform).filter(Platform.name == 'TapTap').first()
        if not platform:
            platform = Platform(name='TapTap', code='taptap')
            db.add(platform)
            db.commit()
            print(f"创建平台: {platform.name}")
        
        # 读取原始评价
        with open(json_file, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        
        print(f"读取到 {len(reviews)} 条评价")
        print(f"分析结果 {len(analysis_data)} 条")
        
        # 统计
        imported = 0
        updated = 0
        skipped = 0
        
        for r in reviews:
            review_id = r.get('review_id')
            existing = db.query(Review).filter(
                Review.platform_id == platform.id,
                Review.review_id == review_id
            ).first()
            
            # 处理日期
            review_date = None
            if r.get('review_date'):
                try:
                    review_date = datetime.strptime(r['review_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            # 处理爬取时间
            crawl_date = None
            if r.get('crawl_date'):
                try:
                    crawl_date = datetime.strptime(r['crawl_date'], '%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            # 获取分析结果
            analysis = analysis_data.get(review_id, {})
            sentiment = normalize_sentiment(analysis.get('sentiment')) if analysis.get('sentiment') else None
            
            if existing:
                # 更新已有记录
                if sentiment:
                    existing.sentiment = sentiment
                    existing.problem_category = analysis.get('problem_category')
                    existing.summary = analysis.get('summary')
                    updated += 1
                else:
                    skipped += 1
            else:
                # 创建新记录
                review = Review(
                    product_id=product.id,
                    platform_id=platform.id,
                    review_id=review_id,
                    user_name=r.get('user_name'),
                    content=r.get('content'),
                    rating=r.get('rating'),
                    sentiment=sentiment,
                    problem_category=analysis.get('problem_category'),
                    summary=analysis.get('summary'),
                    review_date=review_date,
                    crawl_date=crawl_date,
                    raw_data=r
                )
                db.add(review)
                imported += 1
        
        db.commit()
        
        print(f"导入完成: 新增 {imported} 条, 更新 {updated} 条, 跳过 {skipped} 条")
        
        # 统计情感分布
        total = db.query(Review).filter(Review.platform_id == platform.id).count()
        positive = db.query(Review).filter(Review.platform_id == platform.id, Review.sentiment == '正向').count()
        negative = db.query(Review).filter(Review.platform_id == platform.id, Review.sentiment == '负向').count()
        neutral = db.query(Review).filter(Review.platform_id == platform.id, Review.sentiment == '中性').count()
        
        print(f"\n数据库统计:")
        print(f"总评价数: {total}")
        if total > 0:
            print(f"正向: {positive} ({positive/total*100:.1f}%)")
            print(f"负向: {negative} ({negative/total*100:.1f}%)")
            print(f"中性: {neutral} ({neutral/total*100:.1f}%)")
        
    except Exception as e:
        print(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


def run_import():
    """
    执行导入
    """
    json_file = os.path.join(os.path.dirname(__file__), 'goose_goose_duck_reviews_2026-01-07_20260316_192922.json')
    analyzed_file = os.path.join(os.path.dirname(__file__), 'reviews_analyzed.json')
    
    # 读取分析结果
    analysis_data = {}
    if os.path.exists(analyzed_file):
        with open(analyzed_file, 'r', encoding='utf-8') as f:
            analysis_list = json.load(f)
        # 将列表转换为字典
        for item in analysis_list:
            review_id = item.get('review_id')
            if review_id:
                analysis_data[review_id] = {
                    'sentiment': item.get('sentiment'),
                    'problem_category': f"{item.get('problem_category', '')}-{item.get('problem_detail', '')}" if item.get('problem_category') else None,
                    'summary': item.get('summary')
                }
        print(f"读取分析结果: {len(analysis_data)} 条")
    else:
        print("未找到分析结果文件，将只导入原始数据")
    
    import_reviews_with_analysis(json_file, analysis_data)


if __name__ == '__main__':
    run_import()
