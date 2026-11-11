import os
from openai import OpenAI
import pandas as pd
import json
import re

from elasticsearch import Elasticsearch

# ===================== ES初始化 =====================
es = Elasticsearch(
    "https://127.0.0.1:9200/",
    ca_certs="/opt/qianyi/3090/database/elasticsearch-9.2.3/config/certs/http_ca.crt",
    http_auth=('elastic', os.environ.get("ELASTIC_PASSWORD", "")),
    verify_certs=False,
    ssl_show_warn=False
)

# ===================== LLM初始化 =====================
client = OpenAI(
    api_key=os.environ.get('API_KEY', ""),
    base_url="http://127.0.0.1:8000/v1"
)

# ===================== 模型调用 =====================
def test_model(prompt_content):
    try:
        response = client.chat.completions.create(
            model="surgery_agent1_v20260113_1.7B",
            messages=[
                {"role": "user", "content": prompt_content}
            ],
            temperature=0.7,
            max_tokens=512
        )
        json_res = response.choices[0].message.content.split('</think>')[-1].strip()
        return json_res
    except Exception as e:
        print(f"调用失败: {e}")
        return None


# ===================== ES检索 =====================
def __search_icd(surgery_name):
    search_body = {
        "query": {
            "term": {
                "name.keyword": {
                    "value": surgery_name
                }
            }
        }
    }
    res = es.search(index="surgery_icd_tree", body=search_body)

    if res["hits"]["total"]["value"] == 0:
        return None
    else:
        return [hit["_source"]["icd_code"] for hit in res["hits"]["hits"]]


# ===================== 找不到ICD的术语 =====================
def __remove_unmatched_surgery(full_content):
    return [sur for sur in full_content if __search_icd(sur) is None]


# ===================== 归一化 =====================
def normalize_text(text):
    text = str(text)

    # 去后缀
    text = re.sub(r'(术|手术|治疗|操作)$', '', text)

    # 去修饰词（关键！！）
    noise_words = [
        "CT引导下", "CT引导", "经皮", "显微镜下", "腹腔镜", "胸腔镜",
        "占位", "病损", "病变", "肿物", "肿瘤"
    ]

    for w in noise_words:
        text = text.replace(w, "")

    return text


# ===================== 提取核心关键词 =====================
def extract_keywords(text):
    """
    提取核心医学关键词（部位+操作）
    """
    text = normalize_text(text)

    # 常见医学操作词
    action_keywords = [
        "切除", "活检", "穿刺", "造口", "吻合", "扩张",
        "置入", "置换", "修补", "固定", "减压", "引流"
    ]

    keywords = set()

    # 提取操作词
    for ak in action_keywords:
        if ak in text:
            keywords.add(ak)

    # 剩余部分按长度切分（提取部位词）
    parts = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
    for p in parts:
        if p not in action_keywords:
            keywords.add(p)

    return keywords


# ===================== 核心匹配函数（重点） =====================
def is_match(val, text_piece):
    """
    多层匹配：
    1. 原始包含
    2. 归一化包含
    3. 关键词匹配（>=2个交集）
    """

    # 原始
    if val in text_piece or text_piece in val:
        return True

    val_norm = normalize_text(val)
    text_norm = normalize_text(text_piece)

    # 归一化
    if val_norm in text_norm or text_norm in val_norm:
        return True

    # ===== 关键词匹配（核心升级）=====
    val_keys = extract_keywords(val)
    text_keys = extract_keywords(text_piece)

    common = val_keys & text_keys

    # 👉 至少2个关键词重合（非常关键）
    if len(common) >= 2:
        return True

    return False


# ===================== 构造标准答案 =====================
def build_gold_answer(row):

    surgery_text = str(row["手术名称"]) if pd.notna(row["手术名称"]) else ""

    # 优先按 + 分割
    split_texts = re.split(r'[+]', surgery_text)

    # 再细分
    temp = []
    for t in split_texts:
        temp.extend(re.split(r'[，,；;、\s]', t))

    split_texts = [t.strip() for t in temp if t.strip()]

    candidate_fields = ["主要手术操作名称"] + [f"其他手术操作名称{i}" for i in range(1, 31)]

    matched = []

    for field in candidate_fields:
        if field not in row:
            continue

        value = row[field]

        if pd.isna(value):
            continue

        value = str(value).strip()
        if not value:
            continue

        for text_piece in split_texts:
            if is_match(value, text_piece):
                matched.append(value)
                break

    return list(set(matched))


# ===================== 主流程 =====================
if __name__ == "__main__":

    excel_path = "/opt/qianyi/4090/_LLM/ICD_backend/main/tools/28061_top10.xlsx"

    df = pd.read_excel(excel_path, dtype=str, engine="openpyxl")

    start_row = 2
    output_list = []

    for idx, row in df.iloc[start_row:].iterrows():

        case_input = {
            "病案标识": row.get("病案标识", ""),
            "手术名称": row.get("手术名称", ""),
            "手术经过": row.get("手术经过", ""),
            "病程": row.get("病程", ""),
        }

        content = "\n".join([f"{k}:{v}" for k, v in case_input.items()])

        # ===== 模型推理 =====
        json_res = test_model(content)
        if json_res is None:
            continue

        try:
            res = json.loads(json_res)
        except Exception as e:
            print(f"json解析失败: {e}, 内容: {json_res}")
            continue

        sur_list = list(set(res.get("手术名称标准化", [])))

        # ===== 标准答案 =====
        gold_answer = build_gold_answer(row)

        # ===== ICD校验 =====
        unmatched_surgery = __remove_unmatched_surgery(sur_list)

        result_dict = {
            "病历输入": content,
            "标准答案": gold_answer,
            "模型输出": sur_list
        }

        output_list.append(result_dict)

    # ===================== 保存 =====================
    out_json_path = "/opt/qianyi/4090/_LLM/ICD_backend/main/tools/ICD_surgery_check_output.json"

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(output_list, f, ensure_ascii=False, indent=2)

    print(f"已保存至 {out_json_path}")