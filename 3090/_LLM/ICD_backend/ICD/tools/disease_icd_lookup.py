"""国家临床版疾病 ICD 名称/编码校验工具。"""

import json
import re
from pathlib import Path

JSON_FILE = Path(__file__).parent / "disease_icd_lookup.json"

_lookup = None


def _load():
    global _lookup
    if _lookup is None:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            _lookup = json.load(f)
    return _lookup


def _normalize_code(code):
    if code is None:
        return ""
    if isinstance(code, list):
        code = code[0] if code else ""
    code = str(code).strip()
    if not code or code == "无编码":
        return ""
    return re.sub(r"\s+", "", code).upper()
    
SPECIAL_PREFIXES = ("M", "V", "W", "X", "Y")
EXTERNAL_PREFIXES = ("V", "W", "X", "Y")
EXPECTED_PATHOLOGY = "pathology"
EXPECTED_EXTERNAL = "external"


def _same_special_family(source_code, candidate_code):
    """判断两个编码是否属于同一类特殊编码。"""
    if source_code.startswith("M"):
        return candidate_code.startswith("M")

    if source_code.startswith(EXTERNAL_PREFIXES):
        return candidate_code.startswith(EXTERNAL_PREFIXES)

    return False


def is_pathology_code(code):
    """Return whether code is in the ICD-O morphology M80000-M99890 family.

    The behavior suffix may be /0, /1, /2, /3, etc. It is not part of the
    numeric morphology range comparison.
    """
    normalized = _normalize_code(code)
    match = re.fullmatch(r"M(\d{5})/[0-9]", normalized)
    if not match:
        return False
    return 80000 <= int(match.group(1)) <= 99890


def is_external_cause_code(code):
    """Return whether code is in the external-cause range V01-Y98."""
    normalized = _normalize_code(code)
    match = re.match(r"^([VWXY])(\d{2})", normalized)
    if not match:
        return False

    letter = match.group(1)
    number = int(match.group(2))
    if letter == "V":
        return 1 <= number <= 99
    if letter in ("W", "X"):
        return 0 <= number <= 99
    return 0 <= number <= 98


def _matches_expected_type(code, expected_type):
    if expected_type == EXPECTED_PATHOLOGY:
        return is_pathology_code(code)
    if expected_type == EXPECTED_EXTERNAL:
        return is_external_cause_code(code)
    return True


def query(name):
    """按标准疾病名称精确查询，未找到返回 None。"""
    if not name:
        return None
    return _load().get(str(name).strip())

def validate_code(name, icd_code, expected_type=None):
    """
    校验模型输出的疾病名称和 ICD 编码。

    处理规则：
    expected_type="pathology" 时只接受 M80000-M99890 形态学编码；
    expected_type="external" 时只接受 V01-Y98 外因编码。
    名称命中字典但模型类型错误时，优先选择该名称下符合期望类型
    的编码；无法修正时返回空值，防止错误类型进入最终表格。
    """
    name = str(name).strip() if name else ""
    normalized_code = _normalize_code(icd_code)

    if not name:
        return "", ""

    entry = query(name)

    if expected_type in (EXPECTED_PATHOLOGY, EXPECTED_EXTERNAL):
        # 本轮只要求编码类型和范围正确。模型已经给出合法的 M 码或
        # V/W/X/Y 码时必须原样保留，不能因为名称与字典不完全一致
        # 而把正确结果覆盖成未特指兜底编码。
        if normalized_code and _matches_expected_type(normalized_code, expected_type):
            return name, normalized_code

        valid_codes = [
            _normalize_code(code)
            for code in (entry or {}).get("codes", [])
            if _normalize_code(code)
        ]
        expected_codes = [
            code for code in valid_codes
            if _matches_expected_type(code, expected_type)
        ]

        if expected_codes:
            return name, expected_codes[0]

        print(
            f"特殊编码类型校验失败: name={name}, code={normalized_code}, "
            f"expected_type={expected_type}"
        )
        return "", ""

    # 名称未命中时，暂时信任模型给出的特殊编码
    if not entry:
        if normalized_code.startswith(SPECIAL_PREFIXES):
            return name, normalized_code
        return name, "无编码"

    valid_codes = [
        _normalize_code(code)
        for code in entry.get("codes", [])
        if _normalize_code(code)
    ]

    # 名称和编码完全匹配
    if normalized_code and normalized_code in valid_codes:
        return name, normalized_code

    # M/V/W/X/Y 编码不匹配时，优先选择同类编码
    if normalized_code.startswith(SPECIAL_PREFIXES):
        for candidate_code in valid_codes:
            if _same_special_family(normalized_code, candidate_code):
                return name, candidate_code

        # 字典中没有同类编码时，暂时保留模型编码
        return name, normalized_code

    # 普通疾病编码继续使用原来的 primary 回退
    return name, entry.get("primary") or "无编码"
