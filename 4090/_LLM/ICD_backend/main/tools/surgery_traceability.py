# """手术操作模型溯源工具。"""

# import json
# import re

# import requests

# DEEPSEEK_API_KEY = "REDACTED_SECRET"
# TRACEABILITY_URL = "https://api.deepseek.com/chat/completions"
# TRACEABILITY_MODEL = "deepseek-chat"
# REQUEST_TIMEOUT = (10, 200)


# def trace_surgery_evidence(surgeries, messages, url=TRACEABILITY_URL, model=TRACEABILITY_MODEL):
#     """为每个手术操作名称从原始病历中查找依据。"""
#     surgery_names = _normalize_surgeries(surgeries)
#     if not surgery_names:
#         return {}

#     source_text = _messages_to_text(messages)
#     if not source_text.strip():
#         return {name: "" for name in surgery_names}

#     prompt = _build_prompt(surgery_names, source_text)
#     payload = {
#         "model": model,
#         "messages": [{"role": "user", "content": prompt}],
#         "temperature": 0.1,
#         "max_tokens": 2048,
#         "stream": False,
#     }

#     try:
#         response = requests.post(
#             url,
#             headers={
#                 "Content-Type": "application/json",
#                 "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
#             },
#             json=payload,
#             timeout=REQUEST_TIMEOUT,
#         )
#         if response.status_code >= 400:
#             print(f"手术溯源 DeepSeek API 错误响应: {response.text[:1000]}")
#         response.raise_for_status()
#         content = _extract_response_content(response.json())
#         result = _parse_model_result(content)
#     except Exception as exc:
#         print(f"手术溯源 DeepSeek API 调用失败: {exc}")
#         result = {}

#     return {name: _clean_evidence(result.get(name, "")) for name in surgery_names}


# def _normalize_surgeries(surgeries):
#     names = []
#     seen = set()
#     for item in surgeries or []:
#         if isinstance(item, dict):
#             name = item.get("手术名称") or item.get("手术操作名称") or item.get("name")
#         else:
#             name = item
#         name = str(name).strip() if name else ""
#         if name and name not in seen:
#             names.append(name)
#             seen.add(name)
#     return names


# def _messages_to_text(messages):
#     if isinstance(messages, dict):
#         messages = messages.get("messages", [])
#     if not isinstance(messages, list):
#         return str(messages or "")

#     parts = []
#     for message in messages:
#         if not isinstance(message, dict):
#             parts.append(str(message))
#             continue
#         content = message.get("content", "")
#         if isinstance(content, dict):
#             parts.append(json.dumps(content, ensure_ascii=False))
#         else:
#             parts.append(str(content))
#     return "\n".join(part for part in parts if part.strip())


# def _build_prompt(surgery_names, source_text):
#     surgery_json = json.dumps(surgery_names, ensure_ascii=False)
#     return f"""你是病案手术操作溯源助手。请根据原始病历文本，为手术操作列表中的每一个手术操作寻找原文依据。
# 要求：
# 1. 只能使用原始病历文本中出现的信息，不要编造。
# 2. 依据应尽量摘取原文短句或关键片段；如果没有明确依据，返回“模型未能找到依据”。
# 3. 每个手术操作都必须输出一项，手术名称必须与输入列表完全一致。
# 4. 只输出 JSON，不要输出解释、Markdown 或 think 内容。
# 原始病历文本：
# {source_text}

# 手术操作列表：
# {surgery_json}

# 输出格式：
# {{"溯源结果":[{{"手术名称":"手术A","依据":"原文依据"}}]}}
# """


# def _extract_response_content(data):
#     choices = data.get("choices") or [] if isinstance(data, dict) else []
#     if not choices:
#         return ""
#     message = choices[0].get("message") or {}
#     return message.get("content") or ""


# def _strip_think(text):
#     text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S | re.I)
#     return text.strip()


# def _parse_model_result(text):
#     text = _strip_think(text)
#     if not text:
#         return {}

#     data = None
#     for candidate in _json_candidates(text):
#         try:
#             data = json.loads(candidate)
#             break
#         except json.JSONDecodeError:
#             continue
#     if data is None:
#         return {}

