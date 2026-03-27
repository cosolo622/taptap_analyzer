import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.taptap_crawler_scrapling import TapTapCrawler
from nlp.glm_analyzer import AliyunAnalyzer


def main():
    crawler = TapTapCrawler(headless=True)
    reviews = crawler.get_reviews(game_id=258720, max_reviews=20, sort='new')
    crawler.close()

    analyzer = AliyunAnalyzer()
    analyzed = []
    total = len(reviews)
    for idx, item in enumerate(reviews, 1):
        content = (item.get('content') or '').strip()
        if not content:
            continue
        print(f"[{idx}/{total}] 开始分析 review_id={item.get('review_id')}", flush=True)
        result = analyzer.analyze(content=content, review_id=str(item.get('review_id')))
        analyzed.append({
            'review_id': item.get('review_id'),
            'user_name': item.get('user_name'),
            'rating': item.get('rating'),
            'review_date': item.get('review_date'),
            'content': content,
            'sentiment': result.get('sentiment'),
            'problem_category': result.get('problem_category'),
            'summary': result.get('summary'),
            'success': result.get('success'),
            'reason': result.get('reason')
        })
        print(f"[{idx}/{total}] 完成 success={result.get('success')} sentiment={result.get('sentiment')}", flush=True)

    output = {
        'generated_at': datetime.now().isoformat(),
        'count': len(analyzed),
        'items': analyzed
    }

    out_path = f"output/glm_sample20_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(out_path)
    print(json.dumps({
        'count': len(analyzed),
        'success_count': sum(1 for x in analyzed if x.get('success')),
        'failed_count': sum(1 for x in analyzed if not x.get('success'))
    }, ensure_ascii=False))

    for idx, row in enumerate(analyzed[:10], 1):
        print(json.dumps({
            'idx': idx,
            'review_id': row.get('review_id'),
            'rating': row.get('rating'),
            'sentiment': row.get('sentiment'),
            'problem_category': row.get('problem_category'),
            'summary': row.get('summary')
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
