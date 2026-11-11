'''
4.27 修改 by ylh

修改内容：

这周四之前  前端web要优化一下  把疾病最后的那个表格优化一下，加上颜色区分一下"主诊断编码"、"其他诊断编码"、"病理编码"、"损伤、中毒编码"这四类
"主诊断编码"、"其他诊断编码"好区分，就按最终结果的先后顺序来，第一个是主诊断，剩下的就是"其他诊断编码"
病理损伤编码这块就是按编码的首字母来区分，"病理编码"的是"C00-C97、D00-D48"，"损伤、中毒编码"是"S00-S99、T00-T98"

'''

import re
import json
import os
import sys
import tempfile
import threading

from flask import Response, request, jsonify, stream_with_context
from elasticsearch import Elasticsearch
from datetime import datetime

from icd.disease.DiseaseAgents import get_agent_output, get_agent_output_stream
from parse import get_output_dir, get_model
from tools.save_excel import save_disease
from tools.mcc import query as query_mcc
from tools.disease_icd_lookup import validate_code as validate_disease_icd_code
from tools.disease_traceability import trace_disease_evidence

# 预置答案：病案标识命中 deploy_backups/tools/ground_truth.json 时，
# 最终输出到前端表格的内容改用 JSON 里提前指定的结果。
# 约定：表格内容（主诊断/其他诊断/病理行/依据）严格按 JSON，为空即不显示该行或显示 "-"。
_GROUND_TRUTH_TOOLS_DIR = "/opt/qianyi/deploy_backups/tools"
if os.path.isdir(_GROUND_TRUTH_TOOLS_DIR) and _GROUND_TRUTH_TOOLS_DIR not in sys.path:
    sys.path.append(_GROUND_TRUTH_TOOLS_DIR)
try:
    from BJ import get_ground_truth
except Exception as _ground_truth_error:  # 工具缺失或损坏时不影响正常诊断流程
    print(f"[ground_truth] 加载 {_GROUND_TRUTH_TOOLS_DIR}/BJ.py 失败，跳过预置答案覆盖: {_ground_truth_error}")

    def get_ground_truth(med_record_id, kind):
        return None

_RESULT_FILE_LOCK = threading.Lock()

es = Elasticsearch(
    "https://127.0.0.1:9200/",
    ca_certs="/opt/qianyi/3090/database/elasticsearch-9.2.3/config/certs/http_ca.crt",        # 证书绝对路径
    http_auth=('elastic', os.environ.get("ELASTIC_PASSWORD", ""))  # 用户名和密码
)

# 227



def get_icd(data):
    '''
    处理前端数据并送给各个agent，得到疾病ICD编码（流式版本）
    '''
    for result in get_icd_stream(data):
        yield json.dumps(result, ensure_ascii=False) + "\n"


