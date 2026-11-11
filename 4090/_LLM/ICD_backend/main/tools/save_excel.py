import pandas as pd
import openpyxl
from tools.biaoge import getrow
import json
import os


# def str_surgery(med_record_id, main_surgery_name, other_surgery_names):
#     """
#     处理病案标识号和手术名称列表，返回格式化后的字符串。

#     参数:
#         med_record_id (str): 病案标识号，可能包含 "/n" 需要去除。
#         main_surgery_name (str): 主要手术名称。
#         other_surgery_names (list): 其他手术名称列表。

#     返回:
#         tuple: (处理后的病案标识号, 格式化后的手术名称字符串)
#     """
#     # 其他手术名拼接成字符串
#     other_surgery_str = "；".join(other_surgery_names)
#     # 主手术名在前，拼接
#     surgery_info = main_surgery_name + "；" + other_surgery_str if other_surgery_str else main_surgery_name
#     return surgery_info
    
def str_surgery(med_record_id, main_surgery_name, other_surgery_names):
    """
    处理病案标识号和手术名称列表，返回格式化后的字符串。

    参数:
        med_record_id (str): 病案标识号，可能包含 "/n" 需要去除。
        main_surgery_name (str or list): 主要手术名称，可能是字符串或列表。
        other_surgery_names (list): 其他手术名称列表。

    返回:
        tuple: (处理后的病案标识号, 格式化后的手术名称字符串)
    """

    # 处理主要手术名称，确保是字符串
    if isinstance(main_surgery_name, list):
        if main_surgery_name:
            main_surgery_str = "；".join(main_surgery_name)
        else:
            main_surgery_str = ""
    else:
        main_surgery_str = str(main_surgery_name) if main_surgery_name else ""
    
    # 处理其他手术名称，拼接成字符串
    if other_surgery_names:
        other_surgery_str = "；".join(other_surgery_names)
    else:
        other_surgery_str = ""
    
    # 拼接手术信息
    if main_surgery_str and other_surgery_str:
        surgery_info = main_surgery_str + "；" + other_surgery_str
    elif main_surgery_str:
        surgery_info = main_surgery_str
    elif other_surgery_str:
        surgery_info = other_surgery_str
    else:
        surgery_info = ""
    
    return surgery_info

# def save_surgery_info_to_excel(file_path, med_record_id, surgery_info, output_column_name="大模型输出"):
#     # 打开 excel 文件
#     wb = openpyxl.load_workbook(file_path)
#     ws = wb.active
    
#     # 获取表头
#     header = [cell.value for cell in ws[1]]
#     # 病案标识号和“大模型输出”所在的列索引（从1开始）
#     # try:
#     #     med_record_col = header.index("病案标识号") + 1
#     # except ValueError:
#     #     raise Exception("表格中没有 '病案标识号' 列")
#     # try:
#     #     output_col = header.index(output_column_name) + 1
#     # except ValueError:
#     #     raise Exception(f"表格中没有 '{output_column_name}' 列")

    
#     med_record_col = 1
#     output_col=183
#     print(f"病案标识号列: {med_record_col}, 大模型输出列: {output_col}")
    
#     # 查找病案标识号所在行
#     row_to_update = None
#     for row in ws.iter_rows(min_row=2, values_only=False):
#         cell_value = row[med_record_col - 1].value
#         if cell_value == med_record_id:
#             row_to_update = row
#             break
    
    
#     if row_to_update is None:
#         raise Exception(f"未找到病案标识号 {med_record_id} 的行")

#     # 写入 surgery_info 到指定列
#     row_to_update[output_col - 1].value = surgery_info

#     # 保存 excel
#     wb.save(file_path)

# def save_surgery(med_record_id, main_surgery_name, other_surgery_names):
def save_surgery(med_record_id,S_standardized_output,S_additiona_output,main_surgery_orthers_name,S_sorting_output,S_screening_output,main_surgery_name,main_surgery_icd,other_surgery_names,other_surgery_icds):
    """
    把一条手术信息保存为 JSONL 的一行。

    每条记录结构如下：
        {
            "med_record_id": ...,
            "main_surgery_name": ...,
            "other_surgery_names": [...]
        }
    """
    jsonl_path = "/opt/qianyi/4090/_LLM/ICD_backend/new_28061.jsonl"

    # 这里如果你还想要拼好的手术字符串，也可以顺便算一下
    # surgery_info = str_surgery(med_record_id, main_surgery_name, other_surgery_names)
    # record = {
    #     "med_record_id": med_record_id,
    #     "main_surgery_name": main_surgery_name,
    #     "other_surgery_names": other_surgery_names,
    #     "surgery_info": surgery_info,
    # }
    record={
        "med_record_id": med_record_id,
        "标准化": S_standardized_output,
        "潜在疾病": S_additiona_output,
        "另编码": main_surgery_orthers_name,
        "排序": S_sorting_output,
        "筛查": S_screening_output,
        "主手术": main_surgery_name,
        "主手术ICD": main_surgery_icd,
        "其他手术": other_surgery_names,
        "其他手术ICD": other_surgery_icds,
    }

    # 写入 JSON Lines 文件，每条一行
    os.makedirs(os.path.dirname(jsonl_path) or ".", exist_ok=True)
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"已保存病案标识号 {med_record_id} 的手术信息到 {jsonl_path}。")


