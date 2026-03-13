# -*- coding: utf-8 -*-
"""
调试脚本 - 重新检查星星显示方式
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

# 查找评价元素
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
print(f"找到 {len(review_elements)} 个评价元素\n")

# 检查前10个评价
for i, elem in enumerate(review_elements[:10]):
    # 获取用户名
    try:
        user_elem = elem.find_element(By.CSS_SELECTOR, '.review-item__author-name')
        user_name = user_elem.text.strip()
    except:
        user_name = "未知"
    
    # 获取星级 - 详细分析
    star_svgs = elem.find_elements(By.CSS_SELECTOR, '.review-rate__star')
    
    # 分别统计前5个和后5个
    front_5_colors = []
    back_5_colors = []
    
    for j, svg in enumerate(star_svgs):
        try:
            fill = driver.execute_script("return window.getComputedStyle(arguments[0]).fill;", svg)
            if j < 5:
                front_5_colors.append(fill)
            else:
                back_5_colors.append(fill)
        except:
            pass
    
    # 统计亮星
    bright_in_front = sum(1 for c in front_5_colors if 'rgb(0, 217, 197)' in c)
    bright_in_back = sum(1 for c in back_5_colors if 'rgb(0, 217, 197)' in c)
    
    print(f"#{i+1}: {user_name}")
    print(f"  前5个星星颜色: {front_5_colors}")
    print(f"  后5个星星颜色: {back_5_colors}")
    print(f"  前5个亮星数: {bright_in_front}, 后5个亮星数: {bright_in_back}")
    print(f"  总亮星数: {bright_in_front + bright_in_back}")
    print()

driver.quit()
print("调试完成")
