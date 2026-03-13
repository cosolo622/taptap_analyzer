# -*- coding: utf-8 -*-
"""
调试脚本 - 检查日期获取
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

# 查找前5个评价元素
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
print(f"找到 {len(review_elements)} 个评价元素\n")

for i, elem in enumerate(review_elements[:5]):
    # 获取用户名
    try:
        user_elem = elem.find_element(By.CSS_SELECTOR, '.review-item__author-name')
        user_name = user_elem.text.strip()
    except:
        user_name = "未知"
    
    # 获取日期 - 详细分析
    print(f"\n#{i+1}: {user_name}")
    
    # 方法1: 查找tap-time
    try:
        time_elem = elem.find_element(By.CSS_SELECTOR, '.tap-time, .review-item__updated-time')
        time_text = time_elem.text.strip()
        time_class = time_elem.get_attribute('class')
        print(f"  日期元素文本: '{time_text}'")
        print(f"  日期元素class: {time_class}")
    except:
        print("  未找到日期元素")
    
    # 方法2: 查找所有包含日期的元素
    try:
        all_time_elems = elem.find_elements(By.CSS_SELECTOR, '[class*="time"], [class*="date"]')
        for t in all_time_elems:
            t_text = t.text.strip()
            if t_text:
                print(f"  其他时间元素: '{t_text}' (class: {t.get_attribute('class')})")
    except:
        pass
    
    # 方法3: 从完整文本中查找日期
    full_text = elem.text
    date_patterns = [
        r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
        r'\d{1,2}月\d{1,2}日',
        r'\d+\s*天前',
        r'\d+\s*小时前',
        r'昨天',
    ]
    for pattern in date_patterns:
        matches = re.findall(pattern, full_text)
        if matches:
            print(f"  文本中匹配: {matches}")

driver.quit()
print("\n调试完成")
