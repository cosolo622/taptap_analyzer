# -*- coding: utf-8 -*-
"""
调试脚本 - 尝试不同的TapTap API端点
"""

import requests
import json

app_id = 258720

# 尝试不同的API端点
api_endpoints = [
    f"https://www.taptap.cn/webapi/v2/app/{app_id}/reviews",
    f"https://www.taptap.cn/api/v2/app/{app_id}/reviews",
    f"https://www.taptap.cn/webapiv2/app/{app_id}/reviews",
    f"https://api.taptap.cn/v2/app/{app_id}/reviews",
    f"https://www.taptap.cn/webapi/review/v2/list?app_id={app_id}",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': f'https://www.taptap.cn/app/{app_id}/review',
}

for url in api_endpoints:
    print(f"\n尝试: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  成功! keys: {list(data.keys())}")
            if 'data' in data:
                print(f"  data数量: {len(data['data'])}")
            break
        else:
            print(f"  响应: {response.text[:100]}")
    except Exception as e:
        print(f"  错误: {e}")
