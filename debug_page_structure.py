# -*- coding: utf-8 -*-
"""
调试脚本 - 分析TapTap页面结构
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 初始化浏览器
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

url = "https://www.taptap.cn/app/258720/review"
print(f"访问页面: {url}")
driver.get(url)
time.sleep(5)

# 查找评价元素
print("\n=== 查找评价元素 ===")
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item, [class*="ReviewItem"], [class*="review-item"]')
print(f"找到 {len(review_elements)} 个评价元素")

# 分析前3个评价元素
for i, elem in enumerate(review_elements[:3]):
    print(f"\n{'='*60}")
    print(f"评价 #{i+1}")
    print(f"{'='*60}")
    
    # 获取完整文本
    text = elem.text
    print(f"\n完整文本:\n{text[:500]}...")
    
    # 获取HTML
    html = elem.get_attribute('innerHTML')
    print(f"\nHTML长度: {len(html)}")
    
    # 查找星级相关元素
    print("\n--- 星级分析 ---")
    star_selectors = [
        '[class*="star"]',
        '[class*="rating"]',
        '[class*="score"]',
        'svg',
        'img[class*="star"]',
    ]
    
    for selector in star_selectors:
        try:
            stars = elem.find_elements(By.CSS_SELECTOR, selector)
            if stars:
                print(f"  选择器 '{selector}' 找到 {len(stars)} 个元素")
                for j, star in enumerate(stars[:3]):
                    star_class = star.get_attribute('class') or ''
                    star_html = star.get_attribute('outerHTML')[:100]
                    print(f"    [{j}] class: {star_class}")
                    print(f"        html: {star_html}")
        except Exception as e:
            pass
    
    # 查找日期相关元素
    print("\n--- 日期分析 ---")
    date_selectors = [
        '[class*="time"]',
        '[class*="date"]',
        'time',
        'span',
    ]
    
    for selector in date_selectors:
        try:
            dates = elem.find_elements(By.CSS_SELECTOR, selector)
            if dates:
                for j, date_elem in enumerate(dates[:5]):
                    date_text = date_elem.text.strip()
                    date_class = date_elem.get_attribute('class') or ''
                    if date_text and len(date_text) < 30:
                        print(f"  选择器 '{selector}' [{j}]: '{date_text}' (class: {date_class})")
        except:
            pass
    
    # 查找游戏时长相关元素
    print("\n--- 游戏时长分析 ---")
    time_selectors = [
        '[class*="duration"]',
        '[class*="play"]',
        '[class*="hour"]',
        'span',
    ]
    
    for selector in time_selectors:
        try:
            times = elem.find_elements(By.CSS_SELECTOR, selector)
            if times:
                for j, time_elem in enumerate(times[:5]):
                    time_text = time_elem.text.strip()
                    time_class = time_elem.get_attribute('class') or ''
                    if '小时' in time_text or '玩过' in time_text or '时长' in time_text:
                        print(f"  选择器 '{selector}' [{j}]: '{time_text}' (class: {time_class})")
        except:
            pass

driver.quit()
print("\n\n调试完成")
