# -*- coding: utf-8 -*-
"""
TapTap评价分析系统 - 爬虫模块

本模块负责从TapTap平台爬取游戏评价数据。

主要功能：
1. 通过游戏名称搜索获取游戏ID
2. 根据游戏ID爬取评价列表
3. 支持日期范围筛选
4. 自动处理分页和请求频率限制

使用示例：
    crawler = TapTapCrawler()
    app_id = crawler.search_game("原神")
    reviews = crawler.get_reviews(app_id, days=7)

替代实现：
    - 可使用selenium模拟浏览器爬取（适用于动态页面）
    - 可使用scrapy框架构建分布式爬虫
    - 可使用代理池避免IP限制

@author: TapTap Analyzer
@version: 1.1.0
"""

import requests
import time
import logging
import re
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import quote

from config import TAPTAP_CONFIG, LOG_CONFIG

logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format'],
    datefmt=LOG_CONFIG['date_format']
)
logger = logging.getLogger(__name__)


class TapTapCrawler:
    """
    TapTap评价爬虫类
    
    负责从TapTap平台爬取游戏评价数据。
    
    Attributes:
        session: requests会话对象
        config: TapTap配置字典
        
    使用示例：
        crawler = TapTapCrawler()
        app_id = crawler.search_game("鹅鸭杀")
        reviews = crawler.get_reviews(app_id, start_date="2024-01-01", end_date="2024-01-31")
    """
    
    def __init__(self):
        """
        初始化爬虫
        
        创建requests会话并设置请求头。
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.config = TAPTAP_CONFIG
        self.x_ua = quote('V=1&PN=WebApp&LANG=zh_CN&VN_CODE=102&LOC=CN&PLT=PC&DS=Android&DT=PC')
        logger.info("TapTap爬虫初始化完成")
    
    def search_game(self, game_name: str) -> Optional[int]:
        """
        通过游戏名称搜索游戏ID
        
        Args:
            game_name: 游戏名称，如"原神"、"鹅鸭杀"
            
        Returns:
            游戏ID（app_id），未找到返回None
            
        示例返回值：
            258720  # 鹅鸭杀的app_id
            
        替代实现：
            - 可使用模糊匹配返回多个候选游戏
            - 可爬取搜索结果页面获取更多信息
        """
        logger.info(f"搜索游戏: {game_name}")
        
        # 常用游戏ID映射表
        known_games = {
            '鹅鸭杀': 258720,
            '原神': 168332,
            '王者荣耀': 64257,
            '崩坏：星穹铁道': 224575,
            '明日方舟': 64350,
            '和平精英': 68993,
            '蛋仔派对': 206302,
            '金铲铲之战': 235536,
            '英雄联盟手游': 234807,
            '光·遇': 62340,
        }
        
        # 检查已知游戏
        for name, app_id in known_games.items():
            if game_name.lower() in name.lower() or name.lower() in game_name.lower():
                logger.info(f"从已知游戏列表找到: {name} (ID: {app_id})")
                return app_id
        
        # 尝试搜索API
        search_apis = [
            f"https://www.taptap.cn/webapiv2/search/api/v2/search?query={quote(game_name)}&kw={quote(game_name)}",
            f"https://www.taptap.cn/webapiv2/search/api/v1/suggest?query={quote(game_name)}",
        ]
        
        for search_url in search_apis:
            try:
                response = self.session.get(search_url, timeout=self.config['timeout'])
                if response.status_code == 200:
                    data = response.json()
                    
                    # 解析搜索结果
                    if 'data' in data:
                        results = data['data']
                        
                        # 尝试不同的数据结构
                        items = []
                        if isinstance(results, dict):
                            items = results.get('games', results.get('apps', []))
                        elif isinstance(results, list):
                            items = results
                        
                        for item in items:
                            app_info = item.get('app', item)
                            found_name = app_info.get('title', app_info.get('name', ''))
                            app_id = app_info.get('id') or app_info.get('app_id')
                            
                            if app_id and (game_name.lower() in found_name.lower() or found_name.lower() in game_name.lower()):
                                logger.info(f"找到游戏: {found_name} (ID: {app_id})")
                                return int(app_id)
            except Exception as e:
                logger.debug(f"搜索API失败: {e}")
        
        logger.warning(f"未找到游戏: {game_name}")
        return None
    
    def get_reviews(
        self,
        app_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
        max_reviews: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        获取游戏评价列表
        
        Args:
            app_id: 游戏ID
            start_date: 开始日期，格式"YYYY-MM-DD"
            end_date: 结束日期，格式"YYYY-MM-DD"
            days: 过去N天（与start_date/end_date二选一）
            max_reviews: 最大获取评价数量，默认1000
            
        Returns:
            评价列表，每个评价包含：
            - review_date: 评价日期
            - rating: 评价星级(1-5)
            - content: 评价内容
            - play_time: 游玩时长（分钟）
            - user_name: 用户名
            - device: 设备信息
            
        替代实现：
            - 可使用异步请求(aiohttp)提高爬取效率
            - 可添加代理池支持
        """
        # 处理日期参数
        if days:
            end_datetime = datetime.now()
            start_datetime = end_datetime - timedelta(days=days)
            start_date = start_datetime.strftime('%Y-%m-%d')
            end_date = end_datetime.strftime('%Y-%m-%d')
        
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_datetime = datetime(2020, 1, 1)
        
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_datetime = datetime.now()
        
        logger.info(f"开始爬取评价，日期范围: {start_date} 至 {end_date}")
        
        reviews = []
        page = 0
        should_continue = True
        
        # 新版API端点
        base_api = f"http://www.taptap.cn/webapiv2/review/v1/list-by-app?X-UA={self.x_ua}&app_id={app_id}"
        
        while should_continue and len(reviews) < max_reviews:
            # 尝试多种API格式
            apis_to_try = [
                f"{base_api}&from={page * 20}&limit=20&sort=new",
                f"http://www.taptap.cn/webapiv2/review/v2/by-app?app_id={app_id}&from={page * 20}&limit=20&X-UA={self.x_ua}&sort=new",
            ]
            
            page_data = None
            for api_url in apis_to_try:
                try:
                    self.session.headers.update({
                        'Referer': f'https://www.taptap.cn/app/{app_id}/review'
                    })
                    response = self.session.get(api_url, timeout=self.config['timeout'])
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data:
                            page_data = data
                            logger.info(f"使用API成功: {api_url[:60]}...")
                            break
                except Exception as e:
                    logger.debug(f"API尝试失败: {e}")
            
            if not page_data:
                # 尝试从页面获取数据
                page_url = f"https://www.taptap.cn/app/{app_id}/review?page={page + 1}"
                try:
                    response = self.session.get(page_url, timeout=self.config['timeout'])
                    if response.status_code == 200:
                        page_data = self._extract_data_from_html(response.text)
                except Exception as e:
                    logger.error(f"页面请求失败: {e}")
            
            if not page_data:
                logger.info("无法获取更多评价数据")
                break
            
            # 解析评价数据
            review_list = self._extract_reviews_from_data(page_data)
            
            if not review_list:
                logger.info("没有更多评价了")
                break
            
            for item in review_list:
                review = self._parse_review(item)
                
                if review:
                    try:
                        review_datetime = datetime.strptime(review['review_date'], '%Y-%m-%d')
                        
                        if review_datetime > end_datetime:
                            continue
                        elif review_datetime < start_datetime:
                            should_continue = False
                            break
                        else:
                            reviews.append(review)
                    except:
                        reviews.append(review)
            
            logger.info(f"已获取 {len(reviews)} 条评价")
            page += 1
            time.sleep(self.config['request_interval'])
            
            if page > 50:
                break
        
        # 去重
        seen = set()
        unique_reviews = []
        for r in reviews:
            key = (r.get('review_date', ''), r.get('content', '')[:50])
            if key not in seen:
                seen.add(key)
                unique_reviews.append(r)
        
        logger.info(f"爬取完成，共获取 {len(unique_reviews)} 条评价")
        return unique_reviews[:max_reviews]
    
    def _extract_data_from_html(self, html: str) -> Optional[Dict]:
        """
        从HTML中提取数据
        
        Args:
            html: HTML内容
            
        Returns:
            解析出的数据字典
        """
        patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
            r'window\.__NUXT__\s*=\s*(\{.*?\});',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
        
        return None
    
    def _extract_reviews_from_data(self, data: Dict) -> List[Dict]:
        """
        从数据中提取评价列表
        
        Args:
            data: API返回的数据
            
        Returns:
            评价列表
        """
        if 'data' in data:
            inner = data['data']
            
            # 尝试不同的数据路径
            paths = [
                ['list'],
                ['reviews'],
                ['items'],
                ['init_data', 'child_items'],
            ]
            
            for path in paths:
                temp = inner
                found = True
                for key in path:
                    if isinstance(temp, dict) and key in temp:
                        temp = temp[key]
                    else:
                        found = False
                        break
                if found and isinstance(temp, list):
                    return temp
        
        return []
    
    def _parse_review(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        解析单条评价数据
        
        Args:
            item: API返回的原始评价数据
            
        Returns:
            解析后的评价字典，解析失败返回None
            
        替代实现：
            - 可提取更多字段（如点赞数、回复数）
            - 可添加数据清洗逻辑
        """
        try:
            # 提取评价内容
            content = ''
            if 'moment' in item:
                moment = item['moment']
                extended = moment.get('extended_entities', {})
                reviews = extended.get('reviews', [])
                if reviews:
                    content = reviews[0].get('contents', {}).get('text', '')
                created_time = moment.get('created_at', 0)
                user = moment.get('author', {}).get('user', {})
                user_name = user.get('name', '匿名用户')
            else:
                content = item.get('contents', {}).get('text', '') or item.get('content', '')
                created_time = item.get('created_at', 0) or item.get('createdTime', 0)
                user = item.get('user', {}) or item.get('author', {})
                user_name = user.get('name', '') or user.get('username', '匿名用户')
            
            if not content:
                return None
            
            # 提取日期
            if created_time:
                review_date = datetime.fromtimestamp(created_time).strftime('%Y-%m-%d')
            else:
                review_date = datetime.now().strftime('%Y-%m-%d')
            
            # 提取星级
            rating = item.get('rating', 0) or item.get('score', 0)
            
            # 提取游玩时长
            play_time = item.get('played_duration', 0) or item.get('playTime', 0)
            play_time = play_time // 60 if play_time else 0
            
            # 提取设备
            device = item.get('device', '')
            
            return {
                'review_date': review_date,
                'rating': rating,
                'content': content.strip(),
                'play_time': play_time,
                'user_name': user_name,
                'device': device
            }
            
        except Exception as e:
            logger.debug(f"解析评价失败: {e}")
            return None
    
    def close(self):
        """
        关闭爬虫会话
        
        替代实现：
            - 可保存cookies以便下次使用
            - 可记录爬取状态
        """
        self.session.close()
        logger.info("爬虫会话已关闭")


def get_game_reviews(
    game_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days: Optional[int] = None,
    max_reviews: int = 1000
) -> Tuple[Optional[int], List[Dict[str, Any]]]:
    """
    便捷函数：获取指定游戏的评价
    
    Args:
        game_name: 游戏名称
        start_date: 开始日期
        end_date: 结束日期
        days: 过去N天
        max_reviews: 最大评价数量
        
    Returns:
        (app_id, reviews) 元组
        
    使用示例：
        app_id, reviews = get_game_reviews("鹅鸭杀", days=14)
        
    替代实现：
        - 可添加缓存机制避免重复爬取
        - 可支持批量获取多个游戏
    """
    crawler = TapTapCrawler()
    
    try:
        app_id = crawler.search_game(game_name)
        if not app_id:
            logger.error(f"未找到游戏: {game_name}")
            return None, []
        
        reviews = crawler.get_reviews(
            app_id=app_id,
            start_date=start_date,
            end_date=end_date,
            days=days,
            max_reviews=max_reviews
        )
        
        return app_id, reviews
        
    finally:
        crawler.close()


if __name__ == '__main__':
    app_id, reviews = get_game_reviews("鹅鸭杀", days=7, max_reviews=50)
    print(f"游戏ID: {app_id}")
    print(f"评价数量: {len(reviews)}")
    if reviews:
        print(f"第一条评价: {reviews[0]}")
