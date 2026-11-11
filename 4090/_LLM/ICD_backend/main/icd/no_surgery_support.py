from tools.agent_timing import timed_call
from flask import Flask, request, jsonify, Response, stream_with_context
import requests
import json
import time
import os
import threading
import re
import tempfile
from elasticsearch import Elasticsearch
from datetime import datetime
from icd.SurgeryAgents import get_agent_output_stream
from tools.orthers_search import orthers_search, ORTHER
from tools.微创 import query_surgery_level
from tools.save_excel import save_surgery
from tools.surgery_traceability import trace_surgery_evidence

es = Elasticsearch(
    "https://127.0.0.1:9200/",
    ca_certs="/opt/qianyi/3090/database/elasticsearch-9.2.3/config/certs/http_ca.crt",        # 证书绝对路径
    http_auth=('elastic', os.environ.get("ELASTIC_PASSWORD", "")),  # 用户名和密码
    verify_certs=False,  # 禁用证书验证
    ssl_show_warn=False  # 不显示SSL警告
)



    
    
    
    
    
def __trace_surgery_evidence(main_surgery_name, main_surgery_icd, other_surgery_names, other_surgery_icds, messages):
    trace_names = []
    for name in [main_surgery_name] + (other_surgery_names or []):
        if name and name not in trace_names:
            trace_names.append(name)

    print(f"待溯源手术列表: {trace_names}")
    code_map = {}
    if main_surgery_name:
        code_map[main_surgery_name] = main_surgery_icd
    for name, code in zip(other_surgery_names or [], other_surgery_icds or []):
        code_map[name] = code
    evidence_map = trace_surgery_evidence(trace_names, messages, code_map=code_map,
                                          request_timeout=(10, 45), max_attempts=1, max_tokens=2048)
    print(f"手术模型溯源输出: {evidence_map}")
    return evidence_map

def __get_json(text: str) -> dict:
    """
    将病历字符串解析成结构化 JSON
    :param text: 原始病历字符串
    :return: dict，字段与题目要求保持一致
    """

    # 1. 预定义目标字段顺序（可按需要增删）
    keys = [
        "病案标识","手术名称", "手术经过", "病程"
       
    ]

    # 2. 构造正则：以“key：”开头，非贪婪匹配到下一个“key：”或字符串结尾
    pattern = r'(' + '|'.join(map(re.escape, keys)) + r')：\s*(.*?)(?=(?:' + \
              '|'.join(map(re.escape, keys)) + r')：|$)'
    matches = re.findall(pattern, text, flags=re.S)

    # 3. 先放进一个临时 dict
    tmp = {k: v.strip() for k, v in matches}

    # 4. 整理为目标结构
    result = {}
    for k in keys:
        raw = tmp.get(k, "")            
        # 对多行描述型字段保留换行，其余去掉多余空白
        if k in {"病案标识号","手术名称", "手术经过", "病程记录"}:
            raw = re.sub(r'\s+', ' ', raw)      # 合并连续空白
        result[k] = raw

    return result


def __extract_agent_result(full_content, label):
    '''
    从agent的完整响应中提取特定标签的结果
    '''
    full_content = full_content.replace("<think>\n\n</think>\n\n", "")
    
    try:
        if full_content.strip():
            content_data = json.loads(full_content)
            
            # 1) 原逻辑：优先按 label 精确取值（保持兼容）
            if label in content_data:
                return content_data[label]

            # 2) 兜底策略：label 不存在时，尝试返回“最可能的结果”
            # 2.1 优先返回第一个 list[str]
            for v in content_data.values():
                if isinstance(v, list) and all(isinstance(x, str) for x in v):
                    return v

            # 2.2 再退一步：返回第一个 list（不限制元素类型）
            for v in content_data.values():
                if isinstance(v, list):
                    return v
                
            # 2.3 最后：维持你原来的行为（返回 full_content）
            print(f"Warning: {label} not found in response data")
            return full_content
        else:
            print("Warning: full_content is empty")
            return ""
    except json.JSONDecodeError as e:
        print(f"JSON decode error in full_content: {e}, content: {full_content}")
        return full_content