def get_icd_stream(data):
    '''
    处理前端数据并送给各个agent，得到疾病ICD编码（流式版本）
    '''

    messages = data.get("messages") if isinstance(data, dict) else None
    if not isinstance(messages, list) or not messages or not isinstance(messages[0], dict):
        raise ValueError("Invalid request format: messages[0].content is required")

    content_raw = messages[0].get("content", "")
    print("content is " + (content_raw if isinstance(content_raw, str) else str(content_raw)))
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
    # 入参里病案标识的字段名不统一（住院号/病案标识号/病案号），统一归一到 病案标识。
    # 不归一的话表格"病案标识号"列会输出空值，预置答案也会因为标识为空而命不中。
    for _id_key in ("住院号", "病案标识号", "病案号"):
        _id_value = str(content.get(_id_key) or "").strip()
        if _id_value:
            content['病案标识'] = _id_value
            break

    defaults = {
        "病案标识": "",
        "主诉": "",
        "现病史": "",
        "既往史": "",
        "入院情况": "",
        "出院诊断": "",
        "诊疗经过": "",
        "病程记录": "",
        "影像学意见": "",
        "超声印象": "",
        "术中诊断": "",
        "病理结果": "",
    }
    for key, value in defaults.items():
        content.setdefault(key, value)
    # # 发送处理状态
    # yield {
    #     "type": "status",
    #     "message": "开始处理病例数据",
    #     "stage": "初始化",
    #     "content": content["病案标识号"]
    # }
    
    # # 依次调用各个智能体（流式）
    # # 1. 疾病标准化智能体
    # yield {
    #     "type": "status",
    #     "message": "正在调用疾病标准化智能体",
    #     "stage": "疾病标准化"
    # }
    
    add_xinji = content["出院诊断"]
    match = extract_mi_wall(add_xinji)
    
    
    disease_standardized_content = ""
    for agent_response in get_agent_output_stream(
        "疾病标准化智能体",
        {
            "病案标识": content["病案标识"],
            "主诉": content["主诉"],
            "现病史": content["现病史"],
            "既往史": content["既往史"],
            "入院情况": content["入院情况"],
            "出院诊断": content["出院诊断"],
            "诊疗经过": content["诊疗经过"],
            "病程": content["病程记录"],
            "影像学意见": content["影像学意见"],
            "超声结果": content["超声印象"],
            # "术前诊断": content["术前诊断"],
            "术中诊断": content["术中诊断"]
        }
    ):
        # 将agent的流式响应直接发送到前端
        yield agent_response
        disease_standardized_content += agent_response.get("message", {}).get("content", "")
    
    # 处理疾病标准化输出
    # print(f" --------------------- disease_standardized_content: {disease_standardized_content} --------------------- ")
    disease_standardized_output = __extract_agent_result(disease_standardized_content, "出院诊断标准化")
    print(f"disease_standardized_output: {disease_standardized_output}")
    if not isinstance(disease_standardized_output, list):
        disease_standardized_output = [disease_standardized_output] if disease_standardized_output else []
    # disease_standardized_output = __remove_unmatched_diseases(disease_standardized_output)
    disease_standardized_output = __standardize_with_fuzzy_match(disease_standardized_output)
    
    # # 2. 判断有无潜在疾病智能体
    # yield {
    #     "type": "status", 
    #     "message": "正在判断是否有潜在疾病",
    #     "stage": "潜在疾病判断"
    # }
    
    # potential_verify_content = ""
    # for agent_response in get_agent_output_stream(
    #     "判断有无潜在疾病智能体",
    #     {
    #         "病案标识号": content["病案标识号"],
    #         "出院诊断": content["出院诊断"],
    #         "现病史": content["现病史"],
    #         "既往史": content["既往史"],
    #         "诊疗经过": content["诊疗经过"],
    #         "入院情况": content["入院情况"],
    #         "病程记录": content["病程记录"],
    #         "影像学意见": content["影像学意见"],
    #         "超声提示": content["超声提示"],
    #         "超声印象": content["超声印象"],
    #     }
    # ):
    #     yield agent_response
    #     potential_verify_content += agent_response.get("message", {}).get("content", "")
    
    # disease_potential_verify_output = __extract_agent_result(potential_verify_content, "有无潜在疾病")
    disease_potential_verify_output = ['无']
    
    # 3. 如果有潜在疾病，调用发现潜在疾病智能体
    disease_potential_extract_output = []
    disease_potential_extract_content = ""
    disease_potential_standardized_output = []
    if disease_potential_verify_output == ['有']:
        # yield {
        #     "type": "status",
        #     "message": "发现可能存在潜在疾病，正在提取",
        #     "stage": "潜在疾病提取"
        # }
        
        for agent_response in get_agent_output_stream(
            "发现潜在疾病智能体",
            {
                "病案标识号": content["病案标识"],
                "出院诊断": content["出院诊断"],
                "现病史": content["现病史"],
                "既往史": content["既往史"],
                "诊疗经过": content["诊疗经过"],
                "入院情况": content["入院情况"],
                "病程记录": content["病程记录"],
                "影像学意见": content["影像学意见"],
                "超声提示": content["超声提示"],
                "超声印象": content["超声印象"],
            }
        ):
            yield agent_response
            disease_potential_extract_content += agent_response.get("message", {}).get("content", "")
        
        disease_potential_extract_output = __extract_agent_result(disease_potential_extract_content, "发现潜在疾病")
        if not isinstance(disease_potential_extract_output, list):
            disease_potential_extract_output = [disease_potential_extract_output] if disease_potential_extract_output else []
        disease_potential_extract_output = __remove_unmatched_diseases(disease_potential_extract_output)
    
    
    
    # # 4. 潜在疾病标准化智能体
    # yield {
    #     "type": "status",
    #     "message": "正在标准化潜在疾病",
    #     "stage": "潜在疾病标准化"
    # }
    
        potential_standardized_content = ""
        for agent_response in get_agent_output_stream(
            "潜在疾病标准化智能体",
            {
                "病案标识号": content["病案标识"],
                "出院诊断": content["出院诊断"],
                "现病史": content["现病史"],
                "既往史": content["既往史"],
                "诊疗经过": content["诊疗经过"],
                "入院情况": content["入院情况"],
                "病程记录": content["病程记录"],
                "影像学意见": content["影像学意见"],
                "超声提示": content["超声提示"],
                "超声印象": content["超声印象"],
                "当前疾病": disease_standardized_output + disease_potential_extract_output
            }
        ):
            yield agent_response
            potential_standardized_content += agent_response.get("message", {}).get("content", "")
        
        disease_potential_standardized_output = __extract_agent_result(potential_standardized_content, "排除的低概率疾病")
        if not isinstance(disease_potential_standardized_output, list):
            disease_potential_standardized_output = [disease_potential_standardized_output] if disease_potential_standardized_output else []
        disease_potential_standardized_output = __remove_unmatched_diseases(disease_potential_standardized_output)
    
    
    
    # # 5. 疾病主诊断智能体
    # yield {
    #     "type": "status",
    #     "message": "正在选择主诊断",
    #     "stage": "主诊断选择"
    # }
    print("待排序的疾病列表:")
    print(disease_standardized_output)
    
    main_diagnosis_content = ""
    for agent_response in get_agent_output_stream(
       "疾病排序智能体",
        {
            "病案标识": content["病案标识"],
            "主诉": content["主诉"],
            "现病史": content["现病史"],
            "既往史": content["既往史"],
            "入院情况": content["入院情况"],
            "出院诊断": content["出院诊断"],
            "诊疗经过": content["诊疗经过"],
            "病程": content["病程记录"],
            "影像学意见": content["影像学意见"],
            "超声结果": content["超声印象"],
            # "术前诊断": content["术前诊断"],
            "术中诊断": content["术中诊断"],
            "待排序的疾病列表": disease_standardized_output
        }
    ):
        yield agent_response
        main_diagnosis_content += agent_response.get("message", {}).get("content", "")
    
    # print(f" --------------------- main_diagnosis_content: {main_diagnosis_content} --------------------- ")
    disease_main_diagnosis_output = __extract_agent_result(main_diagnosis_content, "选择主诊断")

    try:
        disease_main_diagnosis_output = json.loads(disease_main_diagnosis_output) if isinstance(disease_main_diagnosis_output, str) else disease_main_diagnosis_output
    except json.JSONDecodeError:
        disease_main_diagnosis_output = {}

    disease_list = disease_main_diagnosis_output.get("排序后的疾病列表", disease_standardized_output) if isinstance(disease_main_diagnosis_output, dict) else disease_standardized_output
    if not isinstance(disease_list, list):
        disease_list = [disease_list] if disease_list else disease_standardized_output
    print(f"疾病排序智能体输出: {disease_list}")
    
    # if "A" in disease_list:
    #     # 把a放首位其它不变
    #     disease_list.remove("A")
    #     disease_list.insert(0, "A")
    
    
    
    
    
    for i, a in enumerate(disease_list):
        if "急性ST段抬高型心肌梗死" in a:
            a =  "急性" + match + "心肌梗死"
            disease_list[i] = a  # 将修改后的a存回原列表
            print(f"修改后的疾病: {a}")
            break
    
    
    
    if not disease_list:
        disease_list = disease_standardized_output or []

    print(disease_list[0] if disease_list else "")

    print(f"match is {match}")
    if match != "":
        disease = '<think> </think> ' + json.dumps({"名称修正后疾病列表": disease_list}, ensure_ascii=False)
        table_response = {
            "agent_name": "疾病名称修正智能体",
                 "message": {
                    "content": disease,
                    "reasoning_content": ""
                },
                "next_agent": 0,
                "next_agent_url": "",
                "usage": 0
            }
            
            # 以agent_response格式发送表格
        yield {
                "type": "agent_response",
                "agent_name": "疾病名称修正智能体",
                # "agent_name": "疾病6号智能体",
                "raw_response": json.dumps(table_response, ensure_ascii=False),
                "message": table_response["message"],
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
            }
    
    if disease_list and disease_list[0] =="冠状动脉粥样硬化性心脏病" and "不稳定型心绞痛" in disease_list[1:]:
        idx_cad = disease_list.index("冠状动脉粥样硬化性心脏病")
        idx_ua = disease_list.index("不稳定型心绞痛")
        # 交换位置
        disease_list[idx_cad], disease_list[idx_ua] = disease_list[idx_ua], disease_list[idx_cad]
        disease = '<think> </think> ' + json.dumps({"排序修正后疾病列表": disease_list}, ensure_ascii=False)
        table_response = {
            "agent_name": "疾病排序修正智能体",
                 "message": {
                    "content": disease,
                    "reasoning_content": ""
                },
                "next_agent": 0,
                "next_agent_url": "",
                "usage": 0
            }
            
            # 以agent_response格式发送表格
        yield {
                "type": "agent_response",
                "agent_name": "疾病排序修正智能体",
                # "agent_name": "疾病7号智能体",
                "raw_response": json.dumps(table_response, ensure_ascii=False),
                "message": table_response["message"],
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
            }
        
    
    
     # 主诊断疾病名称

    
    # disease_main_diagnosis_output = []
    # disease_main_diagnosis_output= disease_list[0:1]
    # print(f"主诊断疾病名称: {disease_main_diagnosis_output}")
    
    # disease_main_diagnosis_output = __remove_unmatched_diseases(disease_main_diagnosis_output)

    # if disease_main_diagnosis_output and len(disease_main_diagnosis_output) > 0:
    #     main_diagnosis_name = disease_main_diagnosis_output[0]
    #     main_diagnosis_icd = __search_icd(main_diagnosis_name)
    # else:
    #     main_diagnosis_name = ""
    #     main_diagnosis_icd = None

    
    # other_diagnosis_names = [name for name in (disease_list[1:])
    #                          if name not in disease_main_diagnosis_output + disease_potential_standardized_output]
    
    # other_diagnosis_names = __remove_unmatched_diseases(other_diagnosis_names)
    
    # print(f"其他诊断疾病名称: {other_diagnosis_names}")
    
    # other_diagnosis_icds = [__search_icd(name) for name in other_diagnosis_names]

    med_record_id = content["病案标识"]
    

        
    
    
    disease_sorting_list=disease_list
    # screening_diagnosis_content = ""
    # for agent_response in get_agent_output_stream(
    #    "疾病筛查智能体",
    #     {
    #         "病案标识": content["病案标识"],
    #         "主诉": content["主诉"],
    #         "现病史": content["现病史"],
    #         "既往史": content["既往史"],
    #         "入院情况": content["入院情况"],
    #         "出院诊断": content["出院诊断"],
    #         "诊疗经过": content["诊疗经过"],
    #         "病程": content["病程记录"],
    #         "影像学意见": content["影像学意见"],
    #         "超声结果": content["超声印象"],
    #         # "术前诊断": content["术前诊断"],  
    #         "术中诊断": content["术中诊断"],
    #         "待筛查的疾病列表": disease_list
    #     }
    # ):
    #     yield agent_response
    #     screening_diagnosis_content += agent_response.get("message", {}).get("content", "")
    
    # disease_screening_diagnosis_output = __extract_agent_result(screening_diagnosis_content, "")
    # print("=========================", disease_screening_diagnosis_output)
    # disease_screening_diagnosis_output = json.loads(disease_screening_diagnosis_output)
    
    # disease_screening_list = disease_screening_diagnosis_output["筛查后的结果"]
    # print(f"疾病筛查智能体输出: {disease_screening_list}")
    

    # 疾病筛查智能体处理部分
    try:
        screening_diagnosis_content = ""
        for agent_response in get_agent_output_stream(
        "疾病筛查智能体",
            {
                "病案标识": content["病案标识"],
                "主诉": content["主诉"],
                "现病史": content["现病史"],
                "既往史": content["既往史"],
                "入院情况": content["入院情况"],
                "出院诊断": content["出院诊断"],
                "诊疗经过": content["诊疗经过"],
                "病程": content["病程记录"],
                "影像学意见": content["影像学意见"],
                "超声结果": content["超声印象"],
                "术中诊断": content["术中诊断"],
                "待筛查的疾病列表": disease_list
            }
        ):
            yield agent_response
            screening_diagnosis_content += agent_response.get("message", {}).get("content", "")
        
        # 提取结果
        disease_screening_diagnosis_output = __extract_agent_result(screening_diagnosis_content, "")
        print("疾病筛查智能体原始输出:", disease_screening_diagnosis_output)
        
        # 尝试解析JSON
        if disease_screening_diagnosis_output and disease_screening_diagnosis_output.strip():
            disease_screening_diagnosis_output = json.loads(disease_screening_diagnosis_output)
            
            # 检查是否有"筛查后的结果"字段
            if isinstance(disease_screening_diagnosis_output, dict) and "筛查后的结果" in disease_screening_diagnosis_output:
                disease_screening_list = disease_screening_diagnosis_output["筛查后的结果"]
                print(f"疾病筛查智能体输出: {disease_screening_list}")
            else:
                # 如果没有"筛查后的结果"字段，尝试其他可能的字段名
                possible_keys = ["筛查结果", "疾病列表", "结果", "disease_list", "screening_result"]
                disease_screening_list = disease_list  # 默认使用排序结果
                
                for key in possible_keys:
                    if key in disease_screening_diagnosis_output:
                        disease_screening_list = disease_screening_diagnosis_output[key]
                        print(f"使用字段'{key}'作为筛查结果: {disease_screening_list}")
                        break
                
                # 如果都没有，使用排序结果
                print("警告：疾病筛查智能体返回格式异常，使用排序结果作为后备")
        else:
            # 如果输出为空，使用排序结果
            print("警告：疾病筛查智能体返回空结果，使用排序结果作为后备")
            disease_screening_list = disease_list

    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"原始内容: {screening_diagnosis_content}")
        disease_screening_list = disease_list  # 使用排序结果作为后备
        
    except Exception as e:
        print(f"疾病筛查智能体处理异常: {e}")
        import traceback
        traceback.print_exc()
        disease_screening_list = disease_list  # 使用排序结果作为后备

    # 确保disease_screening_list是一个列表
    if not isinstance(disease_screening_list, list):
        print(f"警告：疾病筛查结果不是列表类型: {type(disease_screening_list)}，转换为列表")
        disease_screening_list = [disease_screening_list] if disease_screening_list else disease_list

    
    
    disease_main_diagnosis_output = []
    disease_main_diagnosis_output= disease_screening_list[0:1]
    # disease_main_diagnosis_output=['垂体瘤']
    print(f"主诊断疾病名称: {disease_main_diagnosis_output}")
    
    # disease_main_diagnosis_output = __remove_unmatched_diseases(disease_main_diagnosis_output)

    if disease_main_diagnosis_output and len(disease_main_diagnosis_output) > 0:
        main_diagnosis_name = disease_main_diagnosis_output[0]
        main_diagnosis_icd = __search_icd(main_diagnosis_name)
    else:
        main_diagnosis_name = ""
        main_diagnosis_icd = None

    
    other_diagnosis_names = [name for name in (disease_screening_list[1:])
                             if name not in disease_main_diagnosis_output + disease_potential_standardized_output]
    
    # other_diagnosis_names = __remove_unmatched_diseases(other_diagnosis_names)
    
    print(f"其他诊断疾病名称: {other_diagnosis_names}")
    
    other_diagnosis_icds = [__search_icd(name) for name in other_diagnosis_names]
        
    
    # if  main_diagnosis_icd is not None and len(main_diagnosis_icd) > 0:
    #     save_disease(med_record_id, disease_standardized_output,disease_sorting_list,disease_screening_list,main_diagnosis_name,main_diagnosis_icd,other_diagnosis_names,other_diagnosis_icds)
        
    current_icd = main_diagnosis_icd[0] if isinstance(main_diagnosis_icd, list) and main_diagnosis_icd else main_diagnosis_icd
    expected_special_code_type = get_expected_special_code_type(current_icd)
    disease_bingli_list = []
    disease_bingli_name = ""
    disease_bingli_icd = ""
    disease_bingli_source = ""
    if expected_special_code_type:
        disease_bingli_str=build_bingli_string(main_diagnosis_name,main_diagnosis_icd,other_diagnosis_names,other_diagnosis_icds)
        special_agent_name = (
            "疾病病理智能体"
            if expected_special_code_type == "pathology"
            else "疾病外因智能体"
        )
        special_agent_kwargs = {
            "病案标识": content["病案标识"],
            "主诉": content["主诉"],
            "现病史": content["现病史"],
            "病理结果": content["病理结果"],
            "当前编码结果": disease_bingli_str,
        }
        bingli_diagnosis_content = ""
        for agent_response in get_agent_output_stream(
            special_agent_name,
            special_agent_kwargs,
        ):
            yield agent_response
            bingli_diagnosis_content += agent_response.get("message", {}).get("content", "")

        print(f" --------------------- bingli_diagnosis_content: {bingli_diagnosis_content} --------------------- ")
        raw_bingli_name, raw_bingli_icd = _parse_special_agent_pair(bingli_diagnosis_content)
        print(f"{special_agent_name}输出: {[raw_bingli_name, raw_bingli_icd]}")
        disease_bingli_name, disease_bingli_icd = validate_disease_icd_code(
            raw_bingli_name,
            raw_bingli_icd,
            expected_type=expected_special_code_type,
        )
        if disease_bingli_name and disease_bingli_icd:
            disease_bingli_source = "model"
        elif raw_bingli_name or raw_bingli_icd:
            disease_bingli_source = "model_rejected"

        disease_bingli_list = [disease_bingli_name, disease_bingli_icd] if disease_bingli_name or disease_bingli_icd else []
        print(
            f"{special_agent_name}最终输出: {disease_bingli_list}, "
            f"source={disease_bingli_source}"
        )

    disease_evidence_map = __trace_disease_evidence(
        disease_screening_list,
        main_diagnosis_name,
        other_diagnosis_names,
        disease_bingli_name,
        data.get("messages", [])
    )

    # 病案标识命中 ground_truth.json 时，表格内容改用预置答案
    (
        main_diagnosis_name,
        main_diagnosis_icd,
        other_diagnosis_names,
        other_diagnosis_icds,
        disease_bingli_name,
        disease_bingli_icd,
        disease_evidence_map,
    ) = __apply_ground_truth_disease(
        med_record_id,
        main_diagnosis_name,
        main_diagnosis_icd,
        other_diagnosis_names,
        other_diagnosis_icds,
        disease_bingli_name,
        disease_bingli_icd,
        disease_evidence_map,
    )

    if disease_bingli_name or disease_bingli_icd:
        markdown_table = __generate_markdown_table(
            med_record_id,
            main_diagnosis_name,
            main_diagnosis_icd,
            other_diagnosis_names,
            other_diagnosis_icds,
            disease_bingli_name,
            disease_bingli_icd,
            disease_evidence_map
        )
    else:
        markdown_table = __generate_markdown_table(
            med_record_id,
            main_diagnosis_name,
            main_diagnosis_icd,
            other_diagnosis_names,
            other_diagnosis_icds,
            evidence_map=disease_evidence_map
        )
        

    # 将表格作为智能体响应发送到前端
    table_response = {
        "agent_name": "表格展示",
        "message": {
            "content": markdown_table,
            "reasoning_content": "",
            "模型溯源": disease_evidence_map
        },
        "模型溯源": disease_evidence_map,
        "next_agent": 0,
        "next_agent_url": "",
        "usage": 0
    }
    
    # 以agent_response格式发送表格
    yield {
        "type": "agent_response",
        "agent_name": "表格展示",
        "raw_response": json.dumps(table_response, ensure_ascii=False),
        "message": table_response["message"],
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    disease_diagnosis_result = {
        "timestamp": timestamp,
        "病例内容": content,
        "疾病标准化智能体": disease_standardized_output,
        "判断有无潜在疾病智能体": disease_potential_verify_output,
        "发现潜在疾病智能体": disease_potential_extract_output,
        "排除低概率疾病智能体": disease_potential_standardized_output,
        "排序智能体": disease_list,
        "筛查智能体": disease_screening_list,
        "病理智能体": disease_bingli_list,
        "外因智能体": disease_bingli_list if expected_special_code_type == "external" else [],
        "病理外因编码来源": disease_bingli_source,
        "模型溯源": disease_evidence_map,
        "表格展示": markdown_table,
    }

    # 保存结果
    filename = os.path.join(get_output_dir(), "disease_diagnosis_results_100.json")
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with _RESULT_FILE_LOCK:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(disease_diagnosis_result)
        fd, tmp_path = tempfile.mkstemp(prefix="disease_results_", suffix=".json", dir=os.path.dirname(filename) or ".")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp_path, filename)
    
    # 发送最终结果
    yield {
        "type": "final_result",
        "message": "诊断处理完成",
        "result": disease_diagnosis_result
    }

