# -*- coding: utf-8 -*-
"""
TapTap舆情监控 - FastAPI后端
v1.1版本 - 支持数据库和Excel两种数据源
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np
import os
from datetime import datetime
from collections import Counter
import jieba
import math
from typing import Optional

from api.crawler import router as crawler_router
from models import SessionLocal, init_db, Product, Review, CrawlLog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'output'))

app = FastAPI(title="TapTap舆情监控API", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crawler_router)

if os.path.exists(OUTPUT_DIR):
    app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")


def clean_value(val):
    """清理值，处理NaN和None"""
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    return val


def clean_dict(d):
    """清理字典中的NaN值"""
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = clean_dict(v)
        elif isinstance(v, list):
            result[k] = [clean_value(x) if not isinstance(x, dict) else clean_dict(x) for x in v]
        else:
            result[k] = clean_value(v)
    return result


@app.get("/")
async def root():
    return {"message": "TapTap舆情监控API v1.1", "status": "running"}


@app.get("/api/products")
async def get_products():
    """获取产品列表"""
    try:
        from models import SessionLocal, Product
        db = SessionLocal()
        products = db.query(Product).all()
        db.close()
        return {
            "products": [{"id": p.id, "name": p.name, "code": p.code} for p in products]
        }
    except Exception as e:
        return {"products": [{"id": 1, "name": "鹅鸭杀", "code": "goose_goose_duck"}]}


@app.get("/api/platforms")
async def get_platforms():
    """获取平台列表"""
    try:
        from models import SessionLocal, Platform
        db = SessionLocal()
        platforms = db.query(Platform).all()
        db.close()
        return {
            "platforms": [{"id": p.id, "name": p.name, "code": p.code} for p in platforms]
        }
    except Exception as e:
        return {"platforms": [{"id": 1, "name": "TapTap", "code": "taptap"}]}


@app.get("/api/data")
async def get_data(
    file: str = "鹅鸭杀_GLM分析_v1.1.xlsx",
    product_id: Optional[int] = Query(None, description="产品ID"),
    platform_id: Optional[int] = Query(None, description="平台ID"),
    use_db: bool = Query(True, description="是否使用数据库")
):
    """获取数据 - 支持数据库和Excel两种方式"""
    
    if use_db:
        try:
            return await get_data_from_db(product_id, platform_id)
        except Exception as e:
            print(f"数据库查询失败，回退到Excel: {e}")
    
    return await get_data_from_excel(file)


async def get_data_from_db(product_id: Optional[int], platform_id: Optional[int]):
    """从数据库获取数据"""
    from models import SessionLocal, Review
    
    db = SessionLocal()
    
    try:
        query = db.query(Review)
        
        if product_id:
            query = query.filter(Review.product_id == product_id)
        if platform_id:
            query = query.filter(Review.platform_id == platform_id)
        
        reviews = query.all()
        
        if not reviews:
            raise HTTPException(status_code=404, detail="没有找到数据")
        
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
            {"name": k, "value": v} for k, v in sentiment_count.items()
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
            {"name": k, "value": v, "children": [{"name": sk, "value": sv} for sk, sv in v.items()]}
            for k, v in problem_hierarchy.items()
        ]
        
        stopwords = set(['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                         '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                         '自己', '这', '那', '他', '她', '它', '们', '这个', '那个', '什么', '怎么',
                         '可以', '因为', '所以', '但是', '如果', '还是', '或者', '而且', '然后',
                         '比较', '真的', '非常', '特别', '已经', '一直', '一下', '一些',
                         '觉得', '感觉', '可能', '应该', '需要', '希望', '建议', '游戏', '玩家',
                         '鹅鸭杀', '鹅', '鸭', '杀', '玩', '好玩', '有趣', '不错', '挺好', '太'])
        
        all_text = ' '.join([r.content for r in reviews if r.content])
        words = jieba.cut(all_text)
        word_list = [w for w in words if len(w) >= 2 and w not in stopwords]
        word_counter = Counter(word_list)
        top_words = [{'词语': w, '频次': c} for w, c in word_counter.most_common(20)]
        
        # 从数据库获取周列表（基于实际评价日期）
        from datetime import timedelta
        weeks = []
        if reviews:
            # 获取日期范围
            valid_dates = [r.review_date for r in reviews if r.review_date]
            if valid_dates:
                min_date = min(valid_dates)
                max_date = max(valid_dates)
                
                # 计算所有周
                current_week = min_date - timedelta(days=min_date.weekday())
                end_week = max_date - timedelta(days=max_date.weekday())
                
                while current_week <= end_week:
                    weeks.append(current_week.strftime('%Y-%m-%d'))
                    current_week += timedelta(days=7)
        
        weeks.sort()
        
        reviews_list = []
        for r in reviews[:500]:
            reviews_list.append({
                '日期': r.review_date.isoformat() if r.review_date else None,
                '用户名': r.user_name,
                '星级': r.rating if r.rating else None,
                '情感': r.sentiment,
                '问题分类': r.problem_category,
                '一句话摘要': r.summary,
                '评价内容': r.content
            })
        
        result = {
            'total': total,
            'avgRating': avg_rating,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'neutralNeg': neutral_neg,
            'sentimentDistribution': sentiment_distribution,
            'dates': dates,
            'sentimentTrend': sentiment_trend,
            'dailyCounts': daily_counts,
            'topProblems': top_problems,
            'mainCategories': main_categories,
            'hierarchy': problem_hierarchy,
            'topWords': top_words,
            'weeks': weeks,
            'reviews': reviews_list,
            'weeklyData': [],
            'dataSource': 'database'
        }
        
        return clean_dict(result)
        
    finally:
        db.close()


async def get_data_from_excel(file: str):
    """从Excel获取数据（备用方案）"""
    file_path = os.path.join(OUTPUT_DIR, file)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {file}")
    
    try:
        df_detail = pd.read_excel(file_path, sheet_name='评价明细')
        df_sentiment = pd.read_excel(file_path, sheet_name='情感分布-总体')
        df_daily = pd.read_excel(file_path, sheet_name='情感分布-按天')
        df_weekly = pd.read_excel(file_path, sheet_name='情感分布-按周')
        
        try:
            df_main_cat = pd.read_excel(file_path, sheet_name='问题分类-大类')
        except:
            df_main_cat = pd.DataFrame()
        
        try:
            df_hierarchy = pd.read_excel(file_path, sheet_name='问题分类-层级汇总')
        except:
            df_hierarchy = pd.DataFrame()
        
        df_detail['日期'] = pd.to_datetime(df_detail['日期'], errors='coerce')
        
        def parse_rating(x):
            if pd.isna(x):
                return 0
            try:
                return int(float(str(x).replace('星', '').strip()))
            except:
                return 0
        
        df_detail['星级'] = df_detail['星级'].apply(parse_rating)
        
        sentiment_distribution = []
        for _, row in df_sentiment.iterrows():
            sentiment_distribution.append({
                'name': str(row['情感']) if pd.notna(row.get('情感')) else '',
                'value': int(row['数量']) if pd.notna(row.get('数量')) else 0
            })
        
        dates = df_daily['日期'].dt.strftime('%Y-%m-%d').tolist() if '日期' in df_daily.columns else []
        dates = [d for d in dates if d and d != 'NaT']
        
        sentiment_trend = []
        for col in ['正向', '负向', '中性', '中性偏负']:
            if col in df_daily.columns:
                sentiment_trend.append({
                    'name': col,
                    'data': [int(x) if pd.notna(x) else 0 for x in df_daily[col].tolist()]
                })
        
        daily_counts = df_detail.groupby(df_detail['日期'].dt.strftime('%Y-%m-%d')).size().to_dict()
        daily_counts = [int(daily_counts.get(d, 0)) for d in dates]
        
        stopwords = set(['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                         '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                         '自己', '这', '那', '他', '她', '它', '们', '这个', '那个', '什么', '怎么',
                         '可以', '因为', '所以', '但是', '如果', '还是', '或者', '而且', '然后',
                         '比较', '真的', '非常', '特别', '已经', '一直', '一下', '一些',
                         '觉得', '感觉', '可能', '应该', '需要', '希望', '建议', '游戏', '玩家',
                         '鹅鸭杀', '鹅', '鸭', '杀', '玩', '好玩', '有趣', '不错', '挺好', '太'])
        
        all_text = ' '.join(df_detail['评价内容'].dropna().astype(str))
        words = jieba.cut(all_text)
        word_list = [w for w in words if len(w) >= 2 and w not in stopwords]
        word_counter = Counter(word_list)
        top_words = [{'词语': w, '频次': c} for w, c in word_counter.most_common(20)]
        
        weeks = []
        charts_dir = os.path.join(OUTPUT_DIR, 'charts')
        if os.path.exists(charts_dir):
            for f in os.listdir(charts_dir):
                if f.startswith('词云_') and f.endswith('.png'):
                    week = f.replace('词云_', '').replace('.png', '')
                    weeks.append(week)
            weeks.sort()
        
        main_categories = []
        if not df_main_cat.empty:
            main_categories = df_main_cat.fillna('').to_dict('records')
        
        hierarchy = []
        if not df_hierarchy.empty:
            hierarchy = df_hierarchy.fillna('').to_dict('records')
        
        reviews = []
        for _, row in df_detail.iterrows():
            date_val = row['日期']
            reviews.append({
                '日期': date_val.strftime('%Y-%m-%d') if pd.notna(date_val) else '',
                '用户名': str(row.get('用户名', '')) if pd.notna(row.get('用户名')) else '',
                '星级': int(row['星级']) if pd.notna(row.get('星级')) else 0,
                '情感': str(row.get('情感', '')) if pd.notna(row.get('情感')) else '',
                '问题分类': str(row.get('问题分类', '')) if pd.notna(row.get('问题分类')) else '',
                '一句话摘要': str(row.get('一句话摘要', '')) if pd.notna(row.get('一句话摘要')) else '',
                '评价内容': str(row.get('评价内容', '')) if pd.notna(row.get('评价内容')) else ''
            })
        
        weekly_data = []
        if not df_weekly.empty:
            for _, row in df_weekly.iterrows():
                record = {}
                for col in df_weekly.columns:
                    val = row[col]
                    if pd.isna(val):
                        record[col] = None
                    elif isinstance(val, float):
                        if math.isnan(val) or math.isinf(val):
                            record[col] = None
                        else:
                            record[col] = val
                    else:
                        record[col] = val
                weekly_data.append(record)
        
        result = {
            'total': len(df_detail),
            'avgRating': float(df_detail['星级'].mean()) if '星级' in df_detail.columns and len(df_detail) > 0 else 0,
            'positive': len(df_detail[df_detail['情感'] == '正向']) if '情感' in df_detail.columns else 0,
            'negative': len(df_detail[df_detail['情感'] == '负向']) if '情感' in df_detail.columns else 0,
            'sentimentDistribution': sentiment_distribution,
            'dates': dates,
            'sentimentTrend': sentiment_trend,
            'dailyCounts': daily_counts,
            'topProblems': main_categories[:10],
            'mainCategories': main_categories,
            'hierarchy': hierarchy,
            'topWords': top_words,
            'weeks': weeks,
            'reviews': reviews,
            'weeklyData': weekly_data,
            'dataSource': 'excel'
        }
        
        return clean_dict(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"读取数据失败: {str(e)}")


@app.get("/api/files")
async def get_files():
    """获取可用的Excel文件列表"""
    files = []
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith('.xlsx') and 'GLM分析' in f:
                files.append(f)
    return {"files": files}


@app.get("/api/monitor/status")
async def get_monitor_status():
    """
    获取系统监控状态
    
    Returns:
        系统状态、Token消耗、任务日志等信息
    """
    import json
    from datetime import datetime
    
    # 读取Token使用记录
    token_file = os.path.join(BASE_DIR, 'logs', 'token_usage.json')
    daily_tokens = 0
    total_tokens = 0
    
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                token_logs = json.load(f)
                today = datetime.now().strftime('%Y-%m-%d')
                for entry in token_logs:
                    if entry.get('timestamp', '').startswith(today):
                        daily_tokens += entry.get('total', 0)
                    total_tokens += entry.get('total', 0)
        except:
            pass
    
    # 读取任务日志
    task_log_file = os.path.join(BASE_DIR, 'logs', 'task_logs.json')
    task_logs = []
    today_processed = 0
    
    if os.path.exists(task_log_file):
        try:
            with open(task_log_file, 'r', encoding='utf-8') as f:
                all_logs = json.load(f)
                today = datetime.now().strftime('%Y-%m-%d')
                
                # 过滤今日日志
                for log in all_logs:
                    if log.get('timestamp', '').startswith(today):
                        task_logs.append(log)
                        if log.get('status') == 'success':
                            today_processed += log.get('details', {}).get('saved', 0)
                
                # 只返回最近10条
                task_logs = task_logs[-10:][::-1]
        except:
            pass
    
    # 计算预估费用（GLM-4-flash 约 ¥0.001/1k tokens）
    estimated_cost = round(daily_tokens * 0.001 / 1000, 4)
    
    # 计算下次执行时间
    now = datetime.now()
    current_hour = now.hour
    run_hours = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
    
    next_hour = None
    for h in run_hours:
        if h > current_hour:
            next_hour = h
            break
    
    if next_hour is None:
        next_hour = run_hours[0]  # 第二天0点
    
    next_run = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    if next_hour <= current_hour:
        next_run = next_run.replace(day=now.day + 1)
    
    next_run_time = next_run.strftime('%Y-%m-%d %H:%M')
    
    # 判断系统状态
    system_status = 'running'
    if daily_tokens >= 90000:  # 90%以上
        system_status = 'warning'
    elif task_logs and task_logs[0].get('status') == 'failed':
        system_status = 'error'
    
    return {
        'system_status': system_status,
        'next_run_time': next_run_time,
        'today_processed': today_processed,
        'daily_tokens': daily_tokens,
        'daily_limit': 100000,
        'estimated_cost': str(estimated_cost),
        'task_logs': task_logs
    }


# ========== 产品管理API ==========

@app.get("/api/products")
async def get_products():
    """
    获取所有监控产品列表
    
    Returns:
        products: 产品列表
    """
    init_db()
    db = SessionLocal()
    
    try:
        products = db.query(Product).all()
        return {
            'products': [
                {
                    'id': p.id,
                    'name': p.name,
                    'code': p.code,
                    'platform': 'taptap',
                    'status': 'active',
                    'last_crawl': None,
                    'review_count': db.query(Review).filter(Review.product_id == p.id).count()
                }
                for p in products
            ]
        }
    finally:
        db.close()


@app.get("/api/products/search")
async def search_products(keyword: str = Query(..., min_length=1)):
    """
    搜索产品（模糊匹配）- 使用Playwright真实搜索TapTap
    
    参数:
        keyword: 搜索关键词
        
    返回:
        results: 匹配的产品列表
    """
    from crawler.taptap_search_playwright import search_taptap_game
    
    try:
        results = search_taptap_game(keyword, max_results=10)
        return {'results': results}
    except Exception as e:
        print(f"搜索失败: {e}")
        return {'results': [], 'error': str(e)}


@app.post("/api/products")
async def add_product(name: str, platform: str = 'taptap', code: str = None):
    """
    添加新的监控产品
    
    Args:
        name: 产品名称
        platform: 平台
        code: 产品代码
        
    Returns:
        添加结果
    """
    init_db()
    db = SessionLocal()
    
    try:
        # 检查是否已存在
        existing = db.query(Product).filter(Product.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="产品已存在")
        
        # 创建新产品
        product = Product(
            name=name,
            code=code or name,
        )
        db.add(product)
        db.commit()
        
        return {'success': True, 'id': product.id}
    finally:
        db.close()


@app.post("/api/products/{product_id}/pause")
async def pause_product(product_id: int):
    """
    暂停产品监控
    
    Args:
        product_id: 产品ID
    """
    # TODO: 实现暂停逻辑
    return {'success': True}


# ========== 爬虫控制API ==========

# 导入api/crawler.py中的全局状态
from api.crawler import _crawler_status as crawler_status, update_crawler_status


@app.post("/api/crawler/start")
async def start_crawler(product_id: int, max_count: int = 100):
    """
    启动爬虫任务
    
    Args:
        product_id: 产品ID
        max_count: 最大爬取数量
    """
    global crawler_status
    
    init_db()
    db = SessionLocal()
    
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="产品不存在")
        
        crawler_status['running'] = True
        crawler_status['product'] = product.name
        crawler_status['crawled'] = 0
        crawler_status['analyzed'] = 0
        crawler_status['total'] = max_count
        crawler_status['logs'] = [
            {'type': 'info', 'message': f'开始爬取 {product.name} 的评价...'}
        ]
        
        # TODO: 实际启动爬虫任务
        # 这里应该异步启动爬虫
        
        return {'success': True, 'message': '爬虫任务已启动'}
    finally:
        db.close()


@app.post("/api/crawler/stop")
async def stop_crawler():
    """
    停止爬虫任务
    """
    global crawler_status
    
    crawler_status['running'] = False
    crawler_status['logs'].append({
        'type': 'warning',
        'message': '爬虫任务已停止'
    })
    
    return {'success': True, 'message': '爬虫任务已停止'}


@app.get("/api/data-status")
async def get_data_status(product_id: Optional[int] = Query(None, description="产品ID")):
    """
    获取数据状态
    
    Returns:
        total_reviews: 总评价数
        last_review_date: 最新评价日期
        last_crawl_date: 最后爬取日期
        last_crawl_status: 最后爬取状态
        gap_days: 缺失天数
        gap_dates: 缺失日期列表
    """
    from models import SessionLocal, Review, CrawlLog
    from datetime import timedelta
    
    init_db()
    db = SessionLocal()
    
    try:
        query = db.query(Review)
        if product_id:
            query = query.filter(Review.product_id == product_id)
        
        total_reviews = query.count()
        
        last_review = query.filter(Review.review_date != None).order_by(Review.review_date.desc()).first()
        last_review_date = last_review.review_date.isoformat() if last_review and last_review.review_date else None
        
        crawl_query = db.query(CrawlLog)
        if product_id:
            crawl_query = crawl_query.filter(CrawlLog.product_id == product_id)
        
        last_crawl = crawl_query.order_by(CrawlLog.start_time.desc()).first()
        last_crawl_date = last_crawl.start_time.strftime('%Y-%m-%d %H:%M:%S') if last_crawl and last_crawl.start_time else None
        last_crawl_status = last_crawl.status if last_crawl else '无记录'
        
        gap_days = 0
        gap_dates = []
        
        if last_review_date:
            from datetime import datetime as dt
            last_date = dt.strptime(last_review_date, '%Y-%m-%d').date()
            today = dt.now().date()
            days_diff = (today - last_date).days
            
            if days_diff > 1:
                existing_dates = set(
                    r.review_date for r in query.filter(Review.review_date != None).all()
                )
                
                check_start = today - timedelta(days=30)
                current = check_start
                while current <= today:
                    if current not in existing_dates and current.weekday() < 5:
                        gap_dates.append(current.isoformat())
                    current += timedelta(days=1)
                
                gap_days = len(gap_dates)
        
        return {
            'total_reviews': total_reviews,
            'last_review_date': last_review_date or '无数据',
            'last_crawl_date': last_crawl_date or '无记录',
            'last_crawl_status': last_crawl_status,
            'gap_days': gap_days,
            'gap_dates': gap_dates[:10]
        }
    finally:
        db.close()


@app.get("/api/crawl-logs")
async def get_crawl_logs(
    product_id: Optional[int] = Query(None, description="产品ID"),
    limit: int = Query(20, description="返回条数")
):
    """
    获取爬取日志
    
    Args:
        product_id: 产品ID
        limit: 返回条数
        
    Returns:
        logs: 爬取日志列表
    """
    from models import SessionLocal, CrawlLog
    
    init_db()
    db = SessionLocal()
    
    try:
        query = db.query(CrawlLog)
        if product_id:
            query = query.filter(CrawlLog.product_id == product_id)
        
        logs = query.order_by(CrawlLog.start_time.desc()).limit(limit).all()
        
        return {
            'logs': [
                {
                    'id': log.id,
                    'spider_name': log.spider_name,
                    'start_time': log.start_time.isoformat() if log.start_time else None,
                    'end_time': log.end_time.isoformat() if log.end_time else None,
                    'pages_crawled': log.pages_crawled,
                    'reviews_added': log.reviews_added,
                    'reviews_updated': log.reviews_updated,
                    'errors': log.errors,
                    'status': log.status,
                    'error_message': log.error_message
                }
                for log in logs
            ]
        }
    finally:
        db.close()


@app.post("/api/crawler/incremental")
async def crawl_incremental(
    product_id: int = Query(..., description="产品ID"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期")
):
    """
    增量更新爬取
    
    Args:
        product_id: 产品ID
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        
    Returns:
        任务启动结果
    """
    from models import SessionLocal, Product, Review, CrawlLog
    from datetime import datetime as dt, timedelta
    import asyncio
    import threading
    
    global crawler_status
    
    init_db()
    db = SessionLocal()
    
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="产品不存在")
        
        if not start_date:
            last_review = db.query(Review).filter(
                Review.product_id == product_id
            ).order_by(Review.review_date.desc()).first()
            
            if last_review and last_review.review_date:
                start_date = (last_review.review_date + timedelta(days=1)).isoformat()
            else:
                start_date = (dt.now().date() - timedelta(days=7)).isoformat()
        
        if not end_date:
            end_date = dt.now().date().isoformat()
        
        crawl_log = CrawlLog(
            spider_name='incremental',
            product_id=product_id,
            platform_id=1,
            start_time=dt.now(),
            status='running'
        )
        db.add(crawl_log)
        db.commit()
        
        crawler_status['running'] = True
        crawler_status['product'] = product.name
        crawler_status['crawled'] = 0
        crawler_status['analyzed'] = 0
        crawler_status['total'] = 100
        crawler_status['logs'] = [
            {'type': 'info', 'message': f'开始增量爬取 {product.name} ({start_date} ~ {end_date})'}
        ]
        
        def run_crawler():
            try:
                from scripts.run_crawler import TapTapCrawler
                
                crawler = TapTapCrawler(
                    product_name=product.name,
                    max_reviews=500,
                    target_date=start_date
                )
                reviews = crawler.run()
                
                if reviews:
                    crawler_status['crawled'] = len(reviews)
                    crawler_status['logs'].append({
                        'type': 'success',
                        'message': f'爬取完成，获取 {len(reviews)} 条评价'
                    })
                    
                    crawl_log.reviews_added = len(reviews)
                    crawl_log.end_time = dt.now()
                    crawl_log.status = 'success'
                    db.commit()
                else:
                    crawler_status['logs'].append({
                        'type': 'warning',
                        'message': '未获取到新评价'
                    })
                    crawl_log.end_time = dt.now()
                    crawl_log.status = 'success'
                    crawl_log.reviews_added = 0
                    db.commit()
                    
            except Exception as e:
                crawler_status['logs'].append({
                    'type': 'error',
                    'message': f'爬取失败: {str(e)}'
                })
                crawl_log.end_time = dt.now()
                crawl_log.status = 'failed'
                crawl_log.error_message = str(e)
                db.commit()
            finally:
                crawler_status['running'] = False
        
        thread = threading.Thread(target=run_crawler)
        thread.daemon = True
        thread.start()
        
        return {
            'success': True,
            'message': f'增量更新已启动 ({start_date} ~ {end_date})',
            'crawl_log_id': crawl_log.id
        }
        
    finally:
        db.close()


@app.post("/api/crawler/fill-gaps")
async def fill_gaps(product_id: int = Query(..., description="产品ID")):
    """
    自动补漏
    
    Args:
        product_id: 产品ID
        
    Returns:
        任务启动结果
    """
    from models import SessionLocal, Product, Review, CrawlLog
    from datetime import datetime as dt, timedelta
    
    global crawler_status
    
    init_db()
    db = SessionLocal()
    
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="产品不存在")
        
        existing_dates = set(
            r.review_date for r in db.query(Review).filter(
                Review.product_id == product_id,
                Review.review_date != None
            ).all()
        )
        
        today = dt.now().date()
        check_start = today - timedelta(days=30)
        gap_dates = []
        
        current = check_start
        while current <= today:
            if current not in existing_dates and current.weekday() < 5:
                gap_dates.append(current.isoformat())
            current += timedelta(days=1)
        
        if not gap_dates:
            return {
                'status': 'skipped',
                'message': '没有检测到缺失的日期'
            }
        
        crawl_log = CrawlLog(
            spider_name='fill_gaps',
            product_id=product_id,
            platform_id=1,
            start_time=dt.now(),
            status='running'
        )
        db.add(crawl_log)
        db.commit()
        
        crawler_status['running'] = True
        crawler_status['product'] = product.name
        crawler_status['crawled'] = 0
        crawler_status['analyzed'] = 0
        crawler_status['total'] = len(gap_dates)
        crawler_status['logs'] = [
            {'type': 'info', 'message': f'开始补漏，共 {len(gap_dates)} 天'}
        ]
        
        return {
            'success': True,
            'message': f'补漏任务已启动，共 {len(gap_dates)} 天缺失',
            'gap_dates': gap_dates[:10]
        }
        
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
