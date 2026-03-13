# -*- coding: utf-8 -*-
"""
调试脚本 - 从Selenium网络请求中获取API数据
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager

# 配置Selenium捕获网络请求
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')

# 启用性能日志
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

url = "https://www.taptap.cn/app/258720/review"
print(f"访问页面: {url}")
driver.get(url)
time.sleep(5)

# 获取网络日志
logs = driver.get_log('performance')
print(f"\n获取到 {len(logs)} 条网络日志")

# 查找包含review的API请求
for log in logs:
    try:
        message = json.loads(log['message'])
        if message['message']['method'] == 'Network.responseReceived':
            response = message['message']['params']['response']
            url = response.get('url', '')
            if 'review' in url.lower() or 'app' in url.lower():
                print(f"\n找到API: {url}")
                print(f"  状态码: {response.get('status')}")
                
                # 尝试获取响应内容
                request_id = message['message']['params']['requestId']
                try:
                    body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                    body_text = body.get('body', '')[:500]
                    print(f"  响应内容: {body_text}")
                except:
                    pass
    except:
        pass

driver.quit()
print("\n调试完成")
