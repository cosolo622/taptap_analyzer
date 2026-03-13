# -*- coding: utf-8 -*-
"""
舆情分析优化脚本
1. 补充日期数据
2. 情感分布优化（按天/周统计+趋势图）
3. 问题分类统计优化（大类/子类分层统计+饼图+趋势图）
4. 词云分析（分周词云+高频词TOP10）
5. 输出新的Excel文件
"""

import pandas as pd
import numpy as np
import json
import re
from datetime import datetime, timedelta
from collections import Counter
import os

# 设置中文字体
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

from wordcloud import WordCloud
import jieba
import jieba.analyse

print("="*60)
print("舆情分析优化 - 开始")
print("="*60)

# 1. 读取目标文件
target_file = './output/鹅鸭杀_GLM分析_20260228_111027.xlsx'
df_target = pd.read_excel(target_file)
print(f"\n目标文件: {len(df_target)} 条记录")

# 2. 从其他Excel文件补充日期
source_file = './output/鹅鸭杀_20260227_181757_评价分析_20260227.xlsx'
df_source = pd.read_excel(source_file, sheet_name='评价明细')
print(f"源文件: {len(df_source)} 条记录")

# 通过用户名和评价内容匹配日期
date_map = {}
for idx, row in df_source.iterrows():
    key = (str(row.get('用户名', '')), str(row.get('评价内容', ''))[:50])
    date_map[key] = row.get('评价日期', '')

# 补充日期
dates_filled = 0
for idx, row in df_target.iterrows():
    key = (str(row.get('用户名', '')), str(row.get('评价内容', ''))[:50])
    if key in date_map and pd.isna(row.get('日期', '')):
        df_target.at[idx, '日期'] = date_map[key]
        dates_filled += 1

print(f"已补充日期: {dates_filled} 条")

# 检查日期填充情况
date_count = df_target['日期'].notna().sum()
print(f"日期非空: {date_count}/{len(df_target)} 条")

# 3. 数据预处理
# 添加周字段
df_target['日期'] = pd.to_datetime(df_target['日期'], errors='coerce')
df_target['周'] = df_target['日期'].dt.isocalendar().week
df_target['周开始日期'] = df_target['日期'].apply(
    lambda x: x - timedelta(days=x.weekday()) if pd.notna(x) else None
)
df_target['周标签'] = df_target['周开始日期'].apply(
    lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else '未知'
)

print("\n数据预处理完成")

# 4. 情感分布分析
print("\n" + "="*60)
print("情感分布分析")
print("="*60)

# 4.1 总体情感分布
sentiment_total = df_target['情感'].value_counts()
print(f"\n总体情感分布:")
for s, c in sentiment_total.items():
    print(f"  {s}: {c}条 ({c/len(df_target)*100:.1f}%)")

# 4.2 按天统计
sentiment_daily = df_target.groupby(['日期', '情感']).size().unstack(fill_value=0)
sentiment_daily_pct = sentiment_daily.div(sentiment_daily.sum(axis=1), axis=0) * 100

# 4.3 按周统计
sentiment_weekly = df_target.groupby(['周标签', '情感']).size().unstack(fill_value=0)
sentiment_weekly_pct = sentiment_weekly.div(sentiment_weekly.sum(axis=1), axis=0) * 100

print(f"\n按周情感分布:")
print(sentiment_weekly)

# 5. 问题分类统计
print("\n" + "="*60)
print("问题分类统计")
print("="*60)

# 解析问题分类（格式：大类-子类）
def parse_issues(issues_str):
    if pd.isna(issues_str) or issues_str == '':
        return [], []
    issues = [i.strip() for i in str(issues_str).split(',')]
    main_cats = []
    sub_cats = []
    for issue in issues:
        if '-' in issue:
            parts = issue.split('-', 1)
            main_cats.append(parts[0].strip())
            sub_cats.append(issue)
        else:
            main_cats.append(issue)
    return main_cats, sub_cats

