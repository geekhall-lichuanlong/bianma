import pandas as pd
from collections import Counter
from datetime import datetime

def process_excel_complete(input_file):
    try:
        # 读取Excel文件
        df = pd.read_excel(input_file)
        
        # 收集主要诊断编码
        main_codes = []
        if '主要诊断编码' in df.columns:
            codes = df['主要诊断编码'].dropna().astype(str)
            main_codes.extend(codes[codes.str.strip() != ''].str.strip().tolist())
        
        # 收集其他诊断编码
        other_codes = []
        other_columns = [f'其他诊断编码{i}' for i in range(1, 8)]
        for column in other_columns:
            if column in df.columns:
                codes = df[column].dropna().astype(str)
                other_codes.extend(codes[codes.str.strip() != ''].str.strip().tolist())
        
        # 统计频率
        main_frequency = Counter(main_codes)
        other_frequency = Counter(other_codes)
        
        # 获取所有唯一的ICD编码
        all_codes = set(main_codes) | set(other_codes)
        
        # 创建结果列表
        results = []
        for code in all_codes:
            results.append({
                'ICD编码': code,
                '主要诊断出现次数': main_frequency[code],
                '其他诊断出现次数': other_frequency[code],
                '总出现次数': main_frequency[code] + other_frequency[code]
            })
        
        # 创建结果DataFrame并排序
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values('总出现次数', ascending=False)
        result_df = result_df.reset_index(drop=True)
        
        # 获取高频编码集合
        high_freq_main_codes = {code for code, count in main_frequency.items() if count >= 320}
        high_freq_other_codes = {code for code, count in other_frequency.items() if count >= 300}
        
        # 将高频编码转换为以分号分隔的字符串
        high_freq_main_str = ";".join(sorted(high_freq_main_codes))
        high_freq_other_str = ";".join(sorted(high_freq_other_codes))
        
        # 分析每条记录是否满足高频组合条件
        def has_high_freq_other_diagnosis(row):
            for i in range(1, 8):
                col = f'其他诊断编码{i}'
                if col in row and pd.notna(row[col]):
                    if str(row[col]).strip() in high_freq_other_codes:
                        return True
            return False
        
        # 计算每个病例中高频其他诊断的数量
        def count_high_freq_other_diagnoses(row):
            count = 0
            for i in range(1, 8):
                col = f'其他诊断编码{i}'
                if col in row and pd.notna(row[col]):
                    if str(row[col]).strip() in high_freq_other_codes:
                        count += 1
            return count
        
        # 为原始数据添加标记列
        df['满足高频主诊断'] = df['主要诊断编码'].apply(lambda x: str(x).strip() in high_freq_main_codes if pd.notna(x) else False)
        df['满足高频其他诊断'] = df.apply(has_high_freq_other_diagnosis, axis=1)
        df['满足组合条件'] = df['满足高频主诊断'] & df['满足高频其他诊断']
        
        # 计算满足条件的记录数
        matching_records = df['满足组合条件'].sum()
        
        # 创建统计信息DataFrame
        stats = [
            {'统计指标': '统计时间', '数值': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {'统计指标': '不同ICD编码数量', '数值': len(all_codes)},
            {'统计指标': '主要诊断编码总出现次数', '数值': sum(main_frequency.values())},
            {'统计指标': '其他诊断编码总出现次数', '数值': sum(other_frequency.values())},
            {'统计指标': '总出现次数', '数值': result_df['总出现次数'].sum()},
            {'统计指标': '高频主要诊断编码数量(≥320次)', '数值': len(high_freq_main_codes)},
            {'统计指标': '高频其他诊断编码数量(≥300次)', '数值': len(high_freq_other_codes)},
            {'统计指标': '满足高频组合条件的病例数', '数值': matching_records}
        ]
        stats_df = pd.DataFrame(stats)
        
        # 保存结果到新的Excel文件
        output_file = 'ICD编码统计结果_完整版.xlsx'
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 写入主要统计结果
            result_df.to_excel(writer, index=False, sheet_name='ICD编码统计')
            
            # 写入统计信息
            stats_df.to_excel(writer, index=False, sheet_name='统计汇总')
            
            # 写入满足条件的记录以及高频其他诊断数量
            matching_records_df = df[df['满足组合条件']].copy()
            matching_records_df['高频其他诊断数量'] = matching_records_df.apply(count_high_freq_other_diagnoses, axis=1)
            
            # 重新排列列顺序，将'高频其他诊断数量'放在最前面
            columns = matching_records_df.columns.tolist()
            columns.remove('高频其他诊断数量')
            columns = ['高频其他诊断数量'] + columns
            matching_records_df = matching_records_df[columns]
            
            matching_records_df.to_excel(writer, index=False, sheet_name='满足条件的病例')
            
            # 写入高频编码列表
            high_freq_codes_df = pd.DataFrame({
                '高频主要诊断编码': list(high_freq_main_codes) + [''] * (len(high_freq_other_codes) - len(high_freq_main_codes)) if len(high_freq_other_codes) > len(high_freq_main_codes) else list(high_freq_main_codes),
                '高频其他诊断编码': list(high_freq_other_codes) + [''] * (len(high_freq_main_codes) - len(high_freq_other_codes)) if len(high_freq_main_codes) > len(high_freq_other_codes) else list(high_freq_other_codes)
            })
            high_freq_codes_df.to_excel(writer, index=False, sheet_name='高频编码列表')
            
            # 获取工作簿
            workbook = writer.book
            
            # 调整各个工作表的格式
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column = [cell for cell in column]
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
        
        # 保存高频编码到文本文件
        with open('高频编码列表.txt', 'w', encoding='utf-8') as f:
            f.write("高频主要诊断编码(≥320次):\n")
            f.write(high_freq_main_str + "\n\n")
            f.write("高频其他诊断编码(≥300次):\n")
            f.write(high_freq_other_str)
        
        # 打印高频编码
        print("\n=== 高频编码列表 ===")
        print(f"\n高频主要诊断编码(≥320次):\n{high_freq_main_str}")
        print(f"\n高频其他诊断编码(≥300次):\n{high_freq_other_str}")
        
        # 打印关键统计结果
        print(f"\n=== 统计结果 ===")
        print(f"高频主要诊断编码数量(≥320次): {len(high_freq_main_codes)}")
        print(f"高频其他诊断编码数量(≥300次): {len(high_freq_other_codes)}")
        print(f"满足高频组合条件的病例数: {matching_records}")
        print(f"\n详细结果已保存至: {output_file}")
        print(f"高频编码列表已保存至: 高频编码列表.txt")
        
        return result_df, stats_df, matching_records_df, high_freq_codes_df, high_freq_main_str, high_freq_other_str
        
    except Exception as e:
        print(f"处理Excel文件时发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    # 替换为你的Excel文件路径
    input_file = "心内首页2024.xlsx"
    result_df, stats_df, matching_df, high_freq_df, high_freq_main_str, high_freq_other_str = process_excel_complete(input_file)