import pandas as pd
import openpyxl
from tools.biaoge import getrow
import json
import os

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

def save_surgery(med_record_id, main_surgery_name, other_surgery_names):
    """
    把一条手术信息保存为 JSONL 的一行。

    每条记录结构如下：
        {
            "med_record_id": ...,
            "main_surgery_name": ...,
            "other_surgery_names": [...]
        }
    """
    jsonl_path = "/mnt/bigdisk/all_surgery/data/re/28061.jsonl"

    # 这里如果你还想要拼好的手术字符串，也可以顺便算一下
    surgery_info = str_surgery(med_record_id, main_surgery_name, other_surgery_names)

    record = {
        "med_record_id": med_record_id,
        "main_surgery_name": main_surgery_name,
        "other_surgery_names": other_surgery_names,
        "surgery_info": surgery_info,
    }

    # 写入 JSON Lines 文件，每条一行
    os.makedirs(os.path.dirname(jsonl_path) or ".", exist_ok=True)
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"已保存病案标识号 {med_record_id} 的手术信息到 {jsonl_path}。")