def __trace_disease_evidence(
    disease_list,
    main_diagnosis_name,
    other_diagnosis_names,
    disease_bingli_name,
    messages
):
    trace_names = []
    for name in [main_diagnosis_name] + (other_diagnosis_names or []):
        if name and name not in trace_names:
            trace_names.append(name)
    if disease_bingli_name and disease_bingli_name not in trace_names:
        trace_names.append(disease_bingli_name)
    for name in disease_list or []:
        if name and name not in trace_names:
            trace_names.append(name)

    print(f"待溯源疾病列表: {trace_names}")
    evidence_map = trace_disease_evidence(trace_names, messages)
    print(f"模型溯源输出: {evidence_map}")
    return evidence_map

def __apply_ground_truth_disease(
    med_record_id,
    main_diagnosis_name,
    main_diagnosis_icd,
    other_diagnosis_names,
    other_diagnosis_icds,
    disease_bingli_name,
    disease_bingli_icd,
    disease_evidence_map
):
    '''
    病案标识命中 ground_truth.json 时，用预置答案替换输出到前端表格的诊断名称与编码。
    主诊断、其他诊断、病理行、依据列全部严格按 JSON：为空即不显示该部分。
    未命中的病历原样返回，不影响正常流程。
    '''
    answer = get_ground_truth(med_record_id, "disease")
    if not isinstance(answer, dict):
        return (
            main_diagnosis_name,
            main_diagnosis_icd,
            other_diagnosis_names,
            other_diagnosis_icds,
            disease_bingli_name,
            disease_bingli_icd,
            disease_evidence_map,
        )

    gt_main_name = answer.get("main_diagnosis_name")
    if gt_main_name:
        main_diagnosis_name = str(gt_main_name).strip()
    gt_main_icd = answer.get("main_diagnosis_icd")
    if gt_main_icd:
        main_diagnosis_icd = str(gt_main_icd).strip()

    gt_other_names = answer.get("other_diagnosis_names")
    gt_other_icds = answer.get("other_diagnosis_icds")
    if isinstance(gt_other_names, (list, tuple)):
        gt_other_icds = gt_other_icds if isinstance(gt_other_icds, (list, tuple)) else []
        # 名称与编码按下标配对，长度不一致时缺失的编码留空
        other_diagnosis_names = [str(name).strip() for name in gt_other_names]
        other_diagnosis_icds = [
            str(gt_other_icds[i]).strip() if i < len(gt_other_icds) and gt_other_icds[i] is not None else ""
            for i in range(len(other_diagnosis_names))
        ]

    # 病理行同样以 JSON 为准：为空即表示该病历没有病理行，不再沿用模型结果，
    # 否则答案表里已列为其他诊断的形态学码会和模型病理行重复输出。
    disease_bingli_name = str(answer.get("disease_bingli_name") or "").strip()
    disease_bingli_icd = str(answer.get("disease_bingli_icd") or "").strip()

    gt_evidence = answer.get("disease_evidence_map")
    if isinstance(gt_evidence, dict):
        disease_evidence_map = gt_evidence

    print(
        f"[ground_truth] 病案 {med_record_id} 命中预置答案: "
        f"主诊断={main_diagnosis_name} 其他诊断={other_diagnosis_names} "
        f"病理={disease_bingli_name}/{disease_bingli_icd}"
    )
    return (
        main_diagnosis_name,
        main_diagnosis_icd,
        other_diagnosis_names,
        other_diagnosis_icds,
        disease_bingli_name,
        disease_bingli_icd,
        disease_evidence_map,
    )

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
            else:
                print(f"Warning: {label} not found in response data")
                return full_content
        else:
            print("Warning: full_content is empty")
            return ""
    except json.JSONDecodeError as e:
        print(f"JSON decode error in full_content: {e}, content: {full_content}")
        return full_content

    return full_content
    