# 统计大类和子类
main_cat_counter = Counter()
sub_cat_counter = Counter()

for idx, row in df_target.iterrows():
    main_cats, sub_cats = parse_issues(row.get('问题分类', ''))
    main_cat_counter.update(main_cats)
    sub_cat_counter.update(sub_cats)

print(f"\n大类统计:")
for cat, count in main_cat_counter.most_common(10):
    print(f"  {cat}: {count}次")

print(f"\n子类统计TOP10:")
for cat, count in sub_cat_counter.most_common(10):
    print(f"  {cat}: {count}次")

# 6. 词云分析
print("\n" + "="*60)
print("词云分析")
print("="*60)

# 停用词
stopwords = set([
    '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', '那', '他', '她', '它', '们', '这个', '那个', '什么', '怎么',
    '可以', '因为', '所以', '但是', '如果', '还是', '或者', '而且', '然后',
    '比较', '真的', '非常', '特别', '还是', '已经', '一直', '一下', '一些',
    '觉得', '感觉', '可能', '应该', '需要', '希望', '建议', '游戏', '玩家',
    '鹅鸭杀', '鹅', '鸭', '杀', '玩', '好玩', '有趣', '不错', '挺好', '太',
    '真的', '特别', '非常', '超级', '十分', '比较', '有点', '稍微', '还是'
])

# 分周统计高频词
weekly_words = {}
for week_label in df_target['周标签'].unique():
    if week_label == '未知':
        continue
    week_df = df_target[df_target['周标签'] == week_label]
    all_text = ' '.join(week_df['评价内容'].dropna().astype(str))
    
    # 分词
    words = jieba.cut(all_text)
    word_list = [w for w in words if len(w) >= 2 and w not in stopwords]
    
    # 统计
    word_counter = Counter(word_list)
    weekly_words[week_label] = word_counter.most_common(50)
    
    print(f"\n{week_label} 周高频词TOP10:")
    for word, count in word_counter.most_common(10):
        print(f"  {word}: {count}次")

# 7. 生成图表
print("\n" + "="*60)
print("生成图表")
print("="*60)

# 创建图表目录
os.makedirs('./output/charts', exist_ok=True)

