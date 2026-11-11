from flask import Flask, Response, jsonify, request, stream_with_context
import json

from routes.disease.DiseaseApp import get_disease_app
from routes.surgery.SurgeryApp import get_surgery_app
from parse import get_flask_url


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.register_blueprint(get_disease_app(), url_prefix='/disease')
app.register_blueprint(get_surgery_app(), url_prefix='/surgery')

url = get_flask_url()


def _get_request_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Invalid request format"}), 400)
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return None, (jsonify({"error": "Invalid request format"}), 400)
    first = messages[0]
    if not isinstance(first, dict) or "content" not in first:
        return None, (jsonify({"error": "Invalid request format"}), 400)
    return data, None


@app.route('/qwen3/diagnosis_qwen', methods=['POST'])
def disease_diagnosis():
    try:
        data, error = _get_request_data()
        if error:
            return error

        from icd.disease.GetICD import get_icd
        return Response(
            stream_with_context(get_icd(data)),
            content_type='application/json'
        )
    except Exception as e:
        print(f"疾病诊断处理错误: {e}")
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
    app.run(host="0.0.0.0", port=5000)
