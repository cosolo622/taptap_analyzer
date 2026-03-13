# -*- coding: utf-8 -*-
"""
TapTap评价分析系统 - 评价分类模块 (优化版)

本模块负责对评价内容进行分类，识别评价涉及的问题类型。

优化点：
1. 默认支持多标签分类（一条评价可属于多个分类）
2. 保存所有匹配的分类，不丢失信息
3. 优化分类关键词

@author: TapTap Analyzer
@version: 1.1.0
"""

import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

from config import CATEGORY_KEYWORDS, LOG_CONFIG

logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format'],
    datefmt=LOG_CONFIG['date_format']
)
logger = logging.getLogger(__name__)


class ReviewClassifier:
    """
    评价分类器类
    
    基于关键词匹配对评价内容进行分类，支持多标签分类。
    """
    
    def __init__(self):
        self.category_keywords = CATEGORY_KEYWORDS
        self.keyword_index = self._build_keyword_index()
        logger.info(f"分类器初始化完成，共 {len(self.category_keywords)} 个一级分类")
    
    def _build_keyword_index(self) -> Dict[str, Tuple[str, str]]:
        index = {}
        for primary_cat, secondary_cats in self.category_keywords.items():
            for secondary_cat, keywords in secondary_cats.items():
                for keyword in keywords:
                    index[keyword] = (primary_cat, secondary_cat)
        return index
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        对单条文本进行分类（多标签模式）
        
        Args:
            text: 待分类的文本内容
            
        Returns:
            分类结果字典：
            - primary: 主一级分类（匹配最多的）
            - secondary: 主二级分类
            - all_primaries: 所有匹配的一级分类列表
            - all_secondaries: 所有匹配的二级分类列表
            - matched_keywords: 匹配到的关键词及对应分类
        """
        if not text or not text.strip():
            return {
                'primary': '其他',
                'secondary': '其他',
                'all_primaries': ['其他'],
                'all_secondaries': ['其他'],
                'matched_keywords': []
            }
        
        # 查找匹配的关键词
        matched = []
        text_lower = text.lower()
        
        for keyword, (primary, secondary) in self.keyword_index.items():
            if keyword.lower() in text_lower:
                matched.append({
                    'keyword': keyword,
                    'primary': primary,
                    'secondary': secondary
                })
        
        if not matched:
            return {
                'primary': '其他',
                'secondary': '其他',
                'all_primaries': ['其他'],
                'all_secondaries': ['其他'],
                'matched_keywords': []
            }
        
        # 获取所有匹配的分类（去重）
        all_primaries = list(set(m['primary'] for m in matched))
        all_secondaries = list(set(m['secondary'] for m in matched))
        
        # 统计各分类的匹配次数，选择主分类
        primary_count = defaultdict(int)
        secondary_count = defaultdict(int)
        
        for m in matched:
            primary_count[m['primary']] += 1
            secondary_count[m['secondary']] += 1
        
        # 选择匹配次数最多的分类作为主分类
        best_primary = max(primary_count.keys(), key=lambda x: primary_count[x])
        
        # 在最佳一级分类下选择最佳二级分类
        best_secondary = None
        best_count = 0
        for m in matched:
            if m['primary'] == best_primary:
                if secondary_count[m['secondary']] > best_count:
                    best_count = secondary_count[m['secondary']]
                    best_secondary = m['secondary']
        
        return {
            'primary': best_primary,
            'secondary': best_secondary,
            'all_primaries': all_primaries,
            'all_secondaries': all_secondaries,
            'matched_keywords': matched
        }
    
    def classify_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        results = []
        total = len(texts)
        
        for i, text in enumerate(texts):
            result = self.classify(text)
            results.append(result)
            
            if (i + 1) % 100 == 0:
                logger.info(f"分类进度: {i + 1}/{total}")
        
        logger.info(f"分类完成，共处理 {total} 条文本")
        return results
    
    def get_category_distribution(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        distribution = defaultdict(lambda: defaultdict(int))
        
        for result in results:
            primary = result.get('primary', '其他')
            secondary = result.get('secondary', '其他')
            distribution[primary][secondary] += 1
        
        return {k: dict(v) for k, v in distribution.items()}
    
    def get_primary_distribution(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        distribution = defaultdict(int)
        
        for result in results:
            primary = result.get('primary', '其他')
            distribution[primary] += 1
        
        return dict(distribution)
    
    def get_all_primaries_distribution(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        统计所有一级分类分布（包含多标签）
        
        Args:
            results: 分类结果列表
            
        Returns:
            一级分类的数量统计（每条评价可能贡献多次）
        """
        distribution = defaultdict(int)
        
        for result in results:
            all_primaries = result.get('all_primaries', ['其他'])
            for primary in all_primaries:
                distribution[primary] += 1
        
        return dict(distribution)


def classify_review(review: Dict[str, Any]) -> Dict[str, Any]:
    classifier = ReviewClassifier()
    content = review.get('content', '')
    
    category = classifier.classify(content)
    
    result = review.copy()
    result['primary_category'] = category['primary']
    result['secondary_category'] = category['secondary']
    result['all_primary_categories'] = category['all_primaries']
    result['all_secondary_categories'] = category['all_secondaries']
    result['matched_keywords'] = category['matched_keywords']
    
    return result


def classify_reviews_batch(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    classifier = ReviewClassifier()
    texts = [r.get('content', '') for r in reviews]
    
    categories = classifier.classify_batch(texts)
    
    results = []
    for review, category in zip(reviews, categories):
        result = review.copy()
        result['primary_category'] = category['primary']
        result['secondary_category'] = category['secondary']
        result['all_primary_categories'] = category['all_primaries']
        result['all_secondary_categories'] = category['all_secondaries']
        result['matched_keywords'] = category['matched_keywords']
        results.append(result)
    
    return results


def get_category_statistics(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    classifier = ReviewClassifier()
    
    categories = [
        {
            'primary': r.get('primary_category', '其他'),
            'secondary': r.get('secondary_category', '其他'),
            'all_primaries': r.get('all_primary_categories', ['其他']),
            'all_secondaries': r.get('all_secondary_categories', ['其他'])
        }
        for r in reviews
    ]
    
    return {
        'primary_distribution': classifier.get_primary_distribution(categories),
        'secondary_distribution': classifier.get_category_distribution(categories),
        'all_primaries_distribution': classifier.get_all_primaries_distribution(categories),
        'total_count': len(reviews)
    }


if __name__ == '__main__':
    classifier = ReviewClassifier()
    
    test_texts = [
        "游戏太氪金了，不充钱根本玩不下去",
        "闪退严重，卡顿，根本玩不了",
        "画面精美，玩法有趣，推荐！",
        "外挂太多了，把把遇到挂逼",
        "更新太慢了，版本内容太少",
        "玩了70多个小时，内容消耗快，新鲜感跟不上，需要新地图新角色"
    ]
    
    print("多标签分类测试：")
    for text in test_texts:
        result = classifier.classify(text)
        print(f"文本: {text[:40]}...")
        print(f"主分类: {result['primary']} -> {result['secondary']}")
        print(f"所有分类: {result['all_primaries']}")
        print(f"关键词: {[m['keyword'] for m in result['matched_keywords']]}\n")
