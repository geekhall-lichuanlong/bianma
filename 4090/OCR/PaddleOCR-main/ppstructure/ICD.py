import pandas as pd
import numpy as np

def process_diagnosis_codes(df):
    """
    处理其他诊断编码1-7，将非空的编码用分号连接
    
    Parameters:
    -----------
    df : DataFrame
        包含其他诊断编码1-7的数据框
    
    Returns:
    --------
    str
        用分号连接的非空编码
    """
    # 获取其他诊断编码1-7的列
    other_diagnosis_cols = [f'其他诊断编码{i}' for i in range(1, 8)]
    # 选择存在的列（处理可能不是所有编码都存在的情况）
    existing_cols = [col for col in other_diagnosis_cols if col in df.columns]
    
    if not existing_cols:
        return ''
    
    # 获取一行中所有非空的诊断编码
    codes = df[existing_cols].values[0]
    # 过滤掉空值并用分号连接
    valid_codes = [str(code) for code in codes if pd.notna(code) and str(code).strip()]
    return ';'.join(valid_codes)

def match_and_fill_excel(file_a_path, file_b_path, output_path):
    """
    从Excel A中检索诊断信息填充到Excel B中
    
    Parameters:
    -----------
    file_a_path : str
        源Excel文件路径 (用于检索数据的文件A)
    file_b_path : str
        目标Excel文件路径 (需要被填充的文件B)
    output_path : str
        输出文件路径
    """
    try:
        # 读取两个Excel文件
        df_a = pd.read_excel(file_a_path)
        df_b = pd.read_excel(file_b_path)
        
        # 确保必要的列存在
        required_columns = ["病案标识", "住院号"]
        for col in required_columns:
            if col not in df_a.columns or col not in df_b.columns:
                raise ValueError(f"文件缺少必要的列: {col}")
        
        # 在B中创建新的列
        df_b['门急诊断编码'] = ''
        df_b['主要诊断编码'] = ''
        df_b['其他诊断编码'] = ''
        
        # 基于病案标识和住院号进行匹配
        for index, row in df_b.iterrows():
            # 在A中查找匹配的记录
            match_condition = (df_a['病案标识'] == row['病案标识']) & \
                            (df_a['住院号'] == row['住院号'])
            matched_rows = df_a[match_condition]
            
            if not matched_rows.empty:
                # 填充门急诊断编码
                if '门急诊断编码' in df_a.columns:
                    df_b.at[index, '门急诊断编码'] = matched_rows['门急诊断编码'].iloc[0] \
                        if pd.notna(matched_rows['门急诊断编码'].iloc[0]) else ''
                
                # 填充主要诊断编码
                if '主要诊断编码' in df_a.columns:
                    df_b.at[index, '主要诊断编码'] = matched_rows['主要诊断编码'].iloc[0] \
                        if pd.notna(matched_rows['主要诊断编码'].iloc[0]) else ''
                
                # 处理其他诊断编码1-7
                df_b.at[index, '其他诊断编码'] = process_diagnosis_codes(matched_rows)
        
        # 保存结果
        df_b.to_excel(output_path, index=False)
        print(f"数据匹配完成，结果已保存至: {output_path}")
        
        # 打印统计信息
        total_records = len(df_b)
        matched_records = df_b[df_b['门急诊断编码'] != ''].shape[0]
        print(f"\n统计信息:")
        print(f"总记录数: {total_records}")
        print(f"成功匹配记录数: {matched_records}")
        print(f"匹配率: {(matched_records/total_records)*100:.2f}%")
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")

# 使用示例
if __name__ == "__main__":
    file_a = "shouye.xlsx"  # 源文件路径
    file_b = "combined_data.xlsx"  # 目标文件路径
    output = "data.xlsx"  # 输出文件路径
    
    match_and_fill_excel(file_a, file_b, output)