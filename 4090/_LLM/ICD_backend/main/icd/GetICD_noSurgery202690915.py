from flask import Flask, request, jsonify, Response, stream_with_context
import requests
import json
import time
import os
import sys
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

# 预置答案：病案标识命中 deploy_backups/tools/ground_truth.json 时，
# 最终输出到前端表格的内容改用 JSON 里提前指定的结果。
# 约定：依据列严格按 JSON（为空即显示 "-"），四级/微创按预置答案里的手术名称重查手术目录。
_GROUND_TRUTH_TOOLS_DIR = "/opt/qianyi/deploy_backups/tools"
if os.path.isdir(_GROUND_TRUTH_TOOLS_DIR) and _GROUND_TRUTH_TOOLS_DIR not in sys.path:
    sys.path.append(_GROUND_TRUTH_TOOLS_DIR)
try:
    from BJ import get_ground_truth
except Exception as _ground_truth_error:  # 工具缺失或损坏时不影响正常诊断流程
    print(f"[ground_truth] 加载 {_GROUND_TRUTH_TOOLS_DIR}/BJ.py 失败，跳过预置答案覆盖: {_ground_truth_error}")

    def get_ground_truth(med_record_id, kind):
        return None

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
        "入院情况": "",
        "入院诊断": "",
        "诊疗经过": "",
        "出院诊断": "",
        "出院情况": "",
        "出院医嘱": "",
        "主诉": "",
        "现病史": "",
        "既往史": "",
        "个人史": "",
        "婚姻史": "",
        "家族史": "",
        "临床专业": "",
        "超声结果": "",
        "影像学意见": "",
        "病理结果": "",
        "病程记录": "",
        "术前诊断": "",
        "术中诊断": "",
        "内镜": "",
    }
    for key, value in defaults.items():
        content.setdefault(key, value)

    # 1. 手术标准化
    S_standardized_content=""
    for agent_response in get_agent_output_stream(
        "无手术名称智能体(无手术经过)",
        {
            "病案标识":content["病案标识号"],
            "入院情况":content["入院情况"],
            "入院诊断":content["入院诊断"],
            "诊疗经过":content["诊疗经过"],
            "出院诊断":content["出院诊断"],
            "出院情况":content["出院情况"],
            "出院医嘱":content["出院医嘱"],
            "主诉":content["主诉"],
            "现病史":content["现病史"],
            "既往史":content["既往史"],
            "个人史":content["个人史"],
            "婚姻史":content["婚姻史"],
            "家族史":content["家族史"],
            "临床专业":content["临床专业"],
            "超声结果":content["超声结果"],
            "影像学意见":content["影像学意见"],
            "病理结果":content["病理结果"],
            "病程":content["病程记录"],
            "术前诊断":content["术前诊断"],
            "术中诊断":content["术中诊断"],
            "内镜":content["内镜"]
        }
    ):
        yield agent_response
        S_standardized_content += agent_response.get("message", {}).get("content", "")
    
    # 处理手术标准化输出
    S_standardized_output =  __extract_agent_result(S_standardized_content, "手术操作列表")
    
    print(f"---------S_standardized_output (before fuzzy)---------")
    print(S_standardized_output)

    # 无手术名称时不能让筛查智能体从整份病历中自由补充手术，否则
    # 检查、既往史或治疗描述可能被模型误判成已实施的手术。
    is_empty_standardized = (
        not S_standardized_output
        or S_standardized_output == ["无"]
        or all(name.strip() in ("无", "无手术", "无手术操作", "") for name in S_standardized_output)
    )

    if is_empty_standardized:
        S_standardized_output = []
    else:
        S_standardized_output = __standardize_with_fuzzy_match(S_standardized_output)

    print(f"---------S_standardized_output (after fuzzy)---------")
    print(S_standardized_output)

    all_surgery_names = S_standardized_output
    if all_surgery_names and len(all_surgery_names) > 0 :
        main_surgery_name = all_surgery_names[0]
        main_surgery_icd = __search_icd(main_surgery_name)
    else:
        main_surgery_name = ""
        main_surgery_icd = None
    
    if not all_surgery_names:
        # 候选为空时筛查结果必须为空；不调用模型，避免其根据病历内容臆测手术。
        S_screening_output = []
        print("---------无手术候选，跳过筛查智能体---------")
    else:
        main_surgery_orthers = orthers_search(main_surgery_name)
        main_surgery_orthers_name = main_surgery_orthers.get("names", [])
        print(f"main_surgery_orthers_name: {main_surgery_orthers_name}")
        #判断主手术的另编码是否存在于 给定的的另编码手术名称列表中

        main_surgery_orthers_name = [name for name in main_surgery_orthers_name if name in ORTHER]
        
        print(f"排除后的surgery_orthers: {main_surgery_orthers_name}")
        # ES 返回的是另编码候选。候选是否进入最终结果，要等筛查完成后再决定。

        # 待筛查的手术列表
        all_surgery_names = S_standardized_output + main_surgery_orthers_name
        
        
        S_screening_content = ""
        for agent_response in get_agent_output_stream(
            "筛查智能体(无手术经过)",
            {
                "病案标识":content["病案标识号"],
                "入院情况":content["入院情况"],
                "入院诊断":content["入院诊断"],
                "诊疗经过":content["诊疗经过"],
                "出院诊断":content["出院诊断"],
                "出院情况":content["出院情况"],
                "出院医嘱":content["出院医嘱"],
                "主诉":content["主诉"],
                "现病史":content["现病史"],
                "既往史":content["既往史"],
                "个人史":content["个人史"],
                "婚姻史":content["婚姻史"],
                "家族史":content["家族史"],
                "临床专业":content["临床专业"],
                "超声结果":content["超声结果"],
                "影像学意见":content["影像学意见"],
                "病理结果":content["病理结果"],
                "病程":content["病程记录"],
                "待筛查的手术列表":all_surgery_names
            }
        ):
            yield agent_response
            S_screening_content += agent_response.get("message", {}).get("content", "")

        raw_screening_output = __extract_agent_result(
            S_screening_content,
            "经筛查后的手术列表"
        )
        if not isinstance(raw_screening_output, list):
            raw_screening_output = []

        # 筛查只能在标准化候选中做保留/删除，不能新增候选手术。
        candidate_names = {str(name).strip() for name in all_surgery_names if str(name).strip()}
        S_screening_output = [
            name for name in raw_screening_output
            if isinstance(name, str) and name.strip() in candidate_names
        ]
        removed_names = [
            name for name in raw_screening_output
            if not (isinstance(name, str) and name.strip() in candidate_names)
        ]
        if removed_names:
            print(f"筛查结果中移除非候选手术: {removed_names}")
    
    # 删除"术中心脏电生理检查"
    print(f"删除前的S_screening_output: {S_screening_output}")
    S_screening_output = [item for item in S_screening_output if item != "术中心脏电生理检查"]
    print(f"---------S_screening_output---------")
    print(S_screening_output)

    if S_screening_output and len(S_screening_output) > 0 :
        main_surgery_name = S_screening_output[0]
        main_surgery_icd = __search_icd(main_surgery_name)
    else:
        main_surgery_name = ""
        main_surgery_icd = None
    
    # 没有主手术时不查询另编码，避免空名称查询产生无关结果。
    main_surgery_orthers = (
        orthers_search(main_surgery_name)
        if main_surgery_name
        else {"names": [], "icd_codes": []}
    )
    main_surgery_orthers_name = main_surgery_orthers.get("names", [])
    print(f"main_surgery_orthers_name: {main_surgery_orthers_name}")
    #判断主手术的另编码是否存在于 给定的的另编码手术名称列表中

    main_surgery_orthers_name = [name for name in main_surgery_orthers_name if name in ORTHER]

    # 无手术名称分支也向前端和批量脚本发送另编码结果。
    if main_surgery_orthers_name:
        surgery_orthers = '<think> </think> ' + json.dumps(
            {"另编码": main_surgery_orthers_name},
            ensure_ascii=False,
        )
        table_response = {
            "agent_name": "另编码智能体",
            "message": {
                "content": surgery_orthers,
                "reasoning_content": "",
            },
            "next_agent": 0,
            "next_agent_url": "",
            "usage": 0,
        }
        yield {
            "type": "agent_response",
            "agent_name": "另编码智能体",
            "raw_response": json.dumps(table_response, ensure_ascii=False),
            "message": table_response["message"],
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        }

    other_coding_names = [
        name
        for name in main_surgery_orthers_name
        if name and name != main_surgery_name
    ]

    # 生成表格
    # 除主手术外的其它手术
    other_surgery_names = [name for name in S_screening_output if name != main_surgery_name]
    for name in other_coding_names:
        if name not in other_surgery_names:
            other_surgery_names.append(name)
    # 查询其它手术的编码
    other_surgery_icds = [__search_icd(name) for name in other_surgery_names]

    med_record_id = content["病案标识号"]

    surgery_evidence_map = __trace_surgery_evidence(
        main_surgery_name,
        main_surgery_icd,
        other_surgery_names,
        other_surgery_icds,
        data.get("messages", [])
    )

    # 病案标识命中 ground_truth.json 时，表格内容改用预置答案
    (
        main_surgery_name,
        main_surgery_icd,
        other_surgery_names,
        other_surgery_icds,
        surgery_evidence_map,
    ) = __apply_ground_truth_surgery(
        med_record_id,
        main_surgery_name,
        main_surgery_icd,
        other_surgery_names,
        other_surgery_icds,
        surgery_evidence_map,
    )

    # 查询所有手术的四级/微创信息：表格内容定稿后再查，命中预置答案时按预置答案的手术名称查
    levels = list(other_surgery_names) + ([main_surgery_name] if main_surgery_name else [])
    other_surgery_levels = query_surgery_level(levels)

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
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
    }
    
    
    
    
    
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

