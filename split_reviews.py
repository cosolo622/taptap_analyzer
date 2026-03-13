# -*- coding: utf-8 -*-
"""
分批读取评价数据
"""

import json

# 读取全部评价
with open('./output/reviews_for_analysis.json', 'r', encoding='utf-8') as f:
    reviews = json.load(f)

print(f"共 {len(reviews)} 条评价")

# 分批保存，每批20条
batch_size = 20
for i in range(0, len(reviews), batch_size):
    batch = reviews[i:i+batch_size]
    batch_file = f'./output/batch_{i//batch_size + 1}.json'
    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
    print(f"批次 {i//batch_size + 1}: {len(batch)} 条 -> {batch_file}")

print("\n分批完成！")
