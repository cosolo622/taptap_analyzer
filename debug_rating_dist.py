# -*- coding: utf-8 -*-
"""
调试脚本 - 滚动查找不同星级的评价
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

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

url = "https://www.taptap.cn/app/258720/review"
print(f"访问页面: {url}")
driver.get(url)
time.sleep(5)

# 滚动几次加载更多评价
for _ in range(3):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# 查找所有评价元素
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
print(f"找到 {len(review_elements)} 个评价元素\n")

# 统计星级分布
rating_dist = {}

for i, elem in enumerate(review_elements[:20]):
    # 获取星级
    star_svgs = elem.find_elements(By.CSS_SELECTOR, '.review-rate__star')
    bright_count = 0
    for svg in star_svgs:
        try:
            fill = driver.execute_script("return window.getComputedStyle(arguments[0]).fill;", svg)
            if 'rgb(0, 217, 197)' in str(fill):
                bright_count += 1
        except:
            pass
    
    # 获取用户名
    try:
        user_elem = elem.find_element(By.CSS_SELECTOR, '.review-item__author-name')
        user_name = user_elem.text.strip()
    except:
        user_name = "未知"
    
    # 获取日期
    try:
        time_elem = elem.find_element(By.CSS_SELECTOR, '.tap-time, .review-item__updated-time')
        time_text = time_elem.text.strip()
    except:
        time_text = "未知"
    
    # 获取游戏时长
    try:
        time_labels = elem.find_elements(By.CSS_SELECTOR, '.review-item__time-label')
        play_time = ''
        for tl in time_labels:
            tl_text = tl.text.strip()
            if tl_text:
                play_time = tl_text
                break
    except:
        play_time = "未知"
    
    # 统计
    rating_dist[bright_count] = rating_dist.get(bright_count, 0) + 1
    
    print(f"#{i+1}: {user_name} | {bright_count}星 | {time_text} | {play_time}")

print(f"\n星级分布: {rating_dist}")

driver.quit()
print("\n调试完成")
