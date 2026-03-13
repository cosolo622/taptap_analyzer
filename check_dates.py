"""
检查原始数据中的日期字段
"""
import json
import os

# 检查多个JSON文件
json_files = [
    'output/batch_1.json',
    'output/reviews_for_analysis.json',
    'output/analysis_batch_1.json'
]

for json_file in json_files:
    if os.path.exists(json_file):
        print(f"\n{'='*60}")
        print(f"文件: {json_file}")
        print('='*60)

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"数据类型: {type(data)}")
        print(f"总记录数: {len(data) if isinstance(data, list) else 'N/A'}")

        # 检查前5条数据
        items = data[:5] if isinstance(data, list) else list(data.values())[0][:5] if isinstance(data, dict) else []

        print("\n前5条数据的日期字段:")
        for i, item in enumerate(items, 1):
            date_val = item.get('date', '无date字段')
            print(f"  {i}. date: '{date_val}'")

        # 统计日期字段情况
        all_items = data if isinstance(data, list) else list(data.values())[0] if isinstance(data, dict) else []
        empty_count = sum(1 for item in all_items if item.get('date', '') == '')
        non_empty_count = len(all_items) - empty_count

        print(f"\n日期字段统计:")
        print(f"  空值数量: {empty_count}")
        print(f"  非空数量: {non_empty_count}")

        # 显示非空日期示例
        if non_empty_count > 0:
            print("\n非空日期示例:")
            non_empty_dates = [item.get('date') for item in all_items if item.get('date', '') != '']
            for i, date in enumerate(non_empty_dates[:5], 1):
                print(f"  {i}. {date}")
