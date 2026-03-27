# -*- coding: utf-8 -*-
import sys
import time

sys.path.insert(0, r'c:\Users\Administrator\Documents\trae_projects\99multi\taptap_analyzer\v1.1\backend')

from models import SessionLocal
from services.crawler_service import CrawlerService


def main():
    db = SessionLocal()
    try:
        service = CrawlerService(db)
        ts = time.time()
        result = service.crawl_incremental('鹅鸭杀', start_date='2026-01-07')
        print('elapsed_seconds=', round(time.time() - ts, 1))
        print('result=', result)
    finally:
        db.close()


if __name__ == '__main__':
    main()
