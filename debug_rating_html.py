# -*- coding: utf-8 -*-
"""
调试脚本 - 从页面数据中获取星级
"""

import time
import json
import re
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

# 查找评价元素
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
print(f"找到 {len(review_elements)} 个评价元素\n")

# 检查前5个评价的HTML
for i, elem in enumerate(review_elements[:5]):
    # 获取用户名
    try:
        user_elem = elem.find_element(By.CSS_SELECTOR, '.review-item__author-name')
        user_name = user_elem.text.strip()
    except:
        user_name = "未知"
    
    # 获取完整HTML
    html = elem.get_attribute('outerHTML')
    
    # 查找星级相关数据
    # 方法1: 查找data属性
    data_rating = elem.get_attribute('data-rating')
    data_score = elem.get_attribute('data-score')
    
    # 方法2: 从HTML中查找
    rating_match = re.search(r'"rating"\s*:\s*(\d)', html)
    score_match = re.search(r'"score"\s*:\s*(\d)', html)
    
    # 方法3: 查找review-rate的class
    rate_class_match = re.search(r'review-rate[^"]*score-(\d)', html)
    
    print(f"#{i+1}: {user_name}")
    print(f"  data-rating: {data_rating}")
    print(f"  data-score: {data_score}")
    print(f"  rating匹配: {rating_match.group(1) if rating_match else '无'}")
    print(f"  score匹配: {score_match.group(1) if score_match else '无'}")
    print(f"  rate class匹配: {rate_class_match.group(1) if rate_class_match else '无'}")
    
    # 打印包含rating的HTML片段
    rating_html = re.findall(r'.{0,50}rating.{0,50}', html, re.IGNORECASE)
    if rating_html:
        print(f"  包含rating的HTML: {rating_html[:3]}")
    print()

driver.quit()
print("调试完成")
