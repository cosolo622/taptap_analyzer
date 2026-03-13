# -*- coding: utf-8 -*-
"""
GLM大模型分析模块

使用智谱GLM大模型对评价进行智能分析：
- 情感分析
- 问题分类（灵活归纳，不限定固定标签）
- 一句话总结

替代实现方式：
- 使用 OpenAI GPT API
- 使用本地部署的开源模型（如 Qwen、ChatGLM）
- 使用关键词匹配（准确率较低）
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GLM_API_KEY = os.environ.get('GLM_API_KEY', '')
GLM_API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'


def analyze_with_glm(content: str, rating: int = 0) -> Dict[str, Any]:
    """
    使用GLM大模型分析单条评价
    
    参数:
        content: 评价内容
        rating: 星级评分(1-5)
        
    返回:
        dict: {
            'sentiment': '正向/中性/负向',
            'issues': ['大类-细分问题', ...],
            'summary': '一句话总结'
        }
        
    示例:
        >>> result = analyze_with_glm("游戏好玩但段位机制需改进", 4)
        >>> print(result)
        {
            'sentiment': '正向',
            'issues': ['玩法建议-排位机制'],
            'summary': '游戏好玩但段位机制需改进'
        }
    """
    if not content or not content.strip():
        return {
            'sentiment': '中性',
            'issues': [],
            'summary': ''
        }
    
    if not GLM_API_KEY:
        logger.warning("GLM_API_KEY未配置，使用关键词匹配降级方案")
        return _fallback_analyze(content, rating)
    
    try:
        import requests
        
        prompt = f"""请分析以下游戏评价，输出JSON格式结果。

评价内容：{content}
星级：{rating}星

请输出以下字段：
1. sentiment: 情感倾向，取值：正向/中性/负向
2. issues: 问题分类列表，格式为"大类-细分问题"，如：
   - 环境问题-低素质玩家
   - 技术问题-优化不足
   - 商业化问题-氪金点过多
   - 玩法建议-排位机制
   如果是正面评价没有问题，返回空列表[]
3. summary: 一句话总结评价核心内容（不超过50字）

只输出JSON，不要其他内容。"""

        headers = {
            'Authorization': f'Bearer {GLM_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'glm-4-flash',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 500
        }
        
        response = requests.post(GLM_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content_text = result['choices'][0]['message']['content']
        
        json_match = content_text[content_text.find('{'):content_text.rfind('}')+1]
        parsed = json.loads(json_match)
        
        return {
            'sentiment': parsed.get('sentiment', '中性'),
            'issues': parsed.get('issues', []),
            'summary': parsed.get('summary', '')
        }
        
    except Exception as e:
        logger.warning(f"GLM分析失败: {e}，使用降级方案")
        return _fallback_analyze(content, rating)


def _fallback_analyze(content: str, rating: int) -> Dict[str, Any]:
    """
    降级方案：关键词匹配分析
    
    参数:
        content: 评价内容
        rating: 星级评分
        
    返回:
        dict: 分析结果
    """
    from .classifier import ReviewClassifier
    from .sentiment import SentimentAnalyzer
    
    classifier = ReviewClassifier()
    sentiment_analyzer = SentimentAnalyzer()
    
    category = classifier.classify(content)
    sentiment = sentiment_analyzer.analyze(content, rating)
    
    issues = []
    if category['primary'] != '其他' and category['primary'] != '正向评价':
        issues.append(f"{category['primary']}-{category['secondary']}")
    
    summary = _generate_summary(content)
    
    return {
        'sentiment': sentiment['label'],
        'issues': issues,
        'summary': summary
    }


def _generate_summary(content: str, max_length: int = 50) -> str:
    """
    生成一句话摘要（基于关键句提取）
    
    参数:
        content: 评价内容
        max_length: 最大长度
        
    返回:
        str: 摘要文本
    """
    if not content:
        return ""
    
    sentences = content.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    priority_keywords = [
        '建议', '希望', '应该', '需要', '问题', '缺点', '优点',
        '太', '很', '非常', '严重', '太多', '太少',
        '好玩', '垃圾', '卡', '闪退', '氪金', '外挂', '匹配'
    ]
    
    scored_sentences = []
    for sent in sentences:
        score = 0
        for kw in priority_keywords:
            if kw in sent:
                score += 1
        if 10 < len(sent) < 50:
            score += 1
        scored_sentences.append((sent, score))
    
    scored_sentences.sort(key=lambda x: -x[1])
    
    summary = ""
    for sent, score in scored_sentences:
        if len(summary) + len(sent) <= max_length:
            if summary:
                summary += "；"
            summary += sent[:max_length - len(summary)]
        else:
            break
    
    if not summary:
        summary = content[:max_length]
    
    return summary


def analyze_reviews_batch_glm(reviews: List[Dict[str, Any]], use_glm: bool = True) -> List[Dict[str, Any]]:
    """
    批量分析评价（支持GLM或降级方案）
    
    参数:
        reviews: 评价列表，每个评价需包含 'content' 和 'rating' 字段
        use_glm: 是否使用GLM大模型
        
    返回:
        list[dict]: 添加了分析结果的评价列表
        每个评价新增字段：
        - sentiment: 情感倾向
        - issues: 问题分类列表
        - summary: 一句话总结
        - problem_category: 问题分类字符串（逗号分隔）
    """
    results = []
    total = len(reviews)
    
    for i, review in enumerate(reviews):
        content = review.get('content', '')
        rating = review.get('rating', 0)
        
        if use_glm and GLM_API_KEY:
            analysis = analyze_with_glm(content, rating)
        else:
            analysis = _fallback_analyze(content, rating)
        
        result = review.copy()
        result['sentiment'] = analysis['sentiment']
        result['issues'] = analysis['issues']
        result['summary'] = analysis['summary']
        result['problem_category'] = ', '.join(analysis['issues']) if analysis['issues'] else None
        
        results.append(result)
        
        if (i + 1) % 10 == 0:
            logger.info(f"分析进度: {i + 1}/{total}")
    
    logger.info(f"分析完成，共处理 {total} 条评价")
    return results


if __name__ == '__main__':
    test_reviews = [
        {'content': '游戏好玩但段位机制需改进，建议优化排位积分规则', 'rating': 4},
        {'content': '闪退严重，卡顿，根本玩不了', 'rating': 1},
        {'content': '画面精美，玩法有趣，推荐！', 'rating': 5},
    ]
    
    results = analyze_reviews_batch_glm(test_reviews, use_glm=False)
    for r in results:
        print(f"内容: {r['content'][:30]}...")
        print(f"情感: {r['sentiment']}")
        print(f"问题: {r['issues']}")
        print(f"摘要: {r['summary']}")
        print(f"分类: {r['problem_category']}")
        print()