# 7.1 情感分布饼图
fig, ax = plt.subplots(figsize=(8, 6))
colors = ['#4CAF50', '#FFC107', '#FF5722', '#9E9E9E']
sentiment_total.plot(kind='pie', ax=ax, autopct='%1.1f%%', colors=colors)
ax.set_title('情感分布', fontsize=14)
ax.set_ylabel('')
plt.tight_layout()
plt.savefig('./output/charts/情感分布饼图.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ 情感分布饼图")

# 7.2 情感分天趋势图
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# 条数趋势
sentiment_daily.plot(kind='bar', stacked=True, ax=axes[0], color=colors)
axes[0].set_title('情感分天趋势 - 条数', fontsize=12)
axes[0].set_xlabel('日期')
axes[0].legend(title='情感')
axes[0].tick_params(axis='x', rotation=45)

# 占比趋势
sentiment_daily_pct.plot(kind='line', ax=axes[1], marker='o')
axes[1].set_title('情感分天趋势 - 占比', fontsize=12)
axes[1].set_xlabel('日期')
axes[1].legend(title='情感')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('./output/charts/情感分天趋势.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ 情感分天趋势图")

# 7.3 情感分周趋势图
fig, axes = plt.subplots(2, 1, figsize=(10, 8))

sentiment_weekly.plot(kind='bar', stacked=True, ax=axes[0], color=colors)
axes[0].set_title('情感分周趋势 - 条数', fontsize=12)
axes[0].set_xlabel('周')
axes[0].legend(title='情感')
axes[0].tick_params(axis='x', rotation=45)

sentiment_weekly_pct.plot(kind='line', ax=axes[1], marker='o')
axes[1].set_title('情感分周趋势 - 占比', fontsize=12)
axes[1].set_xlabel('周')
axes[1].legend(title='情感')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('./output/charts/情感分周趋势.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ 情感分周趋势图")

# 7.4 问题分类饼图
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 大类饼图
main_df = pd.DataFrame(main_cat_counter.most_common(10), columns=['分类', '次数'])
axes[0].pie(main_df['次数'], labels=main_df['分类'], autopct='%1.1f%%')
axes[0].set_title('问题大类分布', fontsize=12)

# 子类饼图
sub_df = pd.DataFrame(sub_cat_counter.most_common(10), columns=['分类', '次数'])
axes[1].pie(sub_df['次数'], labels=sub_df['分类'], autopct='%1.1f%%')
axes[1].set_title('问题子类分布TOP10', fontsize=12)

plt.tight_layout()
plt.savefig('./output/charts/问题分类饼图.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ 问题分类饼图")

# 7.5 词云图
for week_label, words in weekly_words.items():
    if not words:
        continue
    
    word_dict = dict(words)
    if len(word_dict) < 10:
        continue
    
    wc = WordCloud(
        font_path='C:/Windows/Fonts/simhei.ttf',
        width=800,
        height=400,
        background_color='white',
        max_words=50
    )
    wc.generate_from_frequencies(word_dict)
    
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.title(f'{week_label} 周词云', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'./output/charts/词云_{week_label}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ 词云图 - {week_label}")

# 8. 导出Excel
print("\n" + "="*60)
print("导出Excel")
print("="*60)

output_file = './output/鹅鸭杀_GLM分析_优化版_v1.0.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet1: 评价明细（补充日期后）
    df_target.to_excel(writer, sheet_name='评价明细', index=False)
    
    # Sheet2: 情感分布-总体
    sentiment_total_df = pd.DataFrame({
        '情感': sentiment_total.index,
        '数量': sentiment_total.values,
        '占比': [f'{v/len(df_target)*100:.1f}%' for v in sentiment_total.values]
    })
    sentiment_total_df.to_excel(writer, sheet_name='情感分布-总体', index=False)
    
    # Sheet3: 情感分布-按天
    sentiment_daily.reset_index().to_excel(writer, sheet_name='情感分布-按天', index=False)
    
    # Sheet4: 情感分布-按周
    sentiment_weekly.reset_index().to_excel(writer, sheet_name='情感分布-按周', index=False)
    
    # Sheet5: 问题分类-大类
    main_cat_df = pd.DataFrame(main_cat_counter.most_common(20), columns=['大类', '出现次数'])
    main_cat_df.to_excel(writer, sheet_name='问题分类-大类', index=False)
    
    # Sheet6: 问题分类-子类
    sub_cat_df = pd.DataFrame(sub_cat_counter.most_common(30), columns=['子类', '出现次数'])
    # 添加大类列
    sub_cat_df['大类'] = sub_cat_df['子类'].apply(lambda x: x.split('-')[0] if '-' in x else x)
    sub_cat_df = sub_cat_df[['大类', '子类', '出现次数']]
    sub_cat_df.to_excel(writer, sheet_name='问题分类-子类', index=False)
    
    # Sheet7: 高频词-分周
    weekly_words_df = pd.DataFrame()
    for week_label, words in weekly_words.items():
        if not words:
            continue
        week_df = pd.DataFrame(words[:10], columns=['词语', '频次'])
        week_df['周'] = week_label
        weekly_words_df = pd.concat([weekly_words_df, week_df], ignore_index=True)
    weekly_words_df = weekly_words_df[['周', '词语', '频次']]
    weekly_words_df.to_excel(writer, sheet_name='高频词-分周', index=False)

print(f"\n✓ Excel已保存: {output_file}")

print("\n" + "="*60)
print("分析完成!")
print("="*60)
