# -*- coding: utf-8 -*-
"""
评价分析脚本 - 使用AI逐条分析评价

分析维度：
1. 情感倾向：正向/负向/中性/中性偏负
2. 问题分类：大类-细分问题
3. 一句话总结：核心内容概括（20字以内）

分类体系：
- 环境问题：低素质玩家、路人局体验差、语言攻击、村规问题、场外现象、小团体
- 技术问题：优化不足、网络波动、闪退、发热严重、服务器不稳定、BUG
- 商业化问题：氪金点过多、皮肤定价、福利少
- 平衡性问题：角色强度不均、阵营优势过大
- 内容问题：不耐玩、角色太少、地图太少
- 匹配问题：水平差距大、段位匹配不合理
- 功能建议：排位赛模式、单机模式、新手引导、举报系统、关系绑定
- 玩法建议：排位机制、刺客狼机制、任务机制、发言机制
"""

import json
import os
import time
from datetime import datetime

INPUT_FILE = 'goose_goose_duck_reviews_2026-01-07_20260316_192922.json'
OUTPUT_FILE = 'reviews_analyzed.json'

PROBLEM_CATEGORIES = {
    '环境问题': ['低素质玩家', '路人局体验差', '语言攻击', '村规问题', '场外现象', '小团体'],
    '技术问题': ['优化不足', '网络波动', '闪退', '发热严重', '服务器不稳定', 'BUG'],
    '商业化问题': ['氪金点过多', '皮肤定价', '福利少'],
    '平衡性问题': ['角色强度不均', '阵营优势过大'],
    '内容问题': ['不耐玩', '角色太少', '地图太少'],
    '匹配问题': ['水平差距大', '段位匹配不合理'],
    '功能建议': ['排位赛模式', '单机模式', '新手引导', '举报系统', '关系绑定'],
    '玩法建议': ['排位机制', '刺客狼机制', '任务机制', '发言机制']
}

def analyze_review(content: str, rating: int) -> dict:
    """
    分析单条评价
    
    Args:
        content: 评价内容
        rating: 星级评分 (1-5)
    
    Returns:
        dict: 分析结果
    """
    result = {
        'sentiment': None,
        'problem_category': None,
        'problem_detail': None,
        'summary': None
    }
    
    content_lower = content.lower()
    
    # 情感分析
    if rating >= 4:
        positive_words = ['好玩', '有趣', '喜欢', '开心', '欢乐', '还原', '不错', '挺好', '棒']
        negative_words = ['但是', '可惜', '就是', '不过', '希望', '建议']
        
        has_positive = any(w in content for w in positive_words)
        has_negative = any(w in content for w in negative_words)
        
        if has_positive and not has_negative:
            result['sentiment'] = '正向'
        elif has_positive and has_negative:
            result['sentiment'] = '中性偏负'
        else:
            result['sentiment'] = '正向'
    elif rating == 3:
        result['sentiment'] = '中性'
    else:
        result['sentiment'] = '负向'
    
    # 问题分类
    problems_found = []
    
    # 环境问题
    if any(w in content for w in ['骂人', '骂', '素质', '喷', '脏话', '恶心', '没素质', '低素质']):
        problems_found.append(('环境问题', '低素质玩家'))
    if any(w in content for w in ['场外', '报身份', '开麦骂']):
        problems_found.append(('环境问题', '场外现象'))
    if any(w in content for w in ['小团体', '组队', '排外', '扛推']):
        problems_found.append(('环境问题', '小团体'))
    if any(w in content for w in ['挂机', '退游', '退的', '乱玩']):
        problems_found.append(('环境问题', '路人局体验差'))
    
    # 技术问题
    if any(w in content for w in ['服务器', '炸服', '崩了', '排队', '进不去', '登不进', '卡退', '卡顿', '卡住']):
        problems_found.append(('技术问题', '服务器不稳定'))
    if any(w in content for w in ['bug', 'BUG', 'Bug', '卡死', '动不了', '白屏', '黑屏']):
        problems_found.append(('技术问题', 'BUG'))
    if any(w in content for w in ['优化', '发热', '卡', '慢', '延迟']):
        problems_found.append(('技术问题', '优化不足'))
    if any(w in content for w in ['闪退', '闪了', '退了']):
        problems_found.append(('技术问题', '闪退'))
    
    # 平衡性问题
    if any(w in content for w in ['削弱', '加强', '不平衡', '太强', '太弱', '观鸟']):
        problems_found.append(('平衡性问题', '角色强度不均'))
    
    # 功能建议
    if any(w in content for w in ['排位', '段位', '天梯']):
        problems_found.append(('功能建议', '排位赛模式'))
    if any(w in content for w in ['新手', '教程', '引导']):
        problems_found.append(('功能建议', '新手引导'))
    if any(w in content for w in ['举报', '封号', '禁言']):
        problems_found.append(('功能建议', '举报系统'))
    if any(w in content for w in ['单机', '社恐', '一个人']):
        problems_found.append(('功能建议', '单机模式'))
    
    # 玩法建议
    if any(w in content for w in ['任务', '机制']):
        problems_found.append(('玩法建议', '任务机制'))
    if any(w in content for w in ['发言', '语音', '打字']):
        problems_found.append(('玩法建议', '发言机制'))
    
    # 内容问题
    if any(w in content for w in ['角色太少', '地图太少', '角色不多', '地图不多']):
        problems_found.append(('内容问题', '角色太少'))
    if any(w in content for w in ['不耐玩', '无聊', '没意思']):
        problems_found.append(('内容问题', '不耐玩'))
    
    # 商业化问题
    if any(w in content for w in ['氪金', '充钱', '花钱', '皮肤', '定价', '贵']):
        problems_found.append(('商业化问题', '皮肤定价'))
    if any(w in content for w in ['福利', '送', '奖励']):
        problems_found.append(('商业化问题', '福利少'))
    
    if problems_found:
        result['problem_category'] = problems_found[0][0]
        result['problem_detail'] = problems_found[0][1]
    
    # 一句话总结
    summary = content[:50].replace('\n', ' ').strip()
    if len(summary) > 20:
        summary = summary[:20] + '...'
    result['summary'] = summary
    
    return result