#     if isinstance(data, dict) and isinstance(data.get("溯源结果"), list):
#         items = data.get("溯源结果")
#     elif isinstance(data, list):
#         items = data
#     elif isinstance(data, dict):
#         return {str(k).strip(): _clean_evidence(v) for k, v in data.items() if str(k).strip()}
#     else:
#         return {}

#     result = {}
#     for item in items:
#         if not isinstance(item, dict):
#             continue
#         name = str(item.get("手术名称") or item.get("手术操作名称") or item.get("name") or "").strip()
#         evidence = item.get("依据") or item.get("原文依据") or item.get("evidence") or ""
#         if name:
#             result[name] = _clean_evidence(evidence)
#     return result


# def _json_candidates(text):
#     yield text
#     start = text.find("{")
#     end = text.rfind("}")
#     if start >= 0 and end > start:
#         yield text[start:end + 1]
#     start = text.find("[")
#     end = text.rfind("]")
#     if start >= 0 and end > start:
#         yield text[start:end + 1]


# def _clean_evidence(value):
#     if value is None:
#         return ""
#     if isinstance(value, (list, tuple)):
#         value = "；".join(str(item).strip() for item in value if str(item).strip())
#     else:
#         value = str(value).strip()
#     return value.replace("|", "/").replace("\n", " ")

"""手术操作模型溯源工具。"""

import json
import os
import re

import requests

TRACEABILITY_URL = os.getenv("SURGERY_TRACEABILITY_URL", "http://localhost:8020/v1/chat/completions")
TRACEABILITY_MODEL = os.getenv("SURGERY_TRACEABILITY_MODEL", "Qwen3.5-4B")
RULES_PATH = os.getenv(
    "SURGERY_TRACE_RULES_PATH",
    "/opt/qianyi/4090/_LLM/ICD_backend/main/tools/surgery_trace_rules_20260811.json",
)
REQUEST_TIMEOUT = (10, 200)
_RULES_CACHE = None


def _load_surgery_rules():
    global _RULES_CACHE
    if _RULES_CACHE is not None:
        return _RULES_CACHE
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        _RULES_CACHE = payload.get("rules", {}) if isinstance(payload, dict) else {}
    except Exception as exc:
        print(f"手术溯源规则表加载失败: {exc}")
        _RULES_CACHE = {}
    return _RULES_CACHE


def _normalize_code(value):
    if isinstance(value, (list, tuple)):
        value = next((item for item in value if str(item or "").strip()), "")
    return str(value or "").strip().replace("＊", "").replace("*", "").upper()


def trace_surgery_evidence(surgeries, messages, url=TRACEABILITY_URL, model=TRACEABILITY_MODEL, code_map=None, request_timeout=None, max_attempts=2, max_tokens=4096):
    """为每个手术操作名称从原始病历中查找依据。"""
    surgery_names = _normalize_surgeries(surgeries)
    if not surgery_names:
        return {}

    source_text = _messages_to_text(messages)
    result = {}
    if source_text.strip():
        prompt = _build_prompt(surgery_names, source_text)
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            # 溯源必须优先保证 JSON 格式稳定，避免偶发少引号导致整批证据丢失。
            "temperature": 0,
            "max_tokens": max_tokens,
            "stream": False,
        }

        attempts = max(1, min(max_attempts, 2))
        for attempt in range(attempts):
            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=request_timeout or REQUEST_TIMEOUT,
                )
                if response.status_code >= 400:
                    print(f"溯源模型错误响应: {response.text[:1000]}")
                response.raise_for_status()
                content = _extract_response_content(response.json())
                parsed = _parse_model_result(content)
                if not parsed:
                    parsed = _parse_partial_model_result(content)
                result.update(parsed)
                if all(name in result for name in surgery_names):
                    break
                if attempt + 1 < attempts:
                    print("手术溯源响应不完整，正在重试缺失证据")
            except Exception as exc:
                print(f"手术溯源模型调用失败（第 {attempt + 1} 次）: {exc}")

    code_map = code_map or {}
    rules = _load_surgery_rules()
    output = {}
    for name in surgery_names:
        code = _normalize_code(code_map.get(name, ""))
        rule = rules.get(code, {}) if code else {}
        output[name] = {
            "手术编码": code,
            "病历原文依据": _clean_evidence(result.get(name, "")),
            "注释规则": str(rule.get("note") or "").strip(),
            "另编码规则": [str(item).strip() for item in (rule.get("additional") or []) if str(item).strip()],
        }
    return output


