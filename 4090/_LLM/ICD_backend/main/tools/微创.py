import json
import os
from functools import lru_cache

# 手术目录 JSON 文件路径
_SURGERY_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "手术目录.json")


@lru_cache(maxsize=1)
def load_surgery_catalog():
    """
    加载手术目录 JSON 文件
    :return: dict, key 为手术名称, value 为 "四级" 或 "微创"
    """
    with open(_SURGERY_CATALOG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def query_surgery_level(surgery_names):
    """
    查询手术列表中每个手术是否为四级或微创。
    只查询其它编码的手术，主手术不需要传入。

    :param surgery_names: list[str], 手术名称列表
    :return: list[dict], 每个元素包含 'is_level4' 和 'is_minimally_invasive' 两个字段
             值为 "是" 或 "-"
    """
    if not surgery_names:
        return []

    catalog = load_surgery_catalog()
    results = []
    for name in surgery_names:
        level = catalog.get(name, None)
        is_level4 = "是" if level == "四级" else "-"
        is_minimally_invasive = "是" if level == "微创" else "-"
        results.append({
            'is_level4': is_level4,
            'is_minimally_invasive': is_minimally_invasive
        })
    return results
