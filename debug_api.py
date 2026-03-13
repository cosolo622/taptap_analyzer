# -*- coding: utf-8 -*-
"""
调试脚本 - 从TapTap API获取评价数据
"""

import requests
import json

# TapTap评价API
app_id = 258720
url = f"https://www.taptap.cn/webapiv2/review/v2/by-app?app_id={app_id}&limit=10&order=latest"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': f'https://www.taptap.cn/app/{app_id}/review',
}

print(f"请求API: {url}")
response = requests.get(url, headers=headers)
print(f"状态码: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    # 打印结构
    print(f"\n响应数据结构:")
    print(f"  keys: {list(data.keys())}")
    
    if 'data' in data:
        reviews = data['data']
        print(f"  评价数量: {len(reviews)}")
        
        for i, review in enumerate(reviews[:5]):
            print(f"\n评价 #{i+1}:")
            
            # 查找rating
            if 'rating' in review:
                print(f"  rating: {review['rating']}")
            
            if 'moment' in review:
                moment = review['moment']
                if 'author' in moment:
                    author = moment['author']
                    if 'user' in author:
                        user = author['user']
                        print(f"  user_name: {user.get('name', '未知')}")
                
                # 查找created_at
                if 'created_at' in moment:
                    import time
                    created_at = moment['created_at']
                    date_str = time.strftime('%Y-%m-%d', time.localtime(created_at))
                    print(f"  date: {date_str}")
            
            # 打印所有键
            print(f"  所有键: {list(review.keys())}")
            
            # 打印完整数据（部分）
            print(f"  数据: {json.dumps(review, ensure_ascii=False, indent=2)[:500]}...")
else:
    print(f"请求失败: {response.text[:500]}")
