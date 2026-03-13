# -*- coding: utf-8 -*-
"""
修复问题分类统计逻辑 - 口径B
- 大类统计：每个问题子类对应的大类都计1次（不去重）
- 子类统计：每个子类计1次
"""

import pandas as pd
import numpy as np
from collections import Counter
import os

print("="*60)
print("修复问题分类统计 - 口径B（重复统计）")
print("="*60)

# 读取文件
target_file = './output/鹅鸭杀_GLM分析_优化版_v1.0.xlsx'
df_target = pd.read_excel(target_file)

# 解析问题分类（格式：大类-子类）
def parse_issues(issues_str):
    if pd.isna(issues_str) or issues_str == '':
        return [], []  # 使用list，不去重
    issues = [i.strip() for i in str(issues_str).split(',') if i.strip()]
    main_cats = []  # 使用list，允许重复
    sub_cats = []
    for issue in issues:
        if '-' in issue:
            parts = issue.split('-', 1)
            main_cats.append(parts[0].strip())  # 使用append，不去重
            sub_cats.append(issue)
        else:
            main_cats.append(issue)
    return main_cats, sub_cats

# 统计大类和子类
main_cat_counter = Counter()
sub_cat_counter = Counter()

for idx, row in df_target.iterrows():
    main_cats, sub_cats = parse_issues(row.get('问题分类', ''))
    main_cat_counter.update(main_cats)  # 每个子类对应的大类都计1次
    sub_cat_counter.update(sub_cats)    # 每个子类计1次

print(f"\n大类统计（口径B - 重复统计）:")
for cat, count in main_cat_counter.most_common(15):
    print(f"  {cat}: {count}次")

print(f"\n子类统计TOP15:")
for cat, count in sub_cat_counter.most_common(15):
    main_cat = cat.split('-')[0] if '-' in cat else cat
    print(f"  {cat}: {count}次 (大类: {main_cat})")

# 验证：子类中各大类的总数应该等于大类统计
print(f"\n验证 - 子类中各大类总数:")
sub_main_cat_counter = Counter()
for sub_cat, count in sub_cat_counter.items():
    main_cat = sub_cat.split('-')[0] if '-' in sub_cat else sub_cat
    sub_main_cat_counter[main_cat] += count

for cat, count in sub_main_cat_counter.most_common(10):
    print(f"  {cat}: {count}次")

# 验证是否一致
print(f"\n一致性检查:")
print(f"  大类统计总和: {sum(main_cat_counter.values())}")
print(f"  子类统计总和: {sum(sub_cat_counter.values())}")
print(f"  子类推算大类总和: {sum(sub_main_cat_counter.values())}")

# 导出修正后的Excel
output_file = './output/鹅鸭杀_GLM分析_v1.1_修复版.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet1: 评价明细
    df_target.to_excel(writer, sheet_name='评价明细', index=False)
    
    # Sheet2: 情感分布-总体
    sentiment_total = df_target['情感'].value_counts()
    sentiment_total_df = pd.DataFrame({
        '情感': sentiment_total.index,
        '数量': sentiment_total.values,
        '占比': [f'{v/len(df_target)*100:.1f}%' for v in sentiment_total.values]
    })
    sentiment_total_df.to_excel(writer, sheet_name='情感分布-总体', index=False)
    
    # Sheet3: 情感分布-按天
    sentiment_daily = df_target.groupby(['日期', '情感']).size().unstack(fill_value=0)
    sentiment_daily.reset_index().to_excel(writer, sheet_name='情感分布-按天', index=False)
    
    # Sheet4: 情感分布-按周
    df_target['日期'] = pd.to_datetime(df_target['日期'], errors='coerce')
    df_target['周开始日期'] = df_target['日期'].apply(
        lambda x: x - pd.Timedelta(days=x.weekday()) if pd.notna(x) else None
    )
    df_target['周标签'] = df_target['周开始日期'].apply(
        lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else '未知'
    )
    sentiment_weekly = df_target.groupby(['周标签', '情感']).size().unstack(fill_value=0)
    sentiment_weekly.reset_index().to_excel(writer, sheet_name='情感分布-按周', index=False)
    
    # Sheet5: 问题分类-大类（口径B）
    main_cat_df = pd.DataFrame(main_cat_counter.most_common(50), columns=['大类', '出现次数'])
    main_cat_df['占比'] = (main_cat_df['出现次数'] / sum(main_cat_counter.values()) * 100).round(1).astype(str) + '%'
    main_cat_df.to_excel(writer, sheet_name='问题分类-大类', index=False)
    
    # Sheet6: 问题分类-子类
    sub_cat_list = []
    for sub_cat, count in sub_cat_counter.most_common(100):
        main_cat = sub_cat.split('-')[0] if '-' in sub_cat else sub_cat
        sub_cat_list.append({
            '大类': main_cat,
            '子类': sub_cat,
            '出现次数': count,
            '占比': f'{count/sum(sub_cat_counter.values())*100:.1f}%'
        })
    sub_cat_df = pd.DataFrame(sub_cat_list)
    sub_cat_df.to_excel(writer, sheet_name='问题分类-子类', index=False)
    
    # Sheet7: 问题分类-层级汇总
    sub_by_main = {}
    for sub_cat, count in sub_cat_counter.items():
        main_cat = sub_cat.split('-')[0] if '-' in sub_cat else sub_cat
        if main_cat not in sub_by_main:
            sub_by_main[main_cat] = []
        sub_by_main[main_cat].append((sub_cat, count))
    
    sub_summary_list = []
    for main_cat in sorted(sub_by_main.keys(), key=lambda x: sub_main_cat_counter[x], reverse=True):
        subs = sorted(sub_by_main[main_cat], key=lambda x: x[1], reverse=True)
        for sub_cat, count in subs:
            sub_summary_list.append({
                '大类': main_cat,
                '大类出现次数': sub_main_cat_counter[main_cat],
                '子类': sub_cat,
                '子类出现次数': count
            })
    
    sub_summary_df = pd.DataFrame(sub_summary_list)
    sub_summary_df.to_excel(writer, sheet_name='问题分类-层级汇总', index=False)

print(f"\n✓ Excel已保存: {output_file}")

# 打印统计摘要
print("\n" + "="*60)
print("统计摘要")
print("="*60)
print(f"总评价数: {len(df_target)}")
print(f"有问题分类的评价: {df_target['问题分类'].notna().sum()}")
print(f"大类出现总次数: {sum(main_cat_counter.values())}")
print(f"子类出现总次数: {sum(sub_cat_counter.values())}")
print(f"大类种类数: {len(main_cat_counter)}")
print(f"子类种类数: {len(sub_cat_counter)}")
