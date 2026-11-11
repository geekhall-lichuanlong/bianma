import pandas as pd

# Excel 文件路径
excel_file = r"/opt/lcl/OCR/PaddleOCR-main/ppstructure/6186.xlsx"

# 读取 Excel 文件（确保使用 openpyxl 引擎）
df = pd.read_excel(excel_file, engine="openpyxl")

# 将 NaN 替换为 None，以便在导出 JSON 时显示为空字符串或 null
df = df.where(pd.notnull(df), None)

# 转换为 JSON 格式（每一行是一个字典，组成一个列表）
json_data = df.to_dict(orient="records")

# 保存为 .json 文件（可选）
output_file = r"/opt/lcl/OCR/PaddleOCR-main/ppstructure/6186.json"
with open(output_file, "w", encoding="utf-8") as f:
    import json
    json.dump(json_data, f, ensure_ascii=False, indent=4)

print("转换完成，输出文件路径：", output_file)
