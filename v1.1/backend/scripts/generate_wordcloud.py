# -*- coding: utf-8 -*-
"""
生成词云图
按周生成词云图片，保存到output/charts目录
"""
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
import jieba

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, init_db
from models.review import Review
from sqlalchemy import func

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'charts'))

# 停用词列表
STOPWORDS = set([
    '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', '那', '他', '她', '它', '们', '这个', '那个', '什么', '怎么',
    '可以', '因为', '所以', '但是', '如果', '还是', '或者', '而且', '然后',
    '比较', '真的', '非常', '特别', '已经', '一直', '一下', '一些',
    '觉得', '感觉', '可能', '应该', '需要', '希望', '建议', '游戏', '玩家',
    '鹅鸭杀', '鹅', '鸭', '杀', '玩', '好玩', '有趣', '不错', '挺好', '太'
])


def get_week_start(date):
    """
    获取某日期所在周的周一日期
    
    Args:
        date: 日期对象
        
    Returns:
        该周周一的日期
    """
    return date - timedelta(days=date.weekday())


def generate_wordcloud_image(text, output_path, title=""):
    """
    生成词云图片
    
    Args:
        text: 文本内容
        output_path: 输出路径
        title: 词云标题
    """
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        
        # 分词
        words = jieba.cut(text)
        word_list = [w for w in words if len(w) >= 2 and w not in STOPWORDS]
        word_counter = Counter(word_list)
        
        if not word_counter:
            print(f"  警告: 没有有效词语，跳过生成")
            return False
        
        # 生成词云
        wc = WordCloud(
            font_path='C:/Windows/Fonts/simhei.ttf',
            width=800,
            height=400,
            background_color='white',
            max_words=100,
            max_font_size=100,
            random_state=42
        )
        wc.generate_from_frequencies(word_counter)
        
        # 保存图片
        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        if title:
            plt.title(title, fontsize=14)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  生成词云: {output_path}")
        return True
        
    except ImportError:
        print("  警告: 未安装wordcloud库，跳过词云生成")
        print("  安装命令: pip install wordcloud")
        return False


def generate_all_wordclouds():
    """
    生成所有周的词云图片
    """
    init_db()
    db = SessionLocal()
    
    try:
        # 确保输出目录存在
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 获取所有评价，按周分组
        reviews = db.query(Review).filter(Review.review_date.isnot(None)).order_by(Review.review_date).all()
        
        if not reviews:
            print("没有找到评价数据")
            return
        
        print(f"共找到 {len(reviews)} 条评价")
        
        # 按周分组
        weekly_texts = {}
        for r in reviews:
            week_start = get_week_start(r.review_date)
            week_key = week_start.strftime('%Y-%m-%d')
            
            if week_key not in weekly_texts:
                weekly_texts[week_key] = []
            
            if r.content:
                weekly_texts[week_key].append(r.content)
        
        print(f"共 {len(weekly_texts)} 周")
        
        # 生成每周词云
        generated = 0
        for week_key in sorted(weekly_texts.keys()):
            output_path = os.path.join(OUTPUT_DIR, f'词云_{week_key}.png')
            
            # 如果已存在则跳过
            if os.path.exists(output_path):
                print(f"  跳过已存在: {week_key}")
                continue
            
            text = ' '.join(weekly_texts[week_key])
            if generate_wordcloud_image(text, output_path, f"词云 {week_key}"):
                generated += 1
        
        print(f"\n生成完成: 新增 {generated} 个词云图片")
        print(f"输出目录: {OUTPUT_DIR}")
        
    finally:
        db.close()


if __name__ == '__main__':
    generate_all_wordclouds()
