# -*- coding: utf-8 -*-
"""
优化问题分类统计：
1. 子类合并：相似的子类合并为一个标准子类
2. 保留原子类作为子子类
3. 删除问题分类-子类sheet，改为层级汇总
"""

import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import os

print("="*60)
print("优化问题分类统计 - 子类合并")
print("="*60)

# 子类合并映射表（原子类 -> 标准子类）
SUB_CLASS_MERGE = {
    # 骂人相关 -> 环境问题-骂人
    '环境问题-开麦骂人': '环境问题-骂人',
    '环境问题-骂人': '环境问题-骂人',
    '环境问题-言语辱骂': '环境问题-骂人',
    '环境问题-语言攻击': '环境问题-骂人',
    
    # 素质相关 -> 环境问题-低素质玩家
    '环境问题-低素质玩家': '环境问题-低素质玩家',
    '环境问题-玩家素质差': '环境问题-低素质玩家',
    '环境问题-素质差': '环境问题-低素质玩家',
    
    # 路人局相关 -> 环境问题-路人局体验差
    '环境问题-路人局体验差': '环境问题-路人局体验差',
    '环境问题-路人局节奏乱': '环境问题-路人局体验差',
    '环境问题-陌生人局体验差': '环境问题-路人局体验差',
    
    # 村规相关 -> 环境问题-村规问题
    '环境问题-村规问题': '环境问题-村规问题',
    '环境问题-村规传播': '环境问题-村规问题',
    '环境问题-房规不统一': '环境问题-村规问题',
    
    # 场外相关 -> 环境问题-场外现象
    '环境问题-场外现象': '环境问题-场外现象',
    '环境问题-场外爆信息': '环境问题-场外现象',
    '环境问题-场外无限制': '环境问题-场外现象',
    '环境问题-贴脸场外': '环境问题-场外现象',
    
    # 技术问题-网络相关 -> 技术问题-网络问题
    '技术问题-网络波动': '技术问题-网络问题',
    '技术问题-网络不稳定': '技术问题-网络问题',
    '技术问题-连接不稳定': '技术问题-网络问题',
    
    # 技术问题-闪退相关 -> 技术问题-闪退问题
    '技术问题-闪退': '技术问题-闪退问题',
    '技术问题-闪退卡顿': '技术问题-闪退问题',
    '技术问题-闪退发热': '技术问题-闪退问题',
    '技术问题-系统崩溃闪退': '技术问题-闪退问题',
    '技术问题-白屏进不去': '技术问题-闪退问题',
    
    # 技术问题-卡顿相关 -> 技术问题-卡顿问题
    '技术问题-卡顿': '技术问题-卡顿问题',
    '技术问题-大厅网络卡': '技术问题-卡顿问题',
    
    # 商业化-氪金相关 -> 商业化问题-氪金问题
    '商业化问题-氪金点过多': '商业化问题-氪金问题',
    '商业化问题-太氪金': '商业化问题-氪金问题',
    '商业化问题-收费高': '商业化问题-氪金问题',
    '商业化问题-圈米严重': '商业化问题-氪金问题',
    
    # 匹配相关 -> 匹配问题-匹配机制
    '匹配问题-匹配机制问题': '匹配问题-匹配机制',
    '匹配问题-水平差距大': '匹配问题-匹配机制',
    '匹配问题-段位匹配不合理': '匹配问题-匹配机制',
}

# 读取文件
target_file = './output/鹅鸭杀_GLM分析_优化版_v1.0.xlsx'
df_target = pd.read_excel(target_file)

# 解析问题分类（格式：大类-子类）
def parse_issues(issues_str):
    if pd.isna(issues_str) or issues_str == '':
        return [], [], []  # 大类列表, 标准子类列表, 原子类列表
    issues = [i.strip() for i in str(issues_str).split(',') if i.strip()]
    main_cats = []
    standard_sub_cats = []  # 合并后的标准子类
    original_sub_cats = []  # 原子类
    
    for issue in issues:
        if '-' in issue:
            parts = issue.split('-', 1)
            main_cat = parts[0].strip()
            main_cats.append(main_cat)
            
            # 获取标准子类（合并后）
            standard_sub = SUB_CLASS_MERGE.get(issue, issue)
            standard_sub_cats.append(standard_sub)
            original_sub_cats.append(issue)  # 保留原子类
        else:
            main_cats.append(issue)
    
    return main_cats, standard_sub_cats, original_sub_cats

# 统计
main_cat_counter = Counter()
standard_sub_cat_counter = Counter()  # 标准子类
original_sub_cat_counter = Counter()  # 原子类（子子类）

