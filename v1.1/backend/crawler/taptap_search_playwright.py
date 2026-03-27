# -*- coding: utf-8 -*-
"""
TapTap产品搜索模块 - Playwright版本
使用Playwright在TapTap网站上搜索游戏
"""
import re
import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TapTapSearcherPlaywright:
    """TapTap游戏搜索器 - 使用Playwright"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def _init_browser(self):
        """初始化浏览器"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
                viewport={'width': 1920, 'height': 1080}
            )
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
            """)
            self.page = await self.context.new_page()
            logger.info("Playwright浏览器初始化完成")
    
    async def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
        if self.playwright:
            self.playwright = None
    
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
            
            search_url = f"https://www.taptap.cn/search/{keyword}?type=app"
            logger.info(f"搜索URL: {search_url}")
            
            await self.page.goto(search_url, timeout=60000)
            
            await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            
            try:
                await self.page.wait_for_selector('a[href*="/app/"]', timeout=15000)
            except:
                logger.warning("等待选择器超时，尝试直接解析")
            
            game_links = await self.page.query_selector_all('a[href*="/app/"]')
            logger.info(f"找到 {len(game_links)} 个游戏链接")
            
            seen_ids = set()
            
            for link in game_links:
                try:
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
                    
                    name = ''
                    parent = link
                    for _ in range(5):
                        parent = await parent.evaluate_handle('el => el.parentElement')
                        text = await parent.evaluate('el => el.innerText')
                        if text and len(text) < 100:
                            lines = text.strip().split('\n')
                            if lines:
                                name = lines[0].strip()
                                break
                    
                    if not name:
                        name = await link.inner_text()
                        name = name.strip()
                    
                    if not name or len(name) > 50:
                        continue
                    
                    rating = 0
                    parent_elem = link
                    for _ in range(3):
                        parent_elem = await parent_elem.evaluate_handle('el => el.parentElement')
                    
                    rating_text = await parent_elem.evaluate('''
                        el => {
                            const ratingEl = el.querySelector('[class*="rating"], [class*="score"]');
                            return ratingEl ? ratingEl.innerText : '';
                        }
                    ''')
                    if rating_text:
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                    
                    results.append({
                        'id': game_id,
                        'name': name,
                        'developer': '',
                        'rating': rating,
                        'category': '',
                        'url': f"https://www.taptap.cn/app/{game_id}",
                        'platform': 'TapTap'
                    })
                    
                    logger.info(f"找到游戏: {name} (ID: {game_id}, 评分: {rating})")
                    
                    if len(results) >= max_results:
                        break
                        
                except Exception as e:
                    logger.debug(f"解析游戏链接失败: {e}")
                    continue
            
            if not results:
                html = await self.page.content()
                logger.warning(f"未找到游戏，页面内容长度: {len(html)}")
                
                with open('search_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.info("已保存页面内容到 search_debug.html")
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self._close_browser()
        
        keyword_norm = re.sub(r'\s+', '', keyword).lower()
        scored_results = []
        for item in results:
            name_norm = re.sub(r'\s+', '', item.get('name', '')).lower()
            score = 0
            if name_norm == keyword_norm:
                score += 100
            if keyword_norm and keyword_norm in name_norm:
                score += 60
            for token in re.split(r'[\s·\-_/]+', keyword_norm):
                if token and token in name_norm:
                    score += 10
            scored_results.append((score, item))

        scored_results.sort(key=lambda x: (x[0], x[1].get('rating', 0)), reverse=True)
        strict_results = [item for score, item in scored_results if score >= 60]
        if strict_results:
            return strict_results[:max_results]
        return [item for _, item in scored_results][:max_results]
    
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
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.search_async(keyword, max_results))
                    return future.result(timeout=120)
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
    searcher = TapTapSearcherPlaywright()
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
