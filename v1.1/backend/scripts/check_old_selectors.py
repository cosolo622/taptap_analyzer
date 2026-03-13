# -*- coding: utf-8 -*-
"""
检查老爬虫抓取的内容选择器
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
driver.get('https://www.taptap.cn/app/258720/review')
import time
time.sleep(5)

review_items = driver.find_elements(By.CSS_SELECTOR, '.review-item')
print(f'.review-item 数量: {len(review_items)}')

for i, range(min(3, len(review_items))):
    item = review_items[i]
    print(f'\n=== 评价 {i+1} ===')
    
    # 检查所有可能的内容选择器
    selectors = [
        '.review-text',
        '.content',
        '.item-text',
        '.review-item__contents',
        '.review-item__content',
        '.review-comment-item__content',
    ]
    
    for sel in selectors:
        try:
                elems = item.find_elements(By.CSS_SELECTOR, sel)
                if elems:
                    for j, range(min(2, len(elems)):
                        text = elems[j].text
                        if text and len(text.strip()) > 5:
                            print(f'{sel}[{j}]: {text[:100]}...')
        except:
            pass

driver.quit()
