# -*- coding: utf-8 -*-
"""
爬虫管理 API 路由

提供数据更新入口，支持：
1. 全量爬取：一次性爬取某产品的历史数据
2. 增量更新：从最后爬取日期继续爬到今天
3. 自动补漏：检测并补足缺失日期的数据
"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict
import logging

from models import get_db, Product, Platform
from services.crawler_service import CrawlerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/crawler", tags=["crawler"])


@router.get("/status")
def get_crawler_status(
    product_name: str = Query(..., description="产品名称，如：鹅鸭杀"),
    platform_name: str = Query(default="TapTap", description="平台名称"),
    db: Session = Depends(get_db)
):
    """
    获取爬取状态
    
    返回：
    - total_reviews: 总评价数
    - last_review_date: 最新评价日期
    - last_crawl_time: 最后爬取时间
    - gap_days: 缺失天数
    - gap_dates: 缺失日期列表
    """
    service = CrawlerService(db)
    return service.get_status(product_name, platform_name)


@router.post("/full")
def crawl_full(
    background_tasks: BackgroundTasks,
    product_name: str = Query(..., description="产品名称，如：鹅鸭杀"),
    platform_name: str = Query(default="TapTap", description="平台名称"),
    max_reviews: int = Query(default=8000, description="最大爬取数量"),
    db: Session = Depends(get_db)
):
    """
    全量爬取
    
    一次性爬取某产品的历史数据，适合首次爬取或重新爬取。
    后台执行，避免阻塞。
    """
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


@router.post("/incremental")
def crawl_incremental(
    background_tasks: BackgroundTasks,
    product_name: str = Query(..., description="产品名称，如：鹅鸭杀"),
    platform_name: str = Query(default="TapTap", description="平台名称"),
    days: int = Query(default=7, description="爬取最近N天的数据"),
    db: Session = Depends(get_db)
):
    """
    增量更新
    
    从数据库中最后爬取日期开始，继续爬到今天。
    适合定期更新数据。
    """
    service = CrawlerService(db)
    
    # 后台执行
    background_tasks.add_task(
        service.crawl_incremental,
        product_name=product_name,
        platform_name=platform_name,
        days=days
    )
    
    return {
        "status": "started",
        "message": f"开始增量爬取 {product_name} 最近 {days} 天的数据"
    }


@router.post("/fill-gaps")
def fill_gaps(
    background_tasks: BackgroundTasks,
    product_name: str = Query(..., description="产品名称，如：鹅鸭杀"),
    platform_name: str = Query(default="TapTap", description="平台名称"),
    db: Session = Depends(get_db)
):
    """
    自动补漏
    
    检测最近30天内缺失的日期，自动补足数据。
    适合爬虫长时间未运行后的数据修复。
    """
    service = CrawlerService(db)
    
    # 先获取状态
    status = service.get_status(product_name, platform_name)
    
    if status.get("gap_days", 0) == 0:
        return {
            "status": "skipped",
            "message": "没有发现数据缺口，无需补漏"
        }
    
    # 后台执行
    background_tasks.add_task(
        service.fill_gaps,
        product_name=product_name,
        platform_name=platform_name
    )
    
    return {
        "status": "started",
        "message": f"开始补漏 {product_name} 的数据缺口",
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
