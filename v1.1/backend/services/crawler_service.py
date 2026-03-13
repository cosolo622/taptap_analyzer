# -*- coding: utf-8 -*-
"""
爬虫服务模块

提供数据更新的核心功能：
1. 全量爬取：一次性爬取所有历史数据
2. 增量更新：检测最后爬取日期，自动爬取新数据
3. 自动补漏：检测数据缺口， 自动补齐缺失日期的数据

参数:
    db: 数据库会话
    
返回:
    CrawlerService: 爬虫服务实例

示例:
    service = CrawlerService(db)
    result = service.crawl_full('鹅鸭杀', 'TapTap', max_reviews=8000)
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import logging

from models import Product, Platform, Review, CrawlLog
from crawler.taptap_crawler_scrapling import TapTapCrawler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CrawlerService:
    """
    爬虫服务类
    
    替代实现方式：
    - 使用 Celery: 分布式任务队列
    - 使用 APScheduler: 定时任务调度
    """
    
    TAPTAP_GAME_MAP = {
        '鹅鸭杀': 258720,
        '王者荣耀': 64257,
        '和平精英': 36863,
        '原神': 168825,
        '崩坏：星穹铁道': 224575,
        '明日方舟': 52314,
    }
    
    def __init__(self, db: Session):
        """
        初始化爬虫服务
        
        参数:
            db: 数据库会话
        """
        self.db = db
    
    def get_last_crawl_date(self, product_id: int, platform_id: int) -> Optional[datetime]:
        """
        获取最后爬取的评价日期
        
        参数:
            product_id: 产品ID
            platform_id: 平台ID
        
        返回:
            datetime: 最后评价日期
        """
        last_review = self.db.query(Review).filter(
            and_(
                Review.product_id == product_id,
                Review.platform_id == platform_id
            )
        ).order_by(Review.review_date.desc()).first()
        
        return last_review.review_date if last_review else None
    
    def get_date_gaps(self, product_id: int, platform_id: int, days: int = 30) -> List[str]:
        """
        检测数据缺口（哪些日期没有数据）
        
        参数:
            product_id: 产品ID
            platform_id: 平台ID
            days: 检测最近多少天
        
        返回:
            list: 缺失日期列表
        """
        existing_dates = set(
            r[0] for r in self.db.query(Review.review_date).filter(
                and_(
                    Review.product_id == product_id,
                    Review.platform_id == platform_id,
                    Review.review_date >= datetime.now().date() - timedelta(days=days)
                )
            ).distinct().all()
        )
        
        all_dates = set()
        for i in range(days):
            date = (datetime.now().date() - timedelta(days=i))
            all_dates.add(date)
        
        gaps = sorted(all_dates - existing_dates, reverse=True)
        return [str(g) for g in gaps]
    
    def crawl_full(self, product_name: str, platform_name: str = 'TapTap', max_reviews: int = 8000) -> Dict:
        """
        全量爬取
        
        参数:
            product_name: 产品名称
            platform_name: 平台名称
            max_reviews: 最大爬取数量
        
        返回:
            dict: 爬取结果
        """
        product = self._get_or_create_product(product_name)
        platform = self._get_or_create_platform(platform_name)
        
        game_id = self.TAPTAP_GAME_MAP.get(product_name)
        if not game_id:
            return {"error": f"未找到游戏 {product_name} 的 TapTap ID"}
        
        crawl_log = self._create_crawl_log(product.id, platform.id, 'full')
        
        try:
            logger.info(f"开始全量爬取: {product_name}, 目标数量: {max_reviews}")
            crawler = TapTapCrawler(headless=True)
            reviews = crawler.get_reviews(game_id, max_reviews=max_reviews)
            crawler.close()
            
            added, updated = self._save_reviews(reviews, product.id, platform.id)
            
            crawl_log.status = 'success'
            crawl_log.end_time = datetime.now()
            crawl_log.reviews_added = added
            crawl_log.reviews_updated = updated
            self.db.commit()
            
            logger.info(f"全量爬取完成: 新增 {added}, 更新 {updated}")
            return {
                "status": "success",
                "added": added,
                "updated": updated,
                "total": len(reviews)
            }
            
        except Exception as e:
            crawl_log.status = 'failed'
            crawl_log.error_message = str(e)
            crawl_log.end_time = datetime.now()
            self.db.commit()
            logger.error(f"全量爬取失败: {e}")
            return {"error": str(e)}
    
    def crawl_incremental(self, product_name: str, platform_name: str = 'TapTap') -> Dict:
        """
        增量更新
        
        自动检测最后爬取日期，从该日期开始爬取到今天
        
        参数:
            product_name: 产品名称
            platform_name: 平台名称
        
        返回:
            dict: 爬取结果
        """
        product = self._get_or_create_product(product_name)
        platform = self._get_or_create_platform(platform_name)
        
        game_id = self.TAPTAP_GAME_MAP.get(product_name)
        if not game_id:
            return {"error": f"未找到游戏 {product_name} 的 TapTap ID"}
        
        last_date = self.get_last_crawl_date(product.id, platform.id)
        
        crawl_log = self._create_crawl_log(product.id, platform.id, 'incremental')
        
        try:
            logger.info(f"开始增量爬取: {product_name}, 从 {last_date or '开始'}")
            crawler = TapTapCrawler(headless=True)
            reviews = crawler.get_reviews(game_id, max_reviews=2000)
            crawler.close()
            
            if last_date:
                reviews = [r for r in reviews if r['review_date'] > last_date]
            
            added, updated = self._save_reviews(reviews, product.id, platform.id)
            
            crawl_log.status = 'success'
            crawl_log.end_time = datetime.now()
            crawl_log.reviews_added = added
            crawl_log.reviews_updated = updated
            self.db.commit()
            
            logger.info(f"增量爬取完成: 新增 {added}, 更新 {updated}")
            return {
                "status": "Success",
                "last_date": str(last_date) if last_date else None,
                "added": added,
                "updated": updated,
                "total": len(reviews)
            }
            
        except Exception as e:
            crawl_log.status = 'failed'
            crawl_log.error_message = str(e)
            crawl_log.end_time = datetime.now()
            self.db.commit()
            logger.error(f"增量爬取失败: {e}")
            return {"error": str(e)}
    
    def fill_gaps(self, product_name: str, platform_name: str = 'TapTap', days: int = 30) -> Dict:
        """
        自动补漏
        
        检测最近N天内缺失的日期，自动补齐
        
        参数:
            product_name: 产品名称
            platform_name: 平台名称
            days: 检测天数
        
        返回:
            dict: 补漏结果
        """
        product = self._get_or_create_product(product_name)
        platform = self._get_or_create_platform(platform_name)
        
        game_id = self.TAPTAP_GAME_MAP.get(product_name)
        if not game_id:
            return {"error": f"未找到游戏 {product_name} 的 TapTap ID"}
        
        gaps = self.get_date_gaps(product.id, platform.id, days)
        
        if not gaps:
            return {
                "status": "no_gaps",
                "message": "数据完整，无需补漏"
            }
        
        crawl_log = self._create_crawl_log(product.id, platform.id, 'fill_gaps')
        
        try:
            logger.info(f"开始补漏: {product_name}, 缺失 {len(gaps)} 天")
            crawler = TapTapCrawler(headless=True)
            reviews = crawler.get_reviews(game_id, max_reviews=2000)
            crawler.close()
            
            gap_dates = set(gaps)
            gap_reviews = [r for r in reviews if r['review_date'] in gap_dates]
            
            added, updated = self._save_reviews(gap_reviews, product.id, platform.id)
            
            crawl_log.status = 'success'
            crawl_log.end_time = datetime.now()
            crawl_log.reviews_added = added
            crawl_log.reviews_updated = updated
            self.db.commit()
            
            logger.info(f"补漏完成: 新增 {added}")
            return {
                "status": "success",
                "gaps_found": len(gaps),
                "gaps_filled": len(gap_reviews),
                "added": added,
                "updated": updated
            }
            
        except Exception as e:
            crawl_log.status = 'failed'
            crawl_log.error_message = str(e)
            crawl_log.end_time = datetime.now()
            self.db.commit()
            logger.error(f"补漏失败: {e}")
            return {"error": str(e)}
    
    def get_status(self, product_name: str, platform_name: str = 'TapTap') -> Dict:
        """
        获取爬取状态
        
        参数:
            product_name: 产品名称
            platform_name: 平台名称
        
        返回:
            dict: 状态信息
        """
        product = self.db.query(Product).filter(Product.name == product_name).first()
        if not product:
            return {"error": f"未找到产品 {product_name}"}
        
        platform = self.db.query(Platform).filter(Platform.name == platform_name).first()
        if not platform:
            return {"error": f"未找到平台 {platform_name}"}
        
        total_reviews = self.db.query(Review).filter(
            and_(
                Review.product_id == product.id,
                Review.platform_id == platform.id
            )
        ).count()
        
        last_date = self.get_last_crawl_date(product.id, platform.id)
        
        last_log = self.db.query(CrawlLog).filter(
            and_(
                CrawlLog.product_id == product.id,
                CrawlLog.platform_id == platform.id
            )
        ).order_by(CrawlLog.start_time.desc()).first()
        
        gaps = self.get_date_gaps(product.id, platform.id, days=30)
        
        return {
            "product": product_name,
            "platform": platform_name,
            "total_reviews": total_reviews,
            "last_crawl_date": str(last_date) if last_date else None,
            "last_crawl_status": last_log.status if last_log else None,
            "last_crawl_time": str(last_log.start_time) if last_log and last_log.start_time else None,
            "gap_days": len(gaps),
            "gap_dates": gaps[:10]
        }
    
    def _get_or_create_product(self, name: str) -> Product:
        """获取或创建产品"""
        product = self.db.query(Product).filter(Product.name == name).first()
        if not product:
            code = name.lower().replace(' ', '_')
            product = Product(name=name, code=code)
            self.db.add(product)
            self.db.commit()
        return product
    
    def _get_or_create_platform(self, name: str) -> Platform:
        """获取或创建平台"""
        platform = self.db.query(Platform).filter(Platform.name == name).first()
        if not platform:
            code = name.lower()
            platform = Platform(name=name, code=code)
            self.db.add(platform)
            self.db.commit()
        return platform
    
    def _create_crawl_log(self, product_id: int, platform_id: int, mode: str) -> CrawlLog:
        """创建爬取日志"""
        log = CrawlLog(
            spider_name=f'taptap_{mode}',
            product_id=product_id,
            platform_id=platform_id,
            start_time=datetime.now(),
            status='running'
        )
        self.db.add(log)
        self.db.commit()
        return log
    
    def _save_reviews(self, reviews: list, product_id: int, platform_id: int) -> tuple:
        """
        保存评价到数据库
        
        参数:
            reviews: 评价列表
            product_id: 产品ID
            platform_id: 平台ID
        
        返回:
            tuple: (新增数量, 更新数量)
        """
        added = 0
        updated = 0
        
        for r in reviews:
            existing = self.db.query(Review).filter(
                and_(
                    Review.product_id == product_id,
                    Review.platform_id == platform_id,
                    Review.user_name == r['user_name'],
                    Review.review_date == r['review_date']
                )
            ).first()
            
            if existing:
                existing.content = r['content']
                existing.rating = r['rating']
                existing.crawl_date = r['crawl_date']
                updated += 1
            else:
                review = Review(
                    product_id=product_id,
                    platform_id=platform_id,
                    user_name=r['user_name'],
                    content=r['content'],
                    rating=r['rating'],
                    review_date=r['review_date'],
                    crawl_date=r['crawl_date']
                )
                self.db.add(review)
                added += 1
        
        self.db.commit()
        return added, updated
