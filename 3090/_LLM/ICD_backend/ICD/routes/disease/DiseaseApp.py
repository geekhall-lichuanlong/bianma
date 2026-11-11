from flask import Blueprint, Response, jsonify, request, stream_with_context

from api.CallAPI import call_api_stream
from parse import get_model, get_url


disease_app = Blueprint('disease', __name__)


def get_disease_app():
    return disease_app


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


@disease_app.route('/disease_standardized', methods=['POST'])
def disease_standardized():
    return _agent_response("disease_standardized")


@disease_app.route('/disease_potential_extract', methods=['POST'])
def disease_potential_extract():
    return _agent_response("disease_potential_extract")


@disease_app.route('/disease_potential_standardized', methods=['POST'])
def disease_potential_standardized():
    return _agent_response("disease_potential_standardized")


@disease_app.route('/disease_main_diagnosis', methods=['POST'])
def disease_main_diagnosis():
    return _agent_response("disease_main_diagnosis")


@disease_app.route('/disease_screening', methods=['POST'])
def disease_screening():
    return _agent_response("disease_screening")


@disease_app.route('/disease_potential_verify', methods=['POST'])
def disease_potential_verify():
    return _agent_response("disease_potential_verify")


@disease_app.route('/disease_bingli', methods=['POST'])
def disease_bingli():
    return _agent_response("disease_bingli")


@disease_app.route('/disease_external', methods=['POST'])
def disease_external():
    return _agent_response("disease_external")