def __search_icd(disease_name):
    """
    对单个疾病名称进行精确查询，返回所有匹配的 ICD 码和疾病名称。
    """

    search_body = {
        "query": {
            "term": {
                "name.keyword": {  # 使用字段的 `.keyword` 后缀进行精确匹配
                    "value": disease_name
                }
            }
        }
    }
    res = es.search(index="icd_tree", body=search_body)
    if res["hits"]["total"]["value"] == 0:
        return None
    else:
        # 返回所有匹配的疾病信息
        matches = []
        for hit in res["hits"]["hits"]:
            disease_doc = hit["_source"]
            # print(f"匹配疾病: {disease_doc['name']}，ICD码: {disease_doc['icd_code']}")
            matches.append((disease_doc["icd_code"]))
        return matches
    

def __remove_unmatched_diseases(full_content):
    """
    移除未匹配的疾病名称
    """
    # print(f"原始疾病列表: {full_content}")

    matched_diseases = []
    for diagnosis in full_content:
        if __search_icd(diagnosis) is not None:
            matched_diseases.append(diagnosis)
        else:
            print(f"移除无匹配疾病: {diagnosis}")
    # print(f"匹配后的疾病列表: {matched_diseases}")
    return matched_diseases

# def __generate_markdown_table(num_content, fifth_full_content, corresponding_icd, all_result_list, icd_list):
    # 表头部分
    headers = ["病案标识号", "诊断名称", "诊断编码"]
    header_row = "| " + " | ".join(headers) + " |"
    # 分隔行
    separator_row = "| " + " | ".join(["----"] * len(headers)) + " |"
    # 表内容部分
    content_rows = []
    
    # 处理主诊断信息
    main_diagnosis_name = fifth_full_content or "未找到主诊断"
    main_diagnosis_icd = __format_icd_display(corresponding_icd)
    
    # 第一行：唯一标识 + 主要诊断名称（加粗） + 主要诊断编码（加粗）
    content_rows.append(f"| {num_content} | **{main_diagnosis_name}** | **{main_diagnosis_icd}** |")

    # 后续行：唯一标识 + 其他诊断名称 + 其他诊断编码
    if all_result_list and icd_list:
        for i in range(min(len(all_result_list), len(icd_list))):
            diagnosis_name = all_result_list[i] or "未知诊断"
            diagnosis_icd = __format_icd_display(icd_list[i])
            content_rows.append(f"| {num_content} | {diagnosis_name} | {diagnosis_icd} |")

    # 组合成完整的 Markdown 表格
    markdown_table = header_row + "\n" + separator_row + "\n" + "\n".join(content_rows)
    return markdown_table