def __search_icd(surgery_name):
    """
    对单个手术名称进行精确查询，返回所有匹配的 ICD 码和手术名称。
    """

    search_body = {
        "query": {
            "term": {
                "name.keyword": {  # 使用字段的 `.keyword` 后缀进行精确匹配
                    "value": surgery_name
                }
            }
        }
    }
    res = es.search(index="surgery_icd_tree", body=search_body)
    if res["hits"]["total"]["value"] == 0:
        return None
    else:
        # 返回所有匹配的手术信息
        matches = []
        for hit in res["hits"]["hits"]:
            surgery_doc = hit["_source"]
            # print(f"匹配手术: {disease_doc['name']}，ICD码: {disease_doc['icd_code']}")
            matches.append((surgery_doc["icd_code"]))
        return matches

def __remove_unmatched_surgery(full_content):
    """
    移除未匹配的手术名称
    """
    # print(f"原始手术列表: {full_content}")

    matched_surgery = []
    for diagnosis in full_content:
        if __search_icd(diagnosis) is not None:
            matched_surgery.append(diagnosis)
        else:
            print(f"移除无匹配手术: {diagnosis}")
    # print(f"匹配后的手术列表: {matched_surgery}")
    return matched_surgery

# def __reserve_unmatched_surgery(full_content):
#     """
#     保留未匹配的手术名称
#     """

#     matched_surgery = []
#     for diagnosis in full_content:
#         if __search_icd(diagnosis) is not None:
#             matched_surgery.append(diagnosis)
#         else:
#             matched_surgery.append(diagnosis)+{"icd_code": None}
#             print(f"保留无匹配手术: {diagnosis}")
#     # print(f"匹配后的手术列表: {matched_surgery}")
#     return matched_surgery



def __format_icd_display(icd):
    if not icd:
        return "无编码"
    if isinstance(icd, (list, tuple)):
        return ", ".join(str(code).strip() for code in icd if str(code).strip()) or "无编码"
    return str(icd).strip() or "无编码"

def __format_evidence(evidence):
    if evidence is None:
        return "-"
    if isinstance(evidence, dict):
        evidence = evidence.get("病历原文依据") or evidence.get("原文依据") or evidence.get("依据") or ""
    if isinstance(evidence, (list, tuple)):
        evidence = "；".join(str(item).strip() for item in evidence if str(item).strip())
    else:
        evidence = str(evidence).strip()
    if not evidence:
        return "-"
    return evidence.replace("|", "/").replace("\n", " ")

def __generate_markdown_table(num_content, fifth_full_content, corresponding_icd, all_result_list, icd_list, other_surgery_levels=None, evidence_map=None, other_coding_names=None):
    # 表头部分
    evidence_map = evidence_map or {}
    other_coding_names = set(other_coding_names or [])
    headers = ["病案标识号", "手术名称", "手术编码", "是否四级", "是否微创", "依据", "编码类型"]
    header_row = "| " + " | ".join(headers) + " |"
    # 分隔行
    separator_row = "| " + " | ".join(["----"] * len(headers)) + " |"
    # 表内容部分
    content_rows = []

    # 处理主诊断信息
    main_diagnosis_name = fifth_full_content or "未找到主手术"
    main_diagnosis_icd = __format_icd_display(corresponding_icd)

    if other_surgery_levels is None:
        other_surgery_levels = []

    # 提取主手术的四级/微创信息（位于列表末尾）
    main_surgery_level = other_surgery_levels[-1] if other_surgery_levels else {}
    main_is_level4 = main_surgery_level.get('is_level4', '-')
    main_is_minimally_invasive = main_surgery_level.get('is_minimally_invasive', '-')

    # 其它手术的四级/微创信息（不含末尾主手术）
    other_levels = other_surgery_levels[:-1] if other_surgery_levels else []

    # 第一行：主手术
    main_evidence = __format_evidence(evidence_map.get(main_diagnosis_name, ""))
    if main_diagnosis_icd not in ("", "无编码"):
        content_rows.append(f"| {num_content} | **{main_diagnosis_name}** | **{main_diagnosis_icd}** | {main_is_level4} | {main_is_minimally_invasive} | {main_evidence} | 主手术编码 |")

    # 后续行：其它手术 + 四级/微创信息
    if all_result_list and icd_list:
        for i in range(min(len(all_result_list), len(icd_list))):
            diagnosis_name = all_result_list[i] or "未知手术"
            diagnosis_icd = __format_icd_display(icd_list[i])
            if diagnosis_icd in ("", "无编码"):
                continue
            # 获取该手术的四级/微创信息
            if i < len(other_levels):
                is_level4 = other_levels[i].get('is_level4', '-')
                is_minimally_invasive = other_levels[i].get('is_minimally_invasive', '-')
            else:
                is_level4 = '-'
                is_minimally_invasive = '-'
            evidence = __format_evidence(evidence_map.get(diagnosis_name, ""))
            content_rows.append(f"| {num_content} | {diagnosis_name} | {diagnosis_icd} | {is_level4} | {is_minimally_invasive} | {evidence} | 其他手术编码 |")

    if not content_rows:
        return "本次未匹配到可输出的手术编码。"

    # 组合成完整的 Markdown 表格
    markdown_table = header_row + "\n" + separator_row + "\n" + "\n".join(content_rows)
    return markdown_table


