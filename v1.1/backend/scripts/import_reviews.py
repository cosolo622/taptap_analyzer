# -*- coding: utf-8 -*-
"""
导入爬取的评价数据到数据库
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import init_db, SessionLocal, Product, Platform, Review
from datetime import datetime

def import_reviews(json_file: str):
    """
    导入评价数据到数据库
    
    Args:
        json_file: JSON文件路径
    """
    init_db()
    
    db = SessionLocal()
    
    try:
        product = db.query(Product).filter(Product.name == '鹅鸭杀').first()
        if not product:
            product = Product(name='鹅鸭杀', code='goose_goose_duck')
            db.add(product)
            db.commit()
            print(f"创建产品: {product.name}")
        
        platform = db.query(Platform).filter(Platform.name == 'TapTap').first()
        if not platform:
            platform = Platform(name='TapTap', code='taptap')
            db.add(platform)
            db.commit()
            print(f"创建平台: {platform.name}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        
        print(f"读取到 {len(reviews)} 条评价")
        
        imported = 0
        skipped = 0
        
        for r in reviews:
            existing = db.query(Review).filter(
                Review.platform_id == platform.id,
                Review.review_id == r.get('review_id')
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            review_date = None
            if r.get('review_date'):
                try:
                    review_date = datetime.strptime(r['review_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            review = Review(
                product_id=product.id,
                platform_id=platform.id,
                review_id=r.get('review_id'),
                user_name=r.get('user_name'),
                content=r.get('content'),
                rating=r.get('rating'),
                review_date=review_date,
                crawl_date=datetime.now(),
                raw_data=r
            )
            db.add(review)
            imported += 1
        
        db.commit()
        
        print(f"导入完成: 新增 {imported} 条, 跳过 {skipped} 条重复")
        
        total = db.query(Review).filter(Review.product_id == product.id).count()
        print(f"数据库中共有 {total} 条评价")
        
    finally:
        db.close()


if __name__ == '__main__':
    json_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'reviews_100.json')
    import_reviews(json_file)