def _normalize_surgeries(surgeries):
    names = []
    seen = set()
    for item in surgeries or []:
        if isinstance(item, dict):
            name = item.get("手术名称") or item.get("手术操作名称") or item.get("name")
        else:
            name = item
        name = str(name).strip() if name else ""
        if name and name not in seen:
            names.append(name)
            seen.add(name)
    return names


def _messages_to_text(messages):
    if isinstance(messages, dict):
        messages = messages.get("messages", [])
    if not isinstance(messages, list):
        return str(messages or "")

    parts = []
    for message in messages:
        if not isinstance(message, dict):
            parts.append(str(message))
            continue
        content = message.get("content", "")
        if isinstance(content, dict):
            parts.append(json.dumps(content, ensure_ascii=False))
        else:
            parts.append(str(content))
    return "\n".join(part for part in parts if part.strip())


def _build_prompt(surgery_names, source_text):
    surgery_json = json.dumps(surgery_names, ensure_ascii=False)
    return f"""你是病案手术操作溯源助手。请根据原始病历文本，为手术操作列表中的每一个手术操作寻找原文依据。
要求：
1. 只能使用原始病历文本中出现的信息，不要编造。
2. 依据应尽量摘取原文短句或关键片段；如果没有明确依据，依据返回空字符串。
3. 每个手术操作都必须输出一项，手术名称必须与输入列表完全一致。
4. 只输出 JSON，不要输出解释、Markdown 或 think 内容。
原始病历文本：
{source_text}

手术操作列表：
{surgery_json}

输出格式：
{{"溯源结果":[{{"手术名称":"手术A","依据":"原文依据"}}]}}
"""


def _extract_response_content(data):
    choices = data.get("choices") or [] if isinstance(data, dict) else []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return message.get("content") or ""


def _strip_think(text):
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S | re.I)
    return text.strip()


def _parse_model_result(text):
    text = _strip_think(text)
    if not text:
        return {}

    data = None
    for candidate in _json_candidates(text):
        try:
            data = json.loads(candidate)
            break
        except json.JSONDecodeError:
            continue
    if data is None:
        return {}

    if isinstance(data, dict) and isinstance(data.get("溯源结果"), list):
        items = data.get("溯源结果")
    elif isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        return {str(k).strip(): _clean_evidence(v) for k, v in data.items() if str(k).strip()}
    else:
        return {}

    result = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("手术名称") or item.get("手术操作名称") or item.get("name") or "").strip()
        evidence = item.get("依据") or item.get("原文依据") or item.get("evidence") or ""
        if name:
            result[name] = _clean_evidence(evidence)
    return result


def _parse_partial_model_result(text):
    """从不完整 JSON 中尽量提取已经生成的手术名称和依据。"""
    text = _strip_think(text)
    if not text:
        return {}
    pattern = re.compile(
        r'"(?:手术名称|手术操作名称|name)"\s*:\s*"((?:\\.|[^"\\])*)"'
        r'.{0,1200}?"(?:依据|原文依据|evidence)"\s*:\s*"((?:\\.|[^"\\])*)"',
        re.S,
    )
    result = {}
    for match in pattern.finditer(text):
        try:
            name = json.loads('"' + match.group(1) + '"').strip()
            evidence = json.loads('"' + match.group(2) + '"')
        except (json.JSONDecodeError, TypeError):
            name = match.group(1).strip()
            evidence = match.group(2).strip()
        if name:
            result[name] = _clean_evidence(evidence)
    return result


def _json_candidates(text):
    yield text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        yield text[start:end + 1]
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        yield text[start:end + 1]


def _clean_evidence(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = "；".join(str(item).strip() for item in value if str(item).strip())
    else:
        value = str(value).strip()
    value = value.replace("|", "/").replace("\n", " ")
    if value in {"模型未能找到依据", "未能找到依据", "无明确依据"}:
        return ""
    return value