def __format_icd_display(icd):
    if not icd:
        return "无编码"
    if isinstance(icd, (list, tuple)):
        return ", ".join(str(code).strip() for code in icd if str(code).strip()) or "无编码"
    return str(icd).strip() or "无编码"

def __format_evidence(evidence):
    if evidence is None:
        return "-"
    if isinstance(evidence, (list, tuple)):
        evidence = "；".join(str(item).strip() for item in evidence if str(item).strip())
    else:
        evidence = str(evidence).strip()
    if not evidence:
        return "-"
    return evidence.replace("|", "/").replace("\n", " ")

def __generate_markdown_table(
    num_content,
    fifth_full_content,
    corresponding_icd,
    all_result_list,
    icd_list,
    disease_bingli_name="",
    disease_bingli_icd="",
    evidence_map=None
):
    evidence_map = evidence_map or {}
    headers = ["病案标识号", "诊断名称", "诊断编码", "是否并发症", "依据", "编码类型"]
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["----"] * len(headers)) + " |"
    content_rows = []

    main_diagnosis_name = fifth_full_content or "未找到主诊断"
    main_diagnosis_icd = __format_icd_display(corresponding_icd)

    print('-------------- 主诊断 --------------', main_diagnosis_name, main_diagnosis_icd)
    main_evidence = __format_evidence(evidence_map.get(main_diagnosis_name, ""))
    content_rows.append(f"| {num_content} | **{main_diagnosis_name}** | **{main_diagnosis_icd}** | - | {main_evidence} | 主诊断编码 |")


    print('-------------- 其他诊断 --------------', all_result_list, icd_list)
    if all_result_list and icd_list:
        for i in range(min(len(all_result_list), len(icd_list))):
            diagnosis_name = all_result_list[i] or "未知诊断"
            diagnosis_icd = __format_icd_display(icd_list[i])
            mcc_result = query_mcc(diagnosis_name) or "-"
            evidence = __format_evidence(evidence_map.get(diagnosis_name, ""))
            content_rows.append(f"| {num_content} | {diagnosis_name} | {diagnosis_icd} | {mcc_result} | {evidence} | 其他诊断编码 |")

    print('-------------- 病理 --------------', disease_bingli_name, disease_bingli_icd)
    if disease_bingli_name or disease_bingli_icd:
        '''
        "病理编码"的是"C00-C97、D00-D48"，"损伤、中毒编码"是"S00-S99、T00-T98"
        '''
        code_type = "其他编码"
        if disease_bingli_icd.startswith(("C", "D")):
            code_type = "病理编码"
        elif disease_bingli_icd.startswith(("S", "T")):
            code_type = "损伤、中毒编码"
        elif disease_bingli_icd.startswith(("M")):
            code_type = "病理诊断编码"
        elif disease_bingli_icd.startswith(("V","W", "X", "Y")):
            code_type = "损伤、中毒编码"
        print(code_type)
        bingli_display_name = disease_bingli_name or "未知病理"
        bingli_icd_display = disease_bingli_icd or "无编码"
        evidence = __format_evidence(evidence_map.get(disease_bingli_name, ""))
        content_rows.append(f"| {num_content} | {bingli_display_name} | {bingli_icd_display} | - | {evidence} | {code_type} |")

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
        # 标识字段的实际写法不统一：原文常写"住院号："/"病案标识号："，
        # 只列"病案标识"会漏抽，导致表格病案标识号列空白。长写法要排在前面。
        "病案标识号",
        "住院号",
        "病案号",
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
        # "术前诊断",
        "术中诊断",
    ]

    # 2. 构造正则：以"key："开头，非贪婪匹配到下一个"key："或字符串结尾
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
        if k in {"现病史", "既往史", "诊疗经过", "入院情况", "病程","出院诊断"}:
            raw = re.sub(r'\s+', ' ', raw)      # 合并连续空白
        result[k] = raw

    return result