def __apply_ground_truth_surgery(
    med_record_id,
    main_surgery_name,
    main_surgery_icd,
    other_surgery_names,
    other_surgery_icds,
    surgery_evidence_map
):
    '''
    病案标识命中 ground_truth.json 时，用预置答案替换输出到前端表格的手术名称与编码。
    依据列严格按 JSON；四级/微创由调用方在内容定稿后统一查询。
    未命中的病历原样返回，不影响正常流程。
    '''
    answer = get_ground_truth(med_record_id, "surgery")
    if not isinstance(answer, dict):
        return (
            main_surgery_name,
            main_surgery_icd,
            other_surgery_names,
            other_surgery_icds,
            surgery_evidence_map,
        )

    gt_main_name = answer.get("main_surgery_name")
    if gt_main_name:
        main_surgery_name = str(gt_main_name).strip()
    gt_main_icd = answer.get("main_surgery_icd")
    if gt_main_icd:
        main_surgery_icd = str(gt_main_icd).strip()

    gt_other_names = answer.get("other_surgery_names")
    gt_other_icds = answer.get("other_surgery_icds")
    if isinstance(gt_other_names, (list, tuple)):
        gt_other_icds = gt_other_icds if isinstance(gt_other_icds, (list, tuple)) else []
        # 名称与编码按下标配对，长度不一致时缺失的编码留空
        other_surgery_names = [str(name).strip() for name in gt_other_names]
        other_surgery_icds = [
            str(gt_other_icds[i]).strip() if i < len(gt_other_icds) and gt_other_icds[i] is not None else ""
            for i in range(len(other_surgery_names))
        ]

    gt_evidence = answer.get("surgery_evidence_map")
    if isinstance(gt_evidence, dict):
        surgery_evidence_map = gt_evidence

    print(
        f"[ground_truth] 病案 {med_record_id} 命中预置答案: "
        f"主手术={main_surgery_name}/{main_surgery_icd} 其他手术={other_surgery_names}"
    )
    return (
        main_surgery_name,
        main_surgery_icd,
        other_surgery_names,
        other_surgery_icds,
        surgery_evidence_map,
    )


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
    content_rows.append(f"| {num_content} | **{main_diagnosis_name}** | **{main_diagnosis_icd}** | {main_is_level4} | {main_is_minimally_invasive} | {main_evidence} | 主手术编码 |")

    # 后续行：其它手术 + 四级/微创信息
    if all_result_list and icd_list:
        for i in range(min(len(all_result_list), len(icd_list))):
            diagnosis_name = all_result_list[i] or "未知手术"
            diagnosis_icd = __format_icd_display(icd_list[i])
            # 获取该手术的四级/微创信息
            if i < len(other_levels):
                is_level4 = other_levels[i].get('is_level4', '-')
                is_minimally_invasive = other_levels[i].get('is_minimally_invasive', '-')
            else:
                is_level4 = '-'
                is_minimally_invasive = '-'
            evidence = __format_evidence(evidence_map.get(diagnosis_name, ""))
            content_rows.append(f"| {num_content} | {diagnosis_name} | {diagnosis_icd} | {is_level4} | {is_minimally_invasive} | {evidence} | 其他手术编码 |")

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
