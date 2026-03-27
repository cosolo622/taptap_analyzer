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
from nlp.glm_analyzer import AliyunAnalyzer
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
MAX_ANALYZE_PER_RUN = 300


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

    def _resolve_game_id(self, product: Product, product_name: str) -> Optional[int]:
        code = str(product.code or '').strip()
        if code.isdigit():
            return int(code)
        return self.TAPTAP_GAME_MAP.get(product_name)
    
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
                Review.platform_id == platform_id,
                Review.review_date.isnot(None)
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
    
    def crawl_full(
        self,
        product_name: str,
        platform_name: str = 'TapTap',
        max_reviews: Optional[int] = None,
        should_stop=None,
        progress_callback=None
    ) -> Dict:
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
        
        game_id = self._resolve_game_id(product, product_name)
        if not game_id:
            return {"error": f"未找到游戏 {product_name} 的 TapTap ID"}
        
        crawl_log = self._create_crawl_log(product.id, platform.id, 'full')
        
        try:
            logger.info(f"开始全量爬取: {product_name}, 目标数量: {max_reviews or '不限'}")
            crawler = TapTapCrawler(headless=True)
            reviews = crawler.get_reviews(
                game_id,
                max_reviews=max_reviews,
                stop_checker=should_stop,
                progress_callback=progress_callback
            )
            crawler.close()
            if callable(should_stop) and should_stop():
                return {"error": "任务已停止"}
            
            added, duplicated = self._save_reviews(reviews, product.id, platform.id)

            crawl_log.status = 'success'
            crawl_log.end_time = datetime.now()
            crawl_log.reviews_added = added
            crawl_log.reviews_updated = duplicated
            self.db.commit()

            logger.info(f"全量爬取完成: 新增 {added}, 重复 {duplicated}")
            return {
                "status": "success",
                "added": added,
                "updated": duplicated,
                "total": len(reviews)
            }
            
        except Exception as e:
            crawl_log.status = 'failed'
            crawl_log.error_message = str(e)
            crawl_log.end_time = datetime.now()
            self.db.commit()
            logger.error(f"全量爬取失败: {e}")
            return {"error": str(e)}
    
    def crawl_incremental(
        self,
        product_name: str,
        platform_name: str = 'TapTap',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        should_stop=None,
        progress_callback=None
    ) -> Dict:
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
        
        game_id = self._resolve_game_id(product, product_name)
        if not game_id:
            return {"error": f"未找到游戏 {product_name} 的 TapTap ID"}
        
        last_date = self.get_last_crawl_date(product.id, platform.id)
        start_date_obj = self._parse_review_date(start_date)
        end_date_obj = self._parse_review_date(end_date)
        since_date = start_date_obj or last_date
        
        crawl_log = self._create_crawl_log(product.id, platform.id, 'incremental')
        
        try:
            logger.info(f"开始增量爬取: {product_name}, 从 {since_date or '开始'} 到 {end_date_obj or '今天'}")
            crawler = TapTapCrawler(headless=True)
            reviews = crawler.get_reviews(
                game_id,
                max_reviews=2000,
                sort='new',
                since_date=since_date.isoformat() if since_date else None,
                stop_checker=should_stop,
                progress_callback=progress_callback
            )
            crawler.close()
            if callable(should_stop) and should_stop():
                return {"error": "任务已停止"}
            if end_date_obj:
                reviews = [
                    r for r in reviews
                    if self._parse_review_date(r.get('review_date')) and self._parse_review_date(r.get('review_date')) <= end_date_obj
                ]
            reviews_to_analyze = self._filter_new_reviews(reviews, product.id, platform.id)[:MAX_ANALYZE_PER_RUN]

            analyzed_reviews = []
            if reviews_to_analyze:
                logger.info(f"开始AI分析 {len(reviews_to_analyze)} 条评价...")
                analyzer = AliyunAnalyzer()
                for idx, r in enumerate(reviews_to_analyze, start=1):
                    if callable(should_stop) and should_stop():
                        return {"error": "任务已停止"}
                    try:
                        result = analyzer.analyze(r.get('content', ''))
                        r['sentiment'] = result.get('sentiment', '中性')
                        r['problem_category'] = result.get('problem_category', '其他')
                        r['summary'] = result.get('summary', '')
                        analyzed_reviews.append(r)
                    except Exception as e:
                        logger.warning(f"AI分析失败: {e}")
                        r['sentiment'] = '中性'
                        r['problem_category'] = '其他'
                        r['summary'] = ''
                        analyzed_reviews.append(r)
                    if idx % 20 == 0:
                        logger.info(f"AI分析进度: {idx}/{len(reviews_to_analyze)}")
                logger.info(f"AI分析完成")

            added, duplicated = self._save_reviews(analyzed_reviews, product.id, platform.id)

            crawl_log.status = 'success'
            crawl_log.end_time = datetime.now()
            crawl_log.reviews_added = added
            crawl_log.reviews_updated = duplicated
            self.db.commit()

            logger.info(f"增量爬取完成: 新增 {added}, 重复 {duplicated}")
            return {
                "status": "success",
                "last_date": str(last_date) if last_date else None,
                "start_date": since_date.isoformat() if since_date else None,
                "end_date": end_date_obj.isoformat() if end_date_obj else None,
                "added": added,
                "duplicated": duplicated,
                "updated": duplicated,
                "total": len(reviews)
            }
            
        except Exception as e:
            crawl_log.status = 'failed'
            crawl_log.error_message = str(e)
            crawl_log.end_time = datetime.now()
            self.db.commit()
            logger.error(f"增量爬取失败: {e}")
            return {"error": str(e)}
    
    def fill_gaps(
        self,
        product_name: str,
        platform_name: str = 'TapTap',
        days: int = 30,
        should_stop=None,
        progress_callback=None
    ) -> Dict:
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
        
        game_id = self._resolve_game_id(product, product_name)
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
            gap_dates = {d for d in (self._parse_review_date(g) for g in gaps) if d}
            start_gap = min(gap_dates).isoformat() if gap_dates else None
            end_gap = max(gap_dates) if gap_dates else None
            crawler = TapTapCrawler(headless=True)
            reviews = crawler.get_reviews(
                game_id,
                max_reviews=2000,
                sort='new',
                since_date=start_gap,
                stop_checker=should_stop,
                progress_callback=progress_callback
            )
            crawler.close()
            if callable(should_stop) and should_stop():
                return {"error": "任务已停止"}

            gap_reviews = []
            for r in reviews:
                review_date = self._parse_review_date(r.get('review_date'))
                if not review_date:
                    continue
                if review_date in gap_dates and (not end_gap or review_date <= end_gap):
                    gap_reviews.append(r)
            reviews_to_analyze = self._filter_new_reviews(gap_reviews, product.id, platform.id)[:MAX_ANALYZE_PER_RUN]

            analyzed_reviews = []
            if reviews_to_analyze:
                logger.info(f"开始AI分析 {len(reviews_to_analyze)} 条补漏评价...")
                analyzer = AliyunAnalyzer()
                for idx, r in enumerate(reviews_to_analyze, start=1):
                    if callable(should_stop) and should_stop():
                        return {"error": "任务已停止"}
                    try:
                        result = analyzer.analyze(r.get('content', ''))
                        r['sentiment'] = result.get('sentiment', '中性')
                        r['problem_category'] = result.get('problem_category', '其他')
                        r['summary'] = result.get('summary', '')
                        analyzed_reviews.append(r)
                    except Exception as e:
                        logger.warning(f"AI分析失败: {e}")
                        r['sentiment'] = '中性'
                        r['problem_category'] = '其他'
                        r['summary'] = ''
                        analyzed_reviews.append(r)
                    if idx % 20 == 0:
                        logger.info(f"补漏AI分析进度: {idx}/{len(reviews_to_analyze)}")
                logger.info(f"AI分析完成")

            added, duplicated = self._save_reviews(analyzed_reviews, product.id, platform.id)

            crawl_log.status = 'success'
            crawl_log.end_time = datetime.now()
            crawl_log.reviews_added = added
            crawl_log.reviews_updated = duplicated
            self.db.commit()

            logger.info(f"补漏完成: 新增 {added}, 重复 {duplicated}")
            return {
                "status": "success",
                "gaps_found": len(gaps),
                "gaps_filled": len(gap_reviews),
                "added": added,
                "duplicated": duplicated
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
            tuple: (新增数量, 重复数量)
        """
        added = 0
        duplicated = 0
        batch_keys = set()

        for r in reviews:
            user_name = (r.get('user_name') or '').strip()
            content = (r.get('content') or '').strip()
            review_date = self._parse_review_date(r.get('review_date'))
            if not user_name or not content:
                duplicated += 1
                continue

            dedupe_key = f"{review_date.isoformat() if review_date else ''}|{user_name}|{content}"
            if dedupe_key in batch_keys:
                duplicated += 1
                continue

            base_query = self.db.query(Review).filter(
                and_(
                    Review.product_id == product_id,
                    Review.platform_id == platform_id,
                    Review.user_name == user_name,
                    Review.content == content
                )
            )

            if review_date:
                existing = base_query.filter(
                    (Review.review_date == review_date) | (Review.review_date.is_(None))
                ).first()
            else:
                existing = base_query.first()

            if existing:
                duplicated += 1
            else:
                review = Review(
                    product_id=product_id,
                    platform_id=platform_id,
                    review_id=(r.get('review_id') or None),
                    user_name=user_name,
                    content=content,
                    rating=r.get('rating'),
                    review_date=review_date,
                    crawl_date=self._parse_crawl_datetime(r.get('crawl_date')),
                    sentiment=r.get('sentiment'),
                    problem_category=r.get('problem_category'),
                    summary=r.get('summary')
                )
                self.db.add(review)
                added += 1
                batch_keys.add(dedupe_key)

        self.db.commit()
        return added, duplicated

    def _parse_review_date(self, value):
        if not value:
            return None
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            if isinstance(value, datetime):
                return value.date()
            return value
        text = str(value).strip()
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.strptime(text, fmt).date()
            except Exception:
                continue
        return None

    def _parse_crawl_datetime(self, value):
        if not value:
            return datetime.now()
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return datetime.strptime(text, fmt)
            except Exception:
                continue
        return datetime.now()

    def _filter_new_reviews(self, reviews: list, product_id: int, platform_id: int) -> list:
        filtered = []
        seen = set()
        for r in reviews:
            user_name = (r.get('user_name') or '').strip()
            content = (r.get('content') or '').strip()
            review_date = self._parse_review_date(r.get('review_date'))
            if not user_name or not content:
                continue
            dedupe_key = f"{review_date.isoformat() if review_date else ''}|{user_name}|{content}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            base_query = self.db.query(Review).filter(
                and_(
                    Review.product_id == product_id,
                    Review.platform_id == platform_id,
                    Review.user_name == user_name,
                    Review.content == content
                )
            )
            if review_date:
                existing = base_query.filter(
                    (Review.review_date == review_date) | (Review.review_date.is_(None))
                ).first()
            else:
                existing = base_query.first()
            if not existing:
                filtered.append(r)
        return filtered