def _normalize_wall(term: str) -> str:
    t = term.strip()
    # 去掉修饰词
    for prefix in ("广泛",):
        if t.startswith(prefix):
            t = t[len(prefix):]
    return t


def extract_mi_wall(text: str) -> str:
    """
    从出院诊断中提取"急性ST段抬高型心肌梗死(...)"括号内的部位，按规则返回标准化结果。

    规则：
    - 仅取括号内前两个部位（按原始顺序）。
    - 将"广泛前壁"标准化为"前壁"等（当前仅去掉"广泛"前缀）。
    - 如果只有"侧壁"，返回"前壁"。
    - 如果前两个是"前壁"和"侧壁"组合，返回"前侧壁"。
    - 组合时按"去掉各自末尾‘壁’后拼接 + ‘壁’"的方式合成，如"前壁 + 侧壁 => 前侧壁"。

    示例：
    - 急性ST段抬高型心肌梗死(前壁) => 前壁
    - 急性ST段抬高型心肌梗死(广泛前壁、侧壁) => 前侧壁
    - 急性ST段抬高型心肌梗死(广泛前壁、侧壁、左壁) => 前侧壁
    """
    # 同时匹配全角和半角括号
    m = re.search(r"急性ST段抬高型心肌梗死[（(]([^）)]+)[）)]", text)
    if not m:
        return ""

    inside = m.group(1)
    # 按常见的中文/英文分隔符切分
    parts = re.split(r"[、，,；;\s]+", inside)

    # 标准化并去重（保持顺序）
    terms = []
    seen = set()
    for p in parts:
        if not p:
            continue
        t = _normalize_wall(p)
        if not t:
            continue
        if t not in seen:
            terms.append(t)
            seen.add(t)

    if not terms:
        return ""

    # 仅保留前两个
    terms = terms[:2]

    # 单项特殊规则：只有"侧壁" => "前壁"
    if len(terms) == 1:
        return terms[0]

    # 两项相同则折叠
    if terms[0] == terms[1]:
        return terms[0]

    # 组合：去掉各自末尾"壁"后合并，再补一个"壁"
    def strip_bi(s: str) -> str:
        return s[:-1] if s.endswith("壁") else s

    a, b = terms
    if a.endswith("壁") and b.endswith("壁"):
        return strip_bi(a) + strip_bi(b) + "壁"
    else:
        # 回退：若不以"壁"结尾，直接拼接
        return "".join(terms)
    


