def get_prompt(prompt_name, kwargs):
    if not isinstance(kwargs, dict):
        return ""
    lines = []
    for key, value in kwargs.items():
        lines.append(f"{key}:{'' if value is None else value}")
    return "\n".join(lines) + ("\n" if lines else "")


if __name__ == "__main__":
    test_prompt = get_prompt("disease_standardized", {
        "病案标识号": "12345",
        "手术名称": "高血压",
        "手术经过": "无",
        "病程记录": "稳定",
    })
    print(test_prompt)
