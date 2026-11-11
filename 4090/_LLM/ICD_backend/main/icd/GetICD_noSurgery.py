"""无手术记录：挖掘、标准化、另编码；另编码非空时筛查，否则直接采用标准化结果。"""
import json
import re
import unicodedata
from datetime import datetime

from icd import no_surgery_support as support
from icd.SurgeryAgents import get_agent_output_stream
from tools.agent_timing import timed_call
from tools.orthers_search import orthers_search
from tools.微创 import query_surgery_level
from tools.additional_coding import (collect_additional_candidates, coding_rules_for,
                                     candidate_event, canonical_screened_names, append_fixed_additional_coding, SCREENING_TASK)

VERSION = 'no_surgery'
STAGES = ['挖掘智能体(无手术记录)', '标准化智能体(无手术记录)',
          '另编码智能体(无手术记录)', '筛查智能体(无手术记录)']


def parse_list(text, label):
    text = re.sub(r'<think>.*?</think>', '', text or '', flags=re.S | re.I)
    text = re.sub(r'</?think>', '', text, flags=re.I).strip()
    decoder = json.JSONDecoder()
    for offset, char in enumerate(text):
        if char not in '{[':
            continue
        try:
            value, _ = decoder.raw_decode(text[offset:])
        except ValueError:
            continue
        if isinstance(value, dict):
            value = value.get(label)
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            return list(dict.fromkeys(x.strip() for x in value if x.strip()
                                     and x.strip() not in {'无', '无手术', '无手术操作'}))
    raise ValueError(f'{label}: model did not return a valid list of names')


def call_stage(name, fields, label, publish_content=True):
    for attempt in range(2):
        chunks = []
        for event in get_agent_output_stream(name, fields):
            if publish_content or event.get('type') != 'agent_response':
                yield dict(event, pipeline_version=VERSION, attempt=attempt + 1)
            if event.get('error'):
                raise RuntimeError(f'{name}: {event["error"]}')
            chunks.append((event.get('message') or {}).get('content') or '')
        try:
            return parse_list(''.join(chunks), label)
        except ValueError:
            if attempt == 1:
                raise
            yield {'type': 'agent_status', 'agent_name': name, 'status': 'retrying',
                   'status_text': '输出格式无效，重试一次', 'pipeline_version': VERSION,
                   'message': {'content': '', 'reasoning_content': ''}}


def skipped(name, reason='上游无候选，跳过'):
    return {'type': 'agent_status', 'agent_name': name, 'status': 'skipped',
            'status_text': reason, 'pipeline_version': VERSION,
            'message': {'content': '', 'reasoning_content': ''}}


def name_key(name):
    # Formatting changes are reversible to a catalog name; do not remove anatomy,
    # laterality, technique, or the contents of parentheses.
    value = unicodedata.normalize('NFKC', str(name or ''))
    value = value.translate(str.maketrans({'‐': '-', '‑': '-', '–': '-', '—': '-'}))
    return re.sub(r'\s+', '', value).casefold()


def canonical_names(names, allowed, identifiers=None):
    allowed = list(dict.fromkeys(allowed))
    index = {}
    for name in allowed:
        index.setdefault(name_key(name), set()).add(name)
    result = []
    for value in names:
        value = (identifiers or {}).get(value, value)
        if value in allowed:
            canonical = value
        else:
            matches = index.get(name_key(value), set())
            canonical = next(iter(matches)) if len(matches) == 1 else None
        if canonical and canonical not in result:
            result.append(canonical)
    return result


def resolve_standardized(mined, proposed, options):
    allowed = [option['name'] for group in options.values() for option in group]
    selected = canonical_names(proposed, allowed)
    result, unresolved = [], []
    for original in mined:
        group = [option['name'] for option in options.get(original, [])]
        # Already-standard names must survive an empty or reformatted model reply.
        exact = canonical_names([original], group)
        chosen = exact or [name for name in selected if name in group]
        if not chosen:
            unresolved.append(original)
        result.extend(name for name in chosen if name not in result)
    return result, unresolved


