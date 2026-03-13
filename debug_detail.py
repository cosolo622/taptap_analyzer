# -*- coding: utf-8 -*-
"""
调试脚本 - 详细分析星级和日期
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
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

url = "https://www.taptap.cn/app/258720/review"
print(f"访问页面: {url}")
driver.get(url)
time.sleep(5)

# 查找第一个评价元素
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
print(f"找到 {len(review_elements)} 个评价元素\n")

if review_elements:
    elem = review_elements[0]
    
    print("="*60)
    print("详细分析第一个评价元素")
    print("="*60)
    
    # 1. 分析星级
    print("\n【星级分析】")
    star_svgs = elem.find_elements(By.CSS_SELECTOR, '.review-rate__star')
    print(f"找到 {len(star_svgs)} 个星星SVG")
    
    for i, svg in enumerate(star_svgs):
        try:
            # 获取各种属性
            outer_html = svg.get_attribute('outerHTML')[:200]
            fill = driver.execute_script("return window.getComputedStyle(arguments[0]).fill;", svg)
            color = driver.execute_script("return window.getComputedStyle(arguments[0]).color;", svg)
            
            print(f"\n星星 {i+1}:")
            print(f"  fill: {fill}")
            print(f"  color: {color}")
            print(f"  HTML: {outer_html[:100]}...")
        except Exception as e:
            print(f"  错误: {e}")
    
    # 2. 分析日期
    print("\n【日期分析】")
    time_elems = elem.find_elements(By.CSS_SELECTOR, '.tap-time, .review-item__updated-time, time')
    print(f"找到 {len(time_elems)} 个时间元素")
    
    for i, t in enumerate(time_elems):
        print(f"  时间元素 {i+1}: '{t.text}' (class: {t.get_attribute('class')})")
    
    # 3. 分析游戏时长
    print("\n【游戏时长分析】")
    time_labels = elem.find_elements(By.CSS_SELECTOR, '.review-item__time-label, [class*="time-label"]')
    print(f"找到 {len(time_labels)} 个时长标签")
    
    for i, tl in enumerate(time_labels):
        print(f"  时长标签 {i+1}: '{tl.text}' (class: {tl.get_attribute('class')})")
    
    # 4. 完整文本
    print("\n【完整文本】")
    print(elem.text[:500])

driver.quit()
print("\n调试完成")
