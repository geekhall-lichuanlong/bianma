from flask import Blueprint, Response, jsonify, request, stream_with_context

from api.CallAPI import call_api_stream
from parse import get_model, get_url


surgery_app = Blueprint('surgery', __name__)


def get_surgery_app():
    return surgery_app


def _extract_content():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Invalid request format"}), 400)

    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return None, (jsonify({"error": "Invalid request format"}), 400)

    first = messages[0]
    if not isinstance(first, dict) or "content" not in first:
        return None, (jsonify({"error": "Invalid request format"}), 400)

    return first.get("content") or "", None


def _agent_response(agent_label):
    content, error = _extract_content()
    if error:
        return error

    url = get_url(agent_label)
    model = get_model(agent_label)
    if not url or url == "none" or not model or model == "none":
        return jsonify({"error": f"Agent {agent_label} is not configured"}), 500

    print("-----------------------------------")
    print(agent_label)
    return Response(
        stream_with_context(call_api_stream(content, model, url, agent_label=agent_label)),
        content_type='application/json'
    )


@surgery_app.route('/surgery_standardized', methods=['POST'])
def surgery_standardized():
    return _agent_response("surgery_standardized")


@surgery_app.route('/surgery_additional', methods=['POST'])
def surgery_additional():
    return _agent_response("surgery_additional")


@surgery_app.route('/surgery_another_coding', methods=['POST'])
def surgery_another_coding():
    return _agent_response("surgery_another_coding")


@surgery_app.route('/surgery_sorting', methods=['POST'])
def surgery_sorting():
    return _agent_response("surgery_sorting")


@surgery_app.route('/surgery_screening', methods=['POST'])
def surgery_screening():
    return _agent_response("surgery_screening")


@surgery_app.route('/no_surgery_standardized', methods=['POST'])
def no_surgery_standardized():
    return _agent_response("no_surgery_standardized")


@surgery_app.route('/no_surgery_screening', methods=['POST'])
def no_surgery_screening():
    return _agent_response("no_surgery_screening")


@surgery_app.route('/no_surgery_name', methods=['POST'])
def no_surgery_name():
    return _agent_response("no_surgery_name")