def repair_standardization(unresolved, options, content):
    choices = {}
    identifiers = {}
    by_name = {}
    for original in unresolved:
        choices[original] = []
        for option in options.get(original, []):
            name = option['name']
            if name not in by_name:
                identifier = f'C{len(by_name) + 1:03d}'
                by_name[name] = identifier
                identifiers[identifier] = name
            choices[original].append({'候选ID': by_name[name], **option})
    if not identifiers:
        return []
    answer = yield from call_stage(STAGES[1], {
        '任务': '这是名称标准化的映射修复环节。将每个原始操作名称映射到含义对应的编码库候选。'
                '药物名加治疗的别名要结合本次诊疗经过，判断对应的标准治疗名称。'
                '只做名称映射，不重新筛查操作。没有对应候选则不选择；不能按字面相近猜测术式。'
                '只返回候选ID，禁止照抄原始别名。输出JSON格式：'
                '{"标准化手术列表":["C001"]}。无对应项返回空列表。',
        '需要映射的操作及候选': choices,
        '本次诊疗信息': {key: content.get(key, '') for key in
                         ['出院诊断', '诊疗经过', '病程记录', '病程', '手术名称', '手术经过']},
    }, '标准化手术列表', publish_content=False)
    return canonical_names(answer, identifiers.values(), identifiers)


def normalize_content(data):
    content = data['messages'][0]['content']
    content = json.loads(content) if isinstance(content, str) else dict(content)
    if 'data' in content:
        raw = content['data']
        if isinstance(raw, dict):
            content = dict(raw)
        else:
            try:
                parsed = json.loads(raw)
            except (ValueError, TypeError):
                parsed = None
            if isinstance(parsed, dict):
                content = parsed
            else:
                content = support.__get_json(str(raw or ''))
                content['原始病历'] = str(raw or '')
                # The legacy parser only knows four headings. Preserve all other
                # clinical text so unstructured input does not become an empty case.
                content['诊疗经过'] = str(raw or '')
    content = dict(content)
    content['病案标识号'] = (content.get('病案标识号') or content.get('病案标识')
                           or content.get('住院号') or '')
    return content


def catalog_options(names):
    options = {}
    for name in names:
        exact = support.__search_icd(name)
        if exact:
            options[name] = [{'name': name, 'codes': exact}]
            continue
        result = support.es.search(index='surgery_icd_tree', body={
            'query': {'match': {'name': {'query': name, 'fuzziness': 'AUTO'}}},
            'size': 5,
        })
        options[name] = [{'name': hit['_source']['name'],
                          'codes': hit['_source'].get('icd_code')}
                         for hit in result['hits']['hits']]
    return options


def get_icd(data):
    try:
        for event in get_icd_stream(data):
            yield json.dumps(event, ensure_ascii=False) + '\n'
    except Exception as exc:
        yield json.dumps({'type': 'error', 'status': 'error',
                          'pipeline_version': VERSION, 'message': str(exc)},
                         ensure_ascii=False) + '\n'


