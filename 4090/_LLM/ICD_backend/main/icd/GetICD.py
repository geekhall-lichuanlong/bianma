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
from tools.orthers_search import orthers_search
from tools.additional_coding import (collect_additional_candidates, coding_rules_for,
                                     candidate_event, canonical_screened_names, append_fixed_additional_coding, SCREENING_TASK)
from tools.save_excel import save_surgery
from tools.微创 import query_surgery_level
from tools.surgery_traceability import trace_surgery_evidence

es = Elasticsearch(
    "https://127.0.0.1:9200/",
    ca_certs="/opt/qianyi/3090/database/elasticsearch-9.2.3/config/certs/http_ca.crt",        # 证书绝对路径
    http_auth=('elastic', os.environ.get("ELASTIC_PASSWORD", "")),  # 用户名和密码
    verify_certs=False,  # 禁用证书验证
    ssl_show_warn=False  # 不显示SSL警告
)


def get_icd(data):
    '''
    处理前端数据并送给各个agent，得到手术ICD编码（流式版本）
    '''
    for result in get_icd_stream(data):
            yield json.dumps(result, ensure_ascii=False) + "\n"

def get_icd_stream(data):
    '''
    处理前端数据并送给各个agent，得到手术ICD编码（流式版本）
    '''
    messages = data.get("messages") if isinstance(data, dict) else None
    if not isinstance(messages, list) or not messages or not isinstance(messages[0], dict):
        raise ValueError("Invalid request format: messages[0].content is required")
    content_raw = messages[0].get("content", "")

    if isinstance(content_raw, dict):
        content = content_raw
    else:
        content = json.loads(content_raw or "{}")
    if not isinstance(content, dict):
        raise ValueError("Invalid request format: message content must be a JSON object")

    if "data" in content.keys():
        content = __get_json(content['data'])
        if not isinstance(content, dict):
            raise ValueError("Invalid request format: data must be a JSON object")
    if "住院号" in content.keys():
        content['病案标识号'] = content["住院号"]

    defaults = {
        "病案标识号": "",
        "手术名称": "",
        "手术经过": "",
        "病程记录": "",
    }
    for key, value in defaults.items():
        content.setdefault(key, value)

    # 1. 手术标准化
    S_standardized_content=""
    for agent_response in get_agent_output_stream(
        "手术标准化智能体",
        {
            "病案标识号": content["病案标识号"],
            "手术名称": content["手术名称"],
            "手术经过": content["手术经过"],
            "病程记录": content["病程记录"],
            # "病案标识": content["病案标识"],
            # "手术名称": content["手术名称"],
            # "手术经过": content["手术经过"],
            # "病程": content["病程"],
        }
    ):
        yield agent_response
        S_standardized_content += agent_response.get("message", {}).get("content", "")
    
    # 处理手术标准化输出
    S_standardized_output =  __extract_agent_result(S_standardized_content, "手术名称标准化")
    
    S_standardized_output = __standardize_with_fuzzy_match(S_standardized_output)
    
    print(f"---------S_standardized_output---------")
    print(S_standardized_output)
    
    # 2. 提取额外手术智能体
    
    S_additiona_content = ""
    for agent_response in get_agent_output_stream(
        "提取额外手术智能体",
        {
            "病案标识号": content["病案标识号"],
            "手术名称": content["手术名称"],
            "手术经过": content["手术经过"],
            "病程记录": content["病程记录"],
            # "病案标识": content["病案标识"],
            # "手术名称": content["手术名称"],
            # "手术经过": content["手术经过"],
            # "病程": content["病程"],
        }
    ):
        yield agent_response
        S_additiona_content += agent_response.get("message", {}).get("content", "")
    # 处理额外手术标准化输出
    S_additiona_output =  __extract_agent_result(S_additiona_content, "挖掘额外手术")
    
    S_additiona_output =  __remove_unmatched_surgery(S_additiona_output)
    
    for item in S_additiona_output:
        if item in S_standardized_output:
            med_record_id = content["病案标识号"]
            a = [name for name in S_additiona_output if name not in S_standardized_output]
            with open("/opt/qianyi/4090/_LLM/ICD_backend/save/重复.txt", "a", encoding="utf-8") as f:
                f.write(f"病案标识号：{med_record_id} 标准化手术：{S_standardized_output} 挖掘手术{S_additiona_output} 去重之后的手术{a}\n")
            
            print(f"找到重复记录: {med_record_id}")
            break  # 找到一个匹配就退出，避免重复写入同一病案

        
    S_additiona_output = [name for name in S_additiona_output if name not in S_standardized_output]
    
    print(f"---------S_additiona_output---------")
    print(S_additiona_output)
    
    # # 3. 另编码agent
    # S_another_coding_content = ""
    
    # for agent_response in get_agent_output_stream(
    #     "另编码智能体",
    #     {
    #         "病案标识号": content["病案标识号"],
    #         "手术名称": content["手术名称"],
    #         "手术经过": content["手术经过"],
    #         "病程记录": content["病程记录"],
    #     }
    # ):
    #     yield agent_response
    #     S_another_coding_content += agent_response.get("message", {}).get("content", "")
    # # 处理另编码标准化输出
    # S_another_coding_output =  __extract_agent_result(S_another_coding_content, "处理另编码")
    # S_another_coding_output = __remove_unmatched_surgery(S_another_coding_output)
    
    # print(f"---------S_another_coding_output---------")
    # print(S_another_coding_output)
    
    # 4. 排序智能体 
    S_sorting_content = ""
    
    for agent_response in get_agent_output_stream(
        "排序智能体",
        {
            "病案标识号": content["病案标识号"],
            "手术名称": content["手术名称"],
            "手术经过": content["手术经过"],
            "病程记录": content["病程记录"],
            # "病案标识": content["病案标识"],
            # "手术名称": content["手术名称"],
            # "手术经过": content["手术经过"],
            # "病程": content["病程"],
            "待排序的手术列表":S_standardized_output + S_additiona_output
        }
    ):
        yield agent_response
        S_sorting_content += agent_response.get("message", {}).get("content", "")
    # 处理另编码标准化输出
    
    print(f" ---------------------------------- S_sorting_content: {S_sorting_content}")
    S_sorting_output =  __extract_agent_result(S_sorting_content, "排序后的手术列表")
    S_sorting_output =  __remove_unmatched_surgery(S_sorting_output)
    
    print(f"---------S_sorting_output---------")
    print(S_sorting_output)
    
    
    if S_sorting_output and len(S_sorting_output) > 0 :
        main_surgery_name = S_sorting_output[0]
        main_surgery_icd = __search_icd(main_surgery_name)
    else:
        main_surgery_name = ""
        main_surgery_icd = None
    
    
    # 查询主手术的编码
    main_surgery_orthers = yield from timed_call(
        '另编码智能体', collect_additional_candidates,
        [main_surgery_name] if main_surgery_name else [], lookup=orthers_search)
    # Every mapped name enters screening. No whitelist or pre-screen model.
    main_surgery_orthers_name = main_surgery_orthers['names']
    coding_rules = coding_rules_for([main_surgery_name] if main_surgery_name else [], __search_icd)
    yield candidate_event('另编码智能体', main_surgery_orthers_name)

    # med_record_id = content["病案标识号"]
    # if main_surgery_icd is not None and len(main_surgery_icd) > 0:
    #     save_surgery(med_record_id,S_standardized_output,S_sorting_output,)
    
    # 待筛查的手术列表
    all_surgery_names = list(dict.fromkeys(S_sorting_output + main_surgery_orthers_name))
    S_screening_content = ""
    # 筛查智能体
    for agent_response in get_agent_output_stream(
        "筛查智能体",
        {
            "病案标识号": content["病案标识号"],
            "手术名称": content["手术名称"],
            "手术经过": content["手术经过"],
            "病程记录": content["病程记录"],
            # "病案标识": content["病案标识"],
            # "手术名称": content["手术名称"],
            # "手术经过": content["手术经过"],
            # "病程": content["病程"],
            "待筛查的手术列表": all_surgery_names,
        }
    ):
        S_screening_content += agent_response.get("message", {}).get("content", "")
    # print(f"S_sorting_content: {S_sorting_content}")
    
    S_screening_output =  __extract_agent_result(S_screening_content, "经筛查后的手术列表")
    S_screening_output = canonical_screened_names(S_screening_output, all_surgery_names)
    
    # 筛查结果不再按候选名单或固定名称删除；编码查询另行处理。
    print(f"---------S_screening_output---------")
    print(S_screening_output)
    # S_screening_output = all_surgery_names

    
    
    other_coding_names, other_surgery_names, final_surgery_names = __build_final_surgery_names(
        main_surgery_name,
        S_screening_output,
        main_surgery_orthers_name,
    )
    print(f"最终手术列表: {final_surgery_names}")
    print(f"最终另编码: {other_coding_names}")

    final_list_content = '<think> </think> ' + json.dumps(
        {"经筛查后的手术列表": final_surgery_names}, ensure_ascii=False
    )
    final_list_response = {
        "agent_name": "筛查智能体",
        "message": {
            "content": final_list_content,
            "reasoning_content": "",
        },
        "next_agent": 0,
        "next_agent_url": "",
        "usage": 0,
    }
    yield {
        "type": "agent_response",
        "agent_name": "筛查智能体",
        "raw_response": json.dumps(final_list_response, ensure_ascii=False),
        "message": final_list_response["message"],
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
    }

    # 查询其它手术的编码
    other_surgery_icds = [__search_icd(name) for name in other_surgery_names]

    # 查询所有手术的四级/微创信息
    levels = other_surgery_names + ([main_surgery_name] if main_surgery_name else [])
    other_surgery_levels = query_surgery_level(levels)

    med_record_id = content["病案标识号"]
    if main_surgery_icd is not None and len(main_surgery_icd) > 0:
        save_surgery(med_record_id,S_standardized_output,S_additiona_output,other_coding_names,S_sorting_output,final_surgery_names,main_surgery_name,main_surgery_icd,other_surgery_names,other_surgery_icds)



    surgery_evidence_map = yield from timed_call("手术溯源", __trace_surgery_evidence,
        main_surgery_name,
        main_surgery_icd,
        other_surgery_names,
        other_surgery_icds,
        data.get("messages", [])
    )

    markdown_table = __generate_markdown_table(
        med_record_id,
        main_surgery_name,
        main_surgery_icd,
        other_surgery_names,
        other_surgery_icds,
        other_surgery_levels,
        surgery_evidence_map,
        other_coding_names,
    )
    
        # 将表格作为智能体响应发送到前端
    table_response = {
        "agent_name": "表格展示",
        "message": {
            "content": markdown_table,
            "reasoning_content": "",
            "模型溯源": surgery_evidence_map,
        },
        "next_agent": 0,
        "next_agent_url": "",
        "usage": 0
    }

    yield {
        "type": "agent_response",
        "agent_name": "表格展示",
        "raw_response": json.dumps(table_response, ensure_ascii=False),
        "message": table_response["message"],
        "模型溯源": surgery_evidence_map,
        "pipeline_audit": {
            "另编码候选": main_surgery_orthers_name,
            "另编码关联": main_surgery_orthers['relations'],
            "送筛候选": all_surgery_names,
            "最终手术列表": final_surgery_names,
            "最终另编码": other_coding_names,
        },
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
    }
    
    
    
    
    
