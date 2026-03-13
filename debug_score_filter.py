# -*- coding: utf-8 -*-
"""
调试脚本 - 访问不同评分的评价页面
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

# 尝试不同的评分URL
for score in [3, 1]:
    url = f"https://www.taptap.cn/app/258720/review?score={score}"
    print(f"\n{'='*60}")
    print(f"访问页面: {url}")
    print(f"{'='*60}")
    
    driver.get(url)
    time.sleep(5)
    
    # 查找评价元素
    review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
    print(f"找到 {len(review_elements)} 个评价元素")
    
    if review_elements:
        # 检查前3个评价的星级
        for i, elem in enumerate(review_elements[:3]):
            # 获取用户名
            try:
                user_elem = elem.find_element(By.CSS_SELECTOR, '.review-item__author-name')
                user_name = user_elem.text.strip()
            except:
                user_name = "未知"
            
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
            
            print(f"  #{i+1}: {user_name} | {bright_count}星")

driver.quit()
print("\n调试完成")
