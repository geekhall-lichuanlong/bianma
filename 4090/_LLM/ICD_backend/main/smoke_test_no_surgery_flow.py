#!/usr/bin/env python3
import json

import requests


case = {
    "病案标识号": "NO_SURGERY_FLOW_CHECK",
    "手术名称": "",
    "手术经过": "",
    "主诉": "上腹不适",
    "入院诊断": "上腹痛",
    "诊疗经过": "入院后行胃镜检查及胃黏膜活组织检查。",
    "出院诊断": "慢性胃炎",
    "现病史": "反复上腹不适。",
    "病程记录": "完善胃镜检查并取活检。",
}

payload = {
    "messages": [{"role": "user", "content": json.dumps(case, ensure_ascii=False)}]
}

events = []
with requests.post(
    "http://127.0.0.1:6000/qwen3/surgeries_diagnosis",
    json=payload,
    stream=True,
    timeout=(10, 240),
) as response:
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if line:
            events.append(json.loads(line))

status_agents = [
    event.get("agent_name")
    for event in events
    if event.get("type") == "agent_status"
]
content_by_agent = {}
for event in events:
    content = (event.get("message") or {}).get("content") or ""
    if content:
        name = event.get("agent_name", "")
        content_by_agent[name] = content_by_agent.get(name, "") + content

assert "无手术名称智能体(无手术经过)" in status_agents, status_agents
assert "筛查智能体(无手术经过)" in status_agents, status_agents
assert content_by_agent.get("筛查智能体(无手术经过)"), content_by_agent
assert content_by_agent.get("表格展示"), content_by_agent

print("status_agents:", json.dumps(status_agents, ensure_ascii=False))
for name, content in content_by_agent.items():
    print(name + ":", content[:500].replace("\n", " "))
print("no-surgery screening smoke test passed")
