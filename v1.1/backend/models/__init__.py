# -*- coding: utf-8 -*-
"""
SQLAlchemy 数据模型
当前使用 PostgreSQL（SQLite 已弃用）
"""

from .database import Base, engine, SessionLocal, get_db, init_db
from .product import Product
from .platform import Platform
from .review import Review
from .crawl_log import CrawlLog
from .community import CommunityContent, ContentAITags

__all__ = [
    'Base', 'engine', 'SessionLocal', 'get_db', 'init_db',
    'Product', 'Platform', 'Review', 'CrawlLog',
    'CommunityContent', 'ContentAITags'
]
