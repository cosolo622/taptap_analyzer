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

# 获取页面源码
page_source = driver.page_source

# 查找__NEXT_DATA__
print("\n查找页面数据...")
patterns = [
    r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    r'self\.__next_f\.push\(\[.*?,(.*?)\]\)',
]

for pattern in patterns:
    matches = re.findall(pattern, page_source, re.DOTALL)
    for match in matches:
        try:
            data_str = match.strip()
            if data_str.startswith('"') and data_str.endswith('"'):
                data_str = data_str.encode().decode('unicode_escape')
            
            data = json.loads(data_str)
            
            # 递归查找rating字段
            def find_ratings(obj, path=""):
                ratings = []
                if isinstance(obj, dict):
                    if 'rating' in obj:
                        ratings.append((path + '.rating', obj['rating']))
                    for key, value in obj.items():
                        ratings.extend(find_ratings(value, path + '.' + key))
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        ratings.extend(find_ratings(item, path + f'[{i}]'))
                return ratings
            
            ratings = find_ratings(data)
            if ratings:
                print(f"\n找到 {len(ratings)} 个rating字段:")
                for path, rating in ratings[:20]:
                    print(f"  {path}: {rating}")
        except Exception as e:
            pass

# 也尝试从HTML中查找rating
print("\n从HTML中查找rating...")
rating_matches = re.findall(r'"rating"\s*:\s*(\d)', page_source)
if rating_matches:
    print(f"找到 {len(rating_matches)} 个rating: {rating_matches[:20]}")

# 查找review-item的HTML
print("\n查找review-item HTML...")
review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-item')
if review_elements:
    elem = review_elements[0]
    html = elem.get_attribute('outerHTML')
    # 查找rating相关
    rating_in_html = re.findall(r'rating["\']?\s*[:=]\s*["\']?(\d)', html, re.IGNORECASE)
    print(f"HTML中的rating: {rating_in_html}")
    
    # 打印部分HTML
    print(f"\nreview-item HTML (前1000字符):\n{html[:1000]}")

driver.quit()
print("\n调试完成")
