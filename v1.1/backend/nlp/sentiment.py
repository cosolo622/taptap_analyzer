# -*- coding: utf-8 -*-
"""
TapTap评价分析系统 - 情感分析模块 (优化版)

本模块负责对评价内容进行情感分析，判断评价的正负向。

优化点：
1. 处理SnowNLP返回0的异常情况
2. 结合星级评分辅助判断情感
3. 添加文本预处理，提高准确率

@author: TapTap Analyzer
@version: 1.1.0
"""
import logging
import re
from typing import Dict, List, Any, Optional
from snownlp import SnowNLP

from .config import SENTIMENT_THRESHOLDS, LOG_CONFIG

logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format'],
    datefmt=LOG_CONFIG['date_format']
)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    情感分析器类
    
    使用SnowNLP对中文文本进行情感分析，并结合星级评分辅助判断。
    
    替代实现方式：
    - 使用 GLM 大模型 API 进行情感分析
    - 使用 transformers 库的预训练模型
    """
    
    def __init__(self):
        self.positive_threshold = SENTIMENT_THRESHOLDS['positive']
        self.negative_threshold = SENTIMENT_THRESHOLDS['negative']
        logger.info(f"情感分析器初始化完成，阈值: 正向>{self.positive_threshold}, 负向<={self.negative_threshold}")
    
    def _preprocess_text(self, text: str) -> str:
        """
        文本预处理
        
        参数:
            text: 原始文本
            
        返回:
            str: 处理后的文本
        """
        if not text:
            return ""
        
        text = re.sub(r'#+', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(展开|收起|全文)$', '', text)
        
        return text.strip()
    
    def analyze(self, text: str, rating: int = 0) -> Dict[str, Any]:
        """
        分析单条文本的情感
        
        参数:
            text: 待分析的文本内容
            rating: 星级评分(1-5)，用于辅助判断
            
        返回:
            dict: 包含情感分数和标签的字典
            {'score': 0.8, 'label': '正向', 'method': 'snownlp'}
        """
        if not text or not text.strip():
            return {'score': 0.5, 'label': '中性', 'method': 'default'}
        
        processed_text = self._preprocess_text(text)
        
        if not processed_text:
            return {'score': 0.5, 'label': '中性', 'method': 'default'}
        
        try:
            s = SnowNLP(processed_text)
            score = s.sentiments
            
            if score == 0 or score is None:
                positive_words = ['好玩', '喜欢', '推荐', '不错', '很好', '精彩', '有趣', '良心', '优秀', '棒', '赞']
                negative_words = ['垃圾', '差', '烂', '卡', '闪退', '氪金', '坑', '骗', '失望', '垃圾', '恶心']
                
                pos_count = sum(1 for w in positive_words if w in processed_text)
                neg_count = sum(1 for w in negative_words if w in processed_text)
                
                if pos_count > neg_count:
                    score = 0.6
                elif neg_count > pos_count:
                    score = 0.4
                else:
                    score = 0.5
            
            if rating > 0:
                rating_score = (rating - 1) / 4
                
                if abs(score - rating_score) > 0.3:
                    score = score * 0.7 + rating_score * 0.3
            
            if score > self.positive_threshold:
                label = '正向'
            elif score <= self.negative_threshold:
                label = '负向'
            else:
                label = '中性'
            
            return {
                'score': round(score, 4),
                'label': label,
                'method': 'snownlp'
            }
            
        except Exception as e:
            logger.warning(f"情感分析失败: {e}, 文本: {text[:50]}...")
            
            if rating > 0:
                if rating >= 4:
                    return {'score': 0.7, 'label': '正向', 'method': 'rating_fallback'}
                elif rating <= 2:
                    return {'score': 0.3, 'label': '负向', 'method': 'rating_fallback'}
                else:
                    return {'score': 0.5, 'label': '中性', 'method': 'rating_fallback'}
            
            return {'score': 0.5, 'label': '中性', 'method': 'error_fallback'}
    
    def analyze_batch(self, texts: List[str], ratings: List[int] = None) -> List[Dict[str, Any]]:
        """
        批量分析文本情感
        
        参数:
            texts: 文本列表
            ratings: 星级列表（可选）
            
        返回:
            list[dict]: 情感分析结果列表
        """
        results = []
        total = len(texts)
        
        for i, text in enumerate(texts):
            rating = ratings[i] if ratings and i < len(ratings) else 0
            result = self.analyze(text, rating)
            results.append(result)
            
            if (i + 1) % 100 == 0:
                logger.info(f"情感分析进度: {i + 1}/{total}")
        
        logger.info(f"情感分析完成，共处理 {total} 条文本")
        return results
    
    def get_sentiment_distribution(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        统计情感分布
        
        参数:
            results: 情感分析结果列表
            
        返回:
            dict: {'正向': 10, '中性': 5, '负向': 3}
        """
        distribution = {'正向': 0, '中性': 0, '负向': 0}
        
        for result in results:
            label = result.get('label', '中性')
            if label in distribution:
                distribution[label] += 1
        
        return distribution


def analyze_review_sentiment(review: Dict[str, Any]) -> Dict[str, Any]:
    """
    便捷函数：分析单条评价的情感
    
    参数:
        review: 评价字典，需包含 'content' 和 'rating' 字段
        
    返回:
        dict: 添加了情感分析结果的评价字典
    """
    analyzer = SentimentAnalyzer()
    content = review.get('content', '')
    rating = review.get('rating', 0)
    
    sentiment = analyzer.analyze(content, rating)
    
    result = review.copy()
    result['sentiment_score'] = sentiment['score']
    result['sentiment_label'] = sentiment['label']
    
    return result


def analyze_reviews_batch(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    便捷函数：批量分析评价情感
    
    参数:
        reviews: 评价列表
        
    返回:
        list[dict]: 添加了情感分析结果的评价列表
    """
    analyzer = SentimentAnalyzer()
    texts = [r.get('content', '') for r in reviews]
    ratings = [r.get('rating', 0) for r in reviews]
    
    sentiments = analyzer.analyze_batch(texts, ratings)
    
    results = []
    for review, sentiment in zip(reviews, sentiments):
        result = review.copy()
        result['sentiment_score'] = sentiment['score']
        result['sentiment_label'] = sentiment['label']
        results.append(result)
    
    return results


if __name__ == '__main__':
    analyzer = SentimentAnalyzer()
    
    test_cases = [
        ("游戏好玩，电脑端就玩过一阵子，手游现在已经打到神探段位了", 3),
        ("太卡了，闪退严重", 1),
        ("还行吧，一般般", 3),
        ("良心游戏，推荐！", 5),
    ]
    
    for text, rating in test_cases:
        result = analyzer.analyze(text, rating)
        print(f"文本: {text[:30]}...")
        print(f"星级: {rating}星")
        print(f"结果: {result}\n")
