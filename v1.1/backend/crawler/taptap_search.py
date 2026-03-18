# -*- coding: utf-8 -*-
"""
TapTap产品搜索模块
使用Playwright在TapTap网站上搜索游戏
"""
import re
import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TapTapSearcher:
    """TapTap游戏搜索器 - 使用Playwright"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def _init_browser(self):
        """初始化浏览器"""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN'
            )
            self.page = await context.new_page()
            logger.info("Playwright浏览器初始化完成")
    
    async def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
    
    async def search_async(self, keyword: str, max_results: int = 10) -> list:
        """
        异步搜索游戏
        
        参数:
            keyword: 搜索关键词
            max_results: 最大返回结果数
            
        返回:
            list: 匹配的游戏列表
        """
        results = []
        
        try:
            await self._init_browser()
            
            search_url = f"https://www.taptap.cn/search/{keyword}"
            logger.info(f"搜索URL: {search_url}")
            
            await self.page.goto(search_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)
            
            game_selectors = [
                '.tap-search-app-item',
                '.search-app-item',
                '[class*="search"] [class*="app-item"]',
                '.app-list-item',
                '[class*="game-item"]'
            ]
            
            game_elements = []
            for selector in game_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    game_elements = elements
                    logger.info(f"使用选择器 {selector} 找到 {len(elements)} 个元素")
                    break
            
            if not game_elements:
                await asyncio.sleep(2)
                game_elements = await self.page.query_selector_all('a[href*="/app/"]')
                logger.info(f"使用备用选择器找到 {len(game_elements)} 个链接")
            
            seen_ids = set()
            
            for element in game_elements[:max_results * 2]:
                try:
                    link = element
                    tag_name = await element.evaluate('el => el.tagName')
                    if tag_name != 'A':
                        link = await element.query_selector('a[href*="/app/"]')
                    
                    if not link:
                        continue
                    
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                    
                    game_id_match = re.search(r'/app/(\d+)', href)
                    if not game_id_match:
                        continue
                    
                    game_id = game_id_match.group(1)
                    if game_id in seen_ids:
                        continue
                    seen_ids.add(game_id)
                    
                    name_elem = await element.query_selector('.app-name, .name, h4, [class*="title"], .tap-search-app-name')
                    if not name_elem:
                        name_elem = link
                    
                    name = await name_elem.inner_text() if name_elem else ''
                    name = name.strip()
                    
                    if not name:
                        continue
                    
                    rating = 0
                    rating_elem = await element.query_selector('[class*="rating"], [class*="score"]')
                    if rating_elem:
                        rating_text = await rating_elem.inner_text()
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                    
                    developer = ''
                    dev_elem = await element.query_selector('[class*="author"], [class*="developer"]')
                    if dev_elem:
                        developer = await dev_elem.inner_text()
                        developer = developer.strip()
                    
                    results.append({
                        'id': game_id,
                        'name': name,
                        'developer': developer,
                        'rating': rating,
                        'category': '',
                        'url': f"https://www.taptap.cn/app/{game_id}",
                        'platform': 'TapTap'
                    })
                    
                    logger.info(f"找到游戏: {name} (ID: {game_id}, 评分: {rating})")
                    
                    if len(results) >= max_results:
                        break
                        
                except Exception as e:
                    logger.debug(f"解析游戏元素失败: {e}")
                    continue
            
            if not results:
                page_content = await self.page.content()
                if '验证' in page_content or 'captcha' in page_content.lower():
                    logger.warning("可能遇到验证码")
                else:
                    logger.warning(f"未找到游戏，页面内容长度: {len(page_content)}")
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
        finally:
            await self._close_browser()
        
        return results
    
    def search(self, keyword: str, max_results: int = 10) -> list:
        """
        同步搜索接口
        
        参数:
            keyword: 搜索关键词
            max_results: 最大返回结果数
            
        返回:
            list: 匹配的游戏列表
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.search_async(keyword, max_results))


def search_taptap_game(keyword: str, max_results: int = 10) -> list:
    """
    搜索TapTap游戏的便捷函数
    
    参数:
        keyword: 搜索关键词
        max_results: 最大返回结果数
        
    返回:
        list: 匹配的游戏列表
        
    示例:
        results = search_taptap_game("猫咪和汤", 5)
        for r in results:
            print(f"{r['name']} (ID: {r['id']})")
    """
    searcher = TapTapSearcher()
    return searcher.search(keyword, max_results)


if __name__ == '__main__':
    print("="*50)
    print("测试TapTap游戏搜索")
    print("="*50)
    
    keywords = ["猫咪和汤", "鹅鸭杀", "原神"]
    
    for kw in keywords:
        print(f"\n搜索: {kw}")
        results = search_taptap_game(kw, 3)
        
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['name']} (ID: {r['id']}, 评分: {r['rating']})")
        
        if not results:
            print("  未找到结果")
