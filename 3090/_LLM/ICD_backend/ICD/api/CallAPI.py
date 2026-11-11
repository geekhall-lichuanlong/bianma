import json
import requests

REQUEST_TIMEOUT = (10, 200)


def _error_chunk(message):
    return json.dumps({"error": message}, ensure_ascii=False) + "\n"


def call_api_stream(content, model, url, agent_label="none"):
    if not url or url == "none":
        yield _error_chunk("API调用失败，未配置模型服务地址。")
        return
    if not model or model == "none":
        yield _error_chunk("API调用失败，未配置模型名称。")
        return

    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": content or ""
            }
        ],
        "stream": True,
        "max_tokens": 4096
    }
    headers = {"Content-Type": "application/json"}

    print("Debug - Calling API with:")
    print(f"  URL: {url}")
    print(f"  Model: {model}")
    print(f"  Content length: {len(content) if content else 0}")
    print(f"  Agent label: {agent_label}")

    try:
        with requests.post(
            url,
            headers=headers,
            json=data,
            stream=True,
            timeout=REQUEST_TIMEOUT,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                decoded_line = line.strip()
                if not decoded_line.startswith("data:"):
                    continue

                json_data = decoded_line[5:].strip()
                if json_data == "[DONE]":
                    break

                try:
                    response_data = json.loads(json_data)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}; line={decoded_line}")
                    continue

                choices = response_data.get("choices") or []
                if not choices:
                    continue

                if choices[0].get("finish_reason") == "length":
                    yield _error_chunk("模型输出达到长度上限，本次输出可能不完整，请核对结果。")
                    return

                delta = choices[0].get("delta") or {}
                result_content = delta.get("content") or ""
                reasoning_content = delta.get("reasoning_content") or ""

                yield json.dumps({
                    "model": model,
                    "agent_label": agent_label,
                    "message": {
                        "content": result_content,
                        "reasoning_content": reasoning_content
                    },
                    "next_agent": 0,
                    "next_agent_url": "",
                    "usage": 0
                }, ensure_ascii=False) + "\n"
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e!r}")
        response = getattr(e, "response", None)
        if response is not None:
            try:
                print(f"Error response body: {response.text}")
            except Exception:
                print("Could not read error response body")
        yield _error_chunk("API调用失败，请检查网络或API配置。")
