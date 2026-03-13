# -*- coding: utf-8 -*-
"""
调试脚本 - 从页面JSON数据中获取星级
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

# 查找self.__next_f.push中的数据
print("\n查找页面JSON数据...")
pattern = r'self\.__next_f\.push\(\[.*?,(.*?)\]\)'
matches = re.findall(pattern, page_source, re.DOTALL)

all_ratings = []

for match in matches:
    try:
        data_str = match.strip()
        if data_str.startswith('"') and data_str.endswith('"'):
            data_str = data_str.encode().decode('unicode_escape')
        
        # 查找rating字段
        rating_matches = re.findall(r'"rating"\s*:\s*(\d)', data_str)
        for r in rating_matches:
            all_ratings.append(int(r))
        
        # 查找score字段
        score_matches = re.findall(r'"score"\s*:\s*(\d)', data_str)
        for s in score_matches:
            if int(s) <= 5:  # 只取1-5的分数
                all_ratings.append(int(s))
    except:
        pass

print(f"\n找到 {len(all_ratings)} 个rating/score值")
print(f"值: {all_ratings[:50]}")

# 统计分布
from collections import Counter
rating_dist = Counter(all_ratings)
print(f"\n分布: {dict(sorted(rating_dist.items()))}")

driver.quit()
print("\n调试完成")
