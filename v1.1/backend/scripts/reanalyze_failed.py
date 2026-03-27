# -*- coding: utf-8 -*-
import sys
from datetime import date
from sqlalchemy import or_

sys.path.insert(0, r'c:\Users\Administrator\Documents\trae_projects\99multi\taptap_analyzer\v1.1\backend')

from models import SessionLocal, Review, Product
from nlp.glm_analyzer import AliyunAnalyzer


def main():
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.name == '鹅鸭杀').first()
        rows = db.query(Review).filter(
            Review.product_id == product.id,
            Review.review_date >= date(2026, 3, 1)
        ).filter(
            or_(
                Review.sentiment == None,
                Review.problem_category == None,
                Review.summary == None,
                Review.summary == '',
                Review.summary.like('分析失败%')
            )
        ).order_by(Review.review_date.asc(), Review.id.asc()).all()

        print(f'to_fix={len(rows)}')
        analyzer = AliyunAnalyzer()
        analyzer.token_tracker.daily_tokens = 0
        fixed = 0
        still_failed = 0

        for r in rows:
            content = (r.content or '').strip()
            if len(content) < 5:
                continue
            result = None
            for _ in range(3):
                candidate = analyzer.analyze(content, review_id=str(r.id))
                if candidate.get('success'):
                    result = candidate
                    break
            if not result:
                still_failed += 1
                continue
            r.sentiment = result.get('sentiment', '中性')
            r.problem_category = result.get('problem_category', '无问题')
            r.summary = result.get('summary', '')
            fixed += 1
            if fixed % 10 == 0:
                print(f'fixed={fixed}')

        db.commit()
        remain = db.query(Review).filter(
            Review.product_id == product.id,
            Review.review_date >= date(2026, 3, 1)
        ).filter(
            or_(
                Review.sentiment == None,
                Review.problem_category == None,
                Review.summary == None,
                Review.summary == '',
                Review.summary.like('分析失败%')
            )
        ).count()
        print(f'fixed_total={fixed}')
        print(f'still_failed={still_failed}')
        print(f'remain={remain}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
