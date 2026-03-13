# -*- coding: utf-8 -*-
"""
平台模型
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime


class Platform(Base):
    """
    平台表
    存储数据来源平台信息
    """
    __tablename__ = 'platforms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment='平台名称，如：TapTap')
    code = Column(String(30), unique=True, comment='平台代码，如：taptap')
    base_url = Column(String(200), comment='平台基础URL')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    reviews = relationship("Review", back_populates="platform")
    crawl_logs = relationship("CrawlLog", back_populates="platform")

    def __repr__(self):
        return f"<Platform(id={self.id}, name='{self.name}', code='{self.code}')>"
