from docx import Document
import re
import pandas as pd
import os
from concurrent.futures import ProcessPoolExecutor
import paddle
from tqdm import tqdm
import openpyxl
import json
import pandas as pd


def find_all_word_files(directory):
    """
    递归查找目录下所有的.docx文件
    """
    word_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.docx'):
                word_files.append(os.path.join(root, file))
    return word_files


def clean_extracted_text(text):
    """
    清理提取的文本内容
    """
    if not text:
        return ''
    # 如果文本以冒号开头，删除冒号
    if text.startswith('：'):
        text = text[1:]
    return text.strip()


def extract_fields(cleaned_text):
    """
    提取所有字段到一个字典中，增强容错性和字段别名支持
    """
    fields_data = {}

    # 辅助函数：增强的正则匹配
    def enhanced_search(pattern_list, text, field_name):
        """
        使用多个模式进行匹配，支持字段名称变体和格式变化
        """
        for pattern in pattern_list:
            match = re.search(pattern, text)
            if match:
                return clean_extracted_text(match.group(1))
        return ''

    # 提高对含"个育史"问题的容错性
    cleaned_text = cleaned_text.replace("个育史", "个人史")
    cleaned_text = cleaned_text.replace("个人更", "个人史")
    cleaned_text = cleaned_text.replace("既往更", "既往史")
    cleaned_text = cleaned_text.replace("注诉", "主诉")
    cleaned_text = cleaned_text.replace("既注史", "既往史")
    cleaned_text = cleaned_text.replace("以往史", "既往史")
    cleaned_text = cleaned_text.replace("治疗经过", "诊疗经过")
    cleaned_text = cleaned_text.replace("入院治疗", "诊疗经过")
    # 首先检查是否存在婚姻史（更全面的检查）
    marriage_exists = bool(re.search(r'婚[育姻言]史[：:·]?', cleaned_text))

    # 根据是否存在婚姻史选择正确的个人史匹配模式
    personal_history_pattern = (
        r'个人史[：:·\s](.*?)(?=婚[育姻言]史[：:]|婚姻史|5人|$)' if marriage_exists
        else r'个人史[：:·\s](.*?)(?=家族史[：:·]|$)'
    )

    # 新增逻辑：先从"主诉"到"家族史"范围内匹配个人史
    main_to_family_match = re.search(r'主诉.*?家族史', cleaned_text, re.DOTALL)
    personal_history = ''

    if main_to_family_match:
        range_text = main_to_family_match.group(0)
        first_try_match = re.search(personal_history_pattern, range_text)
        if first_try_match:
            personal_history = clean_extracted_text(first_try_match.group(1))

    # 如果第一步没有找到个人史内容，则使用原有范围匹配模式
    if not personal_history:
        second_try_match = re.search(personal_history_pattern, cleaned_text)
        if second_try_match:
            personal_history = clean_extracted_text(second_try_match.group(1))

    # 将结果存入字段字典
    fields_data['个人史'] = personal_history

    # 新增：获取现病史和个人史之间的内容
    current_medical_history_match = re.search(r'现病史[：:·](.*?)(?=个育史|个人史[：:·]|个人史|个人更|$)', cleaned_text)

    # 定义字段的匹配模式（包括变体）
    field_patterns = {
        '主诉': [
            r'主诉：(.*?)(?=现病史[：:·，]|入院情况|$)',
            r'主诉[^：:](.*?)(?=现病史[：:·，]|入院情况|$)',  # 处理没有冒号的情况
            r'主诉\s*(.*?)(?=现病史[：:·，]|入院情况|$)'  # 处理可能的空格
        ],
        '入院情况': [
            r'入院情况：(.*?)(?=入院诊断[：:]|入院诊断|$)',
            r'入院情况[^：:](.*?)(?=入院诊断[：:]|入院诊断|$)',
            r'入院情况\s*(.*?)(?=入院诊断[：:]|入院诊断|$)'
        ],
        '入院诊断': [
            r'入院诊断[：:](.*?)(?=诊疗经过|$)',
            r'入院诊断\s*(.*?)(?=诊疗经过|$)'
        ],
        '诊疗经过': [
            r'诊疗经过[：:](.*?)(?=出院诊断|死亡原因|抢救过程无异议|冠状动脉粥样硬化性心脏病|请及时复诊|$)',
            r'诊疗经过\s*(.*?)(?=出院诊断|死亡原因|抢救过程无异议|冠状动脉粥样硬化性心脏病|请及时复诊|$)'
        ],
        '出院诊断': [
            r'出院诊断[：:](.*?)(?=出院情况|医生|出院医嘱|出院医瞩|出院医属|弦字张娇|乏力|病程记录|$)',
            r'出院诊断\s*(.*?)(?=出院情况|医生|出院医嘱|出院医瞩|出院医属|弦字张娇|乏力|病程记录|$)'
        ],
        '出院情况': [
            r'出院情况[：:]?(.*?)(?=出院医(?:[嘱瞩属])?[：:]|$)',
            r'出院情况\s*(.*?)(?=出院医(?:[嘱瞩属])?[：:]|$)'
        ],
        '出院医嘱': [
            r'出院医(?:[嘱瞩属])?[：:](.*?)(?=专家门诊|咨询电话|科室联系方式|主任门诊|治疗组联系方式|主任医师|$)',
            r'出院医(?:[嘱瞩属])?\s*(.*?)(?=专家门诊|咨询电话|科室联系方式|主任门诊|治疗组联系方式|主任医师|$)'
        ],
        # 病程记录的提取模式
        '病程记录': [
            # 情况1：匹配到"今日出院"并将其包含在结果中
            r'病程记录(.*?(今日出院|今日可出院|临床死亡|患者死亡|宣告死亡|出院后继续治疗|明日出院|今日办理出院|今日办理离院手续|及时随诊|随时来诊|自动出院|及时就诊|遵医瞩出院|家属无异议|宣布死亡|以出院|不适随访|准予出院|不适门诊随访|准许出院|及时就医))',
            # 情况2：匹配到其他截止条件但不包含它们
            r'病程记录(.*?)(?=手术记录|超声检查报告单|影像学检查报告单|病理检查报告单|$)'
        ],
        # 添加手术记录的提取模式
        '手术记录': [
            r'手术记录(.*?)(?=平车|手术者签名|$)',
            r'手术记录\s*(.*?)(?=平车|手术者签名|$)'
        ],
        '术中诊断': [
            r'术中诊断[：:](.*?)(?=手术名称|麻醉|切口|$)',
            r'术中诊断\s*(.*?)(?=手术名称|麻醉|切口|$)'
        ]
    }

    # 新增：直接在全文匹配所有手术名称
    surgery_name_matches = re.findall(
        r'手术名称[：:\s]*(.*?)(?=麻醉|手术指导者|方法|切口类型|$)', cleaned_text)
    if surgery_name_matches:
        # 清理每个找到的手术名称
        cleaned_names = [clean_extracted_text(name) for name in surgery_name_matches]
        # 用"；"连接不同手术记录中的手术名称
        fields_data['手术名称'] = '；'.join(cleaned_names)


    # 新增：影像学检查报告单的处理
    # 提取多份影像学检查报告单
    image_reports = re.findall(r'影像学检查报告单(.*?)(?=影像学检查报告单|超声检查报告单|心脏超声检查报告单|$)',
                               cleaned_text)
    if image_reports:
        image_opinions = []
        for report in image_reports:
            # 提取报告内容（从报告单到报告医师之间的内容）
            report_content = re.search(r'(.*?报告医师)', report)
            if report_content:
                report_text = report_content.group(1)
                # 提取影像学意见
                opinion_match = re.search(
                    r'影像学意见[：:](.*?)(?=报告医师|重建医师|重建技师|曲倔|吴楠|刘州州|刘兰|张添钰|刘珊水|程海|审核医师|杨克强|中帆|超|刘州|影家|反等处)',
                    report_text)
                if opinion_match:
                    # 直接使用提取的文本，空格已经在clean_text中处理
                    image_opinions.append(opinion_match.group(1).strip())

        # 将所有影像学意见用分号连接
        if image_opinions:
            fields_data['影像学意见'] = '；'.join(image_opinions)

    # 新增：超声检查报告单的处理
    # 提取多份超声检查报告单
    ultrasound_reports = re.findall(r'超声检查报告单(.*?)(?=超声检查报告单|影像学检查报告单|心脏超声检查报告单|$)',
                                    cleaned_text)
    if ultrasound_reports:
        ultrasound_findings = []
        for report in ultrasound_reports:
            # 提取报告内容（从报告单到报告日期之间的内容）
            report_content = re.search(r'(.*?报告日期)', report)
            if report_content:
                report_text = report_content.group(1)
                # 提取超声提示
                finding_match = re.search(r'超声提示[：:](.*?)(?=报告日期|检查医师|诊断医生|医生签字|$)', report_text)
                if finding_match:
                    # 直接使用提取的文本，空格已经在clean_text中处理
                    ultrasound_findings.append(finding_match.group(1).strip())

        # 将所有超声提示用分号连接
        if ultrasound_findings:
            fields_data['超声提示'] = '；'.join(ultrasound_findings)

    # 新增：心脏超声检查报告单的处理
    # 提取多份心脏超声检查报告单
    cardiac_reports = re.findall(r'心脏超声检查报告单(.*?)(?=心脏超声检查报告单|影像学检查报告单|超声检查报告单|$)',
                                 cleaned_text)
    if cardiac_reports:
        cardiac_impressions = []
        for report in cardiac_reports:
            # 提取报告内容（从报告单到医师签名之间的内容）
            report_content = re.search(r'(.*?医师签名)', report)
            if report_content:
                report_text = report_content.group(1)
                # 提取超声印象
                impression_match = re.search(
                    r'超声印象[：:](.*?)(?=医师签名|记录者|纪录者|深生记|王飞点|张怡然|谭结法|张佩佩|闭谢)', report_text)
                if impression_match:
                    # 直接使用提取的文本，空格已经在clean_text中处理
                    cardiac_impressions.append(impression_match.group(1).strip())

        # 将所有超声印象用分号连接
        if cardiac_impressions:
            fields_data['超声印象'] = '；'.join(cardiac_impressions)

    # 病史相关字段定义
    history_fields = [
        ('现病史', [r'现病史[：:·，](.*?)(?=既往史[：:·]|既往更|入院诊断|$)']),

        # 修改既往史的提取方式：如果存在现病史和个人史之间的内容，则在这段内容中提取
        ('既往史',
         [r'既往史[：:·](.*?)(?=个人史[：:·]|个人史|个人更|质等密切接触史|人史|$)'] if not current_medical_history_match
         else [r'既往史[：:·](.*?)(?=查体|个人史|$)']
         ),
        # ('个人史', [personal_history_pattern]),  # 使用动态选择的模式
    ]

    # 如果存在婚姻史，添加婚姻史字段
    if marriage_exists:
        history_fields.append(
            ('婚姻史', [r'婚[育姻言]史[：:]?(.*?)(?=家族史[：:·]|$)'])
        )

    # 添加家族史字段
    history_fields.append(
        ('家族史', [r'家族史[：:·](.*?)(?=体格检查|入院检查|查体|休格检查|体格检|住院号：|科室：|$)'])
    )

    # 提取主要字段
    for field, patterns in field_patterns.items():
        fields_data[field] = enhanced_search(patterns, cleaned_text, field)

    # 提取病史相关字段
    for field_name, patterns in history_fields:
        fields_data[field_name] = enhanced_search(patterns, cleaned_text, field_name)

        # 从病程记录提取手术名称
    # 1. 先提取有创诊疗操作记录（保持原样）
    medical_records = fields_data.get('病程记录', '')
    if medical_records:
        invasive_operations = re.findall(r'(有创诊疗操作记录.*?操作时间[：:])', medical_records, re.DOTALL)
        extracted_surgery_names = []
        for operation in invasive_operations:
            operation_name_match = re.search(r'操作名称[：:]\s*(.*?)(?=操作时间[：:])', operation)
            if operation_name_match:
                extracted_surgery_names.append(clean_extracted_text(operation_name_match.group(1)))
        if extracted_surgery_names:
            combined_surgery_names = '+'.join(extracted_surgery_names)
            if fields_data.get('手术名称'):
                fields_data['手术名称'] += '+' + combined_surgery_names
            else:
                fields_data['手术名称'] = combined_surgery_names

    # 2. 修改：提取多个手术记录
    # 提取多个手术记录 - 修改这部分代码
    surgery_records = re.findall(r'手术记录\s*(.*?)(?=平车|手术者签名|$)', cleaned_text, re.DOTALL)
    if surgery_records:
        surgery_names = []
        for record in surgery_records:
            name_match = re.search(r'手术名称[：:\s]*(.*?)(?=麻醉|手术指导者|方法|切口类型|手术切口|高亚蕾|$)', record)
            if name_match:
                surgery_name = clean_extracted_text(name_match.group(1))
                if surgery_name:  # 确保不为空
                    surgery_names.append(surgery_name)

        # 直接设置手术名称，不与其他来源合并
        if surgery_names:
            fields_data['手术名称'] = '；'.join(surgery_names)

    # 处理病程记录：去除"签名"、"医师签名"字段
    if fields_data.get('病程记录'):
        # 只删除"签名"或"医师签名"字段本身，保留后续内容
        fields_data['病程记录'] = re.sub(
            r'(医师)?签名[:：]?\s*',  # 修改后的正则表达式
            '',
            fields_data['病程记录']
        )

    # 从手术记录中提取手术名称
    surgery_record = fields_data.get('手术记录', '')
    # if surgery_record:
    #     # 从手术记录中提取手术名称
    #     name_match = re.search(r'手术名称[：:\s]*(.*?)(?=麻醉|手术指导者|方法|切口类型|$)', surgery_record)
    #     if name_match:
    #         fields_data['手术名称'] = clean_extracted_text(name_match.group(1))

    # 修改：提取所有手术经过（从整个文本中查找）
    procedure_matches = re.findall(
        r'手术经过、术中发现的情况及处理[：:](.*?)(?=手术者签名|记录时间|平车|手术过程顺利|安返病房|$)',
        cleaned_text,
        re.DOTALL
    )

    all_procedures = []
    for procedure_text in procedure_matches:
        extracted_text = clean_extracted_text(procedure_text)
        cleaned_text_procedure = re.sub(r'患者姓名.*?组|性别.*?姓名', '', extracted_text, flags=re.DOTALL)
        if cleaned_text_procedure.strip():
            all_procedures.append(cleaned_text_procedure)

    if all_procedures:
        fields_data['手术经过'] = '；'.join(all_procedures)

    # 如果存在现病史和个人史之间的内容，并且存在既往史匹配
    if current_medical_history_match:
        between_content = current_medical_history_match.group(0)
        existing_history_match = re.search(r'既往史[：:·](.*?)(?=个人史[：:·]|个人史|个人更|$)', between_content)
        if existing_history_match:
            fields_data['既往史'] = clean_extracted_text(existing_history_match.group(1))

    # 最后再提取死亡记录，确保它不会被主要字段提取覆盖
    death_record_match = re.search(r'死亡记录(.*?)(?=(签名|入院记录|病程记录))', cleaned_text)
    if death_record_match:
        death_record = death_record_match.group(1)
        # 进一步从死亡记录中提取死亡诊断
        death_diagnosis_match = re.search(r'死亡诊断[：:](.*?)(?=签名|病程记录|医生|弦字张娇|乏力|病程记录|$)',
                                          death_record)
        if death_diagnosis_match:
            death_diagnosis = clean_extracted_text(death_diagnosis_match.group(1))
            # 当找到死亡诊断时，将其存入出院诊断字段
            fields_data['出院诊断'] = death_diagnosis

    if not fields_data.get('出院诊断'):
        death_diagnosis_2_match = re.search(r'死亡诊断[：:](.*?)(?=签名|病程记录|医生|弦字张娇|乏力|病程记录|$)',
                                            cleaned_text)
        if death_diagnosis_2_match:
            cleaned_diagnosis = clean_extracted_text(death_diagnosis_2_match.group(1))
            fields_data['出院诊断'] = cleaned_diagnosis

    # 新增功能：如果手术名称为空，检查诊疗经过中是否有内镜相关信息
    if not fields_data.get('手术名称'):
        diagnosis_process = fields_data.get('诊疗经过', '')

        # 使用集合存储所有可能的手术操作术语
        surgery_terms = {
            '胃镜',
            '结肠镜',
            '内镜',
            '行电复律',
            '胃肠镜',
            '耳镜',
            '喉镜',
            '电子支气管镜',
            '胸腔穿刺',
            '置管',
            '穿刺',
            '气管插管'
        }

        # 检查诊疗经过中出现的手术操作术语
        found_terms = []
        for term in surgery_terms:
            if term in diagnosis_process:
                found_terms.append(term)

        # 如果找到了手术操作术语，用加号连接它们作为手术名称
        if found_terms:
            fields_data['手术名称'] = '+'.join(found_terms)

    # 在检查诊疗经过后，如果手术名称仍为空，检查病程记录中是否有其他医疗设备术语
    if not fields_data.get('手术名称'):
        medical_records = fields_data.get('病程记录', '')

        # 使用集合存储所有可能的医疗设备术语
        equipment_terms = {
            '呼吸机', '气管插管', '心肺复苏', 'CRRT', '胸腔引流', '甲状腺细针穿刺病理', '玻璃体', '拔牙', '牙龈增生',
            '气管插管', '支气管镜', '引流', '活检', '支架置入', '射频消融', '置入', '置管', '穿刺', '淋巴结',
            '透析', '阴道镜'
        }

        # 检查病程记录中出现的医疗设备术语
        found_terms = []
        for term in equipment_terms:
            if term in medical_records:
                found_terms.append(term)

        # 如果找到了医疗设备术语，用加号连接它们作为手术名称
        if found_terms:
            fields_data['手术名称'] = '+'.join(found_terms)

    if not fields_data.get('手术名称'):
        a = cleaned_text
        b = {'CRRT', '肠镜', '息肉切除', '引流', '掌骨骨折', '冠状动脉造影', '活检', '石膏', '呼吸机', '辅助通气',
             '电除颤', '心肺复苏', '电复律', '胸外按压', '心脏按压'}
        # 检查病程记录中出现的医疗设备术语
        c = []
        for term in b:
            if term in a:
                c.append(term)

        # 如果找到了医疗设备术语，用加号连接它们作为手术名称
        if c:
            fields_data['手术名称'] = '+'.join(c)

    return fields_data


