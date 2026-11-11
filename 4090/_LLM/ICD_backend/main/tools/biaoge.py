import openpyxl
import pandas as pd
import requests
import time
# biaoge.py
current_idx = None


def main():
    excel_path = "/mnt/bigdisk/all_surgery/data/re/28061.xlsx"
    cols = ["病案标识", "手术名称", "手术经过", "病程"]
    url = "http://localhost:6000/qwen3/surgeries_diagnosis"

    # 读取 Excel
    df = pd.read_excel(excel_path, dtype=str, engine="openpyxl")
    # 缺失值填充为空字符串
    df[cols] = df[cols].fillna("")
    start_row = 2
    
    # 按行遍历
    # for idx, row in df.iterrows():
    for idx, row in df.iloc[start_row:].iterrows():
        # 分别取出四个字段
        case_id = row["病案标识"]
        surgery_name = row["手术名称"]
        surgery_course = row["手术经过"]
        record = row["病程"]

        # 只有全部非空才拼接并发送请求
        
        set_current_idx(idx)
        start_time = time.time()
        if all([case_id != "", surgery_name != "", surgery_course != "", record != ""]):
            parts = [
                f"病案标识：{case_id}",
                f"手术名称：{surgery_name}",
                f"手术经过：{surgery_course}",
                f"病程：{record}"
            ]
            content = "\n".join(parts)
            # print(f"处理第 {idx + 2} 行，病案标识号: {case_id}")
            # print(content)
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            }
            requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            # time.sleep(1)  # 可选暂停
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"处理第 {idx + 2} 行，病案标识号: {case_id}, 耗时: {processing_time:.2f}秒")
            time.sleep(1)  # 控制请求频率，避免过快


def getrow():
    # print(current_idx)
    return current_idx
def set_current_idx(idx):
    global current_idx
    current_idx = idx

if __name__ == "__main__":
    main()