def __build_final_surgery_names(main_surgery_name, screening_names, another_coding_candidates):
    """根据筛查结果和 ES 另编码候选构造唯一的最终手术列表。"""
    screening_names = screening_names if isinstance(screening_names, list) else []

    candidates = []
    for name in another_coding_candidates or []:
        if name and name != main_surgery_name and name not in candidates:
            candidates.append(name)

    # Screening is authoritative even when exactly one mapped candidate exists.
    selected_another_coding = list(dict.fromkeys(
        name for name in screening_names if name in candidates))

    other_surgery_names = []
    for name in screening_names:
        if not name or name == main_surgery_name or name in other_surgery_names:
            continue
        # 筛查未保留的另编码候选不能重新加入最终列表。
        if name in candidates and name not in selected_another_coding:
            continue
        other_surgery_names.append(name)

    for name in selected_another_coding:
        if name not in other_surgery_names:
            other_surgery_names.append(name)

    final_surgery_names = ([main_surgery_name] if main_surgery_name else []) + other_surgery_names
    final_surgery_names, fixed_coding = append_fixed_additional_coding(main_surgery_name, final_surgery_names)
    other_surgery_names = final_surgery_names[1:] if main_surgery_name else final_surgery_names
    selected_another_coding = [name for name in final_surgery_names
                              if name in selected_another_coding or name in fixed_coding]
    return selected_another_coding, other_surgery_names, final_surgery_names


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
    evidence_map = trace_surgery_evidence(trace_names, messages, code_map=code_map)
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
    # full_content = full_content.replace("<think>\n\n</think>\n\n", "")
    
    print(f"原始 full_content: {full_content}")
    full_content = re.sub(r"</?think>", "", full_content, flags=re.I).strip()
    print(f"清洗 think 标签后的 full_content: {full_content}")
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

