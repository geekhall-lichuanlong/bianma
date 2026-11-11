from tools.agent_timing import timed_agent
import requests
import json

from prompts.GetPrompt import get_prompt, get_prompt_agent6
from parse import get_flask_url, get_output_dir

flask_url = get_flask_url()
url = {
    "disease_standardized": f"{flask_url}disease_standardized",
    "disease_potential_extract": f"{flask_url}disease_potential_extract",
    "disease_potential_standardized": f"{flask_url}disease_potential_standardized",
    "disease_main_diagnosis": f"{flask_url}disease_main_diagnosis",
    "disease_screening": f"{flask_url}disease_screening",
    "disease_bingli": f"{flask_url}disease_bingli",
    "disease_external": f"{flask_url}disease_external",
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

    if agent_name == "疾病筛查智能体":
        prompt_content = get_prompt_agent6(agent_label, kwargs)
    else:
        prompt_content = get_prompt(agent_label, kwargs)

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
    agent_flask_url = f"{get_flask_url()}/disease/{agent_label}"
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
        "疾病标准化智能体": "disease_standardized",
        "疾病排序智能体": "disease_main_diagnosis",
        "疾病筛查智能体": "disease_screening",
        "疾病二次标准化智能体": "disease_standardized",

        "发现潜在疾病智能体": "disease_potential_extract",
        "潜在疾病标准化智能体": "disease_potential_standardized",
        "判断有无潜在疾病智能体": "disease_potential_verify",

        "疾病病理智能体": "disease_bingli",
        "疾病外因智能体": "disease_external"

        
    }

    return agent_dict.get(agent_name, "unknown_agent")

def __get_agent_output_label(agent_name):
    '''
    获取智能体输出标签
    '''
    agent_output_label_dict = {
        "疾病标准化智能体" : "出院诊断标准化",
        "疾病排序智能体": "排序",
        "疾病筛查智能体": "筛查",
        "疾病二次标准化智能体": "出院诊断标准化",
        
        "发现潜在疾病智能体": "发现潜在疾病",
        "排除的低概率疾病智能体": "排除的低概率疾病",
        "判断有无潜在疾病智能体": "有无潜在疾病",

        "疾病病理智能体": "病理",
        "疾病外因智能体": "外因",
    }

    return agent_output_label_dict.get(agent_name, "unknown_agent")

def replace(agent_name):
    '''
    获取智能体输出标签
    '''
    agent_output_label_dict = {
        "疾病标准化智能体" : "疾病1号智能体",
        "疾病排序智能体": "疾病5号智能体5",
        "疾病筛查智能体": "疾病6号智能体",
        "疾病二次标准化智能体": "疾病二次标准化智能体",

        "发现潜在疾病智能体": "疾病3号智能体",
        "潜在疾病标准化智能体": "疾病4号智能体",
        "判断有无潜在疾病智能体": "疾病2号智能体"
    }

    return agent_output_label_dict.get(agent_name, "unknown_agent")
