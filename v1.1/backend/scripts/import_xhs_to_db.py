import os
import sys
import json
import random
from datetime import datetime
from sqlalchemy.orm import Session

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, init_db
from models.community import CommunityContent, ContentAITags
from models.product import Product

def parse_count(count_str):
    if not count_str:
        return 0
    if isinstance(count_str, int):
        return count_str
    count_str = str(count_str).replace('+', '')
    if '万' in count_str:
        return int(float(count_str.replace('万', '')) * 10000)
    if 'w' in count_str.lower():
        return int(float(count_str.lower().replace('w', '')) * 10000)
    try:
        return int(count_str)
    except:
        return 0

def mock_ai_tags(content_text, is_post=True):
    """简单的Mock AI标签生成"""
    import random
    
    # 关键词匹配
    text = str(content_text).lower()
    
    sentiment = "中性"
    if any(word in text for word in ['好', '棒', '喜欢', '赞', '推荐', '优雅', '默契']):
        sentiment = "正向"
    elif any(word in text for word in ['差', '烂', '烦', '退游', '无聊', '卡', '崩', '封']):
        sentiment = "负向"
    else:
        sentiment = random.choices(["正向", "中性", "负向"], weights=[0.4, 0.4, 0.2])[0]
        
    topic_level1 = "其他"
    if is_post:
        topics = ["玩法", "社交", "商业化", "Bug/性能", "二创", "活动"]
        if any(word in text for word in ['刀', '好人', '狼', '套路']):
            topic_level1 = "玩法"
        elif any(word in text for word in ['朋友', '组队', '情侣']):
            topic_level1 = "社交"
        else:
            topic_level1 = random.choice(topics)
            
    risk_level = "低"
    if any(word in text for word in ['退游', '垃圾', '策划死', '封号', '投诉']):
        risk_level = "高"
    elif any(word in text for word in ['卡顿', '掉线', '闪退']):
        risk_level = "中"
        
    return {
        "sentiment": sentiment,
        "topic_level1": topic_level1 if is_post else None,
        "topic_level2": None,
        "summary": text[:20] + "..." if is_post else None,
        "risk_level": risk_level
    }

def import_xhs_data():
    # 确保数据库表已创建
    init_db()
    
    db: Session = SessionLocal()
    try:
        # 获取或创建产品 (假设1为鹅鸭杀)
        product = db.query(Product).filter(Product.name == '鹅鸭杀').first()
        if not product:
            product = Product(name='鹅鸭杀', code='goose_goose_duck')
            db.add(product)
            db.commit()
            db.refresh(product)
            
        project_id = product.id
        
        # 文件路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        jsonl_dir = os.path.join(base_dir, 'MediaCrawler', 'data', 'xhs', 'jsonl')
        
        contents_file = os.path.join(jsonl_dir, 'search_contents_2026-03-25.jsonl')
        comments_file = os.path.join(jsonl_dir, 'search_comments_2026-03-25.jsonl')
        
        imported_posts = 0
        imported_comments = 0
        
        # 导入帖子
        if os.path.exists(contents_file):
            with open(contents_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    
                    original_id = data.get('note_id')
                    global_id = f"xiaohongshu_{original_id}"
                    
                    # 检查是否已存在
                    existing = db.query(CommunityContent).filter(CommunityContent.id == global_id).first()
                    if existing:
                        continue
                        
                    content_text = f"{data.get('title', '')} {data.get('desc', '')}"
                    
                    post = CommunityContent(
                        id=global_id,
                        project_id=project_id,
                        channel="xiaohongshu",
                        content_type=data.get('type', 'image'),
                        post_type="post",
                        original_id=original_id,
                        parent_id=None,
                        author_name=data.get('nickname', ''),
                        author_id=data.get('user_id', ''),
                        content=content_text,
                        publish_time=datetime.fromtimestamp(data.get('time', 0) / 1000.0),
                        interact_likes=parse_count(data.get('liked_count')),
                        interact_comments=parse_count(data.get('comment_count')),
                        interact_shares=parse_count(data.get('share_count')),
                        interact_collects=parse_count(data.get('collected_count')),
                        url=data.get('note_url', f"https://www.xiaohongshu.com/explore/{original_id}")
                    )
                    db.add(post)
                    db.flush() # 立即刷新，确保ID冲突能在当前循环被捕捉或跳过
                    
                    # Mock AI Tags
                    ai_mock = mock_ai_tags(content_text, is_post=True)
                    ai_tag = ContentAITags(
                        content_id=global_id,
                        **ai_mock
                    )
                    db.add(ai_tag)
                    
                    imported_posts += 1
                    if imported_posts % 50 == 0:
                        db.commit() # 分批提交
                    
        # 导入评论
        if os.path.exists(comments_file):
            with open(comments_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    
                    original_id = data.get('comment_id')
                    note_id = data.get('note_id')
                    global_id = f"xiaohongshu_{original_id}"
                    
                    # 检查是否已存在
                    existing = db.query(CommunityContent).filter(CommunityContent.id == global_id).first()
                    if existing:
                        continue
                        
                    content_text = data.get('content', '')
                    
                    comment = CommunityContent(
                        id=global_id,
                        project_id=project_id,
                        channel="xiaohongshu",
                        content_type="text",
                        post_type="comment",
                        original_id=original_id,
                        parent_id=note_id,
                        author_name=data.get('nickname', ''),
                        author_id=data.get('user_id', ''),
                        content=content_text,
                        publish_time=datetime.fromtimestamp(data.get('create_time', 0) / 1000.0),
                        interact_likes=parse_count(data.get('like_count')),
                        interact_comments=parse_count(data.get('sub_comment_count')),
                        interact_shares=0,
                        interact_collects=0,
                        url=f"https://www.xiaohongshu.com/explore/{note_id}"
                    )
                    db.add(comment)
                    db.flush()
                    
                    # Mock AI Tags for comment
                    ai_mock = mock_ai_tags(content_text, is_post=False)
                    ai_tag = ContentAITags(
                        content_id=global_id,
                        **ai_mock
                    )
                    db.add(ai_tag)
                    
                    imported_comments += 1
                    if imported_comments % 50 == 0:
                        db.commit()
                    
        db.commit()
        print(f"成功导入 {imported_posts} 条帖子, {imported_comments} 条评论到 community_contents 表")
        
    except Exception as e:
        db.rollback()
        print(f"导入失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_xhs_data()