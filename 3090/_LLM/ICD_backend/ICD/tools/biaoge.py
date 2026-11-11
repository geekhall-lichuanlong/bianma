import openpyxl
import pandas as pd
import requests
import time
# biaoge.py
current_idx = None


def main():
    excel_path = "/mnt/bigdisk/all_disease/data/79429.xlsx"
    # 使用你指定的这些列名
    cols = [
        "病案标识",
        "主诉",
        "现病史",
        "既往史",
        "入院情况",
        "出院诊断",
        "诊疗经过",
        "病程",
        "影像学意见",
        "超声结果",
        "病理结果",
        "术前诊断",
        "术中诊断",
    ]
    url = "http://localhost:5000/qwen3/diagnosis_qwen"

    # 读取 Excel
    df = pd.read_excel(excel_path, dtype=str, engine="openpyxl")
    # 缺失值填充为空字符串
    df[cols] = df[cols].fillna("")
    start_row = 9433

    # 按行遍历
    # for idx, row in df.iterrows():
    for idx, row in df.iloc[start_row:].iterrows():
        # 分别取出各个字段
        case_id = row["病案标识"]
        chief_complaint = row["主诉"]
        present_history = row["现病史"]
        past_history = row["既往史"]
        admission_status = row["入院情况"]
        discharge_diag = row["出院诊断"]
        treatment_course = row["诊疗经过"]
        course_record = row["病程"]
        imaging_opinion = row["影像学意见"]
        us_result = row["超声结果"]
        pathology_result = row["病理结果"]
        preop_diag = row["术前诊断"]
        intraop_diag = row["术中诊断"]

        set_current_idx(idx)
        start_time = time.time()

        # 只有全部非空才拼接并发送请求
        # 病案标识，主诉，入院情况，出院诊断，诊疗经过，病程   
        if all([
            case_id != "",
            chief_complaint != "",
            admission_status != "",
            discharge_diag != "",
            treatment_course != "",
            course_record != ""
        ]):
            parts = [
                f"病案标识：{case_id}",
                f"主诉：{chief_complaint}",
                f"现病史：{present_history}",
                f"既往史：{past_history}",
                f"入院情况：{admission_status}",
                f"出院诊断：{discharge_diag}",
                f"诊疗经过：{treatment_course}",
                f"病程：{course_record}",
                f"影像学意见：{imaging_opinion}",
                f"超声结果：{us_result}",
                f"病理结果：{pathology_result}",
                f"术前诊断：{preop_diag}",
                f"术中诊断：{intraop_diag}",
            ]
            content = "\n".join(parts)

            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            }
            requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"处理第 {idx + 2} 行，病案标识: {case_id}, 耗时: {processing_time:.2f}秒")
            time.sleep(1)  # 控制请求频率，避免过快
        else :
            print(f"跳过第 {idx + 2} 行，病案标识: {case_id}，存在空字段")


def getrow():
    # print(current_idx)
    return current_idx


def set_current_idx(idx):
    global current_idx
    current_idx = idx


if __name__ == "__main__":
    main()
