# -*- coding: utf-8 -*-
import sys
from datetime import date, timedelta

sys.path.insert(0, r'c:\Users\Administrator\Documents\trae_projects\99multi\taptap_analyzer\v1.1\backend')

from models import SessionLocal
from services.crawler_service import CrawlerService


def date_to_str(d: date) -> str:
    return d.strftime('%Y-%m-%d')


def main():
    db = SessionLocal()
    try:
        service = CrawlerService(db)
        end = date.today()
        min_date = date(2026, 1, 7)
        total_added = 0
        total_dup = 0
        idx = 0
        while end >= min_date:
            start = max(min_date, end - timedelta(days=6))
            idx += 1
            print(f'chunk#{idx} {date_to_str(start)} ~ {date_to_str(end)} 开始')
            result = service.crawl_incremental('鹅鸭杀', start_date=date_to_str(start), end_date=date_to_str(end))
            print(f'chunk#{idx} result={result}')
            if result.get('error'):
                print(f'chunk#{idx} error_stop')
                break
            total_added += int(result.get('added', 0) or 0)
            total_dup += int(result.get('duplicated', 0) or 0)
            print(f'chunk#{idx} 累计新增={total_added} 累计重复={total_dup}')
            end = start - timedelta(days=1)
        print(f'finished 累计新增={total_added} 累计重复={total_dup}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