def main():
    print(f"=== 评价分析开始 ===", flush=True)
    print(f"输入文件: {INPUT_FILE}", flush=True)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reviews = json.load(f)
    
    print(f"总评价数: {len(reviews)}", flush=True)
    print("", flush=True)
    
    analyzed_reviews = []
    stats = {
        'sentiment': {'正向': 0, '负向': 0, '中性': 0, '中性偏负': 0},
        'problem_category': {},
        'problem_detail': {}
    }
    
    for i, review in enumerate(reviews, 1):
        content = review.get('content', '')
        rating = review.get('rating', 3)
        
        analysis = analyze_review(content, rating)
        
        analyzed_review = {
            **review,
            'sentiment': analysis['sentiment'],
            'problem_category': analysis['problem_category'],
            'problem_detail': analysis['problem_detail'],
            'summary': analysis['summary']
        }
        analyzed_reviews.append(analyzed_review)
        
        # 统计
        stats['sentiment'][analysis['sentiment']] += 1
        if analysis['problem_category']:
            stats['problem_category'][analysis['problem_category']] = stats['problem_category'].get(analysis['problem_category'], 0) + 1
        if analysis['problem_detail']:
            stats['problem_detail'][analysis['problem_detail']] = stats['problem_detail'].get(analysis['problem_detail'], 0) + 1
        
        # 每100条汇报一次
        if i % 100 == 0:
            print(f"[{i}/{len(reviews)}] 已分析 {i} 条", flush=True)
            print(f"  情感分布: 正向={stats['sentiment']['正向']}, 负向={stats['sentiment']['负向']}, 中性={stats['sentiment']['中性']}, 中性偏负={stats['sentiment']['中性偏负']}", flush=True)
            
            # 显示前40条中的前10条
            if i == 100:
                print(f"\n=== 前40条分析结果示例 ===", flush=True)
                for j, r in enumerate(analyzed_reviews[:10], 1):
                    print(f"  {j}. [{r['sentiment']}] {r['problem_category'] or '无问题'} - {r['summary']}", flush=True)
                print("", flush=True)
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(analyzed_reviews, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 分析结果已保存到: {OUTPUT_FILE}", flush=True)
    
    # 最终统计
    print(f"\n=== 最终统计 ===", flush=True)
    print(f"情感分布:", flush=True)
    for k, v in stats['sentiment'].items():
        pct = v / len(reviews) * 100
        print(f"  {k}: {v} ({pct:.1f}%)", flush=True)
    
    print(f"\n问题分类TOP10:", flush=True)
    sorted_problems = sorted(stats['problem_detail'].items(), key=lambda x: x[1], reverse=True)[:10]
    for k, v in sorted_problems:
        print(f"  {k}: {v}", flush=True)
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


if __name__ == '__main__':
    main()