def process_medical_record_titles(text):
    """
    专门处理病程记录部分的标题前缀删除
    """
    # 查找所有病程记录部分
    medical_record_pattern = r'(病程记录.*?(?=不适随诊|不适及时就诊|手术记录|超声检查报告单|影像学检查报告单|病理检查报告单|患者死亡|家属无异议|$))'

    def replace_titles_in_record(match):
        record_text = match.group(0)
        titles = ["副主任医师", "主任医师", "主治医师", "护士长", "护士" "护师", "规培医师", "医师", "主管护师"]

        # 处理标题：当匹配到标题时，只删除标题前面的两个字符
        for title in titles:
            # 查找所有匹配的位置
            matches = list(re.finditer(rf'(..)({title})', record_text))
            # 从后向前替换，防止替换影响索引位置
            for match in reversed(matches):
                # 只删除标题前面的两个字符，保留标题本身
                record_text = record_text[:match.start(1)] + record_text[match.end(1):]

        return record_text

    # 使用函数替换来处理每个找到的病程记录部分
    processed_text = re.sub(medical_record_pattern, replace_titles_in_record, text, flags=re.DOTALL)

    return processed_text


def clean_text(text, hospital_number):
    """
    增强的文本清理函数，保留特定部分的空格
    """
    # 统一冒号格式
    text = text.replace(':', '：')

    # 对于需要保留格式的部分，先将空格替换为特殊字符
    # 找到并暂时保护出院诊断和死亡诊断部分中的空格
    diagnosis_matches = []

    # 出院诊断匹配
    discharge_pattern = r'(出院诊断[：:](.*?)(?=出院情况|医生|出院医嘱|出院医瞩|出院医属|弦字张娇|乏力|病程记录|$))'
    discharge_matches = re.findall(discharge_pattern, text, re.DOTALL)
    for match in discharge_matches:
        full_match = match[0]
        protected_text = full_match.replace(' ', '@@SPACE@@')
        text = text.replace(full_match, protected_text)
        diagnosis_matches.append((full_match, protected_text))

    # 入院诊断匹配
    admission_pattern = r'(入院诊断[：:](.*?)(?=诊疗经过|出院诊断|$))'
    admission_matches = re.findall(admission_pattern, text, re.DOTALL)
    for match in admission_matches:
        full_match = match[0]
        protected_text = full_match.replace(' ', '@@SPACE@@')
        text = text.replace(full_match, protected_text)

    # 死亡诊断匹配
    death_pattern = r'(死亡诊断[：:](.*?)(?=签名|病程记录|医生|弦字张娇|乏力|病程记录|$))'
    death_matches = re.findall(death_pattern, text, re.DOTALL)
    for match in death_matches:
        full_match = match[0]
        protected_text = full_match.replace(' ', '@@SPACE@@')
        text = text.replace(full_match, protected_text)
        diagnosis_matches.append((full_match, protected_text))

    # 找到所有影像学检查报告单文本块
    image_reports = re.findall(
        r'(影像学检查报告单.*?(?:(?=影像学检查报告单)|(?=超声检查报告单)|(?=心脏超声检查报告单)|(?=彩色超声实时显像报告单)|$))',
        text, re.DOTALL)
    for report in image_reports:
        # 查找影像学意见部分
        opinion_match = re.search(r'(影像学意见[：:].*?)(?=报告医师|重建医师|影家|反等处)', report, re.DOTALL)
        if opinion_match:
            opinion_text = opinion_match.group(1)
            # 将空格替换为特殊字符
            modified_opinion = opinion_text.replace(' ', '@@SPACE@@')
            text = text.replace(opinion_text, modified_opinion)

    # 找到所有超声检查报告单文本块
    ultrasound_reports = re.findall(
        r'(超声检查报告单.*?(?:(?=超声检查报告单)|(?=影像学检查报告单)|(?=心脏超声检查报告单)|(?=彩色超声实时显像报告单)|$))',
        text, re.DOTALL)
    for report in ultrasound_reports:
        # 查找超声提示部分
        finding_match = re.search(r'(超声提示[：:].*?)(?=报告日期|检查医师|诊断医生|医生签字|$)', report, re.DOTALL)
        if finding_match:
            finding_text = finding_match.group(1)
            # 将空格替换为特殊字符
            modified_finding = finding_text.replace(' ', '@@SPACE@@')
            text = text.replace(finding_text, modified_finding)

    # 找到所有心脏超声检查报告单文本块
    cardiac_reports = re.findall(
        r'(心脏超声检查报告单.*?(?:(?=心脏超声检查报告单)|(?=影像学检查报告单)|(?=超声检查报告单)|(?=彩色超声实时显像报告单)|$))',
        text, re.DOTALL)
    for report in cardiac_reports:
        # 查找超声印象部分
        impression_match = re.search(r'(超声印象[：:].*?)(?=医师签名)', report, re.DOTALL)
        if impression_match:
            impression_text = impression_match.group(1)
            # 将空格替换为特殊字符
            modified_impression = impression_text.replace(' ', '@@SPACE@@')
            text = text.replace(impression_text, modified_impression)

    # 删除所有普通空格和换行符
    text = re.sub(r'[\s\u3000]', '', text)

    # 将特殊字符还原为空格
    text = text.replace('@@SPACE@@', ' ')

    # 删除医院名称等信息
    text = re.sub(
        r'山东第一医科大学\s*第一附属医院[（(]?山东省千佛山医院[）)]?|（山东省千佛山医院）|山东省千佛山医院|山东第一医科大学第一附属医院|蔡心雨|山东第一医科大字第一附属医院|山东第一医科犬学第一附属医院',
        '', text)

    text = process_medical_record_titles(text)

    # 删除人名等敏感信息...（其余的清理代码保持不变）
    names_to_delete = [
        "高梅", "侯应龙", "田秀青", "胡和生", "闫素华", "赵玉杰", "李建", "王清",
        "王同成", "曲海燕", "陈明友", "邢启崇", "李国华", "王晓军", "穆伟", "姚玉才",
        "史新华", "薛梅", "任满意", "王奖荣", "赵学强", "王晔", "郭玲", "张勇",
        "贾晓萌", "王中素", "丁文渊", "李佳曼", "殷洁", "马丽平", "徐振兴", "王聪",
        "张玉娇", "施钰根", "王哗", "蔡卫东", "祝鹏举", "王蔚宗", "陈敏", "王中阳",
        "梁敏", "陈芳芳", "厉泉", "路平", "雷印胜", "张歆杰", "孔中政", "王曦敏",
        "张沛", "刘素兰", "董杰", "董然", "王广丽", "孙丰艳", "程洲", "曾庆师",
        "李政义", "庞涛", "葛五平", "曲倩倩", "李群", "吴摘", "刘青兰", "王艺",
        "张念苦", "盛玉瑞", "韩鹏熙", "刘家皓", "孙菁祥", "王均英", "刘亮", "许祎帆",
        "赵顺德", "皮亚文", "杨古福", "许佛帆", "宋歌声", "王雨欣", "盛华强", "程论",
        "战海宇", "仇海燕", "邓凯", "徐晨", "刘文", "郭宇", "李克建", "歌声", "李刚",
        "智柯宇", "宫凯翔", "刘阳", "添钰", "于洪存", "reporter", "杨志强", "陈金明",
        "张有鑫", "许祎", "刘卅", "玉瑞", "孙艳", "王锐", "魏令珍", "刘芳", "王端",
        "刘珊", "耿海洋", "李美霖", "王大伟", "何蓉", "李晴晴", "刘炎晓", "张明明",
        "高配霞", "郑飞", "刘卅年", "谭经论", "谭结法", "张众苦", "姜舒", "薛祥余",
        "苑呈秀", "吴星臣", "刘玉杰", "杨芸菲", "董栋", "胡莉", "李开科", "刘李兰",
        "艺王", "影信！", "崔凤至", "曲德璃", "影家色", "杨克粥", "刘珊州", "曲德离",
        "盛玉端", "徐龙侠", "岳慧鑫", "程治", "雅洒好", "杨津", "常书林", "滕涂",
        "刘珊珊", "吴情", "王与英", "赵泓宇", "丁伟", "盛王瑞", "曲德",
        "段晓菲", "矫秉轩", "葛亚平", "双 杨双", "常欢", "刘生", "李敏",
        "杨古邓", "于丽丽", "吴 摘", "崔俊杰", "刘嵩兰", "王化与英", "董 杰", "左法",
        "谭结论", "宋谢", "李欣", "王克东", "储风莲", "程洒", "陈中奇", "杨克邓",
        "王钧英", "郭玉霖", "乔婷婷", "素兰", "子 歌", "王为为", "张晓燕", "刘素",
        "侯雷雷", "杨洁", "郑颖颖", "程沟", "贾静", "贾为", "王奖呆", "吴诺",
        "李孝冬", "孟涵", "葛五", "王姣", "文们州", "登洒好", "赵强", "董 然", "王新怡",
        "王晓文", "刘心慧", "杨双", "杨洁", "周海", "张怡", "张岔知", "齐淑娜", "高吉燕",
        "孟习文", "贾文静", "任万青", "萧 不", "与英", "化与英", "吴辆", "潭结法", "引到##",
        "谭法", "漂结法", "浑茫法", "杨艺鸣", "付俊", "大伟", "子小 王", "盛 玉端", "王瑞 盛",
        "董 木", "刘晨", "郭苗苗", "许神帆", "马建飞", "欧好迪", "中凡", "孙羊艳", "谭结讼", "张佩闹", "古#", "子孙",
        "孙焱桐", "孙丰色", "珊/", "王 艺", "文州水", "徐瑜", "闫洪宇", "马振申", "谁洒好", "祎帆", "盛 王瑞", "杨志粥",
        "孙一诺", "刘明", "张 张／付", "刘附州", "商克强", "许佛", "吴尚", "吕杰", "韦帆", "韩明丽", "洪宇", "王瑞",
        "葛血平",
        "杨珊", "于梦雨", "刘萌萌", "邵春龙", "隋美娇", "谭江", "军江法"
    ]

    for name in names_to_delete:
        if name:
            text = re.sub(name, '', text)

    # 提取门诊号
    outpatient_number = None
    outpatient_match = re.search(r'门诊号[：:](.*?)(?=出院记录|死亡记录|$)', text)
    if outpatient_match:
        outpatient_number = clean_extracted_text(outpatient_match.group(1))
        # 清理提取结果：只保留纯数字部分
        outpatient_number = ''.join(filter(lambda x: x.isalnum(), outpatient_number))

        # 如果最终结果为空字符串，则置为 None
        if not outpatient_number:
            outpatient_number = None

    # 提取的敏感信息
    extracted_info = {
        '姓名': None,
        '科室': None,
        '住院号': hospital_number,
        '门诊号': outpatient_number  # 新增门诊号
    }

    # 删除完整的表头字段
    if hospital_number:
        # 使用re.escape确保特殊字符被正确转义
        escaped_hospital_number = re.escape(hospital_number)
        patterns = [
            rf'姓名[：:][^：:]*?科室[：:][^：:]*?住院号[：:]{escaped_hospital_number}(?:门诊号[：:][^：:]*?)?(?=\S|$)',
            rf'姓名[：:][^：:]*?科室[：:][^：:]*?住院号[：:]{escaped_hospital_number}(?=\S|$)'
        ]
        # 在删除表头前先提取姓名和科室信息
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                header_text = match.group(0)
                # 提取姓名
                name_match = re.search(r'姓名[：:]([^：:]*?)(?=科室[：:]|住院号[：:])', header_text)
                if name_match:
                    extracted_info['姓名'] = name_match.group(1).strip()

                # 提取所有科室（处理多个科室的情况）
                dept_matches = re.findall(r'科室[：:]([^：:]*?)(?=姓名[：:]|住院号[：:]|科室[：:]|$)', header_text)
                if dept_matches:
                    # 用分号连接科室名称
                    extracted_info['科室'] = ";".join(dept.strip() for dept in dept_matches)

                # 删除整个表头
                text = re.sub(pattern, '', text)

    # 单独删除敏感字段
    for field, value in extracted_info.items():
        if value:
            # 删除"字段名:字段值"格式的出现
            field_pattern = rf'{field}[：:]{re.escape(value)}'
            text = re.sub(field_pattern, '', text)

            # 删除单独出现的字段值
            text = re.sub(re.escape(value), '', text)

    # 删除敏感字段时增加姓名处理
    if extracted_info['姓名']:
        field_pattern = rf"姓名[：:]{re.escape(extracted_info['姓名'])}"
        text = re.sub(field_pattern, '', text)

        # 删除单独出现的姓名值
        text = re.sub(re.escape(extracted_info['姓名']), '', text)

    # 删除敏感字段时增加门诊号处理
    if outpatient_number:
        # 删除"门诊号:值"的格式
        field_pattern = rf'门诊号[：:]{re.escape(outpatient_number)}'
        text = re.sub(field_pattern, '', text)

        # 删除单独出现的门诊号值
        text = re.sub(re.escape(outpatient_number), '', text)

    # 删除出院号
    if hospital_number:
        # 删除完整匹配 "出院号:值" 或直接出现的值
        hospital_number_1 = "ZY" + hospital_number[2:]
        field_pattern_1 = rf'住院号[：:]{re.escape(hospital_number)}'
        field_pattern_2 = rf'住院号[：:]{re.escape(hospital_number_1)}'
        text = re.sub(field_pattern_1, '', text)
        text = re.sub(field_pattern_2, '', text)
        text = re.sub(re.escape(hospital_number), '', text)
        text = re.sub(re.escape(hospital_number_1), '', text)

    # 删除已提取的科室字段
    if extracted_info['科室']:
        # 拆分所有提取的科室名称
        department_list = extracted_info['科室'].split(";")
        for department in department_list:
            # 构造匹配具体科室的固定字段，例如 "科室：内科"
            specific_pattern = rf'科室[：:]{re.escape(department.strip())}'
            # 删除该科室字段
            text = re.sub(specific_pattern, '', text)
            text = re.sub(re.escape(department), '', text)

        # # 处理 OCR 识别不完全的情况 - 生成部分匹配
        # if len(hospital_number) >= 10:  # 假设号码长度 >= 10 才处理
        #     # 生成所有可能的连续子串（至少 10 位长）
        #     for start in range(len(hospital_number) - 9):  # 开始位置
        #         for length in range(10, len(hospital_number) - start + 1):  # 子串长度至少为 10
        #             partial_number = hospital_number[start:start + length]  # 提取子串
        #             # 删除可能的 "出院号:部分值" 和 "部分值"
        #             field_pattern_partial = rf'住院号[：:]{re.escape(partial_number)}'
        #             text = re.sub(field_pattern_partial, '', text)
        #             text = re.sub(re.escape(partial_number), '', text)

    # 删除页码
    text = re.sub(r'第\d+页', '', text)
    text = re.sub('0003585944', '', text)
    text = re.sub('0005027345', '', text)
    text = re.sub('0005014099', '', text)
    text = re.sub('（示例病历已移除，请使用经授权的脱敏数据）', '', text)
    text = re.sub(r'门诊号：0005014099', '', text)
    text = re.sub(r'科室：中医科2组', '', text)
    text = re.sub(r'0002886506门诊号：', '', text)
    text = re.sub('0002886506', '', text)
    # 统一一些可能的变体格式
    text = text.replace('婚育史', '婚姻史')  # 统一使用婚姻史
    text = text.replace('婚言史', '婚姻史')  # 统一使用婚姻史

    # 返回清理后的文本和提取的敏感信息
    return text, extracted_info


