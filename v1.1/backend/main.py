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
        
        weeks = []
        charts_dir = os.path.join(OUTPUT_DIR, 'charts')
        if os.path.exists(charts_dir):
            for f in os.listdir(charts_dir):
                if f.startswith('词云_') and f.endswith('.png'):
                    week = f.replace('词云_', '').replace('.png', '')
                    weeks.append(week)
            weeks.sort()
        
        reviews_list = []
        for r in reviews[:500]:
            reviews_list.append({
                '日期': r.review_date.isoformat() if r.review_date else None,
                '用户名': r.user_name,
                '星级': f"{r.rating}星" if r.rating else None,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
