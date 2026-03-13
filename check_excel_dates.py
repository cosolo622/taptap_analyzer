"""
检查所有Excel文件，寻找包含日期的数据源
"""
import pandas as pd
import os

output_dir = 'output'
excel_files = [f for f in os.listdir(output_dir) if f.endswith('.xlsx') and not f.startswith('~$')]

print("检查所有Excel文件的日期列情况:")
print("=" * 80)

for excel_file in excel_files:
    file_path = os.path.join(output_dir, excel_file)
    print(f"\n文件: {excel_file}")

    try:
        df = pd.read_excel(file_path)

        # 检查是否有日期相关列
        date_cols = [col for col in df.columns if '日期' in col or 'date' in col.lower() or '时间' in col]

        if date_cols:
            print(f"  日期相关列: {date_cols}")
            for col in date_cols:
                non_empty = df[col].notna().sum()
                print(f"    {col}: 非空数量={non_empty}/{len(df)}")
                if non_empty > 0:
                    print(f"    前5个值: {df[col].head(5).tolist()}")
        else:
            print(f"  无日期相关列")

        # 显示所有列名
        print(f"  所有列: {df.columns.tolist()}")

    except Exception as e:
        print(f"  读取失败: {e}")
