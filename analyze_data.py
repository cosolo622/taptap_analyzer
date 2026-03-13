"""
数据分析脚本 - 读取和诊断Excel文件
"""
import pandas as pd
import os

# 文件路径
file_path = r'c:\Users\Administrator\Documents\trae_projects\99multi\taptap_analyzer\output\鹅鸭杀_GLM分析_20260228_111027.xlsx'

# 读取Excel文件
print("=" * 60)
print("正在读取文件...")
print("=" * 60)
df = pd.read_excel(file_path)

# 基本信息
print(f"\n数据形状: {df.shape}")
print(f"总行数: {len(df)}")
print(f"总列数: {len(df.columns)}")

print("\n列名列表:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")

print("\n数据类型:")
print(df.dtypes)

print("\n前5行数据:")
print(df.head())

print("\n数据统计:")
print(df.describe(include='all'))

# 检查日期列
print("\n" + "=" * 60)
print("日期列诊断")
print("=" * 60)

if '日期' in df.columns:
    print(f"\n日期列存在")
    print(f"日期列非空数量: {df['日期'].notna().sum()}")
    print(f"日期列空值数量: {df['日期'].isna().sum()}")
    print(f"日期列前10个值: {df['日期'].head(10).tolist()}")
    print(f"日期列数据类型: {df['日期'].dtype}")
else:
    print("\n日期列不存在!")
    print("可用列名:", df.columns.tolist())

# 检查其他可能包含日期信息的列
print("\n" + "=" * 60)
print("检查所有列的前5个值")
print("=" * 60)
for col in df.columns:
    print(f"\n列名: {col}")
    print(f"前5个值: {df[col].head(5).tolist()}")
