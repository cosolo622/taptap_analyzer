# -*- coding: utf-8 -*-
"""
定时调度服务 - TapTap舆情监控
功能：每2小时自动执行爬取、AI分析、更新数据库
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, init_db
from models.review import Review
from models.product import Product
from models.platform import Platform

# 配置
DAILY_TOKEN_LIMIT = 100000  # 每日Token上限
PER_REQUEST_TOKEN_LIMIT = 2000  # 单次请求Token上限
MAX_REVIEWS_PER_RUN = 50  # 每次运行最大处理评价数


class TokenTracker:
    """Token消耗追踪器"""
    
    def __init__(self):
        self.total_tokens = 0
        self.daily_tokens = 0
        self.logs = []
        self.log_file = os.path.join(os.path.dirname(__file__), 'token_usage.json')
        self.load_from_file()
    
    def load_from_file(self):
        """从文件加载历史记录"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.total_tokens = data.get('total_tokens', 0)
                    self.logs = data.get('logs', [])
                    
                    # 检查今日记录
                    today = datetime.now().strftime('%Y-%m-%d')
                    self.daily_tokens = sum(
                        log.get('total', 0) 
                        for log in self.logs 
                        if log.get('timestamp', '').startswith(today)
                    )
            except:
                pass
    
    def save_to_file(self):
        """保存到文件"""
        data = {
            'total_tokens': self.total_tokens,
            'logs': self.logs[-1000:]  # 只保留最近1000条
        }
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def log_usage(self, prompt_tokens, completion_tokens, model, review_id=None):
        """
        记录一次API调用的token消耗
        
        Args:
            prompt_tokens: 输入token数
            completion_tokens: 输出token数
            model: 使用的模型
            review_id: 关联的评价ID
        """
        total = prompt_tokens + completion_tokens
        self.total_tokens += total
        self.daily_tokens += total
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total': total,
            'model': model,
            'review_id': review_id,
            'daily_total': self.daily_tokens
        }
        
        self.logs.append(log_entry)
        self.save_to_file()
        
        return log_entry
    
    def can_request(self, estimated_tokens):
        """检查是否可以发起请求"""
        if self.daily_tokens >= DAILY_TOKEN_LIMIT:
            return False, f"今日Token额度已用完: {self.daily_tokens}/{DAILY_TOKEN_LIMIT}"
        if estimated_tokens > PER_REQUEST_TOKEN_LIMIT:
            return False, f"单次请求超过限制: {estimated_tokens} > {PER_REQUEST_TOKEN_LIMIT}"
        return True, "OK"
    
    def get_daily_report(self):
        """获取每日报告"""
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_tokens': self.daily_tokens,
            'limit': DAILY_TOKEN_LIMIT,
            'remaining': DAILY_TOKEN_LIMIT - self.daily_tokens,
            'usage_rate': f"{self.daily_tokens / DAILY_TOKEN_LIMIT * 100:.1f}%"
        }


