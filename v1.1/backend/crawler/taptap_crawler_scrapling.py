# -*- coding: utf-8 -*-
"""
TapTap 评价爬虫模块 - Playwright 版本

完全复刻老爬虫逻辑，使用 Playwright 替代 Selenium。
"""
import re
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Callable
from playwright.async_api import async_playwright, Page, ElementHandle

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TapTapCrawler:
    """TapTap 评价爬虫 - Playwright 版本"""
    
    GAME_ID_MAP = {
        '鹅鸭杀': 258720,
        '王者荣耀': 64257,
        '和平精英': 36863,
        '原神': 168825,
        '崩坏：星穹铁道': 224575,
        '明日方舟': 52314,
    }
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page: Optional[Page] = None
        self.playwright = None
        logger.info("Playwright 爬虫初始化完成")
    
    async def _init_browser(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_game_id(self, game_name: str) -> Optional[int]:
        return self.GAME_ID_MAP.get(game_name)
    
    async def get_reviews_async(
        self,
        game_id: int,
        max_reviews: Optional[int] = None,
        sort: str = 'default',
        since_date: str = None,
        stop_checker: Optional[Callable[[], bool]] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[Dict]:
        """
        获取游戏评价（异步版本）- 极速版
        
        Args:
            game_id: 游戏ID
            max_reviews: 最大评价数量
            sort: 排序方式
                - 'default': 综合排序（默认）
                - 'new': 最新排序
        
        Returns:
            List[Dict]: 评价列表
        
        替代方案：
        - 可以添加更多排序方式：'hot'(热门)、'positive'(好评)等
        """
        if not self.browser:
            await self._init_browser()
        
        # 构建URL，支持排序参数
        url = f"https://www.taptap.cn/app/{game_id}/review"
        if sort == 'new':
            url += "?sort=new"
        
        logger.info(f"开始爬取: {url} (排序: {sort})")

        await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)

        try:
            await self.page.wait_for_selector('.review-item', timeout=15000)
            await self.page.wait_for_timeout(1200)
        except Exception as e:
            logger.warning(f"等待评论元素超时: {e}")
            return []
        
        reviews = []
        seen_ids = set()
        scroll_count = 0
        target_reviews = max_reviews if isinstance(max_reviews, int) and max_reviews > 0 else 10 ** 9
        max_scrolls = (max_reviews // 10) + 200 if isinstance(max_reviews, int) and max_reviews > 0 else 3000
        last_count = 0
        stall_count = 0
        stop_by_since = False
        last_heartbeat_ts = time.time()
        
        while len(reviews) < target_reviews and scroll_count < max_scrolls:
            if callable(stop_checker) and stop_checker():
                logger.info("收到停止信号，结束当前爬取循环")
                break
            new_reviews = await self._parse_reviews(seen_ids)
            page_visible_count = len(new_reviews)

            for review in new_reviews:
                if review['review_id'] not in seen_ids:
                    if since_date and review['review_date'] and review['review_date'] < since_date:
                        logger.info(f"遇到 {review['review_date']} 的评价，停止爬取（since: {since_date}）")
                        stop_by_since = True
                        break
                    seen_ids.add(review['review_id'])
                    reviews.append(review)
            if stop_by_since:
                break

            if since_date:
                has_old = any(r['review_date'] and r['review_date'] < since_date for r in reviews)
                if has_old:
                    break
            
            current_count = len(reviews)
            
            if current_count > last_count:
                last_count = current_count
                if callable(progress_callback):
                    progress_callback(current_count)
                stall_count = 0
                if current_count % 40 == 0:
                    logger.info(f"进度: 已获取 {current_count} 条评价, 滚动 {scroll_count}/{max_scrolls}")
            else:
                stall_count += 1
                if scroll_count % 5 == 0:
                    logger.info(f"进度: 当前 {current_count} 条, 页面可见 {page_visible_count} 条, 连续无增长 {stall_count} 次")
            now_ts = time.time()
            if now_ts - last_heartbeat_ts >= 20:
                logger.info(f"心跳: 当前 {current_count} 条, 滚动 {scroll_count}/{max_scrolls}, 连续无增长 {stall_count} 次")
                last_heartbeat_ts = now_ts
            
            if current_count >= target_reviews:
                break
            
            if stall_count >= 20:
                logger.info(f"连续{stall_count}次无新评价，停止爬取")
                break
            
            try:
                prev_dom_count = len(await self.page.query_selector_all('.review-item'))
                await self.page.evaluate("window.scrollBy(0, 5000);")
                for _ in range(4):
                    await self.page.wait_for_timeout(1200)
                    new_dom_count = len(await self.page.query_selector_all('.review-item'))
                    if new_dom_count > prev_dom_count:
                        break
            except Exception as e:
                logger.warning(f"滚动页面失败: {e}")
                break

            scroll_count += 1
        
        logger.info(f"爬取完成，共 {len(reviews)} 条评价")
        return reviews[:max_reviews] if isinstance(max_reviews, int) and max_reviews > 0 else reviews
    
    def get_reviews(
        self,
        game_id: int,
        max_reviews: Optional[int] = None,
        sort: str = 'default',
        since_date: str = None,
        stop_checker: Optional[Callable[[], bool]] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[Dict]:
        return asyncio.run(self.get_reviews_async(game_id, max_reviews, sort, since_date, stop_checker, progress_callback))
    
    async def _parse_reviews(self, processed_ids: Optional[set] = None) -> List[Dict]:
        """解析页面上的评价"""
        reviews = []
        processed_ids = processed_ids or set()
        
        try:
            review_elements = await self.page.query_selector_all('.review-item')
            
            for elem in review_elements:
                try:
                    review_id = await elem.get_attribute('data-id')
                    if review_id and review_id in processed_ids:
                        continue
                    review = await self._parse_single_review(elem)
                    if review:
                        reviews.append(review)
                except Exception as e:
                    logger.debug(f"解析单条评价失败: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"解析评价列表失败: {e}")
        
        return reviews
    
    async def _parse_single_review(self, elem: ElementHandle) -> Optional[Dict]:
        """解析单条评价 - 完全复刻老爬虫逻辑"""
        try:
            # 获取 review_id
            review_id = await elem.get_attribute('data-id')
            if not review_id:
                elem_text = await elem.text_content()
                review_id = str(hash(elem_text) % (10 ** 9))
            
            # 获取用户名 - 与老爬虫选择器一致
            user_name = None
            for selector in ['.user-name', '.author-name', '[class*="author"]', '.taptap-user-name']:
                try:
                    found = await elem.query_selector(selector)
                    if found:
                        user_name = await found.text_content()
                        if user_name:
                            user_name = user_name.strip()
                            break
                except:
                    continue
            
            if not user_name:
                return None
            
            # 内容 - 获取 collapse-text-emoji__content 元素的 innerText
            content = ''
            content_elem = await elem.query_selector('.collapse-text-emoji__content')
            if content_elem:
                # 获取 innerText（包括隐藏的折叠内容）
                content = await content_elem.evaluate('el => el.innerText')
            else:
                # 备选：
                content_elem = await elem.query_selector('.review-text, .content, .item-text')
                if content_elem:
                    content = await content_elem.text_content()
                    if content:
                        content = content.strip()
            
            # 清理内容
            content = self._clean_content(content, user_name)
            
            # 获取星级
            rating = await self._extract_rating(elem)
            
            # 获取日期
            review_date = await self._extract_date(elem)
            if rating is None or not review_date:
                return None
            
            if not content or len(content) < 5:
                return None
            
            elem_text = await elem.text_content()
            
            return {
                'review_id': review_id,
                'user_name': user_name,
                'content': content,
                'rating': rating,
                'review_date': review_date,
                'crawl_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'raw_data': elem_text[:500] if elem_text else ''
            }
        
        except Exception as e:
            logger.debug(f"解析评价失败: {e}")
            return None
    
    async def _extract_rating(self, elem: ElementHandle) -> Optional[int]:
        """提取星级评分"""
        try:
            highlight = await elem.query_selector('.review-rate__highlight')
            if highlight:
                style = await highlight.get_attribute('style')
                if style:
                    match = re.search(r'width:\s*(\d+)px', style)
                    if match:
                        width = int(match.group(1))
                        rating = round(width / 18)
                        return max(1, min(5, rating))
        except:
            pass
        return None
    
    async def _extract_date(self, elem: ElementHandle) -> Optional[str]:
        """
        提取评价日期 - 完全复刻老爬虫逻辑
        
        优先从title属性获取完整日期，否则从文本解析相对时间
        如果没有.tap-time元素，从整个HTML中提取日期
        """
        try:
            time_elem = await elem.query_selector('.tap-time')
            if time_elem:
                # 优先从title属性获取完整日期（格式：2026/02/26 21:48:26 或 2026/2/26 21:48:26）
                title = await time_elem.get_attribute('title')
                if title:
                    # 支持月份和日期为1-2位数字
                    match = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', title)
                    if match:
                        year, month, day = match.group(1), int(match.group(2)), int(match.group(3))
                        return f"{year}-{month:02d}-{day:02d}"
                
                # 从文本解析
                text = await time_elem.text_content()
                if text:
                    text = text.strip()
                    
                    # YYYY-MM-DD 或 YYYY/MM/DD 格式（支持1-2位月日）
                    if re.match(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', text):
                        parts = re.split(r'[/-]', text)
                        year, month, day = parts[0], int(parts[1]), int(parts[2])
                        return f"{year}-{month:02d}-{day:02d}"
                    
                    # X小时前 - 判断是否>=24小时
                    elif '小时前' in text:
                        hours_match = re.search(r'(\d+)', text)
                        if hours_match:
                            hours = int(hours_match.group(1))
                            if hours >= 24:
                                return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                            else:
                                return datetime.now().strftime('%Y-%m-%d')
                        else:
                            return datetime.now().strftime('%Y-%m-%d')
                    
                    # X分钟前 - 今天
                    elif '分钟前' in text:
                        return datetime.now().strftime('%Y-%m-%d')
                    
                    # X天前
                    elif '天前' in text:
                        days_match = re.search(r'(\d+)', text)
                        days_ago = int(days_match.group(1)) if days_match else 1
                        return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                    
                    # 昨天
                    elif '昨天' in text:
                        return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    
                    # 前天
                    elif '前天' in text:
                        return (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
                    
                    # X月X日 格式
                    elif re.match(r'\d{1,2}月\d{1,2}日', text):
                        match = re.match(r'(\d{1,2})月(\d{1,2})日', text)
                        if match:
                            month, day = int(match.group(1)), int(match.group(2))
                            year = datetime.now().year
                            return f"{year}-{month:02d}-{day:02d}"
            
            # 如果没有.tap-time元素，从整个HTML中提取日期
            html = await elem.evaluate('el => el.outerHTML')
            if html:
                # 查找 YYYY/M/D 或 YYYY-MM-DD 格式
                date_match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', html)
                if date_match:
                    year, month, day = date_match.group(1), int(date_match.group(2)), int(date_match.group(3))
                    return f"{year}-{month:02d}-{day:02d}"
                    
        except Exception as e:
            logger.debug(f"日期解析失败: {e}")
        
        return None
    
    def _clean_content(self, content: str, user_name: str) -> str:
        """清理评价内容"""
        if not content:
            return ""
        
        # 如果内容以用户名开头，删除用户名
        if user_name and user_name != '匿名用户' and content.startswith(user_name):
            content = content[len(user_name):].strip()
        
        # 删除结尾的"玩过"或"已玩过"
        content = re.sub(r'\s*玩过\s*$', '', content)
        content = re.sub(r'\s*已玩过\s*$', '', content)
        
        return content.strip()
    
    async def close_async(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("浏览器会话已关闭")
    
    def close(self):
        """关闭浏览器（同步版本）"""
        try:
            asyncio.run(self.close_async())
        except:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def run_crawler(game_id: int, max_reviews: int = 100, headless: bool = True) -> List[Dict]:
    """运行爬虫"""
    with TapTapCrawler(headless=headless) as crawler:
        return crawler.get_reviews(game_id, max_reviews)


if __name__ == '__main__':
    reviews = run_crawler(game_id=258720, max_reviews=10, headless=False)
    for i, r in enumerate(reviews, 1):
        print(f"\n[{i}] {r['user_name']} - {r['rating']}星 - {r['review_date']}")
        print(f"    {r['content'][:100]}...")
