# -*- coding: utf-8 -*-
"""
爬虫管理 API 路由

提供数据更新入口，支持：
1. 全量爬取：一次性爬取某产品的历史数据
2. 增量更新：从最后爬取日期继续爬到今天
3. 自动补漏：检测并补足缺失日期的数据
"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import Optional, Dict
import logging

from models import get_db, Product, Platform
from services.crawler_service import CrawlerService
from auth_admin import verify_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/crawler", tags=["crawler"])

# 全局爬虫状态
_crawler_status = {
    'running': False,
    'product': None,
    'crawled': 0,
    'analyzed': 0,
    'total': 0,
    'logs': []
}


def get_global_crawler_status():
    """获取全局爬虫状态"""
    return _crawler_status


def update_crawler_status(**kwargs):
    """更新全局爬虫状态"""
    _crawler_status.update(kwargs)


@router.get("/status")
def get_crawler_status(
    product_name: str = Query(default=None, description="产品名称，如：鹅鸭杀"),
    platform_name: str = Query(default="TapTap", description="平台名称"),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    获取爬取状态
    
    返回：
    - running: 是否正在运行
    - product: 当前产品
    - crawled: 已爬取数量
    - analyzed: 已分析数量
    - total: 总数量
    - logs: 日志列表
    """
    verify_admin(authorization, x_admin_token)
    # 如果没有传入product_name，返回全局状态
    if not product_name:
        return _crawler_status
    
    # 否则返回特定产品的状态
    service = CrawlerService(db)
    return service.get_status(product_name, platform_name)


@router.post("/full")
def crawl_full(
    background_tasks: BackgroundTasks,
    product_name: str = Query(..., description="产品名称，如：鹅鸭杀"),
    platform_name: str = Query(default="TapTap", description="平台名称"),
    max_reviews: Optional[int] = Query(default=None, description="最大爬取数量，空表示不限"),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    全量爬取
    
    一次性爬取某产品的历史数据，适合首次爬取或重新爬取。
    后台执行，避免阻塞。
    """
    verify_admin(authorization, x_admin_token)
    service = CrawlerService(db)
    
    # 后台执行
    background_tasks.add_task(
        service.crawl_full,
        product_name=product_name,
        platform_name=platform_name,
        max_reviews=max_reviews
    )
    
    return {
        "status": "started",
        "message": f"开始全量爬取 {product_name} 的 {platform_name} 数据",
        "max_reviews": max_reviews
    }


def _append_log(log_type: str, message: str):
    """添加日志到全局状态"""
    from datetime import datetime
    _crawler_status['logs'].append({
        'type': log_type,
        'message': message,
        'time': datetime.now().isoformat()
    })
    # 只保留最近50条日志
    _crawler_status['logs'] = _crawler_status['logs'][-50:]


def _job_label(job_type: str) -> str:
    mapping = {
        'full': '全量',
        'incremental': '增量',
        'fill_gaps': '补漏'
    }
    return mapping.get(job_type, job_type)


def _run_crawl_task_sync(
    job_type: str,
    product_id: int,
    product_name: str,
    platform_name: str = 'TapTap',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """运行爬虫任务并更新状态（同步版本）"""
    import threading
    
    if _crawler_status.get('running'):
        logger.warning("已有任务在运行中，跳过本次执行")
        return
    
    _crawler_status['running'] = True
    _crawler_status['product'] = product_name
    _crawler_status['crawled'] = 0
    _crawler_status['analyzed'] = 0
    _crawler_status['total'] = 500
    _append_log('info', f'开始{_job_label(job_type)}爬取 {product_name}')
    
    def crawl_worker():
        try:
            from models import SessionLocal
            import concurrent.futures
            db = SessionLocal()
            try:
                service = CrawlerService(db)
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    if job_type == 'incremental':
                        future = executor.submit(
                            service.crawl_incremental,
                            product_name,
                            platform_name,
                            start_date,
                            end_date
                        )
                    elif job_type == 'full':
                        future = executor.submit(service.crawl_full, product_name, platform_name, 8000)
                    else:
                        future = executor.submit(service.fill_gaps, product_name, platform_name)
                    try:
                        result = future.result(timeout=600)
                    except concurrent.futures.TimeoutError:
                        _append_log('error', f'{_job_label(job_type)}任务超时：执行超过10分钟')
                        return
                
                if result.get('error'):
                    _append_log('error', f"{_job_label(job_type)}失败: {result['error']}")
                else:
                    crawled = int(result.get('total', 0))
                    added = int(result.get('added', 0))
                    updated = int(result.get('updated', result.get('duplicated', 0)))
                    _crawler_status['crawled'] = crawled
                    _crawler_status['analyzed'] = crawled
                    _append_log('success', f"{_job_label(job_type)}完成：爬取{crawled}，新增{added}，更新{updated}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"爬虫任务异常: {e}")
            import traceback
            traceback.print_exc()
            _append_log('error', f'{_job_label(job_type)}异常: {str(e)}')
        finally:
            _crawler_status['running'] = False
    
    # 在新线程中运行爬虫
    thread = threading.Thread(target=crawl_worker, daemon=True)
    thread.start()
    return thread


@router.post("/incremental")
def crawl_incremental(
    background_tasks: BackgroundTasks,
    product_id: int = Query(..., description="产品ID"),
    platform_name: str = Query(default="TapTap", description="平台名称"),
    start_date: Optional[str] = Query(default=None, description="开始日期，YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="结束日期，YYYY-MM-DD"),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    增量更新
    
    从数据库中最后爬取日期开始，继续爬到今天。
    适合定期更新数据。
    """
    verify_admin(authorization, x_admin_token)
    # 获取产品名称
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"status": "error", "message": f"产品ID {product_id} 不存在"}
    
    if _crawler_status.get('running'):
        return {"status": "error", "message": "已有任务在运行中"}
    
    # 在新线程中执行爬虫任务
    _run_crawl_task_sync(
        job_type='incremental',
        product_id=product_id,
        product_name=product.name,
        platform_name=platform_name,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "status": "started",
        "message": f"开始增量爬取 {product.name} 的数据（{start_date or '自动'} ~ {end_date or '今天'}）"
    }


