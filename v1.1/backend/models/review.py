# -*- coding: utf-8 -*-
"""
评价模型
"""

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime


class Review(Base):
    """
    评价表（核心表）
    存储从各平台爬取的评价数据
    """
    __tablename__ = 'reviews'
    __table_args__ = (
        UniqueConstraint('platform_id', 'review_id', name='uq_platform_review'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, comment='产品ID')
    platform_id = Column(Integer, ForeignKey('platforms.id'), nullable=False, comment='平台ID')
    
    review_id = Column(String(100), comment='平台评价ID，用于去重')
    user_name = Column(String(100), comment='用户名')
    content = Column(Text, comment='评价内容')
    rating = Column(Integer, comment='星级，1-5')
    sentiment = Column(String(20), comment='情感标签：正向/负向/中性/中性偏负')
    problem_category = Column(String(100), comment='问题分类，如：玩法-平衡性')
    summary = Column(Text, comment='一句话摘要（GLM生成）')
    
    review_date = Column(Date, comment='评价日期')
    crawl_date = Column(DateTime, default=datetime.now, comment='爬取时间')
    
    raw_data = Column(JSON, comment='原始数据（备用）')

    product = relationship("Product", back_populates="reviews")
    platform = relationship("Platform", back_populates="reviews")

    def __repr__(self):
        return f"<Review(id={self.id}, product_id={self.product_id}, sentiment='{self.sentiment}')>"

    def to_dict(self):
        """
        转换为字典
        """
        return {
            'id': self.id,
            'product_id': self.product_id,
            'platform_id': self.platform_id,
            'review_id': self.review_id,
            'user_name': self.user_name,
            'content': self.content,
            'rating': self.rating,
            'sentiment': self.sentiment,
            'problem_category': self.problem_category,
            'summary': self.summary,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'crawl_date': self.crawl_date.isoformat() if self.crawl_date else None
        }
