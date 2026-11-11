from tools.agent_timing import timed_agent
import requests
import json

from prompts.GetPrompt import get_prompt
from parse import get_flask_url, get_output_dir
'''
    目前其中所需内容为：
    {
    "S_standardized": "病案标识号：{}\n手术名称：{}\n手术经过：{}\n病程记录：{}",
    "S_additional": "病案标识号：{}\n手术名称：{}\n手术经过：{}\n病程记录：{}",
    "S_another_coding": "病案标识号：{}\n手术名称：{}\n手术经过：{}\n病程记录：{}",
    "S_sorting": "病案标识号：{}\n手术名称：{}\n手术经过：{}\n病程记录：{}\",
    }

    代码匹配内容已此注释为准
    '''
flask_url = get_flask_url()
url = {
    "S_standardized": f"{flask_url}S_standardized",
    "S_additional": f"{flask_url}S_additional",
    "S_another_coding": f"{flask_url}S_another_coding",
    "S_sorting": f"{flask_url}S_sorting"
}
output_dir = get_output_dir()


def get_agent_output(agent_name, kwargs):
    '''
    获取智能体响应（非流式版本，用于向后兼容）
    '''
    full_content = ""
    for response in get_agent_output_stream(agent_name, kwargs):
        full_content += response.get("message", {}).get("content", "")
    
    # 获取agent输出中的标签
    agent_output_label = __get_agent_output_label(agent_name)
    if agent_output_label == "unknown_agent":
        raise ValueError(f"Unknown agent output label for agent: {agent_name}. Please check the agent name.")
    
    # 将完整内容存储到全局变量中
    full_content = full_content.replace("<think>\n\n</think>\n\n", "")
    
    try:
        if full_content.strip():  # 检查内容是否为空
            content_data = json.loads(full_content)
            if agent_output_label in content_data:
                full_content = content_data[agent_output_label]
            else:
                print(f"Warning: {agent_output_label} not found in response data")
                return full_content
        else:
            print("Warning: full_content is empty")
            return ""
    except json.JSONDecodeError as e:
        print(f"JSON decode error in full_content: {e}, content: {full_content}")
        return full_content  # 返回原始内容而不是抛出异常

    return full_content

@timed_agent
def get_agent_output_stream(agent_name, kwargs):
    '''
    获取智能体响应（流式版本）
    '''
    agent_label = __get_agent_label(agent_name)
    if agent_label == "unknown_agent":
        raise ValueError(f"Unknown agent name: {agent_name}. Please check the agent name.")

    prompt_content = get_prompt(agent_label, kwargs)

    # 先通知前端当前正在调用哪个智能体。content 保持为空，避免上层把状态文本
    # 拼进模型 JSON；前端使用 status_text 单独展示等待状态。
    yield {
        "type": "agent_status",
        "agent_name": agent_name,
        "status": "running",
        "status_text": f"正在调用{agent_name}",
        "message": {
            "content": "",
            "reasoning_content": "",
        },
        "timestamp": "",
    }

    for api_response in __call_agent_api(prompt_content, agent_label):
        if not api_response or not api_response.strip():
            continue
        try:
            response_data = json.loads(api_response)
        except json.JSONDecodeError as e:
            print(f"JSON decode error in api_response: {e}, response: {api_response}")
            yield {
                "type": "agent_response",
                "agent_name": agent_name,
                "raw_response": api_response,
                "error": f"JSON decode error: {str(e)}",
                "timestamp": ""
            }
            continue

        if "error" in response_data and "message" not in response_data:
            yield {
                "type": "agent_response",
                "agent_name": agent_name,
                "raw_response": api_response,
                "error": response_data.get("error", "API调用失败"),
                "timestamp": response_data.get("timestamp", "")
            }
            continue

        yield {
            "type": "agent_response",
            "agent_name": agent_name,
            "raw_response": api_response,
            "message": response_data.get("message", {}),
            "timestamp": response_data.get("timestamp", "")
        }


def __call_agent_api(prompt_content, agent_label):
    '''
    获取智能体响应
    '''
    print(f"Calling agent API: {agent_label}")
    agent_flask_url = f"{get_flask_url()}/surgery/{agent_label}"
    headers = {"Content-Type": "application/json"}
    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt_content or ""
            }
        ]
    }

    try:
        with requests.post(
            agent_flask_url,
            headers=headers,
            json=data,
            timeout=(10, 200),
            stream=True,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                decoded_line = line.strip()
                if not decoded_line:
                    continue
                try:
                    response_data = json.loads(decoded_line)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error in second API response: {e}, line: {decoded_line}")
                    continue

                message = response_data.get("message") or {}
                content = message.get("content") or ""
                reasoning_content = message.get("reasoning_content") or ""

                yield json.dumps({
                    "agent_name": agent_label,
                    "message": {
                        "content": content,
                        "reasoning_content": reasoning_content
                    },
                    "next_agent": 0,
                    "next_agent_url": "",
                    "usage": 0
                }, ensure_ascii=False) + "\n"
    except requests.exceptions.RequestException as e:
        print(f"Error calling {agent_label} API: {e}")
        yield json.dumps({"error": "API调用失败，请检查网络或API配置。"}, ensure_ascii=False) + "\n"


def __get_agent_label(agent_name):
    '''
    获取智能体名称
    '''
    agent_dict = {
        "挖掘智能体(无手术记录)": "no_surgery_name",
        "标准化智能体(无手术记录)": "no_surgery_standardized",
        "另编码智能体(无手术记录)": "surgery_another_coding",
        "筛查智能体(无手术记录)": "no_surgery_screening",
        "手术标准化智能体": "surgery_standardized",
        "提取额外手术智能体": "surgery_additional",
        "另编码智能体": "surgery_another_coding",
        "排序智能体": "surgery_sorting",
        "筛查智能体": "surgery_screening",
        "手术标准化智能体(无手术经过)": "no_surgery_standardized",
        "筛查智能体(无手术经过)": "no_surgery_screening",
        # 64
        '无手术名称智能体(无手术经过)': "no_surgery_name"
    }

    return agent_dict.get(agent_name, "unknown_agent")

def __get_agent_output_label(agent_name):
    '''
    获取智能体输出标签
    '''
    agent_output_label_dict = {
        "手术标准化智能体" : "出院诊断标准化",
        "提取额外手术智能体": "提取额外手术",
        "另编码智能体": "另编码的手术名称",
        "排序智能体": "排序并选择主手术",
        "筛查智能体": "经筛查后的手术列表",
        "手术标准化智能体(无手术经过)":"手术操作列表",
        "筛查智能体(无手术经过)":"经筛查后的手术列表",
        # 64
        '无手术名称智能体(无手术经过)': "手术操作列表"

    }

    return agent_output_label_dict.get(agent_name, "unknown_agent")


def repleace(agent_name):
    
    agent_output_label_dict = {
        "手术标准化智能体" : "手术1号智能体",
        "提取额外手术智能体": "手术2号智能体",
        "另编码智能体": "手术4号智能体",
        "排序智能体": "手术3号智能体",
        "筛查智能体": "手术5号智能体"

    }
    return agent_output_label_dict.get(agent_name, "unknown_agent")
