# -*- coding: utf-8 -*-
"""
查看分析结果
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'postgresql://postgres:12357951@localhost:5432/public_opinion'
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

# 查看分析统计
print("=" * 80)
print("分析结果统计")
print("=" * 80)

# 情感分布
result = db.execute(text("""
    SELECT sentiment, COUNT(*) as cnt
    FROM reviews
    GROUP BY sentiment
    ORDER BY cnt DESC
"""))
print("\n情感分布:")
for row in result:
    print(f"  {row[0]}: {row[1]}")

# 问题分类分布
result = db.execute(text("""
    SELECT problem_category, COUNT(*) as cnt
    FROM reviews
    WHERE problem_category IS NOT NULL
    GROUP BY problem_category
    ORDER BY cnt DESC
    LIMIT 15
"""))
print("\n问题分类分布 (Top 15):")
for row in result:
    print(f"  {row[0]}: {row[1]}")

# 查看几条示例
print("\n" + "=" * 80)
print("分析示例 (前5条)")
print("=" * 80)

result = db.execute(text("""
    SELECT id, content, rating, sentiment, problem_category, summary
    FROM reviews
    WHERE sentiment IS NOT NULL
    LIMIT 5
"""))

for row in result:
    print(f"\nID: {row[0]}")
    print(f"内容: {row[1][:80]}..." if len(row[1] or '') > 80 else f"内容: {row[1]}")
    print(f"星级: {row[2]}")
    print(f"情感: {row[3]}")
    print(f"问题分类: {row[4]}")
    print(f"摘要: {row[5]}")

db.close()