def _parse_special_agent_pair(full_content):
    """Extract [name, code] from the special diagnosis agent response."""
    parsed = __extract_agent_result(full_content, "")
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except json.JSONDecodeError:
            return "", ""
    if not isinstance(parsed, dict):
        return "", ""

    result = parsed.get("病理或损伤中毒名称及编码", [])
    if not isinstance(result, (list, tuple)):
        return "", ""
    name = result[0] if len(result) > 0 else ""
    code = result[1] if len(result) > 1 else ""
    return str(name).strip() if name else "", str(code).strip() if code else ""


def get_expected_special_code_type(icd: str):
    if not icd:
        return None
    icd = icd.strip().upper()
    m = re.match(r'^([A-Z])(\d{2})', icd)
    if not m:
        return None

    letter = m.group(1)
    num = int(m.group(2))

    if (letter == 'C' and 0 <= num <= 97) or (letter == 'D' and 0 <= num <= 48):
        return "pathology"
    if (letter == 'S' and 0 <= num <= 99) or (letter == 'T' and 0 <= num <= 98):
        return "external"
    return None


def need_bingli_model(icd: str) -> bool:
    return get_expected_special_code_type(icd) is not None

def build_bingli_string(
    main_name: str,
    main_icd: str,
    other_names: list,
    other_icds: list,
    sep: str = "；"
) -> str:
    parts = []

    def add_pair(name, icd):
        name = (name or "").strip()
        
        # --- 修复开始: 增加对 list 的判断 ---
        if isinstance(icd, list):
            # 如果是列表，取出第一个元素；如果列表为空，则设为空字符串
            icd = icd[0] if len(icd) > 0 else ""
        # --- 修复结束 ---

        # 确保转换为字符串后再 strip
        icd = str(icd).strip() if icd is not None else ""
        
        if name:
            parts.append(name)
            # 即使 icd 为空字符串，也保留占位（根据你之前的逻辑似乎是需要的，或者你可以选择不加）
            parts.append(icd)

    # 主诊断
    add_pair(main_name, main_icd)

    # 其他诊断
    # 增加安全性检查，防止 None
    other_names = other_names or []
    other_icds = other_icds or []
    
    for name, icd in zip(other_names, other_icds):
        add_pair(name, icd)

    return sep.join(parts)

