# -*- coding: utf-8 -*-
"""
产品模型
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime


class Product(Base):
    """
    产品表
    存储监控的产品信息
    """
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='产品名称，如：鹅鸭杀')
    code = Column(String(50), unique=True, comment='产品代码，如：goose_goose_duck')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    reviews = relationship("Review", back_populates="product")
    crawl_logs = relationship("CrawlLog", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', code='{self.code}')>"
