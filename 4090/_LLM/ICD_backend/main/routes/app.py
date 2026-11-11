from flask import Flask, Response, jsonify, request, stream_with_context
import json

from routes.surgery.SurgeryApp import get_surgery_app
from parse import get_flask_url


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.register_blueprint(get_surgery_app(), url_prefix='/surgery')

url = get_flask_url()


def _get_request_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, None, (jsonify({"error": "Invalid request format"}), 400)

    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return None, None, (jsonify({"error": "Invalid request format"}), 400)

    first = messages[0]
    if not isinstance(first, dict) or "content" not in first:
        return None, None, (jsonify({"error": "Invalid request format"}), 400)

    return data, first.get("content") or "", None


def _parse_content(content):
    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        return {}
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


@app.route('/qwen3/surgeries_diagnosis', methods=['POST'])
def surgery_diagnosis():
    try:
        data, content_raw, error = _get_request_data()
        if error:
            return error

        content = _parse_content(content_raw)
        if not content:
            return jsonify({"error": "Invalid request format"}), 400

        surgery_name = content.get("手术名称") or ""
        surgery_course = content.get("手术经过") or ""

        if surgery_name == "" or surgery_course == "":
            from icd.GetICD_noSurgery import get_icd
        else:
            from icd.GetICD import get_icd

        return Response(
            stream_with_context(get_icd(data)),
            content_type='application/json'
        )
    except Exception as e:
        print(f"诊断处理错误: {e}")
        error_response = {
            "type": "error",
            "status": "error",
            "message": f"处理失败: {str(e)}"
        }
        return Response(
            json.dumps(error_response, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8',
            status=500
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