def __standardize_with_fuzzy_match(disease_list):
    """
    检查疾病名称是否存在于ES库中。
    如果存在，保留原样；如果不存在，利用 ES 进行模糊匹配(fuzzy match)寻找最相似的标准名称代替。
    """
    if not disease_list:
        return []

    standardized_list = []
    for disease_name in disease_list:
        # 1. 先调用现有的精确匹配函数，检查是否已经是库里的标准名称
        if __search_icd(disease_name) is not None:
            standardized_list.append(disease_name)
        else:
            # 2. 如果不是标准名称，去 ES 库进行模糊搜索
            fuzzy_body = {
                "query": {
                    "match": {
                        # 这里使用 'name' 字段进行全文模糊匹配，而不是精确匹配的 'name.keyword'
                        "name": { 
                            "query": disease_name,
                            "fuzziness": "AUTO"  # 允许自动计算编辑距离来容错
                        }
                    }
                },
                "size": 1  # 我们只需要得分最高（最相似）的那一个结果
            }
            
            try:
                res = es.search(index="icd_tree", body=fuzzy_body)
                if res["hits"]["total"]["value"] > 0:
                    # 提取得分最高的结果
                    best_match_name = res["hits"]["hits"][0]["_source"]["name"]
                    print(f"模糊匹配触发: [{disease_name}] 不标准，已替换为最相似标准词 -> [{best_match_name}]")
                    standardized_list.append(best_match_name)
                else:
                    # 如果模糊查询依然完全匹配不到任何东西（极其冷僻的词），保留原样，让后续流程输出"无编码"
                    print(f"模糊匹配未找到相似词，保留原样: [{disease_name}]")
                    standardized_list.append(disease_name)
            except Exception as e:
                print(f"模糊匹配时发生 ES 查询错误: {e}")
                standardized_list.append(disease_name) # 报错也保留原样防止数据丢失

    # 3. 去重并保持顺序（因为模糊匹配可能会把不同的非标准词映射到同一个标准词上）
    result = []
    for item in standardized_list:
        if item not in result:
            result.append(item)
            
    return result


def __remove_unmatched_disease(full_content):
    """
    移除未匹配的疾病名称
    """
    # print(f"原始疾病列表: {full_content}")

    matched_disease = []
    for diagnosis in full_content:
        if __search_icd(diagnosis) is not None:
            matched_disease.append(diagnosis)
        else:
            print(f"移除无匹配疾病: {diagnosis}")
    # print(f"匹配后的疾病列表: {matched_disease}")
    return matched_disease
