# -*- coding: utf-8 -*-
"""
SQLAlchemy 数据模型
支持 SQLite 和 PostgreSQL
"""

from .database import Base, engine, SessionLocal, get_db, init_db
from .product import Product
from .platform import Platform
from .review import Review
from .crawl_log import CrawlLog

__all__ = [
    'Base', 'engine', 'SessionLocal', 'get_db', 'init_db',
    'Product', 'Platform', 'Review', 'CrawlLog'
]