class GLMAnalyzer:
    """智谱GLM-5 情感分析器"""
    
    SYSTEM_PROMPT = """你是一个专业的游戏评价分析师。你的任务是分析TapTap游戏评价。

## 输出要求
严格按照以下JSON格式输出，不要输出其他内容：
{"sentiment": "情感值", "problem_category": "问题分类", "summary": "一句话总结"}

## 情感值选项
- 正向：表达满意、喜欢、推荐
- 负向：表达不满、批评、抱怨
- 中性：客观陈述，无明显情感倾向

## 问题分类选项（选择最匹配的）
- 环境问题-低素质玩家：骂人、贴脸、场外
- 环境问题-新手水平差：不会玩、乱投票
- 技术问题-服务器崩溃：服务器炸了、无法连接
- 技术问题-掉线：断线、重连失败
- 技术问题-闪退：游戏崩溃、闪退
- 技术问题-Bug：游戏bug、功能异常
- 商业化问题-界面设计：充值界面花哨、弹窗多
- 商业化问题-皮肤定价：皮肤太贵
- 平衡性问题-阵营平衡：阵营不平衡
- 平衡性问题-角色平衡：角色太强/太弱
- 内容问题-玩法单调：玩法单一、无聊
- 内容问题-角色数量：角色太少
- 匹配问题-组队匹配：匹配到开黑的
- 功能问题-屏蔽词：正常话被屏蔽
- 功能问题-新手引导：教程不完善
- 运营问题-行为分：信誉分问题
- 无问题：没有明显问题

## 一句话总结要求
- 20-30个汉字
- 保留关键信息
- 简洁明了

## 注意事项
1. 只输出JSON，不要输出其他内容
2. JSON必须是有效格式
3. summary必须是20-30字"""

    def __init__(self, api_key=None):
        """
        初始化分析器
        
        Args:
            api_key: 智谱API密钥（从环境变量或参数获取）
        """
        self.api_key = api_key or os.environ.get('ZHIPU_API_KEY')
        self.token_tracker = TokenTracker()
        self.model = "glm-4-flash"  # 使用快速模型节省成本
    
    async def analyze(self, content, review_id=None):
        """
        分析单条评价
        
        Args:
            content: 评价内容
            review_id: 评价ID（用于日志）
            
        Returns:
            dict: {sentiment, problem_category, summary}
        """
        # 截断过长内容
        if len(content) > 500:
            content = content[:500]
        
        # 预估token（中文约1.5字符/token）
        estimated_tokens = int(len(content) * 1.5) + 200  # 内容 + prompt
        
        # 检查是否可以请求
        can_req, msg = self.token_tracker.can_request(estimated_tokens)
        if not can_req:
            return self._get_default_result(msg)
        
        try:
            # 调用智谱API
            result = await self._call_api(content)
            
            # 记录token消耗
            if 'usage' in result:
                self.token_tracker.log_usage(
                    prompt_tokens=result['usage'].get('prompt_tokens', 0),
                    completion_tokens=result['usage'].get('completion_tokens', 0),
                    model=self.model,
                    review_id=review_id
                )
            
            # 解析结果
            return self._parse_result(result)
            
        except Exception as e:
            return self._get_default_result(f"API调用失败: {str(e)}")
    
    async def _call_api(self, content):
        """调用智谱API"""
        try:
            from zhipuai import ZhipuAI
            
            client = ZhipuAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"分析评价：{content}"}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            return {
                'content': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens
                }
            }
            
        except ImportError:
            # 如果没有安装zhipuai，返回模拟结果
            return {
                'content': '{"sentiment": "中性", "problem_category": "无问题", "summary": "请安装zhipuai库并配置API密钥"}',
                'usage': {'prompt_tokens': 50, 'completion_tokens': 30}
            }
    
    def _parse_result(self, result):
        """解析API返回结果"""
        try:
            content = result.get('content', '')
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                data = json.loads(json_match.group())
                
                # 校验结果
                sentiment = data.get('sentiment', '中性')
                if sentiment not in ['正向', '负向', '中性']:
                    sentiment = '中性'
                
                problem_category = data.get('problem_category', '无问题')
                summary = data.get('summary', '分析结果解析失败')
                
                # 校验summary长度
                if len(summary) < 20:
                    summary = summary + '（内容较短）' * ((20 - len(summary)) // 6 + 1)
                elif len(summary) > 30:
                    summary = summary[:30]
                
                return {
                    'sentiment': sentiment,
                    'problem_category': problem_category,
                    'summary': summary,
                    'success': True
                }
        except Exception as e:
            pass
        
        return self._get_default_result("结果解析失败")
    
    def _get_default_result(self, reason=""):
        """获取默认结果"""
        return {
            'sentiment': '中性',
            'problem_category': '无问题',
            'summary': f'分析失败请检查{reason[:20] if reason else ""}'[:30],
            'success': False,
            'reason': reason
        }


class TaskLogger:
    """任务执行日志"""
    
    def __init__(self):
        self.log_file = os.path.join(os.path.dirname(__file__), 'task_logs.json')
        self.logs = []
        self.load()
    
    def load(self):
        """加载历史日志"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.logs = json.load(f)
            except:
                self.logs = []
    
    def save(self):
        """保存日志"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs[-500:], f, ensure_ascii=False, indent=2)  # 保留最近500条
    
    def log(self, task_type, status, details=None):
        """
        记录任务日志
        
        Args:
            task_type: 任务类型
            status: 状态 (success/failed/running)
            details: 详细信息
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'task_type': task_type,
            'status': status,
            'details': details or {}
        }
        self.logs.append(entry)
        self.save()
        return entry
    
    def get_recent(self, count=10):
        """获取最近的日志"""
        return self.logs[-count:]


# 全局实例
token_tracker = TokenTracker()
task_logger = TaskLogger()
analyzer = GLMAnalyzer()


async def run_scheduled_task():
    """
    定时任务主函数
    执行流程：爬取 -> AI分析 -> 更新数据库 -> 生成词云
    """
    print(f"\n{'='*50}")
    print(f"[{datetime.now()}] 开始执行定时任务...")
    print(f"{'='*50}")
    
    task_logger.log('scheduled_task', 'running', {'message': '任务开始'})
    
    try:
        # 1. 爬取新评价
        print("\n[Step 1] 爬取新评价...")
        new_reviews = await crawl_new_reviews()
        print(f"  爬取到 {len(new_reviews)} 条新评价")
        
        if not new_reviews:
            print("  没有新评价，任务结束")
            task_logger.log('scheduled_task', 'success', {'message': '没有新评价'})
            return
        
        # 2. AI分析
        print("\n[Step 2] AI分析...")
        analyzed = []
        for i, review in enumerate(new_reviews[:MAX_REVIEWS_PER_RUN]):
            result = await analyzer.analyze(review['content'], review['review_id'])
            analyzed.append({**review, **result})
            print(f"  进度: {i+1}/{min(len(new_reviews), MAX_REVIEWS_PER_RUN)}")
        
        print(f"  分析完成 {len(analyzed)} 条")
        
        # 3. 更新数据库
        print("\n[Step 3] 更新数据库...")
        saved = await save_to_database(analyzed)
        print(f"  保存 {saved} 条评价")
        
        # 4. 生成词云
        print("\n[Step 4] 生成词云...")
        await generate_wordcloud()
        print("  词云生成完成")
        
        # 5. 记录结果
        token_report = token_tracker.get_daily_report()
        task_logger.log('scheduled_task', 'success', {
            'new_reviews': len(new_reviews),
            'analyzed': len(analyzed),
            'saved': saved,
            'token_usage': token_report
        })
        
        print(f"\n[{datetime.now()}] 任务完成!")
        print(f"Token消耗: {token_report['total_tokens']} ({token_report['usage_rate']})")
        
    except Exception as e:
        print(f"\n[ERROR] 任务失败: {e}")
        import traceback
        traceback.print_exc()
        task_logger.log('scheduled_task', 'failed', {'error': str(e)})


async def crawl_new_reviews():
    """爬取新评价（简化版，实际需要调用爬虫模块）"""
    # TODO: 集成实际爬虫
    return []


async def save_to_database(analyzed_reviews):
    """保存到数据库"""
    init_db()
    db = SessionLocal()
    
    try:
        # 获取产品和平台
        product = db.query(Product).filter(Product.name == '鹅鸭杀').first()
        platform = db.query(Platform).filter(Platform.name == 'TapTap').first()
        
        if not product or not platform:
            return 0
        
        saved = 0
        for r in analyzed_reviews:
            # 检查是否已存在
            existing = db.query(Review).filter(
                Review.platform_id == platform.id,
                Review.review_id == r['review_id']
            ).first()
            
            if existing:
                continue
            
            # 创建新记录
            review = Review(
                product_id=product.id,
                platform_id=platform.id,
                review_id=r['review_id'],
                user_name=r.get('user_name'),
                content=r.get('content'),
                rating=r.get('rating'),
                sentiment=r.get('sentiment'),
                problem_category=r.get('problem_category'),
                summary=r.get('summary'),
                review_date=datetime.strptime(r['review_date'], '%Y-%m-%d').date() if r.get('review_date') else None,
                crawl_date=datetime.now()
            )
            db.add(review)
            saved += 1
        
        db.commit()
        return saved
        
    finally:
        db.close()


async def generate_wordcloud():
    """生成词云"""
    # 调用词云生成脚本
    from generate_wordcloud import generate_all_wordclouds
    generate_all_wordclouds()


def create_scheduler():
    """创建调度器"""
    scheduler = AsyncIOScheduler()
    
    # 每2小时执行一次（0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22点）
    scheduler.add_job(
        run_scheduled_task,
        CronTrigger(hour='0,2,4,6,8,10,12,14,16,18,20,22', minute=0),
        id='taptap_monitor',
        name='TapTap舆情监控',
        replace_existing=True
    )
    
    return scheduler


async def run_once():
    """手动执行一次（用于测试）"""
    await run_scheduled_task()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='TapTap舆情监控定时服务')
    parser.add_argument('--once', action='store_true', help='只执行一次（测试模式）')
    parser.add_argument('--daemon', action='store_true', help='守护进程模式')
    args = parser.parse_args()
    
    if args.once:
        # 测试模式：只执行一次
        print("测试模式：执行一次任务...")
        asyncio.run(run_once())
    else:
        # 正常模式：启动调度器
        print("="*50)
        print("TapTap舆情监控定时服务")
        print("="*50)
        print("执行时间: 每天 0,2,4,6,8,10,12,14,16,18,20,22 点")
        print(f"每日Token限额: {DAILY_TOKEN_LIMIT}")
        print(f"单次请求限额: {PER_REQUEST_TOKEN_LIMIT}")
        print(f"每次最大处理: {MAX_REVIEWS_PER_RUN} 条评价")
        print("="*50)
        
        scheduler = create_scheduler()
        scheduler.start()
        
        print("\n服务已启动，按 Ctrl+C 停止...")
        
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            print("\n服务已停止")
            scheduler.shutdown()
