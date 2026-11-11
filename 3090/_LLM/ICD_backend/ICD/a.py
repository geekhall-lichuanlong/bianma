import re

def _normalize_wall(term: str) -> str:
    t = term.strip()
    # 去掉修饰词
    for prefix in ("广泛",):
        if t.startswith(prefix):
            t = t[len(prefix):]
    return t

def extract_mi_wall(text: str) -> str:
    """
    从出院诊断中提取“急性ST段抬高型心肌梗死(...)”括号内的部位，按规则返回标准化结果。

    规则：
    - 仅取括号内前两个部位（按原始顺序）。
    - 将“广泛前壁”标准化为“前壁”等（当前仅去掉“广泛”前缀）。
    - 如果只有“侧壁”，返回“前壁”。
    - 如果前两个是“前壁”和“侧壁”组合，返回“前侧壁”。
    - 组合时按“去掉各自末尾‘壁’后拼接 + ‘壁’”的方式合成，如“前壁 + 侧壁 => 前侧壁”。

    示例：
    - 急性ST段抬高型心肌梗死(侧壁) => 前壁
    - 急性ST段抬高型心肌梗死(广泛前壁、侧壁) => 前侧壁
    - 急性ST段抬高型心肌梗死(广泛前壁、侧壁、左壁) => 前侧壁
    """
    # 同时匹配全角和半角括号
    m = re.search(r"急性ST段抬高型心肌梗死[（(]([^）)]+)[）)]", text)
    if not m:
        return ""

    inside = m.group(1)
    # 按常见的中文/英文分隔符切分
    parts = re.split(r"[、，,；;\s]+", inside)

    # 标准化并去重（保持顺序）
    terms = []
    seen = set()
    for p in parts:
        if not p:
            continue
        t = _normalize_wall(p)
        if not t:
            continue
        if t not in seen:
            terms.append(t)
            seen.add(t)

    if not terms:
        return ""

    # 仅保留前两个
    terms = terms[:2]

    # 单项特殊规则：只有“侧壁” => “前壁”
    if len(terms) == 1:
        return terms[0]

    # 两项相同则折叠
    if terms[0] == terms[1]:
        return terms[0]

    # 组合：去掉各自末尾“壁”后合并，再补一个“壁”
    def strip_bi(s: str) -> str:
        return s[:-1] if s.endswith("壁") else s

    a, b = terms
    if a.endswith("壁") and b.endswith("壁"):
        return strip_bi(a) + strip_bi(b) + "壁"
    else:
        # 回退：若不以“壁”结尾，直接拼接
        return "".join(terms)


# 用法示例：
if __name__ == "__main__":
    samples = [
        "急性ST段抬高型心肌梗死(左壁)",
        "急性ST段抬高型心肌梗死(广泛前壁、牛壁)",
        "急性ST段抬高型心肌梗死(广泛前壁、侧壁、左壁)",
        "急性ST段抬高型心肌梗死（广泛前壁、侧壁）",  # 全角括号
    ]
    for s in samples:
        print(s, "=>", extract_mi_wall(s))