# def __extract_agent_result(full_content, label):
#     """
#     从 agent 的完整响应中提取结果
#     兼容:
#     1. 前后带 <think> / </think>
#     2. 前面多余的 </think>
#     3. label 名字不完全一致
#     """
#     if not full_content or not str(full_content).strip():
#         print("Warning: full_content is empty")
#         return []

#     text = str(full_content).strip()

#     # 1) 去掉所有 think 标签，不管前后有几个
#     text = re.sub(r"</?think>", "", text, flags=re.I).strip()

#     # 2) 截取 JSON 主体：从第一个 { 开始，到最后一个 } 结束
#     start = text.find("{")
#     end = text.rfind("}")
#     if start != -1 and end != -1 and start < end:
#         text = text[start:end + 1].strip()

#     try:
#         content_data = json.loads(text)

#         # 优先按 label 取
#         if isinstance(content_data, dict):
#             if label in content_data:
#                 return content_data[label]

#             # 常见别名兼容
#             alias_map = {
#                 "排序后的列表": ["排序后的手术列表"],
#                 "排序后的手术列表": ["排序后的列表"],
#             }
#             for alias in alias_map.get(label, []):
#                 if alias in content_data:
#                     return content_data[alias]

#             # 兜底：返回第一个 list[str]
#             for v in content_data.values():
#                 if isinstance(v, list) and all(isinstance(x, str) for x in v):
#                     return v

#             # 再兜底：返回第一个 list
#             for v in content_data.values():
#                 if isinstance(v, list):
#                     return v

#             print(f"Warning: {label} not found in response data")
#             return []

#         elif isinstance(content_data, list):
#             return content_data

#         return []

#     except json.JSONDecodeError as e:
#         print(f"JSON decode error in full_content: {e}, cleaned content: {text}")
#         return []


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

def __generate_markdown_table(num_content, fifth_full_content, corresponding_icd, all_result_list, icd_list, other_surgery_levels=None, evidence_map=None,other_coding_names=None):
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
    main_diagnosis_name = fifth_full_content or "未找到主诊断"
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
            diagnosis_name = all_result_list[i] or "未知诊断"
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