import re

def __get_json(text: str) -> dict:
    """
    将病历字符串解析成结构化 JSON
    :param text: 原始病历字符串
    :return: dict，字段与题目要求保持一致
    """

    # 1. 预定义目标字段顺序（可按需要增删）
    keys = [
        "病案标识号", "手术名称", "手术经过", "病程记录"
    ]

    # 2. 构造正则：以“key：”开头，非贪婪匹配到下一个“key：”或字符串结尾
    pattern = r'(' + '|'.join(map(re.escape, keys)) + r')：\s*(.*?)(?=(?:' + \
              '|'.join(map(re.escape, keys)) + r')：|$)'
    matches = re.findall(pattern, text, flags=re.S)

    # 3. 先放进一个临时 dict
    tmp = {k: v.strip() for k, v in matches}

    # 4. 整理为目标结构
    result = {}
    for k in keys:
        raw = tmp.get(k, "")
        # 对多行描述型字段保留换行，其余去掉多余空白
        if k in {"病案标识号", "手术名称", "手术经过", "病程记录"}:
            raw = re.sub(r'\s+', ' ', raw)      # 合并连续空白
        result[k] = raw

    return result



def __standardize_with_fuzzy_match(surgery_list):
    """
    检查手术名称是否存在于ES库中。
    如果存在，保留原样；如果不存在，利用 ES 进行模糊匹配(fuzzy match)寻找最相似的标准名称代替。
    """
    if not surgery_list:
        return []

    standardized_list = []
    for surgery_name in surgery_list:
        # 1. 先调用现有的精确匹配函数，检查是否已经是库里的标准名称
        if __search_icd(surgery_name) is not None:
            standardized_list.append(surgery_name)
        else:
            # 2. 如果不是标准名称，去 ES 库进行模糊搜索
            fuzzy_body = {
                "query": {
                    "match": {
                        # 这里使用 'name' 字段进行全文模糊匹配，而不是精确匹配的 'name.keyword'
                        "name": { 
                            "query": surgery_name,
                            "fuzziness": "AUTO"  # 允许自动计算编辑距离来容错
                        }
                    }
                },
                "size": 1  # 我们只需要得分最高（最相似）的那一个结果
            }
            
            try:
                res = es.search(index="surgery_icd_tree", body=fuzzy_body)
                if res["hits"]["total"]["value"] > 0:
                    # 提取得分最高的结果
                    best_match_name = res["hits"]["hits"][0]["_source"]["name"]
                    print(f"模糊匹配触发: [{surgery_name}] 不标准，已替换为最相似标准词 -> [{best_match_name}]")
                    standardized_list.append(best_match_name)
                else:
                    # 如果模糊查询依然完全匹配不到任何东西（极其冷僻的词），保留原样，让后续流程输出"无编码"
                    print(f"模糊匹配未找到相似词，保留原样: [{surgery_name}]")
                    standardized_list.append(surgery_name)
            except Exception as e:
                print(f"模糊匹配时发生 ES 查询错误: {e}")
                standardized_list.append(surgery_name) # 报错也保留原样防止数据丢失

    # 3. 去重并保持顺序（因为模糊匹配可能会把不同的非标准词映射到同一个标准词上）
    result = []
    for item in standardized_list:
        if item not in result:
            result.append(item)
            
    return result
