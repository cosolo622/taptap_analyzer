# -*- coding: utf-8 -*-
"""
TapTap评价分析系统 - 模拟数据生成器

当API不可用时，使用模拟数据演示程序功能。

@author: TapTap Analyzer
@version: 1.0.0
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 模拟评价内容库
REVIEW_TEMPLATES = {
    '正向': [
        "游戏非常好玩，和朋友一起玩特别开心！",
        "画质精美，玩法有趣，推荐大家下载体验。",
        "良心游戏，不氪金也能玩得很开心。",
        "操作流畅，画面精美，是一款难得的好游戏。",
        "游戏体验很好，匹配机制公平，推荐！",
        "玩法多样，每次玩都有新鲜感。",
        "社交属性强，认识了很多新朋友。",
        "游戏平衡性做得很好，每个角色都有特色。",
        "更新频繁，开发者很用心。",
        "新手友好，教程详细，上手很快。"
    ],
    '中性': [
        "游戏还行吧，一般般。",
        "有待改进，希望能优化一下。",
        "玩法还可以，但是有些地方需要优化。",
        "中规中矩，没什么特别的亮点。",
        "还可以，但是玩久了会有点无聊。",
        "游戏还行，就是有点肝。",
        "还行吧，打发时间可以。",
        "一般般，没有想象中那么好玩。"
    ],
    '负向': [
        "太氪金了，不充钱根本玩不下去。",
        "闪退严重，根本玩不了，希望能尽快修复。",
        "外挂太多了，把把遇到挂逼，体验很差。",
        "卡顿严重，玩着玩着就卡死了。",
        "匹配机制太差了，把把遇到坑队友。",
        "更新太慢了，版本内容太少。",
        "客服态度差，反馈问题没人管。",
        "游戏平衡性太差，有些角色太强了。",
        "广告太多了，影响游戏体验。",
        "新手引导太差，完全不知道怎么玩。"
    ]
}

# 分类关键词映射
CATEGORY_MAPPING = {
    '氪金': ('商业化问题', '太氪金/收费高'),
    '充钱': ('商业化问题', '太氪金/收费高'),
    '闪退': ('技术问题', '闪退/崩溃'),
    '卡顿': ('技术问题', '卡顿/掉帧'),
    '外挂': ('外挂问题', '外挂/作弊多'),
    '挂逼': ('外挂问题', '外挂/作弊多'),
    '匹配': ('玩法问题', '匹配机制问题'),
    '更新': ('版本问题', '更新慢/内容少'),
    '客服': ('客服问题', '客服态度差'),
    '广告': ('商业化问题', '广告过多'),
    '好玩': ('正向评价', '游戏好玩'),
    '精美': ('正向评价', '画面精美'),
    '良心': ('正向评价', '良心游戏'),
    '流畅': ('正向评价', '操作流畅'),
}


def generate_mock_reviews(
    game_name: str = "鹅鸭杀",
    days: int = 14,
    count: int = 200
) -> List[Dict[str, Any]]:
    """
    生成模拟评价数据
    
    Args:
        game_name: 游戏名称
        days: 过去N天
        count: 生成数量
        
    Returns:
        模拟评价列表
        
    示例：
        reviews = generate_mock_reviews("鹅鸭杀", days=14, count=200)
    """
    reviews = []
    end_date = datetime.now()
    
    # 情感分布比例
    sentiment_weights = [0.4, 0.3, 0.3]  # 正向、中性、负向
    
    for i in range(count):
        # 随机日期
        days_ago = random.randint(0, days - 1)
        review_date = end_date - timedelta(days=days_ago)
        
        # 随机情感
        sentiment = random.choices(
            ['正向', '中性', '负向'],
            weights=sentiment_weights
        )[0]
        
        # 随机评价内容
        content = random.choice(REVIEW_TEMPLATES[sentiment])
        
        # 根据情感确定星级
        if sentiment == '正向':
            rating = random.choice([4, 5, 5])
        elif sentiment == '中性':
            rating = random.choice([3, 3, 4])
        else:
            rating = random.choice([1, 2, 2])
        
        # 确定分类
        primary_cat = '其他'
        secondary_cat = '其他'
        
        for keyword, (primary, secondary) in CATEGORY_MAPPING.items():
            if keyword in content:
                primary_cat = primary
                secondary_cat = secondary
                break
        
        # 生成评价
        review = {
            'review_date': review_date.strftime('%Y-%m-%d'),
            'rating': rating,
            'content': content,
            'play_time': random.randint(10, 5000),
            'user_name': f'玩家{random.randint(10000, 99999)}',
            'device': random.choice(['iPhone 14', 'iPhone 15', 'Android', 'iPad', '华为Mate60']),
            'sentiment_label': sentiment,
            'sentiment_score': random.uniform(0.1, 0.9) if sentiment == '正向' else (
                random.uniform(0.4, 0.6) if sentiment == '中性' else random.uniform(0.1, 0.4)
            ),
            'primary_category': primary_cat,
            'secondary_category': secondary_cat,
            'matched_keywords': []
        }
        
        reviews.append(review)
    
    # 按日期排序
    reviews.sort(key=lambda x: x['review_date'], reverse=True)
    
    return reviews


if __name__ == '__main__':
    reviews = generate_mock_reviews("鹅鸭杀", days=14, count=10)
    for r in reviews:
        print(f"{r['review_date']} | {r['rating']}星 | {r['sentiment_label']} | {r['content'][:30]}...")
