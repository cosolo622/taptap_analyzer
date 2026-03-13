# -*- coding: utf-8 -*-
"""
TapTap 评价爬虫模块

基于 Selenium 实现，修复了 v1.0 的解析问题：
1. 星级：从 highlight 容器的 width 属性计算（width/18=星级）
2. 日期：从 title 属性获取完整日期
3. 内容：过滤开头用户名和结尾"玩过"

参数:
    game_id: TapTap 游戏 ID（如鹅鸭杀=258720）
    max_reviews: 最大爬取数量
    headless: 是否无头模式

返回:
    list[dict]: 评价列表，每条包含 user_name, content, rating, review_date 等

示例:
    crawler = TapTapCrawler(headless=True)
    reviews = crawler.get_reviews(game_id=258720, max_reviews=100)
"""
import re
import time
import logging
from datetime import datetime
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TapTapCrawler:
    """
    TapTap 评价爬虫
    
    替代实现方式：
    - 使用 Playwright: 更好的异步支持和反爬能力
    - 使用 DrissionPage: 结合 requests 和 selenium 的优点
    """
    
    GAME_ID_MAP = {
        '鹅鸭杀': 258720,
        '王者荣耀': 64257,
        '和平精英': 36863,
        '原神': 168825,
        '崩坏：星穹铁道': 224575,
        '明日方舟': 52314,
    }
    
    def __init__(self, headless: bool = True):
        """
        初始化爬虫
        
        参数:
            headless: 是否使用无头模式（不显示浏览器窗口）
        """
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self._init_driver()
    
    def _init_driver(self):
        """
        初始化 Selenium WebDriver
        
        替代实现方式：
        - 使用 webdriver_manager 自动管理驱动
        - 使用 undetected_chromedriver 绕过反爬检测
        """
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 禁用自动化检测
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
            '''
        })
        logger.info("WebDriver 初始化完成")
    
    def get_game_id(self, game_name: str) -> Optional[int]:
        """
        根据游戏名称获取游戏 ID
        
        参数:
            game_name: 游戏名称
        
        返回:
            int: 游戏 ID，未找到返回 None
        """
        return self.GAME_ID_MAP.get(game_name)
    
    def get_reviews(self, game_id: int, max_reviews: int = 100) -> list[dict]:
        """
        获取游戏评价
        
        参数:
            game_id: TapTap 游戏 ID
            max_reviews: 最大爬取数量
        
        返回:
            list[dict]: 评价列表
        
        替代实现方式：
        - 使用 TapTap API（需要登录态）
        - 使用代理池提高稳定性
        """
        url = f"https://www.taptap.cn/app/{game_id}/review"
        logger.info(f"开始爬取: {url}")
        
        self.driver.get(url)
        time.sleep(3)
        
        reviews = []
        scroll_count = 0
        max_scrolls = (max_reviews // 10) + 5
        
        while len(reviews) < max_reviews and scroll_count < max_scrolls:
            new_reviews = self._parse_reviews()
            
            for review in new_reviews:
                if review['review_id'] not in [r['review_id'] for r in reviews]:
                    reviews.append(review)
                    if len(reviews) >= max_reviews:
                        break
            
            logger.info(f"已获取 {len(reviews)} 条评价")
            
            if len(reviews) < max_reviews:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                scroll_count += 1
        
        logger.info(f"爬取完成，共 {len(reviews)} 条评价")
        return reviews[:max_reviews]
    
    def _parse_reviews(self) -> list[dict]:
        """
        解析页面上的评价
        
        返回:
            list[dict]: 当前页面的评价列表
        
        替代实现方式：
        - 使用 lxml 解析 HTML（更快）
        - 使用 parsel 选择器
        """
        reviews = []
        
        try:
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, '.review-item, [class*="review"]')
            
            for elem in review_elements:
                try:
                    review = self._parse_single_review(elem)
                    if review:
                        reviews.append(review)
                except Exception as e:
                    logger.debug(f"解析单条评价失败: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"解析评价列表失败: {e}")
        
        return reviews
    
    def _parse_single_review(self, elem) -> Optional[dict]:
        """
        解析单条评价
        
        参数:
            elem: Selenium WebElement
        
        返回:
            dict: 评价数据
        
        核心修复：
        1. 星级：从 highlight 容器的 width 属性计算
        2. 日期：从 title 属性获取
        3. 内容：过滤用户名和"玩过"
        """
        try:
            review_id = elem.get_attribute('data-id') or str(hash(elem.text) % (10 ** 9))
            
            user_name = self._extract_text(elem, '.user-name, .author-name, [class*="author"]')
            if not user_name:
                user_name = self._extract_text(elem, '.taptap-user-name')
            
            content = self._extract_text(elem, '.review-text, .content, [class*="content"], .item-text')
            content = self._clean_content(content, user_name)
            
            rating = self._extract_rating(elem)
            
            review_date = self._extract_date(elem)
            
            if not content or len(content) < 5:
                return None
            
            return {
                'review_id': review_id,
                'user_name': user_name or '匿名用户',
                'content': content,
                'rating': rating,
                'review_date': review_date,
                'crawl_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'raw_data': elem.text[:500]
            }
        
        except Exception as e:
            logger.debug(f"解析评价失败: {e}")
            return None
    
    def _extract_text(self, elem, selectors: str) -> str:
        """
        从元素中提取文本
        
        参数:
            elem: Selenium WebElement
            selectors: CSS 选择器（逗号分隔）
        
        返回:
            str: 提取的文本
        """
        for selector in selectors.split(','):
            try:
                found = elem.find_element(By.CSS_SELECTOR, selector.strip())
                if found and found.text:
                    return found.text.strip()
            except NoSuchElementException:
                continue
        return ""
    
    def _extract_rating(self, elem) -> int:
        """
        提取星级评分
        
        核心修复：从 highlight 容器的 width 属性计算
        width / 18 = 星级（每个星星 18px）
        
        参数:
            elem: Selenium WebElement
        
        返回:
            int: 星级（1-5）
        
        替代实现方式：
        - 从 data-rating 属性获取（如果有）
        - 从评分数字文本获取
        """
        try:
            highlight = elem.find_element(By.CSS_SELECTOR, '.review-rate__highlight, [class*="highlight"]')
            style = highlight.get_attribute('style') or ''
            
            match = re.search(r'width:\s*(\d+)px', style)
            if match:
                width = int(match.group(1))
                rating = round(width / 18)
                return max(1, min(5, rating))
        
        except NoSuchElementException:
            pass
        
        try:
            rate_elem = elem.find_element(By.CSS_SELECTOR, '[class*="rate"], [class*="score"], [class*="rating"]')
            text = rate_elem.text
            match = re.search(r'(\d)', text)
            if match:
                return int(match.group(1))
        except NoSuchElementException:
            pass
        
        return 5
    
    def _extract_date(self, elem) -> str:
        """
        提取评价日期
        
        核心修复：从 title 属性获取完整日期
        
        参数:
            elem: Selenium WebElement
        
        返回:
            str: 日期字符串（YYYY-MM-DD）
        
        替代实现方式：
        - 解析相对时间（如"20小时前"）
        - 从 data-time 属性获取
        """
        try:
            time_elem = elem.find_element(By.CSS_SELECTOR, '.tap-time, [class*="time"], time')
            
            title = time_elem.get_attribute('title')
            if title:
                match = re.match(r'(\d{4})/(\d{2})/(\d{2})', title)
                if match:
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            
            text = time_elem.text
            if '小时前' in text or '分钟前' in text:
                return datetime.now().strftime('%Y-%m-%d')
            if '天前' in text:
                match = re.search(r'(\d+)天前', text)
                if match:
                    days = int(match.group(1))
                    date = datetime.now() - __import__('datetime').timedelta(days=days)
                    return date.strftime('%Y-%m-%d')
        
        except NoSuchElementException:
            pass
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _clean_content(self, content: str, user_name: str) -> str:
        """
        清理评价内容
        
        核心修复：过滤开头用户名和结尾"玩过"
        
        参数:
            content: 原始内容
            user_name: 用户名
        
        返回:
            str: 清理后的内容
        """
        if not content:
            return ""
        
        if user_name and content.startswith(user_name):
            content = content[len(user_name):].strip()
        
        content = re.sub(r'^[^\s]+\s*', '', content, count=1)
        
        content = re.sub(r'\s*玩过\s*$', '', content)
        content = re.sub(r'\s*已玩过\s*$', '', content)
        
        return content.strip()
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def run_crawler(game_id: int, max_reviews: int = 100, headless: bool = True) -> list[dict]:
    """
    运行爬虫的便捷函数
    
    参数:
        game_id: TapTap 游戏 ID
        max_reviews: 最大爬取数量
        headless: 是否无头模式
    
    返回:
        list[dict]: 评价列表
    
    示例:
        reviews = run_crawler(258720, max_reviews=50)
    """
    with TapTapCrawler(headless=headless) as crawler:
        return crawler.get_reviews(game_id, max_reviews)


if __name__ == '__main__':
    reviews = run_crawler(game_id=258720, max_reviews=10, headless=False)
    for i, r in enumerate(reviews, 1):
        print(f"\n[{i}] {r['user_name']} - {r['rating']}星 - {r['review_date']}")
        print(f"    {r['content'][:100]}...")