@router.post("/fill-gaps")
def fill_gaps(
    background_tasks: BackgroundTasks,
    product_id: int = Query(..., description="产品ID"),
    platform_name: str = Query(default="TapTap", description="平台名称"),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    自动补漏
    
    检测最近30天内缺失的日期，自动补足数据。
    适合爬虫长时间未运行后的数据修复。
    """
    verify_admin(authorization, x_admin_token)
    # 获取产品名称
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"status": "error", "message": f"产品ID {product_id} 不存在"}
    
    if _crawler_status.get('running'):
        return {"status": "error", "message": "已有任务在运行中"}
    
    service = CrawlerService(db)
    
    # 先获取状态
    status = service.get_status(product.name, platform_name)
    
    if status.get("gap_days", 0) == 0:
        return {
            "status": "skipped",
            "message": "没有发现数据缺口，无需补漏"
        }
    
    # 在新线程中执行爬虫任务
    _run_crawl_task_sync(
        job_type='fill_gaps',
        product_id=product_id,
        product_name=product.name,
        platform_name=platform_name
    )
    
    return {
        "status": "started",
        "message": f"开始补漏 {product.name} 的数据缺口",
        "gap_days": status.get("gap_days", 0),
        "gap_dates": status.get("gap_dates", [])
    }


@router.get("/products")
def get_supported_products():
    """
    获取支持爬取的产品列表
    """
    return {
        "products": [
            {"name": "鹅鸭杀", "taptap_id": 258720},
            {"name": "王者荣耀", "taptap_id": 64257},
            {"name": "和平精英", "taptap_id": 36863},
            {"name": "原神", "taptap_id": 168825},
            {"name": "崩坏：星穹铁道", "taptap_id": 224575},
            {"name": "明日方舟", "taptap_id": 52314},
        ]
    }
