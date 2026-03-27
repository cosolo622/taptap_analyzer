# -*- coding: utf-8 -*-
"""
数据库连接配置
仅支持 PostgreSQL
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:12357951@localhost:5432/public_opinion'
)

if not DATABASE_URL.startswith('postgresql'):
    raise ValueError('当前项目仅支持 PostgreSQL，请设置 DATABASE_URL 为 postgresql://...')

engine = create_engine(
    DATABASE_URL,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    获取数据库会话
    用于 FastAPI 依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库（创建所有表）
    """
    from . import Product, Platform, Review, CrawlLog, CommunityContent, ContentAITags
    Base.metadata.create_all(bind=engine)
    print(f"数据库初始化完成: {DATABASE_URL}")
