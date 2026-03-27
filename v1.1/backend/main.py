# -*- coding: utf-8 -*-
"""
TapTap舆情监控 - FastAPI后端
v1.1版本 - 支持数据库和Excel两种数据源
"""

from fastapi import FastAPI, HTTPException, Query, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np
import os
import glob
import json
import re
from datetime import datetime, timedelta
from collections import Counter
import threading
import time
import subprocess
import jieba
import math
from typing import Optional, List
from sqlalchemy import text
from auth_admin import verify_admin, extract_admin_token, admin_login as do_admin_login, admin_logout as do_admin_logout

from models import SessionLocal, init_db, Product, Review, CrawlLog, Platform, CommunityContent, ContentAITags
from services.crawler_service import CrawlerService

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'output'))
XHS_JSONL_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'MediaCrawler', 'data', 'xhs', 'jsonl'))
XHS_CRAWLER_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'MediaCrawler'))
XHS_RUNTIME_FILE = os.path.join(OUTPUT_DIR, 'xhs_runtime_config.json')

app = FastAPI(title="TapTap舆情监控API", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(OUTPUT_DIR):
    app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")


@app.post("/api/admin/login")
async def admin_login(password: str = Body(..., embed=True)):
    token, expires_at = do_admin_login(password)
    return {
        "success": True,
        "token": token,
        "expires_at": expires_at.isoformat()
    }


@app.get("/api/admin/status")
async def admin_status(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    try:
        verify_admin(authorization, x_admin_token)
        return {"logged_in": True}
    except HTTPException:
        return {"logged_in": False}


@app.post("/api/admin/logout")
async def admin_logout(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    do_admin_logout(authorization, x_admin_token)
    return {"success": True}


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


def parse_social_count(value):
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text_value = str(value).strip().replace('+', '')
    if not text_value:
        return 0
    if text_value.endswith('万'):
        return int(float(text_value[:-1]) * 10000)
    if text_value.endswith('亿'):
        return int(float(text_value[:-1]) * 100000000)
    matched = re.findall(r'\d+(?:\.\d+)?', text_value)
    if not matched:
        return 0
    return int(float(matched[0]))


def get_latest_jsonl_file(prefix: str):
    pattern = os.path.join(XHS_JSONL_DIR, f"{prefix}_*.jsonl")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def read_jsonl_file(file_path: str):
    records = []
    if not file_path or not os.path.exists(file_path):
        return records
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    return records


def _default_xhs_runtime():
    return {
        "monitor_enabled": False,
        "history_enabled": False,
        "interval_minutes": 240,
        "last_run": None,
        "last_mode": None,
        "last_ingest": None,
        "last_result": None,
        "filter_mode": "分层采集",
        "daily_estimate_posts": 1200,
        "daily_estimate_captured": 280
    }


def _load_xhs_runtime():
    try:
        if os.path.exists(XHS_RUNTIME_FILE):
            with open(XHS_RUNTIME_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default = _default_xhs_runtime()
                default.update(data)
                return default
    except Exception:
        pass
    return _default_xhs_runtime()


def _save_xhs_runtime(data: dict):
    os.makedirs(os.path.dirname(XHS_RUNTIME_FILE), exist_ok=True)
    with open(XHS_RUNTIME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


_xhs_runtime = _load_xhs_runtime()
_xhs_auto_update_thread: Optional[threading.Thread] = None
_xhs_auto_update_stop_event = threading.Event()
_xhs_task_lock = threading.Lock()
_xhs_task_status = {
    "running": False,
    "last_error": None
}


def infer_sentiment(text: str):
    negative_words = ['卡顿', '闪退', '掉线', '外挂', '封号', '骗子', '崩溃', '恶心', '垃圾', '失败', '难受', '生气', '糟糕', '风控', '被封', '低素质', '骂人', '有毒']
    positive_words = ['好玩', '喜欢', '推荐', '有趣', '可爱', '精彩', '开心', '神作', '牛', '稳', '顺眼', '良心', '支持', '上头']
    negative_score = sum(1 for w in negative_words if w in text)
    positive_score = sum(1 for w in positive_words if w in text)
    if negative_score > positive_score:
        return '负向'
    if positive_score > negative_score:
        return '正向'
    return '中性'


def infer_topic(text: str):
    mapping = {
        '玩法技巧': ['攻略', '教学', '技巧', '玩法', '阵营', '角色', '地图'],
        '产品口碑': ['好玩', '无聊', '喜欢', '推荐', '体验', '顺眼', '垃圾'],
        '社区生态': ['组队', '队友', '路人', '发言', '低素质', '骂人'],
        '版本活动': ['公测', '上线', '活动', '新春', '版本', '更新'],
        '商业化反馈': ['充值', '氪', '皮肤', '定价', '礼包']
    }
    for topic, words in mapping.items():
        if any(w in text for w in words):
            return topic
    return '其他'


def infer_risk_level(text: str):
    high_risk_words = ['封号', '诈骗', '辱骂', '违法', '崩溃', '恶意']
    medium_risk_words = ['外挂', '掉线', '卡顿', '风控', '冲突', '争议']
    if any(w in text for w in high_risk_words):
        return '高'
    if any(w in text for w in medium_risk_words):
        return '中'
    return '低'


def build_summary(text: str):
    text = re.sub(r'\s+', ' ', text or '').strip()
    if not text:
        return '暂无有效文本'
    return text[:48]


@app.get("/")
async def root():
    return {"message": "TapTap舆情监控API v1.1", "status": "running"}


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


@app.get("/api/xhs/data")
async def get_xhs_data(
    product_id: int = Query(1),
    post_type: Optional[str] = Query(None), # post or comment
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    """
    从数据库获取小红书数据
    """
    db = SessionLocal()
    try:
        query = db.query(CommunityContent).filter(
            CommunityContent.channel == "xiaohongshu",
            CommunityContent.project_id == product_id
        )
        
        if post_type:
            query = query.filter(CommunityContent.post_type == post_type)
            
        if start_date:
            query = query.filter(CommunityContent.publish_time >= start_date)
        if end_date:
            query = query.filter(CommunityContent.publish_time <= end_date)
            
        total = query.count()
        results = query.order_by(CommunityContent.publish_time.desc()).offset(offset).limit(limit).all()
        
        data = []
        for item in results:
            # 关联AI标签
            ai_tags = db.query(ContentAITags).filter(ContentAITags.content_id == item.id).first()
            
            # 计算综合声量: 点赞*1 + 评论*1.5 + 收藏*2 + 分享*2.5
            heat_score = (
                item.interact_likes * 1 +
                item.interact_comments * 1.5 +
                item.interact_collects * 2 +
                item.interact_shares * 2.5
            )
            
            data.append({
                "id": item.id,
                "发布时间": item.publish_time.strftime("%Y-%m-%d %H:%M:%S"),
                "作者": item.author_name,
                "标题": item.content[:100] + "..." if len(item.content) > 100 else item.content,
                "正文": item.content,
                "类型": item.content_type,
                "帖子类型": item.post_type,
                "点赞": item.interact_likes,
                "评论": item.interact_comments,
                "收藏": item.interact_collects,
                "分享": item.interact_shares,
                "综合声量": heat_score,
                "链接": item.url,
                "情感": ai_tags.sentiment if ai_tags else "未知",
                "主题分类": ai_tags.topic_level1 if ai_tags else "其他",
                "风险等级": ai_tags.risk_level if ai_tags else "低"
            })
            
        return {
            "total": total,
            "data": data
        }
    finally:
        db.close()

@app.get("/api/xhs/community")
async def get_xhs_community_data(limit: int = Query(60, ge=20, le=200)):
    notes_file = get_latest_jsonl_file('search_contents')
    comments_file = get_latest_jsonl_file('search_comments')

    notes = read_jsonl_file(notes_file)
    comments = read_jsonl_file(comments_file)

    if not notes:
        raise HTTPException(status_code=404, detail="未找到小红书抓取数据，请先执行抓取任务")

    note_rows = []
    keyword_corpus = []
    topic_counter = Counter()
    sentiment_counter = Counter()
    risk_counter = Counter()

    for note in notes:
        title = (note.get('title') or '').strip()
        desc = (note.get('desc') or '').strip()
        nickname = (note.get('nickname') or '').strip()
        merged_text = f"{title} {desc}".strip()
        liked = parse_social_count(note.get('liked_count'))
        collected = parse_social_count(note.get('collected_count'))
        commented = parse_social_count(note.get('comment_count'))
        shared = parse_social_count(note.get('share_count'))
        sentiment = infer_sentiment(merged_text)
        topic = infer_topic(merged_text)
        risk_level = infer_risk_level(merged_text)
        importance = liked * 1.0 + collected * 1.2 + commented * 1.3 + shared * 1.1
        publish_time = note.get('time')
        publish_dt = None
        if publish_time:
            try:
                publish_dt = datetime.fromtimestamp(int(publish_time) / 1000.0).strftime('%Y-%m-%d %H:%M')
            except Exception:
                publish_dt = None

        row = {
            "平台": "小红书",
            "note_id": note.get('note_id'),
            "标题": title or "无标题",
            "作者": nickname or "未知作者",
            "发布时间": publish_dt,
            "情感": sentiment,
            "主题分类": topic,
            "重要度": round(importance, 2),
            "风险等级": risk_level,
            "点赞": liked,
            "收藏": collected,
            "评论": commented,
            "分享": shared,
            "一句话总结": build_summary(merged_text),
            "链接": note.get('note_url'),
            "原文": merged_text
        }
        note_rows.append(row)
        topic_counter[topic] += 1
        sentiment_counter[sentiment] += 1
        risk_counter[risk_level] += 1
        keyword_corpus.append(merged_text)

    note_rows = sorted(note_rows, key=lambda x: x["重要度"], reverse=True)
    note_rows = note_rows[:limit]

    all_text = ' '.join(keyword_corpus)
    stopwords = {'鹅鸭杀', '手游', '话题', '就是', '一个', '这个', '那个', '我们', '你们', '真的', '可以', '还有', '自己', '没有', '一下', '怎么', '什么', '以及', '因为', '所以', '然后', '非常'}
    tokens = [w for w in jieba.cut(all_text) if len(w) >= 2 and w not in stopwords and not re.match(r'^\d+$', w)]
    top_keywords = [{"关键词": k, "频次": v} for k, v in Counter(tokens).most_common(15)]

    hot_topics = [{"主题": k, "声量": v} for k, v in topic_counter.most_common(8)]
    sentiment_distribution = [{"name": k, "value": v} for k, v in sentiment_counter.items()]
    risk_distribution = [{"等级": k, "数量": v} for k, v in risk_counter.items()]

    risk_samples = []
    for row in note_rows:
        if row["风险等级"] in {"高", "中"}:
            risk_samples.append({
                "标题": row["标题"],
                "风险等级": row["风险等级"],
                "主题分类": row["主题分类"],
                "一句话总结": row["一句话总结"],
                "链接": row["链接"]
            })
    risk_samples = risk_samples[:20]

    feature_copy = [
        "覆盖官方、KOL、普通玩家的真实声音",
        "对语料执行情感分析、关键词提取、重要度评估、风控识别",
        "自动发现热点话题并提供持续追踪与定期解读",
        "结合游戏内行为数据支持运营决策"
    ]

    result = {
        "meta": {
            "notes_file": os.path.basename(notes_file) if notes_file else None,
            "comments_file": os.path.basename(comments_file) if comments_file else None,
            "records_loaded": len(notes),
            "comments_loaded": len(comments),
            "records_returned": len(note_rows)
        },
        "overview": {
            "总帖子数": len(notes),
            "总评论数": len(comments),
            "高风险帖子数": risk_counter.get('高', 0),
            "近似作者数": len(set([(n.get('user_id') or '') for n in notes if n.get('user_id')])),
            "平均重要度": round(sum([r["重要度"] for r in note_rows]) / len(note_rows), 2) if note_rows else 0
        },
        "suite_features": feature_copy,
        "sentiment_distribution": sentiment_distribution,
        "top_keywords": top_keywords,
        "hot_topics": hot_topics,
        "risk_distribution": risk_distribution,
        "risk_samples": risk_samples,
        "records": note_rows
    }
    return clean_dict(result)


@app.get("/api/xhs/ai/config")
async def get_xhs_ai_config():
    return {
        "configured": False,
        "provider": None,
        "message": "AI大模型API尚未配置，请在后续接入模型供应商后启用"
    }


@app.post("/api/xhs/ai/analyze-batch")
async def analyze_xhs_batch(payload: dict = Body(default={})):
    note_ids = payload.get("note_ids", [])
    if not isinstance(note_ids, list):
        raise HTTPException(status_code=400, detail="note_ids 必须为数组")
    return {
        "accepted": True,
        "configured": False,
        "message": "AI分析接口已预留，待配置模型API后可启用",
        "queued_note_count": len(note_ids),
        "provider": None
    }


def _ensure_xhs_platform(db):
    platform = db.query(Platform).filter(Platform.code == 'xiaohongshu').first()
    if not platform:
        platform = Platform(name='小红书', code='xiaohongshu')
        db.add(platform)
        db.commit()
        db.refresh(platform)
    return platform


def _parse_review_date_from_ms(ms):
    try:
        if ms:
            return datetime.fromtimestamp(int(ms) / 1000.0).date()
    except Exception:
        pass
    return datetime.now().date()


def _ingest_xhs_to_db(product_id: int = 1, include_comments: bool = True):
    notes_file = get_latest_jsonl_file('search_contents')
    comments_file = get_latest_jsonl_file('search_comments')
    notes = read_jsonl_file(notes_file)
    comments = read_jsonl_file(comments_file) if include_comments else []
    if not notes and not comments:
        return {"inserted": 0, "updated": 0, "notes": 0, "comments": 0}

    db = SessionLocal()
    inserted = 0
    updated = 0
    try:
        platform = _ensure_xhs_platform(db)

        for item in notes:
            review_id = f"note_{item.get('note_id')}"
            record = db.query(Review).filter(
                Review.platform_id == platform.id,
                Review.review_id == review_id
            ).first()
            merged_text = f"{item.get('title', '')} {item.get('desc', '')}".strip()
            payload = {
                "product_id": product_id,
                "platform_id": platform.id,
                "review_id": review_id,
                "user_name": item.get('nickname') or '未知作者',
                "content": merged_text[:5000],
                "rating": None,
                "sentiment": infer_sentiment(merged_text),
                "problem_category": infer_topic(merged_text),
                "summary": build_summary(merged_text),
                "review_date": _parse_review_date_from_ms(item.get('time')),
                "raw_data": item
            }
            if record:
                for k, v in payload.items():
                    setattr(record, k, v)
                updated += 1
            else:
                db.add(Review(**payload))
                inserted += 1

        for item in comments:
            comment_id = item.get('comment_id')
            if not comment_id:
                continue
            review_id = f"comment_{comment_id}"
            record = db.query(Review).filter(
                Review.platform_id == platform.id,
                Review.review_id == review_id
            ).first()
            content = (item.get('content') or '').strip()
            payload = {
                "product_id": product_id,
                "platform_id": platform.id,
                "review_id": review_id,
                "user_name": item.get('nickname') or '未知作者',
                "content": content[:5000],
                "rating": None,
                "sentiment": infer_sentiment(content),
                "problem_category": infer_topic(content),
                "summary": build_summary(content),
                "review_date": _parse_review_date_from_ms(item.get('create_time')),
                "raw_data": item
            }
            if record:
                for k, v in payload.items():
                    setattr(record, k, v)
                updated += 1
            else:
                db.add(Review(**payload))
                inserted += 1

        db.commit()
        _xhs_runtime["last_ingest"] = datetime.now().isoformat()
        _xhs_runtime["last_result"] = {
            "inserted": inserted,
            "updated": updated,
            "notes": len(notes),
            "comments": len(comments)
        }
        _save_xhs_runtime(_xhs_runtime)
        return {"inserted": inserted, "updated": updated, "notes": len(notes), "comments": len(comments)}
    finally:
        db.close()


def _run_xhs_crawler_once(mode: str = "incremental"):
    command = ["python", "main.py"]
    result = subprocess.run(
        command,
        cwd=XHS_CRAWLER_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=1200
    )
    ok = result.returncode == 0
    return {
        "ok": ok,
        "mode": mode,
        "returncode": result.returncode,
        "stdout_tail": (result.stdout or "")[-1000:],
        "stderr_tail": (result.stderr or "")[-1000:]
    }


def _xhs_auto_update_worker():
    while not _xhs_auto_update_stop_event.is_set():
        if _xhs_runtime.get("monitor_enabled") and not _xhs_task_status.get("running"):
            try:
                _xhs_task_status["running"] = True
                crawl_result = _run_xhs_crawler_once("incremental")
                ingest_result = _ingest_xhs_to_db(product_id=1, include_comments=True)
                _xhs_runtime["last_run"] = datetime.now().isoformat()
                _xhs_runtime["last_mode"] = "incremental"
                _xhs_runtime["last_result"] = {
                    "crawl": crawl_result,
                    "ingest": ingest_result
                }
                _save_xhs_runtime(_xhs_runtime)
            except Exception as e:
                _xhs_task_status["last_error"] = str(e)
            finally:
                _xhs_task_status["running"] = False
        interval_seconds = int(_xhs_runtime.get("interval_minutes", 240)) * 60
        _xhs_auto_update_stop_event.wait(interval_seconds)


def _ensure_xhs_worker_state():
    global _xhs_auto_update_thread
    if _xhs_runtime.get("monitor_enabled"):
        if not _xhs_auto_update_thread or not _xhs_auto_update_thread.is_alive():
            _xhs_auto_update_stop_event.clear()
            _xhs_auto_update_thread = threading.Thread(target=_xhs_auto_update_worker, daemon=True)
            _xhs_auto_update_thread.start()
    else:
        _xhs_auto_update_stop_event.set()


@app.get("/api/xhs/crawler/status")
async def get_xhs_crawler_status():
    records = read_jsonl_file(get_latest_jsonl_file('search_contents'))
    total_today = 0
    today = datetime.now().strftime("%Y-%m-%d")
    for item in records:
        try:
            t = datetime.fromtimestamp(int(item.get('time', 0)) / 1000.0).strftime("%Y-%m-%d")
            if t == today:
                total_today += 1
        except Exception:
            continue
    return {
        "runtime": _xhs_runtime,
        "task": _xhs_task_status,
        "today_posts_in_sample": total_today,
        "latest_notes_file": os.path.basename(get_latest_jsonl_file('search_contents') or ""),
        "latest_comments_file": os.path.basename(get_latest_jsonl_file('search_comments') or "")
    }


@app.post("/api/xhs/crawler/settings")
async def update_xhs_crawler_settings(payload: dict = Body(default={})):
    monitor_enabled = payload.get("monitor_enabled")
    history_enabled = payload.get("history_enabled")
    interval_minutes = payload.get("interval_minutes")
    filter_mode = payload.get("filter_mode")

    if isinstance(monitor_enabled, bool):
        _xhs_runtime["monitor_enabled"] = monitor_enabled
    if isinstance(history_enabled, bool):
        _xhs_runtime["history_enabled"] = history_enabled
    if isinstance(interval_minutes, int):
        _xhs_runtime["interval_minutes"] = max(60, min(interval_minutes, 720))
    if isinstance(filter_mode, str) and filter_mode:
        _xhs_runtime["filter_mode"] = filter_mode

    _save_xhs_runtime(_xhs_runtime)
    _ensure_xhs_worker_state()
    return {"success": True, "runtime": _xhs_runtime}


@app.post("/api/xhs/crawler/run-now")
async def run_xhs_incremental_now():
    if _xhs_task_status.get("running"):
        raise HTTPException(status_code=409, detail="小红书任务正在运行")
    with _xhs_task_lock:
        _xhs_task_status["running"] = True
        try:
            crawl_result = _run_xhs_crawler_once("incremental")
            ingest_result = _ingest_xhs_to_db(product_id=1, include_comments=True)
            _xhs_runtime["last_run"] = datetime.now().isoformat()
            _xhs_runtime["last_mode"] = "incremental"
            _xhs_runtime["last_result"] = {"crawl": crawl_result, "ingest": ingest_result}
            _save_xhs_runtime(_xhs_runtime)
            return {"success": True, "crawl": crawl_result, "ingest": ingest_result}
        finally:
            _xhs_task_status["running"] = False


@app.post("/api/xhs/crawler/run-history")
async def run_xhs_history_now(days_back: int = Query(30, ge=1, le=180)):
    if _xhs_task_status.get("running"):
        raise HTTPException(status_code=409, detail="小红书任务正在运行")
    with _xhs_task_lock:
        _xhs_task_status["running"] = True
        try:
            crawl_result = _run_xhs_crawler_once("history")
            ingest_result = _ingest_xhs_to_db(product_id=1, include_comments=True)
            _xhs_runtime["last_run"] = datetime.now().isoformat()
            _xhs_runtime["last_mode"] = f"history_{days_back}d"
            _xhs_runtime["last_result"] = {"crawl": crawl_result, "ingest": ingest_result}
            _save_xhs_runtime(_xhs_runtime)
            return {"success": True, "days_back": days_back, "crawl": crawl_result, "ingest": ingest_result}
        finally:
            _xhs_task_status["running"] = False


@app.get("/api/xhs/strategy/estimate")
async def get_xhs_strategy_estimate():
    sample_records = read_jsonl_file(get_latest_jsonl_file('search_contents'))
    sample_size = len(sample_records)
    estimated_daily_total = max(sample_size * 8, _xhs_runtime.get("daily_estimate_posts", 1200))
    if _xhs_runtime.get("filter_mode") == "全量":
        estimated_capture = estimated_daily_total
        risk_level = "高"
    else:
        estimated_capture = min(int(estimated_daily_total * 0.25), max(sample_size, 300))
        risk_level = "中"
    return {
        "strategy": {
            "filter_mode": _xhs_runtime.get("filter_mode"),
            "recommendation": "分层采集：先抓卡片元数据，再对高价值帖子深抓正文与评论"
        },
        "estimate": {
            "sample_records": sample_size,
            "estimated_daily_total_posts": estimated_daily_total,
            "estimated_daily_captured_posts": estimated_capture,
            "crawl_runs_per_day": int(24 * 60 / max(1, int(_xhs_runtime.get("interval_minutes", 240)))),
            "account_risk_level": risk_level
        },
        "policy": {
            "mode_all_posts": "不建议长期全量抓取，封禁风险高且水帖占比高",
            "mode_filtered": "建议关键词+热度+时间分层抓取，并保留负面主题优先队列"
        }
    }


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
        
        from datetime import timedelta
        weeks = []
        if reviews:
            valid_dates = [r.review_date for r in reviews if r.review_date]
            if valid_dates:
                min_date = min(valid_dates)
                max_date = max(valid_dates)
                
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
async def get_monitor_status(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    """
    获取系统监控状态
    
    Returns:
        系统状态、Token消耗、任务日志等信息
    """
    verify_admin(authorization, x_admin_token)
    import json
    from datetime import datetime
    
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
    
    task_log_file = os.path.join(BASE_DIR, 'logs', 'task_logs.json')
    task_logs = []
    today_processed = 0
    
    if os.path.exists(task_log_file):
        try:
            with open(task_log_file, 'r', encoding='utf-8') as f:
                all_logs = json.load(f)
                today = datetime.now().strftime('%Y-%m-%d')
                
                for log in all_logs:
                    if log.get('timestamp', '').startswith(today):
                        task_logs.append(log)
                        if log.get('status') == 'success':
                            today_processed += log.get('details', {}).get('saved', 0)
                
                task_logs = task_logs[-10:][::-1]
        except:
            pass
    
    estimated_cost = round(daily_tokens * 0.001 / 1000, 4)
    
    now = datetime.now()
    current_hour = now.hour
    run_hours = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
    
    next_hour = None
    for h in run_hours:
        if h > current_hour:
            next_hour = h
            break
    
    if next_hour is None:
        next_hour = run_hours[0]
    
    next_run = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    if next_hour <= current_hour:
        next_run = next_run.replace(day=now.day + 1)
    
    next_run_time = next_run.strftime('%Y-%m-%d %H:%M')
    
    system_status = 'running'
    if daily_tokens >= 90000:
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
    from crawler.taptap_search_playwright import search_taptap_game as search_v2

    keyword_norm = re.sub(r'\s+', '', keyword).lower()

    def score_and_filter(items):
        scored = []
        for item in items:
            name_norm = re.sub(r'\s+', '', (item.get('name') or '')).lower()
            score = 0
            if name_norm == keyword_norm:
                score += 100
            if keyword_norm and keyword_norm in name_norm:
                score += 60
            for token in re.split(r'[\s·\-_/]+', keyword_norm):
                if token and token in name_norm:
                    score += 10
            scored.append((score, item))
        scored.sort(key=lambda x: (x[0], x[1].get('rating', 0)), reverse=True)
        strict = [item for score, item in scored if score >= 60]
        if strict:
            return strict[:10]
        return []

    try:
        results = search_v2(keyword, max_results=20)
        filtered = score_and_filter(results)
        return {'results': filtered}
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
        existing = db.query(Product).filter(Product.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="产品已存在")
        
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
    return {'success': True}


from api.crawler import _crawler_status as crawler_status, update_crawler_status

_crawler_lock = threading.Lock()
_crawl_stop_event = threading.Event()
_auto_update_thread: Optional[threading.Thread] = None
_auto_update_stop_event = threading.Event()
_auto_update_status = {
    'running': False,
    'product_id': 1,
    'interval_minutes': 1,  # 测试时改为1分钟
    'last_run': None,
    'last_result': None
}


def _append_crawler_log(log_type: str, message: str):
    crawler_status.setdefault('logs', [])
    crawler_status['logs'].append({
        'type': log_type,
        'message': message,
        'time': datetime.now().isoformat()
    })
    crawler_status['logs'] = crawler_status['logs'][-50:]


def _job_label(job_type: str) -> str:
    mapping = {
        'full': '全量',
        'incremental': '增量',
        'fill_gaps': '补漏'
    }
    return mapping.get(job_type, job_type)


def _close_running_crawl_logs(reason: str = '任务已停止', product_id: Optional[int] = None):
    db = SessionLocal()
    try:
        query = db.query(CrawlLog).filter(CrawlLog.status == 'running', CrawlLog.end_time.is_(None))
        if product_id:
            query = query.filter(CrawlLog.product_id == product_id)
        running_logs = query.all()
        if not running_logs:
            return 0
        now = datetime.now()
        for log in running_logs:
            log.status = 'failed'
            log.end_time = now
            if not log.error_message:
                log.error_message = reason
        db.commit()
        return len(running_logs)
    finally:
        db.close()


def _run_crawler_job(
    job_type: str,
    product_id: int,
    max_count: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """运行爬虫任务，带超时机制"""
    import concurrent.futures
    
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            _append_crawler_log('error', f'产品不存在: {product_id}')
            return

        crawler_status['running'] = True
        _crawl_stop_event.clear()
        crawler_status['product'] = product.name
        crawler_status['crawled'] = 0
        crawler_status['analyzed'] = 0
        crawler_status['total'] = max_count or 0
        _append_crawler_log('info', f'开始{_job_label(job_type)}爬取 {product.name}')

        service = CrawlerService(db)
        def _on_progress(count: int):
            crawler_status['crawled'] = int(count or 0)
        
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            _execute_crawl,
            service,
            job_type,
            product.name,
            max_count,
            start_date,
            end_date,
            lambda: _crawl_stop_event.is_set(),
            _on_progress
        )
        total_wait = 0
        while True:
            try:
                result = future.result(timeout=30)
                break
            except concurrent.futures.TimeoutError:
                total_wait += 30
                if _crawl_stop_event.is_set():
                    _append_crawler_log('warning', f'{_job_label(job_type)}停止中：正在强制结束任务线程')
                    future.cancel()
                    executor.shutdown(wait=False, cancel_futures=True)
                    crawler_status['running'] = False
                    return
                _append_crawler_log('info', f'{_job_label(job_type)}进行中：已运行 {total_wait} 秒，当前抓取 {crawler_status.get("crawled", 0)} 条')
                if total_wait >= 3600:
                    _append_crawler_log('error', f'{_job_label(job_type)}任务超时：执行超过60分钟')
                    crawler_status['running'] = False
                    future.cancel()
                    executor.shutdown(wait=False, cancel_futures=True)
                    return
        executor.shutdown(wait=False, cancel_futures=True)

        if result.get('error'):
            _append_crawler_log('error', f"{_job_label(job_type)}失败: {result['error']}")
        else:
            crawled = int(result.get('total', 0))
            added = int(result.get('added', 0))
            updated = int(result.get('updated', result.get('duplicated', 0)))
            crawler_status['crawled'] = crawled
            crawler_status['analyzed'] = crawled
            _append_crawler_log('success', f"{_job_label(job_type)}完成：爬取{crawled}，新增{added}，更新{updated}")
            _auto_update_status['last_result'] = {
                'status': result.get('status', 'success'),
                'total': crawled,
                'added': added,
                'updated': updated
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        _append_crawler_log('error', f'{_job_label(job_type)}异常: {str(e)}')
    finally:
        crawler_status['running'] = False
        _crawl_stop_event.clear()
        db.close()


def _execute_crawl(service, job_type, product_name, max_count, start_date=None, end_date=None, should_stop=None, progress_callback=None):
    """执行爬虫任务（用于线程池）"""
    try:
        if job_type == 'full':
            return service.crawl_full(
                product_name,
                max_reviews=max_count,
                should_stop=should_stop,
                progress_callback=progress_callback
            )
        elif job_type == 'incremental':
            return service.crawl_incremental(
                product_name,
                start_date=start_date,
                end_date=end_date,
                should_stop=should_stop,
                progress_callback=progress_callback
            )
        else:
            return service.fill_gaps(
                product_name,
                should_stop=should_stop,
                progress_callback=progress_callback
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def _start_crawler_thread(
    job_type: str,
    product_id: int,
    max_count: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    if crawler_status.get('running'):
        return False
    _crawl_stop_event.clear()

    def task():
        with _crawler_lock:
            _run_crawler_job(
                job_type=job_type,
                product_id=product_id,
                max_count=max_count,
                start_date=start_date,
                end_date=end_date
            )

    thread = threading.Thread(target=task, daemon=True)
    thread.start()
    return True


def _auto_update_worker():
    while not _auto_update_stop_event.is_set():
        if not crawler_status.get('running'):
            today = datetime.now().strftime('%Y-%m-%d')
            # 使用线程启动爬虫任务，避免阻塞
            started = _start_crawler_thread(
                job_type='incremental',
                product_id=_auto_update_status['product_id'],
                max_count=500,
                start_date=today,
                end_date=today
            )
            if started:
                _auto_update_status['last_run'] = datetime.now().isoformat()
        # 等待间隔时间
        wait_seconds = int(_auto_update_status['interval_minutes']) * 60
        _auto_update_stop_event.wait(wait_seconds)


@app.post("/api/crawler/start")
async def start_crawler(
    product_id: int,
    max_count: Optional[int] = None,
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    """
    启动爬虫任务
    
    Args:
        product_id: 产品ID
        max_count: 最大爬取数量
    """
    verify_admin(authorization, x_admin_token)
    started = _start_crawler_thread('full', product_id, max_count)
    if not started:
        raise HTTPException(status_code=409, detail="已有任务在运行中")
    return {'success': True, 'message': '爬虫任务已启动'}


@app.post("/api/crawler/stop")
async def stop_crawler(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    """
    停止爬虫任务
    """
    verify_admin(authorization, x_admin_token)
    _crawl_stop_event.set()
    crawler_status['running'] = False
    closed = _close_running_crawl_logs('任务被手动停止')
    _append_crawler_log('warning', '已请求停止任务，正在终止当前步骤')
    return {'success': True, 'message': '爬虫任务已停止', 'logs_closed': closed}


@app.get("/api/reviews/delete-by-date")
async def delete_reviews_by_date(
    product_id: int = Query(..., description="产品ID"),
    start_date: str = Query(..., description="开始日期YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期YYYY-MM-DD"),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    """
    删除指定日期范围内的评论
    """
    from models import Review, SessionLocal
    from datetime import datetime

    verify_admin(authorization, x_admin_token)
    db = SessionLocal()
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    deleted = db.query(Review).filter(
        Review.product_id == product_id,
        Review.review_date >= start,
        Review.review_date <= end
    ).delete()
    db.commit()
    db.close()

    logger.info(f"删除评论: 产品{product_id}, 日期{start_date}至{end_date}, 共{deleted}条")
    return {'success': True, 'deleted': deleted}


@app.post("/api/auto-update/start")
async def start_auto_update(
    product_id: int = Query(1, description="产品ID"),
    interval_minutes: int = Query(120, ge=1, le=1440, description="执行间隔（分钟）"),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    global _auto_update_thread
    verify_admin(authorization, x_admin_token)
    if _auto_update_status['running']:
        return {'success': True, 'message': '自动更新已在运行中', 'status': _auto_update_status}
    _auto_update_status['running'] = True
    _auto_update_status['product_id'] = product_id
    _auto_update_status['interval_minutes'] = interval_minutes
    _auto_update_stop_event.clear()
    _auto_update_thread = threading.Thread(target=_auto_update_worker, daemon=True)
    _auto_update_thread.start()
    return {'success': True, 'message': '自动更新已启动', 'status': _auto_update_status}


@app.post("/api/auto-update/stop")
async def stop_auto_update(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    verify_admin(authorization, x_admin_token)
    _auto_update_status['running'] = False
    _auto_update_stop_event.set()
    return {'success': True, 'message': '自动更新已停止', 'status': _auto_update_status}


@app.get("/api/auto-update/status")
async def auto_update_status(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    verify_admin(authorization, x_admin_token)
    return {'status': _auto_update_status}


@app.get("/api/data-status")
async def get_data_status(
    product_id: Optional[int] = Query(None, description="产品ID"),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
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
    verify_admin(authorization, x_admin_token)
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
    limit: int = Query(20, description="返回条数"),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    """
    获取爬取日志
    
    Args:
        product_id: 产品ID
        limit: 返回条数
        
    Returns:
        logs: 爬取日志列表
    """
    verify_admin(authorization, x_admin_token)
    from models import SessionLocal, CrawlLog
    
    init_db()
    db = SessionLocal()
    
    try:
        if not crawler_status.get('running'):
            _close_running_crawl_logs('任务状态异常自动收敛', product_id=product_id)
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


@app.get("/api/crawler/status")
async def get_crawler_status(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    verify_admin(authorization, x_admin_token)
    return crawler_status


@app.post("/api/crawler/incremental")
async def crawl_incremental(
    product_id: int = Query(..., description="产品ID"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
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
    verify_admin(authorization, x_admin_token)
    started = _start_crawler_thread('incremental', product_id, 500, start_date=start_date, end_date=end_date)
    if not started:
        raise HTTPException(status_code=409, detail="已有任务在运行中")
    return {
        'success': True,
        'message': f'增量更新已启动 ({start_date or "自动"} ~ {end_date or "今天"})'
    }


@app.post("/api/crawler/fill-gaps")
async def fill_gaps(
    product_id: int = Query(..., description="产品ID"),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    """
    自动补漏
    
    Args:
        product_id: 产品ID
        
    Returns:
        任务启动结果
    """
    verify_admin(authorization, x_admin_token)
    started = _start_crawler_thread('fill_gaps', product_id, 500)
    if not started:
        raise HTTPException(status_code=409, detail="已有任务在运行中")
    return {
        'success': True,
        'message': '补漏任务已启动'
    }


@app.get("/api/admin/db/overview")
async def db_overview(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    verify_admin(authorization, x_admin_token)
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            select table_name, column_name, data_type
            from information_schema.columns
            where table_schema='public'
            order by table_name, ordinal_position
        """)).fetchall()
        table_columns = {}
        for table_name, column_name, data_type in rows:
            table_columns.setdefault(table_name, []).append({
                "name": column_name,
                "type": data_type
            })
        table_stats = []
        for table_name, columns in table_columns.items():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                continue
            count_sql = text(f'select count(*) from "{table_name}"')
            row_count = db.execute(count_sql).scalar() or 0
            table_stats.append({
                "table_name": table_name,
                "row_count": int(row_count),
                "column_count": len(columns),
                "columns": columns
            })
        table_stats.sort(key=lambda x: x["table_name"])
        return {"tables": table_stats}
    finally:
        db.close()


@app.post("/api/admin/db/query")
async def db_query(
    sql: str = Body(..., embed=True),
    limit: int = Body(200, embed=True),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    verify_admin(authorization, x_admin_token)
    raw_sql = (sql or "").strip().rstrip(";")
    lower_sql = raw_sql.lower()
    if not raw_sql:
        raise HTTPException(status_code=400, detail="SQL不能为空")
    if not (lower_sql.startswith("select") or lower_sql.startswith("with") or lower_sql.startswith("explain")):
        raise HTTPException(status_code=400, detail="当前只允许查询类SQL")
    limit = max(1, min(int(limit), 1000))
    wrapped_sql = text(f"select * from ({raw_sql}) as q limit {limit}")
    db = SessionLocal()
    try:
        result = db.execute(wrapped_sql)
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return {"columns": columns, "rows": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL执行失败: {e}")
    finally:
        db.close()


@app.post("/api/admin/db/deduplicate")
async def db_deduplicate(
    fields: List[str] = Body(..., embed=True),
    product_id: Optional[int] = Body(None, embed=True),
    platform_id: Optional[int] = Body(None, embed=True),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    verify_admin(authorization, x_admin_token)
    field_expr_map = {
        "date": "coalesce(review_date::text,'')",
        "name": "coalesce(trim(user_name),'')",
        "content": "coalesce(trim(content),'')",
        "rating": "coalesce(rating::text,'')",
        "review_id": "coalesce(review_id,'')"
    }
    normalized_fields = [f for f in fields if f in field_expr_map]
    if not normalized_fields:
        raise HTTPException(status_code=400, detail="去重字段不能为空")
    partition_expr = ", ".join(field_expr_map[f] for f in normalized_fields)
    where_parts = []
    params = {}
    if product_id:
        where_parts.append("product_id = :product_id")
        params["product_id"] = product_id
    if platform_id:
        where_parts.append("platform_id = :platform_id")
        params["platform_id"] = platform_id
    where_sql = f"where {' and '.join(where_parts)}" if where_parts else ""
    dedupe_sql = text(f"""
        with ranked as (
            select id, row_number() over (
                partition by product_id, platform_id, {partition_expr}
                order by id
            ) rn
            from reviews
            {where_sql}
        )
        delete from reviews r
        using ranked d
        where r.id = d.id and d.rn > 1
        returning r.id
    """)
    db = SessionLocal()
    try:
        result = db.execute(dedupe_sql, params)
        deleted = len(result.fetchall())
        db.commit()
        return {
            "success": True,
            "deleted": deleted,
            "fields": normalized_fields
        }
    finally:
        db.close()


@app.post("/api/admin/db/delete-by-date")
async def db_delete_by_date(
    product_id: int = Body(..., embed=True),
    start_date: str = Body(..., embed=True),
    end_date: str = Body(..., embed=True),
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None)
):
    verify_admin(authorization, x_admin_token)
    db = SessionLocal()
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        deleted = db.query(Review).filter(
            Review.product_id == product_id,
            Review.review_date >= start,
            Review.review_date <= end
        ).delete()
        db.commit()
        return {"success": True, "deleted": int(deleted)}
    finally:
        db.close()


# ========== 服务启动时自动开启自动更新 ==========
@app.on_event("startup")
async def startup_event():
    """服务启动时自动开启自动更新"""
    global _auto_update_thread
    if not _auto_update_status['running']:
        _auto_update_status['running'] = True
        _auto_update_status['product_id'] = 1  # 默认产品ID
        _auto_update_status['interval_minutes'] = 240  # 统一先按4小时
        _auto_update_stop_event.clear()
        _auto_update_thread = threading.Thread(target=_auto_update_worker, daemon=True)
        _auto_update_thread.start()
        print("=" * 50)
        print("自动更新已启动")
        print("间隔: 240 分钟")
        print("=" * 50)
    _ensure_xhs_worker_state()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