for idx, row in df_target.iterrows():
    main_cats, standard_sub_cats, original_sub_cats = parse_issues(row.get('问题分类', ''))
    main_cat_counter.update(main_cats)
    standard_sub_cat_counter.update(standard_sub_cats)
    original_sub_cat_counter.update(original_sub_cats)

print(f"\n大类统计:")
for cat, count in main_cat_counter.most_common(10):
    print(f"  {cat}: {count}次")

print(f"\n标准子类统计TOP15（合并后）:")
for cat, count in standard_sub_cat_counter.most_common(15):
    print(f"  {cat}: {count}次")

print(f"\n原子类统计TOP15（子子类）:")
for cat, count in original_sub_cat_counter.most_common(15):
    print(f"  {cat}: {count}次")

# 构建层级汇总
# 大类 -> 标准子类 -> 原子类
hierarchy = defaultdict(lambda: defaultdict(Counter))

for idx, row in df_target.iterrows():
    main_cats, standard_sub_cats, original_sub_cats = parse_issues(row.get('问题分类', ''))
    for main_cat, std_sub, orig_sub in zip(main_cats, standard_sub_cats, original_sub_cats):
        hierarchy[main_cat][std_sub][orig_sub] += 1

# 导出Excel
output_file = './output/鹅鸭杀_GLM分析_v1.1_合并子类.xlsx'

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
    
    # Sheet5: 问题分类-大类
    main_cat_df = pd.DataFrame(main_cat_counter.most_common(50), columns=['大类', '出现次数'])
    main_cat_df['占比'] = (main_cat_df['出现次数'] / sum(main_cat_counter.values()) * 100).round(1).astype(str) + '%'
    main_cat_df.to_excel(writer, sheet_name='问题分类-大类', index=False)
    
    # Sheet6: 问题分类-标准子类（合并后）
    std_sub_list = []
    for sub_cat, count in standard_sub_cat_counter.most_common(100):
        main_cat = sub_cat.split('-')[0] if '-' in sub_cat else sub_cat
        std_sub_list.append({
            '大类': main_cat,
            '标准子类': sub_cat,
            '出现次数': count,
            '占比': f'{count/sum(standard_sub_cat_counter.values())*100:.1f}%'
        })
    std_sub_df = pd.DataFrame(std_sub_list)
    std_sub_df.to_excel(writer, sheet_name='问题分类-标准子类', index=False)
    
    # Sheet7: 问题分类-层级汇总（大类->标准子类->原子类）
    hierarchy_list = []
    for main_cat in sorted(hierarchy.keys(), key=lambda x: main_cat_counter[x], reverse=True):
        for std_sub in sorted(hierarchy[main_cat].keys(), key=lambda x: sum(hierarchy[main_cat][x].values()), reverse=True):
            std_count = sum(hierarchy[main_cat][std_sub].values())
            for orig_sub, count in hierarchy[main_cat][std_sub].most_common():
                hierarchy_list.append({
                    '大类': main_cat,
                    '大类出现次数': main_cat_counter[main_cat],
                    '标准子类': std_sub,
                    '标准子类出现次数': std_count,
                    '原子类（子子类）': orig_sub,
                    '原子类出现次数': count
                })
    
    hierarchy_df = pd.DataFrame(hierarchy_list)
    hierarchy_df.to_excel(writer, sheet_name='问题分类-层级汇总', index=False)

print(f"\n✓ Excel已保存: {output_file}")

# 打印统计摘要
print("\n" + "="*60)
print("统计摘要")
print("="*60)
print(f"总评价数: {len(df_target)}")
print(f"有问题分类的评价: {df_target['问题分类'].notna().sum()}")
print(f"大类出现总次数: {sum(main_cat_counter.values())}")
print(f"标准子类出现总次数: {sum(standard_sub_cat_counter.values())}")
print(f"原子类出现总次数: {sum(original_sub_cat_counter.values())}")
print(f"大类种类数: {len(main_cat_counter)}")
print(f"标准子类种类数: {len(standard_sub_cat_counter)}")
print(f"原子类种类数: {len(original_sub_cat_counter)}")

# 打印合并效果
print("\n" + "="*60)
print("合并效果示例")
print("="*60)
print("\n'骂人'相关子类合并:")
merged_count = sum(original_sub_cat_counter[k] for k in original_sub_cat_counter if '骂人' in k or '辱骂' in k or '语言攻击' in k)
print(f"  合并前总次数: {merged_count}次")
print(f"  合并后: 环境问题-骂人 = {standard_sub_cat_counter.get('环境问题-骂人', 0)}次")
print("\n原始分布:")
for k, v in sorted(original_sub_cat_counter.items()):
    if '骂人' in k or '辱骂' in k or '语言攻击' in k:
        print(f"  {k}: {v}次")