def get_icd_stream(data):
    content = normalize_content(data)
    # Keep the original no-record model's input field convention.
    fields = {key: content.get(key, '') for key in [
        '入院情况', '入院诊断', '诊疗经过', '出院诊断', '出院情况', '出院医嘱',
        '主诉', '现病史', '既往史', '个人史', '婚姻史', '家族史', '临床专业',
        '超声结果', '影像学意见', '病理结果', '术前诊断', '术中诊断', '内镜',
        '手术名称', '手术经过', '原始病历']}
    fields['病案标识'] = content['病案标识号']
    fields['病程'] = content.get('病程记录') or content.get('病程', '')
    fields['超声结果'] = content.get('超声结果') or content.get('超声印象') or content.get('超声提示', '')
    mining_fields = {'任务': '你是病案手术操作挖掘智能体。从以下病历中提取本次住院确已实施的手术和操作名称。排除既往手术、拟行、取消和否认的操作。不要改写病历、不要生成病历摘要、不要补充未提供的事实。只输出JSON对象，格式必须为：{"手术操作列表":["操作名称"]}。没有操作时输出{"手术操作列表":[]}。', **fields}
    mined = yield from call_stage(STAGES[0], mining_fields, '手术操作列表')
    standardized, extra, screened, unresolved = [], [], [], []
    relations = {}
    if mined:
        options = catalog_options(mined)
        allowed = {option['name'] for group in options.values() for option in group}
        proposed = yield from call_stage(STAGES[1], {
            '任务': '你是手术操作名称标准化智能体。本环节只做名称映射，不判断操作是否在本次住院实施；是否应保留由最后的筛查智能体判断。每个输入名称都要逐一处理。输入名称已经是编码库候选中的标准名称时必须原样保留，不能删除；别名根据名称中的部位和技术方式映射到对应候选。不能仅按字面相似强制选择不对应的术式。只能输出给定候选名称，不能新增操作。没有对应候选时才不输出该项。只输出JSON：{"标准化手术列表":["标准名称"]}。',
            '挖掘手术列表': mined, '编码库候选': options,
            '本次诊疗信息': {key: content.get(key, '') for key in ['出院诊断', '诊疗经过', '病程记录']},
        }, '标准化手术列表', publish_content=False)
        standardized, unresolved = resolve_standardized(mined, proposed, options)
        if unresolved:
            repaired = yield from repair_standardization(unresolved, options, content)
            # Do not change successful mappings while repairing the remaining items.
            standardized, unresolved = resolve_standardized(mined, standardized + repaired, options)
        summary = {'标准化手术列表': standardized}
        if unresolved:
            summary['待确认操作'] = unresolved
        yield {'type': 'agent_response', 'agent_name': STAGES[1],
               'pipeline_version': VERSION,
               'message': {'content': json.dumps(summary, ensure_ascii=False), 'reasoning_content': ''}}
    else:
        yield skipped(STAGES[1])
    if standardized:
        # Use the first standardized operation as the main operation for lookup.
        primary_operations = standardized[:1]
        lookup_result = yield from timed_call(
            STAGES[2], collect_additional_candidates, primary_operations, lookup=orthers_search)
        relations = lookup_result['relations']
        extra = [name for name in lookup_result['names'] if name not in standardized]
        coding_rules = coding_rules_for(primary_operations, support.__search_icd)
        yield dict(candidate_event(STAGES[2], extra), pipeline_version=VERSION)
        if not extra:
            # Preserve the standardized names and their order exactly.
            screened = list(standardized)
            yield skipped(STAGES[3], '另编码为空，直接输出标准化结果')
        else:
            candidates = list(dict.fromkeys(standardized + extra))
            screening_fields = dict(fields)
            screening_fields['待筛查的手术列表'] = candidates
            screening_fields['任务要求'] = '仅从候选中保留本次已实施且有依据的操作，删除既往、计划、取消、重复及不适用项；按主操作在前排序。只输出JSON：{"经筛查后的手术列表":[]}。'
            screened = yield from call_stage(STAGES[3], screening_fields, '经筛查后的手术列表')
            screened = canonical_screened_names(screened, candidates)
    else:
        yield skipped(STAGES[2])
        yield skipped(STAGES[3])
    # 筛查完成后应用固定输出规则，再查询编码并生成表格。
    main = screened[0] if screened else ''
    screened, fixed_coding = append_fixed_additional_coding(main, screened)
    others = screened[1:]
    main_code = support.__search_icd(main) if main else None
    other_codes = [support.__search_icd(name) for name in others]
    levels = query_surgery_level(others + ([main] if main else []))
    evidence = yield from timed_call('手术溯源', support.__trace_surgery_evidence,
                                    main, main_code, others, other_codes, data['messages'])
    retained_extra = [name for name in screened if name in extra or name in fixed_coding]
    table = support.__generate_markdown_table(content['病案标识号'], main, main_code,
                                             others, other_codes, levels, evidence, retained_extra)
    if not screened:
        if unresolved:
            table = '已识别到手术/操作，但名称尚未匹配到编码库，需要确认：' + '、'.join(unresolved) + '。'
        elif mined and standardized:
            table = '经筛查，本次未保留手术/操作。'
        else:
            table = '本次病历未识别出已实施的手术/操作。'
    elif unresolved:
        table += '\n\n名称待确认（未生成编码）：' + '、'.join(unresolved) + '。'
    audit = {'挖掘': mined, '标准化': standardized, '另编码': extra,
             '最终手术列表': screened, '最终另编码': retained_extra, '待确认操作': unresolved,
             '另编码候选': extra, '另编码关联': relations,
             '送筛候选': list(dict.fromkeys(standardized + extra)) if extra else []}
    yield {'type': 'agent_response', 'agent_name': '表格展示',
           'pipeline_version': VERSION, 'pipeline_audit': audit,
           'message': {'content': table, 'reasoning_content': '', '模型溯源': evidence},
           '模型溯源': evidence, 'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S')}
