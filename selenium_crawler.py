# -*- coding: utf-8 -*-
"""
TapTap评价分析系统 - Selenium爬虫模块 (修复版)

修复点：
1. 准确获取星级（通过SVG图标）
2. 准确获取日期（tap-time类）
3. 准确获取游戏时长
4. 过滤评论区内容

@author: TapTap Analyzer
@version: 1.3.0
"""

import time
import logging
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SeleniumCrawler:
    """
    使用Selenium爬取TapTap评价
    """
    
    def __init__(self, headless: bool = True):
        self.driver = None
        self.headless = headless
        self._init_driver()
    
    def _init_driver(self):
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
            logger.info("Chrome WebDriver初始化成功")
        except Exception as e:
            logger.error(f"WebDriver初始化失败: {e}")
            raise
    
    def get_reviews(
        self,
        app_id: int,
        days: int = 14,
        max_reviews: int = 500
    ) -> List[Dict[str, Any]]:
        url = f"https://www.taptap.cn/app/{app_id}/review"
        logger.info(f"访问页面: {url}")
        
        self.driver.get(url)
        time.sleep(5)
        
        reviews = []
        start_date = datetime.now() - timedelta(days=days)
        
        # 滚动加载更多
        scroll_reviews = self._scroll_and_extract(start_date, max_reviews)
        reviews.extend(scroll_reviews)
        
        # 去重
        seen = set()
        unique_reviews = []
        for r in reviews:
            key = (r.get('review_date', ''), r.get('content', '')[:50] if r.get('content') else '')
            if key not in seen and r.get('content'):
                seen.add(key)
                unique_reviews.append(r)
        
        logger.info(f"共获取 {len(unique_reviews)} 条唯一评价")
        return unique_reviews[:max_reviews]
    
    def _scroll_and_extract(self, start_date: datetime, max_count: int) -> List[Dict]:
        """
        滚动页面加载更多评价
        """
        reviews = []
        last_count = 0
        scroll_count = 0
        max_scrolls = 20
        no_new_count = 0
        
        while scroll_count < max_scrolls and len(reviews) < max_count:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            try:
                # 使用更精确的选择器 - 只选择主评价区域
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, '.review-item')
                
                for elem in review_elements:
                    try:
                        review = self._extract_review_from_element(elem, start_date)
                        if review and review['content']:
                            # 检查是否已存在
                            exists = False
                            for r in reviews:
                                if r['content'][:50] == review['content'][:50]:
                                    exists = True
                                    break
                            if not exists:
                                reviews.append(review)
                    except Exception as e:
                        logger.debug(f"提取元素失败: {e}")
            
            except Exception as e:
                logger.debug(f"查找元素失败: {e}")
            
            if len(reviews) == last_count:
                no_new_count += 1
                if no_new_count >= 3:
                    break
            else:
                no_new_count = 0
                last_count = len(reviews)
            
            logger.info(f"滚动 {scroll_count + 1} 次，已获取 {len(reviews)} 条评价")
            scroll_count += 1
        
        return reviews
    
    def _extract_review_from_element(self, elem, start_date: datetime) -> Optional[Dict]:
        """
        从单个元素提取评价（修复版）
        
        修复点：
        1. 准确获取星级 - 通过SVG图标
        2. 准确获取日期 - tap-time类
        3. 准确获取游戏时长 - review-item__time-label类
        4. 过滤评论区内容
        """
        try:
            # 1. 提取用户名
            user_name = '匿名用户'
            try:
                user_elem = elem.find_element(By.CSS_SELECTOR, '.review-item__author-name, .user-name')
                user_name = user_elem.text.strip()
            except:
                pass
            
            # 2. 提取星级 - 从review-rate__highlight的width属性计算
            rating = 0
            try:
                # 查找highlight容器，获取width属性
                highlight = elem.find_element(By.CSS_SELECTOR, '.review-rate__highlight')
                style = highlight.get_attribute('style') or ''
                
                # 从style中提取width值，如 "width: 72px;"
                width_match = re.search(r'width:\s*(\d+)px', style)
                if width_match:
                    width = int(width_match.group(1))
                    # 每个星星宽度18px，计算星级
                    rating = round(width / 18)
                
                # 如果没有找到width，尝试从星星SVG颜色判断
                if rating == 0:
                    star_svgs = elem.find_elements(By.CSS_SELECTOR, '.review-rate__star')
                    for svg in star_svgs:
                        try:
                            fill = self.driver.execute_script(
                                "return window.getComputedStyle(arguments[0]).fill;", svg
                            )
                            if fill and 'rgb(0, 217, 197)' in str(fill):
                                rating += 1
                        except:
                            pass
            except Exception as e:
                logger.debug(f"星级提取失败: {e}")
            
            # 3. 提取日期 - 从title属性获取完整日期
            review_date = ''
            try:
                time_elem = elem.find_element(By.CSS_SELECTOR, '.tap-time, .review-item__updated-time')
                # 优先从title属性获取完整日期（格式：2026/02/26 21:48:26）
                title = time_elem.get_attribute('title') or ''
                if title:
                    # 解析 YYYY/MM/DD HH:MM:SS 格式
                    date_match = re.match(r'(\d{4})/(\d{2})/(\d{2})', title)
                    if date_match:
                        year, month, day = date_match.group(1), date_match.group(2), date_match.group(3)
                        review_date = f"{year}-{month}-{day}"
                
                # 如果没有title，从文本解析
                if not review_date:
                    time_text = time_elem.text.strip()
                    if re.match(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', time_text):
                        parts = re.split(r'[/-]', time_text)
                        year, month, day = parts[0], parts[1], parts[2]
                        review_date = f"{year}-{int(month):02d}-{int(day):02d}"
                    elif '小时前' in time_text:
                        hours_match = re.search(r'(\d+)', time_text)
                        if hours_match:
                            hours = int(hours_match.group(1))
                            if hours >= 24:
                                review_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                            else:
                                review_date = datetime.now().strftime('%Y-%m-%d')
                        else:
                            review_date = datetime.now().strftime('%Y-%m-%d')
                    elif '分钟前' in time_text:
                        review_date = datetime.now().strftime('%Y-%m-%d')
                    elif '天前' in time_text:
                        days_match = re.search(r'(\d+)', time_text)
                        days_ago = int(days_match.group(1)) if days_match else 1
                        review_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                    elif '昨天' in time_text:
                        review_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    elif '前天' in time_text:
                        review_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
                    elif re.match(r'\d{1,2}月\d{1,2}日', time_text):
                        match = re.match(r'(\d{1,2})月(\d{1,2})日', time_text)
                        month, day = int(match.group(1)), int(match.group(2))
                        year = datetime.now().year
                        review_date = f"{year}-{month:02d}-{day:02d}"
            except:
                # 如果找不到日期元素，从文本中提取
                full_text = elem.text
                date_match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', full_text)
                if date_match:
                    year, month, day = date_match.group(1), int(date_match.group(2)), int(date_match.group(3))
                    review_date = f"{year}-{month:02d}-{day:02d}"
            
            if not review_date:
                review_date = datetime.now().strftime('%Y-%m-%d')
            
            # 4. 提取游戏时长
            play_time_str = ''
            try:
                # 查找所有time-label元素
                time_labels = elem.find_elements(By.CSS_SELECTOR, '.review-item__time-label')
                for tl in time_labels:
                    tl_text = tl.text.strip()
                    if tl_text:
                        if '玩过' in tl_text and '小时' not in tl_text:
                            play_time_str = '玩过'
                            break
                        elif '小时' in tl_text:
                            # 从"游戏时长 3.7 小时后评价"中提取数字
                            match = re.search(r'([\d.]+)\s*小时', tl_text)
                            if match:
                                play_time_str = match.group(1)
                                break
            except:
                pass
            
            # 5. 提取设备
            device = ''
            try:
                # 设备信息通常在日期附近
                device_text = elem.text
                device_patterns = [
                    r'(iPhone\s*\d+(?:\s*(?:Pro|Plus|Max|mini))?)',
                    r'(iPad\s*(?:Pro|Air|mini)?)',
                    r'(Android)',
                    r'来自\s*(\w+)',
                ]
                for pattern in device_patterns:
                    match = re.search(pattern, device_text)
                    if match:
                        device = match.group(1)
                        break
            except:
                pass
            
            # 6. 提取评价内容 - 从文本行中提取
            content = ''
            try:
                lines = elem.text.split('\n')
                content_lines = []
                in_comment_section = False
                found_content_start = False
                
                for line in lines:
                    line = line.strip()
                    
                    # 检测评论区开始标记
                    if re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_]{2,15}$', line) and len(line) < 15:
                        # 如果已经找到内容开始，这是评论区用户名
                        if found_content_start:
                            in_comment_section = True
                        continue
                    
                    if in_comment_section:
                        continue
                    
                    # 跳过用户名行
                    if line == user_name:
                        continue
                    # 跳过"玩过"（单独一行）
                    if line == '玩过':
                        continue
                    # 跳过"游戏时长 X 小时后评价"
                    if re.match(r'^游戏时长\s*[\d.]+\s*小时后评价$', line):
                        continue
                    # 跳过日期行
                    if re.match(r'^\d+\s*(小时前|天前|分钟前)$', line):
                        continue
                    if re.match(r'^昨天$', line):
                        continue
                    if re.match(r'^前天$', line):
                        continue
                    if re.match(r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}$', line):
                        continue
                    if re.match(r'^\d{1,2}月\d{1,2}日$', line):
                        continue
                    # 跳过设备行
                    if line.startswith('来自'):
                        continue
                    # 跳过"因高专业度入选"等标签
                    if '入选' in line and len(line) < 15:
                        continue
                    # 跳过短行
                    if len(line) < 10:
                        continue
                    
                    found_content_start = True
                    content_lines.append(line)
                
                if content_lines:
                    content = '\n'.join(content_lines)
            except Exception as e:
                logger.debug(f"内容提取失败: {e}")
            
            # 7. 过滤评论区内容
            # 检查是否是回复或评论区内容
            if content:
                # 如果内容以"回复"开头或包含"@某人"，可能是评论区内容
                if content.startswith('回复') or re.match(r'^@\w+\s', content):
                    return None
                # 如果内容太短，可能是无效内容
                if len(content) < 10:
                    return None
            
            if not content:
                return None
            
            return {
                'review_date': review_date,
                'rating': rating,
                'content': content.strip(),
                'play_time': 0,
                'play_time_str': play_time_str,
                'user_name': user_name,
                'device': device
            }
        
        except Exception as e:
            logger.debug(f"提取评价元素失败: {e}")
            return None
    
    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")


def crawl_taptap_reviews(app_id: int, days: int = 14, max_reviews: int = 500) -> List[Dict]:
    crawler = SeleniumCrawler(headless=True)
    try:
        return crawler.get_reviews(app_id, days, max_reviews)
    finally:
        crawler.close()


if __name__ == '__main__':
    reviews = crawl_taptap_reviews(258720, days=14, max_reviews=10)
    print(f"获取到 {len(reviews)} 条评价")
    for r in reviews[:5]:
        print(f"{r['review_date']} | {r['rating']}星 | {r['play_time_str']} | {r['user_name']} | {r['content'][:30]}...")
