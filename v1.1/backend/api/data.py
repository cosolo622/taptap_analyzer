# -*- coding: utf-8 -*-
"""
数据库 API 路由
从 PostgreSQL 数据库读取数据
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Optional
import math

from models import get_db, Product, Platform, Review

router = APIRouter(prefix="/api", tags=["data"])


def clean_value(val):
    """处理 NaN 值"""
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return round(val, 4)
    return val


def clean_dict(d):
    """清理字典中的 NaN 值"""
    if not d:
        return d
    return {k: clean_value(v) for k, v in d.items()}


@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    """
    获取所有产品列表
    """
    products = db.query(Product).all()
    return {
        "products": [
            {"id": p.id, "name": p.name, "code": p.code}
            for p in products
        ]
    }


@router.get("/platforms")
def get_platforms(db: Session = Depends(get_db)):
    """
    获取所有平台列表
    """
    platforms = db.query(Platform).all()
    return {
        "platforms": [
            {"id": p.id, "name": p.name, "code": p.code}
            for p in platforms
        ]
    }


@router.get("/data")
def get_data(
    product_id: Optional[int] = Query(None, description="产品ID"),
    platform_id: Optional[int] = Query(None, description="平台ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取舆情数据（从数据库）
    """
    query = db.query(Review)
    
    if product_id:
        query = query.filter(Review.product_id == product_id)
    if platform_id:
        query = query.filter(Review.platform_id == platform_id)
    if start_date:
        query = query.filter(Review.review_date >= start_date)
    if end_date:
        query = query.filter(Review.review_date <= end_date)
    
    reviews = query.all()
    
    if not reviews:
        return {"error": "没有找到数据", "total": 0}
    
    total = len(reviews)
    
    ratings = [r.rating for r in reviews if r.rating and r.rating > 0]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    sentiment_count = {}
    for r in reviews:
        if r.sentiment:
            sentiment_count[r.sentiment] = sentiment_count.get(r.sentiment, 0) + 1
    
    positive = sentiment_count.get('正向', 0)
    negative = sentiment_count.get('负向', 0)
    neutral = sentiment_count.get('中性', 0)
    neutral_neg = sentiment_count.get('中性偏负', 0)
    
    sentiment_distribution = [
        {"name": k, "value": v} 
        for k, v in sentiment_count.items()
    ]
    
    date_count = {}
    date_sentiment = {}
    for r in reviews:
        if r.review_date:
            date_str = r.review_date.isoformat()
            date_count[date_str] = date_count.get(date_str, 0) + 1
            if r.sentiment:
                if date_str not in date_sentiment:
                    date_sentiment[date_str] = {}
                date_sentiment[date_str][r.sentiment] = date_sentiment[date_str].get(r.sentiment, 0) + 1
    
    dates = sorted(date_count.keys())
    daily_counts = [date_count[d] for d in dates]
    
    sentiment_trend = {
        "dates": dates,
        "正向": [date_sentiment.get(d, {}).get('正向', 0) for d in dates],
        "负向": [date_sentiment.get(d, {}).get('负向', 0) for d in dates],
        "中性": [date_sentiment.get(d, {}).get('中性', 0) for d in dates],
        "中性偏负": [date_sentiment.get(d, {}).get('中性偏负', 0) for d in dates]
    }
    
    problem_count = {}
    problem_hierarchy = {}
    for r in reviews:
        if r.problem_category:
            parts = r.problem_category.split('-')
            main_cat = parts[0].strip() if parts else r.problem_category
            problem_count[main_cat] = problem_count.get(main_cat, 0) + 1
            
            if main_cat not in problem_hierarchy:
                problem_hierarchy[main_cat] = {}
            if len(parts) > 1:
                sub_cat = '-'.join(parts[:2]).strip()
                problem_hierarchy[main_cat][sub_cat] = problem_hierarchy[main_cat].get(sub_cat, 0) + 1
    
    top_problems = sorted(problem_count.items(), key=lambda x: x[1], reverse=True)[:10]
    top_problems = [{"name": p[0], "value": p[1]} for p in top_problems]
    
    main_categories = [
        {"name": k, "value": v, "children": [
            {"name": sk, "value": sv} for sk, sv in v.items()
        ]}
        for k, v in problem_hierarchy.items()
    ]
    
    reviews_list = []
    for r in reviews[:500]:
        reviews_list.append({
            "日期": r.review_date.isoformat() if r.review_date else None,
            "用户名": r.user_name,
            "星级": f"{r.rating}星" if r.rating else None,
            "情感": r.sentiment,
            "问题分类": r.problem_category,
            "一句话摘要": r.summary,
            "评价内容": r.content
        })
    
    result = {
        "total": total,
        "avgRating": avg_rating,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "neutralNeg": neutral_neg,
        "sentimentDistribution": sentiment_distribution,
        "dates": dates,
        "dailyCounts": daily_counts,
        "sentimentTrend": sentiment_trend,
        "topProblems": top_problems,
        "mainCategories": main_categories,
        "hierarchy": problem_hierarchy,
        "reviews": reviews_list
    }
    
    return clean_dict(result)
