# -*- coding: utf-8 -*-
import json

with open('goose_goose_duck_reviews_2026-01-07_20260316_192922.json', 'r', encoding='utf-8') as f:
    reviews = json.load(f)

print(f'总评价数: {len(reviews)}')
print()
print('=== 前100条评价内容 ===')
for i, r in enumerate(reviews[:100], 1):
    content = r.get('content', '')[:60].replace('\n', ' ')
    rating = r.get('rating', 0)
    print(f'{i:3d}. [{rating}星] {content}')
