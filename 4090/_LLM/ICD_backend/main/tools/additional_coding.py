"""Shared additional-coding retrieval; clinical selection belongs to screening."""
import re
import unicodedata

from tools.orthers_search import orthers_search
from tools.surgery_traceability import _load_surgery_rules, _normalize_code


SCREENING_TASK = (
    '依据本次病历和对应编码规则，从待筛查候选中选择适用的手术操作及附加编码。'
    '另编码映射仅表示候选，不表示已实施；核对部位、方式、数量和规则要求，'
    '排除既往、计划、取消、不适用及重复项。明确满足另编码规则和实施条件的项目应保留；'
    '数量、范围等附加编码应结合病历对应信息判断。不要仅因映射存在就保留，也不要新增候选外项目。'
    '主操作在前。只输出JSON：{"经筛查后的手术列表":["候选中的标准名称"]}。'
)


def collect_additional_candidates(operation_names, lookup=None):
    lookup = lookup or orthers_search
    base = list(dict.fromkeys(name.strip() for name in operation_names
                              if isinstance(name, str) and name.strip()))
    relations, candidates = {}, []
    for name in base:
        mapped = lookup(name).get('names', []) or []
        mapped = list(dict.fromkeys(value.strip() for value in mapped
                                   if isinstance(value, str) and value.strip()))
        relations[name] = mapped
        for value in mapped:
            if value not in base and value not in candidates:
                candidates.append(value)
    return {'names': candidates, 'relations': relations}


def coding_rules_for(operation_names, search_codes):
    rules = _load_surgery_rules()
    result = {}
    for name in operation_names:
        codes = search_codes(name) or []
        codes = codes if isinstance(codes, (list, tuple)) else [codes]
        result[name] = []
        seen = set()
        for code in codes:
            normalized = _normalize_code(code)
            if normalized in seen:
                continue
            seen.add(normalized)
            rule = rules.get(normalized, {})
            if rule:
                result[name].append({'编码': normalized, **rule})
    return result


def candidate_event(agent_name, names):
    import json
    return {'type': 'agent_response', 'agent_name': agent_name,
            'message': {'content': json.dumps({'另编码候选': names}, ensure_ascii=False),
                        'reasoning_content': ''}}


def canonical_screened_names(names, candidates):
    """校正可唯一对应的格式差异，保留所有候选外筛查名称。"""
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise ValueError('手术筛查未返回有效的名称列表')
    def key(name):
        value = unicodedata.normalize('NFKC', name)
        value = value.translate(str.maketrans({'‐': '-', '‑': '-', '–': '-', '—': '-'}))
        return re.sub(r'\s+', '', value).casefold()
    index = {}
    for name in candidates:
        index.setdefault(key(name), set()).add(name)
    result = []
    for name in names:
        name = name.strip()
        matches = index.get(key(name), set())
        canonical = name if name in candidates else next(iter(matches)) if len(matches) == 1 else name
        if canonical and canonical not in result:
            result.append(canonical)
    return result


def append_fixed_additional_coding(main_surgery_name, surgery_names):
    """按指定主手术名称应用固定输出规则，固定项目只出现一次并置于末尾。"""
    fixed = (['2-3个椎骨融合或再融合']
             if main_surgery_name == '后外侧入路腰椎融合术' else [])
    names = [name for name in surgery_names if name not in fixed] + fixed
    return names, fixed
