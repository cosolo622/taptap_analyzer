# -*- coding: utf-8 -*-
"""
数据导入脚本
将 Excel 数据导入到 SQLite/PostgreSQL 数据库
"""

import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base, engine, SessionLocal, Product, Platform, Review, CrawlLog, init_db


def parse_rating(rating_str):
    """
    解析星级字符串
    @param rating_str: 星级字符串，如 "4星"
    @return: int，星级数字
    """
    if pd.isna(rating_str):
        return 0
    try:
        return int(float(str(rating_str).replace('星', '').strip()))
    except:
        return 0


def import_excel_to_db(excel_path: str, product_name: str, platform_name: str = 'TapTap'):
    """
    将 Excel 数据导入数据库
    @param excel_path: Excel 文件路径
    @param product_name: 产品名称
    @param platform_name: 平台名称
    @return: dict，导入统计信息
    """
    print(f"开始导入: {excel_path}")
    print(f"产品: {product_name}, 平台: {platform_name}")

    init_db()

    db: Session = SessionLocal()

    try:
        product = db.query(Product).filter(Product.name == product_name).first()
        if not product:
            product = Product(name=product_name, code=product_name.lower().replace(' ', '_'))
            db.add(product)
            db.commit()
            print(f"创建产品: {product_name}")
        else:
            print(f"产品已存在: {product_name}")

        platform = db.query(Platform).filter(Platform.name == platform_name).first()
        if not platform:
            platform = Platform(name=platform_name, code=platform_name.lower())
            db.add(platform)
            db.commit()
            print(f"创建平台: {platform_name}")
        else:
            print(f"平台已存在: {platform_name}")

        df = pd.read_excel(excel_path, sheet_name='评价明细')
        print(f"读取到 {len(df)} 条评价记录")

        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')

        added_count = 0
        skipped_count = 0
        error_count = 0

        for idx, row in df.iterrows():
            try:
                review_date = row['日期']
                user_name = str(row.get('用户名', '')) if pd.notna(row.get('用户名')) else None
                rating = parse_rating(row.get('星级'))
                sentiment = str(row.get('情感', '')) if pd.notna(row.get('情感')) else None
                problem_category = str(row.get('问题分类', '')) if pd.notna(row.get('问题分类')) else None
                summary = str(row.get('一句话摘要', '')) if pd.notna(row.get('一句话摘要')) else None
                content = str(row.get('评价内容', '')) if pd.notna(row.get('评价内容')) else None

                review_id = f"{product.id}_{platform.id}_{idx}"

                existing = db.query(Review).filter(
                    Review.platform_id == platform.id,
                    Review.review_id == review_id
                ).first()

                if existing:
                    skipped_count += 1
                    continue

                review = Review(
                    product_id=product.id,
                    platform_id=platform.id,
                    review_id=review_id,
                    user_name=user_name,
                    content=content,
                    rating=rating,
                    sentiment=sentiment,
                    problem_category=problem_category,
                    summary=summary,
                    review_date=review_date.date() if pd.notna(review_date) else None
                )
                db.add(review)
                added_count += 1

                if added_count % 1000 == 0:
                    db.commit()
                    print(f"已导入 {added_count} 条...")

            except Exception as e:
                error_count += 1
                if error_count <= 10:
                    print(f"行 {idx} 导入失败: {e}")

        db.commit()

        crawl_log = CrawlLog(
            spider_name='excel_import',
            product_id=product.id,
            platform_id=platform.id,
            start_time=datetime.now(),
            end_time=datetime.now(),
            pages_crawled=1,
            reviews_added=added_count,
            reviews_updated=0,
            errors=error_count,
            status='success' if error_count == 0 else 'partial'
        )
        db.add(crawl_log)
        db.commit()

        result = {
            'product': product_name,
            'platform': platform_name,
            'total_rows': len(df),
            'added': added_count,
            'skipped': skipped_count,
            'errors': error_count
        }

        print("\n导入完成!")
        print(f"  总行数: {result['total_rows']}")
        print(f"  新增: {result['added']}")
        print(f"  跳过(已存在): {result['skipped']}")
        print(f"  错误: {result['errors']}")

        return result

    except Exception as e:
        db.rollback()
        print(f"导入失败: {e}")
        raise
    finally:
        db.close()


def main():
    """
    主函数
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROJECT_DIR = os.path.dirname(BASE_DIR)

    excel_file = os.path.join(BASE_DIR, 'output', '鹅鸭杀_GLM分析_v1.1.xlsx')

    if not os.path.exists(excel_file):
        excel_file = os.path.join(PROJECT_DIR, 'output', '鹅鸭杀_GLM分析_v1.1.xlsx')

    if not os.path.exists(excel_file):
        print(f"文件不存在: {excel_file}")
        return

    import_excel_to_db(excel_file, '鹅鸭杀', 'TapTap')


if __name__ == '__main__':
    main()
