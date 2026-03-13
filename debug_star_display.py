# -*- coding: utf-8 -*-
"""
调试脚本 - 分析星星显示方式
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

# 查找第一个评价元素
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
print(f"找到 {len(review_elements)} 个评价元素\n")

if review_elements:
    elem = review_elements[0]
    
    print("="*60)
    print("分析星星容器")
    print("="*60)
    
    # 查找星星容器
    try:
        rate_container = elem.find_element(By.CSS_SELECTOR, '.review-rate')
        print(f"\n星星容器HTML:\n{rate_container.get_attribute('outerHTML')[:500]}")
    except:
        print("找不到星星容器")
    
    # 查找所有星星SVG
    star_svgs = elem.find_elements(By.CSS_SELECTOR, '.review-rate__star')
    print(f"\n找到 {len(star_svgs)} 个星星SVG")
    
    # 分析每个星星
    for i, svg in enumerate(star_svgs):
        try:
            # 获取各种属性
            outer_html = svg.get_attribute('outerHTML')[:150]
            fill = driver.execute_script("return window.getComputedStyle(arguments[0]).fill;", svg)
            opacity = driver.execute_script("return window.getComputedStyle(arguments[0]).opacity;", svg)
            display = driver.execute_script("return window.getComputedStyle(arguments[0]).display;", svg)
            visibility = driver.execute_script("return window.getComputedStyle(arguments[0]).visibility;", svg)
            
            print(f"\n星星 {i+1}:")
            print(f"  fill: {fill}")
            print(f"  opacity: {opacity}")
            print(f"  display: {display}")
            print(f"  visibility: {visibility}")
            print(f"  HTML: {outer_html}")
        except Exception as e:
            print(f"  错误: {e}")

driver.quit()
print("\n调试完成")
