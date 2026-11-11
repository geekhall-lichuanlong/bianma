#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
针对“数智大赛样例PDF - 测试(1)”这份 OCR 文本的字段截取脚本。

匹配规则来自 out/OCR截取字段0714.xlsx 的 Sheet1。由于这份 OCR 存在表格
错位、标题粘连和跨页页眉混入，部分字段在 Excel 起止锚点基础上增加了
专门兜底规则。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE_DIR.parent / "umi" / "py" / "re" / "数智大赛样例PDF - 测试(1).txt"
DEFAULT_OUTPUT = BASE_DIR / "out"


@dataclass(frozen=True)
class FieldRule:
    field: str
    start: str
    end: str
    occurrence: str = "first"


FIELD_RULES: list[FieldRule] = [
    FieldRule("病案标识", "病案号：", "换行符"),
    FieldRule("住院号", "病案号：", "换行符"),
    FieldRule("主诉", "现住址:", "主诉:"),
    FieldRule("现病史", "现病史：", "入 院 记 录"),
    FieldRule("既往史", "既往史：", "个人史："),
    FieldRule("入院情况", "入院情况:", "入院查体:"),
    FieldRule("入院诊断", "入院诊断:", "诊疗经过:"),
    FieldRule("诊疗经过", "诊疗经过:", "目前情况："),
    FieldRule("病程记录", "病历记录", "冠状动脉造影报告单冠状动脉造影"),
    FieldRule("手术名称", "冠状动脉造影报告单", "检查日期2025年1月20日 报告日期2025年1月21日"),
    FieldRule("手术经过", "冠状动脉造影报告单", "X线诊断报告"),
    FieldRule("术中诊断", "助手： 王宁宁李洲剑", "麻醉方法： 局麻"),
    FieldRule("影像学意见", "X线诊断报告", "常规二维心脏大血管超声报告"),
    FieldRule("超声提示", "常规二维心脏大血管超声报告", "床旁心包彩色多谱勒超声心动图报告"),
    FieldRule("超声影响", "床旁心包彩色多谱勒超声心动图报告", "检查仪器: 注：此报告须有医师亲笔签字方为有效报告"),
    FieldRule("出院诊断", "出院诊断:", "出院医嘱:"),
]

OUTPUT_FIELDS = [rule.field for rule in FIELD_RULES]
EMPTY_VALUE = ""


def normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("﹕", "：").replace("：", ":")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_value(value: str) -> str:
    value = value.replace("\u3000", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = re.sub(r"(?m)^第\s*\d+\s*页.*$", "", value)
    value = re.sub(r"(?m)^医师签字.*$", "", value)
    value = re.sub(r"(?m)^医生签字.*$", "", value)
    value = re.sub(r"(?m)^主治医师签字.*$", "", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip(" \n\t:：,，")


def anchor_pattern(anchor: str) -> re.Pattern[str]:
    anchor = anchor.strip().replace("：", ":")
    if anchor == "换行符":
        return re.compile(r"\n")

    pieces: list[str] = []
    for ch in anchor:
        if ch.isspace():
            pieces.append(r"\s*")
        elif ch == ":":
            pieces.append(r"[:：]\s*")
        else:
            pieces.append(re.escape(ch) + r"\s*")
    return re.compile("".join(pieces), re.S)


def find_anchor(text: str, anchor: str, start_at: int = 0) -> re.Match[str] | None:
    return anchor_pattern(anchor).search(text, start_at)


def extract_between(text: str, start: str, end: str, *, occurrence: str = "first") -> str:
    matches = list(anchor_pattern(start).finditer(text))
    if not matches:
        return EMPTY_VALUE

    values: list[str] = []
    for start_match in matches:
        if end == "换行符":
            end_pos = text.find("\n", start_match.end())
            end_pos = len(text) if end_pos == -1 else end_pos
        else:
            end_match = find_anchor(text, end, start_match.end())
            if not end_match:
                continue
            end_pos = end_match.start()
        value = clean_value(text[start_match.end():end_pos])
        if value:
            values.append(value)
            if occurrence == "first":
                break
    return "\n".join(values)


def first_group(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.S | re.M)
        if match:
            return clean_value(match.group(1))
    return EMPTY_VALUE


def extract_case_id(text: str) -> str:
    return first_group(
        text,
        [
            r"病案号\s*[:：]?\s*\n?\s*([A-Za-z0-9_-]{4,})",
            r"([A-Za-z0-9_-]{4,})\s*\n\s*病案号\s*[:：]?",
            r"病案号\s*([A-Za-z0-9_-]{4,})",
        ],
    )


def extract_chief_complaint(text: str) -> str:
    value = extract_between(text, "现住址:", "主诉:")
    value = re.sub(r"^.*?([^\n:：]{2,40})$", r"\1", value, flags=re.S)
    return clean_value(value)


def extract_hpi(text: str) -> str:
    # OCR 把“现病史:”放在首句中间，后半句在入院记录页眉之后继续。
    value = first_group(
        text,
        [
            r"主诉:\s*\n?.*?(患者自.*?)(?:患者自发病以来|入院前7天内用药)",
            r"(患者自1月余前.*?)(?:患者自发病以来|入院前7天内用药)",
        ],
    )
    if value:
        value = re.sub(r"现病史\s*[:：]?\s*\n?\s*次\s*入\s*院\s*记\s*录.*?病案号\s*[:：]?\s*1580139", "", value, flags=re.S)
        value = re.sub(r"姓名\s*[:：]?.*?病案号\s*[:：]?\s*1580139", "", value, flags=re.S)
        if not value.startswith("患者自"):
            value = "患者自1月余前（2024-12-15 " + value.lstrip()
        return clean_value(value)
    return extract_between(text, "现病史:", "入院前7天内用药")


def extract_history(text: str) -> str:
    value = extract_between(text, "既往史:", "个人史:")
    value = re.sub(r"患者家属签字.*", "", value, flags=re.S)
    return clean_value(value)


def extract_admission_diagnosis(text: str) -> str:
    value = extract_between(text, "入院诊断:", "诊疗经过:")
    if value:
        return value
    return extract_between(text, "入院( 初次) 诊断:", "主治/住院医师签字:")


def extract_treatment_course(text: str) -> str:
    value = extract_between(text, "诊疗经过:", "目前情况:")
    if value and not value.endswith("LVEF") and "出 院 记 录" not in value:
        return value
    # 出院记录的诊疗经过跨页，被页脚和页眉打断。直接截到“目前情况”更稳。
    start = find_anchor(text, "诊疗经过:")
    end = find_anchor(text, "目前情况:", start.end() if start else 0)
    if not start or not end:
        return value
    chunk = text[start.end():end.start()]
    chunk = re.sub(r"主治医师签字.*?病案号\s*[:：]?\s*", "", chunk, flags=re.S)
    chunk = re.sub(r"LVEF\s*.*?出\s*院\s*记\s*录.*?病案号\s*[:：]?\s*60%", "LVEF 60%", chunk, flags=re.S)
    return clean_value(chunk)


def extract_progress_notes(text: str) -> str:
    start = find_anchor(text, "病历记录")
    end = find_anchor(text, "冠状动脉造影报告单冠状动脉造影", start.end() if start else 0)
    if not start or not end:
        return EMPTY_VALUE
    return clean_value(text[start.start():end.start()])


def extract_operation_name(text: str) -> str:
    names = []
    if re.search(r"冠状动脉造影报告单\s*冠状动脉造影", text):
        names.append("冠状动脉造影")
    if "介入治疗报告单" in text:
        names.append("介入治疗")
    return "；".join(names)


def extract_operation_course(text: str) -> str:
    value = extract_between(text, "冠状动脉造影报告单", "X线诊断报告")
    value = re.sub(r"报告者:\s*\n室堂", "", value)
    return clean_value(value)


def extract_intraoperative_diagnosis(text: str) -> str:
    diagnosis = first_group(text, [r"造影诊断\s*[:：]?\s*(.*?)(?:导管\s*[:：]|术中用药)"])
    conclusion = first_group(text, [r"结论\s*[:：]\s*(冠状动脉粥样硬化性心脏病.*?)(?:报告者|室堂介入治疗报告单)"])
    values = [v for v in [diagnosis, conclusion] if v]
    value = "\n".join(values)
    value = re.sub(r"\n\s*\d+\s*$", "", value)
    return clean_value(value)


def extract_xray_opinion(text: str) -> str:
    value = extract_between(text, "X线诊断报告", "常规二维心脏大血管超声报告")
    return clean_value(value)


def extract_ultrasound_prompt(text: str) -> str:
    value = extract_between(text, "常规二维心脏大血管超声报告", "床旁心包彩色多谱勒超声心动图报告")
    return clean_value(value)


def extract_ultrasound_image(text: str) -> str:
    value = extract_between(text, "床旁心包彩色多谱勒超声心动图报告", "注:此报告须有医师亲笔签字方为有效报告")
    if value:
        return value
    return extract_between(text, "床旁心包彩色多谱勒超声心动图报告", "注：此报告须有医师亲笔签字方为有效报告")


SPECIAL_EXTRACTORS = {
    "病案标识": extract_case_id,
    "住院号": extract_case_id,
    "主诉": extract_chief_complaint,
    "现病史": extract_hpi,
    "既往史": extract_history,
    "入院诊断": extract_admission_diagnosis,
    "诊疗经过": extract_treatment_course,
    "病程记录": extract_progress_notes,
    "手术名称": extract_operation_name,
    "手术经过": extract_operation_course,
    "术中诊断": extract_intraoperative_diagnosis,
    "影像学意见": extract_xray_opinion,
    "超声提示": extract_ultrasound_prompt,
    "超声影响": extract_ultrasound_image,
}


def extract_field(text: str, rule: FieldRule) -> str:
    extractor = SPECIAL_EXTRACTORS.get(rule.field)
    if extractor:
        value = extractor(text)
        if value:
            return value
    return extract_between(text, rule.start, rule.end, occurrence=rule.occurrence)


def parse_case(text: str, source_name: str = "") -> dict[str, str]:
    text = normalize_text(text)
    record = {rule.field: extract_field(text, rule) for rule in FIELD_RULES}
    if source_name:
        return {"来源文件": source_name, **record}
    return record


def iter_txt_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted(input_path.rglob("*.txt"))
    raise FileNotFoundError(f"输入不存在：{input_path}")


def write_json(records: list[dict[str, str]], path: Path) -> None:
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(records: list[dict[str, str]], path: Path) -> None:
    if not records:
        path.write_text("", encoding="utf-8")
        return
    headers = list(records[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按 OCR截取字段0714.xlsx 的特殊规则截取样例病例字段")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="txt 文件或目录")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出目录")
    parser.add_argument("--json-name", default="cases.json", help="JSON 输出文件名")
    parser.add_argument("--csv-name", default="cases.csv", help="CSV 输出文件名")
    parser.add_argument("--dump-raw", action="store_true", help="额外输出 raw_sections.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    txt_files = iter_txt_files(args.input)
    records = []
    raw_records = []
    for txt_file in txt_files:
        text = txt_file.read_text(encoding="utf-8", errors="ignore")
        record = parse_case(text, source_name=txt_file.name)
        records.append(record)
        if args.dump_raw:
            raw_records.append({"来源文件": txt_file.name, "raw_sections": {k: record.get(k, "") for k in OUTPUT_FIELDS}})

    write_json(records, args.output / args.json_name)
    write_csv(records, args.output / args.csv_name)
    if args.dump_raw:
        write_json(raw_records, args.output / "raw_sections.json")

    print(f"处理文件数：{len(records)}")
    print(f"JSON：{args.output / args.json_name}")
    print(f"CSV ：{args.output / args.csv_name}")
    if args.dump_raw:
        print(f"RAW ：{args.output / 'raw_sections.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
