# -*- coding: utf-8 -*-
"""
TapTap舆情监控 - 定时调度服务
每2小时自动执行：爬取 -> AI分析 -> 更新数据库 -> 生成词云
"""
import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, init_db
from models.review import Review
from models.product import Product
from models.platform import Platform
from sqlalchemy import and_, not_

# 导入AI分析器
from nlp.glm_analyzer import GLMAnalyzer
from nlp.token_tracker import TokenTracker

# 导入爬虫
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from run_crawler import TapTapCrawler

# 配置
DAILY_TOKEN_LIMIT = 100000  # 每日Token限额
PER_REQUEST_TOKEN_LIMIT = 500  # 单次请求Token限额
MAX_NEW_REVIEWS_PER_RUN = 50  # 每次最多处理新评价数


class TaskLogger:
    """任务执行日志记录器"""
    
    def __init__(self):
        self.log_file = os.path.join(os.path.dirname(__file__), 'logs', 'task_logs.json')
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self.logs = self._load_logs()
    
    def _load_logs(self):
        """加载历史日志"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_logs(self):
        """保存日志"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs[-1000:], f, ensure_ascii=False, indent=2)  # 只保留最近1000条
    
    def log(self, task_type, status, details=None):
        """记录日志"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'task_type': task_type,
            'status': status,
            'details': details or {}
        }
        self.logs.append(entry)
        self._save_logs()
        return entry
    
    def get_today_logs(self):
        """获取今日日志"""
        today = datetime.now().strftime('%Y-%m-%d')
        return [l for l in self.logs if l['timestamp'].startswith(today)]


class SchedulerService:
    """定时调度服务"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.logger = TaskLogger()
        self.token_tracker = TokenTracker()
        self.analyzer = GLMAnalyzer(token_tracker=self.token_tracker)
        self.crawler = None
        self.db = None
        
    async def run_scheduled_task(self):
        """
        执行定时任务
        流程：爬取 -> AI分析 -> 更新数据库 -> 生成词云
        """
        task_start = datetime.now()
        result = {
            'start_time': task_start.isoformat(),
            'status': 'running',
            'steps': {}
        }
        
        try:
            # Step 1: 爬取新评价
            print(f"[{datetime.now()}] Step 1: 开始爬取新评价...")
            new_reviews = await self._crawl_new_reviews()
            result['steps']['crawl'] = {
                'status': 'success',
                'count': len(new_reviews)
            }
            print(f"  爬取到 {len(new_reviews)} 条新评价")
            
            if not new_reviews:
                result['status'] = 'success'
                result['message'] = '没有新评价需要处理'
                self.logger.log('scheduled_task', 'success', result)
                return result
            
            # Step 2: AI分析
            print(f"[{datetime.now()}] Step 2: 开始AI分析...")
            analyzed = await self._analyze_reviews(new_reviews)
            result['steps']['analyze'] = {
                'status': 'success',
                'count': len(analyzed),
                'token_used': self.token_tracker.daily_tokens
            }
            print(f"  分析完成 {len(analyzed)} 条，今日Token: {self.token_tracker.daily_tokens}")
            
            # Step 3: 更新数据库
            print(f"[{datetime.now()}] Step 3: 更新数据库...")
            saved = await self._save_to_db(analyzed)
            result['steps']['save'] = {
                'status': 'success',
                'count': saved
            }
            print(f"  保存 {saved} 条到数据库")
            
            # Step 4: 生成词云
            print(f"[{datetime.now()}] Step 4: 生成词云...")
            await self._generate_wordcloud()
            result['steps']['wordcloud'] = {'status': 'success'}
            print(f"  词云生成完成")
            
            result['status'] = 'success'
            result['end_time'] = datetime.now().isoformat()
            result['duration'] = (datetime.now() - task_start).total_seconds()
            
            self.logger.log('scheduled_task', 'success', result)
            print(f"[{datetime.now()}] 任务完成！耗时: {result['duration']:.1f}秒")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            result['end_time'] = datetime.now().isoformat()
            self.logger.log('scheduled_task', 'failed', result)
            print(f"[{datetime.now()}] 任务失败: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    async def _crawl_new_reviews(self):
        """爬取新评价"""
        try:
            # 获取数据库中最新的评价日期
            db = SessionLocal()
            try:
                latest = db.query(Review).order_by(Review.review_date.desc()).first()
                since_date = latest.review_date if latest else None
            finally:
                db.close()
            
            # 爬取新评价
            self.crawler = TapTapCrawler()
            reviews = await self.crawler.crawl(since_date=since_date, max_count=MAX_NEW_REVIEWS_PER_RUN)
            
            return reviews
        except Exception as e:
            print(f"  爬取失败: {e}")
            return []
    
    async def _analyze_reviews(self, reviews):
        """AI分析评价"""
        analyzed = []
        for review in reviews:
            try:
                # 检查Token限额
                if self.token_tracker.daily_tokens >= DAILY_TOKEN_LIMIT:
                    print(f"  今日Token额度已用完，停止分析")
                    break
                
                # 调用AI分析
                result = self.analyzer.analyze(review.get('content', ''))
                
                analyzed.append({
                    **review,
                    'sentiment': result['sentiment'],
                    'problem_category': result['problem_category'],
                    'summary': result['summary']
                })
                
            except Exception as e:
                print(f"  分析失败 (review_id={review.get('review_id')}): {e}")
        
        return analyzed
    
    async def _save_to_db(self, reviews):
        """保存到数据库"""
        db = SessionLocal()
        try:
            saved = 0
            for r in reviews:
                # 检查是否已存在
                existing = db.query(Review).filter(Review.review_id == r['review_id']).first()
                if existing:
                    continue
                
                # 创建新记录
                review = Review(
                    product_id=1,  # 鹅鸭杀
                    platform_id=1,  # TapTap
                    review_id=r['review_id'],
                    user_name=r.get('user_name'),
                    content=r.get('content'),
                    rating=r.get('rating'),
                    sentiment=r['sentiment'],
                    problem_category=r['problem_category'],
                    summary=r['summary'],
                    review_date=datetime.strptime(r['review_date'], '%Y-%m-%d').date() if r.get('review_date') else None,
                    crawl_date=datetime.now()
                )
                db.add(review)
                saved += 1
            
            db.commit()
            return saved
        finally:
            db.close()
    
    async def _generate_wordcloud(self):
        """生成词云"""
        from scripts.generate_wordcloud import generate_all_wordclouds
        generate_all_wordclouds()
    
    def start(self):
        """启动调度服务"""
        # 每2小时执行一次
        self.scheduler.add_job(
            self.run_scheduled_task,
            CronTrigger(hour='0,2,4,6,8,10,12,14,16,18,20,22', minute=0),
            id='taptap_monitor',
            name='TapTap舆情监控',
            replace_existing=True
        )
        
        self.scheduler.start()
        print("="*50)
        print("TapTap舆情监控定时服务已启动")
        print("="*50)
        print("执行时间: 每天 0,2,4,6,8,10,12,14,16,18,20,22 点")
        
        jobs = self.scheduler.get_jobs()
        if jobs:
            print(f"下次执行时间: {jobs[0].next_run_time}")
    
    def stop(self):
        """停止调度服务"""
        self.scheduler.shutdown()
        print("调度服务已停止")


async def run_once():
    """手动执行一次（测试模式）"""
    service = SchedulerService()
    await service.run_scheduled_task()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='TapTap舆情监控定时服务')
    parser.add_argument('--once', action='store_true', help='只执行一次（测试模式）')
    parser.add_argument('--test', action='store_true', help='测试模式：只分析3条')
    args = parser.parse_args()
    
    if args.once or args.test:
        print("测试模式：执行一次任务...")
        asyncio.run(run_once())
    else:
        # 正常模式：启动调度器
        service = SchedulerService()
        service.start()
        
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            print("\n服务已停止")
            service.stop()
