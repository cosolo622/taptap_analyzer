# -*- coding: utf-8 -*-
"""
爬虫运行脚本

功能：
1. 爬取 TapTap 评价数据
2. 进行情感分析和问题分类
3. 将结果存入数据库

参数:
    game_id: TapTap 游戏 ID（如鹅鸭杀=258720）
    max_reviews: 最大爬取数量
    headless: 是否无头模式

示例:
    python run_crawler.py --game_id 258720 --max_reviews 100
"""
import sys
import os
import argparse
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.taptap_crawler import TapTapCrawler
from nlp.sentiment import analyze_reviews_batch
from nlp.classifier import classify_reviews_batch
from models.database import SessionLocal
from models.review import Review
from models.product import Product
from models.platform import Platform
from models.crawl_log import CrawlLog

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def save_reviews_to_db(reviews: list[dict], product_id: int, platform_id: int) -> int:
    """
    将评价保存到数据库
    
    参数:
        reviews: 评价列表
        product_id: 产品 ID
        platform_id: 平台 ID
    
    返回:
        int: 成功保存的数量
    """
    db = SessionLocal()
    saved_count = 0
    
    try:
        for review_data in reviews:
            existing = db.query(Review).filter(
                Review.review_id == review_data['review_id'],
                Review.product_id == product_id,
                Review.platform_id == platform_id
            ).first()
            
            if existing:
                continue
            
            review = Review(
                product_id=product_id,
                platform_id=platform_id,
                review_id=review_data['review_id'],
                user_name=review_data.get('user_name', '匿名用户'),
                content=review_data.get('content', ''),
                rating=review_data.get('rating', 5),
                sentiment=review_data.get('sentiment_label', '中性'),
                problem_category=review_data.get('primary_category', '其他'),
                summary=review_data.get('content', '')[:200] if review_data.get('content') else '',
                review_date=review_data.get('review_date', datetime.now().strftime('%Y-%m-%d')),
                crawl_date=datetime.now(),
                raw_data=review_data.get('raw_data', '')
            )
            
            db.add(review)
            saved_count += 1
        
        db.commit()
        logger.info(f"成功保存 {saved_count} 条评价到数据库")
        
    except Exception as e:
        db.rollback()
        logger.error(f"保存评价失败: {e}")
        raise
    finally:
        db.close()
    
    return saved_count


def log_crawl_result(product_id: int, platform_id: int, total_count: int, saved_count: int, status: str, error_msg: str = None):
    """
    记录爬取日志
    
    参数:
        product_id: 产品 ID
        platform_id: 平台 ID
        total_count: 爬取总数
        saved_count: 保存数量
        status: 状态（success/failed）
        error_msg: 错误信息
    """
    db = SessionLocal()
    try:
        log = CrawlLog(
            product_id=product_id,
            platform_id=platform_id,
            crawl_time=datetime.now(),
            total_count=total_count,
            new_count=saved_count,
            status=status,
            error_message=error_msg
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"记录爬取日志失败: {e}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='TapTap 评价爬虫')
    parser.add_argument('--game_id', type=int, default=258720, help='TapTap 游戏 ID')
    parser.add_argument('--max_reviews', type=int, default=100, help='最大爬取数量')
    parser.add_argument('--headless', action='store_true', default=True, help='无头模式')
    parser.add_argument('--no_headless', action='store_true', help='显示浏览器窗口')
    args = parser.parse_args()
    
    headless = not args.no_headless
    
    db = SessionLocal()
    product = db.query(Product).filter(Product.id == 1).first()
    platform = db.query(Platform).filter(Platform.code == 'taptap').first()
    db.close()
    
    if not product:
        logger.error("产品不存在，请先在数据库中创建产品记录")
        return
    
    if not platform:
        logger.error("平台不存在，请先在数据库中创建平台记录")
        return
    
    logger.info(f"开始爬取: 游戏 ID={args.game_id}, 最大数量={args.max_reviews}")
    
    try:
        with TapTapCrawler(headless=headless) as crawler:
            reviews = crawler.get_reviews(args.game_id, args.max_reviews)
        
        if not reviews:
            logger.warning("未爬取到任何评价")
            log_crawl_result(product.id, platform.id, 0, 0, 'failed', '未爬取到评价')
            return
        
        logger.info(f"爬取完成，共 {len(reviews)} 条评价，开始分析...")
        
        reviews = analyze_reviews_batch(reviews)
        reviews = classify_reviews_batch(reviews)
        
        saved_count = save_reviews_to_db(reviews, product.id, platform.id)
        
        log_crawl_result(product.id, platform.id, len(reviews), saved_count, 'success')
        
        logger.info(f"任务完成！爬取 {len(reviews)} 条，新增 {saved_count} 条")
        
    except Exception as e:
        logger.error(f"爬取失败: {e}")
        log_crawl_result(product.id, platform.id, 0, 0, 'failed', str(e))
        raise


if __name__ == '__main__':
    main()
