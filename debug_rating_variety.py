# -*- coding: utf-8 -*-
"""
调试脚本 - 查找不同星级的评价
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 初始化浏览器（非headless模式，方便观察）
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

# 滚动更多次
for _ in range(10):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# 查找评价元素
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
print(f"找到 {len(review_elements)} 个评价元素\n")

# 统计星级分布
rating_dist = {}

for i, elem in enumerate(review_elements):
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
    
    # 统计
    rating_dist[bright_count] = rating_dist.get(bright_count, 0) + 1
    
    # 打印前30个
    if i < 30:
        print(f"#{i+1}: {user_name} | {bright_count}星")

print(f"\n星级分布: {rating_dist}")

driver.quit()
print("\n调试完成")
