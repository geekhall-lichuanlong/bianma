import json
import numpy as np

# 假设 json 文件名叫 data.json，与脚本在同一目录
with open('/opt/WEM/yan1/qianfoshan/p3/ICD/tmp/100.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 按出现顺序拼接：key: value\nkey: value\n...
result = '\n'.join(f'{k}: {v}' for k, v in data[np.random.randint(0, 100)].items())

print(result)          # 直接打印
# 如果需要保存：
# with open('output.txt', 'w', encoding='utf-8') as f_out:
#     f_out.write(result)