"""MCC/CC 并发症查询工具"""

import json
from pathlib import Path

JSON_FILE = Path(__file__).parent / "MCC_CC.json"

_lookup = None


def _load():
    global _lookup
    if _lookup is None:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            _lookup = json.load(f)
    return _lookup


def query(name):
    """精确查询疾病名称，返回 "MCC" / "CC"，未找到返回空字符串"""
    if not name:
        return ""
    lookup = _load()
    return lookup.get(name.strip(), "")


def fuzzy_query(name):
    """模糊查询，返回匹配列表 [(疾病名称, label), ...]"""
    if not name:
        return []
    lookup = _load()
    return [(k, v) for k, v in lookup.items() if name.strip() in k]
