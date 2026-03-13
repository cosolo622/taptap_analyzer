# -*- coding: utf-8 -*-
"""
调试脚本 - 详细检查星级和日期问题
"""

import time
import re
from datetime import datetime, timedelta
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

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

url = "https://www.taptap.cn/app/258720/review"
print(f"访问页面: {url}")
driver.get(url)
time.sleep(5)

# 滚动加载更多
for _ in range(3):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# 查找评价元素
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
print(f"找到 {len(review_elements)} 个评价元素\n")

# 检查前10个评价
for i, elem in enumerate(review_elements[:10]):
    print(f"\n{'='*60}")
    print(f"评价 #{i+1}")
    
    # 1. 用户名
    try:
        user_elem = elem.find_element(By.CSS_SELECTOR, '.review-item__author-name')
        user_name = user_elem.text.strip()
        print(f"用户名: {user_name}")
    except:
        print("用户名: 未知")
    
    # 2. 星级 - 详细分析
    print("\n【星级分析】")
    star_svgs = elem.find_elements(By.CSS_SELECTOR, '.review-rate__star')
    print(f"星星总数: {len(star_svgs)}")
    
    # 检查每个星星的颜色
    bright_count = 0
    for j, svg in enumerate(star_svgs):
        try:
            fill = driver.execute_script("return window.getComputedStyle(arguments[0]).fill;", svg)
            is_bright = 'rgb(0, 217, 197)' in str(fill)
            if is_bright:
                bright_count += 1
            print(f"  星星 {j+1}: fill='{fill}' {'【亮】' if is_bright else ''}")
        except Exception as e:
            print(f"  星星 {j+1}: 错误 {e}")
    
    print(f"亮星数量: {bright_count}")
    
    # 3. 日期 - 详细分析
    print("\n【日期分析】")
    try:
        time_elem = elem.find_element(By.CSS_SELECTOR, '.tap-time, .review-item__updated-time')
        time_text = time_elem.text.strip()
        print(f"原始日期文本: '{time_text}'")
        
        # 解析日期
        review_date = ''
        if re.match(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', time_text):
            parts = re.split(r'[/-]', time_text)
            year, month, day = parts[0], parts[1], parts[2]
            review_date = f"{year}-{int(month):02d}-{int(day):02d}"
        elif '小时前' in time_text:
            review_date = datetime.now().strftime('%Y-%m-%d')
        elif '天前' in time_text:
            days_match = re.search(r'(\d+)', time_text)
            days = int(days_match.group(1)) if days_match else 1
            review_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        elif '昨天' in time_text:
            review_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif re.match(r'\d{1,2}月\d{1,2}日', time_text):
            match = re.match(r'(\d{1,2})月(\d{1,2})日', time_text)
            month, day = int(match.group(1)), int(match.group(2))
            year = datetime.now().year
            review_date = f"{year}-{month:02d}-{day:02d}"
        
        print(f"解析结果: {review_date}")
    except Exception as e:
        print(f"日期错误: {e}")
    
    # 4. 游戏时长
    print("\n【游戏时长】")
    try:
        time_labels = elem.find_elements(By.CSS_SELECTOR, '.review-item__time-label')
        for tl in time_labels:
            tl_text = tl.text.strip()
            if tl_text:
                print(f"时长标签: '{tl_text}'")
    except:
        pass

driver.quit()
print("\n\n调试完成")
