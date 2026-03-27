from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base

class CommunityContent(Base):
    __tablename__ = "community_contents"

    id = Column(String, primary_key=True, index=True, comment="全局唯一ID: {channel}_{original_id}")
    project_id = Column(Integer, ForeignKey("products.id"), index=True, comment="关联的游戏项目ID")
    channel = Column(String, index=True, comment="渠道标识: taptap 或 xiaohongshu")
    content_type = Column(String, comment="内容载体类型: text(纯文本), image(图文), video(视频)")
    post_type = Column(String, index=True, comment="内容层级类型: post(主帖/评价), comment(评论)")
    original_id = Column(String, index=True, comment="原平台内容ID")
    parent_id = Column(String, index=True, nullable=True, comment="父级ID: 若为评论，记录关联的主帖ID")
    author_name = Column(String, comment="作者昵称")
    author_id = Column(String, comment="作者ID")
    content = Column(Text, comment="正文内容")
    publish_time = Column(DateTime, index=True, comment="发布时间")
    
    interact_likes = Column(Integer, default=0, comment="点赞数")
    interact_comments = Column(Integer, default=0, comment="评论/回复数")
    interact_shares = Column(Integer, default=0, comment="转发/分享数")
    interact_collects = Column(Integer, default=0, comment="收藏数")
    url = Column(String, comment="原始链接")

    # 关联AI标签
    ai_tags = relationship("ContentAITags", back_populates="content", uselist=False)
    # 关联产品
    product = relationship("Product")

class ContentAITags(Base):
    __tablename__ = "content_ai_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String, ForeignKey("community_contents.id"), unique=True, index=True, comment="关联主表ID")
    sentiment = Column(String, index=True, comment="正向/负向/中性")
    topic_level1 = Column(String, index=True, comment="一级主题，如：玩法、商业化、bug")
    topic_level2 = Column(String, comment="二级主题")
    summary = Column(String, comment="一句话总结")
    risk_level = Column(String, index=True, comment="风控等级: 高/中/低")

    content = relationship("CommunityContent", back_populates="ai_tags")
