# -*- coding: utf-8 -*-
"""
鹅鸭杀评价爬虫 - 手动运行版

目标：从今天往前爬取到2026-01-07（项目公测日期）
使用方法：python crawl_manual.py
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

GAME_ID = 258720  # 鹅鸭杀
STOP_DATE = '2026-01-07'  # 项目公测日期


async def extract_date(elem: ElementHandle) -> str:
    """提取评价日期"""
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
                elif '小时前' in text or '分钟前' in text:
                    return datetime.now().strftime('%Y-%m-%d')
                elif '天前' in text:
                    days_match = re.search(r'(\d+)', text)
                    days_ago = int(days_match.group(1)) if days_match else 1
                    return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        html = await elem.evaluate('el => el.outerHTML')
        if html:
            date_match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', html)
            if date_match:
                year, month, day = date_match.group(1), int(date_match.group(2)), int(date_match.group(3))
                return f"{year}-{month:02d}-{day:02d}"
    except:
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


async def crawl_until_date():
    """爬取评价直到指定日期"""
    print(f"=== 鹅鸭杀评价爬虫 ===")
    print(f"目标日期: {STOP_DATE}（项目公测日期）")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
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
        print(f"开始爬取: {url}")
        
        await page.goto(url, wait_until='domcontentloaded')
        await page.wait_for_selector('.review-item', timeout=10000)
        
        reviews = []
        seen_ids = set()
        scroll_count = 0
        max_scrolls = 10000  # 最大滚动次数
        last_count = 0
        stall_count = 0
        
        # 参数设置
        scroll_step = 1500  # 滚动步长
        wait_timeout = 5.0  # 等待时间
        max_stall = 1000  # 最大停止容忍度
        
        while scroll_count < max_scrolls:
            review_elements = await page.query_selector_all('.review-item')
            new_count = 0
            found_stop_date = False
            
            for elem in review_elements:
                try:
                    review_id = await elem.get_attribute('data-id')
                    if not review_id:
                        elem_text = await elem.text_content()
                        review_id = str(hash(elem_text) % (10 ** 9))
                    
                    if review_id not in seen_ids:
                        seen_ids.add(review_id)
                        
                        user_name = None
                        for selector in ['.user-name', '.author-name', '[class*="author"]']:
                            try:
                                found = await elem.query_selector(selector)
                                if found:
                                    user_name = await found.text_content()
                                    if user_name:
                                        user_name = user_name.strip()
                                        break
                            except:
                                pass
                        
                        if not user_name:
                            user_name = '匿名用户'
                        
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
                        
                        rating = await extract_rating(elem)
                        review_date = await extract_date(elem)
                        
                        if not content or len(content) < 5:
                            continue
                        
                        review = {
                            'review_id': review_id,
                            'user_name': user_name,
                            'content': content,
                            'rating': rating,
                            'review_date': review_date,
                            'crawl_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        reviews.append(review)
                        new_count += 1
                        
                        if review_date and review_date <= STOP_DATE:
                            print(f"\n到达停止日期: {review_date}")
                            found_stop_date = True
                except:
                    continue
            
            if found_stop_date:
                reviews = [r for r in reviews if r['review_date'] and r['review_date'] > STOP_DATE]
                break
            
            current_count = len(reviews)
            
            if current_count > last_count:
                elapsed = time.time() - start_time
                speed = current_count / elapsed if elapsed > 0 else 0
                latest_date = reviews[-1]['review_date'] if reviews else 'unknown'
                print(f"[{scroll_count}] 已获取 {current_count} 条 | 速度: {speed:.1f}条/秒 | 最新日期: {latest_date}")
                last_count = current_count
                stall_count = 0
            else:
                stall_count += 1
            
            if stall_count >= max_stall:
                print(f"连续{stall_count}次无新评价，停止爬取")
                break
            
            await page.evaluate(f"window.scrollBy(0, {scroll_step});")
            await asyncio.sleep(wait_timeout)
            
            scroll_count += 1
        
        await browser.close()
    
    elapsed = time.time() - start_time
    metrics['end_time'] = datetime.now().isoformat()
    metrics['elapsed_seconds'] = round(elapsed, 2)
    metrics['total_reviews'] = len(reviews)
    metrics['avg_speed'] = round(len(reviews) / elapsed, 2) if elapsed > 0 else 0
    metrics['scroll_count'] = scroll_count
    
    print(f"\n=== 爬取完成 ===")
    print(f"总评价数: {len(reviews)}")
    print(f"总耗时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)")
    print(f"平均速度: {metrics['avg_speed']:.2f}条/秒")
    
    return reviews, metrics


def main():
    reviews, metrics = asyncio.run(crawl_until_date())
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(OUTPUT_DIR, f'goose_goose_duck_reviews_{STOP_DATE}_{timestamp}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"\n评价已保存到: {output_file}")
    
    metrics_file = os.path.join(OUTPUT_DIR, f'crawl_metrics_{timestamp}.json')
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"指标已保存到: {metrics_file}")
    
    date_count = {}
    for r in reviews:
        date = r.get('review_date', 'unknown')
        date_count[date] = date_count.get(date, 0) + 1
    
    print(f"\n=== 日期分布 ===")
    for date in sorted(date_count.keys(), reverse=True)[:30]:
        print(f"  {date}: {date_count[date]}条")
    
    print(f"\n总计: {len(reviews)}条评价")
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