def process_word_document(file_path):
    """
    处理单个Word文档并返回提取的数据
    """
    try:
        # 读取Word文档
        doc = Document(file_path)

        # 存储所有文本
        all_text = ""

        # 遍历文档中的每个段落并合并文本
        for paragraph in doc.paragraphs:
            all_text += paragraph.text

        # 提取住院号 - 允许字母和数字组合
        hospital_number = None
        header_match = re.search(r'姓名：.*?科室：.*?住院号：([A-Za-z0-9]+)', all_text)
        if header_match:
            hospital_number = header_match.group(1)

        # 校正 OCR 错误：将以 "2Y" 开头的住院号替换为 "ZY"（特定条件下修正）
        if hospital_number.startswith("2Y"):
            hospital_number = "ZY" + hospital_number[2:]

        # # 获取病案标识（文件名）
        # case_id = os.path.basename(file_path).split('.')[0]

        # 获取病案标识（取文件名前14位）
        case_id = os.path.basename(file_path).split('.')[0][:14]

        # 清理并处理文本，同时获取提取的敏感信息
        cleaned_text, sensitive_info = clean_text(all_text, hospital_number)

        # 提取字段
        data_dict = extract_fields(cleaned_text)

        # 添加病案标识和住院号
        data_dict['病案标识'] = case_id
        data_dict['住院号'] = hospital_number if hospital_number else ''

        # 安全检查：确保敏感信息不会出现在其他字段中
        for field_name, field_value in data_dict.items():
            if field_name not in ['病案标识', '住院号'] and field_value:
                for info_type, info_value in sensitive_info.items():
                    if info_value and info_value in field_value:
                        # 找到泄露的敏感信息，进行替换
                        data_dict[field_name] = field_value.replace(info_value, f"[{info_type}已脱敏]")

        return data_dict

    except Exception as e:
        print(f"处理文件 {file_path} 时发生错误: {str(e)}")
        return None


