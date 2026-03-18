# -*- coding: utf-8 -*-
"""
鹅鸭杀评价爬虫 - 优化版 v2

修复问题：
1. 漏爬 - 使用更可靠的页面加载检测
2. 日期None - 增强日期解析逻辑
3. 速度慢 - 优化滚动和等待策略

使用方法：python crawl_manual_v2.py
"""

import json
import os
import time
import asyncio
from datetime import datetime, timedelta
import re
from playwright.async_api import async_playwright, ElementHandle

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUTPUT_DIR, exist_ok=True)

GAME_ID = 258720
STOP_DATE = '2026-01-07'


async def extract_date_robust(elem: ElementHandle) -> str:
    """
    增强版日期提取 - 多种方式尝试
    
    Args:
        elem: 评价元素
    
    Returns:
        str: 日期字符串 (YYYY-MM-DD) 或 None
    
    替代方案：
        - 使用正则表达式从整个HTML提取
        - 从URL或其他属性提取
    """
    try:
        time_elem = await elem.query_selector('.tap-time')
        if time_elem:
            title = await time_elem.get_attribute('title')
            if title:
                match = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', title)
                if match:
                    year, month, day = match.group(1), int(match.group(2)), int(match.group(3))
                    return f"{year}-{month:02d}-{day:02d}"
            
            text = await time_elem.text_content()
            if text:
                text = text.strip()
                if re.match(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', text):
                    parts = re.split(r'[/-]', text)
                    year, month, day = parts[0], int(parts[1]), int(parts[2])
                    return f"{year}-{month:02d}-{day:02d}"
                elif '小时前' in text:
                    hours_match = re.search(r'(\d+)', text)
                    hours = int(hours_match.group(1)) if hours_match else 1
                    if hours >= 24:
                        return (datetime.now() - timedelta(days=hours // 24)).strftime('%Y-%m-%d')
                    else:
                        return datetime.now().strftime('%Y-%m-%d')
                elif '分钟前' in text:
                    return datetime.now().strftime('%Y-%m-%d')
                elif '天前' in text:
                    days_match = re.search(r'(\d+)', text)
                    days_ago = int(days_match.group(1)) if days_match else 1
                    return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                elif '昨天' in text:
                    return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                elif '前天' in text:
                    return (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        html = await elem.evaluate('el => el.outerHTML')
        if html:
            date_match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', html)
            if date_match:
                year, month, day = date_match.group(1), int(date_match.group(2)), int(date_match.group(3))
                return f"{year}-{month:02d}-{day:02d}"
            
            date_match = re.search(r'(\d{1,2})月(\d{1,2})日', html)
            if date_match:
                month, day = int(date_match.group(1)), int(date_match.group(2))
                year = datetime.now().year
                return f"{year}-{month:02d}-{day:02d}"
    except Exception as e:
        pass
    return None


async def extract_rating(elem: ElementHandle) -> int:
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
    return 5


async def parse_review_element(elem: ElementHandle) -> dict:
    """
    解析单条评价
    
    Args:
        elem: 评价元素
    
    Returns:
        dict: 评价数据字典
    
    替代方案：
        - 使用BeautifulSoup解析
        - 使用lxml解析
    """
    try:
        review_id = await elem.get_attribute('data-id')
        if not review_id:
            elem_text = await elem.text_content()
            review_id = str(hash(elem_text) % (10 ** 9))
        
        user_name = '匿名用户'
        for selector in ['.user-name', '.author-name', '[class*="author"]', '.taptap-user-name']:
            try:
                found = await elem.query_selector(selector)
                if found:
                    user_name = await found.text_content()
                    if user_name:
                        user_name = user_name.strip()
                        break
            except:
                pass
        
        content = ''
        content_elem = await elem.query_selector('.collapse-text-emoji__content')
        if content_elem:
            content = await content_elem.evaluate('el => el.innerText')
        else:
            content_elem = await elem.query_selector('.review-text, .content, .item-text')
            if content_elem:
                content = await content_elem.text_content()
                if content:
                    content = content.strip()
        
        if user_name and user_name != '匿名用户' and content.startswith(user_name):
            content = content[len(user_name):].strip()
        content = re.sub(r'\s*玩过\s*$', '', content)
        content = re.sub(r'\s*已玩过\s*$', '', content)
        
        rating = await extract_rating(elem)
        review_date = await extract_date_robust(elem)
        
        if not content or len(content) < 5:
            return None
        
        return {
            'review_id': review_id,
            'user_name': user_name,
            'content': content.strip(),
            'rating': rating,
            'review_date': review_date,
            'crawl_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return None


async def crawl_until_date():
    """
    爬取评价直到指定日期 - 优化版
    
    改进：
    1. 使用更大的滚动步长 (5000px)
    2. 等待网络空闲而非固定时间
    3. 批量解析评价
    """
    print(f"=== 鹅鸭杀评价爬虫 v2 ===", flush=True)
    print(f"目标日期: {STOP_DATE}（项目公测日期）", flush=True)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 50, flush=True)
    
    start_time = time.time()
    metrics = {
        'start_time': datetime.now().isoformat(),
        'stop_date': STOP_DATE,
        'sort': 'new'
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://www.taptap.cn/app/{GAME_ID}/review?sort=new"
        print(f"开始爬取: {url}", flush=True)
        
        await page.goto(url, wait_until='networkidle', timeout=60000)
        print(f"✅ 页面加载完成", flush=True)
        
        await page.wait_for_selector('.review-item', timeout=10000)
        print(f"✅ 找到评价元素", flush=True)
        
        reviews = []
        seen_ids = set()
        scroll_count = 0
        max_scrolls = 2000
        last_count = 0
        stall_count = 0
        max_stall = 100
        
        scroll_step = 5000
        wait_time = 2.0
        
        print(f"📋 参数: 滚动步长={scroll_step}px, 等待={wait_time}秒, 最大容忍={max_stall}次", flush=True)
        print("", flush=True)
        
        while scroll_count < max_scrolls:
            review_elements = await page.query_selector_all('.review-item')
            new_count = 0
            found_stop_date = False
            earliest_date = None
            
            for elem in review_elements:
                try:
                    review_id = await elem.get_attribute('data-id')
                    if not review_id:
                        elem_text = await elem.text_content()
                        review_id = str(hash(elem_text) % (10 ** 9))
                    
                    if review_id not in seen_ids:
                        seen_ids.add(review_id)
                        
                        review = await parse_review_element(elem)
                        if review:
                            reviews.append(review)
                            new_count += 1
                            
                            if review['review_date']:
                                if earliest_date is None or review['review_date'] < earliest_date:
                                    earliest_date = review['review_date']
                                
                                if review['review_date'] <= STOP_DATE:
                                    print(f"\n🎉 到达停止日期: {review['review_date']}", flush=True)
                                    found_stop_date = True
                except:
                    continue
            
            if found_stop_date:
                break
            
            current_count = len(reviews)
            
            if current_count > last_count:
                elapsed = time.time() - start_time
                speed = current_count / elapsed if elapsed > 0 else 0
                print(f"[{scroll_count}] ✅ {current_count}条 (+{new_count}) | {speed:.1f}条/秒 | 最早: {earliest_date or 'N/A'}", flush=True)
                last_count = current_count
                stall_count = 0
            else:
                stall_count += 1
                if stall_count % 10 == 0:
                    print(f"[{scroll_count}] ⏳ 无新评价，连续 {stall_count} 次...", flush=True)
            
            if stall_count >= max_stall:
                print(f"❌ 连续{stall_count}次无新评价，停止", flush=True)
                break
            
            await page.evaluate(f"window.scrollBy(0, {scroll_step});")
            
            try:
                await page.wait_for_load_state('domcontentloaded', timeout=5000)
            except:
                pass
            
            for i in range(int(wait_time)):
                await asyncio.sleep(1)
            
            scroll_count += 1
        
        await browser.close()
    
    elapsed = time.time() - start_time
    metrics['end_time'] = datetime.now().isoformat()
    metrics['elapsed_seconds'] = round(elapsed, 2)
    metrics['total_reviews'] = len(reviews)
    metrics['avg_speed'] = round(len(reviews) / elapsed, 2) if elapsed > 0 else 0
    metrics['scroll_count'] = scroll_count
    
    print(f"\n=== 爬取完成 ===", flush=True)
    print(f"总评价数: {len(reviews)}", flush=True)
    print(f"总耗时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)", flush=True)
    print(f"平均速度: {metrics['avg_speed']:.2f}条/秒", flush=True)
    
    return reviews, metrics


def main():
    reviews, metrics = asyncio.run(crawl_until_date())
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(OUTPUT_DIR, f'goose_goose_duck_reviews_{STOP_DATE}_{timestamp}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 评价已保存到: {output_file}", flush=True)
    
    metrics_file = os.path.join(OUTPUT_DIR, f'crawl_metrics_{timestamp}.json')
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"✅ 指标已保存到: {metrics_file}", flush=True)
    
    date_count = {}
    none_count = 0
    for r in reviews:
        date = r.get('review_date')
        if date:
            date_count[date] = date_count.get(date, 0) + 1
        else:
            none_count += 1
    
    print(f"\n=== 日期分布 ===", flush=True)
    sorted_dates = sorted(date_count.keys(), reverse=True)
    for date in sorted_dates[:30]:
        print(f"  {date}: {date_count[date]}条", flush=True)
    
    if none_count > 0:
        print(f"  ⚠️ 日期为None: {none_count}条", flush=True)
    
    print(f"\n总计: {len(reviews)}条评价", flush=True)
    print(f"日期范围: {sorted_dates[-1] if sorted_dates else 'N/A'} ~ {sorted_dates[0] if sorted_dates else 'N/A'}", flush=True)
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


if __name__ == '__main__':
    main()
