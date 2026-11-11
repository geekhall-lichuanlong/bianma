import pandas as pd

input_path = "/opt/qianyi/4090/_LLM/ICD_backend/main/tools/28061.xlsx"
output_path = "/opt/qianyi/4090/_LLM/ICD_backend/main/tools/28061_top10.xlsx"

# 读取前10行
df_top10 = pd.read_excel(input_path, nrows=10)

# 保存
df_top10.to_excel(output_path, index=False)

print("Saved first 10 rows to:", output_path)