# -*- coding: utf-8 -*-
"""
爬取日志模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime


class CrawlLog(Base):
    """
    爬取日志表
    记录每次爬取的执行情况
    """
    __tablename__ = 'crawl_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    spider_name = Column(String(50), comment='爬虫名称')
    product_id = Column(Integer, ForeignKey('products.id'), comment='产品ID')
    platform_id = Column(Integer, ForeignKey('platforms.id'), comment='平台ID')
    
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    pages_crawled = Column(Integer, default=0, comment='爬取页数')
    reviews_added = Column(Integer, default=0, comment='新增评价数')
    reviews_updated = Column(Integer, default=0, comment='更新评价数')
    errors = Column(Integer, default=0, comment='错误数')
    status = Column(String(20), comment='状态：running/success/failed')
    error_message = Column(String(500), comment='错误信息')

    product = relationship("Product", back_populates="crawl_logs")
    platform = relationship("Platform", back_populates="crawl_logs")

    def __repr__(self):
        return f"<CrawlLog(id={self.id}, spider='{self.spider_name}', status='{self.status}')>"
