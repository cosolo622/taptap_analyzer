# -*- coding: utf-8 -*-
"""
调试脚本 - 测试星级获取
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

# 查找前5个评价元素
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
print(f"找到 {len(review_elements)} 个评价元素\n")

for i, elem in enumerate(review_elements[:5]):
    print(f"\n{'='*50}")
    print(f"评价 #{i+1}")
    
    # 提取用户名
    try:
        user_elem = elem.find_element(By.CSS_SELECTOR, '.review-item__author-name')
        user_name = user_elem.text.strip()
        print(f"用户名: {user_name}")
    except:
        print("用户名: 未知")
    
    # 提取星级
    rating = 0
    star_svgs = elem.find_elements(By.CSS_SELECTOR, '.review-rate__star')
    print(f"星星数量: {len(star_svgs)}")
    
    for j, svg in enumerate(star_svgs[:5]):  # 只看前5个
        try:
            fill = driver.execute_script("return window.getComputedStyle(arguments[0]).fill;", svg)
            print(f"  星星 {j+1} fill: '{fill}'")
            
            # 检查是否是亮星
            if fill and 'rgb(0, 217, 197)' in str(fill):
                rating += 1
                print(f"    -> 亮星!")
        except Exception as e:
            print(f"  星星 {j+1} 错误: {e}")
    
    print(f"最终星级: {rating}")

driver.quit()
print("\n调试完成")