def main():
    try:
        # 设置输入输出路径
        input_directory = "/opt/lcl/OCR/PaddleOCR-main/output/structure"  # 替换为您的输入文件夹路径
        output_excel = "6186.xlsx"

        # 获取所有Word文件
        word_files = find_all_word_files(input_directory)
        print(f"找到 {len(word_files)} 个Word文件")

        # 设置进程数（根据CPU核心数）
        num_processes = os.cpu_count()

        # 使用进度条显示处理进度
        all_results = []
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            # 将文件列表分成多个批次
            batch_size = max(1, len(word_files) // num_processes)
            batches = [word_files[i:i + batch_size] for i in range(0, len(word_files), batch_size)]

            # 使用tqdm显示进度
            futures = list(tqdm(executor.map(process_batch, batches),
                                total=len(batches),
                                desc="Processing files"))

            # 收集所有结果
            for batch_result in futures:
                all_results.extend(batch_result)

        # 定义字段的顺序，包含新增字段
        columns_order = [
            '病案标识', '住院号',
            '主诉', '现病史', '既往史', '个人史', '婚姻史', '家族史',
            '入院情况', '入院诊断', '诊疗经过', '病程记录',
            '手术名称', '手术经过', '术中诊断', # 添加手术相关字段
            '影像学意见', '超声提示', '超声印象',  # 添加新增的报告单字段
            '出院诊断'
        ]

        # 创建DataFrame并保存到Excel
        df = pd.DataFrame(all_results)

        # 确保所有列都存在
        for col in columns_order:
            if col not in df.columns:
                df[col] = ''

        # 重新排序列
        df = df[columns_order]

        # 处理出院诊断列，将空格替换为换行符并清理连续换行符
        if '出院诊断' in df.columns:
            def clean_newlines(text):
                if not isinstance(text, str):
                    return text
                # 先将空格替换为换行符
                text = text.replace(' ', '\n')
                # 清理连续的换行符，只保留一个
                text = re.sub(r'\n+', '\n', text)
                # 清理前后的换行符
                return text.strip()

            df['出院诊断'] = df['出院诊断'].apply(clean_newlines)

        # 简化的Excel保存逻辑
        df.to_excel(output_excel, index=False)
        print(f"所有数据已成功保存到: {output_excel}")

        #保存为 JSON
        df = df.where(pd.notnull(df), None)
        json_path = output_excel.replace('.xlsx', '.json')
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=4)
        print(f"JSON 文件已保存：{json_path}")

    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        return None


def process_batch(file_paths):
    """
    批量处理Word文档
    """
    results = []
    for file_path in file_paths:
        result = process_word_document(file_path)
        if result:
            results.append(result)
    return results


if __name__ == "__main__":
    # 设置GPU设备（如果可用）
    if paddle.device.is_compiled_with_cuda():
        paddle.device.set_device("gpu:0")
        print("Using GPU:", paddle.get_cudnn_version())
    else:
        print("Using CPU")

    main()
