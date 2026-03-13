# -*- coding: utf-8 -*-
"""
调试脚本 - 从__NEXT_DATA__中提取评价数据
"""

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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
print("\n查找__NEXT_DATA__...")
match = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', page_source, re.DOTALL)

if match:
    try:
        data = json.loads(match.group(1))
        print("成功解析__NEXT_DATA__")
        
        # 递归查找rating字段
        def find_all_ratings(obj, path=""):
            ratings = []
            if isinstance(obj, dict):
                if 'rating' in obj and isinstance(obj['rating'], int):
                    ratings.append((path, obj['rating']))
                for key, value in obj.items():
                    ratings.extend(find_all_ratings(value, f"{path}.{key}"))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    ratings.extend(find_all_ratings(item, f"{path}[{i}]"))
            return ratings
        
        ratings = find_all_ratings(data)
        print(f"\n找到 {len(ratings)} 个rating字段:")
        for path, rating in ratings[:20]:
            print(f"  {path}: {rating}")
        
        # 查找created_at字段
        def find_all_dates(obj, path=""):
            dates = []
            if isinstance(obj, dict):
                if 'created_at' in obj and isinstance(obj['created_at'], (int, float)):
                    dates.append((path, obj['created_at']))
                for key, value in obj.items():
                    dates.extend(find_all_dates(value, f"{path}.{key}"))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    dates.extend(find_all_dates(item, f"{path}[{i}]"))
            return dates
        
        dates = find_all_dates(data)
        print(f"\n找到 {len(dates)} 个created_at字段:")
        for path, ts in dates[:10]:
            import time
            date_str = time.strftime('%Y-%m-%d', time.localtime(ts))
            print(f"  {path}: {ts} -> {date_str}")
        
        # 保存完整数据到文件
        with open('next_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("\n完整数据已保存到 next_data.json")
        
    except Exception as e:
        print(f"解析失败: {e}")
else:
    print("未找到__NEXT_DATA__")

driver.quit()
print("\n调试完成")
