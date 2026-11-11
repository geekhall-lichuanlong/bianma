import json
from functools import lru_cache
from pathlib import Path

PROMPT_FILE = Path(__file__).resolve().parent / "disease_prompt.json"


@lru_cache(maxsize=1)
def _load_prompts():
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _build_content(kwargs):
    if not isinstance(kwargs, dict):
        return ""
    lines = []
    for key, value in kwargs.items():
        lines.append(f"{key}:{'' if value is None else value}")
    return "\n".join(lines) + ("\n" if lines else "")


def get_prompt(prompt_name, kwargs):
    data = _load_prompts()
    if prompt_name not in data:
        raise ValueError(f"Prompt '{prompt_name}' not found in {PROMPT_FILE}")
    return _build_content(kwargs)


def get_prompt_agent6(prompt_name, kwargs):
    data = _load_prompts()
    if prompt_name not in data:
        raise ValueError(f"Prompt '{prompt_name}' not found in {PROMPT_FILE}")

    if not isinstance(kwargs, dict):
        return "待筛查的疾病列表："

    items = list(kwargs.items())
    lines = []
    for key, value in items[:-1]:
        lines.append(f"{key}:{'' if value is None else value}")
    content = "\n".join(lines)
    if content:
        content += "\n"
    disease_list = kwargs.get('待筛查的疾病列表') or []
    if not isinstance(disease_list, (list, tuple)):
        disease_list = [disease_list]
    content += "待筛查的疾病列表："
    content += ",".join(map(str, disease_list))
    return content


if __name__ == "__main__":
    test_prompt = get_prompt("disease_standardized", {
        "病案标识号": "12345",
        "出院诊断": "高血压",
        "现病史": "无明显症状",
    })
    print(test_prompt)
