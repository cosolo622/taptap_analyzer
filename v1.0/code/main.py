# -*- coding: utf-8 -*-
"""
TapTap评价分析系统 - 主程序

本程序是TapTap游戏评价爬取与分析系统的入口。

主要功能：
1. 交互式输入游戏名称和日期范围
2. 自动爬取TapTap评价数据
3. 进行情感分析和分类
4. 导出分析结果到Excel

使用示例：
    交互模式：
    python main.py
    
    命令行模式：
    python main.py --game 鹅鸭杀 --days 14
    python main.py --game 原神 --start 2024-01-01 --end 2024-01-31

替代实现：
    - 可使用argparse进行更复杂的命令行参数解析
    - 可使用GUI界面（如tkinter、PyQt）
    - 可部署为Web服务（如Flask、FastAPI）

@author: TapTap Analyzer
@version: 1.0.0
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import Optional, Tuple

from config import LOG_CONFIG, OUTPUT_CONFIG
from crawler import TapTapCrawler, get_game_reviews
from sentiment import SentimentAnalyzer, analyze_reviews_batch
from classifier import ReviewClassifier, classify_reviews_batch, get_category_statistics
from exporter import ExcelExporter, export_reviews
from mock_data import generate_mock_reviews

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format'],
    datefmt=LOG_CONFIG['date_format']
)
logger = logging.getLogger(__name__)


class TapTapAnalyzer:
    """
    TapTap评价分析器主类
    
    整合爬虫、情感分析、分类和导出功能。
    
    Attributes:
        crawler: 爬虫实例
        sentiment_analyzer: 情感分析器实例
        classifier: 分类器实例
        exporter: 导出器实例
        
    使用示例：
        analyzer = TapTapAnalyzer()
        analyzer.run("鹅鸭杀", days=14)
    """
    
    def __init__(self):
        """
        初始化分析器
        
        创建各模块实例。
        """
        self.crawler = TapTapCrawler()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.classifier = ReviewClassifier()
        self.exporter = ExcelExporter()
        
        logger.info("TapTap评价分析器初始化完成")
    
    def analyze(
        self,
        game_name: str,
        app_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
        max_reviews: int = 1000
    ) -> Tuple[Optional[int], list]:
        """
        执行完整的分析流程
        
        Args:
            game_name: 游戏名称
            app_id: 游戏ID（可选，若提供则跳过搜索）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            days: 过去N天（与start_date/end_date二选一）
            max_reviews: 最大评价数量
            
        Returns:
            (app_id, reviews) 元组，reviews包含情感和分类信息
            
        流程：
        1. 搜索游戏获取app_id
        2. 爬取评价数据
        3. 情感分析
        4. 评价分类
        5. 导出Excel
        
        替代实现：
            # 使用异步处理
            import asyncio
            
            async def analyze_async(self, game_name, **kwargs):
                app_id = await self.crawler.search_game_async(game_name)
                reviews = await self.crawler.get_reviews_async(app_id, **kwargs)
                # ... 异步处理
        """
        print(f"\n{'='*60}")
        print(f"开始分析游戏: {game_name}")
        print(f"{'='*60}\n")
        
        # Step 1: 获取游戏ID
        print(f"[1/5] 获取游戏ID")
        if not app_id:
            app_id = self.crawler.search_game(game_name)
        
        if not app_id:
            print(f"❌ 未找到游戏: {game_name}")
            print(f"   提示: 可以使用 --app-id 参数直接指定游戏ID")
            return None, []
        
        print(f"✓ 游戏ID: {app_id}\n")
        
        # Step 2: 爬取评价
        date_info = ""
        if days:
            date_info = f"过去 {days} 天"
        elif start_date and end_date:
            date_info = f"{start_date} 至 {end_date}"
        
        print(f"[2/5] 爬取评价 ({date_info})")
        reviews = self.crawler.get_reviews(
            app_id=app_id,
            start_date=start_date,
            end_date=end_date,
            days=days,
            max_reviews=max_reviews
        )
        
        # 如果爬取失败，使用模拟数据
        if not reviews:
            print("⚠ API暂时不可用，使用模拟数据进行演示...")
            print(f"   提示: 实际使用时请等待API恢复或使用selenium爬取")
            reviews = generate_mock_reviews(
                game_name=game_name,
                days=days or 30,
                count=min(max_reviews, 200)
            )
            # 为模拟数据添加情感和分类信息
            reviews = analyze_reviews_batch(reviews)
            reviews = classify_reviews_batch(reviews)
            print(f"✓ 生成 {len(reviews)} 条模拟评价数据\n")
        else:
            print(f"✓ 获取到 {len(reviews)} 条评价\n")
        
        # Step 3: 情感分析
        print(f"[3/5] 情感分析")
        reviews = analyze_reviews_batch(reviews)
        
        # 统计情感分布
        sentiment_dist = self.sentiment_analyzer.get_sentiment_distribution(
            [{'label': r['sentiment_label']} for r in reviews]
        )
        print(f"✓ 情感分布: 正向 {sentiment_dist['正向']}, 中性 {sentiment_dist['中性']}, 负向 {sentiment_dist['负向']}\n")
        
        # Step 4: 评价分类
        print(f"[4/5] 评价分类")
        reviews = classify_reviews_batch(reviews)
        
        # 统计分类分布
        stats = get_category_statistics(reviews)
        print(f"✓ 分类完成，主要问题类型:")
        for cat, count in sorted(stats['primary_distribution'].items(), key=lambda x: -x[1])[:5]:
            print(f"   - {cat}: {count} 条")
        print()
        
        # Step 5: 导出Excel
        print(f"[5/5] 导出Excel")
        filepath = self.exporter.export(reviews, stats, game_name)
        print(f"✓ 文件已保存: {filepath}\n")
        
        # 打印摘要
        self._print_summary(reviews, stats, game_name)
        
        return app_id, reviews
    
    def _print_summary(
        self,
        reviews: list,
        stats: dict,
        game_name: str
    ) -> None:
        """
        打印分析摘要
        
        Args:
            reviews: 评价列表
            stats: 统计数据
            game_name: 游戏名称
            
        替代实现：
            # 生成HTML报告
            def generate_html_report(self, reviews, stats, game_name):
                html = f'''
                <html>
                <head><title>{game_name}评价分析报告</title></head>
                <body>
                    <h1>{game_name}评价分析报告</h1>
                    ...
                </body>
                </html>
                '''
                return html
        """
        print(f"\n{'='*60}")
        print(f"分析摘要 - {game_name}")
        print(f"{'='*60}")
        
        total = len(reviews)
        print(f"\n📊 基本统计:")
        print(f"   总评价数: {total}")
        
        if total > 0:
            # 平均星级
            avg_rating = sum(r.get('rating', 0) for r in reviews) / total
            print(f"   平均星级: {avg_rating:.2f}")
            
            # 情感分布
            sentiment_dist = stats.get('sentiment_distribution', {})
            if not sentiment_dist:
                sentiment_dist = {
                    '正向': sum(1 for r in reviews if r.get('sentiment_label') == '正向'),
                    '中性': sum(1 for r in reviews if r.get('sentiment_label') == '中性'),
                    '负向': sum(1 for r in reviews if r.get('sentiment_label') == '负向')
                }
            
            print(f"\n📈 情感分布:")
            for label in ['正向', '中性', '负向']:
                count = sentiment_dist.get(label, 0)
                pct = count / total * 100 if total > 0 else 0
                bar = '█' * int(pct / 5)
                print(f"   {label}: {count} ({pct:.1f}%) {bar}")
            
            # 问题分类TOP5
            print(f"\n📋 问题分类TOP5:")
            primary_dist = stats.get('primary_distribution', {})
            sorted_cats = sorted(primary_dist.items(), key=lambda x: -x[1])[:5]
            for i, (cat, count) in enumerate(sorted_cats, 1):
                pct = count / total * 100 if total > 0 else 0
                print(f"   {i}. {cat}: {count} ({pct:.1f}%)")
        
        print(f"\n{'='*60}\n")
    
    def close(self):
        """
        关闭分析器，释放资源
        
        替代实现：
            # 使用上下文管理器
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.close()
        """
        self.crawler.close()
        logger.info("分析器已关闭")


def interactive_mode():
    """
    交互模式
    
    通过用户输入获取参数。
    
    替代实现：
        # 使用GUI界面
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        def gui_mode():
            root = tk.Tk()
            root.title("TapTap评价分析器")
            # ... 创建GUI组件
            root.mainloop()
    """
    print("\n" + "="*60)
    print("       TapTap 游戏评价分析系统")
    print("="*60)
    
    # 输入游戏名称
    game_name = input("\n请输入游戏名称: ").strip()
    if not game_name:
        print("游戏名称不能为空")
        return
    
    # 选择日期模式
    print("\n请选择日期范围:")
    print("  1. 过去7天")
    print("  2. 过去14天")
    print("  3. 过去30天")
    print("  4. 自定义日期范围")
    print("  5. 全部评价（不限日期）")
    
    choice = input("\n请选择 (1-5): ").strip()
    
    days = None
    start_date = None
    end_date = None
    
    if choice == '1':
        days = 7
    elif choice == '2':
        days = 14
    elif choice == '3':
        days = 30
    elif choice == '4':
        start_date = input("请输入开始日期 (YYYY-MM-DD): ").strip()
        end_date = input("请输入结束日期 (YYYY-MM-DD): ").strip()
    elif choice == '5':
        pass  # 不限日期
    else:
        print("无效选择，使用默认值（过去7天）")
        days = 7
    
    # 最大评价数量
    max_reviews_input = input("\n最大评价数量 (默认1000，回车使用默认): ").strip()
    max_reviews = int(max_reviews_input) if max_reviews_input.isdigit() else 1000
    
    # 执行分析
    analyzer = TapTapAnalyzer()
    try:
        analyzer.analyze(
            game_name=game_name,
            start_date=start_date,
            end_date=end_date,
            days=days,
            max_reviews=max_reviews
        )
    finally:
        analyzer.close()


def command_line_mode(args):
    """
    命令行模式
    
    Args:
        args: 命令行参数
        
    替代实现：
        # 使用click库
        import click
        
        @click.command()
        @click.option('--game', required=True, help='游戏名称')
        @click.option('--days', default=7, help='过去N天')
        def cli(game, days):
            analyzer = TapTapAnalyzer()
            analyzer.analyze(game_name=game, days=days)
    """
    analyzer = TapTapAnalyzer()
    try:
        analyzer.analyze(
            game_name=args.game,
            app_id=args.app_id,
            start_date=args.start,
            end_date=args.end,
            days=args.days,
            max_reviews=args.max_reviews
        )
    finally:
        analyzer.close()


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        解析后的参数对象
        
    替代实现：
        # 使用更简洁的参数解析
        import sys
        
        def parse_simple():
            args = {'game': None, 'days': 7}
            for i, arg in enumerate(sys.argv[1:]):
                if arg == '--game' and i + 1 < len(sys.argv):
                    args['game'] = sys.argv[i + 2]
                elif arg == '--days' and i + 1 < len(sys.argv):
                    args['days'] = int(sys.argv[i + 2])
            return args
    """
    parser = argparse.ArgumentParser(
        description='TapTap游戏评价分析系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py --game 鹅鸭杀 --days 14
  python main.py --game 原神 --start 2024-01-01 --end 2024-01-31
  python main.py --app-id 258720 --days 14  # 直接使用游戏ID
  python main.py                          # 交互模式
  
常用游戏ID:
  鹅鸭杀: 258720
  原神: 168332
  王者荣耀: 64257
        '''
    )
    
    parser.add_argument(
        '--game', '-g',
        type=str,
        help='游戏名称'
    )
    
    parser.add_argument(
        '--app-id', '-a',
        type=int,
        help='游戏ID（可直接指定，跳过搜索）'
    )
    
    parser.add_argument(
        '--days', '-d',
        type=int,
        help='过去N天的评价'
    )
    
    parser.add_argument(
        '--start', '-s',
        type=str,
        help='开始日期 (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end', '-e',
        type=str,
        help='结束日期 (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--max-reviews', '-m',
        type=int,
        default=1000,
        help='最大评价数量 (默认: 1000)'
    )
    
    return parser.parse_args()


def main():
    """
    主函数入口
    
    根据参数选择运行模式。
    
    替代实现：
        # 作为模块导入使用
        def run_analysis(game_name, **kwargs):
            analyzer = TapTapAnalyzer()
            return analyzer.analyze(game_name, **kwargs)
        
        if __name__ == '__main__':
            main()
    """
    args = parse_arguments()
    
    # 判断运行模式
    if args.game:
        # 命令行模式
        command_line_mode(args)
    else:
        # 交互模式
        interactive_mode()


if __name__ == '__main__':
    main()
