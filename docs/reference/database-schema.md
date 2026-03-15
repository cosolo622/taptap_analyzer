# 数据库结构参考

## 连接信息

```
postgresql://postgres:12357951@localhost:5432/public_opinion
```

## 表结构

### products 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 产品名称 |
| code | String | 产品代码 |

### platforms 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 平台名称 |
| code | String | 平台代码 |

### reviews 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| review_id | String | TapTap评价ID |
| product_id | Integer | 产品ID（外键） |
| platform_id | Integer | 平台ID（外键） |
| user_name | String | 用户名 |
| content | Text | 评价内容 |
| rating | Integer | 星级（1-5） |
| review_date | Date | 评价日期 |
| crawl_date | DateTime | 爬取时间 |
| sentiment | String | 情感（正向/负向/中性/中性偏负） |
| problem_category | String | 问题分类（大类-细分问题） |
| summary | String | 一句话总结 |

### crawl_logs 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| product_id | Integer | 产品ID |
| platform_id | Integer | 平台ID |
| crawl_time | DateTime | 爬取时间 |
| reviews_count | Integer | 爬取数量 |
| status | String | 状态 |

## ORM 模型

文件位置：`v1.1/backend/models/database.py`

```python
class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    review_id = Column(String(50), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'))
    platform_id = Column(Integer, ForeignKey('platforms.id'))
    user_name = Column(String(100))
    content = Column(Text)
    rating = Column(Integer)
    review_date = Column(Date)
    crawl_date = Column(DateTime)
    sentiment = Column(String(20))
    problem_category = Column(String(200))
    summary = Column(String(500))
```
